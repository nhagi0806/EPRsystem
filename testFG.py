import pyvisa as visa
# リソースマネージャーを初期化
rm = visa.ResourceManager()

# 接続可能なリソースのリストを取得
visa_list = rm.list_resources()
print(visa_list)

# 関数ジェネレータの初期化
FG = None

# リスト内の各リソースについて処理
for dev_name in visa_list:
    # リソースをオープン
    dev = rm.open_resource(dev_name)
    # リソースから識別情報を取得
    out = dev.query('*IDN?')
    # KeysightまたはAgilentのデバイスであるかどうかをチェック
    if 'KEYSIGHT' in out or 'AGILENT' in out:
        FG = dev
        break

# 関数ジェネレータが見つからない場合は終了
if not FG:
    print("Function Generator not found.")
    exit()

def InitialSetFG():
    # 関数ジェネレータの初期設定
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
