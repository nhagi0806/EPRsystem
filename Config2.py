import math
import datetime
import os
import Const as const

# start time
const.StartTime = datetime.datetime.now()

# Path name
DataDirectryName = "/Data/AFPNMR/2024/0418/RoomA_BL18Onbeam_natXe3atm_Test/"

HomePath         = os.path.expanduser("~")
DataPath         = HomePath + "/Research/" + DataDirectryName

# File name
FileNameLog          = DataPath + "Log.txt"
FileNameParameter    = DataPath + "Parameter.csv"

iFreq = 7500000
Voltage=20
ModulationFreq=1000000
iDeltaFreq=1503

OscWindowscale = 1
#OscWindowscale = 1e-3
OscDelayTime = 0
OscTriggerLevel = 1              # Trigger level [V]
OscChTrigger    = 3              # Osc channel for the sync out of the function generator
OscAverage      = 64             # Number of times of average
OscDataPoint    = 2e5            # Data points {100 | 250 | 500 | 1000 | 2000 | 5000 | 10000 | 20000 | 50000 | 100000 | 200000 | 500000 | 1000000}

TimeInterval         = 1800   # [sec]

FGVoltage       = 4              # Output voltage [V], SmallCoil, NOVACoil
FreqRange = [40e3, 60e3]



