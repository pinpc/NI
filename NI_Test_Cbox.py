
from nidaqmx import *
import nidaqmx
import numpy as np
import time 
start = time.time()
print("hello")
end = time.time()
print(end - start)

fs = 10000 #Hz
T = 1/4
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
Task_I.ai_channels.add_ai_voltage_chan('Optolaser/ai0',
                                       min_val=-2.0, max_val=2.0,
                                       terminal_config = nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)
Task_I.timing.cfg_samp_clk_timing(  rate = fs,
                                    #source='ao/SampleClock', # same clock as for the output
                                    sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                    samps_per_chan=nSamples)

#create writter and reader
#writer = nidaqmx.stream_writers.AnalogSingleChannelWriter(Task_O.out_stream, auto_start=False)
reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_I.in_stream)

#write first signal
#writer.write_many_sample(sig)
#Task_O.write(sig, auto_start=False)

#start
Task_I.start()

#Task_O.start()

while 1:
    #read first data
    start = time.time()
    data = np.zeros(nSamples)
    reader.read_many_sample(data,nSamples)
    data = Task_I.read(nSamples )
    #print("hello")
    end = time.time()
    print("Delta Time: "+ str(end - start)+"\n")
    print("next Reading\n") 
"""
    i = 0
    for item in data:
        i += 1
        print( str(i+1)+ " : "+ str(item) +"\n") """

 
Task_I.stop()
Task_I.close()

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