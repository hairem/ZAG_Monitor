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
#---------------------------------------------------------------------------# 
#Data handling Imports:
#---------------------------------------------------------------------------#
import smbus
import time
import math
import gpiozero
import smbus

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
#tg=18390
#sn=5252
#---------------------------------------------------------------------------# 
# Pull TimeStamp from File
#---------------------------------------------------------------------------# 
def Config():
 f=open('config.txt')
 lines=f.readlines()
 ChemT= int(lines[3])
 PumpT = int(lines[4])
 tg = int(lines[1])
 sn= int(lines[2])
 f.close()
 return(ChemT,PumpT,tg,sn)
#---------------------------------------------------------------------------# 
# define your Data and collect it from Sensors
#---------------------------------------------------------------------------# 
def Device_reader():
     Config()
     calibrate_params = bme280.load_calibration_params(smbus.SMBus(1), 0x76)
     Oventemp = int(32.6*sensor.readTempC()-210) #Scale: -210C - 1800C
     Current = ads.readADCSingleEnded(channel=3)*(65535/5000) #Scale: 0-10 Amps or 0-5 Volts
     AirTemp = int(data.temperature*524.3-40.0) #Scale -40 - 85
     AirRH = int(data.humidity*655.35) #Scale:0-100%
     DewP = (AirTemp - (14.55 + 0.114 * AirTemp) * (1 - (0.01 * AirRH)) - (((2.5 + 0.007 * AirTemp) * (1 - (0.01 * AirRH)))**3) - (15.9 + 0.117 * AirTemp) * ((1 - (0.01 * AirRH))** 14)) #Lowest: -72 Highest:85
     Tank = ads.readADCSingleEnded(channel=0)(65535/5000) #Scale: 0 - 700kPa or 0 - 101.53psi
     ChemChk = (time.time()- ChemT)/86400
     PumpChk = (time.time()- PumpT)/86400
     values= [tg,sn,Current,AirRH,AirTemp,int(DewP),Oventemp,Tank,int(CehmChk),int(PumpChk)]
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
    #data = Device_reader()
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
    di = ModbusSequentialDataBlock(0, [17]*100),
    co = ModbusSequentialDataBlock(0, [17]*100),
    hr = ModbusSequentialDataBlock(0, [17]*100),
    ir = ModbusSequentialDataBlock(0, [17]*100))
context = ModbusServerContext(slaves=store, single=True)

#---------------------------------------------------------------------------# 
# initialize the server information
#---------------------------------------------------------------------------# 
identity = ModbusDeviceIdentification()
identity.VendorName  = 'pymodbus'
identity.ProductCode = 'PM'
identity.VendorUrl   = 'http://github.com/bashwork/pymodbus/'
identity.ProductName = 'pymodbus Server'
identity.ModelName   = 'pymodbus Server'
identity.MajorMinorRevision = '1.0'

#---------------------------------------------------------------------------# 
# run the server you want
#---------------------------------------------------------------------------# 
TimeStamp()
time = 0.5 # 5 seconds delay
loop = LoopingCall(f=updating_writer, a=(context,))
loop.start(time, now=False) # initially delay by time
StartTcpServer(context, identity=identity, address=("localhost", 502)) #because port 502 is being used this program must be ran as sudo
