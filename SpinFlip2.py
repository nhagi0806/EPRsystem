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

rm = visa.ResourceManager()
visa_list = rm.list_resources()
print(visa_list)

FG = None
Osc = None

for index, dev_name in enumerate(visa_list):
  if dev_name.startswith("USB"):
    dev = rm.open_resource(dev_name)
    try:
      out = dev.query('*IDN?')
      print(dev)
      print(out)
      if out.startswith('AGILENT') or out.startswith('KEYSIGHT'):
        Osc = dev
        Osc.timeout = conf.OscTimeout
      elif out.startswith('NF Corporation'):
        FG = dev
    except Exception as e:
      print(f"Error while querying device {dev_name}: {e}")

if FG is None:
  print("Function Generator is not connected...")
  exit()
if Osc is None:
  print("Oscilloscope is not connected...")
  exit()


def InitialSetFG():
  FG.write(":SOURce:MODE BURSt") # 発信モードをバーストに設定
  FG.write(":SOURce:FUNCtion:SHAPe USER") # 関数を任意波形(user)に設定
  FG.write(":SOURce:BURSt:STATe 1") # 発信モードの連続/バースト切り替え(0/1 or OFF/ON)
  FG.write(":SOURce:BURSt:MODE TRIGger") # バーストモードのタイプをトリガーに変更
  FG.write(":SOURce:BURSt:NCYCles 1") # マーク波数を設定
  FG.write(":SOURce:FREQuency %f" % (1/conf.ModulationTime)) #周波数の設定(バーストの信号の長さの設定)
  FG.write(":TRIGger:BURSt:SOURce EXTernal") # 外部トリガー設定
  FG.write(":TRIGger:BURSt:SLOPe OFF") # 外部トリガーの極性をOFFにしておくと、外来ノイズによる誤動作が避けられる(マニュアルP.106)
  FG.write(":SOURce:FUNCtion:USER %i" % conf.FGMemory)  # メモリから任意波形読み込み
  FG.write(":SOURce:VOLTage %f" % conf.FGVoltage) # 波形の振幅を設定
  FG.write(":OUTPut:SYNC:BURSt:TYPE BSYNc") # SYNC OUTの同期出力をバースト同期に設定
  
def InitialSetFG_WideRangeScan():
  FG.write(":SOURce:MODE SWEep") # 発信モードをスイープに設定
  FG.write(":SOURce:FUNCtion:SHAPe SINusoid") # 関数を任意波形(user)に設定
  FG.write(":SOURce:SWEep:MODE GATed") # ゲーテッド単発
  FG.write(":TRIGger:SWEep:SOURce EXTernal") # 外部トリガー設定
  FG.write(":TRIGger:SWEep:SLOPe OFF") # 外部トリガーの極性をOFFにしておくと、外来ノイズによる誤動作が避けられる
  FG.write(":SOURce:SWEep:TIME %f" % conf.ModulationTime) # スイープ時間設定
  FG.write(":SOURce:FREQuency:STARt %f" % conf.StartFreq) # 周波数開始値
  FG.write(":SOURce:FREQuency:STOP %f" % conf.StopFreq) # 周波数停止値
  FG.write(":SOURce:VOLTage %f" % conf.FGVoltage) # 波形の振幅を設定
  FG.write(":OUTPut:SYNC:SWEep:TYPE MARker") # SYNC OUTの同期出力をマーカに設定

# Takada SetOsc
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
  
def SpinFlip():
  # FGのoutputをON
  FG.write("OUTPut:STATe ON")

  # Send time of Trigger
  t = datetime.datetime.now()
  date_1 = str(t)[:-3]
  
  # ファンクションジェネレータのトリガーをON
  FG.write("*TRG")  

  # End time of Trigger
  t = datetime.datetime.now()
  date_2 = str(t)[:-3]

  # オシロch2の波形取得
  Osc.write(":WAVeform:SOURce CHANnel2")
  Oscdata = Osc.query_binary_values(":WAVeform:DATA?", datatype='B')
  
  # FGのoutputをOFF
  FG.write("OUTPut:STATe OFF")
  
  return Oscdata, date_1, date_2


def GetOscInformation():
  TOrigin = float(Osc.query("WAVeform:XORigin?"))       # 最初のデータ点の X 軸値
  TReference = float(Osc.query("WAVeform:XREFerence?")) # 指定されているソース(signal=ch2)の時間基準点
  TIncrement = float(Osc.query("WAVeform:XINCrement?")) # データポイント間の時間差
  
  VOrigin = float(Osc.query("WAVeform:YORigin?"))       # 縦軸の原点 (原点から正方向にずらしていたら負)
  VReference = float(Osc.query("WAVeform:YREFerence?")) # どこを指してるのかよくわからない
  VIncrement = float(Osc.query("WAVeform:YINCrement?")) # 1bitが何Vか
  
  return TOrigin, TReference, TIncrement, VOrigin, VReference, VIncrement


def DataOutputToBinaryFile(Oscdata, BinaryFileName, OscInformation):
  NPointLockin = 0
  VLockin = []
  TimeLockin = []
  VLockintemp = 0
  NPoint = 0
  VMax = 0
  MaxT = 0
  NMean = 1000
  with open(BinaryFileName, mode='wb') as f:
    for iInfo in range(len(OscInformation)):
      f.write(struct.pack("f", OscInformation[iInfo]))
    for iData in Oscdata:
      f.write(struct.pack("B", iData))
    
def DataOutputToParameterFile():
  NowTime = datetime.datetime.now()
  DataDictionary = dict(Time=[NowTime],
                        TimeInterval=[conf.TimeInterval],
                        Voltage=[conf.FGVoltage],
                        FunctionGenerator=[FG],
                        Oscilloscope=[Osc],
                        FreqRange=[conf.FreqRange])
  df = pd.DataFrame(data=DataDictionary)
  
  # output
  header = FileInfo.addHeader(conf.FileNameParameter)
  df.to_csv(conf.FileNameParameter, mode="a", index=False, header=header)
  
  
def main(BinaryFileName):
  # Check FG Setting
  print("Pulse Time : ", conf.ModulationTime, " Memory Number : ", conf.FGMemory)
  
  ###############################
  # Initialization
  print("Initialization of Oscilloscope")
  InitialSetOsc()  
  print("Initialization of Function Generator ")
  if conf.OptWideRangeScan:
    InitialSetFG_WideRangeScan()
  else:
    InitialSetFG()

  ###############################
  # Spin flip
  print("Flip!")
  Oscdata, date_1, date_2 = SpinFlip()
  
  ####
  # Get Osc Information (Origin, Reference, Increment) -> XYScale in Lockin.py    
  OscInformation = GetOscInformation()
  print("TOrigin: {0}, TReference: {1}, TIncrement: {2}".format(OscInformation[0], OscInformation[1], OscInformation[2]))
  print("VOrigin: {0}, VReference: {1}, VIncrement: {2}".format(OscInformation[3], OscInformation[4], OscInformation[5]))
  
  # Start time to write file
  t = datetime.datetime.now()
  date_3 = str(t)[:-3]
  f_log = open(conf.FileNameLog, 'a')
  
  # Write log
  date_line = "TRG IN: "+date_1+' TRG END :' + \
    date_2+' FILE WRITE START '+date_3+'\n'
  f_log.write(date_line)
  f_log.close()
    
  # time of Output
  d_today = datetime.datetime.now()
  str(d_today.strftime('%H%M'))
  
  # Data Output
  DataOutputToBinaryFile(Oscdata, BinaryFileName, OscInformation)
  DataOutputToParameterFile()  
  

  
if __name__ == "__main__":
  
  os.makedirs(conf.DataPath, exist_ok=True)
  FileNo = FileInfo.GetMaxFileNumber() + 1
  BinaryFileName = conf.DataPath + str(FileNo).zfill(4) + ".bin"
  main(BinaryFileName)  