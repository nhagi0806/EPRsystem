import pyvisa as visa #import visa causes an error "module 'visa' has no attribute 'ResourceManager'"
import ROOT
from array import array
import time
import datetime
import csv
import math
import sys

argvs = sys.argv  
argc = len(argvs) 
FreqValue_path = "./FreqValue/"
EPRsignal_path = "./EPRsignal/"

rm = visa.ResourceManager()

#Parameters
FG=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")#Noda-san's FG
Osc = rm.open_resource("USB0::0x0957::0x1798::MY61410321::INSTR")#New Keysight Oscillo  
Meter = rm.open_resource("ASRL5::INSTR")

Osc.timeout = 1000000          #time out time (ms)
Threthold=0.05              #Volt
ChSignal=1                  #channel of the signal input
ChSync=3                    #channel of the sync out from the function generator
ChTrigger=ChSync

ModulationFunc="UpRamp"
Function="SIN"
ModulationFreq=1503       #Hz Modulation frequency
iFreq= 7500000
iDeltaFreq=1e6*0.5 #iFreq*0.03  #Hz Initial amplitude of the deviation 
Voltage=20           #Volt
N_wave=4
WaveFormPoints = 1000

Query_delay = 0
SleepTime=1
NAverage=500/2


Osc.write(":RUN")
Osc.write(":TRIGger:SWEep AUTO")
Osc.write(":RUN")
Osc.write(":ACQuire:TYPE Normal")
TOrigin=float(Osc.query("WAVeform:XORigin?"))
TReference=float(Osc.query("WAVeform:XREFerence?"))
TIncrement=float(Osc.query("WAVeform:XINCrement?"))

def InitialSetFM():
    FG.write(":Source1:FM:State ON")
    FG.write(":Source1:FM:Source Internal")
    FG.write(":Source1:Function:Shape %s" %Function)
    FG.write(":Source1:FM:Internal:Function:Shape %s" %ModulationFunc)
    FG.write(":Source1:Voltage %f" %Voltage)
    FG.write(":Source1:FM:Internal:Frequency %fHZ" %(ModulationFreq))
    FG.write(":Source1:Frequency %fHZ" %(iFreq))
    FG.write(":Source1:FM:Deviation %fHZ" %(iDeltaFreq))
    

def InitialSetOsc(NorA):
    Osc.write(":TIMebase:RANGe %f" %(1./ModulationFreq*N_wave))
    Osc.write(":TRIGger:SWEep Normal")
    Osc.write(":TRIGger:LEVel 0.0")
    Osc.write(":TRIGger:Source Channel%d" %(ChTrigger))
    Osc.write(":ACQuire:COMPlete 100")
    Osc.write(":WAVeform:FORMat BYTE") #set the data transmission mode for waveform data points
    Osc.write(":WAVeform:FORMat ASCII")
    Osc.write(":WAVeform:POINts:MODE MAXimum")
    Osc.write(":WAVeform:POINts %d" %(WaveFormPoints))

    
def AverageSetOsc(NorA, Avecount):
    if(NorA=="N"): Osc.write(":ACQuire:TYPE Normal")
    if(NorA=="A"):
        Osc.write(":ACQuire:TYPE Average")
        Osc.write(":MTESt:AVERage:COUNt %d" %(Avecount))

def SetFM(Freq,Deltafreq):
    FG.write(":Source1:Frequency %fHZ" %(Freq))
    FG.write(":Source1:FM:Deviation %fHZ" %(Deltafreq))

def CloseDevices():
    FG.close()
    Osc.close()

def GetEPRFreqLockin(Freq, DeltaFreq):
    AverageSetOsc("A", NAverage)
    Osc.write(":WAVeform:SOURce CHANnel1")
    print("wrote")
    value=Osc.query(":WAVeform:DATA?", delay = Query_delay)  #delayはmsで書かれる
    V=value.split(",")
    V[0]=V[0][10:]
    V=list(map(float, V))
    NPoint=len(V)

    AverageSetOsc("N", 0)
    Osc.write(":WAVeform:SOURce CHANnel%d"%(ChSync))
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
    
    tmpmax=0
    FreqEPR=iFreq
    VSyncEPR=0
    NEPRSignal=500
    TimeEPRSignal=0
    LockinValue=0
    VLockin=[]
    VInteg=0
    
    VSyncEPR=0
    NEPRSignal=500
    TimeEPRSignal=0
    i_OffsetRegion=0
    for i in range(NPoint):
        if(V[i]>tmpmax):
            tmpmax=V[i]
            NEPRSignal=i
            TimeEPRSignal=Time[NEPRSignal]
            VSyncEPR=VSync[NEPRSignal]
            
            
        LockinValue=LockinValue+V[i]*VSync[i]
        VLockin.append(V[i]*VSync[i])
        Point_at1Wave=NPoint/N_wave
        Percent_OffsetRegion=0.1
        if((Point_at1Wave*(1-Percent_OffsetRegion)<i<Point_at1Wave*(1+0*Percent_OffsetRegion)) or 
        (Point_at1Wave*(2-Percent_OffsetRegion)<i<Point_at1Wave*(2+0*Percent_OffsetRegion)) or
        (Point_at1Wave*(3-Percent_OffsetRegion)<i<Point_at1Wave*(3+0*Percent_OffsetRegion))):
            VInteg=VInteg+V[i]*VSync[i]
            i_OffsetRegion+=1
    
    LockinValueTimeAve=LockinValue/Time[NPoint-1]
    VInteg=VInteg/Time[NPoint-1]*(NPoint/i_OffsetRegion)

    return LockinValueTimeAve,VLockin,VInteg,VCurrent,Time,NPoint

def CalEnergyLevel(mF, B):
    mu0=4*math.pi*1e-7 #H/m
    muB=927.401e-26 #J/T
    gI=-0.0002936400
    ge=2.002319 #ge=gJ in Ino silde
    I=5./2. #85Rb spin
    muHe=-1.074617e-26 #J/T
    A=1.01191e9 #Hz 85Rb Hyperfine constant
    h=6.626e-34 #J/s
    DeltaEperh=3035.73e6
    epsilon=(ge-gI)/(DeltaEperh*h)*muB*B
    DeltaE=gI*muB*B*mF/h+DeltaEperh/2*(1+4*mF/(2*I+1)*epsilon+epsilon**2)**0.5
    return DeltaE


    
if __name__ == '__main__':
    print(rm.list_resources())
    MODE="Lockin" #"PeakDetect"
    
    InitialSetFM()
    InitialSetOsc("A")
    Vpp=0
    Vpp=1
    
    FreqEPR=iFreq
    VCurrenti=0
    CurrentCorrection=1
    VCurrentMean=0
    VCurrentCount=15
    VCurrentList=[0 for i in range(VCurrentCount)]
    itime = time.time()
    FG.write("OUTPut:STATe ON")
    
    for j in range(10000):
        print("============= %dth measurement :: Initial Frequency : %f===============" %(j,FreqEPR))
        
        DeltaFreq=iDeltaFreq
        flag=0
        i=0
        VCurrentMean=0
        if(MODE=="Lockin"):
                SetFM(FreqEPR,DeltaFreq)
                Lockin,V,VInteg,VCurrent,Time,NPoint=GetEPRFreqLockin(FreqEPR, DeltaFreq)
                if(j==0): VCurrenti=VCurrent
                
                VCurrentList[j%VCurrentCount]=VCurrent
                if(j>VCurrentCount):
                    for l in range(VCurrentCount): VCurrentMean=VCurrentMean+VCurrentList[l]
                    VCurrentMean=VCurrentMean/(VCurrentCount)
                else: VCurrentMean=VCurrenti
                print(VCurrentMean)
                CurrentCorrection=1+(VCurrentMean-VCurrenti)/VCurrenti
                fB1=CalEnergyLevel(3,2e-3)-CalEnergyLevel(2,2e-3)
                fB2=CalEnergyLevel(3,2e-3*CurrentCorrection)-CalEnergyLevel(2,2e-3*CurrentCorrection)
                FreqCorrection=(fB2-fB1)
                factor=abs(Lockin)
                Henka=Lockin*10
                
                if(abs(Henka)>1e4):
                    Henka=Henka/100

                if(abs(Henka)>1e3):
                    Henka=Henka/10

                FreqEPR=(FreqEPR-Henka)
                FreqCorrectionRatio=1+(FreqCorrection)/FreqEPR
                FreqEPRCorrected=FreqEPR*1/FreqCorrectionRatio
                print("Mean(V*VSync)= %f" %(Lockin))
                print("%dth Loop :: Frequency : %f   Henka : %f  factor : %f  VInteg : %f" %(j,FreqEPR,Henka,factor, VInteg))
                print("FreqCorrection : %f   FreqCorrectionRatio : %f  FrequencyCorrected : %f" %(FreqCorrection,FreqCorrectionRatio,FreqEPRCorrected))
                
        f=open(FreqValue_path + argvs[1],"a")
        f.write("%f %f %f\n" %(FreqEPRCorrected, FreqEPR, VCurrentMean))
        f.close()
        print("wating next measurement...")
    FG.write("OUTPut:STATe OFF")
    CloseDevices()