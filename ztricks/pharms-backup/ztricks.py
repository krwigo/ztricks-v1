import es, os, re, playerlib, gamethread, effectlib, urllib, time, popuplib
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
# TODO:
# - add direction element to tricks so it can detect sideways or backwards.
# - find velocity number and divide by 26(?) to mph
# - database for records (speed, time)
# - trick time needs to count all the way back to x1
#

rate=0.01								# timer rate
max_idle=10								# seconds
config_file='cstrike/addons/eventscripts/ztricks/zconfig.txt'		# configuration file

# A hash to store player data
players={}

# Lists of triggers and tricks so they don't keep loading the file
triggers=[]
tricks=[]

def playerTriggerReset(userid):
	# If a player dies their trigger lists are reset here.
	check_keys(userid)

	#es.msg("reset pre: %s" % players[userid]['triggerlist'] )
	#del players[userid]['triggerlist'][:]
	#del players[userid]['triggertimes'][:]
	#del players[userid]['triggerangles'][:]
	#es.msg("reset post: %s" % players[userid]['triggerlist'])

def playerTriggerAdd(userid, triggerindex):
	# When a player touches a trigger, this function records the trigger, time, and angles
	# so that when a trick is completed, these values can be checked to validate.
	check_keys(userid)
	global players
	players[userid]['triggerlist'].append( triggerindex )
	players[userid]['triggertimes'].append( time.time() )
	players[userid]['triggerangles'].append( getPlayerAngles(userid) )

def getPlayerAngles(userid):
	## FIXME
	# This function should read the players angles and vect to determine if they are
	# going forwards, backwards, sideways, half side ways.
	# fw, bw, sw, hsw
	return "fw"

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

		triggerindex=getTrigger(x, y, z)
		if not triggerindex >= 0: continue
		if len( players[userid]['triggerlist'] ) > 0:
			if players[userid]['triggerlist'][-1] == triggerindex: continue
		if players[userid]['debug'] == 1: es.tell(userid, "#multi", "#lightgreenyou just triggered #green%s#lightgreen !!" % getTriggerName(triggerindex))
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

	# check all tricks to see if one was completed
	# score is based on the length of the trick, more=better
	# so find the longest trick that has been completed and go with that.
	best_score=-1
	best_index=-1
	for trick in tricks:
		index=tricks.index(trick)
		[pathlist, passlist, points, name]=trick

		if len(pathlist) <= best_score: continue

		#if len(players[userid]['tricklist']) > 0:
		#	if players[userid]['tricklist'][-1] == index: continue

		if compareList(pathlist, passlist, players[userid]['triggerlist']) < 1: continue

		best_score=len(pathlist)
		best_index=index

	if best_score == -1: return
	foundTrick(userid, best_index)

def getTrickTime(userid, pathlist):
	#
	# Return the amount of seconds it took to complete the trick for this player
	#
	total=0
	delta=int("-%s" % len(pathlist))
	# FIXME: delta should be of the previous ?x too!
	return players[userid]['triggertimes'][-1] - players[userid]['triggertimes'][delta]

def foundTrick(userid, trickindex):
	#
	# This function is fired when a player has done a trick.
	# - Give them points
	# - Correctly count it
	# - Say a nice message
	#

	[pathlist, passlist, points, name]=tricks[trickindex]

	trick_total_time=getTrickTime(userid, pathlist)

	if len(players[userid]['tricklist']) == 0:
		# First trick, =1
		players[userid]['trick_count'] = 1
	elif players[userid]['tricklist'][-1] == trickindex:
		# They did the same trick again, +1
		players[userid]['trick_count'] = players[userid]['trick_count'] + 1
	else:
		# This is the first of the trick they have done. =1
		players[userid]['trick_count'] = 1

	# special awp counter +1
	if name == "awp" and players[userid]['trick_count'] == 1:
		players[userid]['trick_count']=2

	givePlayerPoints(userid, int(points))
	players[userid]['tricklist'].append(trickindex)

	es.msg("#multi", "#lightgreen%s just completed #green%s#lightgreen !! it took #green%.2f#lightgreen seconds !!" % (getPlayerName(userid), trickName(name, players[userid]['trick_count']), trick_total_time))

def trickName(name, count):
	if count > 1:
		return "%s x%s" % (name, count)
	return name

def compareList(pathlist, passlist, userlist):
	if len(pathlist) > len(userlist): return -2
	delta=int("-%s" % len(pathlist))

	# a userlist may not end in a passlist item
	if userlist[-1] in passlist:
		return -3

	#
	# compareList v3
	# 
	# This functions job is to see if pathlist is on the end of userlist.
	# However, this time we have a pass list.
	#

	newlist=[]
	for point in userlist:
		if not point in passlist:
			# This is a required point
			newlist.append(point)

	if newlist[delta:] == pathlist:	return 1
	return -2

def loadConfig():
	global triggers
	global tricks
	es.msg("loading configuration")
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
	for line in lines:
		m=re.match("^(\w+)", line)
		if not m: continue
		[type]=m.groups()

		# Symetrical Triggers
		# These are written for the terrorist side first and automatically doubled for the ct side.
		#trig_sym	51	-500,-8800,-1600	100,-8300,-1400		awp box
		# [id, name, [x1,y1,z1], [x2,y2,z2] ]
		if type == "trig_sym":
			m=re.match("trig_sym\t+(\d+)\t+(.*?)\t+(.*?)\t+(.*)", line)
			if not m: continue
			[id, c1, c2, name]=m.groups()

			[x1,y1,z1]=c1.split(',')
			[x2,y2,z2]=c2.split(',')

			[x1, x2]=autoswitch(x1, x2)
			[y1, y2]=autoswitch(y1, y2)
			[z1, z2]=autoswitch(z1, z2)

			# Add the first box (T)
			triggers.append([id, name, [x1, y1, z1], [x2, y2, z2]])

			# Add the second box (CT)
			[y1, y2]=[y2, y1]
			#  and make them positive.
			y1=pn_flip(y1)
			y2=pn_flip(y2)
			triggers.append([id, name, [x1, y1, z1], [x2, y2, z2]])

		# Triggers (First Generation)
		#trigger		8	-1050,0,6000		-1800,-250,5900		terrorist spawn
		# [id, name, [x1,y1,z1], [x2,y2,z2] ]
		if type == "trigger":
			m=re.match("trigger\t+(\d+)\t+(.*?)\t+(.*?)\t+(.*)", line)
			if not m: continue
			[id, point1, point2, name]=m.groups()
			[x1, y1, z1]=re.split(',', point1)
			[x2, y2, z2]=re.split(',', point2)

			[x1, x2]=autoswitch(x1, x2)
			[y1, y2]=autoswitch(y1, y2)
			[z1, z2]=autoswitch(z1, z2)

			triggers.append([id, name, [x1, y1, z1], [x2, y2, z2]])

		# Tricks (Second Generation)
		# Same as before except these now have a pass through element that players are allowed to touch.
		#trickv2		1,54,52					-					400		hop to under 2nd to awp
		# [pathlist, passlist, points, name]
		if type == "trickv2":
			m=re.match("trickv2\t+(.*?)\t+(.*?)\t+(\d+)\t+(.*)", line)
			if not m: continue
			[path, passthru, points, name]=m.groups()

			pathlist=path.split(',')
			if passthru == "-":	passlist=[]
			else:			passlist=passthru.split(',')
			tricks.append([pathlist, passlist, points, name])

	for trigger in triggers:
		print "found trigger %s" % trigger
	for trick in tricks:
		print "found trick %s" % trick

	return "found %s triggers, %s tricks" % (len(triggers), len(tricks))

def getTriggerName(i):
	for box in triggers:
		if box[0] == i: return box[1]
	return "error"

def getTrigger(px, py, pz):
	# check each defined trigger to see if xyz matches and return the triggers id
	for trigger in triggers:
		[id, name, coord1, coord2]=trigger
		[x1,y1,z1]=coord1
		[x2,y2,z2]=coord2
		if (px > int(x1) and px < int(x2)) or (px > int(x2) and px < int(x1)):
			if (py > int(y1) and py < int(y2)) or (py > int(y2) and py < int(y1)):
				if (pz > int(z1) and pz < int(z2)) or (pz > int(z2) and pz < int(z1)):
					return id
	return -1

def load():
	loadConfig()
	es.addons.registerSayFilter(sayFilter)
	gamethread.delayedname(rate, 'timer1', timer)
	es.msg("ztricks loaded")

def unload():
	r=gamethread.cancelDelayed('timer1')
	es.msg("disabling timer: %s" % r)
	es.addons.unregisterSayFilter(sayFilter)
	es.msg("ztricks unloaded")

def sayFilter(userid, text, teamOnly):
	text_noquote = text.strip('"')
	words = text_noquote.split(" ")
	cmd = words[0].lower()

	if cmd in ['rank', '!rank', '!score']:
		es.msg("#lightgreen", "%s has %s points!" % (getPlayerName(userid), players[userid]['points']))
		return (0, "", 0)

	if cmd == "!info":
		if len(words) == 1:
			es.tell(userid, "#lightgreen", "usage: !info awp2awp")
			return (0, "", 0)
		tmp=text_noquote.split("!info ")
		req=tmp[1]
		print "!info called with [%s]" % req
		# find the trick with that name
		for box in tricks:
			[pathlist, path, points, name]=box
			if name == req:
				# create a string for each path
				namelist=[]
				for p in pathlist:
					namelist.append(getTriggerName(p))
				es.tell(userid, "#lightgreen", "[ztricks] trick %s is %s" % (req, " -> ".join(namelist)) )
				return (0, "", 0)
		es.tell(userid, "#lightgreen", "[ztricks] unknown trick %s" % req)
		return (0, "", 0)

	if cmd == "!drawbox":
		es.msg("drawing..")
		for trigger in triggers:
			[id, name, coord1, coord2]=trigger
			[x1,y1,z1]=coord1
			[x2,y2,z2]=coord2
			#drawline([x1,y1,z1], [x1,y2,z1])
			drawline([x1,y2,z1], [x2,y2,z1])
			#drawline([x2,y2,z1], [x2,y1,z1])
			#drawline([x2,y1,z1], [x1,y1,z1])

			#drawline([x1,y1,z2], [x1,y2,z2])
			#drawline([x1,y2,z2], [x2,y2,z2])
			#drawline([x2,y2,z2], [x2,y1,z2])
			drawline([x2,y1,z2], [x1,y1,z2])

			#drawline([x1,y1,z1], [x1,y1,z2])
			#drawline([x1,y2,z1], [x1,y2,z2])
			#drawline([x2,y1,z1], [x2,y1,z2])
			#drawline([x2,y2,z1], [x2,y2,z2])
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
		show_draw_menu(userid)
		return (0,'',0)

	if cmd == "!reload":
		es.msg("reloading configuration")
		es.msg(loadConfig())
		return (0, "", 0)

	return (userid, text, teamOnly)

def drawmenuselect (userid, choice, popupid):
	#print "drawmenuselect() called"
	#print "- userid=%s choice=%s popupid=%s" % (userid,choice,popupid)

	for trigger in triggers:
		[id, name, coord1, coord2]=trigger
		if not name == choice: continue
		[x1,y1,z1]=coord1
		[x2,y2,z2]=coord2

		drawline([x1,y1,z1], [x1,y2,z1])
		drawline([x1,y2,z1], [x2,y2,z1])
		drawline([x2,y2,z1], [x2,y1,z1])
		drawline([x2,y1,z1], [x1,y1,z1])

		drawline([x1,y1,z2], [x1,y2,z2])
		drawline([x1,y2,z2], [x2,y2,z2])
		drawline([x2,y2,z2], [x2,y1,z2])
		drawline([x2,y1,z2], [x1,y1,z2])

		drawline([x1,y1,z1], [x1,y1,z2])
		drawline([x1,y2,z1], [x1,y2,z2])
		drawline([x2,y1,z1], [x2,y1,z2])
		drawline([x2,y2,z1], [x2,y2,z2])

def show_draw_menu(userid):
	myPopup = popuplib.easymenu('example_menu',None, drawmenuselect)
	myPopup.settitle("Select trigger:")

	dupe=[]
	for trigger in triggers:
		[id, name, coord1, coord2]=trigger
		if id in dupe: continue
		dupe.append(id)
		myPopup.addoption(name, "%s (%s)"%(name,id))

	myPopup.send(userid)

def drawline(coord1, coord2):
	effectlib.drawLine(coord1, coord2, model="materials/sprites/laser.vmt", halo="materials/sprites/halo01.vmt", seconds=120, width=5, red=255, green=255, blue=255)

def getPlayerCoords(userid):
	myPlayer = playerlib.getPlayer(userid)
	return [myPlayer.attributes['x'], myPlayer.attributes['y'], myPlayer.attributes['z']]

def givePlayerPoints(userid, points):
	players[userid]['points'] = players[userid]['points'] + int(points)

def player_spawn(ev):
	playerTriggerReset(ev['userid'])

def player_death(ev):
	playerTriggerReset(ev['userid'])

def check_keys(userid):
	global players
	if not players.has_key(userid):
		print "check_keys creating %s" % userid
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
	thePlayer = playerlib.getPlayer(userid)
	return thePlayer.attributes['name']

def autoswitch(a, b):
	if (int(a) + 100000) < (int(b) + 100000): return [b, a]
	return [a, b]

def pn_flip(i):
	if int(i) < 0:
		m=re.match("\-(.*)", i)
		if m:	[i]=m.groups()
	elif int(i) > 0:
		i=-i
	return i
