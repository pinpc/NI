import nidaqmx
from nidaqmx.constants import (LineGrouping)
import time

MOTORSTART22 =[True, True, True, True,True, True, True, True,True, True, True, True,True, True, True, True,True, True, True, True,True, True]
MOTORSTOP22  =[False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]

task_o = nidaqmx.Task()
task_o.do_channels.add_do_chan('Motorcontrol/port0/line0:21',
                                line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES)

try:
    task_o.start()
    print('N Lines 1 Sample Boolean Write (Error Expected): ')
    while True:
        task_o.write(MOTORSTART22)
        time.sleep(1)
        task_o.write(MOTORSTOP22)
        time .sleep(1)
    task_o.stop()
    task_o.close()
except nidaqmx.DaqError as e:
    print(e)

    print('1 Channel N Lines 1 Sample Unsigned Integer Write: ')
    #task1.write(8)
    #print(task.write(8))

    print('1 Channel N Lines N Samples Unsigned Integer Write: ')
    #print(task1.write([1, 2, 4, 8], auto_start=True))