from time import sleep
import appscript
from envoy import run
from osascript import osascript

class cls(object):
    name=None
    def __init__(self,name=None):
        self.name=name

    @property
    def app(self):
        return appscript.app(self.name)

    def activate(self):
        """Activate Application"""
        self.app.activate()
        counter=0
        while not self.frontmost: # wait for animation 
            sleep(0.01) # 
            counter+=0.01
            if counter>1:
                break
        return self

    @property
    def active(self):
        """return True if application is active"""
        return self.app.isrunning()

    def open(self):
        """open app if not active"""
        if not self.active:
            run("open -a %s" % self.name)

    def tell(self,code,flags=None):
        """Tell application %(self.name)s
    %(code)s
end Tell
        """
        return osascript("""
tell application "%s"
    %s
end tell
""" % (self.name,code),flags)

    def keystroke(self,*args,**kwargs):
        """applescript.app('System Events').keystroke"""
        self.activate() # make app frontmost
        appscript.app('System Events').keystroke(*args,**kwargs)
        return self

    def togglescreen(self):
        raise NotImplementedError("togglescreen")

    def fullscreen(self):
        """Enter Application fullscreen mode"""
        self.activate()
        if not self.isfullscreen:
            self.togglescreen()
            counter=0
            while not self.isfullscreen: # animation/desktop switch?
                sleep(0.01) #
                counter+=0.01
                if counter>1:
                    break
        return self

    def normalscreen(self):
        """Exit Application fullscreen mode"""
        if self.isfullscreen:
            self.activate()
            self.togglescreen()
            counter=0
            while self.isfullscreen: # animation/desktop switch?
                sleep(0.01) # 
                counter+=0.01
                if counter>1:
                    break
        return self

    @property
    def isfullscreen(self):
        """return true if application is fullscreen"""
        raise NotImplementedError("isfullscreen")

    @property
    def frontmost(self):
        """return True if Application is frontmost"""
        return type(self)("System Events").\
        tell("name of (first process whose frontmost is true)").lower()==self.name.lower()

    def quit(self):
        """Quit Application"""
        if self.active:
            self.app.quit()
            counter=0
            while self.active:
                sleep(0.01) # sleep for update system events
                counter+=0.01
                if counter>5:
                    break
        return self