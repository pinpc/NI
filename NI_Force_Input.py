
from nidaqmx import *
import nidaqmx
import numpy as np
import time 
import pickle
import json

DataFILE ='C://temp//NI_Force//Force_data.cvs'
F_FACTOR = 238.8741
F_OFFSET = 0.00828929
start = time.time()
print("hello")
end = time.time()
print(end - start)

fs = 10000 #Hz
T = 1/2
nSamples = int(T * fs) #samples
#nSamples =1452000

"""

import matplotlib.pyplot as plt

plt.ion()


a0 = 5
f0 = 3
t = np.arange(nSamples)/fs
sig = a0*np.sin(2*np.pi*f0*t)

fig, ax = plt.subplots()
plt.subplots_adjust(left=0.25, bottom=0.25)

lw, = plt.plot(t, sig, lw=2, color='red',label= 'write')
lr, = plt.plot(t, sig*0, lw=2, color='blue',label= 'read')


#create outup channel
Task_O = nidaqmx.Task()
Task_O.ao_channels.add_ao_voltage_chan('Dev2/ao0')
Task_O.out_stream.regen_mode = nidaqmx.constants.RegenerationMode.DONT_ALLOW_REGENERATION
Task_O.timing.cfg_samp_clk_timing(  rate = fs,
                                    sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                    samps_per_chan=nSamples*1000) 
"""

#create input channel
Task_I = nidaqmx.Task()
Task_I.ai_channels.add_ai_bridge_chan('Force/ai0',
                                       min_val=-0.5, max_val=0.5,
                                       units=nidaqmx.constants.BridgeUnits.M_VOLTS_PER_VOLT,
                                       bridge_config= nidaqmx.constants.BridgeConfiguration.FULL_BRIDGE,
                                       voltage_excit_source=nidaqmx.constants.ExcitationSource.INTERNAL,
                                       nominal_bridge_resistance= 350.0)
Task_I.timing.cfg_samp_clk_timing(  rate = fs,
                                    #source='ao/SampleClock', # same clock as for the output
                                    sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                    samps_per_chan=nSamples) 


class NIForceTask:
    
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

#create writter and reader
#writer = nidaqmx.stream_writers.AnalogSingleChannelWriter(Task_O.out_stream, auto_start=False)
reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_I.in_stream)

#write first signal
#writer.write_many_sample(sig)
#Task_O.write(sig, auto_start=False)

#start
Task_I.start()

#Task_O.start()

for loop in range(3):
    #read first data
    #start = time.time()
    data = np.zeros(nSamples)
    reader.read_many_sample(data,nSamples)
    data = Task_I.read(nSamples )
    force_normalized = [(abs(x)-F_OFFSET)*F_FACTOR for x in data]
    arr = np.array(force_normalized)
    np.savetxt('force_data.csv', [arr], delimiter=';', fmt='%.2f')
   # force_str = ["%.2f" % x for x in force_normalized]
    average = np.mean(data)
    max = np.max(data)
    min = np.min(data)
    #json.dump(force_str, filehandle)
    print("len: " + str(len(data)))
    print(" av: "+str(average)+ " Max:" +str(max)+" Min: "+str(min) +"\n" )
    #end = time.time()
    print("Delta Time: "+ str(end - start)+"\n")
    #print("next Reading\n") 

"""
    i = 0
    for item in data:
        i += 1
        print( str(i+1)+ " : "+ str(item) +"\n") """

 
Task_I.stop()
Task_I.close()
#filehandle.close()

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
