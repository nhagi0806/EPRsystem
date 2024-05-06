import csv
import os
import struct
import time
import pyvisa as visa
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
        Osc.timeout = conf2.OscTimeout
    elif 'NF Corporation' in out:
        FG = dev

if not FG or not Osc:
    print("Necessary devices are not connected.")
    sys.exit()

def InitialSetFG():
    FG.write(f":SOURce:FREQuency {conf2.iFreq}")
    FG.write(f":SOURce:VOLTage {conf2.Voltage}")
    FG.write(":SOURce:MODulation:FM:STATe ON")
    FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {conf2.ModulationFreq}")
    FG.write(f":SOURce:MODulation:FM:DEViation {conf2.iDeltaFreq}")
    FG.write(":OUTPut ON")

def InitialSetOsc():
    Osc.write(":CHANnel1:DISPlay ON")
    Osc.write(":CHANnel2:DISPlay ON")
    Osc.write(f":TIMebase:RANGe {1/conf2.ModulationFreq * conf2.N_wave}")
    Osc.write(":TRIGger:LEVel 0.05")
    Osc.write(":TRIGger:EDGE:SOURce CHANnel1")
    Osc.write(":ACQuire:TYPE AVERage")
    Osc.write(f":ACQuire:COUNt {conf2.NAverage}")

# ファイル番号を追跡する
file_number = 1

def get_next_filename(base_filename, file_number, file_extension):
    return f"{base_filename}_{file_number}.{file_extension}"

def get_next_filepaths(base_filename, file_number, file_extension1, file_extension2):
    filename1 = get_next_filename(base_filename, file_number, file_extension1)
    filename2 = get_next_filename(base_filename, file_number, file_extension2)
    return (
        os.path.join(conf2.EPRsignal_path, filename1),
        os.path.join(conf2.EPRsignal_path, filename2)
    )

def GetEPRData(Osc):
    global file_number  # グローバル変数として宣言
    Osc.write(":WAVeform:POINts:MODE RAW")
    Osc.write(":WAVeform:FORMat ASCII")
    TOrigin, TIncrement = float(Osc.query("WAVeform:XORigin?")), float(Osc.query("WAVeform:XINCrement?"))
    C1 = list(map(float, Osc.query(":WAVeform:SOURce CHANnel1;DATA?").split(',')))
    C2 = list(map(float, Osc.query(":WAVeform:SOURce CHANnel2;DATA?").split(',')))

    save_path_csv, save_path_bin = get_next_filepaths("EPR_data", file_number, "csv", "bin")

    with open(save_path_csv, "a", newline='') as file_csv:
        writer_csv = csv.writer(file_csv)
        with open(save_path_bin, "ab") as file_bin:
            for i, (v1, v2) in enumerate(zip(C1, C2)):
                time_val = TOrigin + i * TIncrement
                writer_csv.writerow([time_val, v1, v2])
                file_bin.write(struct.pack('d', time_val))
                file_bin.write(struct.pack('f', v1))
                file_bin.write(struct.pack('f', v2))

    print(f"Data saved to {save_path_csv} and {save_path_bin}")

    file_number += 1  # ファイル番号のインクリメント

def TurnOffFG():
    FG.write(":OUTPut OFF")

def main():
    InitialSetFG()
    InitialSetOsc()
    time.sleep(5)
    GetEPRData(Osc)
    TurnOffFG()

if __name__ == "__main__":
    main()
