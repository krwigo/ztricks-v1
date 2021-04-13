import sys, es, os, re, playerlib, gamethread, effectlib, urllib, time, popuplib, vecmath, math, sets, shutil, thread, ConfigParser, traceback
from time import strftime #strftime("%Y-%m-%d %H:%M:%S")

ver=20
our_dir=es.getAddonPath('ztricks-core')
hard_timelimit=1240049290

players={}

trickdata={}
triggerdata={}

trickwrite=0
triggerwrite=0

allow_disable=1

##############################################################################
# Main Flow
##############################################################################

def timer():
	#_func_start=time.time()

	global write_triggers
	global write_tricks
	global triggers
	global tricks
	global players

	try:
		for userid in playerlib.getUseridList("#alive"):
			check_keys(userid)
			[x,y,z]=es.getplayerlocation(userid)
			player_velocity=getPlayerVelocity(userid)
	
			# Find the _first_ trigger that the player is in
			found=0
			id=0
			for name in triggerdata:
				if found > 0: break
				if trigger(name, 'bEnabled') != True: continue
	
				id=trigger(name,'iId')
				shape=trigger(name,'sShape')
	
				if shape == 'box':
					if trigger_box(userid, name, x, y, z) == 1: found = 1
				elif shape == 'sphere':
					if trigger_sphere(userid, name, x, y, z) == 1: found = 1
	
			if found > 0:
				if getPlayerLastTrigger(userid) == id:
					players[userid]['leave_trigger_time'][-1] = time.time()
				else:
					players[userid]['leave_trigger_time'].append( time.time() )
					foundTrigger(userid, shape, name, id, x, y, z, player_velocity)

	except:
		vlog("exception during timer")
		print_exception()

	checkwrite()
	gamethread.delayedname(0.001, 'timer1', timer)
	#if isDev(): print "benchmark timer() took %.10f seconds" % (time.time() - _func_start)

def foundTrigger(userid, trigger_shape, trigger_name, trigger_id, x, y, z, player_velocity):
	global write_triggers
	global write_tricks
	global triggers
	global tricks
	
	vlog("foundTrigger()")
	
	if len(players[userid]['tricklist']) > 0:	last_trick_id=players[userid]['tricklist'][-1]
	else:						last_trick_id=-1

	playerTriggerAdd(userid, trigger_id)

	# Fire the event
	es.event("initialize", 'ontrigger')
	es.event("setstring", 'ontrigger', 'userid',		userid)
	es.event("setstring", 'ontrigger', 'trigger_id',	trigger_id)
	es.event("setstring", 'ontrigger', 'trigger_name',	trigger_name)
	es.event("setstring", 'ontrigger', 'player_velocity',	player_velocity)
	es.event("setstring", 'ontrigger', 'player_mph',	player_velocity / 26)
	es.event("setstring", 'ontrigger', 'player_angle',	getPlayerAngle(userid))
	es.event("fire", 'ontrigger')

	# If it's impossible to do x2+ then add an empty to the players tricklist
	if last_trick_id >= 0:
		if not trigger_id in trick( idToTrick(last_trick_id), 'lPath'):
			players[userid]['tricklist'].append(-19)

	# Find the trick that matches
	best_name=None
	best_path=[]
	
	for name in trickdata:
		if not trick(name, 'bEnabled'): continue
		trickpath=trick(name, 'lPath')

		[t, angle, speed]=compareList(trickpath, trick(name, 'lPass'), userid)
		if t < 1000000: continue
		if len(best_path) >= len(trickpath): continue

		best_angle=angle
		best_speed=speed
		best_t=t
		best_path=trickpath
		best_name=name

		# turn speed[list] into number
		speed_total=0
		speed_velocity=0
		for x in speed:
			speed_total += x
			speed_velocity += x
		if speed_total > 0:
			speed_total = (speed_total / len(speed)) / 26
			speed_velocity = (speed_total / len(speed))

	if best_name != None:
		foundTrick(userid, best_name, trigger(best_name, 'iId'), best_t, best_angle, speed_total, best_path, speed_velocity)

	# 2009 04 13 - reset combo on some triggers
	if trigger(name, 'bEndCombo'):
		endCombo(userid)
		return

def foundTrick(userid, trick_name, trick_id, time_first, angles, speed, pathlist, speed_velocity):
	global write_triggers
	global write_tricks
	global triggers
	global tricks
	global players
	
	vlog("foundTrick()")
	
	angle=anglesToAngle(angles)
	trick_total_time=getTrickTime(userid, pathlist)
	
	if len(players[userid]['tricklist']) == 0:
		# First trick, =1
		players[userid]['trick_count'] = 1
		players[userid]['_trick_time'] = time_first

		# make a new item
		players[userid]['combolist'].append('null')

	elif players[userid]['tricklist'][-1] == trick_id and angle == players[userid]['lastangle']:
		players[userid]['trick_count'] += 1

	else:
		# This is the first of the trick they have done. =1
		players[userid]['trick_count'] = 1
		players[userid]['_trick_time'] = time_first

		# make a new item
		players[userid]['combolist'].append('null')


	players[userid]['lastangle'] = angle
	seconds=time.time() - players[userid]['_trick_time']

	# special awp counter +1
	if trick_name == "awp" and players[userid]['trick_count'] == 1: players[userid]['trick_count']=2

	players[userid]['tricklist'].append(trick_id)
	trick_name_full=trickName(trick_name, players[userid]['trick_count'], angle)
	players[userid]['combolist'][-1] = trick_name_full
	
	# Fire the event
	es.event("initialize", 'ontrick')
	es.event("setstring", 'ontrick', 'userid',	userid)
	es.event("setstring", 'ontrick', 'trick_id',	trick_id)
	es.event("setstring", 'ontrick', 'trick_short', trick_name)
	es.event("setstring", 'ontrick', 'trick_name',	trick_name_full)
	es.event("setstring", 'ontrick', 'trick_speed',	speed)
	es.event("setstring", 'ontrick', 'trick_speed_velocity', speed_velocity)
	es.event("setstring", 'ontrick', 'trick_angle', angle)
	es.event("setstring", 'ontrick', 'trick_time',	seconds)
	es.event("fire", 'ontrick')
	
def timer4():
	global players
	# Detect the end of combos by no movement
	for userid in playerlib.getUseridList("#alive"):
		check_keys(userid)
		if getPlayerVelocity(userid) < 10:
			if players[userid]['is_moving'] == 1: endCombo(userid)
			players[userid]['is_moving'] = 0
		else:
			players[userid]['is_moving'] = 1

	# endCombo for dead people too!
	for userid in playerlib.getUseridList("#dead"):
		check_keys(userid)
		if players[userid]['is_moving'] == 1:
			endCombo(userid)
			players[userid]['is_moving'] = 0

	gamethread.delayedname(0.01, 'timer4', timer4)

def endCombo(userid):
	global players
	check_keys(userid)
	
	# Turn ids into names
	list=[]
	for key in players[userid]['combolist']:
		#if key != 'null':
		list.append(key)
	if list == []:
		# this makes spawn hop work !!!!
		playerReset(userid)
		return

	vlog("endCombo player->%s list->%s" % (players[userid]['combolist'], list))

	# Fire event
	es.event("initialize", 'oncombo')
	es.event("setstring", 'oncombo', 'userid',	userid)
	es.event("setstring", 'oncombo', 'list',	"::".join(list))
	es.event("fire", 'oncombo')
	
	# Clear trigger and trick lists
	playerReset(userid)

##############################################################################
# Configuration Handling
##############################################################################

def checkwrite():
	global triggerdata
	global triggerwrite
	global trickdata
	global trickwrite

	if trickwrite == 1:
		fh=open("%s/tricks.cfg", our_dir)
		for section in trickdata:
			fh.write("%s\r\n" % section)
			for key in trickdata[section]:
				fh.write("%s=%s\r\n" % (key, trickdata[section][key]))
		fh.close()
		trickwrite=0

	if triggerwrite == 1:
		fh=open("%s/triggers.cfg", our_dir)
		for section in triggerdata:
			fh.write("%s\r\n" % section)
			for key in triggerdata[section]:
				fh.write("%s=%s\r\n" % (key, triggerdata[section][key]))
		fh.close()
		triggerwrite=0

def loadConfig():
	global trickdata
	global triggerdata

	trickdata={}
	triggerdata={}

	if time.time() > hard_timelimit:
		msg("Impossible to continue because I hate you.")
		return

	## Triggers
	try:
		fh=open("%s/triggers.cfg", our_dir)
		vlog("opening triggers")
		lines=fh.readlines()
		section='no_section'
		for line in lines:
			m=re.match('[(.*)]', line)
			if m:
				[section] = m.groups()
				vlog("found section ->%s<-" % section)
				continue
	
			m=re.match('(.*?)\s*=\s*(.*)', line)
			if m:
				[key, value] = m.groups()
				if not triggerdata.has_key(section): triggerdata[section]={}
				triggerdata[section][key]=value
				vlog("read key->[%s] value->[%s]" % (key, value))
		fh.close()
	except:
		msg("Error while reading triggers")

	## Tricks
	try:
		fh=open("%s/tricks.cfg", our_dir)
		vlog("opening tricks")
		lines=fh.readlines()
		section='no_section'
		for line in lines:
			m=re.match('[(.*)]', line)
			if m:
				[section] = m.groups()
				vlog("found section ->%s<-" % section)
				continue
	
			m=re.match('(.*?)\s*=\s*(.*)', line)
			if m:
				[key, value] = m.groups()
				if not trickdata.has_key(section): trickdata[section]={}
				trickdata[section][key]=value
				vlog("read key->[%s] value->[%s]" % (key, value))
		fh.close()
	except:
		msg("Error while reading tricks")

	msg("found %s triggers and %s tricks" % ( len(triggerdata), len(trickdata) ))

def trigger(section, key, value=None):
	global triggerdata
	global triggerwrite
	
	if value:
		if not triggerdata.has_key(section): triggerdata[section]={}
		triggerdata[section][key]=value
		triggerwrite=1
		return

	try:	value = triggerdata[section][key]
	except: value = None

	newv = typing(key, value)
	if newv != value:
		# store the value so we don't have to calculate again
		triggerdata[section][key] = value
		triggerwrite=1

	# return the value requested
	return newv

def typing(key, value):
	if key.startswith('i') and type(value) != int:
		try:	value=int(value)
		except:	value=int(0)
	elif key.startswith('b') and type(value) != bool:
		try:	value=bool(value)
		except:	value=bool(False)
	elif key.startswith('f') and type(value) != float:
		try:	value=float(value)
		except:	value=float(0)
	elif key.startswith('l') and type(value) != list:
		try:
			# remove all non numbers
			value = re.sub('([^0-9\-\,])', '', value)
			# remove pre/post ,
			value = re.sub('(?:^^,|,$$)', '', value)
			
			temp = value.split(',')
			i = 0
			for t in temp:
				if isInt(t): temp[i] = int(temp[i])
				i += 1
			value = temp
		except:
			value=[]
	return value

def trick(section, key, value=None):
	global trickdata
	global trickwrite
	if value:
		if not trickdata.has_key(section): trickdata[section]={}
		trickdata[section][key]=value
		trickwrite=1
		return

	try:	value = trickdata[section][key]
	except: value = None

	newv = typing(key, value)
	if newv != value:
		# store the value so we don't have to calculate again
		trickdata[section][key] = value
		trickwrite=1

	# return the value requested
	return newv

##############################################################################
# Common Functions
##############################################################################

def getPlayerLastTrigger(userid):
	if len(players[userid]['triggerlist']) > 0:
		return players[userid]['triggerlist'][-1]

def timer2():
	return
	gamethread.delayedname(0.5, 'timer2', timer2)

def timer3():
	return
	gamethread.delayedname(0.1, 'timer3', timer3)

def isDev():
	return os.path.exists("%s/is_dev_server.txt" % our_dir)
	
def sayFilter(userid, text, teamOnly):
	if text.lower() == "!reset":
		endCombo(userid)
		return (0, '', 0)
		
	return (userid, text, teamOnly)
	
def check_keys(userid):
	global players
	if not players.has_key(userid):
		vlog("creating new key for %s" % userid)
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

		players[userid]['_trick_time']=0
		
		players[userid]['lastangle']=''
		players[userid]['lasttrick']=''
		players[userid]['combolist']=[]

		players[userid]['triggerlist']=[]
		players[userid]['triggertimes']=[]
		players[userid]['triggerangles']=[]
		players[userid]['triggerspeeds']=[]
		
		players[userid]['leave_trigger_time']=[]
		
		players[userid]['is_moving']=0

def getDist(c1, c2):
	return vecmath.distance(c1, c2)
	
def getAngle(a,b,c):
	return math.degrees(math.acos(((b**2)+(c**2)-(a**2))/(2*b*c)))

def vlog(text):
	try:
		file=open("%s/vlog.txt" % our_dir, 'a')
		file.write("%s %s\r\n" % (time.time(), text))
		file.close()
	except:
		print "### Failed to open file ###"

	if isDev():
		print "vlog: %s" % text
	
def msg(text):
	vlog("msg(): %s" % text)
	es.msg('#multi', "#green[ztricks-core]#default %s" % text)

def isInt(input):
	try:	return int(input)
	except: pass

def isBool(input):
	try:	return bool(input)
	except:
		print_exception()

def idToTrick(id):
	for key in trickdata:
		if trick(key, 'iId') == int(id):
			return key
	
def getTrickTime(userid, pathlist):
	# Return the amount of seconds it took to complete the trick for this player
	delta=int("-%s" % len(pathlist))
	return players[userid]['triggertimes'][-1] - players[userid]['triggertimes'][delta]

def anglesToAngle(angles):
	s = sets.Set(angles)
	angle=s.pop()
	if len(s) == 1 and not angle == "forward":	return angle
	else:						return "forward"

def trickName(name, count, angle):
	# 20090315 - see if they did it all one way
	if not angle == "forward":
		if count > 1:	return "%s %s x%s" % (angle, name, count)
		else:		return "%s %s" % (angle, name)
	else:
		if count > 1:	return "%s x%s" % (name, count)
		else:		return name

def compareList(pathlist, passlist, userid):
	# return -1		if the user did not do the pathlist
	# return time		return the first time in the delta list

	userlist=players[userid]['triggerlist']
	usertime=players[userid]['triggertimes']
	userangle=players[userid]['triggerangles']
	userspeed=players[userid]['triggerspeeds']

	if len(pathlist) > len(userlist): return [-1, -1, -1]
	delta=int("-%s" % len(pathlist))
	#delta = len(pathlist) * -1

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

	if newlist[delta:] == pathlist:	return [ players[userid]['leave_trigger_time'][delta] , newangle[delta:] , newspeed[delta:] ]
	else:				return [-3, -3, -3]

	#if newlist[delta:] == pathlist:	return [ newtime[delta:][0] , newangle[delta:] , newspeed[delta:] ]
	#else:				return [-3, -3, -3]

def getTrickName(id):
	for name in trickdata:
		if trick(name, 'iId') == id: return name
	return

def trigger_box(userid, name, x, y, z):
	c1x=trigger(name, 'fCoord1_x')
	c1y=trigger(name, 'fCoord1_y')
	c1z=trigger(name, 'fCoord1_z')

	c2x=trigger(name, 'fCoord2_x')
	c2y=trigger(name, 'fCoord2_y')
	c2z=trigger(name, 'fCoord2_z')

	if c1x == 0 and c1y == 0 and c1z == 0:
		disableTrigger(name, "Coordinate 1 is empty")
		return

	if c2x == 0 and c2y == 0 and c2z == 0:
		disableTrigger(name, "Coordinate 2 is empty")
		return

	# Honor wasdfr
	wasdfr=gtrigger(name, 'sDirectionOnly')
	if wasdfr in ['f','r']:
		if not wasdfr == getPlayerDest(userid, 'fr'): continue
	if wasdfr in ['w','a','s','d']:
		if not wasdfr == getPlayerDest(userid, 'wasd'): continue

	# Actual Testing
	if trigger_box_single(name, c1x, c1y, c1z, c2x, c2y, c2z, x, y ,z) == 1: return 1
	if trigger(name, 'bSymetrical'): return trigger_box_single(name, c1x, c2y - (c2y * 2), c1z, c2x, c1y - (c1y * 2), c2z, x, y, z)

def trigger_box_single(name, c1x, c1y, c1z, c2x, c2y, c2z, x, y, z):
	# Determine if in the box
	if (x > c1x and x < c2x) or (x > c2x and x < c1x):
		if (y > c1y and y < c2y) or (y > c2y and y < c1y):
			if (z > c1z and z < c2z) or (z > c2z and z < c1z):
				return 1

def disableTrigger(name, reason=None):
	if allow_disable == 0:
		vlog("Disable trigger request denied (allow_disable = 0) name->%s reason->%s" % (name, reason))

	msg("Disabled trigger name->%s reason->%s" % (name, reason))
	trigger(name, 'bEnabled', False)

def disableTrick(name, reason=None):
	if allow_disable == 0:
		vlog("Disable trick request denied (allow_disable = 0) name->%s reason->%s" % (name, reason))

	msg("Disabled trick name->%s reason->%s" % (name, reason))
	trigger(name, 'bEnabled', False)

def trigger_sphere(userid, name, x, y, z):
	basex=trigger(name, 'fCoord1_x')
	basey=trigger(name, 'fCoord1_y')
	basez=trigger(name, 'fCoord1_z')

	if basex == 0 and basey == 0 and basez == 0:
		disableTrigger(name, "Coordinate 1 is empty")
		return

	radius=trigger(name, 'fRadius')
	if radius == 0:
		disableTrigger(name, "No radius")
		return
	
	height=trigger(name, 'fHeight')
	if height == 0:
		height=radius
		trigger(name, 'fHeight', height)

	# Honor height restriction
	if z < (basez - height) or z > (basez + height): return

	# Actual Distance
	if getDist([basex,basey,basez], [x,y,z]) <= radius: return 1
	if trigger(name, 'bSymetrical'):
		if getDist([basex, basey - (basey * 2) ,basez], [x,y,z]) <= radius: return 1
	
def trigger_awpmain(userid, name, x, y, z):
	return
	
##############################################################################################################
# EVENTS
##############################################################################################################
def player_spawn(ev):
	userid = ev['userid']
	endCombo(userid)

def player_death(ev):
	userid = ev['userid']
	endCombo(userid)

def zreload():
	loadConfig()
	
def player_say(ev):
	if ev['text'].lower() == "!version":
		msg("Version %s" % ver)

def load():
	vlog("load() called")
	try:
		loadConfig()
		es.loadevents('declare', "%s/ztricks-core.res" % our_dir)
		#es.addons.registerSayFilter(sayFilter)

		#gamethread.delayedname(rate, 'timer1', timer)
		timer()
		timer2()
		timer3()
		timer4()
		
	        es.regclientcmd("zdrawmenu", 'ztricks-core/sendMenu')
	        es.regclientcmd("zreload", 'ztricks-core/zreload')

		msg("loaded v%s" % ver)
	except:
		msg("FATAL DURING LOAD")
		print_exception()
	vlog("load() ended")

def unload():
	vlog("unload() called")

	gamethread.cancelDelayed('timer1')
	gamethread.cancelDelayed('timer2')
	gamethread.cancelDelayed('timer3')
	gamethread.cancelDelayed('timer4')
	#es.addons.unregisterSayFilter(sayFilter)

        es.unregclientcmd("zdrawmenu")
        es.unregclientcmd("zreload")

	msg("unloaded")
	vlog("unload() ended")

##############################################################################################################
# COMMON FUNCTIONS
##############################################################################################################
def playerReset(userid):
	# If a player dies their trigger lists are reset here.
	global players

	check_keys(userid)

	players[userid]['triggerlist'] = []
	players[userid]['triggertimes'] = []
	players[userid]['triggerangles'] = []
	players[userid]['triggerspeeds'] = []
	players[userid]['combolist'] = []
	players[userid]['tricklist'] = []

def playerTriggerAdd(userid, triggerindex):
	# When a player touches a trigger, this function records the trigger, time, and angles
	# so that when a trick is completed, these values can be checked to validate.
	global players

	check_keys(userid)

	players[userid]['triggerlist'].append( triggerindex )
	players[userid]['triggertimes'].append( time.time() )
	players[userid]['triggerangles'].append( getPlayerAngle(userid) )
	players[userid]['triggerspeeds'].append( getPlayerVelocity(userid) )

def getPlayerVelocity(userid):
	x=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[0]')
	y=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[1]')
	z=es.getplayerprop(userid,'CBasePlayer.localdata.m_vecVelocity[2]')
	return math.sqrt(x*x + y*y + z*z)

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

def getPlayerAngle_test(userid):
	
	look=getPlayerLook(userid)
	move=getPlayerDest(userid)

	if look > 180: look=360 - look
	if move > 180: move=360 - move

	alpha=look - move
	beta=move - look
	
	if alpha > 0:	perc=alpha
	else:		perc=beta
	
	msg("localized perc->#lightgreen%s#default" % perc)

	#look += 10000
	#move += 10000

	if perc < 22.5:		return "forward"
	elif perc < 67.5:	return "halfsideways"
	elif perc < 112.5:	return "sideways"
	elif perc < 157.5:	return "halfsideways"
	else:					return "backwards"

	return
	if plusminus(look, move, 22.5):		return "forward"
	elif plusminus(look, move, 67.5):	return "halfsideways"
	elif plusminus(look, move, 112.5):	return "sideways"
	elif plusminus(look, move, 157.5):	return "halfsideways"
	else:					return "backwards"

def getPlayerAngle(userid):
	look=getPlayerLook(userid)
	move=getPlayerDest(userid)
	
	if look > move:	diff = look - move
	else:		diff = move - look
	
	if (diff < 22.5):	return "forward"
	elif (diff < 67.5):	return "halfsideways"
	elif (diff < 112.5):	return "sideways"
	elif (diff < 157.5):	return "halfsideways"
	elif (diff < 202.5):	return "backwards"
	elif (diff < 247.5):	return "halfsideways"
	elif (diff < 292.5):	return "sideways"
	elif (diff < 337.5):	return "halfsideways"
	else:			return "forward"

def getPlayerAngle_orig(userid):
	look=getPlayerLook(userid) + 10000
	move=getPlayerDest(userid) + 10000
	if plusminus(look, move, 22.5):		return "forward"
	elif plusminus(look, move, 67.5):	return "halfsideways"
	elif plusminus(look, move, 112.5):	return "sideways"
	elif plusminus(look, move, 157.5):	return "halfsideways"
	else:					return "backwards"

def drawtrigger(userid, name):
	shape=trigger(name, 'sShape')
	
	if shape == 'box':
		c1x=trigger(name, 'fCoord1_x')
		c1y=trigger(name, 'fCoord1_y')
		c1z=trigger(name, 'fCoord1_z')
		c2x=trigger(name, 'fCoord2_x')
		c2y=trigger(name, 'fCoord2_y')
		c2z=trigger(name, 'fCoord2_z')

		drawbox([c1x,c1y,c1z], [c2x,c2y,c2z])
		if trigger(name, 'bSymetrical'): drawbox([c1x,c2y - (c2y * 2),c1z], [c2x,c1y - (c1y * 2),c2z])

	elif shape == 'sphere':
		radius=trigger(name, 'fRadius')
		height=trigger(name, 'fHeight')
		if height == 0: height = radius

		c1x=trigger(name, 'fCoord1_x')
		c1y=trigger(name, 'fCoord1_y')
		c1z=trigger(name, 'fCoord1_z')

		# First
		drawcircle([c1x,c1y,c1z + height], radius, 'z', 4)
		drawcircle([c1x,c1y,c1z - height], radius, 'z', 4)
		drawcircle([c1x,c1y,c1z], radius, 'x')
		drawcircle([c1x,c1y,c1z], radius, 'y')

		# Second
		if trigger(name, 'bSymetrical'):
			c1y=c1y - (c1y * 2)
			drawcircle([c1x,c1y,c1z + height], radius, 'z', 4)
			drawcircle([c1x,c1y,c1z - height], radius, 'z', 4)
			drawcircle([c1x,c1y,c1z], radius, 'x')
			drawcircle([c1x,c1y,c1z], radius, 'y')

	else:
		msg("unsupported type!")
	
def drawline(coord1, coord2):
	effectlib.drawLine(coord1, coord2, model="materials/sprites/laser.vmt", halo="materials/sprites/halo01.vmt", seconds=120, width=5, red=255, green=255, blue=255)

def drawcircle(origin, radius, axle='z', s=12, t=30):
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

	effectlib.drawCircle(origin, float(radius), steps=s, axle1=a1, axle2=a2, seconds=t)

def drawbox(coord1, coord2, secs=30):
	effectlib.drawBox(coord1, coord2, model="materials/sprites/laser.vmt", halo="materials/sprites/halo01.vmt", seconds=secs, width=5, red=255, green=255, blue=255)

def gpn(userid):
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
	"""
	# calculate and return an array coordinate of the center
	# get coords

	if shape == "trig_sphere" or shape == "trig_sphere_sym":
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
	"""

def plusminus(master, slave,offset=22.5):
	if slave > (master - offset) and slave < (master + offset): return True

def print_exception():
	vlog("exception!!")
	#vlog(traceback.format_exception)

	formatted_lines = traceback.format_exc().splitlines()
	for line in formatted_lines:
		vlog("EX: %s" % line)

def sendMenu():
	userid = es.getcmduserid()
	
	# send a draw menu so we can draw triggers
	myPopup = popuplib.easymenu("draw menu for %s" % userid, None, drawSelect)
	myPopup.settitle("draw")

	for name in triggerdata:
		myPopup.addoption("drawtrigger:%s" % name, "%s id->%s type->%s" % (name, trigger(name, 'iId'), trigger(name, 'sShape')))

	myPopup.send(userid)

def drawSelect (userid, choice, popupid):
	[n, name] = choice.split(":")
	try:
		drawtrigger(userid, name)
	except:
		msg("there was an unknown error")
		print_exception()

	
	
	
	
	
	
	
	
	
	
	
	
	