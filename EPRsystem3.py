import pyvisa as visa
import sys
import os

import Config2 as conf2

rm = visa.ResourceManager()
visa_list = rm.list_resources()
print(visa_list)

FG = None
Osc = None

for dev_name in visa_list:
    dev = rm.open_resource(dev_name)
    out = dev.query('*IDN?')
    if 'KEYSIGHT' in out or 'AGILENT' in out:
        Osc = dev
        Osc.timeout = conf.OscTimeout
    elif 'NF Corporation' in out:
        FG = dev

if not FG or not Osc:
    print("Necessary devices are not connected.")
    sys.exit()

def InitialSetFG():
    FG.write(f":SOURce:FREQuency {conf.iFreq}")
    FG.write(f":SOURce:VOLTage {conf.Voltage}")
    FG.write(":SOURce:MODulation:FM:STATe ON")
    FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {conf.ModulationFreq}")
    FG.write(f":SOURce:MODulation:FM:DEViation {conf.iDeltaFreq}")
    FG.write(":OUTPut ON")

def InitialSetOsc():
    Osc.write(":CHANnel1:DISPlay ON")
    Osc.write(":CHANnel2:DISPlay ON")
    Osc.write(f":TIMebase:RANGe {1/conf.ModulationFreq * conf.N_wave}")
    Osc.write(":TRIGger:LEVel 0.05")
    Osc.write(":TRIGger:EDGE:SOURce CHANnel1")
    Osc.write(":ACQuire:TYPE AVERage")
    Osc.write(f":ACQuire:COUNt {conf.NAverage}")

def GetEPRData():
    Osc.write(":WAVeform:POINts:MODE RAW")
    Osc.write(":WAVeform:FORMat ASCII")
    TOrigin, TIncrement = float(Osc.query("WAVeform:XORigin?")), float(Osc.query("WAVeform:XINCrement?"))
    C1 = list(map(float, Osc.query(":WAVeform:SOURce CHANnel1;DATA?").split(',')))
    C2 = list(map(float, Osc.query(":WAVeform:SOURce CHANnel2;DATA?").split(',')))

    save_path = os.path.join(conf.EPRsignal_path, "EPR_data_combined.txt")
    with open(save_path, "a") as f:
        for i, (v1, v2) in enumerate(zip(C1, C2)):
            time = TOrigin + i * TIncrement
            f.write(f"{time} {v1} {v2}\n")

    print(f"Data saved to {save_path}")

def main():
    InitialSetFG()
    InitialSetOsc()
    GetEPRData()

if __name__ == "__main__":
    main()
