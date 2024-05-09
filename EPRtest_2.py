import csv
import os
import struct
import time
import pyvisa as visa
import Config as conf
import datetime
import pandas as pd
import FileInfo
import sys

argvs = sys.argv  
argc = len(argvs) 
DataDirectryName = "/Data/AFPNMR/2024/0509/Runtest/"
HomePath         = os.path.expanduser("~")
EPRsignal_path   = HomePath + "/Research/" + DataDirectryName

rm = visa.ResourceManager()                                                 # VISAリソースマネージャをインスタンス化
visa_list = rm.list_resources()                                             # 利用可能なVISAリソース(機器)のリストを取得
print(visa_list)                                                            # 機器リストを出力

FG = None                                                                   # ファンクションジェネレータのための変数を初期化
Osc = None                                                                  # オシロスコープのための変数を初期化



# ファンクションジェネレータとオシロスコープのリソースをオープン
FG=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")                 # ノダさんのファンクションジェネレータ
Osc = rm.open_resource("USB0::0x0957::0x1798::MY61410321::INSTR")           # Keysightオシロスコープ

NAverage=64
Query_delay = 0
TOrigin=float(Osc.query("WAVeform:XORigin?"))
TReference=float(Osc.query("WAVeform:XREFerence?"))
TIncrement=float(Osc.query("WAVeform:XINCrement?"))

def InitialSetFG():
  # ファンクションジェネレータの初期設定
  FG.write(":SOURce:MODE Modulation") 
  FG.write(":SOURce:FUNCtion:SHAPe Sin")                                    # 関数をサイン波に設定
  FG.write(f":SOURce:FREQuency {conf.Freq_EPR}")
  FG.write(f":SOURce:VOLTage {conf.Voltage_EPR}")
  FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {conf.ModulationFreq_EPR}")
  FG.write(f":SOURce:MODulation:FM:DEViation {conf.iDeltaFreq_EPR}")

def InitialSetOsc():
  # オシロスコープの初期設定
  Osc.write(":RUN")                                                         # フロントパネルのRunを押す
  Osc.write(":DISPlay:CLEar")  # オシロの表示をリセット
  Osc.write(":TIMebase:RANGe %f" % (conf.OscWindowscale_EPR))               # ウィンドウの水平方向のフルスケールを秒単位で設定
  Osc.write(":TIMebase:REFerence CENTer")                                   # 信号のディレイの基準点を中央にする
  Osc.write(":TIMebase:POSition %f" % (conf.OscDelayTime_EPR))              # トリガーと基準点の時間間隔を設定

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
  Osc.write(":MTESt:TRIGger:SOURce CHANnel%d" % (conf.OscChTrigger_EPR))    # トリガーとして使用するチャンネルを設定
  Osc.write(":TRIGger:EDGE:LEVel %f" % (conf.OscTriggerLevel_EPR))          # トリガーレベルを設定
  Osc.write(":TRIGger:SLOPe NEGative")                                      # トリガーの立ち下がりエッジを検出

  # データ取得の設定
  Osc.write(":ACQuire:COMPlete 100")                                        # 取り込みの完了基準を100%に設定
  Osc.write(":WAVeform:FORMat BYTE")                                        # データ形式をバイト形式に設定
  Osc.write(":WAVeform:POINts %d" % (conf.OscDataPoint_EPR))                # 波形のポイント数を設定
  Osc.write(":WAVeform:POINts:MODE MAXimum")                                # 取得する波形ポイントの最大数を使用
  Osc.write(":STOP")                                                        # フロントパネルのStopを押す
  Osc.write(":RUN")                                                         # フロントパネルのRunを押す
  Osc.write(":TRIGger:SWEep Normal")                                        # トリガーモードをNormalに設定
  Osc.write(":DIGitize")                                                    # データ取得を開始

def AverageSetOsc(NorA, Avecount):
    if(NorA=="N"): Osc.write(":ACQuire:TYPE Normal")
    if(NorA=="A"):
        Osc.write(":ACQuire:TYPE Average")
        Osc.write(":MTESt:AVERage:COUNt %d" %(Avecount))

def EPR():
  # EPR測定のための波形取得処理
  AverageSetOsc("A", NAverage)
  FG.write("OUTPut:STATe ON")                                               # ファンクションジェネレータの出力をON
  #time.sleep(5)                                                             # アベレージのために少し待つ

  # オシロスコープからチャンネル2と3のデータを取得
  Osc.write(":WAVeform:SOURce CHANnel1")
  print("wrote")
  value=Osc.query(":WAVeform:DATA?", delay = Query_delay)  #delayはmsで書かれる
  V=value.split(",")
  V[0]=V[0][10:]
  V=list(map(float, V))
  NPoint=len(V)

  AverageSetOsc("N", 0)
  Osc.write(":WAVeform:SOURce CHANnel3")
  value2=Osc.query(":WAVeform:DATA?")
  VSync=value2.split(",")
  VSync[0]=VSync[0][10:]
  VSync=list(map(float, VSync))

  VCurrent=1 #Meter.query(":Measure:Current?")  
  VCurrent=float(VCurrent)

  Time=[(i-TReference)*TIncrement+TOrigin for i in range(NPoint)]

    # 得た電圧の情報をテキストファイルに書き込む.
  if argc == 3:
    f=open(EPRsignal_path + argvs[2],"a")
    for i in range(NPoint):
        f.write("%f %f %f\n" %(Time[i], V[i], VSync[i]))
    f.close()

  FG.write("OUTPut:STATe OFF")                                              # ファンクションジェネレータの出力をOFF

def main():
  #print("Pulse Time : ", conf.ModulationTime, " Memory Number : ", conf.FGMemory)
  print("Initialization of Oscilloscope")
  InitialSetOsc()
  print("Initialization of Function Generator ")
  InitialSetFG()

  print("EPR Get")
  EPR()

  t = datetime.datetime.now()
  date_3 = str(t)[:-3]
  f_log = open(conf.FileNameLog, 'a')
  date_line = "FILE WRITE START " + date_3 + '\n'
  f_log.write(date_line)
  f_log.close()

  d_today = datetime.datetime.now()
  str(d_today.strftime('%H%M'))

if __name__ == "__main__":
  main()                                                      # メイン関数を実行
