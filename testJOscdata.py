import pyvisa
import time
from datetime import datetime
import pandas as pd


VISAAddr = "USB0::___::____::INSTR" #rm.list_resources()にて得られる接続先のアドレス
MAX_CH = 4     #オシロスコープの最大チャンネル数
ch_en=[]
IsFirstCh = False

#リソースマネージャを実体化し、オシロスコープと接続を行う
rm = pyvisa.ResourceManager()
inst = rm.open_resource(VISAAddr)

#接続先のオシロスコープの情報を表示（表示できない場合はエラーで終了）
print(inst.query('*IDN?'))

####################
##波形データの取得処理###
####################

#アクティブ状態のチャンネルを検出する（同時に最も若い番号のチャンネル番号も取得）
for i in range(MAX_CH):
    ch_en.append(int(inst.query('DISplay:GLObal:CH'+str(i+1)+':STATE?')))
    if ch_en[i] == 1 and IsFirstCh:
        first_ch = i
        IsFirstCh = False
        
#チャンネルごとに波形データ取得処理
csv_lst = [ 0 for i in range(MAX_CH)]

for n in range(MAX_CH):
    #チャンネルがアクティブなら波形取得処理開始
    if ch_en[n]==1:
        #チャンネル番号を生成し、PyVISAでオシロスコープの内蔵HDに波形データを保存させる
        ch_no = "CH" + str(i+1)
        inst.write('SAVE:WAVEform '+ch_no +', \"C:Temp.csv\"')
        
        #PC側へ保存する個別波形データの名前を定義
        filename = "temp_" + ch_no +".csv"
        csv_lst [n] = filename
        
        #波形データの保存処理が終了するまで待つ
        while inst.query('*OPC?')[0]!="1":
            print("Waiting")
            time.sleep(1)
            
        #オシロスコープ上の波形データを読み出す
        inst.write('FILESystem:READFile \"C:/Temp.csv\"')
        wave_data = inst.read_raw()
        
        #読み出した波形データを指定したファイル名でPCに保存
        file = open(filename,"wb")
        file.write(wave_data)
        file.close()
        
        #オシロスコープ側のテンポラリ画像ファイルを削除
        inst.write('FILESystem:DELEte \"C:/Temp.csv\"')
        
        #処理終了を示すメッセージ
        print("Channel "+ str(ch_no) + " Done")

#測定終了後にオシロスコープとの通信を切断する
inst.close()
rm.close()

####################
##波形データの統合処理###
####################
CSV_HEADER_ROWS = 7
CSV_SKIP_ROWS = 9

#アクティブチャンネルを検出した数だけ波形データの格納リストを作る
ch_wave =[[] for i in range(sum(ch_en))]

#最も若いチャンネル番号のcsv波形データファイルからヘッダデータと時間軸データを取得
header = pd.read_csv(csv_lst[first_ch],header = None, nrows = CSV_HEADER_ROWS)
time_dt = pd.read_csv(csv_lst[first_ch],header = None, usecols=[0],skiprows=CSV_SKIP_ROWS)

#最大チャンネル数まで波形データが保存されているかをチェックし、あれば格納リストにcsvデータを格納
wave_cnt = 0
for i in range(MAX_CH):
    if csv_lst[i]!=0:
        ch_wave[wave_cnt] = pd.read_csv(csv_lst[first_ch],header = None, usecols=[1],skiprows=CSV_SKIP_ROWS)
        ch_wave[wave_cnt].columns =["CH" +str(i+1)]
        wave_cnt +=1
        
#取得したチャンネルごとの波形データを1つのDataFrameに統合(最初の列は時間軸にする)
out_dt = time_dt
for i in range(sum(ch_en)):
    out_dt = pd.concat([out_dt,ch_wave[i]],axis=1)
    
#PC側に保存する際にdatetimeモジュールを使い、日付＋時間のファイル名生成
dt=datetime.now()
wave_filename = dt.strftime("Wave_%Y%m%d_%H%M%S.csv")

#Pandasの機能を使って、DataFrameをcsvに変換。このとき個別のcsvとヘッダデータ部分は共通にする
header.to_csv(wave_filename,header= False, index = False)
out_dt.to_csv(wave_filename,header= True, index = False,mode = 'a')
print("Wave File Output Complete")