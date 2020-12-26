
from nidaqmx import *
import nidaqmx
import numpy as np
import time 
from enum import Enum

start = time.time()
print("hello")
end = time.time()
print(end - start)

class Config():
    #Trigger measurement setting
    fsTrigger = 500 #Hz
    nSamplestrigger = 1
    chnTrigger = 'Laser-Ready/ai2'
    minValTrigger = -10 # -10V
    maxValTrigger = 10 # 10V
    
    #Voltage measurement setting
    vHigh1 = 4.5
    vHigh2 = 4.0
    vLow1 = 1
    vLow2 = 0.5
    
    fsVoltageRecord = 20000 #Hz
    T = 1/4
    nSamplesVoltagerecord = int(T * fsVoltageRecord ) #samples
    tVoltageRecord = 1 # 10s
    voltagefilename = "c:\\temp_test\\voltage.csv"
    chnVoltage = 'Laser-Ready/ai3'
    minValVoltage = -10 # -10V
    maxValVoltage = 10 # 10V

    #Force measurement setting
    F_FACTOR = 238.8741
    F_OFFSET = 0.00828929

    fsForceRecord = 10000 #Hz
    T = 1/2
    nSamplesForcerecord = int(T * fsForceRecord) #samples
    tForceRecord = 5 # 10s
    forcefilename = "c:\\temp_test\\Force.csv"
    chnForce = 'Force/ai0'
    minValForce = -0.5 # -0.5V
    maxValForce = 0.5 # 0.5V

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
    
    def __ini__(self, s, state):
        self.s = s
        self.triggerstate = state
        self.currentState = state
        self.pastState = state

    def getSignal(self, signalIn):
        self.s = signalIn

    def checkState(self):
       if self.triggerstate == Signalstatus.NCH:
            if self.s <= Config.vLow1 :
                self.triggerstate = Signalstatus.FF
                return
       
       if self.triggerstate == Signalstatus.FF:
            if self.s <= Config.vLow2 :
                self.triggerstate = Signalstatus.NCL
                return
                
       if self.triggerstate == Signalstatus.NCL:
            if self.s >= Config.vHigh1 :
                self.triggerstate = Signalstatus.RF
                return

       if self.triggerstate == Signalstatus.RF:
            if self.s >= Config.vHigh2 :
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
                                                     min_val=min, max_val=max,
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
                                                    min_val = min, max_val=max,
                                                    units = nidaqmx.constants.BridgeUnits.M_VOLTS_PER_VOLT,
                                                    bridge_config = nidaqmx.constants.BridgeConfiguration.FULL_BRIDGE,
                                                    voltage_excit_source = nidaqmx.constants.ExcitationSource.INTERNAL,
                                                    nominal_bridge_resistance = 350.0)

        self.Task_I.timing.cfg_samp_clk_timing( rate = fs,
                                                #source='ao/SampleClock', # same clock as for the output
                                                sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                                samps_per_chan = sample) 

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

def RecordVoltageProcess(file):
    print( " RecordVoltageProzecss: \n")
    try:
        File = open(file, "w")
    except:
        print ("recod file" + file + "not found\n")

    Task_record = NIaiVoltageTask()
    Task_record.config(Config.chnVoltage, Config.minValVoltage, Config.maxValVoltage, Config.fsVoltageRecord, Config.nSamplesVoltagerecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start
    nSamplesrecord = Config.nSamplesVoltagerecord

    while t_diff < Config.tVoltageRecord:
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

def RecordForceProcess(file):
    print( " ForceProzecss: \n")
    try:
        File = open(file, "w")
    except:
        print ("recod file" + file + "not found\n")

    Task_record = NIaiBridgeTask()
   
    Task_record.config(Config.chnForce, Config.minValForce, Config.maxValForce, Config.fsForceRecord, Config.nSamplesForcerecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start
    nSamplesrecord = Config.nSamplesForcerecord
    eval = DataEvaluation()
   

    while t_diff < Config.tForceRecord:
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_record.Task_I.read(nSamplesrecord )
        force_normalized = [(abs(x)-Config.F_OFFSET)*Config.F_FACTOR for x in data]
        arr = np.array(force_normalized)
        np.savetxt(File, [arr], delimiter="\n", fmt='%.2f')
        eval.checklimits(*arr)
    
        end = time.time()
        t_diff = end - start

    amax = eval.getmax()
    amin = eval.getmin()
    File.write(" ; max : \n")
    np.savetxt(File, [amax], delimiter="\n", fmt='%.2f')
    File.write(" ; min : \n")
    np.savetxt(File, [amin], delimiter="\n", fmt='%.2f')

    Task_record.Task_I.stop()
    Task_record.Task_I.close()
    File.close()

    print ("duration of data recording" + str(t_diff) + "\n")
    print("RecordProzecss end \n") 

TriggerProzecss()
#RecordVoltageProcess(Config.voltagefilename)
#RecordForceProcess(Config.forcefilename)

"""
arr =  [0,-2,-6,5,9,-3,0,8,7,5,1,100,-9,-2]
eval = DataEvaluation()
eval.checklimits(*arr)
eval.getmax()
eval.getmin()
"""
