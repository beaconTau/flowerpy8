import flower
import time
import numpy

ADC0_SAMPLE_SHIFT_REG = 0x38
ADC1_SAMPLE_SHIFT_REG = 0x39

def acquire(dev, mode=4):
    '''
    mode= num_chans
    '''
    dev.bufferClear()
    dev.softwareTrigger()
    dat = dev.readRam(dev.DEV_FLOWER, 0, 128, mode)
    return dat

def getPeaks(dat, mode=4):
    '''
    mode= num_chans
    '''
    peak0 = dat[0].index(min(dat[0]))
    if mode==4:
        peak1 = dat[2].index(min(dat[2]))
    elif mode==8:
        peak1 = dat[4].index(min(dat[4]))
    #some conditions:
    if min(dat[0]) > 115 or min(dat[2]) > 115:
        return None
    elif peak0 < 10 or peak0 > 500 or peak1 < 10 or peak1 > 500:
        return None
    else: return peak0, peak1

def align(dev, num_tries=20, mode=8):
    '''mode=num_chans'''

    dev.write(dev.DEV_FLOWER, [ADC0_SAMPLE_SHIFT_REG, 0, 0, 0x00]) #start with no adjustment
    dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x00]) #start with no adjustment
    tries=0
    while(tries < num_tries):
        tries+=1
        dat = acquire(dev, mode)
        peaks = getPeaks(dat, mode)
    
        if peaks is not None:
            diff = peaks[1] - peaks[0] #get difference
            if tries == 1:
                print ('adc sample diff is', diff)
            if diff == 0: return 0 #aligned!
            elif diff == 1: #adc1 slower by 1 sample
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x01])
            elif diff == 2: #adc1 slower by 2 samples   
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x02])
            elif diff ==-1: #adc1 faster by 1 sample
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x05])
            elif diff ==-2: #adc1 faster by 2 samples    
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x06])
            elif diff == 3:
                #speed up adc1 by 2, slow adc0 by 1
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x02])
                dev.write(dev.DEV_FLOWER, [ADC0_SAMPLE_SHIFT_REG, 0, 0, 0x05])
            elif diff == 4:
                #speed up adc1 by 2, slow adc0 by 2
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x02])
                dev.write(dev.DEV_FLOWER, [ADC0_SAMPLE_SHIFT_REG, 0, 0, 0x06])
            elif diff == -3:
                #slow adc1 by 2, speed adc0 by 1
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x06])
                dev.write(dev.DEV_FLOWER, [ADC0_SAMPLE_SHIFT_REG, 0, 0, 0x01])
            elif diff == -4:
                #speed up adc1 by 2, slow adc0 by 2
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x06])
                dev.write(dev.DEV_FLOWER, [ADC0_SAMPLE_SHIFT_REG, 0, 0, 0x02])
            else: return 1 #exceeds +/- 4 sample diff.

    return 2 #timeout return
            
def do(dev, mode=8):
    dev.calPulser(True)
    retval = align(dev)
    if retval == 0:
        print ('adcs succesfully aligned')
    else:
        print ('problem here..')

    dat = acquire(dev, mode=mode)
    numpy.savetxt('output/test_align.txt', numpy.array(dat))
    dev.calPulser(False)
    return retval

if __name__=='__main__':
    dev = flower.Flower()
    do(dev)
    
