import struct
import numpy as np
import ROOT

def read_binary_data(filename):
    """バイナリファイルからデータを読み込み、時間と信号の配列を返す"""
    with open(filename, "rb") as f:
        # ファイルからオシロスコープ情報を読み込む
        # 仮定として、各情報はfloat型（4バイト）で保存されているとします
        t_origin, t_reference, t_increment, v_origin, v_reference, v_increment = struct.unpack("6f", f.read(24))
        
        # チャンネルデータの読み込み
        data = f.read()
        osc_data = np.frombuffer(data, dtype=np.uint8)
        
    # チャンネルごとのデータポイント数を計算
    num_points = len(osc_data) // 2
    osc_data_ch2 = osc_data[:num_points]
    osc_data_ch3 = osc_data[num_points:]
    
    # 時間軸の生成
    time_axis = np.arange(num_points) * t_increment + t_origin
    
    return time_axis, osc_data_ch2, osc_data_ch3

def plot_data(time_axis, data, title):
    """ROOTを使用してデータをプロットする"""
    graph = ROOT.TGraph(len(time_axis), time_axis, data)
    graph.SetTitle(title)
    graph.GetXaxis().SetTitle("Time (s)")
    graph.GetYaxis().SetTitle("Voltage (V)")
    graph.SetMarkerStyle(20)
    graph.SetMarkerSize(0.7)
    graph.Draw("APL")
    ROOT.gPad.Update()
    input("Press Enter to exit...")

# データの読み込み
time_axis, osc_data_ch2, osc_data_ch3 = read_binary_data("path_to_your_binary_file.bin")

# データのプロット
ROOT.TCanvas("c1", "Channel 2", 800, 600)
plot_data(time_axis, osc_data_ch2.astype(np.float32), "Channel 2 Signal")

ROOT.TCanvas("c2", "Channel 3", 800, 600)
plot_data(time_axis, osc_data_ch3.astype(np.float32), "Channel 3 Signal")