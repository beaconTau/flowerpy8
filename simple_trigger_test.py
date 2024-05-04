import flower_trig
import time
import setup_board

trig = flower_trig.FlowerTrig()

trig.dev.calPulser(False)
setup_board.adcGainSelect(trig.dev, 5)
effective_disable_thresh = [120,120,120,120,120,120,120,120]
trig.trigEnable(coinc_trig=1,phased_trig=0)
for i in range(20, 4, -1):
    print (i)
    trig.initCoincTrig(1, [i,i,i,i,i,i,i,i], [120,120,120,120,120,120,120,120], vppmode=0)
    print (trig.dev.readRegister(trig.dev.DEV_FLOWER, 0x57))
    time.sleep(1)
    for j in range(0,16):
        trig.setScalerOut(j)
        print (i,i+1,":",trig.readSingleScaler())
    trig.setScalerOut(0)
    print ('scaler pps', trig.readSingleScaler())

trig.dev.calPulser(False)
trig.initCoincTrig(3, effective_disable_thresh, effective_disable_thresh, vppmode=0)
trig.enableTrig()
