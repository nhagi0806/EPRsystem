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
        Osc.timeout = conf.OscTimeout  # タイムアウトを設定
    elif 'NF Corporation' in out:  # NF Corporationのデバイスの場合
        FG = dev  # 関数ジェネレータとして設定

# 必要なデバイスが接続されていない場合、プログラムを終了
if not FG or not Osc:
    print("Necessary devices are not connected.")
    sys.exit()

def InitialSetFG():
    # 関数ジェネレータの初期設定
    FG.write(f":SOURce:FREQuency {conf.iFreq}")  # 周波数を設定
    FG.write(f":SOURce:VOLTage {conf.Voltage}")  # 電圧を設定
    FG.write(":SOURce:MODulation:FM:STATe ON")  # 周波数変調をON
    FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {conf.ModulationFreq}")  # 変調周波数を設定
    FG.write(f":SOURce:MODulation:FM:DEViation {conf.iDeltaFreq}")  # 変調の偏差を設定
    FG.write(":OUTPut ON")  # 出力をON

def InitialSetOsc():
    # オシロスコープの初期設定
    Osc.write(":CHANnel1:DISPlay ON")  # チャンネル1を表示
    Osc.write(":CHANnel2:DISPlay ON")  # チャンネル2を表示
    Osc.write(f":TIMebase:RANGe {1/conf.ModulationFreq * conf.N_wave}")  # タイムベースの範囲を設定
    Osc.write(":TRIGger:LEVel 0.05")  # トリガーレベルを設定
    Osc.write(":TRIGger:EDGE:SOURce CHANnel1")  # トリガーソースをチャンネル1に設定
    Osc.write(":ACQuire:TYPE AVERage")  # 取得タイプを平均に設定
    Osc.write(f":ACQuire:COUNt {conf.NAverage}")  # 平均回数を設定

def GetEPRData():
    # EPRデータを取得
    Osc.write(":WAVeform:POINts:MODE RAW")  # データポイントのモードをRAWに設定
    Osc.write(":WAVeform:FORMat ASCII")  # データ形式をASCIIに設定
    TOrigin, TIncrement = float(Osc.query("WAVeform:XORigin?")), float(Osc.query("WAVeform:XINCrement?"))  # 時間の原点と増分を取得
    C1 = list(map(float, Osc.query(":WAVeform:SOURce CHANnel1;DATA?").split(',')))  # チャンネル1のデータを取得
    C2 = list(map(float, Osc.query(":WAVeform:SOURce CHANnel2;DATA?").split(',')))  # チャンネル2のデータを取得

    save_path_csv = os.path.join(conf.EPRsignal_path, "EPR_data.csv")  # CSVファイルの保存パスを設定
    save_path_bin = os.path.join(conf.EPRsignal_path, "EPR_data.bin")  # バイナリファイルの保存パスを設定

    # データをCSVとバイナリファイルに保存
    with open(save_path_csv, "a", newline='') as file:
        writer = csv.writer(file)
        with open(save_path_bin, "ab") as bin_file:
            for i, (v1, v2) in enumerate(zip(C1, C2)):
                time = TOrigin + i * TIncrement
                writer.writerow([time, v1, v2])
                bin_file.write(struct.pack('d', time))
                bin_file.write(struct.pack('f', v1))
                bin_file.write(struct.pack('f', v2))

    print(f"Data saved to {save_path_csv} and {save_path_bin}")  # 保存完了のメッセージを表示

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
