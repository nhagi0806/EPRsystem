import csv
import os
import struct
import time
import pyvisa as visa
import Config2 as conf2
import Config as conf
import datetime
import pandas as pd
import FileInfo

rm = visa.ResourceManager()
visa_list = rm.list_resources()
print(visa_list)

FG = None
Osc = None

FG = rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")  # Function Generator
Osc = rm.open_resource("USB0::0x0957::0x1798::MY61410321::INSTR")  # Oscilloscope

def InitialSetFG():
    FG.write(":SOURce:MODE Modulation")
    FG.write(":SOURce:FUNCtion:SHAPe Sin")
    FG.write(f":SOURce:FREQuency {conf2.iFreq}")
    FG.write(f":SOURce:VOLTage {conf2.Voltage}")
    FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {conf2.ModulationFreq}")
    FG.write(f":SOURce:MODulation:FM:DEViation {conf2.iDeltaFreq}")

def InitialSetOsc():
    Osc.write(":RUN")
    Osc.write(":DISPlay:CLEar")
    Osc.write(":TIMebase:RANGe %f" % (conf.ModulationTime * conf.NSpinFlip))
    Osc.write(":TIMebase:REFerence CENTer")
    Osc.write(":TIMebase:POSition %f" % (conf.ModulationTime * conf.NSpinFlip / 2.))
    Osc.write(":CHANnel1:DISPlay 1")
    Osc.write(":CHANnel2:DISPlay 1")
    Osc.write(":CHANnel3:DISPlay 1")
    Osc.write(":CHANnel4:DISPlay 0")
    Osc.write(":CHANnel1:OFFSet 0 V")
    Osc.write(":CHANnel2:OFFSet 0 V")
    Osc.write(":CHANnel3:OFFSet 0 V")
    Osc.write(":CHANnel4:OFFSet 0 V")
    Osc.write(":MTESt:TRIGger:SOURce CHANnel%d" % (conf.OscChTrigger))
    Osc.write(":TRIGger:EDGE:LEVel %f" % (conf.OscTriggerLevel))
    Osc.write(":TRIGger:SLOPe NEGative")
    Osc.write(":ACQuire:TYPE Average")
    Osc.write(":ACQuire:COUNt %d" % (conf.OscAverage))
    Osc.write(":ACQuire:COMPlete 100")
    Osc.write(":WAVeform:FORMat BYTE")
    Osc.write(":WAVeform:POINts %d" % (conf.OscDataPoint))
    Osc.write(":WAVeform:POINts:MODE MAXimum")
    Osc.write(":STOP")
    Osc.write(":RUN")
    Osc.write(":TRIGger:SWEep Normal")
    Osc.write(":DIGitize")

def EPR():
    FG.write("OUTPut:STATe ON")
    time.sleep(5)
    Osc.write(":WAVeform:SOURce CHANnel2")
    Osc.write(":WAVeform:FORMat ASCII")
    file_path = "/usb/myData_CH2.csv"
    Osc.write(f":DISK:SAVE:WAVeform CHANnel2,'{file_path}'")
    data = Osc.query(f":DISK:LOAD? '{file_path}'")
    with open("myData_CH2.csv", "w") as file:
        file.write(data)
    Osc.write(":WAVeform:SOURce CHANnel3")
    file_path_ch3 = "/usb/myData_CH3.csv"
    Osc.write(f":DISK:SAVE:WAVeform CHANnel3,'{file_path_ch3}'")
    data_ch3 = Osc.query(f":DISK:LOAD? '{file_path_ch3}'")
    with open("myData_CH3.csv", "w") as file:
        file.write(data_ch3)
    FG.write("OUTPut:STATe OFF")

def GetOscInformation():
    TOrigin = float(Osc.query("WAVeform:XORigin?"))
    TReference = float(Osc.query("WAVeform:XREFerence?"))
    TIncrement = float(Osc.query("WAVeform:XINCrement?"))
    VOrigin = float(Osc.query("WAVeform:YORigin?"))
    VReference = float(Osc.query("WAVeform:YREFerence?"))
    VIncrement = float(Osc.query("WAVeform:YINCrement?"))
    return TOrigin, TReference, TIncrement, VOrigin, VReference, VIncrement

def DataOutputToParameterFile():
    NowTime = datetime.datetime.now()
    DataDictionary = {
        "Time": [NowTime],
        "TimeInterval": [conf.TimeInterval],
        "Voltage": [conf.FGVoltage],
        "FunctionGenerator": [FG],
        "Oscilloscope": [Osc],
        "FreqRange": [conf.FreqRange]
    }
    df = pd.DataFrame(data=DataDictionary)
    header = FileInfo.addHeader(conf.FileNameParameter)
    df.to_csv(conf.FileNameParameter, mode="a", index=False, header=header)

def main(BinaryFileName):
    print("Pulse Time : ", conf.ModulationTime, " Memory Number : ", conf.FGMemory)
    InitialSetOsc()
    InitialSetFG()

    t = datetime.datetime.now()
    date_3 = str(t)[:-3]
    f_log = open(conf.FileNameLog, 'a')
    date_line = "FILE WRITE START " + date_3 + '\n'
    f_log.write(date_line)
    f_log.close()

    EPR()

    OscInformation = GetOscInformation()
    print("TOrigin: {0}, TReference: {1}, TIncrement: {2}".format(OscInformation[0], OscInformation[1], OscInformation[2]))
    print("VOrigin: {0}, VReference: {1}, VIncrement: {2}".format(OscInformation[3], OscInformation[4], OscInformation[5]))

    DataOutputToParameterFile()

    d_today = datetime.datetime.now()
    time_str = str(d_today.strftime('%H%M'))
    print(f"Current time: {time_str}")

if __name__ == "__main__":
    os.makedirs(conf.DataPath, exist_ok=True)
    FileNo = FileInfo.GetMaxFileNumber() + 1
    BinaryFileName = conf.DataPath + str(FileNo).zfill(4) + ".bin"
    main(BinaryFileName)
