import datetime

legal_time = 2


def now():
    return datetime.datetime.now() + datetime.timedelta(hours = legal_time)
    
