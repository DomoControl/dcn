import sht21
import time

print sht21.SHT21(1).read_temperature()
time.sleep(2)
print sht21.SHT21(1).read_humidity()

print dir(sht21.SHT21)
print help(sht21.SHT21)





