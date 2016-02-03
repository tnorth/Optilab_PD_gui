#!/usr/bin/python

import serial
import sys
import time
import numpy as np
import pylab
import re

class OptiLabPD:
    rate = 9600
    port = None
    baudrate = None
    cmds = {"READ":"READ",}
    
    temperature = None
    voltage_12 = None
    voltage_8 = None
    input_power_dBm = None
    power_alarm = False
    serialnumber = None
    name = None
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.connect()


    def connect(self):
        sys.stderr.write("Connecting OptiLab Photodiode at %s with a baudrate of %d\n" % 
                            (self.port, self.baudrate)
                        )
        self.pd = serial.Serial(self.port, self.baudrate, timeout=0.1)
        
        # initiate a READ
        self.read()
    
    def disconnect(self):
        if self.pd:
            sys.stderr.write("Closing Photodiode connection.\n")
            self.pd.close()
        else:
            sys.stderr.write("No Photodiode is currently connected.\n")
        
    def read(self):
        self.pd.write((self.cmds["READ"] + '\n').encode())
        while 1:
            resp = self.pd.readlines()
            if resp != []: break
        #print(resp)
        #for line in resp:
        #    print line
        
        def parse_read(msg):
            msg = [mm.decode(errors='ignore') for mm in msg]
            #print("msg: {}".format(msg))
            msg = '\n'.join(msg)
            #print msg
            name = re.search("(LR.*?)\r\n", msg)
            self.name = name.group(1)
            #print(name.group(1))
            serialnumber = re.search("(S\/N.*?)\r\n", msg)
            self.serialnumber = serialnumber.group(1)
            #print(serialnumber.group(1))
            
            # Can be in 3 different states:
            # 1) No input (says: "NO INPUT!")
            # 2) Input with value (says "Input 1    +\n2.8dBm")
            # 3) Input high (says: "INPUT HIGH\n!")
            
            state_noinput = re.search("NO INPUT", msg)
            state_normal = re.search("Input 1", msg)
            state_toohigh = re.search("INPUT HIGH", msg)
            
            
            # If there is no input:
            if state_noinput:
                self.input_power_dBm = -float('inf')
                self.power_alarm = False
                
            if state_normal:
                pow_ = re.search("Input 1\s+(.*?)dBm", msg)
                #print pow_.group(1)
                self.power_alarm = False
                self.input_power_dBm = float(pow_.group(1))

            if state_toohigh:
                self.power_alarm = True
                
            # Get temperature
            temp = re.search("System Temp\s+(\d+).*?\n", msg)
            if temp:
                self.temperature = float(temp.group(1))
            # Get voltages
            v8 = re.search("\+8V monitor\s+(.*?)V", msg)
            v12 = re.search("\+12V monitor\s+(.*?)V", msg)
            self.voltage_8 = float(v8.group(1))
            self.voltage_12 = float(v12.group(1))
            
        parse_read(resp)
    
    def print_status(self):
        print(self.name)
        print(self.serialnumber)
        print(self.temperature)
        print(self.voltage_8)
        print(self.voltage_12)
        print(self.input_power_dBm)
        print(self.power_alarm)
	
    def get_status(self):
        self.read()
        return [self.temperature, self.voltage_8, self.voltage_12,
                self.input_power_dBm, self.power_alarm]
    
    

if __name__ == "__main__":
    # TEST
    pd = OptiLabPD()
    pd.read()
    pd.print_status()
    pd.disconnect()
     
