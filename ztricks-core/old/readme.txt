
4:08 PM - z.: I should warn you though
4:08 PM - z.: It can be very picky right now.
4:08 PM - z.: For example if you write a line with: enabled = true
4:08 PM - z.: It will probably break because it's not True
4:09 PM - z.: Let's see
4:09 PM - z.: tricks have to be like this
4:09 PM - z.: [name of the trick]
4:09 PM - z.: path=1,2,3
4:09 PM - z.: pass=1,2,3
4:09 PM - z.: id=1
4:09 PM - z.: You do not have to write the pass. Use it only if you have a number to put there.
4:10 PM - z.: No spaces between the 1,2,3 like 1, 4, 5
4:10 PM - z.: On to triggers
4:10 PM - Pharmacist | DCHservers.com: i c
4:10 PM - z.: [name of the trigger]
4:10 PM - z.: the name MUST be unique
4:10 PM - Pharmacist | DCHservers.com: k
4:10 PM - z.: a trigger must have an id too
4:10 PM - z.: and shape
4:11 PM - z.: shape can be box or sphere
4:11 PM - z.: a box uses coord1 and coord2
4:11 PM - z.: a sphere only uses coord1
4:11 PM - z.: symetrical = True if you want it to be replicated to the ct side too
4:11 PM - z.: in both tricks and triggers, you can use enabled=False to tell it not to use it.
4:12 PM - z.: By default it will be True
4:12 PM - z.: Just make it good practice to only put what you want.
4:12 PM - z.: If it's not symetrical don't even write that line
4:12 PM - z.: triggers also have a new speed setting
4:12 PM - z.: speed_min = 100
4:13 PM - z.: speed_max = 500
4:13 PM - z.: Those are velocity numbers, NOT mph!
4:13 PM - z.: oh and sphere must have a radius= number. height= is optional as before.
4:14 PM - z.: If it finds a problem it's supposed to disable the trick or trigger automatically but that's kinda shakey :/
4:14 PM - Pharmacist | DCHservers.com: i c
4:15 PM - z.: The plan is that you would never touch the actual ini files. It should be menu driven but ughhhh :D