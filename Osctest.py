import pyvisa as visa
import Config as conf
# リソースマネージャーを初期化
rm = visa.ResourceManager()

# 接続可能なリソースのリストを取得
visa_list = rm.list_resources()
print(visa_list)

Osc = None

Osc = rm.open_resource("USB0::0x0957::0x1798::MY61410321::INSTR")#New Keysight Oscillo


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


InitialSetOsc()


