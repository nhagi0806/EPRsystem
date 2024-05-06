"""
今までGetEPRFreqLockinを使う直前でAverageSetOscしていたが、これだとsweepしている振動磁場まで
averageしていて時間が無駄だった。
そのためGetEPRFreqLockinの中にAverageSetOscを入れて、PDの信号のみaverageするようにした。
"""



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
#FG=rm.open_resource("USB0::0x0D4A::0x000D::9122074::INSTR")#Harada-san's FG
#Osc = rm.open_resource("USB0::2391::5989::MY50070140::INSTR")
Osc = rm.open_resource("USB0::0x0957::0x1798::MY61410321::INSTR")#New Keysight Oscillo  
#Meter = rm.open_resource("GPIB0::16::INSTR")
Meter = rm.open_resource("ASRL5::INSTR")
#Osc = rm.open_resource("USB0::0x0957::0x1765::MY50070140::INSTR")

Osc.timeout = 1000000          #time out time (ms)
Threthold=0.05              #Volt
ChSignal=1                  #channel of the signal input
#ChRF=2                      #channel of the RF input from the function generator
ChSync=3                    #channel of the sync out from the function generator
ChTrigger=ChSync
#ChMonitor=2

#ModulationFunc="TRIangle"
ModulationFunc="PRAMP"
#ModulationFunc="SIN"
Function="SIN"
#ModulationFreq=60       #Hz Modulation frequency
ModulationFreq=1001       #Hz Modulation frequency
#iFreq= 7334000             #Hz Initial central value of the frequency
#iFreq= 7270000
#iFreq= 7260000
#iFreq= 5925000 #B_0 0.55A,1.23 mT
#iFreq= 7348600       #10/18
#iFreq= 7385000
#iFreq= 7300000
#iFreq= 7225000
#iFreq= 7158000
#iFreq= 7164000
iFreq= 7268000
#iFreq= 7155000
#iFreq= 7212000
#iFreq= 7405000 #120度
#iFreq= 7418000 #110度
#iFreq= 7427000 #100度
#iFreq= 7453000 #
#iFreq= 7358000 
#iFreq= 7334600             #Hz Initial central value of the frequency
iDeltaFreq=1e6*0.5 #iFreq*0.03  #Hz Initial amplitude of the deviation 
#iDeltaFreq=1e6*0.5
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

#Meter.write(":Current:DC:NPLCycles 10") #integration time of multimeter

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
    """
    if(NorA=="N"): Osc.write(":ACQuire:TYPE Normal")
    if(NorA=="A"):
        Osc.write(":ACQuire:TYPE Average")
        Osc.write(":MTESt:AVERage:COUNt %d" %(Avecount))
    """
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
        #print("writeしたよ")

def SetFM(Freq,Deltafreq):
    FG.write(":Source1:Frequency %fHZ" %(Freq))
    FG.write(":Source1:FM:Deviation %fHZ" %(Deltafreq))

def CloseDevices():
    FG.close()
    Osc.close()

def GetEPRFreqLockin(Freq, DeltaFreq):
    #Osc.write(":RUN")
    #Osc.write(":STOP")
    #Osc.write(":DIGitize CHANnel")
    #Osc.write(":DIGitize CHANnel1") 
    #Osc.write(":DIGitize CHANnel3")
    #Osc.write(":DIGitize CHANnel2")

    AverageSetOsc("A", NAverage)
    Osc.write(":WAVeform:SOURce CHANnel1")
    print("wrote")
    #value=Osc.query_binary_values(":WAVeform:DATA?", datatype = 'B', delay = Query_delay)
    value=Osc.query(":WAVeform:DATA?", delay = Query_delay)
    #print(value)
    V=value.split(",")
    #V=value
    V[0]=V[0][10:]
    V=list(map(float, V))
    NPoint=len(V)

    AverageSetOsc("N", 0)
    Osc.write(":WAVeform:SOURce CHANnel%d"%(ChSync))
    value2=Osc.query(":WAVeform:DATA?")
    VSync=value2.split(",")
    VSync[0]=VSync[0][10:]
    VSync=list(map(float, VSync))


    """
    Osc.write(":WAVeform:SOURce CHANnel4")
    value3=Osc.query(":WAVeform:DATA?")
    VCurrent=value3.split(",")
    VCurrent[0]=VCurrent[0][10:]
    VCurrent=list(map(float, VCurrent))
    """
    VCurrent=1#Meter.query(":Measure:Current?")  
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
    LockinValue=0;
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
        #VCurrentMean=VCurrentMean+VCurrent[i]
    
    LockinValueTimeAve=LockinValue/Time[NPoint-1]
    #LockinValueTimeAve=tmpmax*VSyncEPR
    #VCurrentMean=VCurrentMean/NPoint
    #print("Mean(V*VSync)= %f" %(LockinValueTimeAve))
    VInteg=VInteg/Time[NPoint-1]*(NPoint/i_OffsetRegion)
    # VInteg=VInteg/Time[NPoint-1]
    #LockinValueTimeAve=LockinValueTimeAve-VInteg

    return LockinValueTimeAve,VLockin,VInteg,VCurrent,Time,NPoint

def CalEnergyLevel(mF, B):
    mu0=4*math.pi*1e-7 #H/m
    muB=927.401e-26 #J/T
    gI=-0.0002936400
    ge=2.002319 #ge=gJ in Ino silde
    I=5./2. #85Rb spin
    muHe=-1.074617e-26 #J/T
    A=1.01191e9 #Hz 85Rb Hyperfine constant
    #B=2e-3#1.9e-3 #T
    h=6.626e-34 #J/s
    DeltaEperh=3035.73e6
    epsilon=(ge-gI)/(DeltaEperh*h)*muB*B
    
    #DeltaE=-DeltaEperh/(2*(2*I+1))+gI*muB*B*mF+DeltaEperh*(1+4*mF/(2*I+1)*epsilon+epsilon**2)**0.5
    DeltaE=gI*muB*B*mF/h+DeltaEperh/2*(1+4*mF/(2*I+1)*epsilon+epsilon**2)**0.5
    return DeltaE


    
if __name__ == '__main__':
    print(rm.list_resources())
    MODE="Lockin" #"PeakDetect"
    
    InitialSetFM()
    #InitialSetOsc("N",64)
    InitialSetOsc("A")
    Vpp=0
    #for i in range(20): Vpp=Vpp+float(Osc.query(":Measure:VPP? Channel1"))
    #Vpp=Vpp/20
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
        #Osc.write(":TRIGger:SWEep AUTO")
        #GetSaveFileFormat()
        
        DeltaFreq=iDeltaFreq
        flag=0
        i=0
        VCurrentMean=0
        if(MODE=="Lockin"):
                #if(j!=0 and i==0):
                #    print(j,i)
                #    i=i+19
                SetFM(FreqEPR,DeltaFreq)
                #InitialSetOsc("A",16*2)
                #AverageSetOsc("A", 16*3)
                Lockin,V,VInteg,VCurrent,Time,NPoint=GetEPRFreqLockin(FreqEPR, DeltaFreq)
                #print("got EPRfreq")
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
                #Henka=Lockin/Vpp*factor
                #Henka=Lockin*factor
                #Henka=Lockin*factor*1
                Henka=Lockin*10
                #Henka=Lockin*factor*10
                #Henka=abs(Lockin)/Lockin

                """
                if(Henka<0):          #電源ノイズによるブレは何故かEPR freq.を上振れさせやすいため、バイアスをかけている。物理的な意味はない。
                    Henka=Henka/4
                """
                
                if(abs(Henka)>1e4):
                    Henka=Henka/100

                if(abs(Henka)>1e3):
                    Henka=Henka/10
                
                """
                if(abs(Henka)>1e6):
                    Henka=Henka/1000

                if(1e6>abs(Henka)>5e5):
                    Henka=Henka/100

                if(5e5>abs(Henka)>1e4):
                    Henka=Henka/80

                elif(1e4>abs(Henka)>3e3):
                    Henka=Henka/70

                elif(3e3>abs(Henka)>2e3):
                    Henka=Henka/50

                
                elif(2e3>abs(Henka)>1e3):
                    Henka=Henka/120.
                """

                FreqEPR=(FreqEPR-Henka)
                FreqCorrectionRatio=1+(FreqCorrection)/FreqEPR
                FreqEPRCorrected=FreqEPR*1/FreqCorrectionRatio
                print("Mean(V*VSync)= %f" %(Lockin))
                print("%dth Loop :: Frequency : %f   Henka : %f  factor : %f  VInteg : %f" %(j,FreqEPR,Henka,factor, VInteg))
                print("FreqCorrection : %f   FreqCorrectionRatio : %f  FrequencyCorrected : %f" %(FreqCorrection,FreqCorrectionRatio,FreqEPRCorrected))
                
        '''
        while(i<1):
            if(MODE=="PeakDetect"):
                #time.sleep(1)
                DeltaFreq=DeltaFreq/3 # should be lower than 10
                SetFM(FreqEPR,DeltaFreq)
                FreqEPR, V, VSync, Time, NPoint=GetEPRFreq(FreqEPR, DeltaFreq)
                Osc.write(":MEASure:STATistics:RESet") #reset averaging data
                Osc.write(":MTESt:COUNt:RESet")
            if(MODE=="Lockin"):
                #if(j!=0 and i==0):
                #    print(j,i)
                #    i=i+19
                SetFM(FreqEPR,DeltaFreq)
                #InitialSetOsc("A",16*2)
                AverageSetOsc("A",16*2)
                time.sleep(SleepTime)
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
                """
                if(abs(Lockin)<20): factor=1
                if(abs(Lockin)>20 and abs(Lockin)<150): factor=2
                if(abs(Lockin)>150 and abs(Lockin)<1000): factor=10
                if(abs(Lockin)>1000): factor=20
                """
                """
                if(abs(Lockin)>20 and abs(Lockin)<100): factor=10
                if(abs(Lockin)>100 and abs(Lockin)<200): factor=20
                if(abs(Lockin)>200): factor=30
                #if(abs(Lockin)>100 and abs(Lockin)<200): factor=14
                #if(abs(Lockin)>200 and abs(Lockin)<1000): factor=10
                #if(abs(Lockin)>1000): factor=20
                """
                factor=abs(Lockin)
                #Henka=Lockin/Vpp*factor
                #Henka=Lockin*factor
                #Henka=Lockin*factor*2
                Henka=Lockin*factor*200
                #Henka=abs(Lockin)/Lockin
                if(abs(Henka)>40e3):
                    Henka=Henka/100.
                
                FreqEPR=(FreqEPR+Henka)
                FreqCorrectionRatio=1+(FreqCorrection)/FreqEPR
                FreqEPRCorrected=FreqEPR*1/FreqCorrectionRatio
                print("Mean(V*VSync)= %f" %(Lockin))
                print("%dth Loop :: Frequency : %f   Henka : %f  factor : %f" %(j,FreqEPR,Henka,factor))
                print("FreqCorrection : %f   FreqCorrectionRatio : %f  FrequencyCorrected : %f" %(FreqCorrection,FreqCorrectionRatio,FreqEPRCorrected))
                i=i+1
        '''
        #date = datetime.datetime.now()
        
        #f=open("Test/0801_6_Rb87.txt","a")
        f=open(FreqValue_path + argvs[1],"a")
        #f.write("%d-%d-%d-%d-%d %f %f %f\n" %(date.month,date.day,date.hour,date.minute,date.second, FreqEPRCorrected, FreqEPR, VCurrentMean))
        #f.write("%f %f %f %f\n" %(time.time()-itime, FreqEPRCorrected, FreqEPR, VCurrentMean))
        f.write("%f %f %f\n" %(FreqEPRCorrected, FreqEPR, VCurrentMean))
        #f.write("%d-%d-%d-%d-%d %f %f\n" %(date.month,date.day,date.hour,date.minute,date.second, VCurrent, VInteg))
        #f.write("%d-%d-%d-%d-%d %f\n" %(date.month,date.day,date.hour,date.minute,date.second, Lockin/Vpp))
        f.close()
        #FG.write("OUTPut:STATe OFF")
        print("wating next measurement...")
    FG.write("OUTPut:STATe OFF")
    CloseDevices()