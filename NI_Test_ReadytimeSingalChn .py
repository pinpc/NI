
from nidaqmx import *
import nidaqmx
import numpy as np
import time 
from enum import Enum
from nidaqmx.constants import (
    Coupling, DigitalPatternCondition, Edge, Slope, TriggerType,
    WindowTriggerCondition1)


def exportData(data):
    import csv
    filename = "c:\\temp\\NI_trigger"+str(testcycle)+".csv"
    file =  open(filename, 'w', newline='')

    #file.write("time duration: "+ str(endtime-starttime)+"\n") 
    i = 0
    for item in data:
        item = round(item,3) 
        str_1 = str(i)+ ":"+ str(item)+"\n"
        file.write(str_1)
        i += 1
    file.close()
    print("Date acquisition completed \n")

start = time.time()
print("hello")
end = time.time()
print(end - start)

fsTrigger = 10000 #Hz
nSamplestrigger = 200
pretrigger_samples =100


fsRecorde = 20000 #Hz
T = 1/4
nSamplesrecord = int(T * fsRecorde ) #samples
tRecord = 1 # 10s
filename = "c:\\temp_test\\voltage.csv"
s1 = 0
s2 = 0

Task_I = nidaqmx.Task()

#Task_I.ai_channels.add_ai_voltage_chan('Laser-Ready/ai2:6', 
Task_I.ai_channels.add_ai_voltage_chan('Laser-Ready/ai2', 
                                        min_val=-10, max_val=10,
                                        terminal_config = nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)

Task_I.timing.cfg_samp_clk_timing(rate = fsTrigger,
                                #source='ao/SampleClock', # same clock as for the output
                                sample_mode = nidaqmx.constants.AcquisitionType.FINITE,
                                samps_per_chan = nSamplestrigger)

Task_I.triggers.reference_trigger.cfg_anlg_edge_ref_trig('Laser-Ready/ai2', pretrigger_samples, trigger_slope=Slope.FALLING, trigger_level=3.0) 

reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_I.in_stream)


for testcycle in range (2):
    Task_I.start()
    print("Date acquisition start \n")
    #start
    #starttime = int(round(time.time() * 1000))
    #print("starttime "+str(starttime))
    data = np.zeros(nSamplestrigger )
    data = Task_I.read(nSamplestrigger,timeout= 100 )
    #endtime = int(round(time.time() * 1000))
    print("Date reading end \n")
    exportData(data)
    Task_I.stop()
    time.sleep(1)
Task_I.close()

