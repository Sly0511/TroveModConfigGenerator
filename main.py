import os
import shutil
import winreg
from tqdm import tqdm
from pathlib import Path

# Registry Constants
Hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
Nodes = ["WOW6432Node\\"]
TrovePath = "Microsoft\\Windows\\CurrentVersion\\Uninstall\\"
TroveKey = "Glyph Trove"
TroveInstallValue = "InstallLocation"

class Progress(tqdm):
    def update_to(self, i, desc=None, total=None):
        if total is not None:
            self.total = total
        if desc is not None:
            self.desc = desc
        self.update(i)

def GetKeys(key, path, look_for):
    """
    Looks for keys within a given key and filters out the keys unrelated to Glyph
    """
    i = 0
    while True:
        try:
            subkey = winreg.EnumKey(key, i)
            if subkey.startswith(look_for):
                yield path+subkey+"\\"
        except WindowsError:
            break
        i += 1

def SearchRegistry():
    """
    Looks for the 'Uninstall' path where Glyph keys are stored
    """
    for Hive in Hives:
        for Node in Nodes:
            try:
                LookPath = "SOFTWARE\\"+Node+TrovePath
                RegistryKeyPath = winreg.OpenKeyEx(Hive, LookPath)
                Keys = GetKeys(RegistryKeyPath, LookPath, TroveKey)
                for Key in Keys:
                    yield winreg.OpenKeyEx(Hive, Key)
            except WindowsError:
                ...

def SanityCheck(Path, Registry=True):
    """
    This checks if directories exist and are valid.
    Returns alerts when invalid directories are found.
    """
    TroveExe = Path.joinpath("Trove.exe")
    ModsFolder = Path.joinpath("mods")
    if not Path.exists():
        if Registry:
            print("Directory found in Registry but folder wasn't found:\n\t -> "+str(Path.absolute())+"\n\n")
        else:
            print("Directory wasn't found:\n\t -> "+str(Path.absolute())+"\n\n")
        return False
    if not TroveExe.exists():
        if Registry:
            print("Directory found in Registry but 'Trove.exe' wasn't found:\n\t-> "+str(TroveExe.absolute())+"\n\n")
        else:
            print("Directory found but 'Trove.exe' wasn't found:\n\t -> "+str(TroveExe.absolute())+"\n\n")
        return False
    if not ModsFolder.exists():
        if Registry:
            print("Directory found in Registry but 'mods' folder wasn't found:\n\t-> "+str(ModsFolder.absolute())+"\n\n")
        else:
            print("Directory found but 'mods' folder wasn't found:\n\t -> "+str(ModsFolder.absolute())+"\n\n")
        return False
    return True

def GetTroveLocations():
    """
    This is a generator that returns Trove Directories found in registry.
    """
    for Key in SearchRegistry():
        try:
            GamePath = winreg.QueryValueEx(Key, TroveInstallValue)[0] # Extracts path out of value in Glyph keys
        except WindowsError:
            continue
        if SanityCheck(Path(GamePath)):
            yield Path(GamePath)

def CreateDirectory(Path: Path, Warn=False):
    """
    Creates a directory if it doesn't exist
    """
    if not Path.exists():
        Path.mkdir()
        if Warn:
            print(f"Created necessary directory:\n\t-> '{Path}'")

def GetAllFiles(Folder):
    """
    Gets all files in a directory
    """
    for File in Folder.iterdir():
        FilePath = Folder.joinpath(File)
        if FilePath.is_dir():
            for i in GetAllFiles(FilePath):
                yield i
        else:
            yield File

def ExtractMod(ModPath, ModDestination):
    """
    Extracts a mod's contents
    """
    os.system(f'Trove.exe -tool extractmod -file "{ModPath.absolute()}" -override -output "{ModDestination.absolute()}"')

def CheckModConfig(ModFile, ModPath: Path):
    ModName = ModFile.stem
    ConfigFileName = ModCfgs.joinpath(f"{ModName}.cfg")
    ModDestination = ModCache.joinpath(ModName)
    if ModName in CheckedMods:
        return
    if ConfigFileName.exists() and len(ConfigFileName.open("r").read()):
        return
    CreateDirectory(ModDestination)
    ExtractMod(ModPath, ModDestination)
    SWFFiles = [File for File in GetAllFiles(ModDestination) if File.suffix == ".swf"]
    if SWFFiles:
        with open(ConfigFileName, "w+") as ConfigFile:
            ConfigFile.write("\n\n\n".join([f"[{SWFFile.name}]" for SWFFile in SWFFiles]))
    CheckedMods.append(ModName)
    return

DirectoriesFound = []
look_for = None
print(
"""\nThis script is going to create configuration files for mods automatically
in order to make mod setups easier for the user.\n"""
)
while look_for is None:
    try:
        look_for = input("Would you like to look for mods in all default directories of Trove? [Y/N]:\n").lower() == "y"
        break
    except KeyboardInterrupt:
        exit()
    except:
        ...

if look_for:
    GamePaths = list(GetTroveLocations())
    DirectoriesFound.extend(GamePaths)

if not DirectoriesFound:
    while not DirectoriesFound:
        Inserted = Path(input("Please input a valid Trove directory:\n"))
        if SanityCheck(Inserted, False):
            DirectoriesFound.append(Inserted)
            break
else:
    print(f"Detected {len(DirectoriesFound)} Trove directories\n")
    for Directory in DirectoriesFound:
        print(f"\t-> {Directory}\n")

Appdata = Path(os.getenv('APPDATA'))
AppdataTrove = Appdata.joinpath("Trove")
ModCfgs = AppdataTrove.joinpath("ModCfgs")
CreateDirectory(AppdataTrove, True)
CreateDirectory(ModCfgs, True)

CheckedMods = []
CurrentDirectory = Path(os.getcwd())
ModCache = CurrentDirectory.joinpath("ModConfigsCache")
if not ModCache.exists():
    ModCache.mkdir()

for Directory in DirectoriesFound:
    print(f"\nGenerating mod configs for mods in:\n{Directory}")
    with Progress() as ModsProgress:
        os.chdir(Directory)
        ModsFolder = Directory.joinpath("mods")
        Mods = [(ModFile, ModsFolder.joinpath(ModFile)) for ModFile in ModsFolder.iterdir() if ModFile.is_file() and ModFile.suffix == ".tmod"]
        ModsProgress.update_to(0, total=len(Mods))
        for ModFile, ModPath in Mods:
            ModsProgress.update_to(0, desc=f"{ModFile.name:<64}")
            try:
                CheckModConfig(ModFile, ModPath)
            except KeyboardInterrupt:
                shutil.rmtree(ModCache)
                exit()
            ModsProgress.update_to(1)

shutil.rmtree(ModCache)
print("The mod configs were created successfully. You can now close this window.")
os.system("PAUSE")
