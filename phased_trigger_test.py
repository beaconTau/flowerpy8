import flower_trig
import time
import setup_board

trig = flower_trig.FlowerTrig()

trig.dev.calPulser(False)
setup_board.adcGainSelect(trig.dev, 5)
for i in range(2000, 500, -50):
    print (i)
    trig.initPhasedTrig(i)
    print (trig.dev.readRegister(trig.dev.DEV_FLOWER, 0x57))
    time.sleep(1)
    for j in range(60,72):
        trig.setScalerOut(j)
        print (trig.readSingleScaler())
    trig.setScalerOut(0)
    print ('scaler pps', trig.readSingleScaler())

trig.dev.calPulser(False)
trig.initPhasedTrig(4095)
