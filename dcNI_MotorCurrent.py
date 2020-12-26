import nidaqmx
print("Hallo")
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Motorcurrent/ai0")
    data= task.read()
    print(str(data)+"\n")
print("End Data ="+ str(data))