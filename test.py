import sht21

a = sht21.SHT21(1)
print dir(a)
print a.read_humidity()
