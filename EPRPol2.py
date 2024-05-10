import numpy as np
import pandas as pd
import Config as conf
import sys
from datetime import datetime

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
        peak2.append(data[indices[np.argmin(data[indices, 1])], 0] - i / conf.iDeltaFreq_EPR)
    return peak, peak2

def convertFreq(peaks):
    Freq = [2 * conf.ModulationFreq_EPR * conf.iDeltaFreq_EPR * peak + conf.Freq_EPR - conf.ModulationFreq_EPR for peak in peaks]
    return Freq

def convertPol(Freq1, Freq2, Std1, Std2):
    Delnu_2 = abs(Freq1 - Freq2)
    Delnu = Delnu_2 / 2  # Hz

    const = abs((3 * conf.h * (2 * conf.I + 1) * (2 * conf.I + 1)**2 * conf.h * conf.A_hfs) / (2 * conf.mu_0 * conf.mu_B * conf.g_s * conf.kapper_0 * conf.mu_129 * conf.num_129 * ((2 * conf.I + 1)**2 * conf.h * conf.A_hfs - 8 * conf.I * conf.mu_B * conf.g_s * conf.B_0)))
    Pol = Delnu * const
    Std = (Std1 + Std2) * const
    return Pol, Std

def writeResults(Pol, Std, peak_first, peak_second):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filepath = conf.FileNamePolarizarion
    with open(filepath, 'a') as f:
        f.write(f"Data Acquisition Time: {now}\n")
        f.write(f"Polarization: {Pol:.6f}\n")
        f.write(f"Standard Deviation of Polarization: {Std:.6f}\n")
        f.write(f"Peak Points Before Flip (s): {peak_first}\n")
        f.write(f"Peak Points After Flip (s): {peak_second}\n")
        f.write("--------------------------------------------------\n")

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

    writeResults(Pol, Std, peak_first, peak_second)

if __name__ == "__main__":
    main()
