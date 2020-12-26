import nidaqmx
from nidaqmx.constants import (LineGrouping)
import pprint
import time

from nidaqmx.constants import (
    LineGrouping)

pp = pprint.PrettyPrinter(indent=4)

task_di= nidaqmx.Task()
task_di.di_channels.add_di_chan('Lightbarrier1/port0/line0',
                                 line_grouping=LineGrouping.CHAN_PER_LINE)
while True:
    print('1 Channel 1 Sample Read: ')
    data = task_di.read()
    pp.pprint(data)
    time.sleep(0.3)


task_di.stop()
task_di.close()