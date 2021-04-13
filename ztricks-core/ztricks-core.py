import sys, es, os, re, playerlib, gamethread, effectlib, urllib, time, popuplib, vecmath, math, sets, shutil, thread, ConfigParser, traceback
from time import strftime #strftime("%Y-%m-%d %H:%M:%S")

ver=18
our_dir=es.getAddonPath('ztricks-core')
hard_timelimit=1240049290

players={}

trick_data={}
trigger_data={}

trick_write=0
trigger_write=0

allow_disable=1


#
# Main Flow
#

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
			for name in trigger_data:
				if found > 0: break
				if getTrigger(name, 'enabled', 1) != 1: continue
	
				id=getTrigger(name,'id')
				shape=getTrigger(name,'shape')
	
				if shape == 'box':
					if trigger_box(userid, name, x, y, z) == 1:
						found = 1
						break
	
				if shape == 'sphere':
					if trigger_sphere(userid, name, x, y, z) == 1:
						found = 1
						break
	
			if found > 0:
				if getPlayerLastTrigger(userid) == id:
					#vlog("updating time for player on the last trigger..")
					players[userid]['leave_trigger_time'][-1] = time.time()
				else:
					players[userid]['leave_trigger_time'].append(id)
					#vlog("found trigger %s for player %s" % (name, gpn(userid)))
					foundTrigger(userid, shape, name, id, x, y, z, player_velocity)
	except:
		vlog("exception during timer")
		pass

	check_write()
	gamethread.delayedname(0.001, 'timer1', timer)
	#if isDev(): print "benchmark timer() took %.10f seconds" % (time.time() - _func_start)

def getPlayerLastTrigger(userid):
	if len(players[userid]['triggerlist']) > 0:
		return players[userid]['triggerlist'][-1]

"""
			#if len(players[userid]['triggerlist']) > 0:
			#	if players[userid]['triggerlist'][-1] == id:
			#		break

				### FIXME: removed due to massive lag
				### it MUST be caused by getTrigger? it exceptions
				### enabling getTrigger costs .0004 seconds of lag
				
				# honor speed min and max
				#speed_min=getTrigger(name, 'speed_min')
				#if speed_min:
				#	print "1"
				#	if player_velocity < speed_min:
				#		continue

				#speed_max=getTrigger(name, 'speed_max')
				#if speed_max:
				#	print "2"
				#	if player_velocity > speed_max:
				#		continue
				
				
				
			except:
				vlog("trigger %s has errors! disabling" % name)
				msg("error with trigger #green%s#default, disabling it." % name)
				#allow_disable setTrigger(name, 'enabled', False)
				print_exception()

"""

def timer3():
	return
	##
	## DISABLED
	##
	global players
	# Detect the end of combos by no movement
	for userid in playerlib.getUseridList("#alive"):
		check_keys(userid)
		[x,y,z]=es.getplayerlocation(userid)

		if x == players[userid]['x'] and y == players[userid]['y'] and z == players[userid]['z']:
			if players[userid]['is_moving'] == 1: endCombo(userid)
			players[userid]['is_moving'] = 0
		else:
			players[userid]['x']=x
			players[userid]['y']=y
			players[userid]['z']=z
			players[userid]['is_moving'] = 1
	
	# 0.01 is too fast
	gamethread.delayedname(0.1, 'timer3', timer3)

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

def timer2():
	return
	if not isDev():
		return
	
	for userid in playerlib.getUseridList("#alive"):
		es.msg("#multi", "#lightgreen%s#default Look->#green%s#default Angle->#green%s#default Dest->#green%s" % ( gpn(userid), getPlayerLook(userid), getPlayerAngle(userid), getPlayerDest(userid)   ))

	gamethread.delayedname(0.5, 'timer2', timer2)

def foundTrigger(userid, trigger_shape, trigger_name, trigger_id, x, y, z, player_velocity):
	global write_triggers
	global write_tricks
	global triggers
	global tricks
	
	if len(players[userid]['tricklist']) > 0:	last_trick_id=players[userid]['tricklist'][-1]
	else:						last_trick_id=-1

	#if len(players[userid]['triggerlist']) > 0:	last_trigger_id=players[userid]['triggerlist'][-1]
	#else:						last_trigger_id=-1
	#if last_trigger_id == trigger_id:
	#	#vlog("updating time for user %s" % gpn(userid))
	#	players[userid]['_trick_time'] = time_first
	#	return
	
	#msg("player #green%s#default is in trigger #green%s#default [%s][%s] at %s" % (userid, trigger_name, trigger_id, trigger_shape, [x,y,z]))
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
		if not trigger_id in getTrickPath(last_trick_id):
			players[userid]['tricklist'].append(-19)

	# Find the trick that matches
	best_name=None
	best_path=[]
	
	for name in trick_data:
		if not getTrick(name, 'enabled', 1) == 1:
			continue

		trickpath=getTrickPath(name)

		[t, angle, speed]=compareList(name, trickpath, getTrickPass(name), userid)
		if t < 1000000: continue
		vlog("comparelist returned t->%s a->%s s->%s" % (t,angle,speed))
		if len(best_path) >= len(trickpath): continue

		best_angle=angle
		best_speed=speed
		best_t=t
		best_path=trickpath
		best_name=name

		# turn speed[list] into number
		speed_total=0
		speed_velocity=0
		#speed_len=0
		for x in speed:
			# seems silly to average with a bunch of big numbers and a zero :/
			#if x > 5:
			speed_total += x
			speed_velocity += x
			#speed_len += 1
		if speed_total > 0:
			speed_total = (speed_total / len(speed)) / 26
			speed_velocity = (speed_total / len(speed))

	if best_name == None: return
	foundTrick(userid, best_name, getTrick(best_name, 'id'), best_t, best_angle, speed_total, best_path, speed_velocity)

def foundTrick(userid, trick_name, trick_id, time_first, angles, speed, pathlist, speed_velocity):
	global write_triggers
	global write_tricks
	global triggers
	global tricks
	global players
	
	angle=anglesToAngle(angles)
	trick_total_time=getTrickTime(userid, pathlist)

	#vlog("anglesToAngle returned %s" % angle)
	#vlog("comparing angle[%s] to lastangle[%s]" % (angle, players[userid]['lastangle']))
	
	if len(players[userid]['tricklist']) == 0:
		# First trick, =1
		players[userid]['trick_count'] = 1
		players[userid]['_trick_time'] = time_first

		# make a new item
		players[userid]['combolist'].append('null')

	elif players[userid]['tricklist'][-1] == trick_id and angle == players[userid]['lastangle']:
		players[userid]['trick_count'] += 1

		# don't make a new item, we will overwrite the last
		#players[userid]['combolist'].append('null')

	else:
		# This is the first of the trick they have done. =1
		players[userid]['trick_count'] = 1
		players[userid]['_trick_time'] = time_first

		# make a new item
		players[userid]['combolist'].append('null')


	players[userid]['lastangle'] = angle
	#vlog("updating lastangle to %s" % angle)
	
	seconds=time.time() - players[userid]['_trick_time']

	# special awp counter +1
	if trick_name == "awp" and players[userid]['trick_count'] == 1:
		players[userid]['trick_count']=2

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

#
# Common Functions
#

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

		# why did it work without this?
		#players[userid]['_trick_time']=0
		
		players[userid]['lastangle']=''
		players[userid]['lasttrick']=''
		players[userid]['combolist']=[]

		players[userid]['triggerlist']=[]
		players[userid]['triggertimes']=[]
		players[userid]['triggerangles']=[]
		players[userid]['triggerspeeds']=[]
		
		players[userid]['leave_trigger_time']=[]
		
		players[userid]['is_moving']=0

def setTrigger(section, key, value):
	global trigger_data
	global trigger_write
	try:
		trigger_data[section][key] = value
		trigger_write = 1
	except:
		vlog("settrigger exception!")
		print_exception()

def getTrigger(section, key, value=None):
	global trigger_data
	try:	return trigger_data[section][key]
	except:	return value

def setTrick(section, key, value):
	global trick_data
	global trick_write
	try:
		trick_data[section][key] = value
		trick_write = 1
	except:
		vlog("settrick exception!")
		print_exception()

def getTrick(section, key, value=None):
	global trick_data
	try:	return trick_data[section][key]
	except:	return value

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

def check_write():
	global trick_data
	global trick_write
	global trigger_data
	global trigger_write
	
	if trick_write == 1:
		raw = ConfigParser.RawConfigParser()
		for section in trick_data:
			for key in trick_data[section]:
				if not raw.has_section(section): raw.add_section(section)
				raw.set(section, key, trick_data[section][key])
				
		F=open("%s/tricks.ini" % our_dir,'wb')
		raw.write(F)
		F.close()
		
		trick_write=0

	if trigger_write == 1:
		# convert back to configparser
		raw = ConfigParser.RawConfigParser()

		for section in trigger_data:
			for key in trigger_data[section]:
				if not raw.has_section(section): raw.add_section(section)
				raw.set(section, key, trigger_data[section][key])
				
		F=open("%s/triggers.ini" % our_dir,'wb')
		raw.write(F)
		F.close()
		
		trigger_write=0

	
	"""
	global write_triggers
	global write_tricks
	global triggers
	global tricks
	
	if write_triggers == 1:
		F=open("%s/triggers.ini" % our_dir,'wb')
		if F:
			vlog("wrote trigger configuration")
			write_triggers=0
			triggers.write(F)
		else:
			vlog("unable to write triggers.ini")
		F.close()

	if write_tricks == 1:
		F=open("%s/tricks.ini" % our_dir,'wb')
		if F:
			vlog("wrote tricks configuration")
			write_tricks=0
			tricks.write(F)
		else:
			vlog("unable to write tricks.ini")
		F.close()
		"""

def isInt(input):
	try:	return int(input)
	except: pass

def isBool(input):
	try:	return bool(input)
	except:
		print_exception()
		gamethread.sleep(10)
		pass

def getTrickPath(name):
	if isInt(name):
		for key in trick_data:
			if getTrick(key, 'id') == name:
				name=key
				break
	raw="%s" % getTrick(name, 'path')
	try:
		elements=raw.split(',')
		i=0
		for e in elements:
			elements[i]=int(elements[i])
			i += 1
		return elements
	except:	return []

def getTrickPass(name):
	if isInt(name):
		for key in trick_data:
			if getTrick(key, 'id') == name:
				name=key
				break
	raw="%s" % getTrick(name, 'pass')
	try:
		elements=raw.split(',')
		i=0
		for e in elements:
			elements[i]=int(elements[i])
			i += 1
		return elements
	except: return []
	
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

def compareList(name, pathlist, passlist, userid):
	# return -1		if the user did not do the pathlist
	# return time		return the first time in the delta list

	#vlog("compareList(%s, %s, %s)" % (pathlist, passlist, userid))

	userlist=players[userid]['triggerlist']
	usertime=players[userid]['triggertimes']
	userangle=players[userid]['triggerangles']
	userspeed=players[userid]['triggerspeeds']

	if len(pathlist) > len(userlist):
		return [-1, -1, -1]
	delta=int("-%s" % len(pathlist))

	# a userlist may not end in a passlist item
	if userlist[-1] in passlist:
		return [-2, -2, -2]

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
		index += 1

	if newlist[delta:] == pathlist: return [ players[userid]['leave_trigger_time'][delta] , newangle[delta:] , newspeed[delta:] ]
	else:				return [-3, -3, -3]

	#if newlist[delta:] == pathlist: return [ newtime[delta:][0] , newangle[delta:] , newspeed[delta:] ]
	#else:				return [-3, -3, -3]

def getTrickName(id):
	for name in trick_data:
		if getTrick(name, 'id') == id:
			return name
	return

def loadConfig():
	if time.time() < hard_timelimit:

		raw = ConfigParser.RawConfigParser()
		raw.read("%s/triggers.ini" % our_dir)
		for section in raw.sections():
			for (key, value) in raw.items(section):
				if not trigger_data.has_key(section): trigger_data[section]={}
				if isInt(value): value=int(value)
				trigger_data[section][key]=value

		raw = ConfigParser.RawConfigParser()
		raw.read("%s/tricks.ini" % our_dir)
		for section in raw.sections():
			for (key, value) in raw.items(section):
				if not trick_data.has_key(section): trick_data[section]={}
				if isInt(value): value=int(value)
				trick_data[section][key]=value
	else:
		msg("*** very fatal christmas ***")
		msg("*** diff = %s            ***" % (time.time() - hard_timelimit))

	# Make sure they have an id number!
	
	for name in trick_data:
		if not getTrick(name, 'id'):
			msg("Error, trick #green%s#default does not have a proper id. Disabling it." % name)
			if allow_disable == 1: setTrick(name, 'enabled', False)

		en = getTrick(name, 'enabled', 1)
		if not isInt(en): setTrick(name, 'enabled', 1)
			
	for name in trigger_data:
		en = getTrigger(name, 'enabled', 1)
		if not isInt(en): setTrigger(name, 'enabled', 1)

		sy = "%s" % getTrigger(name, 'symetrical')
		if sy.lower() == "true": 	setTrigger(name, 'symetrical', 1)
		elif sy.lower() == "false":	setTrigger(name, 'symetrical', 0)


		# should move trigger box and sphere coord conversion to here :/
		# otherwise drawbox would fail

	msg("found #green%s#default triggers, #green%s#default tricks" % (len(trigger_data), len(trick_data)))

def coord(text):
	return text.split(',')
	
def trigger_box(userid, name, x, y, z):
	if not isInt( getTrigger(name, 'coord1', 1) ):
		coord1=coord(getTrigger(name, 'coord1'))
		coord2=coord(getTrigger(name, 'coord2'))

		setTrigger(name, 'coord1_x', coord1[0])
		setTrigger(name, 'coord1_y', coord1[1])
		setTrigger(name, 'coord1_z', coord1[2])
	
		setTrigger(name, 'coord2_x', coord2[0])
		setTrigger(name, 'coord2_y', coord2[1])
		setTrigger(name, 'coord2_z', coord2[2])

		setTrigger(name, 'coord1', 1)
		setTrigger(name, 'coord2', 1)
		return

	c1x=getTrigger(name, 'coord1_x', 0)
	c1y=getTrigger(name, 'coord1_y', 0)
	c1z=getTrigger(name, 'coord1_z', 0)

	c2x=getTrigger(name, 'coord2_x', 0)
	c2y=getTrigger(name, 'coord2_y', 0)
	c2z=getTrigger(name, 'coord2_z', 0)

	#if name == "terrorist spawn":
	#	drawbox( [c1x,c1y,c1z] , [c2x,c2y,c2z] )

	## honor wasdfr
	#wasdfr=gtrigger(name, 'wasdfr')
	#if wasdfr in ['f','r']:
	#	if not wasdfr == getPlayerDest(userid, 'fr'): continue
	#if wasdfr in ['w','a','s','d']:
	#	if not wasdfr == getPlayerDest(userid, 'wasd'): continue

	if trigger_box_single(name, c1x, c1y, c1z, c2x, c2y, c2z, x, y ,z) == 1:
		return 1

	if getTrigger(name, 'symetrical', 0) == 1:
		return trigger_box_single(name, c1x, c2y - (c2y * 2), c1z, c2x, c1y - (c1y * 2), c2z, x, y, z)


def s(secs):
	time.sleep(secs)

def trigger_box_single(name, c1x, c1y, c1z, c2x, c2y, c2z, x, y, z):

	c1x=float(c1x)
	c1y=float(c1y)
	c1z=float(c1z)

	c2x=float(c2x)
	c2y=float(c2y)
	c2z=float(c2z)
	
	x=float(x)
	x=float(x)
	x=float(x)

	# Determine if in the box
	if (x > c1x and x < c2x) or (x > c2x and x < c1x):
		if (y > c1y and y < c2y) or (y > c2y and y < c1y):
			if (z > c1z and z < c2z) or (z > c2z and z < c1z):
				return 1

def trigger_sphere(userid, name, x, y, z):
	if not isInt( getTrigger(name, 'coord1', 1) ):
		[basex,basey,basez]=coord(getTrigger(name, 'coord1'))
		setTrigger(name, 'coord1_x', basex)
		setTrigger(name, 'coord1_y', basey)
		setTrigger(name, 'coord1_z', basez)
		setTrigger(name, 'coord1', 1)
		return

	basex=getTrigger(name, 'coord1_x')
	basey=getTrigger(name, 'coord1_y')
	basez=getTrigger(name, 'coord1_z')

	radius=getTrigger(name, 'radius')
	if not radius:
		msg("Warning: no radius, disabling trigger %s" % name)
		if allow_disable == 1: setTrigger(name, 'enabled', False)
		return
	
	height=getTrigger(name, 'height')
	if height:
		# Honor height restriction
		if z < (basez - float(height)) or z > (basez + float(height)): return
	
	if getDist([basex,basey,basez], [x,y,z]) <= radius:
		return 1

	if getTrigger(name, 'symetrical', 0) == 1:
		if getDist([basex, basey - (basey * 2) ,basez], [x,y,z]) <= radius:
			return 1
	
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
	#TODO: update for new system

	shape=getTrigger(name, 'shape')
	
	if shape == 'box':
		c1x=getTrigger(name, 'coord1_x')
		c1y=getTrigger(name, 'coord1_y')
		c1z=getTrigger(name, 'coord1_z')
		c2x=getTrigger(name, 'coord2_x')
		c2y=getTrigger(name, 'coord2_y')
		c2z=getTrigger(name, 'coord2_z')

		drawbox([c1x,c1y,c1z], [c2x,c2y,c2z])

		if getTrigger(name, 'symetrical', 0) == 1:
			drawbox([c1x,c2y - (c2y * 2),c1z], [c2x,c1y - (c1y * 2),c2z])

	elif shape == 'sphere':
		radius=getTrigger(name, 'radius', 0)
		height=getTrigger(name, 'height', radius)

		c1x=getTrigger(name, 'coord1_x')
		c1y=getTrigger(name, 'coord1_y')
		c1z=getTrigger(name, 'coord1_z')

		# First
		if height:
			drawcircle([c1x,c1y,c1z + height], radius, 'z', 4)
			drawcircle([c1x,c1y,c1z - height], radius, 'z', 4)
		drawcircle([c1x,c1y,c1z], radius, 'x')
		drawcircle([c1x,c1y,c1z], radius, 'y')

		# Second
		if getTrigger(name, 'symetrical', 0) == 1:
			c1y=c1y - (c1y * 2)
			if height:
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

	for name in trigger_data:
		myPopup.addoption("drawtrigger:%s" % name, "%s id->%s type->%s" % (name, getTrigger(name, 'id'), getTrigger(name, 'shape')))

	myPopup.send(userid)

def drawSelect (userid, choice, popupid):
	[n, name] = choice.split(":")
	try:
		drawtrigger(userid, name)
	except:
		msg("there was an unknown error")
		print_exception()

	
	
	
	
	
	
	
	
	
	
	
	
	