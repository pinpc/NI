from nidaqmx import *
import nidaqmx
import numpy as np
import time 
from enum import Enum
import configparser


config = configparser.ConfigParser()
config.read("C:\\Tool\\python\\NI_Test_ForceConfig.py")

start = time.time()
print("Start")
end = time.time()
print(end - start)


class Signalstatus(Enum):
    NCH = 0
    NCL = 4
    RF = 2
    FF = 1

class TriggerState:

    s = 0
    triggerstate = Signalstatus.NCL
    currentState = Signalstatus.NCL
    pastState = Signalstatus.NCL
    vLow1 = float(config.get('Vthreshold', 'vLow1'))
    vLow2 = float(config.get('Vthreshold', 'vLow2'))
    vHigh1 = float(config.get('Vthreshold', 'vHigh1'))
    vHigh2 = float(config.get('Vthreshold', 'vHigh2'))

    def __ini__(self, s, state):
        self.s = s
        self.triggerstate = state
        self.currentState = state
        self.pastState = state

    def getSignal(self, signalIn):
        self.s = signalIn
        #print("Signal Input"+str(self.s)+"\n")

    def checkState(self):
       #print("Voltag:"+ str(self.s )+"\n")
       if self.triggerstate == Signalstatus.NCH:
            if self.s <= self.vLow1 :
                self.triggerstate = Signalstatus.FF
                return
       
       if self.triggerstate == Signalstatus.FF:
            if self.s <= self.vLow2 :
                self.triggerstate = Signalstatus.NCL
                return
                
       if self.triggerstate == Signalstatus.NCL:
            if self.s >= self.vHigh1 :
                self.triggerstate = Signalstatus.RF
                return

       if self.triggerstate == Signalstatus.RF:
            if self.s >= self.vHigh2 :
                self.triggerstate = Signalstatus.NCH
                return

    def getTriggerstate(self):
       if self.currentState != self.triggerstate:
           print ("Trigger state:" + str(self.triggerstate) + "\n")
           self.currentState = self.triggerstate
       return self.triggerstate

class DataEvaluation():
    
    def __init__(self):
        self.max = [0, 0.0]
        self.min = [0, 0.0]
        self.lastdata1 = [0, 0.0]
        self.lastdata2 = [0, 0.0]
        self.pos = 0

    def checklimits(self, *arr):
        for item in arr:
            self.pos += 1
            if item > self.max[1]:
                self.max[0] = self.pos
                self.max[1] = item
            if item < self.min[1]:
                self.min[0] = self.pos 
                self.min[1] = item 

    def getmin(self):
        print("min_pos: " + str(self.min[0]) + " " + str(self.min[1])+ "\n")
        return self.min

    def getmax(self):
        print("max_pos: " + str(self.max[0]) + " " + str(self.max[1])+ "\n")
        return self.max

class NIaiVoltageTask:
    
    def __init__(self, *args, **kwargs):
        self.Task_I = nidaqmx.Task()
        return super().__init__(*args, **kwargs)

    def config(self, chn, min, max, fs, sample):
        
        self.Task_I.ai_channels.add_ai_voltage_chan( chn, #'Laser-Ready/ai2'
                                                     min_val= min, max_val= max,
                                                     terminal_config = nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)
        self.Task_I.timing.cfg_samp_clk_timing(  rate = fs,
                                                #source='ao/SampleClock', # same clock as for the output
                                                 sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                                 samps_per_chan = sample)

class NIaiBridgeTask:
    
    def __init__(self, *args, **kwargs):
        self.Task_I = nidaqmx.Task()
        return super().__init__(*args, **kwargs)

    def config(self, chn, min, max, fs, sample):
        self.Task_I.ai_channels.add_ai_bridge_chan( chn,
                                                    min_val = min, max_val = max,
                                                    units = nidaqmx.constants.BridgeUnits.M_VOLTS_PER_VOLT,
                                                    bridge_config = nidaqmx.constants.BridgeConfiguration.FULL_BRIDGE,
                                                    voltage_excit_source = nidaqmx.constants.ExcitationSource.INTERNAL,
                                                    nominal_bridge_resistance = 350.0) #Resistance of the FuteK sensor

        self.Task_I.timing.cfg_samp_clk_timing( rate = fs,
                                                #source='ao/SampleClock', # same clock as for the output
                                                sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                                samps_per_chan = sample) 

def NITriggerProcessINI():
    print("TriggerProzecss: \n")
    global gTrigger
    global gTriggerStateFF
    global gTask_trigger
    global gReader
    global gnSamplestrigger

    gTask_trigger = NIaiVoltageTask()
    chnTrigger = config.get('Trigger', 'chntrigger')
    minValTrigger = float(config.get('Trigger', 'minValTrigger'))
    maxValTrigger = float(config.get('Trigger', 'maxValTrigger')) 
    fsTrigger = int(config.get('Trigger', 'fsTrigger'))
    gnSamplestrigger = int(config.get('Trigger', 'nSamplestrigger'))
   
   # gTask_trigger.config(chnTrigger, minValTrigger, maxValTrigger, fsTrigger, gnSamplestrigger)
   # gReader = nidaqmx.stream_readers.AnalogSingleChannelReader(gTask_trigger.Task_I.in_stream)
    #start
    #gTask_trigger.Task_I.start()
    return True

def NITriggerProcessing():
    global gTriggerStateFF
    global gTask_trigger
    global gReader
    global gnSamplestrigger
    t_max = 0
    nSamplesrecord = gnSamplestrigger

    #read first data
    start = time.time()
    data = np.zeros(nSamplesrecord)
    gReader.read_many_sample(data,nSamplesrecord)
    data = gTask_trigger.Task_I.read(nSamplesrecord )
    end = time.time()
    t_diff = end - start
    if t_max < t_diff:
        t_max = t_diff

    i = 0
    for item in data:
        i += 1
        gTrigger.getSignal(item)
        gTrigger.checkState()
        state = gTrigger.getTriggerstate()
        if (state == Signalstatus.FF) and (gTriggerStateFF == False):
            gTriggerStateFF = True
        #print( str(i+1)+ " : "+ str(item) +"\n")
    #print("Delta MaxTime: "+ str(t_max)+ " " + str( gTrigger.getTriggerstate())+ str(state.value) + "\n")
    return gTriggerStateFF

def NITriggerProcessEnd():
    global gTask_trigger
    global gTriggerStateFF
    for i in range(1,10):
        time.sleep(1)
    gTriggerStateFF = True
    #gTask_trigger.Task_I.stop()
    #gTask_trigger.Task_I.close()
    print("Trigger Task end \n")
    return gTriggerStateFF


def TriggerProcess():

    Task_trigger = NIaiVoltageTask()
    Task_trigger.config(Config.chnTrigger, Config.minValTrigger, Config.maxValTrigger, Config.fsTrigger, Config.nSamplestrigger)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_trigger.Task_I.in_stream)


    #start
    Task_trigger.Task_I.start()
    #Task_O.start()

    trigger = TriggerState()
    t_max = 0
    nSamplesrecord = Config.nSamplestrigger

    while  trigger.getTriggerstate() != Signalstatus.FF:
        #read first data
        start = time.time()
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_trigger.Task_I.read(nSamplesrecord )
        end = time.time()
        t_diff = end - start
        if t_max < t_diff:
            t_max = t_diff

        i = 0
        for item in data:
            i += 1
            trigger.getSignal(item)
            trigger.checkState()
            trigger.getTriggerstate()
            print( str(i+1)+ " : "+ str(item) +"\n")
            
 
    Task_trigger.Task_I.stop()
    Task_trigger.Task_I.close()
    print("Delta MaxTime: "+ str(t_max)+"\n")
    print("Trigger Task end \n")

def RecordVoltageProcess():
    print( " RecordVoltageProzecss: \n")

    Task_record = NIaiVoltageTask()
    chnVoltage = config.get('Vai', 'chnVoltage')
    minValVoltage = float(config.get('Vai', 'minValVoltage'))
    maxValVoltage = float(config.get('Vai', 'maxValVoltage'))
    fsVoltageRecord = int(config.get('Vai', 'fsVoltageRecord'))
    nSamplesVoltagerecord = int(config.get('Vai', 'nSamplesVoltagerecord'))
    Voltagelogfile = config.get('Vai', 'Voltagelogfile')
    tVoltageRecord = int(config.get('Vai', 'tvoltagerecord'))
    
    Task_record.config(chnVoltage, minValVoltage, maxValVoltage, fsVoltageRecord, nSamplesVoltagerecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start
    try:
        File = open(Voltagelogfile, "w")
    except:
        print ("recod logfile" + Voltagelogfile + "not found\n")
    nSamplesrecord = nSamplesVoltagerecord

    while t_diff < tVoltageRecord:
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_record.Task_I.read(nSamplesrecord )
        end = time.time()
        t_diff = end - start
        np.savetxt(File, [data], delimiter="\n", fmt='%.2f')

    Task_record.Task_I.stop()
    Task_record.Task_I.close()
    File.close()

    print ("Duration of data recording" + str(t_diff) + "\n")
    print("RecordVoltageProzecss end \n")

def NIRecordVoltageProcess():
    print( " RecordVoltageProzecss: \n")

    Task_record = NIaiVoltageTask()
    chnVoltage = config.get('Vai', 'chnVoltage')
    minValVoltage = float(config.get('Vai', 'minValVoltage'))
    maxValVoltage = float(config.get('Vai', 'maxValVoltage'))
    fsVoltageRecord = int(config.get('Vai', 'fsVoltageRecord'))
    nSamplesVoltagerecord = int(config.get('Vai', 'nSamplesVoltagerecord'))
    Voltagelogfile = config.get('Vai', 'Voltagelogfile')
    tVoltageRecord = int(config.get('Vai', 'tvoltagerecord'))
    
    Task_record.config(chnVoltage, minValVoltage, maxValVoltage, fsVoltageRecord, nSamplesVoltagerecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start
    try:
        File = open(Voltagelogfile, "w")
    except:
        print ("recod logfile" + Voltagelogfile + "not found\n")
    nSamplesrecord = nSamplesVoltagerecord

    while t_diff < tVoltageRecord:
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_record.Task_I.read(nSamplesrecord )
        end = time.time()
        t_diff = end - start
        np.savetxt(File, [data], delimiter="\n", fmt='%.2f')

    Task_record.Task_I.stop()
    Task_record.Task_I.close()
    File.close()

    print ("Duration of data recording" + str(t_diff) + "\n")
    print("RecordVoltageProzecss end \n")

def RecordForceProcess():
    print( " ForceProzecss: \n")

    Task_record = NIaiBridgeTask()
    chnForce = config.get('Force', 'chnForce')
    minValForce = float(config.get('Force', 'minValForce'))
    maxValForce = float(config.get('Force', 'maxValForce'))
    fsForceRecord = int(config.get('Force', 'fsForceRecord'))
    nSamplesForcerecord = int(config.get('Force', 'nSamplesForcerecord'))
    F_OFFSET = float(config.get('Force', 'F_OFFSET'))
    F_FACTOR = float(config.get('Force', 'F_FACTOR'))
    Forcelogfile =  config.get('Force', 'Forcelogfile')
    tForceRecord = int(config.get('Force', 'tForceRecord'))

    Task_record.config(chnForce, minValForce, maxValForce, fsForceRecord, nSamplesForcerecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start
    try:
        File = open(Forcelogfile, "w")
    except:
        print ("recod logfile" + Forcelogfile + "not found\n")

    nSamplesrecord = nSamplesForcerecord
    eval = DataEvaluation()   

    while t_diff < tForceRecord:
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_record.Task_I.read(nSamplesrecord )
        force_normalized = [(abs(x)- F_OFFSET)* F_FACTOR for x in data]
        arr = np.array(force_normalized)
        np.savetxt(File, [arr], delimiter="\n", fmt='%.2f')
        eval.checklimits(*arr)
    
        end = time.time()
        t_diff = end - start

    amax = eval.getmax()
    amin = eval.getmin()
    File.write(" ; max : \n")
    File.write(" ; ")
    np.savetxt(File, [amax], delimiter="\n", fmt='%.2f')
    File.write(" ; min : \n")
    File.write(" ; ")
    np.savetxt(File, [amin], delimiter="\n", fmt='%.2f')

    Task_record.Task_I.stop()
    Task_record.Task_I.close()
    File.close()

    print ("duration of data recording" + str(t_diff) + "\n")
    print("RecordProzecss end \n") 

def NIRecordForceProcess():
    print( " ForceProzecss: \n")

    Task_record = NIaiBridgeTask()
    chnForce = config.get('Force', 'chnForce')
    minValForce = float(config.get('Force', 'minValForce'))
    maxValForce = float(config.get('Force', 'maxValForce'))
    fsForceRecord = int(config.get('Force', 'fsForceRecord'))
    nSamplesForcerecord = int(config.get('Force', 'nSamplesForcerecord'))
    F_OFFSET = float(config.get('Force', 'F_OFFSET'))
    F_FACTOR = float(config.get('Force', 'F_FACTOR'))
    Forcelogfile =  config.get('Force', 'Forcelogfile')
    tForceRecord = int(config.get('Force', 'tForceRecord'))

    Task_record.config(chnForce, minValForce, maxValForce, fsForceRecord, nSamplesForcerecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start
    try:
        File = open(Forcelogfile, "w")
    except:
        print ("recod logfile" + Forcelogfile + "not found\n")

    nSamplesrecord = nSamplesForcerecord
    eval = DataEvaluation()   

    while t_diff < tForceRecord:
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_record.Task_I.read(nSamplesrecord )
        force_normalized = [(abs(x)- F_OFFSET)* F_FACTOR for x in data]
        arr = np.array(force_normalized)
        np.savetxt(File, [arr], delimiter="\n", fmt='%.2f')
        eval.checklimits(*arr)
    
        end = time.time()
        t_diff = end - start

    amax = eval.getmax()
    amin = eval.getmin()
    File.write(" ; max : \n")
    File.write(" ; ")
    np.savetxt(File, [amax], delimiter="\n", fmt='%.2f')
    File.write(" ; min : \n")
    File.write(" ; ")
    np.savetxt(File, [amin], delimiter="\n", fmt='%.2f')

    Task_record.Task_I.stop()
    Task_record.Task_I.close()
    File.close()

    print ("duration of data recording" + str(t_diff) + "\n")
    print("RecordProzecss end \n") 



gTriggerStateFF = False
gTrigger = TriggerState()
gTask_trigger = NIaiVoltageTask()
gForcelogfile =""
gVoltagelogfile =""
gReader = None
gnSamplestrigger = 0

def NIInit():
    global gTriggerStateFF 
    global gTrigger
    global gForcelogfile
    global gVoltagelogfile
    gTriggerStateFF = False
    gTrigger = TriggerState()
    gVoltagelogfile = config.get('Vai', 'Voltagelogfile')
    gForcelogfile =  config.get('Force', 'Forcelogfile')
    

def RecordForceProcess():
    print( " ForceProzecss: \n")

    Task_record = NIaiBridgeTask()
    chnForce = config.get('Force', 'chnForce')
    minValForce = float(config.get('Force', 'minValForce'))
    maxValForce = float(config.get('Force', 'maxValForce'))
    fsForceRecord = int(config.get('Force', 'fsForceRecord'))
    nSamplesForcerecord = int(config.get('Force', 'nSamplesForcerecord'))
    F_OFFSET = float(config.get('Force', 'F_OFFSET'))
    F_FACTOR = float(config.get('Force', 'F_FACTOR'))
    Forcelogfile =  config.get('Force', 'Forcelogfile')
    tForceRecord = int(config.get('Force', 'tForceRecord'))

    Task_record.config(chnForce, minValForce, maxValForce, fsForceRecord, nSamplesForcerecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start
    try:
        File = open(Forcelogfile, "w")
    except:
        print ("recod logfile" + Forcelogfile + "not found\n")

    nSamplesrecord = nSamplesForcerecord
    eval = DataEvaluation()   

    while t_diff < tForceRecord:
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_record.Task_I.read(nSamplesrecord )
        force_normalized = [(abs(x)- F_OFFSET)* F_FACTOR for x in data]
        arr = np.array(force_normalized)
        np.savetxt(File, [arr], delimiter="\n", fmt='%.2f')
        eval.checklimits(*arr)
    
        end = time.time()
        t_diff = end - start

    amax = eval.getmax()
    amin = eval.getmin()
    File.write(" ; max : \n")
    File.write(" ; ")
    np.savetxt(File, [amax], delimiter="\n", fmt='%.2f')
    File.write(" ; min : \n")
    File.write(" ; ")
    np.savetxt(File, [amin], delimiter="\n", fmt='%.2f')

    Task_record.Task_I.stop()
    Task_record.Task_I.close()
    File.close()

    print ("duration of data recording" + str(t_diff) + "\n")
    print("RecordProzecss end \n") 

def NIRecordForceProcess():
    print( " ForceProzecss: \n")

    Task_record = NIaiBridgeTask()
    chnForce = config.get('Force', 'chnForce')
    minValForce = float(config.get('Force', 'minValForce'))
    maxValForce = float(config.get('Force', 'maxValForce'))
    fsForceRecord = int(config.get('Force', 'fsForceRecord'))
    nSamplesForcerecord = int(config.get('Force', 'nSamplesForcerecord'))
    F_OFFSET = float(config.get('Force', 'F_OFFSET'))
    F_FACTOR = float(config.get('Force', 'F_FACTOR'))
    Forcelogfile =  config.get('Force', 'Forcelogfile')
    tForceRecord = int(config.get('Force', 'tForceRecord'))

    Task_record.config(chnForce, minValForce, maxValForce, fsForceRecord, nSamplesForcerecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start
    try:
        File = open(Forcelogfile, "w")
    except:
        print ("recod logfile" + Forcelogfile + "not found\n")

    nSamplesrecord = nSamplesForcerecord
    eval = DataEvaluation()   

    while t_diff < tForceRecord:
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_record.Task_I.read(nSamplesrecord )
        force_normalized = [(abs(x)- F_OFFSET)* F_FACTOR for x in data]
        arr = np.array(force_normalized)
        np.savetxt(File, [arr], delimiter="\n", fmt='%.2f')
        eval.checklimits(*arr)
    
        end = time.time()
        t_diff = end - start

    amax = eval.getmax()
    amin = eval.getmin()
    File.write(" ; max : \n")
    File.write(" ; ")
    np.savetxt(File, [amax], delimiter="\n", fmt='%.2f')
    File.write(" ; min : \n")
    File.write(" ; ")
    np.savetxt(File, [amin], delimiter="\n", fmt='%.2f')

    Task_record.Task_I.stop()
    Task_record.Task_I.close()
    File.close()

    print ("duration of data recording" + str(t_diff) + "\n")
    print("RecordProzecss end \n") 


def NIInit():
    global gTriggerStateFF 
    global gTrigger
    global gForcelogfile
    global gVoltagelogfile
    gTriggerStateFF = False
    gTrigger = TriggerState()
    gVoltagelogfile = config.get('Vai', 'Voltagelogfile')
    gForcelogfile =  config.get('Force', 'Forcelogfile')

def NIgetForcelogfile():
    global gForcelogfile
    return gForcelogfile

def NIgetVoltagelogfile():
    global gVoltagelogfile
    return gVoltagelogfile

def NIgetTriggerStatus():
    global gTriggerStateFF
    return gTriggerStateFF



#NIInit()
#NIRecordVoltageProcess()
#start = time.time()
#NITriggerProcess()
#end = time.time()
#print("Triggertime Duration##"+ str(end - start)+"\n")
#NIRecordForceProcess()
#NIgetForcelogfile()

start = time.time()
print ("duration of data recording" + str(start) + "\n")
NITriggerProcessINI()
#while not gTriggerStateFF:
#    NITriggerProcessing()
NITriggerProcessEnd()
end = time.time()
print ("duration of data recording" + str(end-start) + "\n")
#NITriggerProcessEnd()
#RecordVoltageProcess()
#RecordForceProcess()

'''
chn ="c"

def testConfigvH1():
    vH= config.get('Vthreshold', 'vHigh1')
    global chn 
    chn =config.get('Vai', 'chnVoltage')
    print("vH: ",vH)
    return vH

conf_vH1 = testConfigvH1()

arr =  [0,-2,-6,5,9,-3,0,8,7,5,1,100,-9,-2]
eval = DataEvaluation()
eval.checklimits(*arr)
eval.getmax()
eval.getmin()

file = config.get('Vai', 'logfile')
File = open(file, "w")
File.write("File accessed\n"+chn)
File.close()
''' 


def testReturn():
    global gTriggerStateFF
    return gTriggerStateFF