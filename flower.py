# flower connected to SPI1 in rno-g implementation

from Adafruit_BBIO import SPI
import Adafruit_BBIO.GPIO as GPIO
import math
import time
import os
import datetime

class Flower():
    spi_bytes = 4  #transaction must include 4 bytes
    firmware_registers_adr_max=128
    firmware_ram_adr_max=128

    map = {
        'FIRMWARE_VER'  : 0x01,
        'FIRMWARE_DATE' : 0x02,
        'SET_READ_REG'  : 0x6D, #pick readout register
        'READ'          : 0x47, #send data to spi miso
        'FORCE_TRIG'    : 0x40, #software trigger
        'CHANNEL'       : 0x41, #select channel to read
        'CHUNK'         : 0x49, #select 32-bit chunk of data in 128-wide bus
        'RAM_ADR'       : 0x45, #ram address
        'MODE'          : 0x42, #select readout mode
        'CALPULSE'      : 0x2A, #toggle RF switch/pulser board
        'DATVALID'      : 0x3A, #once ADCs are setup, this toggles Rx FIFOs
    }
        
    def __init__(self, spi_clk_freq=10000000, flower_dev=0):
        '''
        flower_dev is the device. 
               -->flower_dev=0 for the 'classical' flower slot (on spidev<bus>.<device>=1.0)
               -->flower_dev=1 for the flower in the 'radiant' slot (on spidev<bus>.<device>=0.0)
        '''
        #GPIO61 enables both SPI bus drivers
        if not os.path.isfile('/sys/class/gpio/gpio61/value'):
            GPIO.setup("P8_26", GPIO.OUT) #enable pin for 2.5V bus drivers
            GPIO.output("P8_26", GPIO.LOW)  #enable for 2.5V bus drivers
        if flower_dev==0:    
            self.BUS_FLOWER = 1
            #self.DEV_FLOWER = 0 #these are confusing definitions, sorry to future self (BUS=BBB spi bus; DEV=enumeration)
        elif flower_dev==1:
            self.BUS_FLOWER = 0
            #self.DEV_FLOWER = 1
        self.DEV_FLOWER=0 #just one instance per class for now
            
        self.spi={}
        self.spi[0]=SPI.SPI(self.BUS_FLOWER,0)
        self.spi[0].mode = 0
        try:
            self.spi[0].msh = spi_clk_freq
        except IOError:
            pass #hardware does not support this speed..

        self.current_buffer = 0
        self.current_trigger= 0
    
    def write(self, dev, data):
        if len(data) != 4:
            return None
        if dev < 0 or dev > 1:
            return None
        self.spi[dev].writebytes(data)        
        return 0
        
    def read(self, dev):
        if dev < 0 or dev > 1:
            return None
        return self.spi[dev].readbytes(self.spi_bytes)

    def readRegister(self, dev, address=1):
        if address > self.firmware_registers_adr_max-1 or address < 1:
            return None
        ## set readout register
        send_word=[self.map['SET_READ_REG'], 0x00, 0x00, address & 0xFF]
        self.write(dev, send_word) #set read register of interest
        readback = self.read(dev)
        
        return readback

    def dna(self):
        dna_bytes = 8        
        dna_low = self.readRegister(self.DEV_FLOWER,4)[::-1] #lower 3 bytes 
        dna_mid = self.readRegister(self.DEV_FLOWER,5)[::-1] #middle 3 bytes
        dna_hi  = self.readRegister(self.DEV_FLOWER,6)[::-1] #upper 2 bytes        
        board_dna = 0

        for i in range(dna_bytes):
            if i < 3:
                board_dna = board_dna | (dna_low[i] << i*8)
            elif i < 6:
                board_dna = board_dna | (dna_mid[i-3] << i*8)
            else:
                board_dna = board_dna | (dna_hi[i-6] << i*8)

        return board_dna

    def identify(self, save=False):
        dna = self.dna()

        fw_info=[]
        
        firmware_version = self.readRegister(self.DEV_FLOWER, self.map['FIRMWARE_VER'])
        firmware_version = str(firmware_version[2])+'.'+\
            str((firmware_version[3] & 0xF0)>>4)+'.'+str(firmware_version[3]&0x0F)
        print ('firmware version:', firmware_version)
        firmware_date = self.readRegister(self.DEV_FLOWER, self.map['FIRMWARE_DATE'])
        firmware_date = [(firmware_date[1])<<4 | (firmware_date[2] & 0xF0)>>4, firmware_date[2] & 0x0F, firmware_date[3]]
        print ('firmware date:', firmware_date)
        print ('board DNA:', hex(dna))
        print ('-----------------------------------')
        fw_info.extend([0, hex(dna), firmware_version, firmware_date])

        if save:
            with open('output/fw_info.txt', 'w') as f:
                f.write(str(datetime.datetime.now())+'\n')
                for i in range(len(fw_info)):
                    f.write(str(fw_info[i])+'\n')
            f.close()
                    
        
    def boardInit(self, verbose=False):
        
        self.bufferClear()
        self.calPulser(False)
        self.bufferClear()
    
    '''
    #same as above, but just reset the data manager stuff:
    def eventInit(self):
        self.write(1,[39,0,0,0])
        self.bufferClear(15)
        self.write(1,[39,0,0,1]) #send sync
        self.write(0,[77,0,1,0]) #set buffer to 0 on slave
        self.write(1,[77,0,1,0]) #set buffer to 0
        self.write(1,[39,0,0,0]) #release sync
        self.write(1,[39,0,0,1]) #send sync
        self.write(0,[126,0,0,1]) #reset event counter/timestamp on slave
        self.write(1,[126,0,0,1]) #reset event counter/timestamp
        self.write(1,[39,0,0,0]) #release sync
        self.setReadoutBuffer(0)
    '''    
    def bufferClear(self, buf_clear_flag=1):
         self.write(self.DEV_FLOWER,[77,0,0,buf_clear_flag]) 

    def timestampReset(self):
        self.write(self.DEV_FLOWER, [126,0,0,1])
        
    def calPulser(self, enable=True, freq=0, sync=False, readback=False):
        '''
        freq = 0, standard; freq = 1, rep rate lower by 8x
        '''
        if enable and sync:
            self.write(self.DEV_FLOWER, [42, 0x1, (0x1 & freq) ,3])
        elif enable and not sync:
            self.write(self.DEV_FLOWER, [42, 0x0, (0x1 & freq) ,3])
        else:
            self.write(self.DEV_FLOWER, [42,0,0,0])
        if readback:
            print (self.readRegister(self.DEV_FLOWER,42))
 
    def softwareTrigger(self):
        self.write(self.DEV_FLOWER,[64,0,0,1]) #send software trig 

    def checkBuffer(self):
        full_flag = self.readRegister(self.DEV_FLOWER, 0x7)[3] & 0x1
        return full_flag
        
    def readRam(self, dev, address_start=0, address_stop=64, mode=4):
        '''
        mode=num channels
        '''
        self.write(dev, [65,0,0,1]) #read RAM 0 [ch's 0 & 1 / 0,1,2,3]
        data0=[]
        data1=[]
        data2=[]
        data3=[]
        if mode==4:
            for i in range(address_start, address_stop, 1):
                _dat0, _dat1 = self.readRamAddress(dev, i)
                data0.extend(_dat0)
                data1.extend(_dat1)
        elif mode==8:
            for i in range(address_start, address_stop, 1):
                _dat0, _dat1 = self.readRamAddress(dev, i)
                data0.extend(_dat0[:2])
                data1.extend(_dat0[2:])
                data2.extend(_dat1[:2])
                data3.extend(_dat1[2:])
                
        self.write(dev, [65,0,0,2]) #read RAM 1 [ch's 2 & 3 / 4,5,6,7]
        data4=[]
        data5=[]
        data6=[]
        data7=[]
        if mode==4:
            for i in range(address_start, address_stop, 1):
                _dat2, _dat3 = self.readRamAddress(dev, i)
                data2.extend(_dat2)
                data3.extend(_dat3)
        elif mode==8:
            for i in range(address_start, address_stop, 1):
                _dat2, _dat3 = self.readRamAddress(dev, i)
                data4.extend(_dat2[:2])
                data5.extend(_dat2[2:])
                data6.extend(_dat3[:2])
                data7.extend(_dat3[2:])
                  
        return data0, data1, data2, data3, data4, data5, data6, data7
            
    def readRamAddress(self, dev, address, readback_address=False, verbose=False):
        data0=[]
        data1=[]
        return_address=0
        self.write(dev, [69,0,0, 0xFF & address]) #note only picks off lower byte of address input
        if readback_address:
            return_address=self.readRegister(dev,69)
        self.write(dev,[35,0,0,0])
        data0.extend(self.read(dev))
        self.write(dev,[36,0,0,0])
        data1.extend(self.read(dev))

        if verbose:
            print (dev,return_address,data)

        return data0, data1
    
        
if __name__=="__main__":
    d=Flower(flower_dev=1)
    #d.boardInit()
    d.identify(True)
    d=Flower(flower_dev=0)
    d.identify(True)
