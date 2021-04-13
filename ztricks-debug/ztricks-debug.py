import es

ver=5

def msg(text):
    #es.msg("#multi", "#green[ztricks-debug]#default %s" % text)
    es.msg("#multi", "%s" % text)

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
    d={}
    for key in ['userid','trigger_id','trigger_name','player_velocity','player_mph','player_angle']:
	d[key]=e[key]
    vlog("onTrigger() FIRED %s" % d)
    es.msg('#multi', "#green%s#default touched #green%s#default going #green%.0f#default mph" % (gpn(e['userid']), e['trigger_name'], float(e['player_mph'])))

def ontrick(e):
    d={}
    for key in ['userid','trick_id','trick_speed','trick_time','trick_name','trick_angle']:
	d[key]=e[key]
    vlog("onTrick() FIRED %s" % d)
    es.msg('#multi', "#green%s#default completed #green%s#default in #green%.4f#default seconds going #green%.0f#default mph" % ( gpn(e['userid']), e['trick_name'], float(e['trick_time']), float(e['trick_speed']) ))

def oncombo(e):
    return
    d={}
    for key in ['userid','combo_list']:
	d[key]=e[key]
    vlog("onCombo() FIRED %s" % d)
    es.msg('#multi', "#green%s#default finished a #greencombo#default: %s" % (gpn(e['userid']), d))




