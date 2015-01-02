class cls(list):
    keys=[]
    def __init__(self, data=[], keys=["uid"]):
        self.keys=keys
        list.__init__(self,data)

    def __contains__(self,k):
        try:
            return self[k] is not None
        except:
            return False
        
    def __getitem__(self,key):
        """return object by key"""
        result=[]
        if str(key).isdigit():
            return self[:][key]
        else:
            for i in self[:]:
                for k in self.keys:
                    if getattr(i,k)==key:
                        result.append(i)
            if len(result)>0:
                if len(result)==1:
                    return result[0]
                else:
                    return result
        raise KeyError(key)

    @property
    def first(self):
        """return first item"""
        return self[:]