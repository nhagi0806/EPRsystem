import csv
import os
import struct
import time
import pyvisa as visa
import Config as conf
import datetime
import pandas as pd
import FileInfo

rm = visa.ResourceManager()                                                    # VISAリソースマネージャをインスタンス化
visa_list = rm.list_resources()                                                # 利用可能なVISAリソース(機器)のリストを取得
print(visa_list)                                                               # 機器リストを出力

FG = None                                                                      # ファンクションジェネレータのための変数を初期化
Osc = None                                                                     # オシロスコープのための変数を初期化

# ファンクションジェネレータとオシロスコープのリソースをオープン
FG=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")                    # ノダさんのファンクションジェネレータ
Osc = rm.open_resource("USB0::0x0957::0x1798::MY61410321::INSTR")              # Keysightオシロスコープ

def InitialSetFG():
  # ファンクションジェネレータの初期設定
  FG.write(":SOURce:MODE Modulation") 
  FG.write(":SOURce:FUNCtion:SHAPe Sin")                                       # 関数をサイン波に設定
  FG.write(f":SOURce:FREQuency {conf.Freq_EPR}")
  FG.write(f":SOURce:VOLTage {conf.Voltage_EPR}")
  FG.write(f":SOURce:FM:Internal:Frequency {conf.ModulationFreq_EPR}")
  FG.write(f":SOURce:FM:deviation {conf.iDeltaFreq_EPR}")

def InitialSetOsc():
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
  Osc.write(":WAVeform:POINts %d" % (conf.OscDataPoint_EPR))                   # 波形のポイント数を設定
  Osc.write(":WAVeform:POINts:MODE MAXimum")                                   # 取得する波形ポイントの最大数を使用
  Osc.write(":STOP")                                                           # フロントパネルのStopを押す
  Osc.write(":RUN")                                                            # フロントパネルのRunを押す
  Osc.write(":TRIGger:SWEep Normal")                                           # トリガーモードをNormalに設定
  Osc.write(":DIGitize")                                                       # データ取得を開始


def EPR():
  # EPR測定のための波形取得処理
  FG.write("OUTPut:STATe ON")                                                  # ファンクションジェネレータの出力をON
  time.sleep(2)                                                                # アベレージのために少し待つ

  # オシロスコープからチャンネル2と3のデータを取得
  Osc.write(":WAVeform:SOURce CHANnel2")
  OscData_CH2 = Osc.query_binary_values(":WAVeform:DATA?", datatype='B')    
  Osc.write(":WAVeform:SOURce CHANnel3")
  OscData_CH3 = Osc.query_binary_values(":WAVeform:DATA?", datatype='B')    

  FG.write("OUTPut:STATe OFF")                                                 # ファンクションジェネレータの出力をOFF
  
  return OscData_CH2, OscData_CH3

def GetOscInformation():
  # オシロスコープからのデータに関する情報を取得
  TOrigin = float(Osc.query("WAVeform:XORigin?"))                              # 最初のデータ点の時間
  TReference = float(Osc.query("WAVeform:XREFerence?"))                        # 時間基準点
  TIncrement = float(Osc.query("WAVeform:XINCrement?"))                        # 時間間隔
  VOrigin = float(Osc.query("WAVeform:YORigin?"))                              # 縦軸の原点
  VReference = float(Osc.query("WAVeform:YREFerence?"))                        # 縦軸の参照点
  VIncrement = float(Osc.query("WAVeform:YINCrement?"))                        # 縦軸のインクリメント
  
  return TOrigin, TReference, TIncrement, VOrigin, VReference, VIncrement

def DataOutputToBinaryFile(OscData_CH2, OscData_CH3, BinaryFileName, OscInformation):
  # バイナリファイルへのデータ出力
  with open(BinaryFileName, mode='wb') as f:
    # オシロスコープ情報の書き込み
    for iInfo in range(len(OscInformation)):
      f.write(struct.pack("f", iInfo))      
    # チャンネル2と3のデータをバイナリ形式で書き込み
    for iData2 in OscData_CH2:
      f.write(struct.pack("B", iData2))
    for iData3 in OscData_CH3:
      f.write(struct.pack("B", iData3))

def DataOutputToParameterFile():
  # パラメータファイルへの出力処理
  NowTime = datetime.datetime.now()                                            # 現在の日時を取得
  DataDictionary = dict(
    Time=[NowTime],
    TimeInterval=[conf.TimeInterval],
    Voltage=[conf.FGVoltage],
    FunctionGenerator=[FG],
    Oscilloscope=[Osc],
    FreqRange=[conf.FreqRange]
  )
  df = pd.DataFrame(data=DataDictionary)                                       # データフレームの作成
  
  # パラメータファイルへの出力
  header = FileInfo.addHeader(conf.FileNameParameter)
  df.to_csv(conf.FileNameParameter, mode="a", index=False, header=header)

def main(BinaryFileName):
  print("Pulse Time : ", conf.ModulationTime, " Memory Number : ", conf.FGMemory)
  print("Initialization of Oscilloscope")
  InitialSetOsc()
  print("Initialization of Function Generator ")
  InitialSetFG()

  OscData_CH2, OscData_CH3 = EPR()
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

  DataOutputToBinaryFile(OscData_CH2, OscData_CH3, BinaryFileName, OscInformation)
  DataOutputToParameterFile()

if __name__ == "__main__":
  # スクリプトが直接実行された場合の処理
  os.makedirs(conf.DataPath, exist_ok=True)                                    # データ保存ディレクトリを作成（存在しない場合）
  FileNo = FileInfo.GetMaxFileNumber() + 1                                     # 新しいファイル番号を取得
  BinaryFileName = conf.DataPath + str(FileNo).zfill(4) + ".bin"               # 新しいバイナリファイル名を生成
  main(BinaryFileName)                                                         # メイン関数を実行

