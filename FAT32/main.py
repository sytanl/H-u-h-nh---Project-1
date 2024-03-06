import os

#read from sectorStart to sectorStart + numberSector return  number of bytes 
def readSectors(file, sectorStart, numberSector, bytesPersector = 512):
    file.seek(sectorStart * bytesPersector)
    return file.read(numberSector * bytesPersector)

#
def readNumBuffer(buffer, offset, size):
    # Kiểm tra nếu offset không có tiền tố "0x", thêm tiền tố "0x"
    if not offset.startswith("0x"):
        offset = "0x" + offset
    
    # Chuyển offset thành số nguyên
    offset_int = int(offset, 16)
    
    # Lấy phần của buffer từ offset đến offset + size
    sliced_buffer = buffer[offset_int: offset_int + size]
    
    # Đảo ngược thứ tự của mảng buffer
    reversed_buffer = sliced_buffer[::-1]
    
    # Chuyển đổi mảng reversed_buffer thành số nguyên
    result = int.from_bytes(reversed_buffer, byteorder='big')
    
    return result
   
def intToAscii(value):
    try:
        ascii_string = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big').decode('ascii')
        return ascii_string
    except UnicodeDecodeError:
        return "Unable to decode as ASCII"
def clusterToSector(cluster):
    return (cluster - 2) * sectorPerCluster + reservedSectorCount + (numberOfFATs * sectorPerFAT)

def printFolderTree(cluster, indent, f):
    # Read the directory entry for the given cluster
    directoryEntry = readSectors(f, clusterToSector(cluster), 1)

    # Loop through each directory entry
    for i in range(0, bytesPerSector * sectorPerCluster, 32):
        # Read the current and next entries
        entry = directoryEntry[i:i+32]
        next_entry = directoryEntry[i+32:i+64]

        # Get the first byte of the entry
        firstByte = entry[0]

        # Check if the first byte is 0x00, which means the entry is empty
        if firstByte == 0x00:
            break

        # Check if the first byte is 0xE5, which means the entry is deleted
        if firstByte == 0xE5:
            continue

        # Check if the first byte is 0x2E, which means the entry is a dot entry
        if firstByte == 0x2E:
            continue

        # Check if the first byte is 0x0F, which means the entry is a long file name entry
        if firstByte == 0x0F:
            continue

        # Check if the entry is a directory
        if entry[11] == 0x10:
            # Print the name of the directory
            name = entry[0:11].decode('ascii').strip()
            print(indent + "|-- " + name)

            # Get the cluster of the directory
            subdirectoryCluster = entry[26] + (entry[27] << 8) + (entry[20] << 16) + (entry[21] << 24)

            # Recursively print all subfolders and files of the directory
            printFolderTree(subdirectoryCluster, indent + "|   ", f)

        # Check if the entry is a file
        if entry[11] != 0x10:
            # Extract the name and extension from the entry
            name = entry[0:8].decode('ascii').strip()
            extension = entry[8:11].decode('ascii').strip()

            # Combine name and extension in name.extension format
            file_name = f"{name}.{extension}"

            # Print the name of the file on a single line
            print(indent + "|-- " + file_name)
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


    f = open(disk, 'rb')
    
    bootSector = readSectors(f, 0, 1)

    #số bytes trên 1 sector

    bytesPerSector = readNumBuffer(bootSector, "0x0B", 2)

    print("Số bytes trên 1 sector ", bytesPerSector)

    #Số sector trên 1 cluster

    sectorPerCluster = readNumBuffer(bootSector, "0x0D", 1)

    print("Số sector trên 1 cluster ", sectorPerCluster)

    #Số sector dành cho reserved area

    reservedSectorCount = readNumBuffer(bootSector, "0x0E", 2)

    print("Số sector để dành ", reservedSectorCount)

    #Số lượng FATs

    numberOfFATs = readNumBuffer(bootSector, "0x10", 1)

    print("Số lượng FATs ", numberOfFATs)

    #Số lượng sector trên 1 volume

    totalSectorCount = readNumBuffer(bootSector, "0x13", 4)

    print("Số lượng sector trên 1 volume ", totalSectorCount)

    #Số sector trên 1 FAT

    sectorPerFAT = readNumBuffer(bootSector, "0x24", 4)

    print("Số sector trên 1 FAT ", sectorPerFAT)

    #Chỉ số cluster đầu tiên của rdet

    rootCluster = readNumBuffer(bootSector, "0x2C", 4)

    print("Chỉ số cluster đầu tiên của rdet ", rootCluster)

    #Tên loại FAT tìm trong boot sector, chuyển sang ascii

    fatType = readNumBuffer(bootSector, "0x52", 8)
    ascii_fatType = intToAscii(fatType)
    ascii_fatType = ascii_fatType[::-1]
    #reverse fatType

    print("Tên loại FAT ", ascii_fatType)

    
    print("****************************")
    print("Folder tree")
    print("****************************")
    printFolderTree(rootCluster, "", f)

    

    