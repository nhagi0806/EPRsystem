import os
import Config as conf
import re

def addHeader(filename):
    if os.path.exists(filename):
        return False
    else:
        return True

        
def isEven(data):
    if data % 2 == 0:
        return True
    else:
        return False
    

def GetAndSortBinFileList():
    extension = '.bin'
    # Get file list
    file_list = [f for f in os.listdir(conf.DataPath) if f.endswith(extension)]
    
    # Obtain date/time information contained in file names and store it in the dictionary
    file_info = {}
    for filename in file_list:
        match = re.search(r'\d{8}_\d{4}_\d{1}', filename) # ex) YYYYMMDD_HHMM_1.bin
        if match==None:
            match = re.search(r'\d{4}', filename) # ex) 0001.bin
        if match:
            file_info[filename] = match.group(0)

    # Sort file names
    sorted_file_list = sorted(file_info.keys(), key=lambda x: file_info[x])
    return sorted_file_list
    


def GetMaxFileNumber():
    extension = '.bin'
    pattern = re.compile(r'\d{4}\.bin$')
    files = [f for f in os.listdir(conf.DataPath) if f.endswith(extension) and pattern.match(f)]
    numbers = [int(f.split('.')[0]) for f in files]
    vmax = 0
    print(numbers)
    if not numbers:
        vmax = 0
    else:
        vmax = max(numbers)
    return vmax