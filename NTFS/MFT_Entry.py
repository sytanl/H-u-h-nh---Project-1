from datetime import *
from Constant import *

class MFT_Entry:
    def __init__(self, entry_raw, sc, bs) -> None: 
        self.cur_offset = 0
        self.entry_raw = entry_raw
        self.infor = {}
        
        if self.entry_raw[0x0:0x4] == 0xFFFFFFFF:
            raise Exception("Reach MFT end")
        if self.entry_raw[0x16] == 0 or self.entry_raw[0x16] == 2:   
            raise Exception("Skip this entry")
        
        # mft header
        try:
            self.entry_header = {
                "Signature": self.entry_raw[0x0:0x4].decode(),
                "First Offset of Attribute": int.from_bytes(self.entry_raw[0x14:0x16], byteorder='little'),
                "Entry Flag": int.from_bytes(self.entry_raw[0x16:0x18], byteorder='little'),
                "Entry size": int.from_bytes(self.entry_raw[0x1C:0x20], byteorder='little'),
            }
        except Exception as e:
            pass
        
        self.infor["ID"] = int.from_bytes(self.entry_raw[0x2C:0x30], byteorder='little')
        self.cur_offset = self.entry_header['First Offset of Attribute'] # -----------------------------------------------------
        

        # standard information: get created time, modified time, flag 
        self.mft_attr_header = self.extract_attr()
        
        self.cur_offset += self.mft_attr_header['OFFSET TO CONTENT']
        timestamp = int.from_bytes(self.entry_raw[self.cur_offset: self.cur_offset + 8], byteorder='little')
        _time = datetime(1601, 1, 1) + timedelta(microseconds=timestamp / 10)
        self.infor["Created Time"] = _time.strftime("%Y-%m-%d %H:%M:%S")
     
        timestamp = int.from_bytes(self.entry_raw[self.cur_offset + 8: self.cur_offset + 16], byteorder='little')
        _time = datetime(1601, 1, 1) + timedelta(microseconds=timestamp / 10)
        self.infor["Modified Time"] = _time.strftime("%Y-%m-%d %H:%M:%S")
        self.infor["attr_flag"] = NTFSAttribute(int.from_bytes(self.entry_raw[self.cur_offset + 32: self.cur_offset + 36], byteorder='little') & 0xFFFF)
        
        if NTFSAttribute.SYSTEM in self.infor["attr_flag"] or NTFSAttribute.HIDDEN in self.infor["attr_flag"]:
            raise Exception("Skip this entry")
        
        self.cur_offset += self.mft_attr_header["Attribute length"] - self.mft_attr_header['OFFSET TO CONTENT']
        


        # file name: get parent id, file name
        self.mft_attr_header = self.extract_attr()
        
        self.cur_offset += self.mft_attr_header['OFFSET TO CONTENT']
        self.infor["PARENT ID"] = int.from_bytes(self.entry_raw[self.cur_offset: self.cur_offset + 6], byteorder='little')
        self.infor["NAME LENGTH"] = self.entry_raw[self.cur_offset + 64]
        self.infor["FILE NAME"] = self.entry_raw[self.cur_offset + 66: self.cur_offset + 66 + self.infor["NAME LENGTH"] * 2].decode("utf-16le")
        
        if self.infor["FILE NAME"].startswith('$'):
            raise Exception("Skip this entry")
        
        self.cur_offset += self.mft_attr_header["Attribute length"] - self.mft_attr_header['OFFSET TO CONTENT']


        # data  
        self.mft_attr_header = self.extract_attr()
        if self.mft_attr_header['Attribute type'] == 64:
            self.cur_offset += self.mft_attr_header["Attribute length"]
            self.mft_attr_header = self.extract_attr()
        
        # 128 = file, 144 = folder     
        if self.mft_attr_header['Attribute type'] == 128:
            self.infor['Resident'] = True

            if not self.infor["FILE NAME"].endswith('.txt'):
                self.infor['SIZE OF DATA'] = "2"
                self.infor['DATA'] = "=="
            else:
                if self.mft_attr_header["Resident Flag"] == "Resident":
                    offset = int.from_bytes(self.entry_raw[self.cur_offset + 20: self.cur_offset + 21], byteorder='little')
                    self.infor['SIZE OF DATA'] = int.from_bytes(self.entry_raw[self.cur_offset + 16: self.cur_offset + 19], byteorder='little')
                    self.infor['DATA'] = self.entry_raw[self.cur_offset + offset: self.cur_offset + offset + self.infor['SIZE OF DATA']]
                else:
                    data_run_offset = int.from_bytes(self.entry_raw[self.cur_offset + 32: self.cur_offset + 32 + 2], byteorder='little')
                    total_cluster = int.from_bytes(self.entry_raw[self.cur_offset + data_run_offset + 1: self.cur_offset + data_run_offset + 2], byteorder='little')
                    first_cluster = int.from_bytes(self.entry_raw[self.cur_offset + data_run_offset + 2: self.cur_offset + data_run_offset + 4], byteorder='little')
                    self.infor['SIZE OF DATA'] = total_cluster * sc * bs
                    list_sector = []
                    for cluster in range(first_cluster, first_cluster + total_cluster):
                        for i in range(sc):
                            sector = cluster * sc + i
                            list_sector.append(sector)
                    self.infor['DATA'] = list_sector
                    self.infor['Resident'] = False
        
        elif self.mft_attr_header['Attribute type'] == 144:
            self.infor["attr_flag"] |= NTFSAttribute.DIRECTORY
            self.infor['SIZE OF DATA'] = 0
            self.infor['DATA'] = ""
            self.infor['Resident'] = True
       
        del self.entry_raw    

    # read attribute header 
    def extract_attr(self) -> dict:
        header = {
            "Attribute type": int.from_bytes(self.entry_raw[self.cur_offset: self.cur_offset + 4], byteorder='little'),
            "Attribute length": int.from_bytes(self.entry_raw[self.cur_offset + 4: self.cur_offset + 8], byteorder='little'),
            "Resident Flag": "Resident" if int.from_bytes(self.entry_raw[self.cur_offset + 8: self.cur_offset + 9], byteorder='little') == 0 else "Non-resident",
            "Name size": int.from_bytes(self.entry_raw[self.cur_offset + 9: self.cur_offset + 10], byteorder='little'),
            "Offset to name": int.from_bytes(self.entry_raw[self.cur_offset + 10: self.cur_offset + 12], byteorder='little'),
            "CONTENT SIZE": int.from_bytes(self.entry_raw[self.cur_offset + 16: self.cur_offset + 19], byteorder='little'),
            "OFFSET TO CONTENT": int.from_bytes(self.entry_raw[self.cur_offset + 20: self.cur_offset + 21], byteorder='little'),
        }
        return header
    