#!/usr/bin/env python
'''
Pymodbus Server With Updating Thread
--------------------------------------------------------------------------

This is an example of having a background thread updating the
context while the server is operating. This can also be done with
a python thread::

    from threading import Thread

    thread = Thread(target=updating_writer, args=(context,))
    thread.start()
'''
#---------------------------------------------------------------------------# 
#Senor Imports:
#---------------------------------------------------------------------------# 
import ADS1115
import bme280
ads = ADS1115.ADS1115()

#---------------------------------------------------------------------------# 
#Data handling Imports:
#---------------------------------------------------------------------------#
import smbus2
import time
import math
import gpiozero
import smbus
port = 1
address = 0x76
bus = smbus2.SMBus(port)
#---------------------------------------------------------------------------# 
# import the modbus libraries we need
#---------------------------------------------------------------------------# 
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

#---------------------------------------------------------------------------# 
# import the twisted libraries we need
#---------------------------------------------------------------------------# 
from twisted.internet.task import LoopingCall

#---------------------------------------------------------------------------# 
# configure the service logging
#---------------------------------------------------------------------------# 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#---------------------------------------------------------------------------# 
# define your Property Tag and Serial Number
#---------------------------------------------------------------------------# 
tg=16928
sn=821
#---------------------------------------------------------------------------# 
# define your Data and collect it from Sensors
#---------------------------------------------------------------------------# 
def Device_reader():
     calibration_params = bme280.load_calibration_params(bus, address)
     data = bme280.sample(bus, address, calibration_params)
     Oventemp = ads.readADCSingleEnded(channel=2)*(65535/5000) #Range:-250°C to +750C 
     Current = ads.readADCSingleEnded(channel=3)*(65535/5000) #Scale: 0-10 Amps or 0-5 Volts%
     AirTemp = data.temperature
     AirRH = data.humidity
     Airt = (504.1*data.temperature)+22685
     Airrh = data.humidity*(65535/100)
     DewPf = (AirTemp - (14.55 + 0.114 * AirTemp) * (1 - (0.01 * AirRH)) - (((2.5 + 0.007 * AirTemp) * (1 - (0.01 * AirRH)))**3) - (15.9 + 0.117 * AirTemp) * ((1 - (0.01 * AirRH))** 14)) #Needs to be tested
     DewP = (417.4*DewPf)+30054 #DewPf = (DewP-30054)/417.4
     Tank = ads.readADCSingleEnded(channel=0)*(65535/5000) #Scale: 0 - 700kPa or 0 - 101.5psi
#    print(tg,sn,ads.readADCSingleEnded(channel=3), 49.26*ads.readADCSingleEnded(channel=0)/2500, data.temperature, data.humidity, DewPf, 0.2*ads.readADCSingleEnded(channel=2)-250)
     values= [tg,sn,int(abs(Current)),int(Tank),int(Airrh),int(Airt),int(DewP), int(Oventemp)]
     return(values)
#---------------------------------------------------------------------------# 
# define your callback process
#---------------------------------------------------------------------------# 
def updating_writer(a):
    ''' A worker process that runs every so often and
    updates live values of the context. It should be noted
    that there is a race condition for the update.

    :param arguments: The input arguments to the call
    '''
    log.debug("updating the context")
    values = Device_reader()
    context  = a[0]
    register = 3
    slave_id = 0x00
    address  = 0x00
    #values   = context[slave_id].getValues(register, address, count=5)
    #values   = [v + 1 for v in values]
    log.debug("new values: " + str(values))
    context[slave_id].setValues(register, address, values)
    values.clear()

#---------------------------------------------------------------------------# 
# initialize your data store
#---------------------------------------------------------------------------# 
store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [9]*100),
    co = ModbusSequentialDataBlock(0, [9]*100),
    hr = ModbusSequentialDataBlock(0, [9]*100),
    ir = ModbusSequentialDataBlock(0, [9]*100))
context = ModbusServerContext(slaves=store, single=True)

#---------------------------------------------------------------------------# 
# initialize the server information
#---------------------------------------------------------------------------# 
identity = ModbusDeviceIdentification()
identity.VendorName  = 'San Joaquin Valley Air Pollution Control District and pymodbus'
identity.ProductCode = 'ZAG'
identity.VendorUrl   = ' www.valleyair.org and http://github.com/bashwork/pymodbus/'
identity.ProductName = 'ZAG Server'
identity.ModelName   = 'pymodbus ZAG Server'
identity.MajorMinorRevision = '1.0'

#---------------------------------------------------------------------------# 
# run the server you want
#---------------------------------------------------------------------------# 
time = 0.5 # 5 seconds delay
loop = LoopingCall(f=updating_writer, a=(context,))
loop.start(time, now=False) # initially delay by time
StartTcpServer(context, identity=identity, address=("192.168.1.135", 502)) #because port 502 is being used this program must be ran as sudo


