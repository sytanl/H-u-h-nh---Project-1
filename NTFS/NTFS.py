from PBS import *
from datetime import *
from Constant import *
from MFT_Entry import *

class NTFS:
    def __init__(self, drive_name: str) -> None:
        self.drive_name = drive_name
        self.directory_tree = []
        self.valid_parent_id = [5]

        try:
            self.file = open(r'\\.\%s' % self.drive_name, 'rb')
        except FileNotFoundError:
            print(f"[ERROR] No drive named {drive_name}")
            exit()
        except PermissionError:
            print("[ERROR] Permission denied, try again as admin")
            exit()
            
        # read partition boot sector
        self.boot_sector_raw = self.file.read(0x200)
        self.pbs = PBS(self.boot_sector_raw)
        if self.pbs.boot_sector["OEM_ID"] != "NTFS":
            raise Exception("Not NTFS")
        
        self.sc = self.pbs.boot_sector['Sectors Per Cluster']
        self.bs = self.pbs.boot_sector['Bytes Per Sector']
        self.entry_size = self.pbs.boot_sector['MFT Entry Size']
        self.mft_offset = self.pbs.boot_sector['First Cluster of MFT']
        self.cur_offset = self.mft_offset * self.sc * self.bs
        self.file.seek(self.cur_offset)     
        self.entry_raw = self.file.read(self.entry_size)
        self.num_sector = (int.from_bytes(self.entry_raw[0x118:0x120], byteorder='little') + 1) * 8


        for _ in range(2, 1024, 2):
            self.entry_raw = self.file.read(self.entry_size)
            if self.entry_raw[0x0:0x4] == b'FILE':
                try:
                    mft_entry = MFT_Entry(self.entry_raw, self.sc, self.bs)
                
                    if mft_entry.infor['PARENT ID'] in self.valid_parent_id:
                        if not mft_entry.infor['Resident']:
                            content = b''
                            for sector in mft_entry.infor['DATA']:
                                self.file.seek(sector * self.bs)
                                content = content + self.file.read(self.bs)
                            mft_entry.infor['DATA'] = content
                        node = {
                            "Created time": mft_entry.infor['Created Time'],
                            "Modified time": mft_entry.infor['Modified Time'],
                            "Parent Id": mft_entry.infor['PARENT ID'],
                            "Name": mft_entry.infor['FILE NAME'],
                            "Index": mft_entry.infor['ID'],
                            "TYPE": mft_entry.infor['attr_flag'],
                            "SIZE": mft_entry.infor['SIZE OF DATA'],
                            "DATA": mft_entry.infor['DATA'],
                        }
                        
                        self.directory_tree.append(node)
                        if NTFSAttribute.DIRECTORY in node['TYPE']:
                            self.valid_parent_id.append(node['Index'])
                        node['TYPE'] = [str(member.name).strip('[]') for member in node['TYPE']]
                except Exception as e:
                    pass

    @staticmethod
    def isNTFS(drive_name: str):
        try:
            with open(r'\\.\%s' % drive_name, 'rb') as file:
                if file.read(0x0B)[0x03:] == b'NTFS    ':
                    return True
                return False
        except Exception as e:
            print(f"[ERROR] {e}")
            exit()

    def __del__(self):
        if getattr(self, "file", None):
            self.file.close()
            
drive_name = "E:"
a = NTFS(drive_name)

for item in a.directory_tree:
    print(item)

'''
đọc partition boot sector
đọc mtf: mtf header -> các attribute standard information, file name, data 
parent index của một file = index của folder của file đó
parent index = 5 -> ổ đĩa
'''