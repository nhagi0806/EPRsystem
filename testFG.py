import pyvisa as visa
# リソースマネージャーを初期化
rm = visa.ResourceManager()

# 接続可能なリソースのリストを取得
visa_list = rm.list_resources()
print(visa_list)
FG=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")#Noda-san's FG
# 関数ジェネレータの初期化
#FG = None

'''
def InitialSetFG():
  FG.write(":SOURce:MODE BURSt") # 発信モードをバーストに設定
  FG.write(":SOURce:FUNCtion:SHAPe USER") # 関数を任意波形(user)に設定
  FG.write(":SOURce:BURSt:STATe 1") # 発信モードの連続/バースト切り替え(0/1 or OFF/ON)
  FG.write(":SOURce:BURSt:MODE TRIGger") # バーストモードのタイプをトリガーに変更
  FG.write(":SOURce:BURSt:NCYCles 1") # マーク波数を設定
  FG.write(":SOURce:FREQuency %f" % (1000)) #周波数の設定(バーストの信号の長さの設定)
  FG.write(":TRIGger:BURSt:SOURce EXTernal") # 外部トリガー設定
  FG.write(":TRIGger:BURSt:SLOPe OFF") # 外部トリガーの極性をOFFにしておくと、外来ノイズによる誤動作が避けられる(マニュアルP.106)
  FG.write(":SOURce:FUNCtion:USER %i" % 40000)  # メモリから任意波形読み込み
  FG.write(":SOURce:VOLTage %f" % 2000) # 波形の振幅を設定
  FG.write(":OUTPut:SYNC:BURSt:TYPE BSYNc") # SYNC OUTの同期出力をバースト同期に設定
'''

def InitialSetFG():
    # 関数ジェネレータの初期設定
    FG.write(":SOURce:MODE Modulation") # 発信モードをバーストに設定
    FG.write(":SOURce:FUNCtion:SHAPe sin") # 関数をsinに設定
    FG.write(f":SOURce:FREQuency {7500000}")  # 周波数を設定
    FG.write(f":SOURce:VOLTage {20}")  # 電圧を設定
    FG.write(":SOURce:MODulation:FM:STATe ON")  # 周波数変調をON
    FG.write(f":SOURce:MODulation:FM:INTernal:FREQuency {1000000}")  # 変調周波数を設定
    FG.write(f":SOURce:MODulation:FM:DEViation {1503}")  # 変調の偏差を設定
    FG.write(":OUTPut ON")  # 出力をON

    # 出力をOFFにしたい場合は以下のコマンドを追加します
    # FG.write(":OUTPut OFF")  # 出力をOFFにする

# もし、他の設定を追加したい場合は、上記のように FG.write() を使って追加します

# InitialSetFG()を呼び出して関数ジェネレータの初期設定を行う
InitialSetFG()
