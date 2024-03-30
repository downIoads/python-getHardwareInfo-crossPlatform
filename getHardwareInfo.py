from csv import DictReader
from math import ceil, floor
from os import curdir
from platform import system # detect which OS is running
from plistlib import loads # parse darwin plist
from pprint import pprint
from subprocess import check_output

# #### MacOS #### #

# ---- CPU ----
def darwin_getCPU():
    try:
        # get cores amount: system_profiler SPHardwareDataType
        outputPlist = loads(check_output(["system_profiler","SPHardwareDataType","-xml"]))[0]
        cpuCores = str(outputPlist["_items"][0]["number_processors"])

        # sysctl -n machdep.cpu.brand_string
        return check_output(["sysctl","-n","machdep.cpu.brand_string"]).decode().rstrip("\n") + ", Cores: " + cpuCores
    except Exception as e:
        return str(e)


# ---- GPU ----
def darwin_getGPU():
    try:
        # system_profiler SPDisplaysDataType -xml
        outputPlist = loads(check_output(["system_profiler","SPDisplaysDataType","-xml"]))[0] # access index 0 to get dict
        gpuModel = outputPlist["_items"][0]["_name"]
        gpuVRAM = outputPlist["_items"][0]["spdisplays_vram"]
        return gpuModel + ", VRAM: " + gpuVRAM

    except Exception as e:
        return str(e)


# ---- Mainboard ----
def darwin_getMainboard():
    try:
        return ""

    except Exception as e:
        return str(e)


# ---- Mainboard ----
def darwin_getRAM():
    try:
        # system_profiler SPMemoryDataType -xml
        outputPlist = loads(check_output(["system_profiler","SPMemoryDataType","-xml"]))[0] # access index 0 to get dict
        ramModulesList = outputPlist["_items"][0]["_items"]#["_name"]

        totalRAM = 0

        finalString = ""
        for index,ramStick in enumerate(ramModulesList):
            if index != len(ramModulesList) - 1:
                finalString += "\t" + ramStick["dimm_part_number"] + ", Size: " + ramStick["dimm_size"] + ", Type:" + ramStick["dimm_type"] + ", Slot:" + ramStick["_name"] + "\n"
            else:
                finalString += "\t" + ramStick["dimm_part_number"] + ", Size: " + ramStick["dimm_size"] + ", Type:" + ramStick["dimm_type"] + ", Slot:" + ramStick["_name"]
            # get size of current RAM stick as int
            currentRAMModuleCapacity = ""
            for c in ramStick["dimm_size"]:
                if c.isdigit():
                    currentRAMModuleCapacity += c
            totalRAM += int(currentRAMModuleCapacity)

        finalString = "\t" + str(totalRAM) + " GB Combined\n" + finalString

        return finalString

    except Exception as e:
        return str(e)


# ---- Disks ----
def darwin_getDisks():
    try:
        # get list of disks
        diskList = loads(check_output(["diskutil","list","-plist"]))["WholeDisks"]

        # list of lists, each element is a physical disks that contains further information [location, model, size]
        finalDiskInfos = []

        totalStorage = 0

        # get more info from each disk
        for d in diskList:
            # diskutil info -plist disk0
            diskInfo = loads(check_output(["diskutil","info","-plist", d]))

            # only show actual real-world disks
            if diskInfo["VirtualOrPhysical"] != "Physical":
                continue

            diskLocation = diskInfo["DeviceNode"]
            diskName = diskInfo["MediaName"]
            diskSize = str(floor(float(diskInfo["TotalSize"]) / 1024**3))
            totalStorage += int(diskSize)

            finalDiskInfos.append([diskLocation, diskName, diskSize])


        # build final string
        finalString = "\t" + str(totalStorage) + " GB Combined\n"
        for fDisk in finalDiskInfos:
            finalString += "\t" + fDisk[1] + ",\tSize: " + fDisk[2] + " GB, Location: " + fDisk[0] + "\n"
        return finalString

    except Exception as e:
        return str(e)


# #### WINDOWS #### #

# ---- CPU ----
def windows_getCPU():
    try:
       cpuModel = check_output(["wmic","cpu","get", "name"]).decode().strip().split("\n")[1]
       cpuCoresAmount = check_output(["wmic","cpu","get", "NumberOfCores"]).decode().strip().split("\n")[1]
       return cpuModel + ", Cores: " + cpuCoresAmount
    except Exception as e:
        return str(e)


# ---- GPU ----
def windows_getGPU():
    # wmic path win32_VideoController get /FORMAT:CSV # CSV > LIST for parsing
    try:
        gpuInfo = check_output(["wmic","path","win32_VideoController", "get", "/FORMAT:CSV"]).decode().strip().split("\n")

        gpuList = []
        csv = DictReader(gpuInfo)
        for row in csv:
            gpuList.append(dict(row))

        # list of gpus model names (reported memory by "AdapterRAM" is wrong [reports 4gb instead of 12gb for me], so i will use powershell method instead )
        gpuListRelevant = []

        # iterate over gpuList and extract gpu model names
        for gpu in gpuList:
            # Caption might as well be PNPDeviceID
            gpuListRelevant.append(str(gpu["Caption"]))
        
        # get actually accurate GPU VRAM size using powershell
        accurateVRAMStr = ""
        try:
            command = '(Get-ItemProperty -Path "HKLM:\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0*" -Name HardwareInformation.qwMemorySize -ErrorAction SilentlyContinue)."HardwareInformation.qwMemorySize"'
            accurateVRAM = check_output(["powershell", "-Command", command], text=True)
            accurateVRAMStr = str(ceil(float(accurateVRAM) / 1024**3))
        except Exception as e:
            pass

        # build final string
        finalString = ""
        for index, curGPU in enumerate(gpuListRelevant):
            if index == 0 and accurateVRAMStr != "" : # first GPU will be dedicated gpu if it exists
                finalString += curGPU + " (VRAM: " + accurateVRAMStr + " GB)\n"
            else:
                finalString += "\t\t" + curGPU + "\n"

        return finalString.rstrip("\n")
    except Exception as e:
        return str(e)


# ---- RAM ----
def windows_getRAM():
    try:
        # wmic memorychip get manufacturer
        ramManuList = check_output(["wmic","memorychip","get", "manufacturer"]).decode().strip().replace('\r\r', '').split("\n")[1:]
        cleanedManuList = [r.rstrip() for r in ramManuList]
        
        ramModuleAmount = str(len(ramManuList))
        
        ramCapacity = check_output(["wmic","memorychip","get", "capacity"]).decode().strip().replace('\r\r', '').split("\n")[1:]
        ramCapacityCleaned = [(int(float(r.rstrip()) / 1024**3)) for r in ramCapacity]
        totalRAM = str(sum(ramCapacityCleaned)) 

        finalString = "\t\t" + totalRAM + " GB Combined\n"
        for i in range(len(ramManuList)):
            finalString += "\t\t" + cleanedManuList[i] + ",\tSize: " + str(ramCapacityCleaned[i]) + " GB"
            # no newline at the end
            if i < len(ramManuList)-1:
                finalString += "\n"
          
        return finalString
    except Exception as e:
        return str(e)


# ---- MAINBOARD ----
def windows_getMainboard():
    try:
        # Run the command to get the mainboard model
        manufacturer = check_output(["wmic", "baseboard", "get", "Manufacturer"]).decode().split("\n")[1].strip()
        model = check_output(["wmic", "baseboard", "get", "product"]).decode().split("\n")[1]
        
        # The result will be a string with the format "Product\nModel\n", so we split it into lines and take the second line
        return manufacturer + " " + model
    except Exception as e:
        return str(e)


# ---- Disks ----
def windows_getDisks():
    # wmic diskdrive get model,size
    try:
        diskModels = check_output(["wmic", "diskdrive", "get", "model"]).decode().strip().replace('\r\r', '').split("\n")[1:]
        diskSizes = check_output(["wmic", "diskdrive", "get", "size"]).decode().strip().replace('\r\r', '').split("\n")[1:]
        
        
        # clean data
        diskModelsCleaned = [m.rstrip() for m in diskModels]
        diskSizesCleaned = [floor(float(m.rstrip()) / 1000000000) for m in diskSizes]
        
        totalStorage = str(sum(diskSizesCleaned))
        
        finalString = "\t\t" + totalStorage + " GB Combined\n"
        for i in range(len(diskModelsCleaned)):
            if i != 0:
                finalString += "\t\t" + diskModelsCleaned[i] + ",\tSize: " + str(diskSizesCleaned[i]) + " GB\n"
            else: # extra tab required for some reason on first iteration
                finalString += "\t\t" + diskModelsCleaned[i] + ",\t\tSize: " + str(diskSizesCleaned[i]) + " GB\n"
        
        return finalString
    except Exception as e:
        return str(e)


def main():
    currentOS = system().lower()
    if currentOS == "darwin":
        print("CPU:\t"          + darwin_getCPU())
        print("GPU:\t"          + darwin_getGPU())
        #print("Mainboard:\t"   + darwin_getMainboard()) # no idea if this is possible
        print("RAM:"            + darwin_getRAM())
        print("Disks:"          + darwin_getDisks())
    elif currentOS == "linux":
        print("Linux support will be added soon.. (surely)")
        return
    elif currentOS == "windows":
        print("CPU:\t\t"        + windows_getCPU())
        print("GPU:\t\t"        + windows_getGPU())
        print("Mainboard:\t"    + windows_getMainboard())
        print("RAM:"            + windows_getRAM())
        print("Disks:"          + windows_getDisks())
    else:
        print("Unsupported OS.")


main()
# won't be fixed: macos cant determine mainboard model AFAIK
# won't be fixed: windows version shows advertised storage amount, but macos version shows actual storage amount. who cares, lets not confuse the windows enjoyers
