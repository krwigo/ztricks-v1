import es, ConfigParser, time, sys, traceback, popuplib
ver=1
our_dir=es.getAddonPath('ztricks-score')
raw = ConfigParser.RawConfigParser()

def msg(text):
	es.msg("#multi", "#green[ztricks-score]#default %s" % text)
	
def load():
	global raw
	raw.read("%s/score.ini" % our_dir)
	msg("loaded")

def unload():
	msg("unloaded")

def buildStats():
	# read everything from raw and format it nicely in stat_file
	try:
		#/69.90.189.203 port 27035/cstrike/addons/eventscripts/ztricks-score/
		#eventscripts_gamedir
		file=open("%s/temp.txt" % es.ServerVar("eventscripts_gamedir"), 'wb')
			
		for section in raw.sections():
			if section.startswith("STEAM"):
				continue
			else:
				#assume its a trick
				file.write("%s\n" % section)
				for (key, val) in raw.items(section):
					file.write("- %s: %s\n" % (key, val))
				file.write("\n")
	
		file.close()
	except:
		msg("exception")
		formatted_lines = traceback.format_exc().splitlines()
		for line in formatted_lines:
			msg("EX: %s" % line)		

def player_say(ev):
	userid = ev['userid']
	
	if ev['text'].lower() == "!version":
		msg("Version %s" % ver)
		
	if ev['text'].lower() == "!stats":
		stats_menu(userid)
		
	if ev['text'].lower() == "!mystats":
		mystats_menu(userid)

	#	buildStats()
	#	es.server.cmd("est_motd_f %s stats 0 temp.txt" % ev['userid'])
	
def setValue(section, key, value):
	global raw
	try:
		if not raw.has_section(section): raw.add_section(section)
		raw.set(section, key, value)
		F=open("%s/score.ini" % our_dir,'wb')
		raw.write(F)
		F.close()
	except:
		pass

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
	
#def ontrigger(e):
#	return
#	# This event fires when a player touches any trigger that is valid.
#	#es.msg('#multi', "#green%s#default touched #green%s#default going #green%.0f#default mph" % (gpn(e['userid']), e['trigger_name'], float(e['player_mph'])))
#	#usermsg.saytext2("#all", playerlib.getPlayer(e['userid']).attributes['index'], "test1 \x01meow \x02monkey \x03raven")

#"ztricks-core"
#{
#    "ontrigger"
#    {
#        "userid"            "string"
#        "trigger_id"	    "string"
#        "trigger_name"      "string"
#        "player_velocity"   "string"
#        "player_mph"        "string"
#        "player_angle"      "string"
#    }
#    "ontrick"
#    {
#        "userid"            "string"
#        "trick_id"          "string"
#        "trick_speed"       "string"
#        "trick_time"        "string"
#        "trick_name"        "string"
#	"trick_angle"	    "string"
#	"trick_short"	    "string"
#	"trick_speed_velocity" "string"
#    }
#    "oncombo"
#    {
#	"userid"	    "string"
#	"list"	            "string"
#    }
#}




def stats_menu(userid):
	# list all tricks
	myPopup = popuplib.easymenu("trick records for %s" % userid, None, stats_select)
	myPopup.settitle("trick records")
	myPopup.c_beginsep=None
	myPopup.c_pagesep=None
	myPopup.c_endsep=None

	for name in raw.sections():
		if not name.startswith("STEAM"):
			myPopup.addoption(name, "%s" % (name))

	myPopup.send(userid)

def stats_select (userid, choice, popupid):
	myPopup = popuplib.create('stat_popup')
	myPopup.addline(choice)
	myPopup.addline('   ')

	width = 0
	for (k, v) in raw.items(choice):
		k.replace("_", " ")
		if len(k) > width: width=len(k)

	for (k, v) in raw.items(choice):
		if not k in ['speed_holder_name', 'speed', 'time_holder_name', 'time', 'first_player_name', 'speed_time', 'time_time']:
			continue

		if k in ['time_time', 'speed_time']:
			try:	v=time.asctime( time.localtime( float(v) ) )
			except:	pass

		#" "*(width - len(k))
		myPopup.addline("   %s: %s" % (k,v))

	myPopup.addline('   ')
	myPopup.addline('->0 Close')
	myPopup.send(userid)



def print_exception():
	return
	formatted_lines = traceback.format_exc().splitlines()
	for line in formatted_lines:
		es.tell(4, "EX: %s" % line)


def mystats_menu(userid):
	global raw
	
	# list all tricks
	myPopup = popuplib.easymenu("mystats for %s" % userid, None, mystats_select)
	myPopup.settitle("my stats")
	myPopup.c_beginsep=None
	myPopup.c_pagesep=None
	myPopup.c_endsep=None

	steamid = es.getplayersteamid(userid)

	c=0
	try:
		for (k, v) in raw.items(steamid):
			c += 1
			myPopup.addoption("   %s: %s" % (k, v))
	except:
		es.tell(userid, "There was a problem, this isnt working yet!")
		return

	if c == 0:
		es.tell(userid, "You don't have any stats yet.")
		return

	myPopup.send(userid)

def mystats_select (userid, choice, popupid):
	return





def ontrick(e):
	show_personal_speed = 1
	show_personal_time = 1
	
	userid = e['userid']
	steamid = es.getplayersteamid(userid)
	name = e['trick_name']
	thetime = float(e['trick_time'])
	speed = float(e['trick_speed'])

	# update their general stats
	setValue(steamid, 'name', gpn(userid))
	setValue(steamid, 'last_seen', time.time())

	# trick first person
	if getValue(name, 'first_player_time', 0) == 0:
		setValue(name, 'first_player_time', time.time())
		setValue(name, 'first_player_name', gpn(userid))
		setValue(name, 'first_player_steamid', steamid)

	# trick times
	best_speed = float(getValue(name, 'speed', 0))
	if speed > best_speed:
		diff = speed - best_speed
		if best_speed == 0:
			es.msg('#multi', "#lightgreen%s#default just set the speed record for #lightgreen%s#default with #green%.4f#default mph!!" % ( gpn(userid), name, speed))
		else:
			es.msg('#multi', "#lightgreen%s#default just broke the speed record for #lightgreen%s#default by #green%.4f#default mph!!" % ( gpn(userid), name, diff))

		show_personal_speed = 0
		
		setValue(name, 'speed', speed)
		setValue(name, 'speed_holder_name', gpn(userid))
		setValue(name, 'speed_holder_steamid', steamid)
		setValue(name, 'speed_time', time.time())

	best_time = float(getValue(name, 'time', 10000))
	if thetime < best_time:
		diff = best_time - thetime
		if best_time == 10000:
			es.msg('#multi', "#lightgreen%s#default just set the time record for #lightgreen%s#default with #green%.4f#default seconds!!" % ( gpn(userid), name, thetime))
		else:
			es.msg('#multi', "#lightgreen%s#default just broke the time record for #lightgreen%s#default by #green%.4f#default seconds!!" % ( gpn(userid), name, diff))

		show_personal_time = 0

		setValue(name, 'time', thetime)
		setValue(name, 'time_holder_name', gpn(userid))
		setValue(name, 'time_holder_steamid', steamid)
		setValue(name, 'time_time', time.time())
	
	# personal times
	count = getValue(steamid, "count %s" % name, 0) + 1
	setValue(steamid, "count %s" % name, count)
	if count in [10, 50, 100, 200, 500, 1000]:
		es.msg('#multi', "#lightgreen%s#default just did their #green%sth #lightgreen%s#default!" % ( gpn(userid), count, name))

	best_speed = float(getValue(steamid, "speed %s" % name, 0))
	if speed > best_speed:
		diff = speed - best_speed
		setValue(steamid, "speed %s" % name, speed)
		if best_speed > 0 and show_personal_speed == 1: es.msg('#multi', "#lightgreen%s#default just broke their own speed record for #lightgreen%s#default!!" % (gpn(userid), name))
		
	best_time = float(getValue(steamid, "time %s" % name, 10000))
	if thetime < best_time:
		diff = best_time - thetime
		setValue(steamid, "time %s" % name, thetime)
		if best_time != 10000 and show_personal_time == 1: es.msg('#multi', "#lightgreen%s#default just broke their own time record for #lightgreen%s#default by #green%.4f#default!!" % ( gpn(userid), name, diff ))

#def oncombo(e):
#	return
#	# This event fires when a player stops moving, dies, or cheats.
#	## 20090413 - when velocity < 10
#	##		  - when they die
#	list=e['list'].split('::')
#	es.msg('#multi', "#lightgreen%s#default finished a #lightgreencombo#default: %s" % (gpn(e['userid']), "#green to#default ".join(list)))




