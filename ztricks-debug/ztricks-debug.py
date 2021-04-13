import es
#, usermsg, playerlib

ver=6

def msg(text):
    es.msg("#multi", "#green[ztricks-debug]#default %s" % text)

def vlog(text):
    return
    print "[ztricks-debug] %s" % text
    
def load():
    msg("loaded")

def unload():
    msg("unloaded")

def player_say(ev):
    if ev['text'].lower() == "!version":
	msg("Version %s" % ver)
	
def gpn(id):
    return es.getplayername(id)
    
def ztricks_trigger(e):
    #es.msg('#multi', "#green%s#default touched #green%s#default going #green%.0f#default mph" % (gpn(e['userid']), e['trigger_name'], float(e['player_mph'])))
    return

def ztricks_trick(e):
    es.server.queuecmd("es score add %s 1" % e['userid'])
    es.msg('#multi', "#lightgreen%s#default completed #lightgreen%s#default in #lightgreen%.4f#default seconds going #lightgreen%.0f#default mph" % ( gpn(e['userid']), e['trick_name'], float(e['trick_time']), float(e['player_speed']) ))

def ztricks_combo(e):
    #msg("#lightgreenending %s's combo of #green%s#lightgreen tricks because #green%s" % (gpn(e['userid']), e['count'], e['reason']))

    if int(e['count']) <= 1:
	# Only talk about combos with more than one trick.
	return

    list=e['list'].split('::')
    es.msg('#multi', "#lightgreen%s#default finished a #lightgreencombo#default: %s" % (gpn(e['userid']), "#green to#default ".join(list)))
    es.msg('#multi', "#lightgreenThe reason the combo ended was: %s" % e['reason'])


