#!/usr/bin/python
# -*- coding:utf-8 -*-
import serial
import time, os
import traceback
import sys

path = './Data/'
    
class SensorCO2():
    def __init__(self, autoSavePath = None):
        self.autoSavePath = autoSavePath
        
        self.saveStartTime()
        try:
            # link the serial port 0 with bautrate of 9600
            self.srl = serial.Serial("/dev/ttyAMA0", 9600, timeout=2)
            print('Sensor Init')
        except BaseException:
            # print the err code if a terminal exit
            print(traceback.format_exc())
            if self.autoSavePath!=None: self.saveErrCode()

    def __del__(self):
        # close the serial port if the run loop break
        self.srl.close()
        pass

    def __CRCcheckFail(self, srlData):
        ''' CRC check func. 
        see details in sensor datasheet
        input: 27 bytes array
        output: check result.  = True if check fail. 
        ''' 
        CRCsum = sum(srlData[0:10])
        dataCRC = srlData[10] * 256 + srlData[11]
        # print('CRCsum = ', CRCsum)
        # print('dataCRC = ', dataCRC)
        return dataCRC != CRCsum

    def __dataProcess(self, srlData):
        
        data = list()
        for i in range(len(srlData)//2):
            data.append(srlData[i *2] *256 +srlData[ 1 + i *2])
            
        return data

    # the sensor data read and combine function 
    # input: the serial port
    # output: captured data
    def dataRead(self):
        srlData = self.__srlRead()
        # print(srlData)
        if(srlData == 1):
            print('data error')
            return(1)
        
        # convert the byte srlData to list of num
        if sys.version_info.major==3:
            srlData = list(srlData)
        elif sys.version_info.major==2:
            srlData = list(map(ord,srlData))
        
        # print(srlData)

        # CRC check
        if self.__CRCcheckFail(srlData):
            print('CRC fail!')
            return 1

        # combine the byte data
        data = self.__dataProcess(srlData[4:10])
        # print('data = ', data)
        
        if self.autoSavePath != None: self.__dataSave(data)
        return data
        # dataLength = srlData[0:1]
        # dataVersion = srlData[26]
        # dataErrNo = srlData[27]

        # print('dataVersion = %d, dataErrNo = %d'%(dataVersion, dataErrNo ))


    # save the caputred data into text files
    def __dataSave(self, data):
        # get current system time for 
        LocalTime = time.strftime("%Y%m%d \t %H%M%S", time.localtime())
        
        fileName = time.strftime("%Y%m%d-%H%M.txt", time.localtime())
        fileName = fileName[0:-5]+'0'+fileName[-4:]
        # print(fileName)

        if not os.path.exists(self.autoSavePath):
            os.makedirs(self.autoSavePath)
        
        # attemp to open or create a new text file for save
        with open(path+fileName, 'a') as f:

            # write the current time 
            f.write(LocalTime)

            # write the 12 data
            for i in range(len(data)):
                f.write('\t%d' % data[i])
            
            # line change
            f.write('\r\n')
            
    def __srlRead(self):
        
        # run the following codes, and go to th except lines if any problems occurs.
        try:
            # run code if the serial port is connected correctly.
            if not self.srl.isOpen():
                return('serial is closed!')
                
            self.srl.write(b'\x42\x4d\xe3\x00\x00\x01\x72')
            # print(cmd.encode('hex'))
            
            # search the first head byte of each byte array
            # print(tmp)
            count = 10
            tmp = self.srl.read(1)
            # print(tmp)
            while tmp != b'\x42' and count > 0:
                # print(tmp)
                print('array head lost')
                tmp = self.srl.read(1)
                count -=1
            if count == 0: 
                print('1st array head lost')
                return(1)
            
            # return err if the 2nd head byte unmatch
            tmp = ord(self.srl.read(1))
            # print(tmp)
            if tmp != 0x4d:
                print('2nd array head lost')
                return(1)
            
            # read the other 10 byte via serial
            data = b'\x42\x4d'+self.srl.read(10)
            # print(data.encode('hex'))
            return(data)
        
        # this part works when the system get in error. 
        # the err code will be write into a Err text file.
        except BaseException:
            # print the err code if a terminal exit
            print(traceback.format_exc())
            if self.autoSavePath!=None: self.saveErrCode()

    def continueRead(self, timeStep = 1):
        
        try:
            while(True):
                LocalTime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                tmp = self.dataRead()
                if tmp == 1: 
                    raise ValueError
                    break
                print(LocalTime, tmp)
                time.sleep(timeStep)

        except BaseException:
            # print the err code if a terminal exit
            print(traceback.format_exc())
            if self.autoSavePath!=None: self.saveErrCode()


    def saveStartTime(self):
        if not os.path.exists(self.autoSavePath):
            os.makedirs(self.autoSavePath)

        LocalTime = time.strftime("%Y%m%d-%H%M", time.localtime())
        with open(path+ '/BootAt'+LocalTime+'.txt', 'a') as f:
                LocalTime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                f.write(LocalTime)
                pass
    
    def saveErrCode(self):
        # get the current time when get error
        LocalTime = time.strftime("%Y%m%d-%H%M", time.localtime())
        # open a err text file
        with open(path+'/Err'+LocalTime+'.txt', 'a') as f:
            LocalTime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            f.write(LocalTime)
            # write the err code into the err file
            f.write(traceback.format_exc())
            # print the err code if a terminal exit



if __name__ == '__main__':
    
    # time.sleep(20)
    sCO2 = SensorCO2(autoSavePath=path)
    sCO2.continueRead()