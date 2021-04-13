import sys, es, os, re, playerlib, gamethread, effectlib, urllib, time, popuplib, sqlite3, vecmath, math, sets, shutil, thread, ConfigParser
from time import strftime #strftime("%Y-%m-%d %H:%M:%S")

ver=13
rate=0.01
our_dir=es.getAddonPath('ztricks-core')
hard_timelimit=1234567890

players={}
write_triggers=0
write_tricks=0

#
# Main Flow
#

def timer():
	global triggers
	global tricks
	
	for userid in playerlib.getUseridList("#alive"):
		check_keys(userid)
		[x,y,z]=es.getplayerlocation(userid)

		for name in triggers.sections()
			# test each trigger to see if they are in it.
			if not gettrigger(name, 'enabled', False) == True:
				continue

			id=gettrigger(name,'id')
			if players[userid]['triggerlist'][-1] == id:
				continue

			# get the type so we know how to compare it
			type=gettrigger(name,'type')

			if type == 'box':
				if trigger_box(userid, name, x, y, z) == 1:
					foundTrigger(userid, type, name, id, x, y, z)
					break

			elif type == 'sphere':
				if trigger_sphere(userid, name, x, y, z) == 1:
					foundTrigger(userid, type, name, id, x, y, z)
					break

			elif type == 'awpmain':
				if trigger_awpmain(userid, name, x, y, z) == 1:
					foundTrigger(userid, type, name, id, x, y, z)
					break

	check_write()
	gamethread.delayedname(rate, 'timer1', timer)

def foundTrigger(userid, trigger_type, trigger_name, trigger_id, x, y, z):
	global tricks
	global triggers
	global players
	
	last_trick_id=-1
	
	vlog("player %s is in trigger %s [%s][%s] at %s" % (userid, trigger_name, trigger_id, trigger_type, [x,y,z]))
	playerTriggerAdd(userid, trigger_id)

	# Fire the event
	es.event("initialize", 'ontrigger')
	es.event("setstring", 'ontrigger', 'userid',		userid)
	es.event("setstring", 'ontrigger', 'trigger_id',	trigger_id)
	es.event("setstring", 'ontrigger', 'trigger_name',	trigger_name)
	es.event("setstring", 'ontrigger', 'player_velocity',	getPlayerVelocity(userid))
	es.event("setstring", 'ontrigger', 'player_mph',	getPlayerVelocity(userid) / 26)
	es.event("setstring", 'ontrigger', 'player_angle',	getPlayerAngle(userid))
	es.event("fire", 'ontrigger')

	# If it's impossible to do x2+ then add an empty to the players tricklist
	if len(players[userid]['tricklist']) > 0:
		last_trick_id=players[userid]['tricklist'][-1]
		
	if last_trick_id >= 0:
		if not trigger_id in getTrickPath(last_trick_id):
			players[userid]['tricklist'].append(-19)

	# Find the trick that matches
	for name in tricks.sections():
		if last_trick_id == gettrick(name, 'id'):
			continue

		trickpath=getTrickPath(name)
		[t, angle, speed]=compareList(trickpath, getTrickPass(name), userid)
		if t < 1:	continue

		# turn speed[list] into number
		speed_total=0
		for x in speed:
			speed_total = speed_total + x
		if speed_total > 0 and len(speed) > 1:
			speed_total = (speed_total / len(speed)) / 26
	
		foundTrick(userid, name, gettrick(name, 'id'), t, angle, speed_total, trickpath)

def foundTrick(userid, trick_name, trick_id, time_first, angles, speed, pathlist):
	vlog("foundTrick() fired")
	vlog("- userid: %s" % userid)
	vlog("- trick_name: %s" % trick_name)
	vlog("- trick_id: %s" % trick_id)
	vlog("- time_first: %s" % time_first)
	vlog("- angles: %s" % angles)
	vlog("- speed: %s" % speed)
	vlog("- pathlist: %s" % pathlist)

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
	if trick_name == "awp" and players[userid]['trick_count'] == 1:
		players[userid]['trick_count']=2

	players[userid]['tricklist'].append(trickindex)
	trick_name_full=trickName(name, players[userid]['trick_count'], angles)
	
	# Fire the event
	es.event("initialize", 'ontrick')
	es.event("setstring", 'ontrick', 'userid',	userid)
	es.event("setstring", 'ontrick', 'trick_id',	trick_id)
	es.event("setstring", 'ontrick', 'trick_name',	trick_name)
	es.event("setstring", 'ontrick', 'trick_speed',	speed)
	es.event("setstring", 'ontrick', 'trick_time',	seconds)
	es.event("fire", 'ontrick')

#
# Common Functions
#
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

def settrigger(section, key, value):
	global triggers
	global write_triggers
	if not triggers.has_section(section): triggers.add_section(section)
	triggers.set(section, key, value)
	write_triggers=1
	return

def gettrigger(section, key, value=None):
	global triggers
	#TODO: value is not honnored
	return triggers.get(section, key)

def settrick(section, key, value):
	global tricks
	global write_tricks
	if not tricks.has_section(section): tricks.add_section(section)
	tricks.set(section, key, value)
	write_tricks=1
	return

def gettrick(section, key, value=None):
	global trick
	#TODO: value is not honnored
	return tricks.get(section, key)

def getDist(c1, c2):
	return vecmath.distance(c1, c2)
	
def getAngle(a,b,c):
	return math.degrees(math.acos(((b**2)+(c**2)-(a**2))/(2*b*c)))

def msg(text):
	es.msg('#multi', "#green[ztricks-core]#default %s" % text)

def check_write():
	global triggers
	global tricks
	global write_triggers
	global write_tricks
	
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
		
def getTrickPath(name):
	global tricks
	vlog("[debug] getTrickPath(%s) type = %s" % (name, type(name)))
	if type(name) == int:
		# Find the trick that matches this id
		for key in tricks.sections():
			if gettrick(key, 'id') == name:
				vlog("- located name->%s for id->%s" % (key, name))
				name=key
				break
	raw=gettrick(name, 'pathlist')
	return raw.split(',')

def getTrickPass(name):
	global tricks
	vlog("[debug] getTrickPass(%s) type = %s" % (name, type(name)))
	if type(name) == int:
		# Find the trick that matches this id
		for key in tricks.sections():
			if gettrick(key, 'id') == name:
				vlog("- located name->%s for id->%s" % (key, name))
				name=key
				break
	raw=gettrick(name, 'passlist')
	return raw.split(',')
	
def getTrickTime(userid, pathlist):
	# Return the amount of seconds it took to complete the trick for this player
	delta=int("-%s" % len(pathlist))
	return players[userid]['triggertimes'][-1] - players[userid]['triggertimes'][delta]

def trickName(name, count, angles):
	# 20090315 - see if they did it all one way
	s = sets.Set(angles)
	angle=s.pop()
	if len(s) == 1 and not angle == "forward":
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
	
	triggers=ConfigParser.RawConfigParser()
	tricks=ConfigParser.RawConfigParser()

	if time.time() < hard_timelimit:
		triggers.read("%s/triggers.ini" % our_dir)
		tricks.read("%s/tricks.ini" % our_dir)
	
	msg("found #lightgreen%s#default triggers, #lightgreen%s#default tricks" % (len(triggers.sections()), len(tricks.sections())))

def trigger_box(userid, name, x, y, z):
	[x1,y1,z1]=coord(gtrigger(name, 'coord1'))
	[x2,y2,z2]=coord(gtrigger(name, 'coord2'))


	# honor wasdfr
	wasdfr=gtrigger(name, 'wasdfr')
	if wasdfr in ['f','r']:
		if not wasdfr == getPlayerDest(userid, 'fr'):
			continue
	if wasdfr in ['w','a','s','d']:
		if not wasdfr == getPlayerDest(userid, 'wasd'):
			continue

	# determine if in the box
	if (x > int(x1) and x < int(x2)) or (x > int(x2) and x < int(x1)):
		if (y > int(y1) and y < int(y2)) or (y > int(y2) and y < int(y1)):
			if (z > int(z1) and z < int(z2)) or (z > int(z2) and z < int(z1)):
				return 1

def trigger_sphere(userid, name, x, y, z):
	radius=gtrigger(name, 'radius')
	height=gtrigger(name, 'height')
	
	[basex,basey,basez]=coord(gtrigger(name, 'coord1'))

	if not height == "-":
		height=float(height)
		if z < (basez - height) or z > (basez + height):
			continue

	if getDist([basex,basey,basez], [x,y,z]) <= radius:
		return id

##############################################################################################################
# EVENTS
##############################################################################################################
def player_spawn(ev):
	playerTriggerReset(ev['userid'])

def player_death(ev):
	playerTriggerReset(ev['userid'])

def player_say(ev):
	if ev['text'].lower() == "!reload":
		vlog("reloading configuration..")
		loadConfig()
		
	if ev['text'].lower() == "!version":
		vlog("Version %s" % ver)

def load():
	loadConfig()
	gamethread.delayedname(rate, 'timer1', timer)
	msg("loaded v%s" % ver)

def unload():
	gamethread.cancelDelayed('timer1')
	msg("unloaded")

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
	#TODO: update for new system
	return
	"""
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
	"""
	
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
