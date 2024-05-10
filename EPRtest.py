import csv
import os
import struct
import time
import pyvisa as visa
import Config as conf
import datetime
import pandas as pd
import FileInfo

rm = visa.ResourceManager()                                                 # VISAリソースマネージャをインスタンス化
visa_list = rm.list_resources()                                             # 利用可能なVISAリソース(機器)のリストを取得
print(visa_list)                                                            # 機器リストを出力

FG = None                                                                   # ファンクションジェネレータのための変数を初期化                                                             # オシロスコープのための変数を初期化

# ファンクションジェネレータとオシロスコープのリソースをオープン
FG=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")                 # ノダさんのファンクションジェネレータ

def InitialSetFG():
  # ファンクションジェネレータの初期設定
  FG.write(":SOURce:MODE Modulation") 
  FG.write(":SOURce:FUNCtion:SHAPe Sin")                                    # 関数をサイン波に設定
  FG.write(f":SOURce:FREQuency {conf.Freq_EPR}")
  FG.write(f":SOURce:VOLTage {conf.Voltage_EPR}")
  FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {conf.ModulationFreq_EPR}")
  FG.write(f":SOURce:MODulation:FM:DEViation {conf.iDeltaFreq_EPR}")

def InitialSetFG():
  FG.write(":Source1:FM:State ON")
  FG.write(":Source1:FM:Source Internal")
  FG.write(":Source1:FM:Internal:Function:Shape PRAMP")
  FG.write(":Source1:Voltage 5" )
  FG.write(":Source1:FM:Internal:Frequency 1000Hz")
  FG.write(":Source1:Frequency 9.26e6HZ")
  FG.write(":Source1:FM:Deviation 1.852e6HZ")


def main():
  InitialSetFG()
  print("FG SET OK")