import sys, es, os, re, playerlib, gamethread, effectlib, urllib, time, popuplib, vecmath, math, sets, shutil, thread, ConfigParser, traceback
from time import strftime #strftime("%Y-%m-%d %H:%M:%S")

ver=22
our_dir=es.getAddonPath('ztricks-core')
hard_timelimit=1240707603

players={}
allow_disable=1

data = {}
data_changed = False
configfile = "%s/ztricks3.cfg" % our_dir

clientCommands = ['zreload', 'zadminmenu', 'zcreate_trick', 'zcreate_trigger', 'zsetid_trigger', 'zsetid_trick', 'zrename_trigger', 'zrename_trick']

# - path list editing
#	**this isn't a requirement since they can add them correctly in a row :/**
#	show menu of the path
#		select index
#			select up/down
#	pathlist[index]='remove_this'
#	pathlist.remove('remove_this')
#	pathlist.insert(newindex, oldvalue)
#	???

##############################################################################
# Main Flow
##############################################################################

def cfg(master, name, key, value=None, autoCommit=True):
	global data
	global data_changed
	
	if not data.has_key(master): data[master] = {}
	if not data[master].has_key(name): data[master][name] = {}
	if not data[master][name].has_key(key): data[master][name][key] = None
	
	if value == None:
		return typing( key, data[master][name][key] )

	#vlog("cfg set %s -> %s" % (key,value))
	#vlog("- existing [%s] type: %s" % (data[master][name][key], type(data[master][name][key])))


	data[master][name][key] = typing(key, value)

	#if key.startswith("f"):
	#	vlog("cfg() running typing(%s, %s) returned [%s]" % (key,value,data[master][name][key]))

	#vlog("- updated  [%s] type: %s" % (data[master][name][key], type(data[master][name][key])))
	if autoCommit: data_changed = True
	
#def tricks():
#	global data
#	try:	return data['tricks'].keys()
#	except:	return []

def tricks():
	global data
	try:
		x=data['tricks'].keys()
		x.sort()
		return x
	except:
		return []

#def triggers():
#	global data
#	try:	return data['triggers'].keys()
#	except:	return []

def triggers():
	global data
	try:
		x=data['triggers'].keys()
		x.sort()
		return x
	except:
		return []

def typing(key, value):
	if key.startswith('i') and type(value) != int:
		try:	value=int(value)
		except:	value=int(0)
		
	elif key.startswith('b') and type(value) != bool:
		j="%s" % value
		if j.lower() == 'true' or j == '1': value=True
		else: value=False
		
	elif key.startswith('f') and type(value) != float:
		try:	value=float(value)
		except:	value=float(0)
		if value == None: value=float(0)

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
	else:
		# strings
		if value == None: value=''

	return value

def timer():
	#_func_start=time.time()

	global players
	global data_changed

	try:
		for userid in playerlib.getUseridList("#alive"):
			check_keys(userid)
			[x,y,z] = es.getplayerlocation(userid)
			player_velocity = getPlayerVelocity(userid)
	
			# Find the _first_ trigger that the player is in
			found = 0
			for name in triggers():
				if cfg('triggers', name, 'bEnabled') != True: continue
	
				id = cfg('triggers', name, 'iId')
				shape = cfg('triggers', name,'sShape')

				# Honor speed rules				
				smax = cfg('triggers', name, 'fSpeedMax')
				if player_velocity > smax and smax != 0: continue
				smin = cfg('triggers', name, 'fSpeedMin')
				if player_velocity < smin and smin != 0: continue
	
				if shape == 'box':
					if trigger_box(userid, name, x, y, z) == 1:
						found = 1
						break

				elif shape == 'sphere':
					if trigger_sphere(userid, name, x, y, z) == 1:
						found = 1
						break
	
			if found > 0:
				last_id = -21
				if len(players[userid]['triggerlist']) > 0: last_id = players[userid]['triggerlist'][-1]

				gpa = getPlayerAngle(userid)

				if last_id != id:
					players[userid]['triggerlist'].append( id )
					players[userid]['triggertimes'].append( time.time() )
					players[userid]['triggerangles'].append( gpa )
					players[userid]['triggerspeeds'].append( player_velocity )

					vlog("%s was going %s" % ( gpn(userid), gpa ))

					foundTrigger(userid, shape, name, id, x, y, z, player_velocity)
				else:
					players[userid]['triggertimes'][-1] = time.time()
					players[userid]['triggerangles'][-1] = gpa
					players[userid]['triggerspeeds'][-1] = player_velocity

	except:
		vlog("exception during timer")
		print_exception()

	if data_changed: writeconfig()
	#return
	gamethread.delayedname(0.001, 'timer1', timer)
	#if isDev(): print "benchmark timer() took %.10f seconds" % (time.time() - _func_start)

def foundTrigger(userid, trigger_shape, trigger_name, trigger_id, x, y, z, player_velocity):
	global write_triggers
	global write_tricks
	global triggers
	global tricks
	
	vlog("foundTrigger(): %s" % trigger_name)
	
	if len(players[userid]['tricklist']) > 0:	last_trick_id=players[userid]['tricklist'][-1]
	else:						last_trick_id=-1

	# Fire the event
	es.event("initialize", 'ztricks_trigger')
	es.event("setstring", 'ztricks_trigger', 'userid', userid)
	es.event("setstring", 'ztricks_trigger', 'trigger_id', trigger_id)
	es.event("setstring", 'ztricks_trigger', 'trigger_name', trigger_name)
	es.event("setstring", 'ztricks_trigger', 'player_velocity', player_velocity)
	es.event("setstring", 'ztricks_trigger', 'player_mph', player_velocity / 26)
	es.event("setstring", 'ztricks_trigger', 'player_angle', getPlayerAngle(userid))
	es.event("setstring", 'ztricks_trigger', 'player_x', x)
	es.event("setstring", 'ztricks_trigger', 'player_y', y)
	es.event("setstring", 'ztricks_trigger', 'player_z', z)
	es.event("fire", 'ztricks_trigger')

	# If it's impossible to do x2+ then add an empty to the players tricklist
	if last_trick_id >= 0:
		if not trigger_id in cfg('tricks', idToTrick(last_trick_id), 'lPath'):
			players[userid]['tricklist'].append(-19)

	# Find the trick that matches
	best_name=None
	best_path=[]
	
	for name in tricks():
		if not cfg('tricks', name, 'bEnabled'): continue

		if cfg('tricks', name, 'lPath') == []:
			disableTrick(name, 'No path defined')
			continue

		trickpath = cfg('tricks', name, 'lPath')
		trickpass = cfg('tricks', name, 'lPass')

		#if name != 'razr': continue
		if trickpath[-1] != players[userid]['triggerlist'][-1]: continue
		
		[t, angle, speed] = compareList(trickpath, trickpass, userid)
		if t < 100: continue
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
		foundTrick(userid, best_name, cfg('tricks', best_name, 'iId'), best_t, best_angle, speed_total, best_path, speed_velocity)

	# 2009 04 13 - reset run on some triggers
	if cfg('triggers', trigger_name, 'bEndCombo'):
		endCombo(userid, 'bEndCombo', True)


def foundTrick(userid, trick_name, trick_id, time_first, angles, speed, pathlist, speed_velocity):
	global write_triggers
	global write_tricks
	global triggers
	global tricks
	global players
	
	vlog("foundTrick()")
	vlog("time_first = %f" % time_first)
	
	angle=anglesToAngle(angles)
	trick_total_time=getTrickTime(userid, pathlist)
	
	if len(players[userid]['tricklist']) == 0:
		# First trick, =1
		players[userid]['trick_count'] = 1
		players[userid]['_trick_time'] = time_first
		vlog("resetting time to timefirst 1")

		# make a new item
		players[userid]['combolist'].append('null')

	elif players[userid]['tricklist'][-1] == trick_id and angle == players[userid]['lastangle']:
		players[userid]['trick_count'] += 1

	else:
		# This is the first of the trick they have done. =1
		players[userid]['trick_count'] = 1
		players[userid]['_trick_time'] = time_first
		vlog("resetting time to timefirst 2")

		# make a new item
		players[userid]['combolist'].append('null')


	players[userid]['lastangle'] = angle
	seconds=time.time() - players[userid]['_trick_time']
	
	vlog("time = %f" % time.time())
	vlog("_trick_time = %f" % players[userid]['_trick_time'])
	vlog("foundtrigger seconds -> %f" % seconds)

	# special awp counter +1
	if trick_name == "awp" and players[userid]['trick_count'] == 1: players[userid]['trick_count']=2

	players[userid]['tricklist'].append(trick_id)
	trick_name_full=trickName(trick_name, players[userid]['trick_count'], angle)
	players[userid]['combolist'][-1] = trick_name_full
	
	# Fire the event
	es.event("initialize", 'ztricks_trick')
	es.event("setstring", 'ztricks_trick', 'userid', userid)
	es.event("setstring", 'ztricks_trick', 'trick_id', trick_id)
	es.event("setstring", 'ztricks_trick', 'trick_time', seconds)
	es.event("setstring", 'ztricks_trick', 'trick_name', trick_name_full)
	es.event("setstring", 'ztricks_trick', 'trick_short', trick_name)
	es.event("setstring", 'ztricks_trick', 'trick_points', cfg('tricks', trick_name, 'iPoints'))

	es.event("setstring", 'ztricks_trick', 'player_speed', speed)
	es.event("setstring", 'ztricks_trick', 'player_velocity', speed_velocity)
	es.event("setstring", 'ztricks_trick', 'player_angle', angle)
	es.event("fire", 'ztricks_trick')
	
def timer4():
	global players
	# Detect the end of combos by no movement
	for userid in playerlib.getUseridList("#alive"):
		check_keys(userid)
		if players[userid]['force_end_combo']:
			players[userid]['force_end_combo'] = False
			endCombo(userid, 'force_end_combo')
			continue

		# Detect movement
		if getPlayerVelocity(userid) < 10:
			if players[userid]['is_moving']: endCombo(userid, 'movement')
			players[userid]['is_moving'] = False
		else:
			players[userid]['is_moving'] = True
		
		# Detect spawn
		if not players[userid]['is_alive']:
			players[userid]['is_alive'] = True
			
			es.event("initialize", 'ztricks_playerspawn')
			es.event("setstring", 'ztricks_playerspawn', 'userid', userid)
			es.event("fire", 'ztricks_playerspawn')

	# endCombo for dead people too!
	for userid in playerlib.getUseridList("#dead"):
		check_keys(userid)

		# Detect death if moving
		if players[userid]['is_moving']:
			endCombo(userid, 'death')
			players[userid]['is_moving'] = False

		# Detect first death
		if players[userid]['is_alive']:
			players[userid]['is_alive'] = False

			es.event("initialize", 'ztricks_playerdeath')
			es.event("setstring", 'ztricks_playerdeath', 'userid', userid)
			es.event("fire", 'ztricks_playerdeath')

	gamethread.delayedname(0.01, 'timer4', timer4)

def endCombo(userid, reason, keep_last=False):
	global players
	check_keys(userid)
	vlog("endCombo() called with reason: %s" % reason)
	
	# Turn ids into names
	list=[]
	for key in players[userid]['combolist']:
		#if key != 'null':
		list.append(key)

	# Fire event
	es.event("initialize", 'ztricks_combo')
	es.event("setstring", 'ztricks_combo', 'userid', userid)
	es.event("setstring", 'ztricks_combo', 'list', "::".join(list))
	es.event("setstring", 'ztricks_combo', 'count', len(list))
	es.event("setstring", 'ztricks_combo', 'reason', reason)
	es.event("fire", 'ztricks_combo')
	
	# Clear trigger and trick lists
	playerReset(userid, keep_last)

##############################################################################
# Configuration Handling
##############################################################################

def writeconfig():
	#return
	global data
	global data_changed

	#most_length = 0
	#for master in data:
	#	for name in data[master]:
	#		most_length = len(name)
	#most_length += 1
	#vlog("most_length = %d" % most_length)

	vlog("writing config..")
	fh=open(configfile, 'wb')
	lines = 0
	
	akeys = data.keys()
	akeys.sort()
	for master in akeys:
		bkeys = data[master].keys()
		bkeys.sort()
		for name in bkeys:
			ckeys = data[master][name].keys()
			ckeys.sort()
			for key in ckeys:

				if key == 'fCoord1' or key == 'fCoord2' or key == 'fCoord3':
					continue

				value = typing(key, data[master][name][key])
				#vlog("committing [%s] type: %s" % (value, type(value)))
				
				if type(value) == float:
					fh.write("%s\t%s\t%s\t%f\r\n" % (master, name, key, value))
				else:
					fh.write("%s\t%s\t%s\t%s\r\n" % (master, name, key, value))
				
				lines += 1
				
			fh.write("\r\n")
	fh.close()
	data_changed = False
	vlog("wrote %d lines" % lines)
	
	# make a backup
	try:
		if not os.path.isdir("%s/config-backup" % our_dir):
			os.mkdir("%s/config-backup" % our_dir)
		shutil.copy(configfile, "%s/config-backup/configbackup_%s.cfg" % (our_dir, time.time()))
	except:
		vlog("failed to make backup")
		

def loadConfig():
	global data
	global data_changed
	
	if time.time() > hard_timelimit:
		msg("Impossible to continue because I hate you.")
		msg("ERROR %s" % (time.time() - hard_timelimit))
		return

	## Wipe
	data = {}

	## Read
	try:
		fh = open(configfile, 'rb')
		lines = fh.readlines()

		for line in lines:
			if line.startswith("INFO"):
				continue
			line = re.sub("([^a-zA-Z0-9\#\=\+\^\%\$\@\!\.\,\_\- \t])", '', line)

			m = re.match('^([^\t]+)\t+([^\t]+)\t+([^\t]+)\t+(.+)$', line)
			if m:
				[master, name, key, value] = m.groups()
				
				#if key.startswith("f"):
				#	vlog("loadConfig key=%s value=[%s]" % (key, value))
				#	vlog("matched master->%s name->%s key->%s value->[%s]" % (master,name,key,value))

				cfg(master, name, key, value, False)

	except:
		vlog("Error while reading config")
		print_exception()
		
	try:
		trick_count = len(data['tricks'])
		trigger_count = len(data['triggers'])
	except:
		trick_count = 0
		trigger_count = 0

	msg("Configuration Loaded %d tricks, %d triggers" % (trick_count, trigger_count))
	data_changed = True

##############################################################################
# Common Functions
##############################################################################

def getPlayerLastTrigger(userid):
	if len(players[userid]['triggerlist']) > 0:
		return players[userid]['triggerlist'][-1]

def timer2():
	return
	gamethread.delayedname(1, 'timer2', timer2)

def timer3():
	return
	gamethread.delayedname(0.1, 'timer3', timer3)

def isDev():
	return os.path.exists("%s/is_dev_server.txt" % our_dir)
	
def sayFilter(userid, text, teamOnly):
	if text.lower() == "!reset":
		endCombo(userid, '!reset')
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

		players[userid]['force_end_combo'] = False

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
		
		#players[userid]['leave_trigger_time']=[]
		
		players[userid]['is_moving'] = False
		players[userid]['is_alive'] = True

def getDist(c1, c2):
	return vecmath.distance(c1, c2)
	
def getAngle(a,b,c):
	return math.degrees(math.acos(((b**2)+(c**2)-(a**2))/(2*b*c)))

def vlog(text, important=False):
	if not important and not isDev():
		return

	try:
		file=open("%s/vlog.txt" % our_dir, 'a')
		file.write("%s %s\r\n" % (time.time(), text))
		file.close()
	except:
		print "### Failed to open file ###"

	if isDev():
		print "%.1f vlog: %s" % (time.time(), text)
	
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
	for key in tricks():
		if cfg('tricks', key, 'iId') == int(id):
			return key
	
def idToTrigger(id):
	for key in triggers():
		if cfg('triggers', key, 'iId') == int(id):
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

	# Rapid Checks
	if len(pathlist) > len(userlist): return [-1, -1, -1]
	if userlist[-1] in passlist: return [-2, -2, -2]

	delta = len(pathlist) * -1
	listSpeed = players[userid]['triggerspeeds']
	listAngle = players[userid]['triggerangles']
	listTime=players[userid]['triggertimes']

	newlist = []
	newtime = []
	newangle = []
	newspeed = []
	index = 0
	
	for point in userlist:
		if not point in passlist:
			newlist.append( point )
			newtime.append( listTime[index] )
			newangle.append( listAngle[index] )
			newspeed.append( listSpeed[index] )
		index += 1
	
	if len(pathlist) > len(newlist): return [-4, -4, -4]

	startTime = newtime[delta:][0]

	if newlist[delta:] == pathlist: return [startTime, newangle[delta:], newspeed[delta:]]
	return [-3, -3, -3]

def getTrickName(id):
	for name in tricks():
		if cfg('tricks', name, 'iId') == id: return name
	return

def trigger_box(userid, name, x, y, z):
	c1x=cfg('triggers', name, 'fCoord1_x')
	c1y=cfg('triggers', name, 'fCoord1_y')
	c1z=cfg('triggers', name, 'fCoord1_z')

	c2x=cfg('triggers', name, 'fCoord2_x')
	c2y=cfg('triggers', name, 'fCoord2_y')
	c2z=cfg('triggers', name, 'fCoord2_z')

	if c1x == 0 and c1y == 0 and c1z == 0:
		disableTrigger(name, "Coordinate 1 is empty")
		return

	if c2x == 0 and c2y == 0 and c2z == 0:
		disableTrigger(name, "Coordinate 2 is empty")
		return

	# Honor wasdfr
	wasdfr=cfg('triggers', name, 'sDirectionOnly')
	if wasdfr in ['f','r']:
		if not wasdfr == getPlayerDest(userid, 'fr'): return
	if wasdfr in ['w','a','s','d']:
		if not wasdfr == getPlayerDest(userid, 'wasd'): return

	# Actual Testing
	if trigger_box_single(name, c1x, c1y, c1z, c2x, c2y, c2z, x, y ,z) == 1: return 1
	if cfg('triggers', name, 'bSymetrical'): return trigger_box_single(name, c1x, c2y - (c2y * 2), c1z, c2x, c1y - (c1y * 2), c2z, x, y, z)

def trigger_box_single(name, c1x, c1y, c1z, c2x, c2y, c2z, x, y, z):
	if vecmath.isbetweenRect([x,y,z], [c1x,c1y,c1z], [c2x,c2y,c2z]):
		return 1
	return 0	
	
	# Determine if in the box
	if (x > c1x and x < c2x) or (x > c2x and x < c1x):
		if (y > c1y and y < c2y) or (y > c2y and y < c1y):
			if (z > c1z and z < c2z) or (z > c2z and z < c1z):
				return 1

def disableTrigger(name, reason=None):
	if allow_disable == 0:
		vlog("Disable trigger request denied (allow_disable = 0) name->%s reason->%s" % (name, reason))
		return

	msg("Disabled trigger name->%s reason->%s" % (name, reason))
	cfg('triggers', name, 'bEnabled', False)

def disableTrick(name, reason=None):
	if allow_disable == 0:
		vlog("Disable trick request denied (allow_disable = 0) name->%s reason->%s" % (name, reason))
		return

	msg("Disabled trick name->%s reason->%s" % (name, reason))
	cfg('tricks', name, 'bEnabled', False)

def trigger_sphere(userid, name, x, y, z):
	basex=cfg('triggers', name, 'fCoord1_x')
	basey=cfg('triggers', name, 'fCoord1_y')
	basez=cfg('triggers', name, 'fCoord1_z')

	if basex == 0 and basey == 0 and basez == 0:
		disableTrigger(name, "Coordinate 1 is empty")
		return

	radius=cfg('triggers', name, 'fRadius')
	if radius == 0:
		disableTrigger(name, "No radius")
		return
	
	height=cfg('triggers', name, 'fHeight')
	if height == 0:
		height=radius
		cfg('triggers', name, 'fHeight', height)

	if height > radius:
		msg("#green%s#default height is too high, clamping %.0f -> %.0f" % (name, height, radius))
		height=radius
		cfg('triggers', name, 'fHeight', height)

	if height <= 0:
		msg("#green%s#default height is too low, clamping %.0f -> %.0f" % (name, height, radius))
		height=radius
		cfg('triggers', name, 'fHeight', height)

	# Honor height restriction
	if z < (basez - height) or z > (basez + height): return

	# Actual Distance
	if getDist([basex,basey,basez], [x,y,z]) <= radius: return 1
	if cfg('triggers', name, 'bSymetrical'):
		if getDist([basex, basey - (basey * 2) ,basez], [x,y,z]) <= radius: return 1
	
def trigger_awpmain(userid, name, x, y, z):
	return
	
##############################################################################################################
# EVENTS
##############################################################################################################
def player_spawn(ev):
	userid = ev['userid']
	endCombo(userid, 'player_spawn')

def player_death(ev):
	userid = ev['userid']
	endCombo(userid, 'player_death')

def zreload():
	if not isAdmin(userid):
		es.tell(userid, 'You are not allowed to run that command!')
		return

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

		for cmd in clientCommands:
			es.regclientcmd(cmd, "ztricks-core/%s" % cmd)
			
	        #es.regclientcmd("zdrawmenu", 'ztricks-core/sendMenu')
	        #es.regclientcmd("zreload", 'ztricks-core/zreload')

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

	for cmd in clientCommands:
		es.unregclientcmd(cmd)
        #es.unregclientcmd("zdrawmenu")
        #es.unregclientcmd("zreload")

	msg("unloaded")
	vlog("unload() ended")

##############################################################################################################
# COMMON FUNCTIONS
##############################################################################################################

def zcreate_trick():
	userid = es.getcmduserid()
	text = es.getargs()
	if not isAdmin(userid):
		es.tell(userid, 'You are not allowed to run that command!')
		return

	if text == None:
		es.tell(userid, 'Usage: zcreate_trick awp to awp over main')
		return

	if text in tricks():
		es.tell(userid, 'That trick already exists!')
		return

	# Find a new id..
	for i in range(3000,4000):
		if idToTrick(i) == None or idToTrick(i) == 0:
			vlog("found new id = %s" % i)
			cfg('tricks', text, 'iId', i)
			break

	cfg('tricks', text, 'sCreatedBy', gpn(userid))
	es.tell(userid, 'Created new trick: %s' % text)
	es.tell(userid, '-- Id = %s' % cfg('tricks', text, 'iId'))

def zcreate_trigger():
	userid = es.getcmduserid()
	text = es.getargs()
	if not isAdmin(userid):
		es.tell(userid, 'You are not allowed to run that command!')
		return

	if text == None:
		es.tell(userid, 'Usage: zcreate_trigger awpside3')
		return
	
	if text in triggers():
		es.tell(userid, 'That trigger already exists!')
		return

	# Find a new id..
	for i in range(3000,4000):
		if idToTrigger(i) == None or idToTrigger(i) == 0:
			vlog("found new id = %s" % i)
			cfg('triggers', text, 'iId', i)
			break

	cfg('triggers', text, 'sCreatedBy', gpn(userid))
	es.tell(userid, 'Created new trigger: %s' % text)
	es.tell(userid, '-- Id = %s' % cfg('triggers', text, 'iId'))

def zsetid_trigger():
	# zsetid_trigger some trigger name 205
	# pattern: (.*) (\d+)

	userid = es.getcmduserid()
	text = es.getargs()

	if not isAdmin(userid):
		es.tell(userid, 'You are not allowed to run that command!')
		return

	if text == None:
		es.tell(userid, 'Usage: zsetid_trigger "the name of the trigger" 200')
		es.tell(userid, '       zsetid_trigger <the trigger name> <new id>')
		return
	
	m=re.match("\"(.*)\" (\d+)", text)
	if m:
		[name, id]=m.groups()
		vlog("got name[%s] and id[%s]" % (name, id))
		try:
			id = int(id)
		except:
			es.tell(userid, 'Usage: zsetid_trigger "the name of the trigger" 200')
			es.tell(userid, '       zsetid_trigger <the trigger name> <new id>')
			return
	else:
		es.tell(userid, 'Usage: zsetid_trigger "the name of the trigger" 200')
		es.tell(userid, '       zsetid_trigger <the trigger name> <new id>')
		return

	if not name in triggers():
		es.tell(userid, 'That trigger does not exist! Cannot modify it.')
		return
	
	oldid = cfg('triggers', name, 'iId')
	cfg('triggers', name, 'iId', id)
	es.tell(userid, "Changed id for %s from %s to %s" % (name, oldid, id))
	es.tell(userid, 'Make sure you update existing tricks that used that id!')

def zsetid_trick():
	# zsetid_trick some trick name 205
	# pattern: (.*) (\d+)

	userid = es.getcmduserid()
	text = es.getargs()

	if not isAdmin(userid):
		es.tell(userid, 'You are not allowed to run that command!')
		return

	if text == None:
		es.tell(userid, 'Usage: zsetid_trick "awp to sign" 200')
		es.tell(userid, '       zsetid_trick "<the trick name>" <new id>')
		return
	
	m=re.match("\"(.*)\" (\d+)", text)
	if m:
		[name, id]=m.groups()
		vlog("got name[%s] and id[%s]" % (name, id))
		try:
			id = int(id)
		except:
			es.tell(userid, 'Usage: zsetid_trick "awp to sign" 200')
			es.tell(userid, '       zsetid_trick "<the trick name>" <new id>')
			return
	else:
		es.tell(userid, 'Usage: zsetid_trick "awp to sign" 200')
		es.tell(userid, '       zsetid_trick "<the trick name>" <new id>')
		return

	if not name in tricks():
		es.tell(userid, 'That trick does not exist! Cannot modify it.')
		return
	
	oldid = cfg('tricks', name, 'iId')
	cfg('tricks', name, 'iId', id)
	es.tell(userid, "Changed id for %s from %s to %s" % (name, oldid, id))

def zrename_trigger():
	global data
	global data_changed

	# zrename_trigger "old name" "new name"
	# pattern: \"(.*)\" \"(.*)\"

	userid = es.getcmduserid()
	text = es.getargs()

	if not isAdmin(userid):
		es.tell(userid, 'You are not allowed to run that command!')
		return

	if text == None:
		es.tell(userid, 'Usage: zrename_trigger \"old trigger name\" \"new trigger name\"')
		es.tell(userid, '       zrename_trigger \"awp ramp\" \"old awp ramp box\"')
		return
	
	m=re.match("\"([^\"]+)\" \"([^\"]+)\"", text)
	if m:
		[oldname, newname]=m.groups()
		vlog("got oldname[%s] newname[%s]" % (oldname, newname))
	else:
		es.tell(userid, 'Usage: zrename_trigger \"old trigger name\" \"new trigger name\"')
		es.tell(userid, '       zrename_trigger \"awp ramp\" \"old awp ramp box\"')
		return

	# Does the old exist?
	try:
		if not data['triggers'][oldname]:
			es.tell(userid, 'That trigger does not exist!')
			return
	except:
		es.tell(userid, "That trigger does NOT exist!!")
		#es.tell(userid, "Error, tell z. there was a problem")
		print_exception()
		return
	
	# Duplicate the key
	data['triggers'][newname] = data['triggers'][oldname]
	
	# Delete the old
	del data['triggers'][oldname]
	data_changed = True
	
	es.tell(userid, "Renamed trigger \"%s\" to \"%s\"" % (oldname, newname))
	#es.tell(userid, "This command has not been finished. Nothing will be done.")
	return

def zrename_trick():
	global data
	global data_changed
	
	# zrename_trick "old name" "new name"
	# pattern: \"(.*)\" \"(.*)\"

	userid = es.getcmduserid()
	text = es.getargs()

	if not isAdmin(userid):
		es.tell(userid, 'You are not allowed to run that command!')
		return

	if text == None:
		es.tell(userid, 'Usage: zrename_trick \"old trick name\" \"new trick name\"')
		es.tell(userid, '       zrename_trick \"awp ramp\" \"old awp ramp box\"')
		return
	
	m=re.match("\"([^\"]+)\" \"([^\"]+)\"", text)
	if m:
		[oldname, newname]=m.groups()
		vlog("got oldname[%s] newname[%s]" % (oldname, newname))
	else:
		es.tell(userid, 'Usage: zrename_trick \"old trick name\" \"new trick name\"')
		es.tell(userid, '       zrename_trick \"awp ramp\" \"old awp ramp box\"')
		return

	# Does the old exist?
	try:
		if not data['tricks'][oldname]:
			es.tell(userid, 'That trick does not exist!')
			return
	except:
		es.tell(userid, "That trick does NOT exist!!")
		#es.tell(userid, "Error, tell z. there was a problem")
		print_exception()
		return
	
	# Duplicate the key
	data['tricks'][newname] = data['tricks'][oldname]
	
	# Delete the old
	del data['tricks'][oldname]
	data_changed = True
	
	es.tell(userid, "Renamed trick \"%s\" to \"%s\"" % (oldname, newname))
	#es.tell(userid, "This command has not been finished. Nothing will be done.")
	return

def playerReset(userid, keep_last=False):
	# If a player dies their trigger lists are reset here.
	global players

	check_keys(userid)

	if keep_last:
		players[userid]['triggerlist'] = players[userid]['triggerlist'][-1:]
		players[userid]['triggertimes'] = players[userid]['triggertimes'][-1:]
		players[userid]['triggerangles'] = players[userid]['triggerangles'][-1:]
		players[userid]['triggerspeeds'] = players[userid]['triggerspeeds'][-1:]
	else:
		players[userid]['triggerlist'] = []
		players[userid]['triggertimes'] = []
		players[userid]['triggerangles'] = []
		players[userid]['triggerspeeds'] = []

	players[userid]['combolist'] = []
	players[userid]['tricklist'] = []

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

def gpa_diff(look, move):
	if look < move:	diff1 = (look - move) * -1
	else:		diff1 = (move - look) * -1
	diff2 = 360 - diff1
	if diff2 < 0: return diff1
	if diff1 < 0: return diff2
	if diff1 < diff2:	return diff1
	else:			return diff2

def getPlayerAngle(userid):
	#
	# - test new angle math
	#	look - body
	#	body - look
	#	360 - (look - body)
	#	360 - (body - look)
	#	whichever is lowest, thats the angle diff
	#	use existing ifs to calculate
	#
	#return "forward"

	look=getPlayerLook(userid)
	move=getPlayerDest(userid)

	diff = 999
	a = float(look - move)
	b = float(move - look)
	c = 360 - a
	d = 360 - b
	
	if a > 0 and diff > a: diff = a
	if b > 0 and diff > b: diff = b
	if c > 0 and diff > c: diff = c
	if d > 0 and diff > d: diff = d

	#vlog("%s look->%f body->%f diff->%f" % (gpn(userid), look, move, diff))
	
	if (diff < 22.5):	return "forward"
	elif (diff < 67.5):	return "halfsideways"
	elif (diff < 112.5):	return "sideways"
	elif (diff < 157.5):	return "backwards halfsideways"
	elif (diff < 202.5):	return "backwards"
	elif (diff < 247.5):	return "backwards halfsideways"
	elif (diff < 292.5):	return "sideways"
	elif (diff < 337.5):	return "halfsideways"
	else:			return "forward"

def getPlayerAngle_last(userid):
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
	# instead of just drawing name, lets draw all with that same id too
	id = cfg('triggers', name, 'iId')
	
	shape=cfg('triggers', name, 'sShape')	
	if shape == 'box':
		c1x=cfg('triggers', name, 'fCoord1_x')
		c1y=cfg('triggers', name, 'fCoord1_y')
		c1z=cfg('triggers', name, 'fCoord1_z')
		c2x=cfg('triggers', name, 'fCoord2_x')
		c2y=cfg('triggers', name, 'fCoord2_y')
		c2z=cfg('triggers', name, 'fCoord2_z')

		drawbox([c1x,c1y,c1z], [c2x,c2y,c2z])
		if cfg('triggers', name, 'bSymetrical'): drawbox([c1x,c2y - (c2y * 2),c1z], [c2x,c1y - (c1y * 2),c2z])

	elif shape == 'sphere':
		radius=cfg('triggers', name, 'fRadius')
		height=cfg('triggers', name, 'fHeight')
		if radius == 0:
			disableTrigger(name, 'Radius is zero')
			msg("Unable to draw %s because it does not have a radius." % name)
			return
		if height == 0: height = radius

		c1x=cfg('triggers', name, 'fCoord1_x')
		c1y=cfg('triggers', name, 'fCoord1_y')
		c1z=cfg('triggers', name, 'fCoord1_z')

		# First
		drawcircle([c1x,c1y,c1z + height], radius, 'z', 4)
		drawcircle([c1x,c1y,c1z - height], radius, 'z', 4)
		drawcircle([c1x,c1y,c1z], radius, 'x')
		drawcircle([c1x,c1y,c1z], radius, 'y')

		# Second
		if cfg('triggers', name, 'bSymetrical'):
			c1y=c1y - (c1y * 2)
			drawcircle([c1x,c1y,c1z + height], radius, 'z', 4)
			drawcircle([c1x,c1y,c1z - height], radius, 'z', 4)
			drawcircle([c1x,c1y,c1z], radius, 'x')
			drawcircle([c1x,c1y,c1z], radius, 'y')

	else:
		es.tell(userid, "unsupported type!")
	
def drawline(coord1, coord2):
	effectlib.drawLine(coord1, coord2, model="materials/sprites/laser.vmt", halo="materials/sprites/halo01.vmt", seconds=30, width=5, red=255, green=255, blue=255)

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
	vlog("exception!!", True)
	#vlog(traceback.format_exception)

	formatted_lines = traceback.format_exc().splitlines()
	for line in formatted_lines:
		vlog("EX: %s" % line, True)

def drawmenu():
	userid = es.getcmduserid()
	
	# send a draw menu so we can draw triggers
	myPopup = popuplib.easymenu("draw menu for %s" % userid, None, drawSelect)
	myPopup.settitle("draw")

	for name in triggers():
		myPopup.addoption("drawtrigger:%s" % name, "%s id->%s type->%s" % (name, cfg('triggers', name, 'iId'), cfg('triggers', name, 'sShape')))

	myPopup.send(userid)

def drawSelect (userid, choice, popupid):
	[n, name] = choice.split(":")
	try:
		drawtrigger(userid, name)
	except:
		es.tell(userid, "While drawing, there was an unknown error")
		print_exception()


def isAdmin(userid):
	steamid = es.getplayersteamid(userid)
	if not steamid in menuAdmins(): return
	return 1

def zadminmenu():
	userid = es.getcmduserid()

	if not isAdmin(userid):
		es.tell(userid, 'You are not allowed to run that command!')
		return

	myPopup = popuplib.easymenu("zTricks Admin Menu [%s]" % userid, None, zadminmenuselect)

	# List some basic commands to support
	myPopup.addoption("triggers", "Triggers")
	myPopup.addoption("tricks", "Tricks")
	myPopup.addoption("help", "Help!")

	myPopup.send(userid)

def menuAdmins():
	adminlist=[]
	try:
		fh=open("%s/menuAdmins.txt" % our_dir, 'rb')
		lines = fh.readlines()
		for line in lines:
			line = re.sub("([^STEAM0-9\:\_])", '', line)
			adminlist.append(line)
		fh.close()
	except:
		pass
	return adminlist

def zadminmenuselect(userid, choice, popupid):
	global data
	global data_changed
	vlog("zadminmenuselect(%s, %s, %s)" % (userid, choice, popupid))

	try:
		steamid = es.getplayersteamid(userid)
		if not steamid in menuAdmins():
			es.tell(userid, 'You are not allowed to run that command!')
			return
	
		args = choice.split(":")
		c = len(args)
		vlog("args: %d -> %s" % (c, args))
		if c <= 0: return
		myPopup = popuplib.easymenu("zTricks Admin Menu [%s]" % userid, None, zadminmenuselect)
	
		if args[0] == 'help':
			myPopup = popuplib.create('help_popup')
			myPopup.addline("Everything can be done from inside this menu, except")
			myPopup.addline("actions that require input.")
			myPopup.addline(" ")
			myPopup.addline("There are commands to fix that issue. These are run")
			myPopup.addline("from YOUR ~ console.")
			myPopup.addline(" ")
			myPopup.addline("Possible Commands:")
	
			for cmd in clientCommands:
				myPopup.addline("    %s" % cmd)
	
			myPopup.addline('   ')
			myPopup.addline('The menu options for Set Sphere Height and Set Coords')
			myPopup.addline('both use your position to calculate. So stand where')
			myPopup.addline('where you want it.')
			myPopup.addline('   ')
			myPopup.addline('->0 Close')
			myPopup.send(userid)
			return
			
		elif args[0] == 'tricks':
			if c == 1:
				tkeys = tricks()
				tkeys.sort()
				myPopup.addoption("tricks:[Create New]", "[Create New]")
				for name in tkeys:
					myPopup.addoption("tricks:%s" % name, "%s (%s)" % (name, cfg('tricks', name, 'bEnabled')))
				myPopup.send(userid)
				return
			
			elif c == 2:
				name = args[1]
				
				if name == "[Create New]":
					# Special operation to create a new trigger
					es.tell(userid, 'To create new tricks, you must run the command:')
					es.tell(userid, '  zcreate_trick the new trigger name')
					return
	
				for op in ['Change Enabled', 'Add trigger to pass list', 'Remove trigger from pass list', 'View pass list', 'Add trigger to path list', 'Remove trigger from path list', 'View path list', 'Change point value', 'View current values', 'Draw Boxes', 'Permanently Delete', 'Rename']:
					myPopup.addoption("%s:%s" % (choice, op), op)
				myPopup.send(userid)
				return
			
			elif c == 3:
				name = args[1]
				
				if args[-1] == 'Change Enabled':
					for op in ['True', 'False']:
						myPopup.addoption("%s:%s" % (choice, op), op)
					myPopup.send(userid)
					return

				elif args[-1] == 'Rename':
					es.tell(userid, "To rename a trick, run the command zrename_trick")
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
					return
					
				elif args[-1] == 'Permanently Delete':
					# whatever
					#es.tell(userid, "before: %s" % data['tricks'][name])
					del data['tricks'][name]
					#es.tell(userid, "after: %s" % data['tricks'][name])
					data_changed = True
					es.tell(userid, "Deleted trick %s" % name)
					zadminmenuselect(userid, ":".join( args[:-2] ), popupid)
					return
				
				elif args[-1] == 'Change point value':
					for op in [0,1,2,3,4,5,6,7,8,9,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,125,150,175,200,225,250,275,300,325,350,375,400,425,450,475,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000]:
						myPopup.addoption("%s:%s" % (choice, op), op)
					myPopup.send(userid)
					return
				
				elif args[-1] == 'View current values':
					# display info about it
					
					myPopup = popuplib.create('trick info')
					myPopup.addline("%s" % name)
			
					for k in data['tricks'][name]:
						v = data['tricks'][name][k]
						myPopup.addline("    %s: %s" % (k,v))
			
					myPopup.addline('   ')
					myPopup.addline('->0 Close')
					myPopup.send(userid)
					return
				
				elif args[-1] == 'Add trigger to path list':
					# display a list of triggers to add
					for op in triggers():
						nid = cfg('triggers', op, 'iId')
						if nid == 0: continue
						myPopup.addoption("%s:%s" % (choice, nid), op)
					myPopup.send(userid)
					return
				
				elif args[-1] == 'Remove trigger from path list':
					# ask which to remove
					index = 0
					pathlist = cfg('tricks', name, 'lPath')
					
					if len(pathlist) == 0:
						es.tell(userid, 'The path list is empty, cannot remove any!')
						zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
						return
					
					for item in pathlist:
						myPopup.addoption("%s:%s" % (choice, index), "%d: %s (%d)" % (index, idToTrigger(item), item))
						index += 1
						
					myPopup.send(userid)
					return
	
					
				elif args[-1] == 'View path list':
					pathlist = cfg('tricks', name, 'lPath')
					es.tell(userid, "Path list for %s:" % name)
					for item in pathlist:
						es.tell(userid, "  %s - %s" % (item, idToTrigger(item)))
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
					return
	
				elif args[-1] == 'View pass list':
					passlist = cfg('tricks', name, 'lPass')
					es.tell(userid, "Pass list for %s:" % name)
					for item in passlist:
						es.tell(userid, "  %s - %s" % (item, idToTrigger(item)))
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
					return
				
				elif args[-1] == 'Add trigger to pass list':
					# Give a list of trigger names
					for triggername in triggers():
						myPopup.addoption("%s:%s" % (choice, cfg('triggers', triggername, 'iId')), triggername)
					myPopup.send(userid)
					return
	
				elif args[-1] == 'Remove trigger from pass list':
					# Get the passlist
					passlist = cfg('tricks', name, 'lPass')
	
					if len(passlist) == 0:
						es.tell(userid, 'The pass list is empty, cannot remove any!')
						zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
						return
	
					# Give a list of all the choices
					for item in passlist:
						myPopup.addoption("%s:%s" % (choice, item), "%s - %s" % (item, idToTrigger(item)))
					myPopup.send(userid)
					return
	
				elif args[-1] == 'Draw Boxes':
					path = cfg('tricks', name, 'lPath')
					es.tell(userid, "Drawing boxes for %s %s" % (name, path))
					for triggername in triggers():
						id = cfg('triggers', triggername, 'iId')
						if id in path:
							drawtrigger(userid, triggername)
							es.tell(userid, "- %s (%d)" % (triggername, id))
					
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
	
			elif c == 4:
				name = args[1]
	
				if args[2] == 'Change Enabled':
					cfg('tricks', name, 'bEnabled', typing('bEnabled', args[-1]))
					es.tell(userid, "%s's enabled status is now %s" % (name, cfg('tricks', name, 'bEnabled')))
					
				elif args[2] == 'Add trigger to pass list':
					# Get the passlist
					passlist = cfg('tricks', name, 'lPass')
					
					# Add to the passlist
					passlist.append( int(args[3]) )
					
					# Save the new passlist
					cfg('tricks', name, 'lPass', passlist)
					
					es.tell(userid, 'Updated pass list to: %s' % cfg('tricks', name, 'lPass'))
					zadminmenuselect(userid, ":".join( args[:-2] ), popupid)
					return
	
				elif args[2] == 'Change point value':
					try:
						p = int(args[-1])
					except:
						es.tell(userid, 'Invalid Choice? Cannot continue.')
						return
					
					cfg('tricks', name, 'iPoints', p)
					es.tell(userid, "%s is now worth %s points" % (name, cfg('tricks', name, 'iPoints')))
					
				elif args[2] == 'Remove trigger from path list':
					pathlist = cfg('tricks', name, 'lPath')
					try:
						remove_index = int(args[-1])
					except:
						es.tell(userid, 'Invalid Choice? Cannot continue.')
						return
	
					pathlist[remove_index]="remove_this"
					pathlist.remove("remove_this")
					cfg('tricks', name, 'lPath', pathlist)
					es.tell(userid, "%s's new path list: %s" % (name, cfg('tricks', name, 'lPath')))
					zadminmenuselect(userid, ":".join( args[:-2] ), popupid)
					
				elif args[2] == 'Add trigger to path list':
					try:
						idtoadd = int(args[3])
					except:
						es.tell(userid, "Invalid Choice? Cannot continue.")
						return
					
					pathlist = cfg('tricks', name, 'lPath')
					pathlist.append(idtoadd)
					cfg('tricks', name, 'lPath', pathlist)
					es.tell(userid, "%s's new path list: %s" % (name, cfg('tricks', name, 'lPath')))
					zadminmenuselect(userid, ":".join( args[:-2] ), popupid)
					
					
				elif args[2] == 'Remove trigger from pass list':
					# Get the passlist
					passlist = cfg('tricks', name, 'lPass')
					
					# Add to the passlist
					passlist.remove( int(args[3]) )
					
					# Save the new passlist
					cfg('tricks', name, 'lPass', passlist)
					
					es.tell(userid, 'Updated pass list to: %s' % cfg('tricks', name, 'lPass'))
					zadminmenuselect(userid, ":".join( args[:-2] ), popupid)
					return
	
			vlog("UNHANDLED tricks %s -> %s" % (c, args))
			
		elif args[0] == 'triggers':
			if c == 1:
				# New popup to select the trigger
				tkeys = triggers()
				tkeys.sort()
				myPopup.addoption("triggers:[Create New]", "[Create New]")
				for name in tkeys:
					myPopup.addoption("triggers:%s" % name, "%s (%s)" % (name, cfg('triggers', name, 'bEnabled')))
				myPopup.send(userid)
				return
	
			elif c == 2:
				name = args[1]
				
				if name == '[Create New]':
					# Special operation to create a new trigger
					es.tell(userid, 'To create new triggers, you must run the command:')
					es.tell(userid, '  zcreate_trigger the new trigger name')
					return
	
				# We know the name now, display some actions
				for x in ['Change Shape', 'Set Coord1', 'Set Coord2', 'Set Radius', 'Change Combo End', 'Change Enabled', 'Change Symetrical', 'Set Max Velocity', 'Set Min Velocity', 'Draw It', 'Show Raw Data', 'Set Sphere Height', 'What uses this?', 'Permanently Delete', 'Rename']:
					myPopup.addoption("%s:%s" % (choice, x), x)
				myPopup.send(userid)
				return
	
			elif c == 3:
				name = args[1]
	
				# Take action!
				if args[-1] == 'Change Shape':
					# List some shapes
					for s in ['box', 'sphere']:
						myPopup.addoption("%s:%s" % (choice, s), s)
					myPopup.send(userid)
					return
	
				elif args[-1] == 'Permanently Delete':
					# whatever
					#es.tell(userid, "before: %s" % data['triggers'][name])
					del data['triggers'][name]
					#es.tell(userid, "after: %s" % data['triggers'][name])
					data_changed = True
					es.tell(userid, "Deleted trigger %s" % name)
					zadminmenuselect(userid, ":".join( args[:-2] ), popupid)
					return
					
				elif args[-1] == 'Rename':
					es.tell(userid, "To rename a trigger, run the command zrename_trigger")
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
					return

				elif args[-1] == 'What uses this?':

					# get the id for name
					id = cfg('triggers', name, 'iId')
					if id == None:
						es.tell("There was an error getting the id for that trigger!")
						zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
						return

					if id == 0:
						es.tell("There was an error getting the id for that trigger!")
						zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
						return

					myPopup = popuplib.create('what uses')
					myPopup.addline("%s as a path:" % name)

					for trickname in tricks():
						pathlist = cfg('tricks', trickname, 'lPath')
						#passlist = cfg('tricks', trickname, 'lPass')

						if id in pathlist:
							myPopup.addline("    %s" % trickname)

					myPopup.addline(' ')
					myPopup.addline("%s as a pass:" % name)

					for trickame in tricks():
						#pathlist = cfg('tricks', trickname, 'lPath')
						passlist = cfg('tricks', trickname, 'lPass')

						if id in passlist:
							myPopup.addline("    %s" % trickname)
			
					myPopup.addline('   ')
					myPopup.addline('->0 Close')
					myPopup.send(userid)
					
					#zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
					return
				
				elif args[-1] == 'Set Sphere Height':
					# get coord1_z and the difference between players z
					[x,y,z] = es.getplayerlocation(userid)
					
					oldheight = cfg('triggers', name, 'fHeight')
					sphere_z = cfg('triggers', name, 'fCoord1_z')
					
					a = sphere_z - z
					b = z - sphere_z
					
					if a > 0:	diff = a
					else:		diff = b
	
					cfg('triggers', name, 'fHeight', diff)
					es.tell(userid, "Changed %s's fHeight from %s to %s" % (name, oldheight, cfg('triggers', name, 'fHeight')))
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
					return
	
				elif args[-1] == 'Set Radius':
					# get coord1_x and the difference between players x
					[x,y,z] = es.getplayerlocation(userid)
					
					oldradius = cfg('triggers', name, 'fRadius')
					sphere_x = cfg('triggers', name, 'fCoord1_x')
					
					a = sphere_x - x
					b = x - sphere_x
					
					if a > 0:	diff = a
					else:		diff = b
	
					cfg('triggers', name, 'fRadius', diff)
					es.tell(userid, "Changed %s's fRadius from %s to %s" % (name, oldradius, cfg('triggers', name, 'fRadius')))
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
					return
	
				elif args[-1] == 'Show Raw Data':
					# Print all the keys and values to the user
					es.tell(userid, "Raw data for %s:" % name)
					tkeys = data['triggers'][name].keys()
					tkeys.sort()
					for key in tkeys:
						es.tell(userid, "  %s = %s" % (key, data['triggers'][name][key]))
	
				elif args[-1] == 'Set Max Velocity' or args[-1] == 'Set Min Velocity':
					for op in [0, 50, 100, 250, 300, 500, 1000, 2000]:
						myPopup.addoption("%s:%s" % (choice, op), op)
					myPopup.send(userid)
					return
					
				elif args[-1] == 'Change Symetrical':
					for op in ['True', 'False']:
						myPopup.addoption("%s:%s" % (choice, op), op)
					myPopup.send(userid)
					return
	
				elif args[-1] == 'Change Enabled':
					for op in ['True', 'False']:
						myPopup.addoption("%s:%s" % (choice, op), op)
					myPopup.send(userid)
					return
	
				elif args[-1] == 'Change Combo End':
					for op in ['True', 'False']:
						myPopup.addoption("%s:%s" % (choice, op), op)
					myPopup.send(userid)
					return
				
				elif args[-1] == 'Draw It':
					drawtrigger(userid, name)
					
					# Go back to the menu
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
	
				elif args[-1] == 'Set Coord1':
					# Set the new coord1 of name to this players coordinates
					name = args[1]
					[x,y,z] = es.getplayerlocation(userid)
	
					es.tell(userid, "%s's old Coord1 is %f %f %f" % (name, cfg('triggers', name, 'fCoord1_x'), cfg('triggers', name, 'fCoord1_y'), cfg('triggers', name, 'fCoord1_z')))
					cfg('triggers', name, 'fCoord1_x', x)
					cfg('triggers', name, 'fCoord1_y', y)
					cfg('triggers', name, 'fCoord1_z', z)
					es.tell(userid, "%s's new Coord1 is %f %f %f" % (name, cfg('triggers', name, 'fCoord1_x'), cfg('triggers', name, 'fCoord1_y'), cfg('triggers', name, 'fCoord1_z')))
	
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
	
				elif args[-1] == 'Set Coord2':
					# Set the new coord2 of name to this players coordinates
					[x,y,z] = es.getplayerlocation(userid)
	
					es.tell(userid, "%s's old Coord2 is %f %f %f" % (name, cfg('triggers', name, 'fCoord2_x'), cfg('triggers', name, 'fCoord2_y'), cfg('triggers', name, 'fCoord2_z')))
					cfg('triggers', name, 'fCoord2_x', x)
					cfg('triggers', name, 'fCoord2_y', y)
					cfg('triggers', name, 'fCoord2_z', z)
					es.tell(userid, "%s's new Coord2 is %f %f %f" % (name, cfg('triggers', name, 'fCoord2_x'), cfg('triggers', name, 'fCoord2_y'), cfg('triggers', name, 'fCoord2_z')))
	
					zadminmenuselect(userid, ":".join( args[:-1] ), popupid)
	
			elif c == 4:
				name = args[1]
				#['Change Shape', 'Set Coord1', 'Set Coord2', 'Change Enable/Disable', 'Change Symetrical']:
				
				if args[2] == 'Change Shape':
					# Change names shape to args[-1]
					es.tell(userid, "%s's old shape is %s" % (name, cfg('triggers', name, 'sShape')))
					cfg('triggers', name, 'sShape', args[-1])
					es.tell(userid, "%s's new shape is %s" % (name, cfg('triggers', name, 'sShape')))
					
				elif args[2] == 'Change Enabled':
					cfg('triggers', name, 'bEnabled', typing('bEnabled', args[-1]))
					es.tell(userid, "%s's enabled status is now %s" % (name, cfg('triggers', name, 'bEnabled')))
	
				elif args[2] == 'Change Combo End':
					cfg('triggers', name, 'bEndCombo', typing('bEndCombo', args[-1]))
					es.tell(userid, "%s's end combo status is now %s" % (name, cfg('triggers', name, 'bEndCombo')))
	
				elif args[2] == 'Change Symetrical':
					cfg('triggers', name, 'bSymetrical', typing('bSymetrical', args[-1]))
					es.tell(userid, "%s's symetrical status is now %s" % (name, cfg('triggers', name, 'bSymetrical')))
	
				elif args[2] == 'Set Max Velocity':
					cfg('triggers', name, 'fSpeedMax', args[-1])
					es.tell(userid, "%s's max velocity is now %f" % (name, cfg('triggers', name, 'fSpeedMax')))
	
				elif args[2] == 'Set Min Velocity':
					cfg('triggers', name, 'fSpeedMin', args[-1])
					es.tell(userid, "%s's min velocity is now %f" % (name, cfg('triggers', name, 'fSpeedMin')))
	
				else:
					vlog("UNHANDLED name=%s c=%s args=%s" % (name, c, args))
					return
				
				# Return them to the menu for viewing
				zadminmenuselect(userid, ":".join( args[:-2] ), popupid)
	
		elif args[0] == 'tricks':
			vlog("they selected tricks")

	except:
		print_exception()

















	
	
	
	
	
	