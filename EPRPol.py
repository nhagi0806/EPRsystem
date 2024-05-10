import numpy as np
import pandas as pd
import Config as conf
import sys

def ReadTextPeak(text):
    data = np.loadtxt(text, delimiter=" ", dtype=np.float64)
    sign_changes = np.where(np.diff(np.sign(data[:, 2])) < 0)[0]

    boundary = [data[0][0]]
    for i in sign_changes:
        boundary.append(data[i, 0])
    boundary.append(data[-1][0])

    peak = []
    peak2 = []
    for i in range(len(boundary) - 1):
        indices = np.where((data[:, 0] > boundary[i]) & (data[:, 0] < boundary[i + 1]))[0]
        peak.append(data[indices[np.argmin(data[indices, 1])], 0])
        peak2.append(data[indices[np.argmin(data[indices, 1])], 0]-i/conf.iDeltaFreq_EPR)
    return peak, peak2

def convertFreq(peaks):
    Freq = [2*conf.ModulationFreq_EPR*conf.iDeltaFreq_EPR*peak + conf.Freq_EPR - conf.ModulationFreq_EPR for peak in peaks]
    return Freq

def convertPol(Freq1, Freq2, Std1, Std2):
    A_hfs = 1.011911 * 10**9  # Hz
    I = 5 / 2
    Delnu_2 = abs(Freq1 - Freq2)
    Delnu = Delnu_2 / 2  # Hz
    g_s = 2.002331
    mu_B = 9.927401 * 10**-24  # J/T
    mu_0 = 4 * np.pi * 10**-7
    mu_129 = -3.929344 * 10**-27  # N/A**2
    kapper_0 = 518
    B_0 = 1.6133 * 10**-3  # T
    h = 6.62607015 * 10**-34
    num_129 = 7.32 * 10**25

    const = abs((3 * h * (2 * I + 1) * (2 * I + 1)**2 * h * A_hfs) / (2 * mu_0 * mu_B * g_s * kapper_0 * mu_129 * num_129 * ((2 * I + 1)**2 * h * A_hfs - 8 * I * mu_B * g_s * B_0)))
    Pol = Delnu * const
    Std = (Std1 + Std2) * const
    return Pol, Std

def main():
    peak_first, peak2_first = ReadTextPeak(sys.argv[1])
    Freq_first = convertFreq(peak2_first)
    
    FreqAve_first = np.average(Freq_first)
    FreqStd_first = np.std(Freq_first)

    peak_second, peak2_second = ReadTextPeak(sys.argv[2])
    Freq_second = convertFreq(peak2_second)
    
    FreqAve_second = np.average(Freq_second)
    FreqStd_second = np.std(Freq_second)

    Pol, Std = convertPol(FreqAve_first, FreqAve_second, FreqStd_first, FreqStd_second)

    # 結果をテキストファイルに書き出し
    with open('results.txt', 'w') as f:
        f.write("Polarization: {:.6f}\n".format(Pol))
        f.write("Standard Deviation of Polarization: {:.6f}\n".format(Std))

if __name__ == "__main__":
    main()
