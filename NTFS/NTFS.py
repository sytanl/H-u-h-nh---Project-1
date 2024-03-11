from math import * 
from datetime import *

class NTFS:
    def __init__(self, drive_name: str) -> None:
        self.drive_name = drive_name
        self.directory_tree = []
        self.valid_parent_id = [5]
        self.pbt = {}
        self.file = open(r'\\.\%s' % self.drive_name, 'rb')
        self.raw_data = self.file.read(0x200)

        self.extract_partition_boot_sector()
        if self.pbs['OEM_ID'] != "NTFS":
            raise Exception("Not NTFS")
        
        self.save_offset = self.pbs['First Cluster of MFT'] * self.pbs['bs'] * self.pbs['sc']
        self.file.seek(self.save_offset)
        self.raw_entry = self.file.read(self.pbs['Entry Size'])

        # file đầu tiên = file $mft: chứa toàn bộ thông tin bảng mft 
        first_entry = self.extract_mft_entry()
        self.total_sector = first_entry['end_VCN_of_runlist'] * self.pbs['sc']
        
        
        for _ in range(2, self.total_sector, 2):
            self.save_offset += self.pbs['Entry Size']
            self.file.seek(self.save_offset)
            self.raw_entry = self.file.read(self.pbs['Entry Size'])
          
            if self.raw_entry[0x0:0x4] == b'FILE':
                node = self.extract_mft_entry()
                if node['PARENT ID'] in self.valid_parent_id and not node['FILE NAME'].startswith('$'):
                    if node['attr_flag'] == 0 or node['attr_flag'] == 32:
                        node['sector index'] = self.save_offset // self.pbs['bs']
                        node['SIZE OF DATA'] = str(ceil(node['SIZE OF DATA'] / 1024)) + " KB"
                        self.directory_tree.append(node)
                        if node['attr_flag'] == 0:
                            self.valid_parent_id.append(node['ID'])
                   

    def extract_mft_entry(self) -> dict:
        infor = {}
        try:
            self.entry_header = {
                "Signature": self.raw_entry[0x0:0x4].decode(),
                "First Offset of Attribute": int.from_bytes(self.raw_entry[0x14:0x16], byteorder='little'),
                "Entry Flag": int.from_bytes(self.raw_entry[0x16:0x18], byteorder='little'),
            }
            if self.entry_header['Entry Flag'] == 1:
                self.entry_header['Entry Flag'] = "IN_USE"
            elif self.entry_header['Entry Flag'] == 2:
                self.entry_header['Entry Flag'] = "IS_DIRECTORY"
            elif self.entry_header['Entry Flag'] == 4:
                self.entry_header['Entry Flag'] = "IN_EXTENDED"
            elif self.entry_header['Entry Flag'] == 8:
                self.entry_header['Entry Flag'] = "IS_VIEW_INDEX"
        except Exception as e:
            pass
        infor['status'] = self.entry_header['Entry Flag']
        infor["ID"] = int.from_bytes(self.raw_entry[0x2C:0x2C + 4], byteorder='little')
        self.cur_offset = self.entry_header['First Offset of Attribute'] 
        

        # standard information attribute
        attri_header = self.extract_attr()
        offset_to_content = int.from_bytes(self.raw_entry[self.cur_offset + 20: self.cur_offset + 22], byteorder='little')
        content_size = int.from_bytes(self.raw_entry[self.cur_offset + 16: self.cur_offset + 20], byteorder='little')
        self.cur_offset += offset_to_content

        timestamp = int.from_bytes(self.raw_entry[self.cur_offset: self.cur_offset + 8], byteorder='little')
        _time = datetime(1601, 1, 1) + timedelta(microseconds=timestamp / 10)
        infor["Created Time"] = _time.strftime("%Y-%m-%d %H:%M:%S")
     
        timestamp = int.from_bytes(self.raw_entry[self.cur_offset + 8: self.cur_offset + 16], byteorder='little')
        _time = datetime(1601, 1, 1) + timedelta(microseconds=timestamp / 10)
        infor["Modified Time"] = _time.strftime("%Y-%m-%d %H:%M:%S")
        if self.raw_entry[self.cur_offset + 32: self.cur_offset + 36] == 0x0600:
            return
        
        infor["attr_flag"] = int.from_bytes(self.raw_entry[self.cur_offset + 32: self.cur_offset + 36], byteorder='little') 
        self.cur_offset += attri_header["Attribute length"] - offset_to_content


        # file name attribute
        attri_header = self.extract_attr()
        offset_to_content = int.from_bytes(self.raw_entry[self.cur_offset + 20: self.cur_offset + 22], byteorder='little')
        content_size = int.from_bytes(self.raw_entry[self.cur_offset + 16: self.cur_offset + 20], byteorder='little')
        self.cur_offset += offset_to_content
        infor["PARENT ID"] = int.from_bytes(self.raw_entry[self.cur_offset: self.cur_offset + 6], byteorder='little')
        infor["NAME LENGTH"] = self.raw_entry[self.cur_offset + 64]
        infor["FILE NAME"] = self.raw_entry[self.cur_offset + 66: self.cur_offset + 66 + infor["NAME LENGTH"] * 2].decode("utf-16le")
        
        self.cur_offset += attri_header["Attribute length"] - offset_to_content


        # data attribute
        attri_header = self.extract_attr()
        if attri_header['Attribute type'] == 64:
            self.cur_offset += attri_header["Attribute length"]
            attri_header = self.extract_attr()
     

        if attri_header['Attribute type'] == 128: #file
            if attri_header["Resident Flag"] == "Resident":
                infor['Resident'] = True  
                
                offset = int.from_bytes(self.raw_entry[self.cur_offset + 20: self.cur_offset + 22], byteorder='little')
                infor['SIZE OF DATA'] = int.from_bytes(self.raw_entry[self.cur_offset + 16: self.cur_offset + 20], byteorder='little')
                if infor["FILE NAME"].endswith('.txt'):    
                    infor['DATA'] = self.raw_entry[self.cur_offset + offset: self.cur_offset + offset + infor['SIZE OF DATA']]
                else:
                    infor['SIZE OF DATA'] = int.from_bytes(self.raw_entry[self.cur_offset + 16: self.cur_offset + 20], byteorder='little')
                    infor['DATA'] = "=="
            else:
                infor['Resident'] = False
                infor['start_VCN_of_runlist'] = int.from_bytes(self.raw_entry[self.cur_offset + 16: self.cur_offset + 24], byteorder='little')
                infor['end_VCN_of_runlist'] = int.from_bytes(self.raw_entry[self.cur_offset + 24: self.cur_offset + 32], byteorder='little')
            
                
                offset_to_runlist = int.from_bytes(self.raw_entry[self.cur_offset + 32: self.cur_offset + 34], byteorder='little')
                self.cur_offset += offset_to_runlist
                raw_data_run = self.raw_entry[self.cur_offset:]
                
                result = self.get_data_run(raw_data_run, infor["FILE NAME"][-4:])
                infor['DATA'] = result[0]
                infor['SIZE OF DATA'] = result[1]

        elif attri_header['Attribute type'] == 144: #folder
            infor['SIZE OF DATA'] = 0
            infor['DATA'] = ""
            infor['Resident'] = True

        return infor

    def extract_attr(self) -> dict:
        attr_header = {
            "Attribute type": int.from_bytes(self.raw_entry[self.cur_offset: self.cur_offset + 4], byteorder='little'),
            "Attribute length": int.from_bytes(self.raw_entry[self.cur_offset + 4: self.cur_offset + 8], byteorder='little'),
            "Resident Flag": "Resident" if int.from_bytes(self.raw_entry[self.cur_offset + 8: self.cur_offset + 9], byteorder='little') == 0 else "Non-resident",
            "Name size": int.from_bytes(self.raw_entry[self.cur_offset + 9: self.cur_offset + 10], byteorder='little'),
            "Offset to name": int.from_bytes(self.raw_entry[self.cur_offset + 10: self.cur_offset + 12], byteorder='little'),
        }
        return attr_header
    
    # non-resident data
    def get_data_run(self, raw_data_run, type) -> tuple:
        index = 0
        size = 0
        run_length_byte = 0
        run_offset_byte = 0
        run_length = 0
        run_offset = 0
        content = b''
        while raw_data_run[index] >= 0b00000001:
            run_length_byte = raw_data_run[index] & 0b00001111
            run_offset_byte = (raw_data_run[index] & 0b11110000) >> 4
            
            run_length = int.from_bytes(raw_data_run[index + 1: index + 1 + run_length_byte], byteorder='little')
            index += run_length_byte
            run_offset = int.from_bytes(raw_data_run[index + 1: index + 1 + run_offset_byte], byteorder='little') + run_offset
            index += run_offset_byte 
            if type == ".txt":
                for cluster in range(run_length):
                    for i in range(self.pbs['sc']):
                        sector = cluster * self.pbs['sc'] + i
                        self.file.seek(run_offset * self.pbs['sc'] * self.pbs['bs'] + sector * self.pbs['bs'])
                        content = content + self.file.read(self.pbs['bs'])
            size += run_length
            index += 1
        return content, size * self.pbs['sc'] * self.pbs['bs']
    
    def extract_partition_boot_sector(self):
        self.pbs = {}
        self.pbs['OEM_ID'] = self.raw_data[0x3:0xB].decode().strip()
        self.pbs['bs'] = int.from_bytes(self.raw_data[0x0B:0x0B + 2], byteorder='little')
        self.pbs['sc'] = int.from_bytes(self.raw_data[0x0D:0x0D + 1], byteorder='little')
        self.pbs['Number of Sectors in Track'] = int.from_bytes(self.raw_data[0x18:0x18 + 2], byteorder='little')
        self.pbs['Number of Heads'] = int.from_bytes(self.raw_data[0x1A:0x1A + 2], byteorder='little')
        self.pbs['First Sector of Logic Drive'] = int.from_bytes(self.raw_data[0x1C:0x1C + 4], byteorder='little')
        self.pbs['Total Sector'] = int.from_bytes(self.raw_data[0x28:0x28 + 8], byteorder='little')
        self.pbs['First Cluster of MFT'] = int.from_bytes(self.raw_data[0x30:0x30 + 8], byteorder='little')
        # giá trị thập lục phân là số có dấu -> đổi qua hệ mười = x -> lấy 2^|x|
        self.pbs['Entry Size'] = int(pow(2, fabs(int.from_bytes(self.raw_data[0x40:0x41], byteorder='little', signed=True))))
        self.pbs['Clusters Per Index Buffer'] = int.from_bytes(self.raw_data[0x44:0x44 + 1], byteorder='little')
        self.pbs['Volume Serial Number'] = "{:08X}".format(int.from_bytes(self.raw_data[0x48:0x50], byteorder='little'))  
        self.pbs['Volume Serial Number'] = self.pbs['Volume Serial Number'][8:12] + '-' + self.pbs['Volume Serial Number'][12:]
        

    def print_partrition_data(self):
        print("OEM_ID:", self.pbs['OEM_ID'])
        print("Bytes Per Sector:", self.pbs['bs'])
        print("Sectors Per Cluster:", self.pbs['sc'])
        print("Number of Sectors in Track:", self.pbs['Number of Sectors in Track'])
        print("Number of Heads:", self.pbs['Number of Heads'])
        print("Total Sector:", self.pbs['Total Sector'])
        print("First Cluster of MFT:", self.pbs['First Cluster of MFT'])
        print("MFT Entry Size:", self.pbs['Entry Size'])
        print("Clusters Per Index Buffer:", self.pbs['Clusters Per Index Buffer'])
        print("Volume Serial Number:", self.pbs['Volume Serial Number'])
    def __del__(self):
        if getattr(self, "file", None):
            self.file.close()

