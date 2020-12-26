import nidaqmx.system
import nidaqmx
system = nidaqmx.system.System.local()
system.driver_version
#DriverVersion(major_version=16L, minor_version=0L, update_version=0L)
for device in system.devices:
    print(device)
device = system.devices['Motorcurrent']
print(str(device == nidaqmx.system.Device('Motorcurrent')))
phys_chan = device.ai_physical_chans['ai0']
print(str(phys_chan == nidaqmx.system.PhysicalChannel('Motorcurrent/ai0')))
print(phys_chan.ai_term_cfgs)

with nidaqmx.Task() as task:
    ai_channel = task.ai_channels.add_ai_voltage_chan("Motorcurrent/ai0", terminal_config = nidaqmx.constants.TerminalConfiguration.RSE)
print(ai_channel.ai_term_cfgs)

print("Ende")