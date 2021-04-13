import es, traceback, effectlib
#, usermsg, playerlib

ver=6
players = {}

def check_keys(userid):
    global players
    if not players.has_key(userid):
	players[userid]={}
	players[userid]['show_debug'] = 0
	players[userid]['show_line'] = 0
	players[userid]['line_path'] = []
	vlog("created key %s" % userid)

def msg(text):
    es.msg("#multi", "#green[ztricks-debug]#default %s" % text)

def vlog(text):
    return
    print "[ztricks-debug] %s" % text
    
def load():
    es.regclientcmd("zdebug", "ztricks-debug/toggledebug")
    es.regclientcmd("zdebugline", "ztricks-debug/toggleline")
    msg("loaded")

def unload():
    es.unregclientcmd("zdebug")
    es.unregclientcmd("zdebugline")
    msg("unloaded")

def player_say(ev):
    if ev['text'].lower() == "!version":
	msg("Version %s" % ver)
	
def gpn(id):
    return es.getplayername(id)
    
def toggleline():
    global players
    userid = es.getcmduserid()
    check_keys(userid)
    
    c = players[userid]['show_line']
    if c == 0:
	es.tell(userid, "You will now draw lines, run again to disable")
	players[userid]['show_line'] = 1
    else:
	es.tell(userid, "You will not draw lines, run again to enable")
	players[userid]['show_line'] = 0

    players[userid]['line_path'] = []

def toggledebug():
    global players
    userid = es.getcmduserid()
    check_keys(userid)
    
    c = players[userid]['show_debug']
    if c == 0:
	es.tell(userid, "You will now see debugging messages, run again to disable")
	players[userid]['show_debug'] = 1
    else:
	es.tell(userid, "You will not see anymore debugging messages, run again to enable")
	players[userid]['show_debug'] = 0

    players[userid]['line_path'] = []

def print_exception():
        return
	formatted_lines = traceback.format_exc().splitlines()
	for line in formatted_lines:
		msg("EX: %s" % line)
		
def ztricks_playerdeath(e):
    global players
    userid = int(e['userid'])
    players[userid]['line_path'] = []

def ztricks_trigger(e):
    global players

    try:
	userid = int(e['userid'])
	id = int(e['trigger_id'])
	name = e['trigger_name']
	vel = float(e['player_velocity'])
	mph = float(e['player_mph'])
	ang = e['player_angle']
	x = float(e['player_x'])
	y = float(e['player_y'])
	z = float(e['player_z'])

	# Store these coordinates
    	players[userid]['line_path'].append([x,y,z])

	if players[userid]['show_debug'] == 1:
	    es.tell(userid,"touched trigger name=%s id=%s mph=%.0f ang=%s" % (name, id, mph, ang))
	
	# Draw this line to last
	if players[userid]['show_line'] == 1:
	    path = players[userid]['line_path']
	    if len(path) > 1: drawline(path[-1], path[-2])

    except:
	print_exception()

def drawline(coord1, coord2):
	vlog("drawline():")
	vlog("- coord1: %s" % coord1)
	vlog("- coord2: %s" % coord2)
	effectlib.drawLine(coord1, coord2, model="materials/sprites/laser.vmt", halo="materials/sprites/halo01.vmt", seconds=10, width=20, red=0, green=255, blue=0)

def ztricks_trick(e):
    global players
    userid = int(e['userid'])
    msg("%s did %s!!" % (gpn(userid), name))
    return

    if setting(userid) == 0: return
    
    id = int(e['trick_id'])
    name = e['trick_name']

    es.tell(userid, '#multi', "finished trick name->#green%s#default id->#green%s" % (name, id))


def ztricks_combo(e):
    return
    if int(e['count']) <= 1:
	# Only talk about combos with more than one trick.
	return

    list=e['list'].split('::')
    es.msg('#multi', "#lightgreen%s#default finished a #lightgreencombo#default: %s" % (gpn(e['userid']), "#green to#default ".join(list)))
    es.msg('#multi', "#lightgreenThe reason the combo ended was: %s" % e['reason'])


