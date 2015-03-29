import datetime

legal_time = 2 #Legal time difference

def now():
    return datetime.datetime.now() + datetime.timedelta(hours = legal_time)
    
