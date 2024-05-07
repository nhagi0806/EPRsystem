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

FG=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")#Noda-san's FG
Osc = rm.open_resource("USB0::0x0957::0x1798::MY61410321::INSTR")#New Keysight Oscillo  


def InitialSetFG():
  FG.write(":SOURce:MODE Modulation") 
  FG.write(":SOURce:FUNCtion:SHAPe Sin") # 関数をsinに設定
  FG.write(f":SOURce:FREQuency {conf2.iFreq}")
  FG.write(f":SOURce:VOLTage {conf2.Voltage}")
  FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {conf2.ModulationFreq}")
  FG.write(f":SOURce:MODulation:FM:DEViation {conf2.iDeltaFreq}")

def InitialSetOsc():
  # ディスプレイの設定
  Osc.write(":RUN")                                                            # フロントパネルのRunを押す
  #  Osc.write(":SYSTem:PRECision ON")                                         # 高精度測定モードだけど、2000-Xシリーズでは廃止されたコマンドのため不要
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
  # FGのoutputをON
  FG.write("OUTPut:STATe ON")

  #アベレージのために待つ
  time.sleep(5)

  #オシロのチャンネル2の波形取得
  Osc.write(":WAVeform:SOURce CHANnel2")
  OscData_CH2 = Osc.query_binary_values(":WAVeform:DATA?", datatype='B')
 
  #オシロのチャンネル3の波形取得
  Osc.write(":WAVeform:SOURce CHANnel3")
  OscData_CH3 = Osc.query_binary_values(":WAVeform:DATA?", datatype='B')
  
  # FGのoutputをOFF
  FG.write("OUTPut:STATe OFF")
  
  return OscData_CH2,OscData_CH3

def GetOscInformation():
  TOrigin = float(Osc.query("WAVeform:XORigin?"))       # 最初のデータ点の X 軸値
  TReference = float(Osc.query("WAVeform:XREFerence?")) # 指定されているソース(signal=ch2)の時間基準点
  TIncrement = float(Osc.query("WAVeform:XINCrement?")) # データポイント間の時間差
  VOrigin = float(Osc.query("WAVeform:YORigin?"))       # 縦軸の原点 (原点から正方向にずらしていたら負)
  VReference = float(Osc.query("WAVeform:YREFerence?")) # どこを指してるのかよくわからない
  VIncrement = float(Osc.query("WAVeform:YINCrement?")) # 1bitが何Vか
  
  return TOrigin, TReference, TIncrement, VOrigin, VReference, VIncrement

def DataOutputToBinaryFile(OscData_CH2, OscData_CH3, BinaryFileName, OscInformation):
  with open(BinaryFileName, mode='wb') as f:
    # OscInformation の書き込み
    for iInfo in range(len(OscInformation)):
      f.write(struct.pack("f", iInfo))      
    # OscData_CH2 のデータを書き込み
    for iData2 in OscData_CH2:
      f.write(struct.pack("B", iData2))
    # OscData_CH3 のデータを書き込み
    for iData3 in OscData_CH3:
      f.write(struct.pack("B", iData3))

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
  print("Pulse Time : ", conf.ModulationTime, " Memory Number : ", conf.FGMemory)
  
  print("Initialization of Oscilloscope")
  InitialSetOsc()  
  print("Initialization of Function Generator ")
  InitialSetFG()

  print("EPR Get")
  OscData_CH2,OscData_CH3= EPR()
  
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
  
  DataOutputToBinaryFile(OscData_CH2,OscData_CH3, BinaryFileName, OscInformation)
  DataOutputToParameterFile() 

if __name__ == "__main__":
  
  os.makedirs(conf.DataPath, exist_ok=True)
  FileNo = FileInfo.GetMaxFileNumber() + 1
  BinaryFileName = conf.DataPath + str(FileNo).zfill(4) + ".bin"
  main(BinaryFileName)  
