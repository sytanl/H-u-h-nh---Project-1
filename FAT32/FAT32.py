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




    