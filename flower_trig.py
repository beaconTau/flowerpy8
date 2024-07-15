# trigger control for FLOWER board.

import flower
import time
class FlowerTrig():
    
    map = {
        'SCALER_READ_REG'        : 0x03,
        'SCALER_SEL_REG'         : 0x29,
        'SCALER_UPDATE_REG'      : 0x28,
        'COINC_TRIG_CH0_THRESH'  : 0x56,
        'COINC_TRIG_CH1_THRESH'  : 0x57,
        'COINC_TRIG_CH2_THRESH'  : 0x58,
        'COINC_TRIG_CH3_THRESH'  : 0x59,
        'COINC_TRIG_CH4_THRESH'  : 0x5a,
        'COINC_TRIG_CH5_THRESH'  : 0x5b,
        'COINC_TRIG_CH6_THRESH'  : 0x5c,
        'COINC_TRIG_CH7_THRESH'  : 0x5d,
        'COINC_TRIG_PARAM'       : 0x5f,
        'TRIG_ENABLES'           : 0x3D,
        'PHASED_THRESHOLDS'	 : 0x80,
        'PHASED_MASK_LOWER'      : 0x50,
        'PHASED_MASK_UPPER'      : 0x51,
        'COINC_CHANNEL_MASK'     : 0x62

    }

    def __init__(self):
        self.dev = flower.Flower()

    def initPhasedTrig(self,power_threshold,upper_mask=0xffffff, lower_mask=0xffffff, num_beams=20):
        for i in range(num_beams):
            #servo top 8, servo bottom 4 <<4 + trig top 4, trig bottom 8
            #self.dev.write(self.dev.DEV_FLOWER,[self.map['PHASED_THRESHOLDS']+i,(power_threshold&0xff0)>>4, ((power_threshold&0x00f)<<4)+((power_threshold&0xf00)>>8),power_threshold&0x0ff])
            self.dev.write(self.dev.DEV_FLOWER,[self.map['PHASED_THRESHOLDS']+i,0xff,(0xf<<4)+((power_threshold&0xf00)>>8),power_threshold&0xff])
        self.dev.write(self.dev.DEV_FLOWER,[self.map['PHASED_MASK_LOWER'],(lower_mask&0xff0000)>>16,(lower_mask&0x00ff00)>>8,(lower_mask&0x0000ff)])
        self.dev.write(self.dev.DEV_FLOWER,[self.map['PHASED_MASK_UPPER'],(upper_mask&0xff0000)>>16,(upper_mask&0x00ff00)>>8,(upper_mask&0x0000ff)])

    def initCoincTrig(self, num_coinc, thresh, servo_thresh, vppmode=True, coinc_window=2,mask=0xff):
        for i in range(8):
            self.dev.write(self.dev.DEV_FLOWER, [self.map['COINC_TRIG_CH0_THRESH']+i,0,servo_thresh[i], thresh[i]])
        self.dev.write(self.dev.DEV_FLOWER, [self.map['COINC_TRIG_PARAM'],vppmode,coinc_window, num_coinc])
        self.dev.write(self.dev.DEV_FLOWER,[self.map['COINC_CHANNEL_MASK'],0,0,0xff&mask])
    def setScalerOut(self, scaler_adr=0):
        if scaler_adr < 0 or scaler_adr > 128:
            return None
        self.dev.write(self.dev.DEV_FLOWER, [self.map['SCALER_SEL_REG'],0,0,scaler_adr])
        #print self.dev.readRegister(self.dev.DEV_FLOWER, 41)

    def readSingleScaler(self):
        self.dev.write(self.dev.DEV_FLOWER, [self.map['SCALER_UPDATE_REG'],0,0,1])
        read_scaler_reg = self.dev.readRegister(self.dev.DEV_FLOWER,self.map['SCALER_READ_REG'])
        scaler_low = (read_scaler_reg[2] & 0x0F) << 8 | read_scaler_reg[3]
        scaler_hi  = (read_scaler_reg[1] & 0xFF) << 4 | (read_scaler_reg[2] & 0xF0) >> 4
        return scaler_low, scaler_hi

    def trigEnable(self, coinc_trig=0, pps_trig=0, ext_trig=0, phased_trig=0):
        '''specify '0' or '1' for trigger types
        '''
        self.dev.write(self.dev.DEV_FLOWER, [self.map['TRIG_ENABLES'],ext_trig, (phased_trig<<1)+coinc_trig, pps_trig])

