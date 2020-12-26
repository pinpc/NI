
from nidaqmx import *
import nidaqmx
import numpy as np
import time 
from enum import Enum

start = time.time()
print("hello")
end = time.time()
print(end - start)

fsTrigger = 500 #Hz
nSamplestrigger = 1

fsRecorde = 20000 #Hz
T = 1/4
nSamplesrecord = int(T * fsRecorde ) #samples
tRecord = 1 # 10s
filename = "c:\\temp_test\\voltage.csv"
s1 = 0
s2 = 0

class Signalstatus(Enum):
    NCH = 0
    NCL = 4
    RF = 2
    FF = 1
vHigh1 = 4.5
vHigh2 = 4.0
vLow1 = 1
vLow2 = 0.5



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
            if self.s <= vLow1 :
                self.triggerstate = Signalstatus.FF
                return
       
       if self.triggerstate == Signalstatus.FF:
            if self.s <= vLow2 :
                self.triggerstate = Signalstatus.NCL
                return
                
       if self.triggerstate == Signalstatus.NCL:
            if self.s >= vHigh1 :
                self.triggerstate = Signalstatus.RF
                return

       if self.triggerstate == Signalstatus.RF:
            if self.s >= vHigh2 :
                self.triggerstate = Signalstatus.NCH
                return

    def getTriggerstate(self):
       if self.currentState != self.triggerstate:
           print ("Trigger state:" + str(self.triggerstate) + "\n")
           self.currentState = self.triggerstate
       return self.triggerstate

class NITask:
    
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

def TriggerProzecss():

    Task_trigger = NITask()
    chn = 'Laser-Ready/ai2'
    Task_trigger.config(chn, -10.0, 10.0, fsTrigger, nSamplestrigger)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_trigger.Task_I.in_stream)

    #start
    Task_trigger.Task_I.start()
    #Task_O.start()


    trigger = TriggerState()
    t_max = 0

    while  trigger.getTriggerstate() != Signalstatus.FF:
        #read first data
        start = time.time()
        data = np.zeros(nSamplestrigger)
        reader.read_many_sample(data,nSamplestrigger)
        data = Task_trigger.Task_I.read(nSamplestrigger )
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
            #print( str(i+1)+ " : "+ str(item) +"\n")
 
    Task_trigger.Task_I.stop()
    Task_trigger.Task_I.close()
    print("Delta MaxTime: "+ str(t_max)+"\n")
    print("Trigger Task end \n")

def RecordProzecss(file):
    print( " RecordProzecss: \n")
    try:
        File = open(file, "w")
    except:
        print ("recod file" + file + "not found\n")

    Task_record = NITask()
    chn = 'Laser-Ready/ai3'
    Task_record.config(chn, -10.0, 10.0, fsRecorde, nSamplesrecord)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_record.Task_I.in_stream)

    #start
    Task_record.Task_I.start()
    t_max = 0
    start = end = time.time()
    t_diff = end - start

    while t_diff < tRecord:
        data = np.zeros(nSamplesrecord)
        reader.read_many_sample(data,nSamplesrecord)
        data = Task_record.Task_I.read(nSamplesrecord )
        end = time.time()
        t_diff = end - start

        np.savetxt(File, [data], delimiter="\n", fmt='%.2f')

    
    Task_record.Task_I.stop()
    Task_record.Task_I.close()
    File.close()

    print ("duration of data recording" + str(t_diff) + "\n")
    print("RecordProzecss end \n")

TriggerProzecss()
RecordProzecss(filename)


"""
Task_I = nidaqmx.Task()

def config(chn, min, max, fs, sample):
        self.Task_I.ai_channels.add_ai_voltage_chan( 'Laser-Ready/ai2',
                                                      min_val=-10.0, max_val=10.0,
                                                      terminal_config = nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)
    Task_I.timing.cfg_samp_clk_timing(  rate = fs,
                                        #source='ao/SampleClock', # same clock as for the output
                                        sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                        samps_per_chan=nSamples)
"""

"""
#pause for a moment
plt.pause(T)

#update curve
lr.set_ydata(data)
plt.pause(5)

#Works until here

for i in range(10):
    #create a new signal
    amp = np.random.random(1)*10
    freq = np.random.random(1)*10
    sig = amp*np.sin(2*np.pi*freq*t)

    #write next signal
    writer.write_many_sample(sig)
    # Task_O.write(sig, auto_start=False)
    lw.set_ydata(sig)

    #read next data
    reader.read_many_sample(data,nSamples)#)
    #data = Task_I.read(nSamples )


    plt.pause(T)
    lr.set_ydata(data)
    plt.pause(5)


    nidaqmx.errors.Error()
 
Task_O.stop()
Task_O.close()
Task_O.stop()
Task_O.close()"""