import math
import datetime
import os
import Const as const
import numpy as np
import pandas as pd

# start time
const.StartTime = datetime.datetime.now()
####################################################

# AFPNMR
# Path name
#DataDirectryName = "./test/"
#DataDirectryName = "/Data/AFPNMR/2023/1016/RoomA_OhtamaCoil2_KARIGANE_BeforeInstallation/"
DataDirectryName = "/Data/AFPNMR/2024/0418/RoomA_BL18Onbeam_natXe3atm_Test/"

HomePath         = os.path.expanduser("~")
#DataPath         = HomePath + "/NMRProgram/AFPNMR_FS/" + DataDirectryName
#DataPath         = HomePath + "/research/SpinFilter/AFPNMR_FS/" + DataDirectryName
DataPath         = HomePath + "/Research/" + DataDirectryName
GoogleDrivePath  = HomePath + "/マイドライブ/" + DataDirectryName

# File name
FileNameLog          = DataPath + "Log.txt"
FileNameParameter    = DataPath + "Parameter.csv"
FileNamePolarizarion = DataPath + "Polarizarion.text"

TimeInterval         = 3600   # [sec]

# Option
OptOverWrite         = 0       # if Opt=1, start file number is forcibly to 1
OptOnlyLockin        = 0       # Option for only lockin    (Will be used for phase tuning)
OptOnlySpinFlip      = 0       # Option for only spin flip (Will be used at beamline experiment)
OptCopyToGoogleDrive = 1       # Option for backup to Google Drive
OptBuildRelax        = "R"     # Option for measurement type (Buildup = "B" or Relaxation = "R")
OptWideRangeScan     = 1       # Option for frequency scan
OptCurrentScan       = 0       # Option for Current scan

####################################################
# SpinFlip
#-------------------
# Memory info of FG
MemorySet       = [[0, 0], [1, 1], [0.2, 2], [0.1, 3], [0.05, 4], [0.02, 5], [0.1, 6]]
Memory          = MemorySet[2]   # Memory info to be used
ModulationTime  = 1              # Modulation frequency [Hz] -> reciprocal [sec]
NSpinFlip       = 1              # Not used
FGMemory        = Memory[1]      # Memory number
FGVoltage       = 4              # Output voltage [V], SmallCoil, NOVACoil
#-------------------
# Memory info of Osc
OscMode         = "N"            # Normal or Average
OscAverage      = 64             # Number of times of average
OscDataPoint    = 2e5            # Data points {100 | 250 | 500 | 1000 | 2000 | 5000 | 10000 | 20000 | 50000 | 100000 | 200000 | 500000 | 1000000}
OscTimeout      = 2000           # Timeout time [ms]
OscTriggerLevel = 1              # Trigger level [V]
OscChTrigger    = 3              # Osc channel for the sync out of the function generator

#------------------
# Memory info of FG (Wide range scan mode)
StartFreq       = 1e3
StopFreq        = 60e3

#####################################################
# Lockin
FitRange  = [46e3, 54e3]
NMean     = 1000
Phase      = math.pi*(1.77)
FreqRange = [40e3, 60e3]

GyromagneticRatioHe = 2.038e8 # value of GyromagneticRatio of He-3 = −203.789 (10^6 rad s^-1 T^-1)
FunctionBreitWigner = "[0]/sqrt(pow([1]/(2*2*{0})*{1}, 2) + pow([2]-x, 2))".format(math.pi, GyromagneticRatioHe)
FunctionBackground  = "[0]+[1]*x+[2]*x*x+[3]*x*x*x" 
InitialValueBritWignerBGX = [-10, 2e-5, (FitRange[0]+FitRange[1])*0.5,
                             -1e-1, 1e-5, 1e-10, 1e-14]
InitialValueBritWignerBGY = [-2, 2e-5, (FitRange[0]+FitRange[1])*0.5,
                             1e-3, 1e-5, 1e-5, 1e-5]
ParameterLimitBritWignerBG = [[-1e2, 1e2], [0, 100e-6], [FitRange[0], FitRange[1]],
                              [-1, 1], [-1e-2, 1e-2], [-1e-8, 1e-8], [-1e-10, 1e-10]]


#####################################################
# DrawGraph
FunctionBuild = "[0]*(1-exp(-x/[1]))*exp(-5.52/3600*x/76)"
InitialValueBuild   = [10e-3, 10]
ParameterLimitBuild = [[0, 100000], [0, 100]]

FunctionRelaxation = "[0]*exp(-x/[1])*exp(-5.52/3600*x/76)"
InitialValueRelax   = [50e-3, 150]
ParameterLimitRelax = [[0, 1], [0, 500]]

#EPR
Freq_EPR = 7500000
Voltage_EPR=20
ModulationFreq_EPR=1000000
iDeltaFreq_EPR=1503

#OscWindowscale_EPR = 1
OscWindowscale_EPR = 1e-3
OscDelayTime_EPR = 0
OscTriggerLevel_EPR = 1              # Trigger level [V]
OscChTrigger_EPR    = 3              # Osc channel for the sync out of the function generator
OscAverage_EPR      = 4096             # Number of times of average
OscDataPoint_EPR    = 1000            # Data points {100 | 250 | 500 | 1000 | 2000 | 5000 | 10000 | 20000 | 50000 | 100000 | 200000 | 500000 | 1000000}


A_hfs = 1.011911 * 10**9  # Hz
I = 5 / 2
g_s = 2.002331
mu_B = 9.927401 * 10**-24  # J/T
mu_0 = 4 * np.pi * 10**-7
mu_129 = -3.929344 * 10**-27  # N/A**2
kapper_0 = 518
B_0 = 1.6133 * 10**-3  # T
h = 6.62607015 * 10**-34
num_129 = 7.32 * 10**25