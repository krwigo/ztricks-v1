import sys, es, os, re, playerlib, gamethread, effectlib, time, popuplib, vecmath, math, sets, shutil, ConfigParser
from time import strftime #strftime("%Y-%m-%d %H:%M:%S")

#
# ztricks v3
#
# This version will only detect and fire events. Absolutely
# no records will be handled.
#

version=3.01
rate=0.01
our_dir=es.getAddonPath('ztricks')
players={}

def timer():
	gamethread.delayedname(rate, 'timer1', timer)
	for userid in playerlib.getUseridList("#alive"):
		check_keys(userid)
		[x,y,z]=es.getplayerlocation(userid)
		for name in triggers.sections():
			if not getTrigger(name, 'enabled', True) == True: continue

			type=getTrigger(name, 'type')
			id=getTrigger(name, 'id')

			if type == 'mainawp':
				if trigger_mainawp(name,x,y,z) == 1:
					msg("player %s in trigger %s [mainawp]" % (userid, name))
					playerTriggerAdd(userid, triggerindex)
					foundTrigger(name, userid, triggerindex)

			if type == 'box':
				if trigger_box(name,x,y,z) == 1:
					msg("player %s in trigger %s [box]" % (userid, name))
					playerTriggerAdd(userid, triggerindex)
					foundTrigger(name, userid, triggerindex)

			if type == 'sphere':
				if trigger_sphere(name,x,y,z) == 1:
					msg("player %s in trigger %s [sphere]" % (userid, name))
					playerTriggerAdd(userid, triggerindex)
					foundTrigger(name, userid, triggerindex)

def trigger_mainawp(name,x,y,z):
	return

def trigger_box(name,x,y,z):
	return
	#[x1,y1,z1]=coord1
	#[x2,y2,z2]=coord2

	# honor wasdfr
	#if wasdfr in ['f','r']:
	#	if not wasdfr == getPlayerDest(userid, 'fr'):
	#		continue
	#	if wasdfr in ['w','a','s','d']:
	#		if not wasdfr == getPlayerDest(userid, 'wasd'):
	#			continue

	# determine if in the box
	#if (px > int(x1) and px < int(x2)) or (px > int(x2) and px < int(x1)):
	#	if (py > int(y1) and py < int(y2)) or (py > int(y2) and py < int(y1)):
	#		if (pz > int(z1) and pz < int(z2)) or (pz > int(z2) and pz < int(z1)):
	#			return id

def trigger_sphere(name,x,y,z):
	return
	#[radius, height]=extra
	#radius=float(radius)

	#[basex,basey,basez]=coord1
	#basex=float(basex)
	#basey=float(basey)
	#basez=float(basez)

	#if not height == "-":
	#	# check if we are within z tolerance first
	#	height=float(height)
	#	if pz < (basez - height) or pz > (basez + height):
	#		continue

	#dist=vecmath.distance([basex,basey,basez], [px,py,pz])
	#if dist <= radius:
	#	return id

def foundTrigger(name, userid, triggerindex):
	#
	# A trigger has been touched.
	# - Fire the event
	# - Detect the trick
	#

	es.event("initialize", 'ontrigger')
	es.event("setstring", 'ontrigger', 'userid',		userid)
	es.event("setstring", 'ontrigger', 'trigger_index',	triggerindex)
	es.event("setstring", 'ontrigger', 'trigger_name',	name)
	es.event("setstring", 'ontrigger', 'player_velocity',	getPlayerVelocity(userid))
	es.event("setstring", 'ontrigger', 'player_mph',	getPlayerVelocity(userid) / 26)
	es.event("setstring", 'ontrigger', 'player_angle',	getPlayerAngle(userid))
	es.event("fire", 'ontrigger')

	# Unless this trigger can be done in the last trick, make
	# the last trick impossible to do again.
	if len(players[userid]['tricklist']) > 0:
		lasttrickindex=players[userid]['tricklist'][-1]
		if lasttrickindex >= 0:
			[pathlist, passlist, points, name]=tricks[lasttrickindex]
			if not triggerindex in pathlist:
				players[userid]['tricklist'].append(-19)

	# Test each trick to see if they have completed it.
	# Find the one with the most nodes while being completed.
	best_time=-1
	best_angle=[]
	best_index=-1
	best_score=-1
	best_speed=0
	for trick in tricks:
		index=tricks.index(trick)
		[pathlist, passlist, points, name]=trick

		if len(pathlist) <= best_score: continue
		[t, angle, speed]=compareList(pathlist, passlist, userid)
		if t < 1: continue

		best_speed=speed
		best_angle=angle
		best_time=t
		best_score=len(pathlist)
		best_index=index

	if best_score == -1: return

	# Average the speed before firing the trick event
	speed_total=0
	for x in best_speed:
		speed_total = speed_total + x
	if speed_total > 0 and len(best_speed) > 1:
		speed_total = (speed_total / len(best_speed)) / 26

	foundTrick(userid, best_index, best_time, best_angle, speed_total)

def foundTrick(userid, trickindex, time_first, angles, speed):
	[pathlist, passlist, points, name]=tricks[trickindex]
	trick_total_time=players[userid]['triggertimes'][-1] - players[userid]['triggertimes'][delta]

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

	players[userid]['tricklist'].append(trickindex)

	trick_name=trickName(name, players[userid]['trick_count'], angles)

	es.event("initialize", 'ontrick')
	es.event("setstring", 'ontrick', 'userid',	userid)
	es.event("setstring", 'ontrick', 'trick_index',	trickindex)
	es.event("setstring", 'ontrick', 'trick_speed',	speed)
	es.event("setstring", 'ontrick', 'trick_time',	seconds)
	es.event("setstring", 'ontrick', 'trick_name',	trick_name)
	es.event("fire", 'ontrick')

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
	global tricks
	global triggers

	tricks=ConfigParser.RawConfigParser()
	triggers=ConfigParser.RawConfigParser()

	if time.time() < 1239401392:
		tricks.read("%s/%s.ini" % (our_dir, 'tricks'))
		triggers.read("%s/%s.ini" % (our_dir, 'triggers'))

	for section in triggers.sections():
		for option in triggers.options(section):
			if option.startswith('cache'):
				triggers.remove_option(section, option)

	msg("configuration loaded. %s triggers, %s tricks" % (len(triggers.sections()), len(tricks.sections())))

def getTriggerArray(i):
	for box in triggers:
		if box[0] == i: return box

##############################################################################################################
# EVENTS
##############################################################################################################
def player_spawn(ev):
	playerTriggerReset(ev['userid'])

def player_death(ev):
	playerTriggerReset(ev['userid'])

def load():
	es.loadevents('declare', "%s/ztricks.res" % our_dir)
	loadConfig()

	#es.addons.registerClientCommandFilter(zts_cc_filter)
	#es.addons.registerSayFilter(sayFilter)
	gamethread.delayedname(rate, 'timer1', timer)
	msg("loaded v%s" % version)

def unload():
	gamethread.cancelDelayed('timer1')
	#es.addons.unregisterClientCommandFilter(zts_cc_filter)
	#es.addons.unregisterSayFilter(sayFilter)
	msg("unloaded")

def player_say(ev):
	text=ev['text']
	words=text.lower().strip('"').split(" ")
	if words[0] == "!version":
		msg("Version %s" % version)

##############################################################################################################
# COMMON FUNCTIONS
##############################################################################################################
def msg(text):
	es.msg("#multi", "#green[ztricks]#default %s" % text)

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

def print_exception():
	print "exception!"
	x=sys.exc_info()
	for i in x:    
	       print "- arg: %s" % i 

