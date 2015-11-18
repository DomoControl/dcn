#!/usr/bin/python

import smbus

bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

DEVICE_ADDRESS = 0x27      #7 bit address (will be left shifted to add the read write bit)
DEVICE_REG_MODE1 = 7
DEVICE_REG_LEDOUT0 = 0xff

#Write a single register
bus.write_byte_data(DEVICE_ADDRESS, 6, 0x00)
bus.write_byte_data(DEVICE_ADDRESS, 7, 0x00)

bus.write_byte_data(DEVICE_ADDRESS, 2, 0xFF)
bus.write_byte_data(DEVICE_ADDRESS, 3, 0x00)

#Write an array of registers
#ledout_values = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
#bus.write_i2c_block_data(DEVICE_ADDRESS, DEVICE_REG_LEDOUT0, ledout_values)
