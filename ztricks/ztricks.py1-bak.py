import sys, es, os, re, playerlib, gamethread, effectlib, urllib, time, popuplib, sqlite3, vecmath, math, sets, shutil, thread, ConfigParser
from time import strftime #strftime("%Y-%m-%d %H:%M:%S")

ver=19
rate=0.01								# timer rate
our_dir=es.getAddonPath('ztricks')					# don't touch
config_file="%s/%s" % (our_dir, 'zconfig.txt')				# configuration file

players={}
triggers=[]
tricks=[]

def d(text):
	#es.msg("[debug] %s: %s" % (time.time(), text))
	if isDev():
		print "[debug] %s: %s" % (time.time(), text)


def timer():
	#
	# This function fires every 10ms (unless changed) to check every players
	# position and determine if they have hit a trick or not.
	#
	playerlist = playerlib.getUseridList("#alive")
	try:
		for userid in playerlist:
			check_keys(userid)
			[x,y,z]=getPlayerCoords(userid)

			triggerindex=findTrigger(userid, x, y, z)
			if not triggerindex >= 0: continue
			if len( players[userid]['triggerlist'] ) > 0:
				if players[userid]['triggerlist'][-1] == triggerindex: continue
			if players[userid]['debug'] == 1:
				v=getPlayerVelocity(userid)
				es.tell(userid, "#multi", "#lightgreenYou just triggered->#green%s#lightgreen direction->#green%s#lightgreen speed->#green%.2f# (%d mph)" % (getTriggerName(triggerindex), getPlayerAngle(userid), v, v/26))
			playerTriggerAdd(userid, triggerindex)
			foundTrigger(userid, triggerindex)
	except:
		d("there was an exception during timer()")
	gamethread.delayedname(rate, 'timer1', timer)

def foundTrigger(userid, triggerindex):
	d("foundTrigger()")
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

	#
	# 20090316
	# somewhere above this needs to be a check to see if it was also the same angle, or reset that too.
	#

	#es.msg("you were going %s and %s" % (getPlayerDest(userid, 'fr'), getPlayerDest(userid, 'wasd')))

	# check all tricks to see if one was completed
	# score is based on the length of the trick, more=better
	# so find the longest trick that has been completed and go with that.
	best_time=-1
	best_angle=[]
	best_index=-1
	best_score=-1
	best_speed=0
	for trick in tricks:
		index=tricks.index(trick)
		[pathlist, passlist, points, name]=trick

		if len(pathlist) <= best_score: continue

		#if len(players[userid]['tricklist']) > 0:
		#	if players[userid]['tricklist'][-1] == index: continue

		[t, angle, speed]=compareList(pathlist, passlist, userid)
		if t < 1: continue

		best_speed=speed
		best_angle=angle
		best_time=t
		best_score=len(pathlist)
		best_index=index

	if best_score == -1: return

	# turn speed[list] into number
	speed_total=0
	for x in best_speed:
		speed_total = speed_total + x
	if speed_total > 0 and len(best_speed) > 1:
		speed_total = (speed_total / len(best_speed)) / 26

	foundTrick(userid, best_index, best_time, best_angle, speed_total)

def foundTrick(userid, trickindex, time_first, angles, speed):
	d("foundTrick()")
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

	#s=es.sql('queryvalue','ztricks',"SELECT seconds FROM records WHERE trickname='%s'" % trick_name)
	s=getini('records', trickname, 'seconds', 0)

	diff=(float(seconds) - float(s))

	if s == 0:		diffstr=""
	elif diff >= 0:		diffstr="#green%.4f#lightgreen too slow!" % diff
	else:			diffstr="#green%.4f#lightgreen faster!" % (diff - (diff * 2))

	es.msg("#multi", "#lightgreen%s completed #green%s#lightgreen in #green%.4f#lightgreen seconds going #green%d#lightgreen mph! %s" % (getPlayerName(userid), trick_name, seconds, speed, diffstr))
	check_records(userid, trick_name, seconds)

def getTrickTime(userid, pathlist):
	# Return the amount of seconds it took to complete the trick for this player
	delta=int("-%s" % len(pathlist))
	return players[userid]['triggertimes'][-1] - players[userid]['triggertimes'][delta]

def isDev():
	if os.path.exists("%s/%s" % (our_dir, 'dev-server')):
		return 1

def check_records(userid, trickname, seconds):
	#s=es.sql('queryvalue','ztricks',"SELECT seconds FROM records WHERE trickname='%s'" % trickname)
	s=sql("SELECT seconds FROM records WHERE trickname='%s'" % trickname)
	s=getini('records',trickname,'seconds', 0)
	seconds=float(seconds)

	# see if they broke it
	if seconds < s or s == 0:
		steamid=es.getplayersteamid(userid)
		if steamid in ['STEAM_ID_LAN','STEAM_ID_PENDING','STEAM_ID_LOOPBACK','BOT',None,'']:
			es.msg("#lightgreen", "[ztricks] %s just broke a record but didn't have a steamid!" % getPlayerName(userid))
			return

		#name=es.getplayername(userid)
		#name=name.strip("\'\"")
		name=safePlayerName(userid)

		es.msg("#multi", "#lightgreen[ztricks] #green%s#lightgreen just broke the record for #green%s#lightgreen with #green%.4f#lightgreen seconds! last record was #green%.4f" % (name, trickname, seconds, s))

		#es.sql('query', 'ztricks', "UPDATE records SET seconds='%s', playername='%s', playersteam='%s' WHERE trickname='%s'" % (seconds, name, steamid, trickname))
		#sql("UPDATE records SET seconds='%s', settime='%s', playername='%s', playersteam='%s' WHERE trickname='%s'" % (seconds, time.time(), name, steamid, trickname))

		setini('records',trickname,'seconds',seconds)
		setini('records',trickname,'settime',time.time())
		setini('records',trickname,'playername',name)
		setini('records',trickname,'playersteam',steamid)

		#es.sql('query', 'ztricks', "UPDATE records SET settime='%s' WHERE trickname='%s'" % (time.time(), trickname))
		# why is this here?
		#sql("UPDATE records SET settime='%s' WHERE trickname='%s'" % (time.time(), trickname))

def trickName(name, count, angles):
	# 20090315 - see if they did it all one way
	s = sets.Set(angles)
	angle=s.pop()
	if len(s) == 1 and not angle == "forward":
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
	userspeed=players[userid]['triggerspeeds']

	if len(pathlist) > len(userlist): return [-1, -1, -1]
	delta=int("-%s" % len(pathlist))

	# a userlist may not end in a passlist item
	if userlist[-1] in passlist: return [-2, -2, -2]

	newlist=[]
	newtime=[]
	newangle=[]
	newspeed=[]
	index=0
	for point in userlist:
		if not point in passlist:
			# This is a required point
			newlist.append(point)
			newtime.append( usertime[index] )
			newangle.append( userangle[index] )
			newspeed.append( userspeed[index] )
		index=index + 1

	if newlist[delta:] == pathlist:	return [ newtime[delta:][0] , newangle[delta:] , newspeed[delta:] ]
	else:				return [-3, -3, -3]

def loadConfig():
	global triggers
	global tricks
	d("loading configuration")
	if not os.path.exists(config_file) and os.path.isfile(config_file):
		es.msg("error loading configuration! does not exist")
		return
	f=open(config_file, 'r')
	if not f:
		es.msg("unable to load configuration")
		return

	# 20090316 - every load, copy the existing to the backup directory just incase
	if not os.path.exists("%s/%s" % (our_dir, 'config-backup')):
		os.makedirs("%s/%s" % (our_dir, 'config-backup'))
	if os.path.exists("%s/%s" % (our_dir, 'config-backup')):
		shutil.copyfile(config_file, "%s/%s/zconfig-%s.txt"%(our_dir, 'config-backup', strftime("%Y%m%d_%H%M%S")))

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
		if type == "trig_sphere" or type == "trig_sphere_sym":
			m=re.match("%s\t+(\d+)\t+([-\d,.]+)\t+([-\d]+)\t+([-\d]+)\t+([-asdwfr])\t+(.*)"%type, line)
			if not m:
				es.msg("WARNING! line %s: failed to read line"%linecount)
				continue
			[id, center, radius, height, wasdfr, name]=m.groups()

			if height == "-":
				height=radius
			elif height > radius:
				height=radius

			if not center.count(',') == 2:
				es.msg("WARNING! line %s: invalid comma count"%linecount)
				continue
			# add the first (t)
			triggers.append([id, name, type, center.split(","), [0,0,0], [radius, height], wasdfr.lower()])

			if type == "trig_sphere_sym":
				# add the second (ct)
				[x,y,z]=center.split(",")
				y=pn_flip(y)				
				triggers.append([id, name, type, [x,y,z], [0,0,0], [radius, height], wasdfr.lower()])


		# trig_sym	51	-500,-8800,-1600	100,-8300,-1400		awp box
		if type == "trig_sym" or type == "trigger":
			m=re.match("%s\t+(\d+)\t+([-\d,.]+)\t+([-\d,.]+)\t+([-asdwfr])\t+(.*)"%type, line)
			if not m:
				es.msg("WARNING! line %s: failed to read line"%linecount)
				continue
			[id, c1, c2, wasdfr, name]=m.groups()
			if not c1.count(',') == 2 or not c2.count(',') == 2:
				es.msg("WARNING! line %s: invalid comma count" % linecount)
				continue
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
				es.msg("WARNING! line %s: failed to read line"%linecount)
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
		if type == "trigger" or type == "trig_sym":
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
		elif type == "trig_sphere" or type == "trig_sphere_sym":
			[radius, height]=extra
			radius=float(radius)

			[basex,basey,basez]=coord1
			basex=float(basex)
			basey=float(basey)
			basez=float(basez)

			if not height == "-":
				# check if we are within z tolerance first
				height=float(height)
				if pz < (basez - height) or pz > (basez + height):
					continue

			dist=vecmath.distance([basex,basey,basez], [px,py,pz])
			if dist <= radius:
				return id
	return -1

def setini(file, section, key, value):
	global config
	config.read(file)

	if not config.has_section(section):
		config.add_section(section)

	config.set(section, key, value)

	F=open(file,'wb')
	if not F: return
	config.write(F)
	F.close()
	return 1

def getini(file, section, key, value=None):
	global config
	config.read(file)
	r=config.get(section, key)
	d("getini() type->%s value->%s" % (type(r), r))
	return r

#def check_bad_command(userid, args):
#	text=" ".join(args)
#	if text.find("teleport") > 0 or text.find("setpos") > 0 or text.find("noclip") > 0: playerTriggerReset(userid)

##############################################################################################################
# EVENTS
##############################################################################################################
def player_spawn(ev):
	playerTriggerReset(ev['userid'])

def player_death(ev):
	userid=ev['userid']
	playerTriggerReset(userid)
	es.tell(userid, "#multi", "#lightgreen[ztricks] Type #green!zmenu#lightgreen to view stats! Type #green!rank#lightgreen to view your rank!")

def load():
	d("load() called")

	global config
	config=ConfigParser.RawConfigParser()
	if not config:
		es.msg('[ztricks] there was an error opening the config handler')
		es.unload('ztricks')
		return

	loadConfig()

	es.addons.registerClientCommandFilter(zts_cc_filter)
	es.addons.registerSayFilter(sayFilter)
	gamethread.delayedname(rate, 'timer1', timer)
	es.msg("ztricks loaded v%s" % ver)

def unload():
	d("unload() called")
	gamethread.cancelDelayed('timer1')
	es.addons.unregisterClientCommandFilter(zts_cc_filter)
	es.addons.unregisterSayFilter(sayFilter)
	es.msg("ztricks unloaded")

def zts_cc_filter(userid, args):
	if args[0] in ['menutest','ztricks','!menu','!zmenu','!ztricks']:
		menu_main(userid)
	#check_bad_command(userid, args)
	return True

def sayFilter(userid, text, teamOnly):
	text_noquote = text.strip('"')
	words = text_noquote.split(" ")
	cmd = words[0].lower()

	#check_bad_command(userid, text)

	if cmd in ['menutest','ztricks','!menu','!zmenu','!ztricks']:
		menu_main(userid)
		#return (0, "", 0)

	if cmd in ['rank','!rank','zrank']:
		es.msg("#lightgreen", "[ztricks] %s has %s points!" % (getPlayerName(userid), getPlayerPoints(userid)))
		#return (0, "", 0)
		return (userid, text, teamOnly)

	#if cmd in ['top','!top','ztop']:
	#	menu_top(userid)
	#	return (0, "", 0)
	#	return (userid, text, teamOnly)

	#if cmd in ['points','!points']:
	#	menu_points(userid)
	#	return (0,"",0)

	#if cmd == "!testset":
	#	testest(userid)

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
					c=centerof(type, coord1, coord2)
					[id, name, type, coord1, coord2, extra, wasdfr]=getTriggerArray(lasttrigger)
					l=centerof(type, coord1,coord2)

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

	if cmd == "!drawtrigger":
		menu_drawtrigger(userid)
		return (0,'',0)

	if cmd == "!reload":
		loadConfig()
		return (0, "", 0)

	return (userid, text, teamOnly)

def es_player_validated(ev):
	return
	# FIXME
	steamid=ev['networkid']
	userid=es.getuserid(steamid)
	name=safePlayerName(userid)
	if not name or name == "":
		d("es_player_validated does not have a name!!")
		return
	#sql("UPDATE records SET playername='%s' WHERE playersteam='s'" % (name, steamid))
	#sql("UPDATE points SET playername='%s' WHERE playersteam='s'" % (name, steamid))

##############################################################################################################
# COMMON FUNCTIONS
##############################################################################################################
def playerTriggerReset(userid):
	# If a player dies their trigger lists are reset here.
	check_keys(userid)
	del players[userid]['triggerlist'][:]
	del players[userid]['triggertimes'][:]
	del players[userid]['triggerangles'][:]
	del players[userid]['triggerspeeds'][:]

def playerTriggerAdd(userid, triggerindex):
	# When a player touches a trigger, this function records the trigger, time, and angles
	# so that when a trick is completed, these values can be checked to validate.
	check_keys(userid)
	global players
	players[userid]['triggerlist'].append( triggerindex )
	players[userid]['triggertimes'].append( time.time() )
	players[userid]['triggerangles'].append( getPlayerAngle(userid) )
	players[userid]['triggerspeeds'].append( getPlayerVelocity(userid) )

def getPlayerVelocity(userid):
	x=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[0]')
	y=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[1]')
	z=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[2]')
	return math.sqrt(x*x + y*y + z*z)

def distancefromorigin(x, y, z):
	distance = math.sqrt(x*x + y*y + z*z)
	return distance

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

		elif type == "trig_sphere" or type == "trig_sphere_sym":
			[radius, height]=extra
			#es.tell(userid, "warning, sphere triggers are not enabled yet!")

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
	return es.getplayerlocation(userid)
	#myPlayer = playerlib.getPlayer(userid)
	#return [myPlayer.attributes['x'], myPlayer.attributes['y'], myPlayer.attributes['z']]

def getPlayerPoints(userid):
	#return 2
	steamid=es.getplayersteamid(userid)
	if steamid in ['STEAM_ID_LAN','STEAM_ID_PENDING','STEAM_ID_LOOPBACK','BOT',None,'']: return 0

	#points=es.sql('queryvalue','ztricks',"SELECT points FROM points WHERE playersteam='%s'"%steamid)
	#points=sql("SELECT points FROM points WHERE playersteam='%s'"%steamid)
	return getini('points', playersteam, 0)

def safePlayerName(userid):
	name=es.getplayername(userid)
	if not name:
		d("safePlayerName() is none! [%s]" % name)
		return
	name=name.strip("\'\"")
	return name

def sql_open():
	d("ERROR sql_open() called")
	return
	global connection
	connection = sqlite3.connect("%s/cfg/es_ztricks.sqldb"%es.ServerVar('eventscripts_gamedir'), timeout=0, isolation_level=None)
	if not connection:
		es.msg("[ztricks] unable to open database, failure.")
		return -1
	return 1

def sql_close():
	d("ERROR sql_close() called")
	return
	if not connection:
		return
	connection.commit()
	connection.close()
	d("sql_close()")

def sql(text):
	d("ERROR sql() called with %s" % text)
	return

	#
	# This is going to be like es.sql however with two differences
	# - It will return a list of data instead of 1col1row
	# - Does not auto commit
	#
	d("sql() called")

	if text.startswith("INSERT") or text.startswith("UPDATE"):
		#es.msg("warning: data not stored")
		return

	#	d("sql() given insert or update command, deffering to sqlu()..")
	#	try:
	#		thread.start_new_thread(sqlu,(text,))
	#	except:
	#		es.msg("fatal thread aab")
	#	#reset the connection for some reason :/
	#	sql_open()
	#	return

	global connection
	cursor = connection.cursor()

	try:
		cursor.execute(text)
		d("- ran sql: %s" % text)
		for row in cursor:
			d("- row length=%s" % len(row))
			d("- row=%s" % row)
			return row
	except AttributeError:
		d("command returned 0 results")
	except:
		return ''
		#es.msg("ERROR: DATA WAS NOT SAVED")
		#d("sql exception on text: %s" % text)
		#x=sys.exc_info()
		#for i in x:
		#	d("- arg: %s" % i)
		#d("-[done2]")
	return ''

def givePlayerPoints(userid, points):
	steamid=es.getplayersteamid(userid)
	if steamid in ['STEAM_ID_LAN','STEAM_ID_PENDING','STEAM_ID_LOOPBACK','BOT',None,'']: return

	#sql("UPDATE points SET points=(points + %s), playername='%s' WHERE playersteam='%s'" % (points, safePlayerName(userid), steamid))
	setini('points', playersteam, 'points', int(points) + int(getPlayerPoints(userid))

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
		players[userid]['trick_angle']="none"

		# why did it work without this?
		#players[userid]['_trick_time']=0

		players[userid]['triggerlist']=[]
		players[userid]['triggertimes']=[]
		players[userid]['triggerangles']=[]
		players[userid]['triggerspeeds']=[]

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

def centerof(type, coord1, coord2):
	# calculate and return an array coordinate of the center
	# get coords

	if type == "trig_sphere" or type == "trig_sphere_sym":
		return coord1

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

def getAdmins():
	list=[]
	fh=open("%s/cfg/mani_admin_plugin/clients.txt"%es.ServerVar('eventscripts_gamedir'), 'r')
	if not fh: return list # unable to open the file

	lines=fh.readlines()
	fh.close()
	for line in lines:
		if not "steam" in line: continue
		pat=re.compile("(STEAM.*)\"")
		matches=re.findall(pat,line)
		if matches: list.append(matches[0])
	return list

def isAdmin(userid):
	steamid=es.getplayersteamid(userid)
	if steamid in getAdmins():
		return 1

##############################################################################################################
# MENUS
##############################################################################################################

def menu_main(userid):
	myPopup = popuplib.easymenu("%s -- %s"%(time.time(),userid), None, menu_main_select)
	myPopup.settitle("ZTricks Main Menu")
	myPopup.c_beginsep=None
	myPopup.c_pagesep=None
	myPopup.c_endsep=None
	myPopup.addoption('viewTricks', 'View Tricks')
	myPopup.addoption('viewRecords', 'View Records')
	myPopup.addoption('viewPoints', 'View Points')

	if isAdmin(userid):
		myPopup.addoption('drawTriggers', 'Draw Triggers')
		myPopup.addoption('reloadConfig', 'Reload Configuration')
		myPopup.addoption('toggleDebug', 'Toggle Debug Messages')
		myPopup.addoption('getZtrickSettings', 'Get Ztrick Settings')
	myPopup.send(userid)

def menu_main_select (userid, choice, popupid):
	if choice == 'viewTricks':
		es.tell(userid,'[ztricks] view tricks is not implemented yet')

	elif choice == 'getZtrickSettings':
		try:
			es.tell(userid,'#multi', "#lightgreen[ztricks] version->#green%s" % ver)
			es.tell(userid,'#multi', "#lightgreen[ztricks] speed->#green%s" % rate)
			es.tell(userid,'#multi', "#lightgreen[ztricks] path->#green%s" % our_dir)
			es.tell(userid,'#multi', "#lightgreen[ztricks] getlogin()->#green%s" % os.getlogin())
			es.tell(userid,'#multi', "#lightgreen[ztricks] home->#green%s" % os.getenv('HOME'))
		except:
			pass

	elif choice == 'viewRecords':
		menu_toprecords(userid)

	elif choice == 'viewPoints':
		menu_points(userid)

	elif choice == 'drawTriggers':
		menu_drawtrigger(userid)

	elif choice == 'reloadConfig':
		if not isAdmin(userid):
			es.tell(userid,'[ztricks] That function is for admins only')
			return
		loadConfig()

	elif choice == 'toggleDebug':
		if players[userid]['debug'] == 0:
			es.tell(userid, "#lightgreen", "You will now see debug messages")
			players[userid]['debug']=1
		else:
			es.tell(userid, "#lightgreen", "Debug messages have been disabled")
			players[userid]['debug']=0

	else:
		d("menu_main_select user->%s choice->%s"%(userid,choice))

def menu_drawtrigger(userid):
	if not isAdmin(userid):
		es.tell(userid,'[ztricks] That function is for admins only')
		return

	myPopup = popuplib.easymenu('menu', None, menu_drawtrigger_select)
	myPopup.settitle("Select trigger:")
	myPopup.c_beginsep=None
	myPopup.c_pagesep=None
	myPopup.c_endsep=None
	dupe=[]
	for trigger in triggers:
		[id, name, type, coord1, coord2, extra, wasdfr]=trigger
		if id in dupe: continue
		dupe.append(id)
		myPopup.addoption(name, "%s (%s)"%(name,id))
	myPopup.send(userid)

def menu_drawtrigger_select (userid, choice, popupid):
	if not isAdmin(userid):
		es.tell(userid,'[ztricks] That function is for admins only')
		return

	es.tell(userid, "[ztricks] drawing %s" % choice)
	drawtrigger(userid, choice)

def menu_toprecords(userid):
	myPopup = popuplib.easymenu("top menu for %s" % userid, None, menu_toprecords_select)
	myPopup.settitle("top")
	myPopup.c_beginsep=None
	myPopup.c_pagesep=None
	myPopup.c_endsep=None

	cursor = connection.cursor()
	if not cursor: es.msg("fail -2")
	cursor.execute('select trickname, playername, seconds from records order by trickname')
	for row in cursor:
		trickname, playername, seconds = row
		myPopup.addoption(trickname, "%s -> %s -> %s" % (trickname,playername,seconds))
	myPopup.send(userid)

def menu_toprecords_select (userid, choice, popupid):
	for box in tricks:
		[pathlist, path, points, name]=box
		if name == choice:
			# create a string for each path
			namelist=[]
			for p in pathlist: namelist.append(getTriggerName(p))
			es.tell(userid, "#lightgreen", "[ztricks] trick %s is %s" % (choice, " -> ".join(namelist)) )
			return (0, "", 0)

def menu_points(userid):
	myPopup = popuplib.easymenu("points menu for %s" % userid, None, menu_points_select)
	myPopup.settitle("points")
	myPopup.c_beginsep=None
	myPopup.c_pagesep=None
	myPopup.c_endsep=None

	cursor = connection.cursor()
	if not cursor: es.msg("fail -2")
	cursor.execute('select playersteam, playername, points from points order by points desc')
	for row in cursor:
		playersteam, playername, points = row
		if playername == "unknown player":
			playername=playersteam
		myPopup.addoption(playername, "%s %s" % (points, playername))
	myPopup.send(userid)

def menu_points_select(userid, choice, popupid):
	print "unhandled menu select"


