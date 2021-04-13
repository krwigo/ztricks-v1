import es, os, re, playerlib, gamethread, effectlib, urllib
from time import strftime #strftime("%Y-%m-%d %H:%M:%S")

#
# ztricks
# 20090227 - initial
# 20090228 - tricks and detection working
# 20090302 - spawning clears list
# 20090303 - added player death to reset
#

rate=0.05								# timer rate
max_idle=60								# seconds
config_file='cstrike/addons/eventscripts/ztricks/zconfig.txt'		# configuration file

global players
players={}
triggers=[]
tricks=[]

def player_spawn(ev):
	global players
	userid=ev['userid']
	check_keys(userid)
	players[userid]['triggerlist'].append(-10)

def check_keys(userid):
	global players
	if not players.has_key(userid):
		players[userid]={}
	if not players[userid].has_key('x'):
		players[userid]['x']=0
		players[userid]['y']=0
		players[userid]['z']=0
		players[userid]['idletime']=0
		players[userid]['triggerlist']=[-1]
		players[userid]['tricklist']=[]
		players[userid]['points']=0
		players[userid]['quiet']=1

def timer():
	gamethread.delayedname(rate, 'timer1', timer)
	playerlist = playerlib.getUseridList("#alive")
	for userid in playerlist:
		check_keys(userid)

		# get this players xyz
		myPlayer = playerlib.getPlayer(userid)
		x = myPlayer.attributes['x']
		y = myPlayer.attributes['y']
		z = myPlayer.attributes['z']

		# compare to idle check
		if x != players[userid]['x'] or y != players[userid]['y'] or z != players[userid]['z']:
			players[userid]['idletime']=0
		#else:
		#	#players[userid]['idletime'] = players[userid]['idletime'] + (1 / rate)
		#	#es.tell(userid, "#lightgreen", "you have been idle for %s seconds" % players[userid]['idletime'])
		#	#print "- player has not moved, has been idle for %d seconds" % players[userid]['idletime']
		#	#if players[userid]['idletime'] > max_idle:
		#	#	es.msg("#lightgreen", "- max idle was hit for player %s" % userid)
		#	#	es.server.cmd("kickid %s" % userid)

		# compare to triggers
		trig=getTrigger(x, y, z)
		if trig >= 0:
			if players[userid]['triggerlist'][-1] != trig:
				if players[userid]['quiet'] == 0: es.tell(userid, "#multi", "#lightgreenyou just triggered #green%s#lightgreen !!" % getTriggerName(trig))
				players[userid]['triggerlist'].append(trig)

				best_score=-1
				best_index=-1
				# score is based on the length of the trick, more=better
				# so find the longest trick that has been completed and go with that.
				for trk in tricks:
					[pathlist, path, points, name]=trk
					if len(pathlist) > best_score and compareList(pathlist, players[userid]['triggerlist']) > 0:
						# new best!
						best_score=len(pathlist)
						best_index=tricks.index(trk)

				if best_score > -1:
					[pathlist, path, points, name]=tricks[best_index]

					# award them some points
					players[userid]['points'] = players[userid]['points'] + int(points)

					# add this trick to the list
					players[userid]['tricklist'].append(best_index)

					# display the message
					es.msg("#multi", "#lightgreen%s just completed #green%s#lightgreen !!" % (getPlayerName(userid), name))
					#es.msg("#multi", "#lightgreen%s just completed #green%s#lightgreen !! worth #green%s#lightgreen points !!" % (getPlayerName(userid), name, points))
					#es.tell(userid, "#multi", "#lightgreenyou now have a total of #green%s#lightgreen points" % players[userid]['points'])


def compareList(pathlist, userlist):
	if len(pathlist) > len(userlist): return -2
	delta=int("-%s" % len(pathlist))

	use_stripped=1

	# check to see if an optional trigger is in the pathlist, if so then check the old fashioned way
	for item in pathlist:
		if int(item) >= 1000:
			use_stripped=0

	if use_stripped == 1:
		cleanedlist=[]
		for item in userlist:
			if int(item) >= 1000: continue
			cleanedlist.append(item)

		#print "compareList(): path->%s user->%s cleaned->%s using cleaned version" % (pathlist, userlist, cleanedlist)
		if cleanedlist[delta:] == pathlist: return 1
	else:
		#print "compareList(): path->%s user->%s forced to use old because an optional was requested" % (pathlist, userlist[delta:])
		if userlist[delta:] == pathlist:
			return 1
		else:
			return -2
	return -1

def getPlayerName(userid):
	thePlayer = playerlib.getPlayer(userid)
	return thePlayer.attributes['name']

def loadConfig():
	global triggers
	global tricks
	print "loading configuration"
	print "current directory: %s" % os.getcwd()
	f=open(config_file, 'r')
	if not f:
		print "unable to load configuration"
		return
	triggers=[]
	tricks=[]
	lines=f.readlines()
	for line in lines:
		m=re.match("^(\w+)", line)
		if not m: continue
		[type]=m.groups()

		# tricks are [pathlist, path, points, name]
		if type == "trick":
			m=re.match("trick\t+(.*?)\t+(\d+)\t+(.*)", line)
			if not m: continue
			[path, points, name]=m.groups()
			print "found trick [%s] [%s] [%s]" % (path, points, name)
			es.msg("- found trick: %s" % name)
			pathlist=path.split(',')
			tricks.append([pathlist, path, points, name])

		# triggers are [id, name, x1, y1, z1, x2, y2, z2]
		if type == "trigger":
			m=re.match("trigger\t+(\d+)\t+(.*?)\t+(.*?)\t+(.*)", line)
			if not m: continue
			[id, point1, point2, name]=m.groups()
			[x1, y1, z1]=re.split(',', point1)
			[x2, y2, z2]=re.split(',', point2)
			if not x1 < x2:
				es.msg("- WARNING x is bad! should be %s,%s,%s %s,%s,%s (%s %s)" % (x2,y1,z1, x1,y2,z2, id, name))
				tmp=x1
				x1=x2
				x2=tmp
			if not y1 > y2:
				es.msg("- WARNING y is bad! should be %s,%s,%s %s,%s,%s (%s %s)" % (x1,y2,z1, x2,y1,z2, id, name))
				tmp=y1
				y1=y2
				y2=tmp
			if not z1 > z2:
				es.msg("- WARNING z is bad! should be %s,%s,%s %s,%s,%s (%s %s)" % (x1,y1,z2, x2,y2,z1, id, name))
				tmp=z1
				z1=z2
				z2=tmp
			triggers.append([id, name, x1, y1, z1, x2, y2, z2])
	
	#print "triggers"
	#for box in triggers:
	#	#print "- %s" % box
	#
	#print "\ntricks";
	for box in tricks:
		[pathlist, path, points, name]=box
		#print "- %s: points->[%s] path->[%s] pathlist:%s" % (name, points, path, pathlist)

	es.msg("done.")
	return "found %s triggers, %s tricks" % (len(triggers), len(tricks))

def getTriggerName(i):
	for box in triggers:
		if box[0] == i:
			return box[1]
	return "error"

def getTrigger(px, py, pz):
	# check each defined trigger to see if xyz matches and return the triggers id
	for box in triggers:
		[id, name, x1, y1, z1, x2, y2, z2]=box
		if (px > int(x1) and px < int(x2)) or (px > int(x2) and px < int(x1)):
			if (py > int(y1) and py < int(y2)) or (py > int(y2) and py < int(y1)):
				if (pz > int(z1) and pz < int(z2)) or (pz > int(z2) and pz < int(z1)):
					return id
	return -1

def load():
	es.msg("ztricks loaded")
	loadConfig()
	gamethread.delayedname(rate, 'timer1', timer)

def unload():
	gamethread.cancelDelayed('timer1')
	es.msg("ztricks unloaded")

def sayFilter(userid, text, teamOnly):
	global players
	n = text.strip('"')
	n = n.split(" ")
	n = n[0].lower()
	if n in ['rank', '!rank', '!score']:
		es.msg("#lightgreen", "%s has %s points!" % (getPlayerName(userid), players[userid]['points']))
		return (0, "", 0)

	if n == "!zdownload":
		es.msg("downloading new configuration file..")

		#>>> import urllib
		#>>> opener = urllib.FancyURLopener({})
		#>>> f = opener.open("http://www.python.org/")
		#>>> f.read()

		opener = urllib.FancyURLopener({})
		f = opener.open("http://es.darksidebio.com/es/zconfig.txt")
		if not f:
			es.msg("unable to open")
			return (0, "", 0)
		data=f.read()

		#mysock = urllib.urlopen("http://es.darksidebio.com/es/zconfig.txt")
		#data = mysock.read()

		oFile = open(config_file,'wb')
		oFile.write(data)
		oFile.close

		loadConfig()
		return (0, "", 0)

	if n == "!drawbox":
		for trigger in triggers:
			[id, name, x1, y1, z1, x2, y2, z2]=trigger
			effectlib.drawBox([x1, y1, z1], [x2, y2, z2], seconds = 60)
			effectlib.drawBox([x2, y2, z2], [x1, y1, z1], seconds = 60)
		return (0, "", 0)

	if n == "!quiet":
		c=players[userid]['quiet']
		if c == 1:
			es.tell(userid, "#lightgreen", "you will now see more messages")
			players[userid]['quiet']=0
		else:
			es.tell(userid, "#lightgreen", "debug messages have been disabled")
			players[userid]['quiet']=1
		return (0, "", 0)

	if n == "!reload":
		es.msg("reloading configuration")
		es.msg(loadConfig())
		return (0, "", 0)

	return (userid, text, teamOnly)

def player_death(ev):
	global players
	userid=ev['userid']
	players[userid]['triggerlist'].append(-10)

es.addons.registerSayFilter(sayFilter)

