import domocontrol
import smbus



a = smbus.SMBus(1)
print dir(a)
print help(a)
print a.read_byte_data(33, 2)
#print a.read_byte_data(1, 33, 0)
