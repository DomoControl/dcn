class cls(object):
    reference = None

    def __init__(self,reference):
        self.reference=reference

    @property
    def properties(self):
        """return list of self.reference.properties()"""
        if self.reference:
            return filter(
                lambda p:p!="class_",
                map(
                    lambda p:str(p).replace("k.",""),
                    self.reference.properties().keys()
                )
            )
        else:
            return []

    def __getattribute__(self,k):
        """return app(name).reference.k()"""
        try:  # exists
            #print "__getattribute__",k
            return object.__getattribute__(self, k)
        except AttributeError, e:  # not exists
            #print str(e)
            #print self.properties
            if k in self.properties:
                #print "k in self.properties"
                return getattr(self.reference,k)()
            else:
                #print "%s not in self.properties" % k
                raise AttributeError(k)
        except Exception, e:
            print type(e), str(e)

    def __setattr__(self, k,v):
        """app(name).reference.k.set(v)"""
        if hasattr(self,k):
            if k in self.properties and not hasattr(type(self),k):
                getattr(self.reference,k).set(v)
            else:
                object.__setattr__(self,k, v)
        else:
            AttributeError(k)

    def delete(self):
        """delete this object from iCal"""
        self.reference.delete()

    def __eq__(self,t):
        """return True if references equal"""
        return self.__class__==t.__class__ and \
        self.uid==t.uid