import csv  # CSVファイル操作のためのモジュールをインポート
import os  # OSモジュールをインポート、ファイルパスの操作に使用
import sys  # システム固有のパラメータや関数にアクセスするためのモジュール
import struct  # バイナリデータ操作のためのモジュール
import pyvisa as visa  # PyVISAライブラリをインポート、計測機器との通信に使用
import time  # 時間操作のためのモジュール

import Config2 as conf2  # 設定値を含む別のファイルをインポート

rm = visa.ResourceManager()  # Visaリソースマネージャを作成
visa_list = rm.list_resources()  # 接続されているVISAデバイスのリストを取得
print(visa_list)  # デバイスリストを表示

FG = None  # 関数ジェネレータの初期値設定
Osc = None  # オシロスコープの初期値設定

# 接続されているデバイスを走査し、対象のデバイスを特定
for dev_name in visa_list:
    dev = rm.open_resource(dev_name)  # デバイスをオープン
    out = dev.query('*IDN?')  # デバイス識別情報をクエリ
    if 'KEYSIGHT' in out or 'AGILENT' in out:  # KeysightまたはAgilentのデバイスの場合
        Osc = dev  # オシロスコープとして設定
        Osc.timeout = conf2.OscTimeout  # タイムアウトを設定
    elif 'NF Corporation' in out:  # NF Corporationのデバイスの場合
        FG = dev  # 関数ジェネレータとして設定

# 必要なデバイスが接続されていない場合、プログラムを終了
if not FG or not Osc:
    print("Necessary devices are not connected.")
    sys.exit()

def InitialSetFG():
    # 関数ジェネレータの初期設定
    FG.write(f":SOURce:FREQuency {conf2.iFreq}")  # 周波数を設定
    FG.write(f":SOURce:VOLTage {conf2.Voltage}")  # 電圧を設定
    FG.write(":SOURce:MODulation:FM:STATe ON")  # 周波数変調をON
    FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {conf2.ModulationFreq}")  # 変調周波数を設定
    FG.write(f":SOURce:MODulation:FM:DEViation {conf2.iDeltaFreq}")  # 変調の偏差を設定
    FG.write(":OUTPut ON")  # 出力をON

def InitialSetOsc():
    # オシロスコープの初期設定
    Osc.write(":CHANnel1:DISPlay ON")  # チャンネル1を表示
    Osc.write(":CHANnel2:DISPlay ON")  # チャンネル2を表示
    Osc.write(f":TIMebase:RANGe {1/conf2.ModulationFreq * conf2.N_wave}")  # タイムベースの範囲を設定
    Osc.write(":TRIGger:LEVel 0.05")  # トリガーレベルを設定
    Osc.write(":TRIGger:EDGE:SOURce CHANnel1")  # トリガーソースをチャンネル1に設定
    Osc.write(":ACQuire:TYPE AVERage")  # 取得タイプを平均に設定
    Osc.write(f":ACQuire:COUNt {conf2.NAverage}")  # 平均回数を設定

# ファイル番号を追跡する
file_number = 1

def get_next_filename(base_filename, file_number, file_extension):
    # ファイル名に番号を付けて返す関数
    return f"{base_filename}_{file_number}.{file_extension}"

def get_next_filepath(base_filename, file_number, file_extension):
    # ファイルパスを生成して返す関数
    filename = get_next_filename(base_filename, file_number, file_extension)
    return os.path.join(conf2.EPRsignal_path, filename)

def get_next_filepaths(base_filename, file_number, file_extension1, file_extension2):
    # バイナリファイルとCSVファイルのファイルパスを生成して返す関数
    filename1 = get_next_filename(base_filename, file_number, file_extension1)
    filename2 = get_next_filename(base_filename, file_number, file_extension2)
    return (
        os.path.join(conf2.EPRsignal_path, filename1),
        os.path.join(conf2.EPRsignal_path, filename2)
    )

def GetEPRData(Osc):
    # EPRデータの取得を実行する関数
    Osc.write(":WAVeform:POINts:MODE RAW")  
    Osc.write(":WAVeform:FORMat ASCII")  
    TOrigin, TIncrement = float(Osc.query("WAVeform:XORigin?")), float(Osc.query("WAVeform:XINCrement?"))  
    C1 = list(map(float, Osc.query(":WAVeform:SOURce CHANnel1;DATA?").split(',')))  
    C2 = list(map(float, Osc.query(":WAVeform:SOURce CHANnel2;DATA?").split(',')))  

    # ファイルパスの取得
    save_path_csv, save_path_bin = get_next_filepaths("EPR_data", file_number, "csv", "bin")

    # CSVとバイナリファイルへのデータの保存
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

    # ファイル番号のインクリメント
    global file_number
    file_number += 1


def TurnOffFG():
    FG.write(":OUTPut OFF")  # 関数ジェネレータの出力をオフにする


def main():
    InitialSetFG()  # 関数ジェネレータの初期設定を実行
    InitialSetOsc()  # オシロスコープの初期設定を実行
    time.sleep(5)  # 5秒間待つ
    GetEPRData()  # EPRデータの取得を実行
    TurnOffFG()  # 関数ジェネレータの出力をオフにする

if __name__ == "__main__":
    main()
