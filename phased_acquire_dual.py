import flower
import flower_trig
import numpy
import setup_board as setup
import time
import Adafruit_BBIO.GPIO as GPIO

if __name__ == '__main__':


    #GPIO.setup("P8_12", GPIO.IN) #dev0 data-ready
    #GPIO.setup("P8_30", GPIO.IN) #dev1 data-ready
    dev0 = flower.Flower(flower_dev=0)
    dev1 = flower.Flower(flower_dev=1)
    setup.adcGainSelect(dev0,5)
    setup.adcGainSelect(dev1,5)
    trig=flower_trig.FlowerTrig()

    ##time.sleep(0.5)
    dev1.write(dev1.DEV_FLOWER, [0x63, 0x00, 0x00, 0x02]) #assign slave
    dev0.write(dev0.DEV_FLOWER, [0x63, 0x00, 0x00, 0x01]) #assign slave
    dev0.timestampReset()
    dev1.timestampReset()
    dev0.write(dev0.DEV_FLOWER, [0x63, 0x00, 0x00, 0x00]) #release master
    dev1.write(dev1.DEV_FLOWER, [0x63, 0x00, 0x00, 0x00]) #assign slave
    
    dev0.bufferClear()
    dev1.bufferClear()
    trig.initPhasedTrig(1500)
    trig.trigEnable(coinc_trig=0,phased_trig=1)
    i=0
    while(i<50):
        time.sleep(0.1)
        #dev0.bufferClear()
        #dev1.bufferClear()
        
        #print (dev.readRegister(dev.DEV_FLOWER, 0x7)) #print out status register
        print (dev0.checkBuffer()) #check and print full flag

        #dev0.calPulser(True, sync=True)
        #dev1.calPulser(True, sync=True)
        #print(dev0.readRegister(dev0.DEV_FLOWER, 42))

        #sync--->
        #dev1.write(dev1.DEV_FLOWER, [0x63, 0x00, 0x00, 0x02]) #assign slave
        #dev0.write(dev0.DEV_FLOWER, [0x63, 0x00, 0x00, 0x01]) #assign master
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x63),dev1.readRegister(dev1.DEV_FLOWER, 0x63))
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x0A),dev1.readRegister(dev1.DEV_FLOWER, 0x0A))
        #dev0.softwareTrigger()
        #dev1.softwareTrigger()
        #time.sleep(0.2)
        #print(GPIO.input("P8_12"), GPIO.input("P8_30"))
        
        #dev0.write(dev0.DEV_FLOWER, [0x63, 0x00, 0x00, 0x00]) #release master
        #dev1.write(dev1.DEV_FLOWER, [0x63, 0x00, 0x00, 0x00]) #release slave
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x63),dev1.readRegister(dev1.DEV_FLOWER, 0x63))
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x0A),dev1.readRegister(dev1.DEV_FLOWER, 0x0A))
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x0B),dev1.readRegister(dev1.DEV_FLOWER, 0x0B))
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x0C),dev1.readRegister(dev1.DEV_FLOWER, 0x0C))
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x0D),dev1.readRegister(dev1.DEV_FLOWER, 0x0D))
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x0E),dev1.readRegister(dev1.DEV_FLOWER, 0x0E))
        #print(dev0.readRegister(dev0.DEV_FLOWER, 0x0F),dev1.readRegister(dev1.DEV_FLOWER, 0x0F))
        if dev0.checkBuffer():

            dat=[]
            start = time.time() 
            dat.extend(dev0.readRam(dev0.DEV_FLOWER, 0, 256, mode=8))
            dat.extend(dev1.readRam(dev1.DEV_FLOWER, 0, 256, mode=8))
            end = time.time() 
            print("readout took ", end-start)
    
            dev0.bufferClear()
            dev1.bufferClear()
            numpy.savetxt('test_terra.txt', numpy.array(dat, dtype=numpy.uint8))
        i=i+1

    dev0.bufferClear()
    dev1.bufferClear()
    trig.trigEnable()
