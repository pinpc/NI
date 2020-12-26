
from nidaqmx import *
import nidaqmx
import numpy as np
import time 
from enum import Enum

import tkinter as tk
import tkinter.font
import time
global lightstatus1
global light1status

light1status = 0

#root = tk.Tk()

start = time.time()
print("hello")
end = time.time()
print(end - start)

class Signalstatus(Enum):
    NCH = 0
    FF = 1
    RF = 2
    NCL = 4

global ReadyTriggerState
ReadyTriggerState = Signalstatus.NCH


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
    global ReadyTriggerState
    Task_trigger = NIaiVoltageTask()
    Task_trigger.config(Config.chnTrigger, Config.minValTrigger, Config.maxValTrigger, Config.fsTrigger, Config.nSamplestrigger)

    reader = nidaqmx.stream_readers.AnalogSingleChannelReader(Task_trigger.Task_I.in_stream)


    #start
    Task_trigger.Task_I.start()
    #Task_O.start()

    trigger = TriggerState()
    t_max = 0
    nSamplesrecord = Config.nSamplestrigger

    while trigger.getTriggerstate() != Signalstatus.FF:
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
            ReadyTriggerState = trigger.getTriggerstate()
           #print( str( trigger.getTriggerstate())+ " : "+ str(item) +"\n")
 
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

#TriggerProcess()
#RecordVoltageProcess(Config.voltagefilename)
#RecordForceProcess(Config.forcefilename)



def ReadyStatus():
    global strongboxlt
    global ReadyTriggerState
    global root
    if (ReadyTriggerState == Signalstatus.NCL) or (ReadyTriggerState == Signalstatus.FF):
    	strongboxlt.config(bg = "red",text = " Test run" )
    else:
    	light1status = 0
    	strongboxlt.config(bg = "green",text = "Test Stop" )
    '''
    if light1status == 0:
    	strongboxlt.config(bg = "green")
    	light1status = 1
    else:
    	light1status = 0
    	strongboxlt.config(bg = "red")'''
    root.after(500, ReadyStatus)



from threading import Thread
from queue import Queue
import time


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()

        self.entrythingy = tk.Entry()
        self.entrythingy.pack()

        # Create the application variable.
        self.contents = tk.StringVar()
        # Set it to some value.
        self.contents.set("this is a variable")
        # Tell the entry widget to watch this variable.
        self.entrythingy["textvariable"] = self.contents

        # Define a callback for when the user hits return.
        # It prints the current value of the variable.
        self.entrythingy.bind('<Key-Return>',
                             self.print_contents)

    def print_contents(self, event):
        print("Hi. The current entry content is:",
              self.contents.get())

'''root = tk.Tk()
myapp = App(root)
myapp.mainloop()'''

def thread1(threadname, q):
    root = tk.Tk()
    myapp = App(root)
    myapp.mainloop()

#global root


def thread_GUI(threadname, q):
    global strongboxlt
    global root
    root = tk.Tk()
    frames_Title = tk.font.Font(family = "Calibri", size = 20)
    buttonfont = tk.font.Font(family = "Calibri", size = 30)
    # Main Frame Colour
    lightingmainC = "#ffffd4"
    watermainC = "#c9e5ff"
    tempmainC = "#ffdfba"
    hydromainC = "#baffc9"
    # Sub Frame Colour
    lightingsubC = "yellow"
    watersubC = "blue"
    tempsubC = "orange"
    # creating frames for control famalies
    Triggert_frame = tk.Frame(root, height = 460, width = 912, bg = lightingmainC)
    Triggert_frame.place(x=0,y=0)
    water_frame = tk.Frame(root, height = 460, width = 912, bg = watermainC)
    water_frame.place(x=912,y=0)
    temp_frame = tk.Frame(root, height = 460, width = 912, bg = tempmainC)
    temp_frame.place(x=0,y=460)
    hydro_frame = tk.Frame(root, height = 460, width = 912, bg = hydromainC)
    hydro_frame.place(x=912, y=460)

    # titles in frames
    Triggert_Title = tk.Label(Triggert_frame, font = frames_Title, text = "Test Triggert", bg = lightingmainC)
    Triggert_Title.place(x=400, y=12)
    water_Title = tk.Label(water_frame, font = frames_Title, text = "Watering", bg = watermainC)
    water_Title.place(x=400, y=12)
    temp_Title = tk.Label(temp_frame, font = frames_Title, text = "Temperature Control", bg = tempmainC)
    temp_Title.place(x=340, y=12)
    hydro_Title = tk.Label(hydro_frame, font = frames_Title, text = "Hydroponic Pumps", bg = hydromainC)
    hydro_Title.place(x=350, y=12)

    #Triggert subframes
    Triggert_subframe1 = tk.Frame(Triggert_frame, height = 360, width = 350, bg = lightingsubC, highlightthickness = 3, highlightbackground = "black")
    Triggert_subframe1.place(x=50,y=50)
    Triggert_subframe2 = tk.Frame(Triggert_frame, height = 155, width = 412, bg = lightingsubC, highlightthickness = 3, highlightbackground = "black")
    Triggert_subframe2.place(x=450,y=50)
    Triggert_subframe3 = tk.Frame(Triggert_frame, height = 155, width = 412, bg = lightingsubC, highlightthickness = 3, highlightbackground = "black")
    Triggert_subframe3.place(x=450,y=255)

    #lighting subframe labels
    Triggert_SubTitle1 = tk.Label(Triggert_subframe1, font = frames_Title, text = "Test status", bg = lightingsubC)
    Triggert_SubTitle1.place(x=110, y=10)
    Triggert_SubTitle2 = tk.Label(Triggert_subframe2, font = frames_Title, text = "Tub 1", bg = lightingsubC)
    Triggert_SubTitle2.place(x=165, y=10)
    Triggert_SubTitle3 = tk.Label(Triggert_subframe3, font = frames_Title, text = "Tub 2", bg = lightingsubC)
    Triggert_SubTitle3.place(x=165, y=10)

    #lighting subframe buttons
    strongboxlt = tk.Button(Triggert_subframe1, command = ReadyStatus, text = "Strngbx Light", fg = "black", bg = "red", padx = 20, pady = 20, font = buttonfont )
    strongboxlt.place(x = 45, y= 75)
    bucketlt = tk.Button(Triggert_subframe1, text = "Bucket Light", fg = "black", bg = "red", padx = 25, pady = 20, font = buttonfont )
    bucketlt.place(x = 45, y= 200)
    tub1lt1 = tk.Button(Triggert_subframe2, text = "Light 1", fg = "black", bg = "red", padx = 5, pady = 10, font = buttonfont )
    tub1lt1.place(x = 5, y= 60)
    tub1lt2 = tk.Button(Triggert_subframe2, text = "Light 2", fg = "black", bg = "red", padx = 5, pady = 10, font = buttonfont )
    tub1lt2.place(x = 140, y= 60)
    tub1lt3 = tk.Button(Triggert_subframe2, text = "Light 3", fg = "black", bg = "red", padx = 5, pady = 10, font = buttonfont )
    tub1lt3.place(x = 275, y= 60)
    tub2lt1 = tk.Button(Triggert_subframe3, text = "Light 1", fg = "black", bg = "red", padx = 5, pady = 10, font = buttonfont )
    tub2lt1.place(x = 5, y= 60)
    tub2lt2 = tk.Button(Triggert_subframe3, text = "Light 2", fg = "black", bg = "red", padx = 5, pady = 10, font = buttonfont )
    tub2lt2.place(x = 140, y= 60)
    tub2lt3 = tk.Button(Triggert_subframe3, text = "Light 3", fg = "black", bg = "red", padx = 5, pady = 10, font = buttonfont )
    tub2lt3.place(x = 275, y= 60)

    #watering subframes
    watering_subframe1 = tk.Frame(water_frame, height = 150, width = 750, bg = watersubC, highlightthickness = 3, highlightbackground = "black")
    watering_subframe1.place(x=80,y=50)
    watering_subframe2 = tk.Frame(water_frame, height = 150, width = 750, bg = watersubC, highlightthickness = 3, highlightbackground = "black")
    watering_subframe2.place(x=80,y=255)

    #watering subframe labels
    water_SubTitle1 = tk.Label(watering_subframe1, font = frames_Title, text = "Tub 1", bg = watersubC, fg = "white")
    water_SubTitle1.place(x=10, y=60)
    water_SubTitle2 = tk.Label(watering_subframe2, font = frames_Title, text = "Tub 2", bg = watersubC, fg = "white")
    water_SubTitle2.place(x=10, y=60)

    #watering buttons
    tub1auto = tk.Button(watering_subframe1, text = "Auto", fg = "black", bg = "green", padx = 30, pady = 20, font = buttonfont )
    tub1auto.place(x = 125, y= 30)
    tub1fill = tk.Button(watering_subframe1, text = "Fill", fg = "black", bg = "red", padx = 35, pady = 20, font = buttonfont )
    tub1fill.place(x = 325, y= 30)
    tub1drain = tk.Button(watering_subframe1, text = "Drain", fg = "black", bg = "green", padx = 30, pady = 20, font = buttonfont )
    tub1drain.place(x = 500, y= 30)
    tub2auto = tk.Button(watering_subframe2, text = "Auto", fg = "black", bg = "green", padx = 30, pady = 20, font = buttonfont )
    tub2auto.place(x = 125, y= 30)
    tub2fill = tk.Button(watering_subframe2, text = "Fill", fg = "black", bg = "red", padx = 35, pady = 20, font = buttonfont )
    tub2fill.place(x = 325, y= 30)
    tub2drain = tk.Button(watering_subframe2, text = "Drain", fg = "black", bg = "green", padx = 30, pady = 20, font = buttonfont )
    tub2drain.place(x = 500, y= 30)

    #heat subframes
    temp_subframe1 = tk.Frame(temp_frame, height = 180, width = 750, bg = tempsubC, highlightthickness = 3, highlightbackground = "black")
    temp_subframe1.place(x=80,y=50)

    #heat subframe labels
    temp_ambientlabel = tk.Label(temp_subframe1, font = frames_Title, text = "Ambient Tempature", bg = tempsubC)
    temp_ambientlabel.place(x=260, y=10)
    hydro_ambientlabel = tk.Label(temp_subframe1, font = frames_Title, text = "Hydroponics", bg = tempsubC)
    hydro_ambientlabel.place(x=75, y=50)
    tub1_ambientlabel = tk.Label(temp_subframe1, font = frames_Title, text = "Tub 1", bg = tempsubC)
    tub1_ambientlabel.place(x=330, y=50)
    tub2_ambientlabel = tk.Label(temp_subframe1, font = frames_Title, text = "Tub 2", bg = tempsubC)
    tub2_ambientlabel.place(x=550, y=50)

    #hydroponic pump buttons
    strongbox1pump = tk.Button(hydro_frame, text = "Strongbox 1", fg = "black", bg = "red", padx = 30, pady = 30, font = buttonfont, highlightthickness = 5, highlightbackground = "yellow" )
    strongbox1pump.place(x = 50, y= 100)
    strongbox2pump = tk.Button(hydro_frame, text = "Strongbox 2", fg = "black", bg = "red", padx = 30, pady = 30, font = buttonfont, highlightthickness = 5, highlightbackground = "yellow" )
    strongbox2pump.place(x = 50, y= 300)
    bucket1pump = tk.Button(hydro_frame, text = "Bucket 1", fg = "black", bg = "red", padx = 30, pady = 30, font = buttonfont, highlightthickness = 5, highlightbackground = "blue" )
    bucket1pump.place(x = 375, y= 50)
    bucket2pump = tk.Button(hydro_frame, text = "Bucket 2", fg = "black", bg = "red", padx = 30, pady = 30, font = buttonfont, highlightthickness = 5, highlightbackground = "blue" )
    bucket2pump.place(x = 650, y= 50)
    bucket3pump = tk.Button(hydro_frame, text = "Bucket 3", fg = "black", bg = "red", padx = 30, pady = 30, font = buttonfont, highlightthickness = 5, highlightbackground = "blue" )
    bucket3pump.place(x = 510, y= 185)
    bucket4pump = tk.Button(hydro_frame, text = "Bucket 4", fg = "black", bg = "red", padx = 30, pady = 30, font = buttonfont, highlightthickness = 5, highlightbackground = "blue" )
    bucket4pump.place(x = 375, y= 325)
    bucket5pump = tk.Button(hydro_frame, text = "Bucket 5", fg = "black", bg = "red", padx = 30, pady = 30, font = buttonfont, highlightthickness = 5, highlightbackground = "blue" )
    bucket5pump.place(x = 650, y= 325)


    root.after(500, ReadyStatus)
    root.mainloop()
    #read variable "a" modify by thread 2
    '''while True:
        a = q.get()
        if a is None: return # Poison pill
        print ("a=: ",a)'''

def thread2(threadname, q):
    while True:
        TriggerProcess()
        RecordVoltageProcess(Config.voltagefilename)
   
    '''
    a = 0
    for i in range(10):
        a += 1
        q.put(a)
        time.sleep(1)
    q.put(None) # Poison pill'''

def thread3(threadname, q):
    RecordVoltageProcess(Config.voltagefilename)

queue = Queue()
thread1 = Thread( target=thread_GUI, args=("Thread-1", queue) )
thread2 = Thread( target=thread2, args=("Thread-2", queue) )
#thread3 = Thread( target=thread3, args=("Thread-3", queue) )
thread1.start()
thread2.start()
#thread3.start()

thread1.join()
thread2.join()
thread3.join()


"""
arr =  [0,-2,-6,5,9,-3,0,8,7,5,1,100,-9,-2]
eval = DataEvaluation()
eval.checklimits(*arr)
eval.getmax()
eval.getmin()
"""
