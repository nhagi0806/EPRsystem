import pyvisa
import os

# リソースマネージャの作成
rm = pyvisa.ResourceManager()

# オシロスコープとの接続（リソース名は実際の環境に合わせて変更してください）
scope = rm.open_resource('GPIB::1')

# ディレクトリのパスを設定
data_directory = "/Data/AFPNMR/2024/0418/RoomA_BL18Onbeam_natXe3atm_Test/"

# ディレクトリが存在しない場合は作成
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

# オシロスコープの設定
scope.write('DATA:SOURCE CH2')  # データソースをチャンネル2に設定
scope.write('DATA:WIDTH 2')  # データのビット幅（2 = 16ビット）
scope.write('DATA:ENC RPB')  # データ形式をバイナリに設定（RPB = 最も下位のバイト先）
scope.write('ACQUIRE:MODE AVERAGE')  # 取得モードを平均に設定
scope.write('ACQUIRE:NUMAVG 16')  # 平均するサンプル数を設定

# 波形データの取得コマンド
scope.write('CURVE?')
raw_data = scope.read_raw()

# バイナリファイルとしてデータを保存
file_path = os.path.join(data_directory, 'waveform.bin')
with open(file_path, 'wb') as f:
    f.write(raw_data[2:])  # 先頭のヘッダをスキップしてデータのみを保存

# 接続のクローズ
scope.close()

print(f"データが {file_path} にバイナリファイルとして保存されました。")
