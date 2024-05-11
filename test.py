import pyvisa as visa
from array import array
import time
import datetime
import csv
import math
import struct
import sys
import os
import pandas as pd
import Config as conf
import FileInfo
import numpy as np
import sys

rm = visa.ResourceManager()                                                    # VISAリソースマネージャをインスタンス化
visa_list = rm.list_resources()                                                # 利用可能なVISAリソース(機器)のリストを取得
print(visa_list)                                                               # 機器リストを出力

FG_1 = None
FG_2 = None
Osc = None

# ファンクションジェネレータとオシロスコープのリソースをオープン
FG_1=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")                 # ノダさんのファンクションジェネレータ
FG_2=rm.open_resource("USB0::0x0D4A::0x000D::9122074::INSTR")                # 原田さんのファンクションジェネレータ
Osc = rm.open_resource("USB0::0x0957::0x1798::MY61410321::INSTR")              # Keysightオシロスコープ

if FG_1 is None:
    print("EPR Function Generator is not connected...")
    exit()
if FG_2 is None:
    print("SpinFlip Function Generator is not connected...")
    exit()
if Osc is None:
    print("Oscilloscope is not connected...")
    exit()

def InitialSetFG_EPR():
    # ファンクションジェネレータの初期設定
    FG_1.write(":SOURce:MODE Modulation") 
    FG_1.write(":SOURce:FUNCtion:SHAPe Sin")                                     # 関数をサイン波に設定
    FG_1.write(f":SOURce:FREQuency {conf.Freq_EPR}")
    FG_1.write(f":SOURce:VOLTage {conf.Voltage_EPR}")
    FG_1.write(f":SOURce:FM:Internal:Frequency {conf.ModulationFreq_EPR}")
    FG_1.write(f":SOURce:FM:deviation {conf.iDeltaFreq_EPR}")

def InitialSetOsc_EPR():
    # オシロスコープの初期設定
    Osc.write(":RUN")                                                            # フロントパネルのRunを押す
    Osc.write(":DISPlay:CLEar")                                                  # オシロの表示をリセット
    Osc.write(":TIMebase:RANGe %f" % (conf.OscWindowscale_EPR))                  # ウィンドウの水平方向のフルスケールを秒単位で設定
    Osc.write(":TIMebase:REFerence LEFT")                                        # 信号のディレイの基準点をLEFTにする
    Osc.write(":TIMebase:POSition %f" % (conf.OscDelayTime_EPR))                 # トリガーと基準点の時間間隔を設定

    # チャンネルのON/OFFとオフセットを設定
    Osc.write(":CHANnel1:DISPlay 1")
    Osc.write(":CHANnel2:DISPlay 1")
    Osc.write(":CHANnel3:DISPlay 1")
    Osc.write(":CHANnel4:DISPlay 0")  
    Osc.write(":CHANnel1:OFFSet 0 V")  
    Osc.write(":CHANnel2:OFFSet 0 V")  
    Osc.write(":CHANnel3:OFFSet 0 V")  
    Osc.write(":CHANnel4:OFFSet 0 V")  

    # トリガーの設定
    Osc.write(":MTESt:TRIGger:SOURce CHANnel%d" % (conf.OscChTrigger_EPR))       # トリガーとして使用するチャンネルを設定
    Osc.write(":TRIGger:EDGE:LEVel %f" % (conf.OscTriggerLevel_EPR))             # トリガーレベルを設定
    Osc.write(":TRIGger:SLOPe NEGative")                                         # トリガーの立ち下がりエッジを検出

    # データ取得の設定
    Osc.write(":ACQuire:TYPE Average")                                           # 平均化モードを使用
    Osc.write(":ACQuire:COUNt %d" % (conf.OscAverage_EPR))                       # 平均化数を設定
    Osc.write(":ACQuire:COMPlete 100")                                           # 取り込みの完了基準を100%に設定
    Osc.write(":WAVeform:FORMat BYTE")                                           # データ形式をバイト形式に設定
    Osc.write(":WAVeform:FORMat ASCII")
    Osc.write(":WAVeform:POINts %d" % (conf.OscDataPoint_EPR))                   # 波形のポイント数を設定
    Osc.write(":WAVeform:POINts:MODE MAXimum")                                   # 取得する波形ポイントの最大数を使用
    Osc.write(":STOP")                                                           # フロントパネルのStopを押す
    Osc.write(":RUN")                                                            # フロントパネルのRunを押す
    Osc.write(":TRIGger:SWEep Normal")                                           # トリガーモードをNormalに設定
    Osc.write(":DIGitize")                                                       # データ取得を開始

def InitialSetFG():
    FG_2.write(":SOURce:MODE BURSt")                                             # 発信モードをバーストに設定
    FG_2.write(":SOURce:FUNCtion:SHAPe USER")                                    # 関数を任意波形(user)に設定
    FG_2.write(":SOURce:BURSt:STATe 1")                                          # 発信モードの連続/バースト切り替え(0/1 or OFF/ON)
    FG_2.write(":SOURce:BURSt:MODE TRIGger")                                     # バーストモードのタイプをトリガーに変更
    FG_2.write(":SOURce:BURSt:NCYCles 1")                                        # マーク波数を設定
    FG_2.write(":SOURce:FREQuency %f" % (1/conf.ModulationTime))                 # 周波数の設定(バーストの信号の長さの設定)
    FG_2.write(":TRIGger:BURSt:SOURce EXTernal")                                 # 外部トリガー設定
    FG_2.write(":TRIGger:BURSt:SLOPe OFF")                                       # 外部トリガーの極性をOFFにしておくと、外来ノイズによる誤動作が避けられる(マニュアルP.106)
    FG_2.write(":SOURce:FUNCtion:USER %i" % conf.FGMemory)                       # メモリから任意波形読み込み
    FG_2.write(":SOURce:VOLTage %f" % conf.FGVoltage)                            # 波形の振幅を設定
    FG_2.write(":OUTPut:SYNC:BURSt:TYPE BSYNc")                                  # SYNC OUTの同期出力をバースト同期に設定
  
def InitialSetFG_WideRangeScan():
    FG_2.write(":SOURce:MODE SWEep")                                             # 発信モードをスイープに設定
    FG_2.write(":SOURce:FUNCtion:SHAPe SINusoid")                                # 関数を任意波形(user)に設定
    FG_2.write(":SOURce:SWEep:MODE GATed")                                       # ゲーテッド単発
    FG_2.write(":TRIGger:SWEep:SOURce EXTernal")                                 # 外部トリガー設定
    FG_2.write(":TRIGger:SWEep:SLOPe OFF")                                       # 外部トリガーの極性をOFFにしておくと、外来ノイズによる誤動作が避けられる
    FG_2.write(":SOURce:SWEep:TIME %f" % conf.ModulationTime)                    # スイープ時間設定
    FG_2.write(":SOURce:FREQuency:STARt %f" % conf.StartFreq)                    # 周波数開始値
    FG_2.write(":SOURce:FREQuency:STOP %f" % conf.StopFreq)                      # 周波数停止値
    FG_2.write(":SOURce:VOLTage %f" % conf.FGVoltage)                            # 波形の振幅を設定
    FG_2.write(":OUTPut:SYNC:SWEep:TYPE MARker")                                 # SYNC OUTの同期出力をマーカに設定

def InitialSetOsc():
    # ディスプレイの設定
    Osc.write(":RUN")                                                            # フロントパネルのRunを押す
    Osc.write(":DISPlay:CLEar")                                                  # オシロの表示をリセット   
    Osc.write(":TIMebase:RANGe %f" % (conf.ModulationTime*conf.NSpinFlip))       # ウィンドウの水平方向のフルスケール。秒単位で設定。（時間分割設定の10倍）  
    Osc.write(":TIMebase:REFerence CENTer")                                      # 信号のディレイの基準点をCENTerにする。
    Osc.write(":TIMebase:POSition %f" % (conf.ModulationTime*conf.NSpinFlip/2.)) # トリガーと基準点と時間間隔（DELayコマンドは廃止のため換えた）。
    
    # チャンネルの設定
    Osc.write(":CHANnel1:DISPlay 1")                                             # ChannelのON/OFFボタン (Monitor)
    Osc.write(":CHANnel2:DISPlay 1")                                             # ChannelのON/OFFボタン (Signal)
    Osc.write(":CHANnel3:DISPlay 1")                                             # ChannelのON/OFFボタン (Trigger)
    Osc.write(":CHANnel4:DISPlay 0")                                             # ChannelのON/OFFボタン (CH4はいつも使ってないのでOFFにしておく)  
    Osc.write(":CHANnel1:OFFSet 0 V")                                            # Channelのオフセット
    Osc.write(":CHANnel2:OFFSet 0 V")                                            # Channelのオフセット
    Osc.write(":CHANnel3:OFFSet 0 V")                                            # Channelのオフセット
    Osc.write(":CHANnel4:OFFSet 0 V")                                            # Channelのオフセット  
    
    # トリガーの設定
    Osc.write(":MTESt:TRIGger:SOURce CHANnel%d" % (conf.OscChTrigger))           # Trigger(FGのSync out)を入れるチャンネル  
    Osc.write(":TRIGger:EDGE:LEVel %f" % (conf.OscTriggerLevel))                 # トリガーレベル
    Osc.write(":TRIGger:SLOPe NEGative")                                         # トリガースロープを立ち下がりに設定  

    # データ取得モード ノーマル or 平均
    if (conf.OscMode == "N"):
      Osc.write(":ACQuire:TYPE Normal")                                          # Normal mode
    if (conf.OscMode == "A"):
      Osc.write(":ACQuire:TYPE Average")                                         # Average mode
      Osc.write(":ACQuire:COUNt %d" % (conf.OscAverage))                         # 波形の平均化数を設定。:MTESt:AVERage:COUNtコマンドは廃止のため換えた。

    # データ取得の設定
    Osc.write(":ACQuire:COMPlete 100")                                           # 取り込みの最小完了基準を指定。
    Osc.write(":WAVeform:FORMat BYTE")                                           # バイナリ形式で保存する。
    Osc.write(":WAVeform:POINts %d" % (conf.OscDataPoint))                       # 波形のポイント数を指定。
    Osc.write(":WAVeform:POINts:MODE MAXimum")                                   # 波形の最大ポイント数？  
    Osc.write(":STOP")                                                           # フロントパネルのStopを押す (これはなんのため？)
    Osc.write(":RUN")                                                            # フロントパネルのRunを押す (これはなんのため？)
    Osc.write(":TRIGger:SWEep Normal")                                           # トリガー信号がない場合、Autoでは非同期信号、Normalでは前の取得データがそのまま残る。(これは不要？)
    Osc.write(":DIGitize")                                                       # データ取得するコマンド。これがないと動かない。

def EPR():
    # EPR測定のための波形取得処理
    FG_1.write("OUTPut:STATe ON")                                                # ファンクションジェネレータの出力をON
    time.sleep(2)                                                                # アベレージのために少し待つ

    # オシロスコープからチャンネル2と3のデータを取得
    Osc.write(":WAVeform:SOURce CHANnel2")
    value = Osc.query(":WAVeform:DATA?")
    OscData_CH2=value.split(",")
    OscData_CH2[0]=OscData_CH2[0][10:]
    OscData_CH2=list(map(float, OscData_CH2))
    NPoint=len(OscData_CH2)

    Osc.write(":WAVeform:SOURce CHANnel3")
    value2 = Osc.query(":WAVeform:DATA?") 
    OscData_CH3=value2.split(",")
    OscData_CH3[0]=OscData_CH3[0][10:]
    OscData_CH3=list(map(float, OscData_CH3))

    TOrigin = float(Osc.query("WAVeform:XORigin?"))                              # 最初のデータ点の時間
    TReference = float(Osc.query("WAVeform:XREFerence?"))                        # 時間基準点
    TIncrement = float(Osc.query("WAVeform:XINCrement?"))                        # 時間間隔

    Time=[(i-TReference)*TIncrement+TOrigin for i in range(NPoint)]              # 時間点の較正

    FG_1.write("OUTPut:STATe OFF")                                               # ファンクションジェネレータの出力をOFF
    
    return OscData_CH2, OscData_CH3,Time, NPoint

def SpinFlip():
    # FGのoutputをON
    FG_2.write("OUTPut:STATe ON")

    # Send time of Trigger
    t = datetime.datetime.now()
    date_1 = str(t)[:-3]
    
    # ファンクションジェネレータのトリガーをON
    FG_2.write("*TRG")  

    # End time of Trigger
    t = datetime.datetime.now()
    date_2 = str(t)[:-3]

    # オシロch2の波形取得
    Osc.write(":WAVeform:SOURce CHANnel2")
    Oscdata = Osc.query_binary_values(":WAVeform:DATA?", datatype='B')
    
    # FGのoutputをOFF
    FG_2.write("OUTPut:STATe OFF")
    
    return Oscdata, date_1, date_2

def GetOscInformation():
    TOrigin = float(Osc.query("WAVeform:XORigin?"))                              # 最初のデータ点の X 軸値
    TReference = float(Osc.query("WAVeform:XREFerence?"))                        # 指定されているソース(signal=ch2)の時間基準点
    TIncrement = float(Osc.query("WAVeform:XINCrement?"))                        # データポイント間の時間差
    
    VOrigin = float(Osc.query("WAVeform:YORigin?"))                              # 縦軸の原点 (原点から正方向にずらしていたら負)
    VReference = float(Osc.query("WAVeform:YREFerence?"))                        # どこを指してるのかよくわからない
    VIncrement = float(Osc.query("WAVeform:YINCrement?"))                        # 1bitが何Vか
    
    return TOrigin, TReference, TIncrement, VOrigin, VReference, VIncrement

def DataOutputToBinaryFile(Oscdata, BinaryFileName, OscInformation):
    with open(BinaryFileName, mode='wb') as f:
        for iInfo in range(len(OscInformation)):
            f.write(struct.pack("f", OscInformation[iInfo]))
        for iData in Oscdata:
            f.write(struct.pack("B", iData))

def DataOutputToTextFile(OscData_CH2, OscData_CH3, Time, NPoint, TextFileName):
  # テキストファイルへのデータ出力
  with open(TextFileName,mode="a") as f:
    for i in range(NPoint):
      f.write("%f %f %f\n" %(Time[i], OscData_CH2[i], OscData_CH3[i]))

def DataOutputToParameterFile():    
    # パラメータファイルへの出力処理
    NowTime = datetime.datetime.now()                                            # 現在の日時を取得
    DataDictionary = dict(
        Time=[NowTime],
        TimeInterval=[conf.TimeInterval],
        Voltage=[conf.FGVoltage],
        Oscilloscope=[Osc],
        FreqRange=[conf.FreqRange]
    )
    df = pd.DataFrame(data=DataDictionary)                                       # データフレームの作成
  
  # パラメータファイルへの出力
    header = FileInfo.addHeader(conf.FileNameParameter)
    df.to_csv(conf.FileNameParameter, mode="a", index=False, header=header)

def ReadTextPeak(text):
    data = np.loadtxt(text, delimiter=" ", dtype=np.float64)
    sign_changes = np.where(np.diff(np.sign(data[:, 2])) < 0)[0]

    boundary = [data[0][0]]
    for i in sign_changes:
        boundary.append(data[i, 0])
    boundary.append(data[-1][0])

    peak = []
    peak2 = []
    for i in range(len(boundary) - 1):
        indices = np.where((data[:, 0] > boundary[i]) & (data[:, 0] < boundary[i + 1]))[0]
        peak.append(data[indices[np.argmin(data[indices, 1])], 0])
        peak2.append(data[indices[np.argmin(data[indices, 1])], 0] - i / conf.iDeltaFreq_EPR)
    return peak, peak2

def convertFreq(peaks):
    Freq = [2 * conf.ModulationFreq_EPR * conf.iDeltaFreq_EPR * peak + conf.Freq_EPR - conf.ModulationFreq_EPR for peak in peaks]
    return Freq

def convertPol(Freq1, Freq2, Std1, Std2):
    Delnu_2 = abs(Freq1 - Freq2)
    Delnu = Delnu_2 / 2  # Hz

    const = abs((3 * conf.h * (2 * conf.I + 1) * (2 * conf.I + 1)**2 * conf.h * conf.A_hfs) / (2 * conf.mu_0 * conf.mu_B * conf.g_s * conf.kapper_0 * conf.mu_129 * conf.num_129 * ((2 * conf.I + 1)**2 * conf.h * conf.A_hfs - 8 * conf.I * conf.mu_B * conf.g_s * conf.B_0)))
    Pol = Delnu * const
    Std = (Std1 + Std2) * const
    return Pol, Std

def writeResults(Pol, Std, peak_first, peak_second):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filepath = conf.FileNamePolarizarion
    with open(filepath, 'a') as f:
        f.write(f"Data Acquisition Time: {now}\n")
        f.write(f"Polarization: {Pol:.6f}\n")
        f.write(f"Standard Deviation of Polarization: {Std:.6f}\n")
        f.write(f"Peak Points Before Flip (s): {peak_first}\n")
        f.write(f"Peak Points After Flip (s): {peak_second}\n")
        f.write("--------------------------------------------------\n")

def main():
    text_filenames = []  # テキストファイル名を保存するリスト
    for i in range(2):
        # EPR
        FileNo = FileInfo.GetMaxFileNumber_text() + 1
        TextFileName = conf.DataPath + str(FileNo).zfill(4) + ".text"
        text_filenames.append(TextFileName)  # ファイル名をリストに追加
        print("Initialization of Oscilloscope for EPR")
        InitialSetOsc_EPR()
        print("Initialization of Function Generator for EPR ")
        InitialSetFG_EPR()

        OscData_CH2, OscData_CH3,Time, NPoint = EPR()
        print("EPR Get")

        OscInformation = GetOscInformation()
        print("TOrigin: {0}, TReference: {1}, TIncrement: {2}".format(OscInformation[0], OscInformation[1], OscInformation[2]))
        print("VOrigin: {0}, VReference: {1}, VIncrement: {2}".format(OscInformation[3], OscInformation[4], OscInformation[5]))

        t = datetime.datetime.now()
        date_3 = str(t)[:-3]
        f_log = open(conf.FileNameLog, 'a')
        date_line = "FILE WRITE START " + date_3 + '\n'
        f_log.write(date_line)
        f_log.close()

        d_today = datetime.datetime.now()
        str(d_today.strftime('%H%M'))

        DataOutputToTextFile(OscData_CH2, OscData_CH3, Time, NPoint, TextFileName)
        DataOutputToParameterFile()

        # Spin Flip
        FileNo = FileInfo.GetMaxFileNumber() + 1
        BinaryFileName = conf.DataPath + str(FileNo).zfill(4) + ".bin"
        print("Pulse Time : ", conf.ModulationTime, " Memory Number : ", conf.FGMemory)
  
        print("Initialization of Oscilloscope")
        InitialSetOsc()  
        print("Initialization of Function Generator ")
        if conf.OptWideRangeScan:
            InitialSetFG_WideRangeScan()
        else:
            InitialSetFG()

        print("Flip!")
        Oscdata, date_1, date_2 = SpinFlip()
  
        OscInformation = GetOscInformation()
        print("TOrigin: {0}, TReference: {1}, TIncrement: {2}".format(OscInformation[0], OscInformation[1], OscInformation[2]))
        print("VOrigin: {0}, VReference: {1}, VIncrement: {2}".format(OscInformation[3], OscInformation[4], OscInformation[5]))
  
        t = datetime.datetime.now()
        date_3 = str(t)[:-3]
        f_log = open(conf.FileNameLog, 'a')
  
        date_line = "TRG IN: "+date_1+' TRG END :' + \
        date_2+' FILE WRITE START '+date_3+'\n'
        f_log.write(date_line)
        f_log.close()
    
        d_today = datetime.datetime.now()
        str(d_today.strftime('%H%M'))
  
        DataOutputToBinaryFile(Oscdata, BinaryFileName, OscInformation)
        DataOutputToParameterFile()
    
    if len(text_filenames) >= 2:
        peak_first, peak2_first = ReadTextPeak(text_filenames[0])
        Freq_first = convertFreq(peak2_first)
    
        FreqAve_first = np.average(Freq_first)
        FreqStd_first = np.std(Freq_first)

        peak_second, peak2_second = ReadTextPeak(text_filenames[1])
        Freq_second = convertFreq(peak2_second)
    
        FreqAve_second = np.average(Freq_second)
        FreqStd_second = np.std(Freq_second)

        Pol, Std = convertPol(FreqAve_first, FreqAve_second, FreqStd_first, FreqStd_second)

        writeResults(Pol, Std, peak_first, peak_second)
        

if __name__ == "__main__": 
    os.makedirs(conf.DataPath, exist_ok=True)
    main()  