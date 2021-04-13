import es, ConfigParser, time, sys, traceback, popuplib
ver=1
our_dir=es.getAddonPath('ztricks-score')
raw = ConfigParser.RawConfigParser()
need_to_write = False


def ztricks_trigger(e):
	#
	# ztricks_trigger
	#
	# When someone touches a trigger, this information is available:
	#	userid
	#	trigger_id	
	#	trigger_name
	#	player_velocity		The players velocity
	#	player_mph		A number of velocity / 26
	#	player_angle		forward, half side ways, backwards
	#

	userid = e['userid']
	steamid = es.getplayersteamid(userid)

	# Store the players last seen time and name
	setValue(steamid, 'name', gpn(userid))
	setValue(steamid, 'last_seen', time.time())


def ztricks_trick(e):
	#
	# ztricks_trick
	#
	# When someone lands a trick successfully, this is available:
	#	userid
	#	trick_id		The internal number of the trick
	#	trick_time		The total time it took to complete the trick
	#	trick_short		The short name for the trick. If you did a awp3, this would be "awp"
	#	trick_points		The point value of the trick
	#	player_velocity		The players velocity. (This must be an average)
	#	player_mph		Velocity / 26
	#	player_angle		forward, half side ways, backwards
	#
	
	userid = e['userid']
	steamid = es.getplayersteamid(userid)
	name = e['trick_name']
	thetime = float(e['trick_time'])
	speed = float(e['player_speed'])
	playername = gpn(userid)
	points = int(e['trick_points'])
	
	# Give them a point
	es.server.queuecmd("es score add %s 1" % e['userid'])
	
	# Give them points
	setValue(steamid, 'points', (getValue(steamid, 'points', 0) + points))
		
	# Say the message
	es.msg("#multi", "#lightgreen%s#default just completed #lightgreen%s#default going #green%.0f#default mph in #lightgreen%.4f#default seconds!!" % (playername, name, speed, thetime))

	# Total count
	# FIXME?
	#cnt = int(getValue(name, 'total_completed', 0))
	#setValue(name, 'total_completed', (cnt + 1))

	###########################################
	# First person to do the trick
	###########################################
	if getValue(name, 'first_player_time', 0) == 0:
		setValue(name, 'first_player_time', time.time())
		setValue(name, 'first_player_name', playername)
		setValue(name, 'first_player_steamid', steamid)

	###########################################
	# TRICK SPEED
	###########################################
	fastest_speed = float(getValue(name, 'fastest_speed_mph', 0))
	slowest_speed = float(getValue(name, 'slowest_speed_mph', 0))
	
	if fastest_speed == 0:
		es.msg("#multi", "#lightgreen%s#default just set the first speed record for #lightgreen%s#default!!" % (playername, name))
		fastest_speed = speed
		setValue(name, 'fastest_speed_first_mph', speed)
		setValue(name, 'fastest_speed_first_name', playername)
		setValue(name, 'fastest_speed_first_steamid', steamid)
		setValue(name, 'fastest_speed_first_date', time.time())
		setValue(name, 'fastest_speed_mph', speed)
		setValue(name, 'fastest_speed_name', playername)
		setValue(name, 'fastest_speed_steamid', steamid)
		setValue(name, 'fastest_speed_date', time.time())
		slowest_speed = speed
		setValue(name, 'slowest_speed_first_mph', speed)
		setValue(name, 'slowest_speed_first_name', playername)
		setValue(name, 'slowest_speed_first_steamid', steamid)
		setValue(name, 'slowest_speed_first_date', time.time())
		setValue(name, 'slowest_speed_mph', speed)
		setValue(name, 'slowest_speed_name', playername)
		setValue(name, 'slowest_speed_steamid', steamid)
		setValue(name, 'slowest_speed_date', time.time())

	elif speed > fastest_speed:
		diff = speed - fastest_speed
		es.msg('#multi', "#lightgreen%s#default just broke the speed record for #lightgreen%s#default by #green%.4f#default mph!!" % (playername, name, diff))
		setValue(name, 'fastest_speed_mph', speed)
		setValue(name, 'fastest_speed_name', playername)
		setValue(name, 'fastest_speed_steamid', steamid)
		setValue(name, 'fastest_speed_date', time.time())
		
	elif speed < slowest_speed:
		diff = slowest_speed - speed
		#es.msg("#multi", "#lightgreen%s#default just broke the slowest speed record for #lightgreen%s#default by #green%.4f#default mph!!" % (playername, name, diff))
		es.tell(userid, "That was the slowest speed for %s!!" % name)
		setValue(name, 'slowest_speed_mph', speed)
		setValue(name, 'slowest_speed_name', playername)
		setValue(name, 'slowest_speed_steamid', steamid)
		setValue(name, 'slowest_speed_date', time.time())

	###########################################
	# TRICK TIME
	###########################################
	fastest_time = float(getValue(name, 'fastest_time_time', 0))
	slowest_time = float(getValue(name, 'slowest_time_time', 0))

	if fastest_time == 0:
		es.msg("#multi", "#lightgreen%s#default just set the first time record for #lightgreen%s#default!!" % (playername, name))
		fastest_time = thetime
		setValue(name, 'fastest_time_first_time', thetime)
		setValue(name, 'fastest_time_first_name', playername)
		setValue(name, 'fastest_time_first_steamid', steamid)
		setValue(name, 'fastest_time_first_date', time.time())
		setValue(name, 'fastest_time_time', thetime)
		setValue(name, 'fastest_time_name', playername)
		setValue(name, 'fastest_time_steamid', steamid)
		setValue(name, 'fastest_time_date', time.time())
		slowest_time = thetime
		setValue(name, 'slowest_time_first_time', thetime)
		setValue(name, 'slowest_time_first_name', playername)
		setValue(name, 'slowest_time_first_steamid', steamid)
		setValue(name, 'slowest_time_first_date', time.time())
		setValue(name, 'slowest_time_time', thetime)
		setValue(name, 'slowest_time_name', playername)
		setValue(name, 'slowest_time_steamid', steamid)
		setValue(name, 'slowest_time_date', time.time())

	elif thetime < fastest_time:
		diff = fastest_time - thetime
		es.msg("#multi", "#lightgreen%s#default just broke the time record for #lightgreen%s#default by #green%.4f#default seconds!!" % (playername, name, diff))
		setValue(name, 'fastest_time_time', thetime)
		setValue(name, 'fastest_time_name', playername)
		setValue(name, 'fastest_time_steamid', steamid)
		setValue(name, 'fastest_time_date', time.time())

	elif thetime > slowest_time:
		diff = thetime - slowest_time
		#es.msg("#multi", "#lightgreen%s#default just broke the slowest time record for #lightgreen%s#default by #green%.4f#default seconds!!" % (playername, name, diff))
		es.tell(userid, "That was the slowest time for %s!!" % name)
		setValue(name, 'slowest_time_time', thetime)
		setValue(name, 'slowest_time_name', playername)
		setValue(name, 'slowest_time_steamid', steamid)
		setValue(name, 'slowest_time_date', time.time())
		

	###########################################
	# Personal Stats
	###########################################
	count = getValue(steamid, "count %s" % name, 0) + 1
	setValue(steamid, "count %s" % name, count)
	if count in [10, 25, 50, 75, 100, 150, 200, 300, 400, 500, 750, 1000]:
		es.msg('#multi', "#lightgreen%s#default just did their #green%sth #lightgreen%s#default!" % (playername, count, name))


def ztricks_combo(e):
	#
	# ztricks_combo
	#
	# When someone ends a combo this event gets called with this data:
	#	userid		The userid who caused the combo to end.
	#	count		The number of tricks that are in the list.
	#	list		A string of trick names joined by '::'. Example: awp x2::spawn hop::razr to last x9
	#	reason		This is the reason the event got fired. Example: movement, death, ..
	#

	count = int(e['count'])
	if count <= 1:
		# Only talk about combos with more than one trick.
		return

	list=e['list'].split('::')
	es.msg('#multi', "#lightgreen%s#default finished a combo: %s" % ( gpn(e['userid']), "#green to#default ".join(list) ) )



################################################################################
# Common Functions
################################################################################

def timer():
	global need_to_write
	if need_to_write:
		writefile()
		
	gamethread.delayedname(5, 'timer', timer)

def msg(text):
	es.msg("#multi", "#green[ztricks-score]#default %s" % text)
	
def myscore():
	userid = es.getcmduserid()
	steamid = es.getplayersteamid(userid)
	es.msg("#multi", "#lightgreen%s's#default score is #lightgreen%s#default!" % (gpn(userid), getValue(steamid, 'points', 0)))
	
def load():
	global raw
	raw.read("%s/score.ini" % our_dir)

	es.regsaycmd('!points', 'ztricks-score/myscore', 'Tells the player their score')
	
	timer()
	msg("loaded")

def unload():
	es.unregsaycmd('!points')
	gamethread.cancelDelayed('timer')
	writefile()
	msg("unloaded")

def player_say(ev):
	userid = ev['userid']
	if ev['text'].lower() == "!version": msg("Version %s" % ver)
	if ev['text'].lower() == "!stats": stats_menu(userid)
	if ev['text'].lower() == "!mystats": mystats_menu(userid)
	
def writefile():
	global raw
	global need_to_write

	F=open("%s/score.ini" % our_dir,'wb')
	raw.write(F)
	F.close()
	
	need_to_write = False
	
def setValue(section, key, value):
	global raw
	global need_to_write

	need_to_write = True

	if not raw.has_section(section): raw.add_section(section)
	raw.set(section, key, value)

def getValue(section, key, value=None):
	try:
		r=raw.get(section, key)
		if isInt(r): return int(r)
		return r
	except:
		return value

def isInt(input):
	try:	return int(input)
	except: pass

def gpn(id):
	return es.getplayername(id)

################################################################################
# Menus
################################################################################

def stats_menu(userid):
	# list all tricks
	myPopup = popuplib.easymenu("trick records for %s" % userid, None, stats_select)
	myPopup.settitle("trick records")
	myPopup.c_beginsep=None
	myPopup.c_pagesep=None
	myPopup.c_endsep=None

	x=raw.sections()
	x.sort()
	for name in x:
		if not name.startswith("STEAM"):
			myPopup.addoption(name, "%s" % (name))

	myPopup.send(userid)

def epochtime(i):
	return time.asctime( time.localtime( float(i) ) )

def stats_select (userid, choice, popupid):
	myPopup = popuplib.create('stat_popup')
	myPopup.addline(choice)
	myPopup.addline(" "*80)
	#time.asctime( time.localtime( float(v) ) )
	#myPopup.addline("   %s: %s" % (k,v))

	# Broken
	#myPopup.addline("Times completed: %s" % getValue(choice, 'total_completed', 1))
	#myPopup.addline(" ")

	# First
	myPopup.addline("First Person:")
	myPopup.addline("  %s" % getValue(choice, 'first_player_name'))
	myPopup.addline("  %s" % epochtime(getValue(choice, 'first_player_time')))
	myPopup.addline(" ")

	# Speed
	myPopup.addline("Fastest Person (Speed):")
	myPopup.addline("  %s" % getValue(choice, 'fastest_speed_name'))
	myPopup.addline("  %.4f mph" % float(getValue(choice, 'fastest_speed_mph')))
	myPopup.addline("  %s" % epochtime(getValue(choice, 'fastest_speed_date')))
	myPopup.addline(" ")
	
	myPopup.addline("Slowest Person (Speed):")
	myPopup.addline("  %s" % getValue(choice, 'slowest_speed_name'))
	myPopup.addline("  %.4f mph" % float(getValue(choice, 'slowest_speed_mph')))
	myPopup.addline("  %s" % epochtime(getValue(choice, 'slowest_speed_date')))
	myPopup.addline(" ")

	# Time
	myPopup.addline("Fastest Person (Time):")
	myPopup.addline("  %s" % getValue(choice, 'fastest_time_name'))
	myPopup.addline("  %.4f" % float(getValue(choice, 'fastest_time_time')))
	myPopup.addline("  %s" % epochtime(getValue(choice, 'fastest_time_date')))
	myPopup.addline(" ")
	
	myPopup.addline("Slowest Person (Time):")
	myPopup.addline("  %s" % getValue(choice, 'slowest_time_name'))
	myPopup.addline("  %.4f" % float(getValue(choice, 'slowest_time_time')))
	myPopup.addline("  %s" % epochtime(getValue(choice, 'slowest_time_date')))
	myPopup.addline(" ")

	#myPopup.addline("   %s: %s" % (k,v))

	myPopup.addline('->9 Back')
	myPopup.addline('->0 Close')
	myPopup.menuselect = stats_select_func
	myPopup.send(userid)

def stats_select_func(userid, choice, popupid):
	print "stats_select_func(%s, %s, %s)" % (userid, choice, popupid)
	
	choice = int(choice)
	if choice == 9 or choice == 8:
		# restart the menu
		stats_menu(userid)

def print_exception():
	return
	formatted_lines = traceback.format_exc().splitlines()
	for line in formatted_lines:
		es.tell(4, "EX: %s" % line)

def mystats_menu(userid):
	global raw
	steamid = es.getplayersteamid(userid)
	
	myPopup = popuplib.create('stat_popup')
	myPopup.addline("Your Stats")
	myPopup.addline('   ')
	myPopup.addline("  points: %s" % getValue(steamid, 'points', 0))
	myPopup.addline('   ')
	myPopup.addline('->0 Close')
	myPopup.send(userid)

def mystats_select (userid, choice, popupid):
	return




