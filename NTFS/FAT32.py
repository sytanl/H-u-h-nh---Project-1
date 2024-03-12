import os

def readSectors(file, sectorStart, numberSector, bytesPersector=512):
    file.seek(sectorStart * bytesPersector)
    return file.read(numberSector * bytesPersector)

def readNumBuffer(buffer, offset, size):
    if not offset.startswith("0x"):
        offset = "0x" + offset
    offset_int = int(offset, 16)
    sliced_buffer = buffer[offset_int: offset_int + size]
    reversed_buffer = sliced_buffer[::-1]
    result = int.from_bytes(reversed_buffer, byteorder='big')
    return result

def intToAscii(value):
    try:
        ascii_string = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big').decode('ascii')
        return ascii_string
    except UnicodeDecodeError:
        return "Unable to decode as ASCII"

def clusterToSector(cluster, bootSector):
    bytesPerSector = readNumBuffer(bootSector, "0x0B", 2)
    sectorPerCluster = readNumBuffer(bootSector, "0x0D", 1)
    numberOfFATs = readNumBuffer(bootSector, "0x10", 1)
    sectorPerFAT = readNumBuffer(bootSector, "0x24", 4)
    reservedSectorCount = readNumBuffer(bootSector, "0x0E", 2)
    return (cluster - 2) * sectorPerCluster + reservedSectorCount + (numberOfFATs * sectorPerFAT)

def read_entry(entry, i):
    previous_entry_flag = entry[i + 11 - 32]
    if previous_entry_flag == 0x0F:
        part1 = entry[i + 1 - 32: i + 11 - 32].decode('latin-1', errors='ignore').strip().replace('\xff', '')
        part2 = entry[i + 14 - 32: i + 26 - 32].decode('latin-1', errors='ignore').strip().replace('\xff', '')
        part3 = entry[i + 28 - 32: i + 32 - 32].decode('latin-1', errors='ignore').strip().replace('\xff', '')
        full_name = part1 + part2 + part3
        return full_name + read_entry(entry, i - 32)
    else:
        return ""
    
def classify_file(indent, extension):

    software_name = None
    if (extension == "DOCX"):
        software_name = "Microsoft Word"
    elif (extension == "PDF"):
        software_name = "Adobe Acrobat Reader"
    elif (extension == "XLSX"):
        software_name = "Microsoft Excel"
    elif (extension == "ODS"):
        software_name = "LibreOffice"
    elif (extension == "PPTX"):
        software_name = "Microsoft PowerPoint"
    elif (extension == "JPG"):
        software_name = "Windows Photo Viewer"
    elif (extension == "PNG"):
        software_name = "IrfanView"
    elif (extension == "GIF"):
        software_name = "Web browser"
    elif (extension == "MP4"):
        software_name = "VLC Media Player"
    elif (extension == "MOV"):
        software_name = "QuickTime"
    elif (extension == "AVI"):
        software_name = "KMPlayer"
    elif (extension == "MP3"):
        software_name = "Windows Media Player"
    elif (extension == "WAV"):
        software_name = "Audacity"
    elif (extension == "ZIP"):
        software_name = "WinRAR"
    elif (extension == "RAR"):
        software_name = "7-Zip"
    elif (extension == "7Z"):
        software_name = "7_Zip"
    elif (extension == "HTML"):
        software_name = "Web browser"
    elif (extension == "PY"):
        software_name = "Visual Studio Code"
    elif (extension == "CPP"):
        software_name = "Visual Studio Code"
    else:
        software_name = "compatible software"

    print(indent + f"|   |__(Use {software_name} to read the content)")

def printFolderTree(cluster, indent, f, bootSector):
    directoryEntry = readSectors(f, clusterToSector(cluster, bootSector), 1)
    bytesPerSector = readNumBuffer(bootSector, "0x0B", 2)
    sectorPerCluster = readNumBuffer(bootSector, "0x0D", 1)
    numberOfFATs = readNumBuffer(bootSector, "0x10", 1)
    sectorPerFAT = readNumBuffer(bootSector, "0x24", 4)
    
    for i in range(0, bytesPerSector * sectorPerCluster, 32):
        entry = directoryEntry[i:i + 32]
        next_entry = directoryEntry[i + 32:i + 64]

        if (len(entry) <= 0):
            break

        firstByte = entry[0]
        attributes = entry[11]

        if firstByte == 0x00:
            break

        if firstByte == 0xE5:
            continue

        if firstByte == 0x2E:
            continue

        if attributes == 0x0F:
            continue

        if attributes == 0x08:
            continue

        if attributes & 0x02:
            continue

        first_cluster_root_dir = int.from_bytes(entry[44:48], byteorder='little')
        cluster_size = int.from_bytes(entry[13:14], byteorder='little') * 512
        reserved_sectors = int.from_bytes(entry[14:16], byteorder='little')
        root_dir_sector = reserved_sectors + (first_cluster_root_dir - 2) * cluster_size // 512

        if entry[11] == 0x10:
            if directoryEntry[i + 11 - 32] == 0x0F:
                name = read_entry(directoryEntry, i)
            else:
                name = entry[0:11].decode('ascii').strip()
            print(indent + "|-- " + name + f"(Sector: {root_dir_sector})")
            subdirectory_cluster = entry[26] + (entry[27] << 8) + (entry[20] << 16) + (entry[21] << 24)
            printFolderTree(subdirectory_cluster, indent + "|   ", f, bootSector)

        if entry[11] != 0x10:
            flag = 0
            if directoryEntry[i + 11 - 32] == 0x0F:
                name = read_entry(directoryEntry, i)
                flag = 1
            else:
                name = entry[0:8].decode('ascii').strip()
            extension = entry[8:11].decode('ascii').strip()
            file_size = int.from_bytes(entry[28:32], byteorder='little', signed=False)

            if extension == "TXT":
                print(indent + "|-- " + name + f"(Sector: {root_dir_sector}) " + f" (Size: {file_size / 1024} KB)")
                startingCluster = entry[26] + (entry[27] << 8) + (entry[20] << 16) + (entry[21] << 24)
                file_content = readSectors(f, clusterToSector(startingCluster, bootSector), 1)
                print(indent + "|   |__(Content) " + file_content.decode('ascii').strip())
            else:
                if flag == 1:
                    print(indent + "|-- " + name + f"(Sector: {root_dir_sector}) " + f" (Size: {file_size / 1024} KB)")
                elif flag == 0: 
                    print(indent + "|-- " + name + "." + extension.lower() + f"(Sector: {root_dir_sector}) " + f" (Size: {file_size / 1024} KB)")
                classify_file(indent, extension)


def bootSectorInfo(bootSector):
    bytesPerSector = readNumBuffer(bootSector, "0x0B", 2)
    sectorPerCluster = readNumBuffer(bootSector, "0x0D", 1)
    reservedSectorCount = readNumBuffer(bootSector, "0x0E", 2)
    numberOfFATs = readNumBuffer(bootSector, "0x10", 1)
    totalSectorCount = readNumBuffer(bootSector, "0x13", 4)
    sectorPerFAT = readNumBuffer(bootSector, "0x24", 4)
    rootCluster = readNumBuffer(bootSector, "0x2C", 4)
    fatType = readNumBuffer(bootSector, "0x52", 8)
    ascii_fatType = intToAscii(fatType)
    ascii_fatType = ascii_fatType[::-1]

    print("Bytes per sector:", bytesPerSector)
    print("Bytes per cluster:", sectorPerCluster)
    print("Number of Reserved Sector:", reservedSectorCount)
    print("Number of FAT:", numberOfFATs)
    print("Number Sector in volume:", totalSectorCount)
    print("Sector per FAT:", sectorPerFAT)
    print("First cluster of FAT:", rootCluster)
    print("FAT name:", ascii_fatType)

def readCluster(file, cluster, bootSector):
    bytesPerSector = readNumBuffer(bootSector, "0x0B", 2)
    sectorPerCluster = readNumBuffer(bootSector, "0x0D", 1)
    return readSectors(file, clusterToSector(cluster, bootSector), sectorPerCluster)
def isFolder(entry):
    attributes = entry[11]
    return (attributes & 0x10) != 0

def readName(entry):
    name_bytes = entry[0:8]
    extension_bytes = entry[8:11]

    try:
        name = name_bytes.decode('ascii', errors='replace').strip()
        extension = extension_bytes.decode('ascii', errors='replace').strip()

        full_name = name
        if extension:
            full_name += "." + extension

        return full_name
    except UnicodeDecodeError:
        print("Error decoding name.")
        return ""


def changeDirectory(currentCluster, folderName, file, bootSector):
    clusterSize = readNumBuffer(bootSector, "0x0D", 1) * readNumBuffer(bootSector, "0x0B", 2)
    directory = readCluster(file, currentCluster, bootSector)
    
    folderName = folderName.replace(" ", "")  # Remove white spaces from the input folderName

    for i in range(0, len(directory), 32):
        entry = directory[i:i+32]
        attributes = readNumBuffer(entry, "0x0B", 1)
        firstCluster = readNumBuffer(entry, "0x1A", 2)
        entryName = entry[0:11].decode('ascii').strip()  # Remove white spaces from the entryName
        
        if entry[11] == 0x10 and entryName == folderName.upper():
            return firstCluster
    print("Directory not found.")
    return currentCluster


def ReadFAT(disk):
    f = open(disk, 'rb')
    bootSector = readSectors(f, 0, 1)
    rootCluster = readNumBuffer(bootSector, "0x2C", 4)  
    bootSectorInfo(bootSector)

    #make me a menu with options 1. cd 2. print tree 3.exit
    while True:
        print("****************************")
        print("Menu")
        print("1. Change directory")
        print("2. Print folder tree")
        print("3. Return to root")
        print("4. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            folderName = input("Enter folder name: ")
            rootCluster = changeDirectory(rootCluster, folderName, f, bootSector)
            print(rootCluster)
            #clear the screen
            os.system('cls' if os.name == 'nt' else 'clear')
            #change current f path to the folder
            print("****************************")
            currentFolderName = readName(readCluster(f, rootCluster, bootSector))
            print("Folder changed to " + folderName)


        elif choice == "2":
            #clear the screen
            os.system('cls' if os.name == 'nt' else 'clear')
            print("****************************")
            print("Folder tree")
            print("****************************")
            printFolderTree(rootCluster, "", f, bootSector)
        elif choice == "3":
            rootCluster = readNumBuffer(bootSector, "0x2C", 4)
            print("Folder changed to root")
        elif choice == "4":
            break
        else:
            print("Invalid choice")

def check_fat32(volume_name):
    disk = '\\\\.\\' + volume_name
    f = open(disk, 'rb')
    #return true if it is fat
    bootSector = readSectors(f, 0, 1)
    fatType = readNumBuffer(bootSector, "0x52", 8)
    ascii_fatType = intToAscii(fatType).strip()
    ascii_fatType = ascii_fatType[::-1]
    print(ascii_fatType)
    if ascii_fatType.lower() == "fat32":
        return True
    else:
        return False
