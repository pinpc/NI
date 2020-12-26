
from nidaqmx import *
import nidaqmx
import numpy as np
import time 
from enum import Enum
from nidaqmx.constants import (
    Coupling, DigitalPatternCondition, Edge, Slope, TriggerType,
    WindowTriggerCondition1)

start = time.time()
print("hello")
end = time.time()
print(end - start)

fsTrigger = 1000 #Hz
nSamplestrigger = 10
trigger_level = 4.0
trigger_slope= 10280

fsRecorde = 20000 #Hz
T = 1/4
nSamplesrecord = int(T * fsRecorde ) #samples
tRecord = 1 # 10s
filename = "c:\\temp_test\\voltage.csv"
s1 = 0
s2 = 0

Task_I = nidaqmx.Task()

#Task_I.ai_channels.add_ai_voltage_chan('Laser-Ready/ai2:6', 
Task_I.ai_channels.add_ai_voltage_chan('Laser-Ready/ai2:6', 
                                        min_val=-10, max_val=10,
                                        terminal_config = nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)

Task_I.timing.cfg_samp_clk_timing(rate = fsTrigger,
                                #source='ao/SampleClock', # same clock as for the output
                                sample_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                samps_per_chan = nSamplestrigger)


reader = nidaqmx.stream_readers.AnalogMultiChannelReader(Task_I.in_stream)

#start
Task_I.start()


while True:
    #read first data
    start = time.time()
    data = np.zeros(shape=(5,nSamplestrigger), dtype=float, order='C')
    reader.read_many_sample(data,nSamplestrigger)

    data = Task_I.read(nSamplestrigger )
    i = 0
    for item in data:
       item = round(item[0],3) 
       print(str(i)+ ":"+ str(item)+ " ")
       i += 1
    print("\n")
        
Task_I.stop()
Task_I.close()
 
    #print("Delta MaxTime: "+ str(t_max)+"\n")
    #print("Trigger Task end \n")