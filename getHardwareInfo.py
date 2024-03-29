# This script only works on WINDOWS with NVIDIA GPUs.
from math import ceil, floor
from subprocess import check_output


# ---- CPU ----
def getCPU():
    try:
        return check_output(["wmic","cpu","get", "name"]).decode().strip().split("\n")[1]
    except Exception as e:
        return str(e)


# ---- GPU ----
# only works for NVIDIA GPU
def getGPU():
    try:
        line_as_bytes = check_output("nvidia-smi -L", shell=True)
        line = line_as_bytes.decode("ascii")
        _, line = line.split(":", 1)
        line, _ = line.split("(")
        gpuModelName = line.strip()
        gpuMemory = getGPUMemory()
        
        return gpuModelName + " (" + gpuMemory + ")"
    except Exception as e:
        return str(e)

# only works for NVIDIA GPU
def getGPUMemory():
    try:
        command = "nvidia-smi --query-gpu=memory.free --format=csv"
        memory_free_info = check_output(command.split()).decode('ascii').split('\n')[:-1][1:]
        memory_free_values = [int(x.split()[0]) for i, x in enumerate(memory_free_info)]
        
        # dirty way to get correct memory amount in GB
        approxMemory = ceil(memory_free_values[0] * 1.1)
        memInGb = 0
        while True:
            approxMemory -= 1000
            memInGb += 1
            if approxMemory < 1000:
                break
        memInGb = str(memInGb)
        
        return memInGb + " GB Memory"
    except Exception as e:
        return str(e)


# ---- RAM ----
def getRAM():
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
def getMainboard():
    try:
        # Run the command to get the mainboard model
        manufacturer = check_output(["wmic", "baseboard", "get", "Manufacturer"]).decode().split("\n")[1].strip()
        model = check_output(["wmic", "baseboard", "get", "product"]).decode().split("\n")[1]
        
        # The result will be a string with the format "Product\nModel\n", so we split it into lines and take the second line
        return manufacturer + " " + model
    except Exception as e:
        return str(e)


# ---- Disks ----
def getDisks():
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
    print("CPU:\t\t"        + getCPU())
    print("GPU:\t\t"        + getGPU())
    print("Mainboard:\t"    + getMainboard())
    print("RAM:"            + getRAM())
    print("Disks:"          + getDisks())


main()
