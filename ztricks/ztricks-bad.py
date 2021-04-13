import es, os, re, playerlib, gamethread, effectlib, urllib, time, popuplib, sqlite3, vecmath, math, sets
from time import strftime #strftime("%Y-%m-%d %H:%M:%S")

#
# ztricks
# 20090227 - initial
# 20090228 - tricks and detection working
# 20090302 - spawning clears list
# 20090303 - added player death to reset
# 20090307 - changed drawbox to drawline
#          - recalculated xyz on load
#          - reduced time rate
#          - fixed load and unload
#          - fixed unloading issues
#          - added !info <trick>
#          - changed compareList
#          - player death now clears the players path list
#
# 20090312 - completely redone
#          - added menu to show triggers
#          - tricks cannot end in passthru
#          - renamed quiet to debug
#          - new found...() functions
#
# 20090313 - harsher config regex and warnings about the lines
# 20090314 - correctly count time for tricks now
#          - added support for checking records
# 20090315 - detects and stores player direction
#          - awards based on the name
#          - fixed newtime delta
#
#          - fixed trickName forward bug
#
# TODO:
# - add direction element to tricks so it can detect sideways or backwards.
# - find velocity number and divide by 26(?) to mph
# - database for records (speed, time)
# [DONE] trick time needs to count all the way back to x1
# - menu for tricks (records, display, how)
# - est_effect to draw on only one user screen
#

rate=0.01								# timer rate
max_idle=10								# seconds
config_file='cstrike/addons/eventscripts/ztricks/zconfig.txt'		# configuration file

players={}
triggers=[]
tricks=[]

def timer():
	#
	# This function fires every 10ms (unless changed) to check every players
	# position and determine if they have hit a trick or not.
	#
	gamethread.delayedname(rate, 'timer1', timer)
	playerlist = playerlib.getUseridList("#alive")
	for userid in playerlist:
		check_keys(userid)
		[x,y,z]=getPlayerCoords(userid)

		triggerindex=findTrigger(userid, x, y, z)
		if not triggerindex >= 0: continue
		if len( players[userid]['triggerlist'] ) > 0:
			if players[userid]['triggerlist'][-1] == triggerindex: continue
		if players[userid]['debug'] == 1:
			es.tell(userid, "#multi", "#lightgreenyou just triggered #green%s#lightgreen !!" % getTriggerName(triggerindex))
			es.tell(userid, "#multi", "#lightgreenyou were going #green%s" % getPlayerAngle(userid))
		playerTriggerAdd(userid, triggerindex)
		foundTrigger(userid, triggerindex)

def foundTrigger(userid, triggerindex):
	#
	# This function fires when a player has touched a trigger.
	# - Determine if a trick has been completed
	#

	# if this trigger is NOT in the last trick, make it impossible to do x+1
	# - get last trick path
	# - see if this trigger is in that trick
	if len(players[userid]['tricklist']) > 0:
		lasttrickindex=players[userid]['tricklist'][-1]
		# check to see if lasttrickindex is even possible
		if lasttrickindex >= 0:
			lasttrick=tricks[lasttrickindex]
			[pathlist, passlist, points, name]=lasttrick
			if not triggerindex in pathlist:
				players[userid]['tricklist'].append(-19)

	#es.msg("you were going %s and %s" % (getPlayerDest(userid, 'fr'), getPlayerDest(userid, 'wasd')))

	# check all tricks to see if one was completed
	# score is based on the length of the trick, more=better
	# so find the longest trick that has been completed and go with that.
	best_time=-1
	best_angle=[]
	best_index=-1
	best_score=-1
	for trick in tricks:
		index=tricks.index(trick)
		[pathlist, passlist, points, name]=trick

		if len(pathlist) <= best_score: continue

		#if len(players[userid]['tricklist']) > 0:
		#	if players[userid]['tricklist'][-1] == index: continue

		[t, angle]=compareList(pathlist, passlist, userid)
		if t < 1: continue

		best_angle=angle
		best_time=t
		best_score=len(pathlist)
		best_index=index

	if best_score == -1: return
	foundTrick(userid, best_index, best_time, best_angle)

def foundTrick(userid, trickindex, time_first, angles):
	#
	# This function is fired when a player has done a trick.
	# - Give them points
	# - Correctly count it
	# - Say a nice message
	# - add seconds onto the trick times
	#

	[pathlist, passlist, points, name]=tricks[trickindex]

	trick_total_time=getTrickTime(userid, pathlist)

	if len(players[userid]['tricklist']) == 0:
		# First trick, =1
		players[userid]['trick_count'] = 1
		players[userid]['_trick_time'] = time_first
	elif players[userid]['tricklist'][-1] == trickindex:
		# They did the same trick again, +1
		players[userid]['trick_count'] = players[userid]['trick_count'] + 1
	else:
		# This is the first of the trick they have done. =1
		players[userid]['trick_count'] = 1
		players[userid]['_trick_time'] = time_first

	seconds=time.time() - players[userid]['_trick_time']

	# special awp counter +1
	if name == "awp" and players[userid]['trick_count'] == 1:
		players[userid]['trick_count']=2

	givePlayerPoints(userid, int(points))
	players[userid]['tricklist'].append(trickindex)

	trick_name=trickName(name, players[userid]['trick_count'], angles)
	s=es.sql('queryvalue','ztricks',"SELECT seconds FROM records WHERE trickname='%s'" % trick_name)
	if not s: s=float(0)
	diff=(float(seconds) - float(s))

	es.msg("#multi", "#lightgreen%s just completed #green%s#lightgreen !! it took #green%.4f#lightgreen seconds !! #green%.4f#lightgreen difference !!" % (getPlayerName(userid), trick_name, seconds, diff))
	es.tell(userid, "#multi", "#lightgreenYou now have #green%s#lightgreen points !!" % (getPlayerPoints(userid)))

	check_records(userid, trick_name, seconds)

def getTrickTime(userid, pathlist):
	# Return the amount of seconds it took to complete the trick for this player
	delta=int("-%s" % len(pathlist))
	return players[userid]['triggertimes'][-1] - players[userid]['triggertimes'][delta]

def check_records(userid, trickname, seconds):
	es.sql('query','ztricks',"INSERT INTO records (trickname) VALUES ('%s')" % trickname)
	s=es.sql('queryvalue','ztricks',"SELECT seconds FROM records WHERE trickname='%s'" % trickname)
	s=float(s)
	seconds=float(seconds)

	# see if they broke it
	if seconds < s or s == 0:
		steamid=es.getplayersteamid(userid)
		if steamid in ['STEAM_ID_LAN','STEAM_ID_PENDING','STEAM_ID_LOOPBACK','BOT',None,'']:
			es.msg("#lightgreen", "[ztricks] %s just broke a record but didn't have a steamid!" % getPlayerName(userid))
			return

		name=es.getplayername(userid)
		name=name.strip("\'\"")

		es.msg("#multi", "#lightgreen[ztricks] #green%s#lightgreen just broke a record !!" % name)
		es.msg("#multi", "#lightgreen[ztricks] new record for #green%s#lightgreen is now #green%.4f#lightgreen seconds !! last record was #green%.4f" % (trickname, seconds, s))
		es.sql('query', 'ztricks', "UPDATE records SET seconds='%s', playername='%s', playersteam='%s' WHERE trickname='%s'" % (seconds, name, steamid, trickname))
		es.sql('query', 'ztricks', "UPDATE records SET settime='%s' WHERE trickname='%s'" % (time.time(), trickname))

def trickName(name, count, angles):
	# 20090315 - see if they did it all one way
	s = sets.Set(angles)
	if len(s) == 1 and not angle == "forward":
		angle=s.pop()
		if count > 1:	return "%s %s x%s" % (angle, name, count)
		else:		return "%s %s" % (angle, name)
	else:
		if count > 1:	return "%s x%s" % (name, count)
	return name

def compareList(pathlist, passlist, userid):
	# return -1		if the user did not do the pathlist
	# return time		return the first time in the delta list

	userlist=players[userid]['triggerlist']
	usertime=players[userid]['triggertimes']
	userangle=players[userid]['triggerangles']

	if len(pathlist) > len(userlist): return [-1, -1]
	delta=int("-%s" % len(pathlist))

	# a userlist may not end in a passlist item
	if userlist[-1] in passlist: return [-2, -2]

	newlist=[]
	newtime=[]
	newangle=[]
	index=0
	for point in userlist:
		if not point in passlist:
			# This is a required point
			newlist.append(point)
			newtime.append( usertime[index] )
			newangle.append( userangle[index] )
		index=index + 1

	if newlist[delta:] == pathlist:	return [ newtime[delta:][0] , newangle[delta:] ]
	else:				return [-3, -3]

def loadConfig():
	global triggers
	global tricks
	print "loading configuration"
	if not os.path.exists(config_file) and os.path.isfile(config_file):
		es.msg("error loading configuration! does not exist")
		return
	f=open(config_file, 'r')
	if not f:
		es.msg("unable to load configuration")
		return
	triggers=[]
	tricks=[]
	lines=f.readlines()
	linecount=0
	for line in lines:
		linecount=linecount + 1
		m=re.match("^(\w+)", line)
		if not m: continue
		[type]=m.groups()

		# trig_sphere	1	0,0,0	150	10	-	hello
		if type == "trig_sphere":
			m=re.match("%s\t+(\d+)\t+([-\d,.]+)\t+([-\d]+)\t+([-\d]+)\t+([-asdwfr])\t+(.*)"%type, line)
			if not m:
				es.msg("WARNING: failed to read line %s"%linecount)
				continue
			[id, center, radius, height, wasdfr, name]=m.groups()
			triggers.append([id, name, type, center.split(","), [0,0,0], [radius, height], wasdfr.lower()])


		# trig_sym	51	-500,-8800,-1600	100,-8300,-1400		awp box
		if type == "trig_sym" or type == "trigger":
			m=re.match("%s\t+(\d+)\t+([-\d,.]+)\t+([-\d,.]+)\t+([-asdwfr])\t+(.*)"%type, line)
			if not m:
				es.msg("WARNING: failed to read line %s"%linecount)
				continue
			[id, c1, c2, wasdfr, name]=m.groups()
			[x1,y1,z1]=c1.split(',')
			[x2,y2,z2]=c2.split(',')

			[x1, x2]=autoswitch(x1, x2)
			[y1, y2]=autoswitch(y1, y2)
			[z1, z2]=autoswitch(z1, z2)

			# Add the first box (T)
			triggers.append([id, name, type, [x1, y1, z1], [x2, y2, z2], [], wasdfr.lower()])

			if type == "trig_sym":
				# Add the second box (CT)
				[y1, y2]=[y2, y1]
				#  and make them positive.
				y1=pn_flip(y1)
				y2=pn_flip(y2)
				triggers.append([id, name, type, [x1, y1, z1], [x2, y2, z2], [], wasdfr.lower()])

		# trickv2		1,54,52					-					400		hop to under 2nd to awp
		# [pathlist, passlist, points, name]
		if type == "trickv2":
			m=re.match("trickv2\t+([-\d,.]+)\t+([-\d,.]+)\t+(\d+)\t+(.*)", line)
			if not m:
				es.msg("WARNING: failed to read line %s"%linecount)
				continue
			[path, passthru, points, name]=m.groups()

			pathlist=path.split(',')
			if passthru == "-":	passlist=[]
			else:			passlist=passthru.split(',')
			tricks.append([pathlist, passlist, points, name])

	es.msg("found %s triggers, %s tricks" % (len(triggers), len(tricks)))

def getTriggerName(i):
	for box in triggers:
		if box[0] == i: return box[1]
	return "error"

def getTriggerArray(i):
	for box in triggers:
		if box[0] == i: return box

def findTrigger(userid, px, py, pz):
	# check each defined trigger to see if xyz matches and return the triggers id
	for trigger in triggers:
		[id, name, type, coord1, coord2, extra, wasdfr]=trigger
		[x1,y1,z1]=coord1
		[x2,y2,z2]=coord2

		# honor wasdfr
		if wasdfr in ['f','r']:
			if not wasdfr == getPlayerDest(userid, 'fr'):
				continue
		if wasdfr in ['w','a','s','d']:
			if not wasdfr == getPlayerDest(userid, 'wasd'):
				continue

		# determine if in the box
		if (px > int(x1) and px < int(x2)) or (px > int(x2) and px < int(x1)):
			if (py > int(y1) and py < int(y2)) or (py > int(y2) and py < int(y1)):
				if (pz > int(z1) and pz < int(z2)) or (pz > int(z2) and pz < int(z1)):
					return id
	return -1

def check_bad_command(userid, args):
	text=" ".join(args)
	if text.find("teleport") > 0 or text.find("setpos") > 0 or text.find("noclip") > 0: playerTriggerReset(userid)

##############################################################################################################
# EVENTS
##############################################################################################################
def player_spawn(ev):
	playerTriggerReset(ev['userid'])

def player_death(ev):
	playerTriggerReset(ev['userid'])

def load():
	loadConfig()
	es.sql('open','ztricks')
	es.sql('query','ztricks',"CREATE TABLE IF NOT EXISTS records (trickname VARCHAR(200) PRIMARY KEY NOT NULL, playername TEXT, playersteam TEXT, seconds INTEGER DEFAULT '0', settime TEXT)")
	es.sql('query','ztricks',"CREATE TABLE IF NOT EXISTS points (playersteam VARCHAR(200) NOT NULL PRIMARY KEY, points INTEGER DEFAULT '0')")

	# there was a bug where it would give forward tricks.
	es.sql('query','ztricks',"DELETE FROM records WHERE trickname LIKE 'forward%'")

	es.addons.registerClientCommandFilter(zts_cc_filter)
	es.addons.registerSayFilter(sayFilter)
	gamethread.delayedname(rate, 'timer1', timer)
	es.msg("ztricks loaded")

def unload():
	r=gamethread.cancelDelayed('timer1')
	es.sql('close','ztricks')
	es.addons.unregisterClientCommandFilter(zts_cc_filter)
	es.addons.unregisterSayFilter(sayFilter)
	es.msg("ztricks unloaded")

def zts_cc_filter(userid, args):
	check_bad_command(userid, args)
	return True

def sayFilter(userid, text, teamOnly):
	text_noquote = text.strip('"')
	words = text_noquote.split(" ")
	cmd = words[0].lower()

	check_bad_command(userid, words)

	if cmd in ['rank', '!rank']:
		es.msg("#lightgreen", "[ztricks] %s has %s points!" % (getPlayerName(userid), getPlayerPoints(userid)))
		return (0, "", 0)
		return (userid, text, teamOnly)

	if cmd in ['top','!top']:
		menu_top(userid)
		return (0, "", 0)
		return (userid, text, teamOnly)

	if cmd == "!show":
		if len(words) == 1:
			es.tell(userid, "#lightgreen", "usage: !show awp2awp")
			return (0, "", 0)
		tmp=text_noquote.split("!show ")
		req=tmp[1]
		# find the trick with that name
		for box in tricks:
			[pathlist, path, points, name]=box
			if name == req:
				namelist=[]
				for p in pathlist: namelist.append(p)

				# namelist contains the triggers to make the trick
				# draw lines from each to each
				lasttrigger=[]
				for trigger in namelist:
					if lasttrigger == []:
						lasttrigger=trigger
						continue

					[id, name, type, coord1, coord2, extra, wasdfr]=getTriggerArray(trigger)
					c=centerof(coord1, coord2)
					[id, name, type, coord1, coord2, extra, wasdfr]=getTriggerArray(lasttrigger)
					l=centerof(coord1,coord2)

					effectlib.drawLine(c, l, model="materials/sprites/laser.vmt", halo="materials/sprites/halo01.vmt", seconds=60, width=20, red=255, green=0, blue=0)
					lasttrigger=trigger

				es.msg("#multi", "#lightgreen[ztricks] red line is the path of #green%s" % req)
				return (0, "", 0)
		es.tell(userid, "#lightgreen", "[ztricks] unknown trick %s" % req)
		return (0, "", 0)

	if cmd == "!info":
		if len(words) == 1:
			es.tell(userid, "#lightgreen", "usage: !info awp2awp")
			return (0, "", 0)
		tmp=text_noquote.split("!info ")
		req=tmp[1]
		# find the trick with that name
		for box in tricks:
			[pathlist, path, points, name]=box
			if name == req:
				namelist=[]
				for p in pathlist: namelist.append(getTriggerName(p))
				es.tell(userid, "#lightgreen", "[ztricks] trick %s is %s" % (req, " -> ".join(namelist)) )
				return (0, "", 0)
		es.tell(userid, "#lightgreen", "[ztricks] unknown trick %s" % req)
		return (0, "", 0)

	if cmd == "!debug":
		c=players[userid]['debug']
		if c == 0:
			es.tell(userid, "#lightgreen", "you will now see more messages")
			players[userid]['debug']=1
		else:
			es.tell(userid, "#lightgreen", "debug messages have been disabled")
			players[userid]['debug']=0
		return (0, "", 0)

	if cmd == "!drawtrigger":
		menu_drawtrigger(userid)
		return (0,'',0)

	if cmd == "!reload":
		loadConfig()
		return (0, "", 0)

	return (userid, text, teamOnly)

##############################################################################################################
# COMMON FUNCTIONS
##############################################################################################################
def playerTriggerReset(userid):
	# If a player dies their trigger lists are reset here.
	check_keys(userid)
	del players[userid]['triggerlist'][:]
	del players[userid]['triggertimes'][:]
	del players[userid]['triggerangles'][:]

def playerTriggerAdd(userid, triggerindex):
	# When a player touches a trigger, this function records the trigger, time, and angles
	# so that when a trick is completed, these values can be checked to validate.
	check_keys(userid)
	global players
	players[userid]['triggerlist'].append( triggerindex )
	players[userid]['triggertimes'].append( time.time() )
	players[userid]['triggerangles'].append( getPlayerAngle(userid) )

def getPlayerDest(userid, mode='360'):
	v0=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[0]')
	v1=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[1]')
	r=math.degrees( math.atan2(v0,v1) ) + 90
	if r < 0: r = 360 + r
	r=360 - r

	if mode == 'wasd':
		# return as direction wasd
		if r < 45:	return "w"
		elif r < 135:	return "a"
		elif r < 225:	return "s"
		elif r < 315:	return "d"
		else:		return "w"
	elif mode == 'fr':
		# return as direction fr only
		if r < 90:	return "f"
		elif r > 270:	return "f"
		else:		return "r"
	else:
		# return as degrees
		return r

def getPlayerLook(userid):
	temp=es.getplayerprop(userid,'CBaseEntity.m_angRotation')
	temp=temp.split(",")
	return (float(temp[1]) + 180)

def getPlayerAngle(userid):
	look=getPlayerLook(userid) + 10000
	move=getPlayerDest(userid) + 10000
	if plusminus(look, move, 22.5):		return "forward"
	elif plusminus(look, move, 67.5):	return "halfsideways"
	elif plusminus(look, move, 112.5):	return "sideways"
	elif plusminus(look, move, 157.5):	return "halfsideways"
	else:					return "backwards"

def drawtrigger(userid, choice):
	for trigger in triggers:
		[id, name, type, coord1, coord2, extra, wasdfr]=trigger
		if not name == choice: continue
		if type == "trigger" or type == "trig_sym":
			drawbox(coord1,coord2)

		elif type == "trig_sphere":
			[radius, height]=extra
			es.tell(userid, "warning, sphere triggers are not enabled yet!")

			if height == "-":
				# just draw a sphere (3 circles)
				[basex,basey,basez]=coord1
				basex=float(basex)
				basey=float(basey)
				basez=float(basez)

				drawcircle([basex,basey,basez], radius, 'x')
				drawcircle([basex,basey,basez], radius, 'y')
			else:
				# ok, it has a height, draw both top and bottom
				[basex,basey,basez]=coord1
				basex=float(basex)
				basey=float(basey)
				basez=float(basez)

				height=float(height)
				[topx,topy,topz]=[basex,basey,basez + height]
				[botx,boty,botz]=[basex,basey,basez - height]

				drawcircle([topx,topy,topz], radius)
				drawcircle([basex,basey,basez], radius)
				drawcircle([botx,boty,botz], radius)

				# draw two more to show the roundness
				drawcircle([basex,basey,basez], radius, 'x')
				drawcircle([basex,basey,basez], radius, 'y')
		else:
			es.tell(userid, "unknown trigger type, cannot draw it!")

def drawline(coord1, coord2):
	effectlib.drawLine(coord1, coord2, model="materials/sprites/laser.vmt", halo="materials/sprites/halo01.vmt", seconds=120, width=5, red=255, green=255, blue=255)

def drawcircle(origin, radius, axle='z'):
	# axle1 (1,0,0) (0,1,0) = flat like ground
	#       (0,0,1) (0,1,0) = up and down going to awp2awp
	#	(1,0,0) (0,0,1) = up and down going pool to pyramid
	if axle == 'x':
		# pyramid to pool
		a1=(1,0,0)
		a2=(0,0,1)
	elif axle == 'y':
		# awp 2 awp
		a1=(0,0,1)
		a2=(0,1,0)
	else:
		# normal
		a1=(1,0,0)
		a2=(0,1,0)

	effectlib.drawCircle(origin, float(radius), steps=12, axle1=a1, axle2=a2, seconds=120)

def drawbox(coord1, coord2):
	effectlib.drawBox(coord1, coord2, model="materials/sprites/laser.vmt", halo="materials/sprites/halo01.vmt", seconds=120, width=5, red=255, green=255, blue=255)

def getPlayerCoords(userid):
	myPlayer = playerlib.getPlayer(userid)
	return [myPlayer.attributes['x'], myPlayer.attributes['y'], myPlayer.attributes['z']]

def getPlayerPoints(userid):
	steamid=es.getplayersteamid(userid)
	if steamid in ['STEAM_ID_LAN','STEAM_ID_PENDING','STEAM_ID_LOOPBACK','BOT',None,'']: return 0
	points=es.sql('queryvalue','ztricks',"SELECT points FROM points WHERE playersteam='%s'"%steamid)
	return int(points)

def givePlayerPoints(userid, points):
	steamid=es.getplayersteamid(userid)
	if steamid in ['STEAM_ID_LAN','STEAM_ID_PENDING','STEAM_ID_LOOPBACK','BOT',None,'']: return
	es.sql('query','ztricks',"INSERT INTO points (playersteam) VALUES ('%s')" % steamid)
	es.sql('query','ztricks',"UPDATE points SET points=(points + %s) WHERE playersteam='%s'" % (points, steamid))

def check_keys(userid):
	global players
	if not players.has_key(userid):
		players[userid]={}
	if not players[userid].has_key('x'):
		players[userid]['x']=0
		players[userid]['y']=0
		players[userid]['z']=0

		players[userid]['points']=0
		players[userid]['debug']=0

		players[userid]['tricklist']=[]
		players[userid]['trick_count']=0

		players[userid]['triggerlist']=[]
		players[userid]['triggertimes']=[]
		players[userid]['triggerangles']=[]

def getPlayerName(userid):
	return es.getplayername(userid)

def autoswitch(a, b):
	if (int(a) + 100000) < (int(b) + 100000):	return [b, a]
	else:						return [a, b]

def pn_flip(i):
	if int(i) < 0:
		m=re.match("\-(.*)", i)
		if m: [i]=m.groups()
	elif int(i) > 0:
		i=-i
	return i

def centerof(coord1, coord2):
	# calculate and return an array coordinate of the center
	# get coords
	[x1,y1,z1]=coord1
	[x2,y2,z2]=coord2

	# correct them
	[x1, x2]=autoswitch(x1, x2)
	[y1, y2]=autoswitch(y1, y2)
	[z1, z2]=autoswitch(z1, z2)

	# add a bunch :/
	x1=int(x1) + 100000
	x2=int(x2) + 100000
	y1=int(y1) + 100000
	y2=int(y2) + 100000
	z1=int(z1) + 100000
	z2=int(z2) + 100000

	# find middle
	x=(((x1 - x2) / 2) + x2) - 100000
	y=(((y1 - y2) / 2) + y2) - 100000
	z=(((z1 - z2) / 2) + z2) - 100000

	return [x,y,z]

def plusminus(master, slave,offset=22.5):
	if slave > (master - offset) and slave < (master + offset): return True

##############################################################################################################
# MENUS
##############################################################################################################
def menu_drawtrigger_select (userid, choice, popupid):
	drawtrigger(userid, choice)

def menu_drawtrigger(userid):
	myPopup = popuplib.easymenu('menu', None, menu_drawtrigger_select)
	myPopup.settitle("Select trigger:")

	dupe=[]
	for trigger in triggers:
		[id, name, type, coord1, coord2, extra, wasdfr]=trigger
		if id in dupe: continue
		dupe.append(id)
		myPopup.addoption(name, "%s (%s)"%(name,id))

	myPopup.send(userid)

def menu_top(userid):
	myPopup = popuplib.easymenu("top menu for %s" % userid, None, menu_top_select)
	myPopup.settitle("top")

	connection = sqlite3.connect('cstrike/cfg/es_ztricks.sqldb')
	if not connection: es.msg("fail -1")
	cursor = connection.cursor()
	if not cursor: es.msg("fail -2")
	cursor.execute('select trickname, playername, seconds from records order by trickname')
	for row in cursor:
		#es.msg("7")
		trickname, playername, seconds = row
		#print "trick[%s] player[%s] seconds[%s]" % (trickname, playername, seconds)
		#es.msg("8")
		myPopup.addoption(trickname, "%s -> %s -> %s" % (trickname,playername,seconds))

	myPopup.send(userid)

def menu_top_select (userid, choice, popupid):
	for box in tricks:
		[pathlist, path, points, name]=box
		if name == choice:
			# create a string for each path
			namelist=[]
			for p in pathlist: namelist.append(getTriggerName(p))
			es.tell(userid, "#lightgreen", "[ztricks] trick %s is %s" % (choice, " -> ".join(namelist)) )
			return (0, "", 0)










"""
	#dupe=[]
	#for trick in tricks:
	#	[pathlist, passlist, points, trickname]=trick
	#	if trickname in dupe: continue
	#	dupe.append(trickname)
	#	seconds=es.sql('queryvalue','ztricks',"SELECT seconds FROM records WHERE trickname='%s'" % trickname)
	#	playername=es.sql('queryvalue','ztricks',"SELECT playername FROM records WHERE trickname='%s'" % trickname)
	#	if not seconds:
	#		seconds="unset"
	#	if not playername:
	#		playername="nobody"
	#	myPopup.addoption(trickname, "%s -> %s -> %s"%(trickname,playername,seconds))

def testest(userid):
	return

	# direction the player is going
	v0=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[0]')
	v1=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[1]')
	r=math.degrees( math.atan2(v0,v1) ) + 90
	if r < 0: r = 360 + r
	r=360 - r

	# players view angle
	temp=es.getplayerprop(userid,'CBaseEntity.m_angRotation')
	temp=temp.split(",")
	view_angle = float(temp[1]) + 180

	# decide what they are doing
	look=view_angle + 10000
	move=r + 10000
	d="unknown"
	if plusminus(look, move, 22.5):		d="forward"
	elif plusminus(look, move, 67.5):	d="hsw front"
	elif plusminus(look,move, 112.5):	d="sideways"
	elif plusminus(look,move, 157.5):	d="hsw back"
	else:					d="backwards"

	#es.tell(userid, "your going %s" % d)


	#print "x->%s" % players[userid]['x']
	#	staticVec=es.createvectorstring(players[userid]['x'], players[userid]['y'] , players[userid]['z'])
	#	playerVec=es.createvectorstring(x,y,z)
	#
	#	ourVector = es.createvectorfrompoints(staticVec, playerVec)
	#	ourVector = es.splitvectorstring(ourVector)
	#	#print "our vec 1->%s 2->%s" % (float(ourVector[1]), float(ourVector[0]))
	#	try:
	#		ourAtan = math.degrees(math.atan(float(ourVector[1])/float(ourVector[0])))
	#	except:
	#		return
	#	#ourAtan = float(ourAtan) + 180
	#	#if ourAtan < 0:
	#	#	ourAtan = ourAtan + 180
	#	#else:
	#	#	ourAtan = ourAtan + 360

	#es.tell(userid, "base->%s" % es.getplayerprop(userid,'CBasePlayer.localdata.m_vecBaseVelocity'))
	#user_location = vecmath.vector(es.getplayerlocation(userid)) 
	return

	attacker_pos = vecmath.Vector( [0,0,0] )
	victim_pos = vecmath.Vector( es.getplayerlocation(userid) )
	player_segment = attacker_pos - victim_pos

	pitch, yaw, roll = vecmath.viewangles(player_segment) 
	es.tell(userid, "pitch->%s yaw->%s roll->%s" % (pitch, yaw, roll))

	#connection = sqlite3.connect('cstrike/cfg/es_ztricks.sqldb')
	#cursor = connection.cursor()
	#cursor.execute('select trickname, playername, seconds from records')
	#for row in cursor:
	#	trickname, playername, seconds = row
	#	print "trick[%s] player[%s] seconds[%s]" % (trickname, playername, seconds)

	#x=es.sql('queryvalue','ztricks','select trickname, playername, seconds from records')
	#print "x = %s" % x
"""
