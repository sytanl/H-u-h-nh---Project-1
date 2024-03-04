from math import *

class PBS:
    infor = ["OEM_ID",
             "Bytes Per Sector",
             "Sectors Per Cluster",
             "Number of Sectors in Track",
             "Number of Heads",
             "First Sector of Logic Drive",
             "Total Sector",
             "First Cluster of MFT",
             "MFT Entry Size",
             "Clusters Per Index Buffer",
             "Volume Serial Number"]
    
    def __init__(self, boot_sector_raw: str) -> None:
        self.boot_sector = {}
        self.extract_pbs(boot_sector_raw)

    def extract_pbs(self, boot_sector_raw: str):
        self.boot_sector['OEM_ID'] = boot_sector_raw[0x3:0xB].decode().strip()
        self.boot_sector['Bytes Per Sector'] = int.from_bytes(boot_sector_raw[0x0B:0x0B + 2], byteorder='little')
        self.boot_sector['Sectors Per Cluster'] = int.from_bytes(boot_sector_raw[0x0D:0x0D + 1], byteorder='little')
        self.boot_sector['Number of Sectors in Track'] = int.from_bytes(boot_sector_raw[0x18:0x18 + 2], byteorder='little')
        self.boot_sector['Number of Heads'] = int.from_bytes(boot_sector_raw[0x1A:0x1A + 2], byteorder='little')
        self.boot_sector['First Sector of Logic Drive'] = int.from_bytes(boot_sector_raw[0x1C:0x1C + 4], byteorder='little')
        self.boot_sector['Total Sector'] = int.from_bytes(boot_sector_raw[0x28:0x28 + 8], byteorder='little')
        self.boot_sector['First Cluster of MFT'] = int.from_bytes(boot_sector_raw[0x30:0x30 + 8], byteorder='little')
        self.boot_sector['MFT Entry Size'] = int(pow(2, fabs(int.from_bytes(boot_sector_raw[0x40:0x41], byteorder='little', signed=True))))
        self.boot_sector['Clusters Per Index Buffer'] = int.from_bytes(boot_sector_raw[0x44:0x44 + 1], byteorder='little')
        self.boot_sector['Volume Serial Number'] = "{:08X}".format(int.from_bytes(boot_sector_raw[0x48:0x50], byteorder='little'))  
        self.boot_sector['Volume Serial Number'] = self.boot_sector['Volume Serial Number'][8:12] + '-' + self.boot_sector['Volume Serial Number'][12:]
        
    def __str__(self):
        out = ""
        for key in PBS.infor:
            out += f"{key}: {self.boot_sector[key]}\n"
        return out