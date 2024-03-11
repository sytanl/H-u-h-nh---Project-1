import cmd
import os
from NTFS import NTFS
class Menu(cmd.Cmd):
    intro=""
    prompt=""
    def __init__(self, vol:NTFS) -> None:
        super().__init__(Menu, self).__init__()
        self.vol=vol
        self._loop_promt()

    def _loop_promt(self):
        Menu.prompt="Input command:"
    
    def do_tree(self,arg):
        '''
        tree: print the tree of the current directory and it's sub-directory
        tree <folder name>: print the directory tree in the specified folder
        '''
        def print_tree(a:NTFS, name, prefix=""):
            if name=="":
                for i in a.directory_tree:
                    if i["PARENT ID"]== 5:
                        print(prefix + ("|-- " ) + i["FILE NAME"] +" (Sector:" + str(i["sector index"])+")" + (" (Size:"+str(i["SIZE OF DATA"])+")" if i["SIZE OF DATA"] else ""))
                        print_tree(a,i["FILE NAME"],'|'+prefix+'   ')
            else:
                for i in a.directory_tree:
                    if i["FILE NAME"]==name:
                        name_id=i["ID"]
                for i in a.directory_tree:
                    if i["PARENT ID"]== name_id:
                        print(prefix +("|-- " )+ i["FILE NAME"]+ " (Sector:" +str(i["sector index"])+")"+ (" (Size:"+str(i["SIZE OF DATA"])+")" if i["SIZE OF DATA"] else ""))
                        print_tree(a,i["FILE NAME"],'|'+'   '+ prefix)
        if arg=="":
            print(self.vol)
        else:
            print(arg)
        print_tree(self.vol,arg)
    
    def do_open(self,arg):
        '''
        cat <file_name>: print content of a specific file (text only)
        '''
        if arg == "":
            print(f"[ERROR] No name provided")
            return
        for i in self.vol.directory_tree:
            if i["FILE NAME"]==arg:
                if i["DATA"]!="":
                    raw_data=i["DATA"].decode()
                    if  raw_data!="":
                        data=raw_data.split("/r/n")
                        for j in data:
                            print(j)
                    else:
                        print("Use other compatible software to read the content")
                else:
                    print("Invalid file")
    
    def do_quit(self,arg):
        '''
        quit: exit the menu
        '''
        print("Thank for using")
        self.close()
        return True
    
    def close(self):
        if self.vol:
            del self.vol
            self.vol = None



if __name__ == "__main__":
    volumes = [chr(x) + ":" for x in range(65, 91) if os.path.exists(chr(x) + ":")]
    print("Available volumes:")
    for i in range(len(volumes)):
        print(f"{i + 1}/", volumes[i])
    try:
        choice = int(input("Which volume to use: "))
    except Exception as e:
        print(f"[ERROR] {e}")
        exit()

    if choice <= 0 and choice > len(volumes):
        print("[ERROR] Invalid choice!")
        exit()
    volume_name = volumes[choice - 1]

    vol=NTFS(volume_name)
    vol.print_partrition_data()
    menu=Menu(vol)
    menu.cmdloop()
