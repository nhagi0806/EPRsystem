import visa
import ROOT
from array import array
import time
import datetime
import csv

rm = visa.ResourceManager()

#Parameters
#FG=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")
FG=rm.open_resource("USB0::0x0D4A::0x000D::9217876::INSTR")
Osc = rm.open_resource("USB0::2391::5989::MY50070140::INSTR")
#Osc = rm.open_resource("USB0::0x0957::0x1765::MY50070140::INSTR")

Osc.timeout = 1000          #time out time (ms)
Threthold=0.05              #Volt
ChSignal=1                  #channel of the signal input
ChRF=2                      #channel of the RF input from the function generator
ChSync=3                    #channel of the sync out from the function generator

#ModulationFunc="TRIangle"
ModulationFunc="PRAMP"
#ModulationFunc="SIN"
ModulationFreq=1000           #Hz Modulation frequency
iFreq=9.25e6             #Hz Initial central value of the frequency
iDeltaFreq=iFreq*0.02  #Hz Initial amplitude of the deviation 
Voltage=20           #Volt

Osc.write(":RUN")
Osc.write(":TRIGger:SWEep AUTO")
TOrigin=float(Osc.query("WAVeform:XORigin?"))
TReference=float(Osc.query("WAVeform:XREFerence?"))
TIncrement=float(Osc.query("WAVeform:XINCrement?"))

def InitialSetFM():
    FG.write(":Source1:FM:State ON")
    FG.write(":Source1:FM:Source Internal")
    FG.write(":Source1:FM:Internal:Function:Shape %s" %ModulationFunc)
    FG.write(":Source1:Voltage %f" %Voltage)
    FG.write(":Source1:FM:Internal:Frequency %fHZ" %(ModulationFreq))
    FG.write(":Source1:Frequency %fHZ" %(iFreq))
    FG.write(":Source1:FM:Deviation %fHZ" %(iDeltaFreq))
        
def SetFM(Freq,Deltafreq):
    FG.write(":Source1:Frequency %fHZ" %(Freq))
    FG.write(":Source1:FM:Deviation %fHZ" %(Deltafreq))

def CloseDevices():
    FG.close()
    Osc.close()

def GetSaveFileFormat():
    print(Osc.query("Save:Filename?"))
    print(Osc.query(":SAVE:WAVeform:FORMat?"))
    print(Osc.query(":SAVE:WAVeform:Length?"))
    print(Osc.query(":SAVE:WAVeform:SEGMented?"))
    
def SetOscFormat(channel):
    #Osc.write(":TRIGger:SWEep AUTO")
    Osc.write(":TIMebase:RANGe %f" %(1./ModulationFreq))
    Osc.write(":TRIGger:SWEep Normal")
    #Osc.write(":ACQuire:TYPE Normal")
    Osc.write(":ACQuire:TYPE Average")
    Osc.write(":MTESt:AVERage:COUNt 200")
    Osc.write(":ACQuire:COMPlete 100")
    #Osc.write(":DIGitize CHANnel%d" %(channel))
    Osc.write(":WAVeform:SOURce CHANnel%d" %(channel))
    Osc.write(":WAVeform:FORMat BYTE")
    Osc.write(":WAVeform:FORMat ASCII")
    Osc.write(":WAVeform:POINts:MODE Maximum")
    Osc.write(":WAVeform:POINts 1000")
    
def GetEPRFreq(Freq, DeltaFreq):
    Osc.write(":RUN")
    #Osc.write(":STOP")
    #Osc.write(":DIGitize CHANnel")
    #Osc.write(":DIGitize CHANnel1") 
    #Osc.write(":DIGitize CHANnel3")
    #Osc.write(":DIGitize CHANnel2")
    
    SetOscFormat(1)
    time.sleep(2)
    value=Osc.query(":WAVeform:DATA?")

    V=value.split(",")
    V[0]=V[0][10:]
    V=list(map(float, V))
    NPoint=len(V)
    
    SetOscFormat(3)
    value2=Osc.query(":WAVeform:DATA?")
    VSync=value2.split(",")
    VSync[0]=VSync[0][10:]
    VSync=list(map(float, VSync))
    
    Time=[(i-TReference)*TIncrement+TOrigin for i in range(NPoint)]
    
    tmpmax=0
    VSyncEPR=0
    NEPRSignal=500
    TimeEPRSignal=0
    for i in range(NPoint):
        if(V[i]>tmpmax):
            tmpmax=V[i]
            NEPRSignal=i
            TimeEPRSignal=Time[NEPRSignal]
            VSyncEPR=VSync[NEPRSignal]
            FreqEPR=Freq+VSyncEPR*DeltaFreq/3. #Convert Syncout volatge to frequancy:: MaxVolatge of Syncout is 3V
    print("MaxVolatage : %f  TimeEPR : %f" %(tmpmax, TimeEPRSignal))
    print("EPR N : %d  EPR Volatge : %f DeltaFreqency : %f  EPR Frequancy : %f" %(NEPRSignal, VSyncEPR,DeltaFreq, FreqEPR))
   
    return FreqEPR, V, VSync, Time, NPoint


def GetEPRFreqLockin(Freq, DeltaFreq):
    Osc.write(":RUN")
    #Osc.write(":STOP")
    #Osc.write(":DIGitize CHANnel")
    Osc.write(":DIGitize CHANnel1") 
    Osc.write(":DIGitize CHANnel3")
    #Osc.write(":DIGitize CHANnel2")
    
    SetOscFormat(1)
    value=Osc.query(":WAVeform:DATA?")
    V=value.split(",")
    V[0]=V[0][10:]
    V=list(map(float, V))
    NPoint=len(V)
    
    SetOscFormat(3)
    value2=Osc.query(":WAVeform:DATA?")
    VSync=value2.split(",")
    VSync[0]=VSync[0][10:]
    VSync=list(map(float, VSync))
    
    Time=[(i-TReference)*TIncrement+TOrigin for i in range(NPoint)]
    
    tmpmax=0
    FreqEPR=iFreq
    VSyncEPR=0
    NEPRSignal=500
    TimeEPRSignal=0
    LockinValue=0;
    VLockin=[]
    for i in range(NPoint):
        LockinValue=LockinValue+V[i]*VSync[i]
        VLockin.append(V[i]*VSync[i])
    print("Mean(V*VSync)= %f" %(LockinValue))
   
    return LockinValue,VLockin,Time,NPoint



if __name__ == '__main__':
    print(rm.list_resources())
    MODE="PeakDetect"
    InitialSetFM()
    
    FreqEPR=iFreq
    FG.write("OUTPut:STATe ON")
    for j in range(500):
        DeltaFreq=iDeltaFreq
        FreqEPR=iFreq
        SetFM(FreqEPR,DeltaFreq)
        print("============= %dth measurement :: Initial Frequency : %f===============" %(j,FreqEPR))
        
        for i in range(1):
            if(MODE=="PeakDetect"):
                #time.sleep(1)
                DeltaFreq=DeltaFreq/3 # should be lower than 10
                SetFM(FreqEPR,DeltaFreq)
                #print(FG.query(":Source1:Frequency?"))
                FreqEPR, V, VSync, Time, NPoint=GetEPRFreq(FreqEPR, DeltaFreq)
                #Osc.write(":MEASure:STATistics:RESet") #reset averaging data
                #Osc.write(":MTESt:COUNt:RESet")
            if(MODE=="Lockin"):    
                if(i==0): FreqEPR=iFreq
                Lockin,V,Time,NPoint=GetEPRFreqLockin(FreqEPR, DeltaFreq)
                if(Lockin>0): FreqEPR=FreqEPR+DeltaFreq*(1./((i+2)**2))
                if(Lockin<0): FreqEPR=FreqEPR-DeltaFreq*(1./((i+2)**2))
                SetFM(FreqEPR,DeltaFreq)
        print("Frequency : %f" %(FreqEPR))        
        date = datetime.datetime.now()
        f=open("Test/TestFrequencyLoop3_Ave64Factor3_0719_1.txt","a")
        f.write("%d-%d-%d-%d-%d %f\n" %(date.month,date.day,date.hour,date.minute,date.second, FreqEPR))
        f.close()
        #FG.write("OUTPut:STATe OFF")
        print("wating next measurement...")

    Va=array("d",V)
    VSynca=array("d",VSync)
    Timea=array("d",Time)
    c=ROOT.TCanvas("c","c",500,400)
    g=ROOT.TGraph(NPoint, Timea, Va)
    g2=ROOT.TGraph(NPoint, Timea, VSynca)
    g.SetLineColor(1)
    g2.SetLineColor(2)
    g.SetMarkerStyle(1)
    g2.SetMarkerStyle(1)
    g.SetMarkerSize(2)
    g2.SetMarkerSize(2)
    g2.Draw("APL")
    g.Draw("PLsame")

    c.Update()
    FG.write("OUTPut:STATe OFF")
        
    """
    SetOscFormat(3)
    value3=Osc.query(":WAVeform:DATA?")
    V2=value2.split(",")
    V2[0]=V2[0][10:]
    V2=list(map(float, V2))
    V2a=array("d",V2)
    g2=ROOT.TGraph(NPoint, Timea, V2a)
    g2.Draw("APL")
    g2.SetLineColor(2)
    c.Update()
    """
    CloseDevices()
        
            
            
