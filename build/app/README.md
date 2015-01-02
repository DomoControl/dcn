Installing
----------

	pip install app

</b>
Usage
----------

#### Application class
	from app import application
	itunes=application("iTunes")
	itunes.open() # open in background
	print itunes.active,itunes.frontmost
	>>> True, False
	itunes.activate() # open and frontmost 
	print itunes.active,itunes.frontmost
	>>> True, True

##### AppleScript 

	itunes.tell("play")

equal to:

	tell application "iTunes"
		play
	end tell

-
	itunes.quit()

#### System Events
	from app.system import events
	print events.processes # processes list
	print events.processes.frontmost # frontmost application
	>>> Terminal
	print "iCal" in events.processes
	>>> True
