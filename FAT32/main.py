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
        return full_name
    else:
        if entry[i + 11] == 0x10:
            full_name = entry[i: i + 11].decode('ascii').strip()
        else:
            part1 = entry[i: i + 8].decode('ascii').strip()
            part2 = entry[i + 8: i + 11].decode('ascii').strip()
            full_name = part1 + "." + part2
        return full_name

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
            name = read_entry(directoryEntry, i)
            print(indent + "|-- " + name + ", (Sector) " + str(root_dir_sector))
            subdirectory_cluster = entry[26] + (entry[27] << 8) + (entry[20] << 16) + (entry[21] << 24)
            printFolderTree(subdirectory_cluster, indent + "|   ", f, bootSector)

        if entry[11] != 0x10:
            name = read_entry(directoryEntry, i)
            extension = entry[8:11].decode('ascii').strip()
            file_size = int.from_bytes(entry[28:32], byteorder='little', signed=False)

            print(indent + "|-- " + name + ", (Sector) " + str(root_dir_sector))
            if extension == "TXT":
                startingCluster = entry[26] + (entry[27] << 8) + (entry[20] << 16) + (entry[21] << 24)
                file_content = readSectors(f, clusterToSector(startingCluster, bootSector), 1)

                print(indent + "|   |__(Size) " + str(file_size) + " byte")
                print(indent + "|   |__(Content) " + file_content.decode('ascii').strip())
            else:
                print(indent + "|   |__(Size) " + str(file_size) + " byte")
                print(indent + "|   |__(Use compatible software to read the content)")

def ReadFAT(disk):
    f = open(disk, 'rb')
    bootSector = readSectors(f, 0, 1)

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

    print("Số bytes trên 1 sector ", bytesPerSector)
    print("Số sector trên 1 cluster ", sectorPerCluster)
    print("Số sector để dành ", reservedSectorCount)
    print("Số lượng FATs ", numberOfFATs)
    print("Số lượng sector trên 1 volume ", totalSectorCount)
    print("Số sector trên 1 FAT ", sectorPerFAT)
    print("Chỉ số cluster đầu tiên của rdet ", rootCluster)
    print("Tên loại FAT ", ascii_fatType)

    print("****************************")
    print("Folder tree")
    print("****************************")
    printFolderTree(rootCluster, "", f, bootSector)

if __name__ == "__main__":
    print("FIT HCMUS - FILE MANAGEMENT SYSTEM")
    print("****************************")
    print("* 22127201 - Vo Hoang Anh Khoa *")
    print("****************************")
    volumes = [chr(x) + ":" for x in range(65, 91) if os.path.exists(chr(x) + ":")]
    print("Available volumes:")
    for i in range(len(volumes)):
        print(f"{i + 1}/", volumes[i])

    print("Choose a volume to explore:")
    choice = int(input())
    volume = volumes[choice - 1]
    disk = '\\\\.\\' + volume

    ReadFAT(disk)
