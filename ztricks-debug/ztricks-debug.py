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
    
def ontrigger(e):
    return
    # This event fires when a player touches any trigger that is valid.
    #es.msg('#multi', "#green%s#default touched #green%s#default going #green%.0f#default mph" % (gpn(e['userid']), e['trigger_name'], float(e['player_mph'])))
    #usermsg.saytext2("#all", playerlib.getPlayer(e['userid']).attributes['index'], "test1 \x01meow \x02monkey \x03raven")

def ontrick(e):
    # This event fires when a player completes a trick.
    es.msg('#multi', "#lightgreen%s#default completed #lightgreen%s#default in #lightgreen%.4f#default seconds going #lightgreen%.0f#default mph" % ( gpn(e['userid']), e['trick_name'], float(e['trick_time']), float(e['trick_speed']) ))

def oncombo(e):
    # This event fires when a player stops moving, dies, or cheats.
    ## 20090413 - when velocity < 10
    ##          - when they die
    list=e['list'].split('::')
    if len(list) > 1:
        es.msg('#multi', "#lightgreen%s#default finished a #lightgreencombo#default: %s" % (gpn(e['userid']), "#green to#default ".join(list)))




