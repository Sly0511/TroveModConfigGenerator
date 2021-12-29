import os
import shutil
import time
import winreg

# Registry Constants
Hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
Nodes = ["WOW6432Node\\"]
Path = "Microsoft\\Windows\\CurrentVersion\\Uninstall\\"
TroveKey = "Glyph Trove"
TroveInstallValue = "InstallLocation"

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
                LookPath = "SOFTWARE\\"+Node+Path
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
    TroveExe = os.path.join(Path, "Trove.exe")
    ModsFolder = os.path.join(Path, "mods")
    if not os.path.exists(Path):
        if Registry:
            print("Directory found in Registry but folder wasn't found:\n\t -> "+Path+"\n\n")
        else:
            print("Directory wasn't found:\n\t -> "+Path+"\n\n")
        return False
    if not os.path.exists(TroveExe):
        if Registry:
            print("Directory found in Registry but 'Trove.exe' wasn't found:\n\t-> "+TroveExe+"\n\n")
        else:
            print("Directory found but 'Trove.exe' wasn't found:\n\t -> "+TroveExe+"\n\n")
        return False
    if not os.path.exists(ModsFolder):
        if Registry:
            print("Directory found in Registry but 'mods' folder wasn't found:\n\t-> "+ModsFolder+"\n\n")
        else:
            print("Directory found but 'mods' folder wasn't found:\n\t -> "+ModsFolder+"\n\n")
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
        if SanityCheck(GamePath):
            yield GamePath

def CreateDirectory(Path, Warn=False):
    """
    Creates a directory if it doesn't exist
    """
    if not os.path.exists(Path):
        os.mkdir(Path)
        if Warn:
            print(f"Created necessary directory:\n\t-> '{Path}'")

def GetAllFiles(Folder):
    """
    Gets all files in a directory
    """
    for File in os.listdir(Folder):
        FilePath = os.path.join(Folder, File)
        if os.path.isdir(FilePath):
            for i in GetAllFiles(FilePath):
                yield i
        else:
            yield File

def ExtractMod(ModPath, ModDestination):
    """
    Extracts a mod's contents
    """
    os.system(f'Trove.exe -tool extractmod -file "{ModPath}" -override -output "{ModDestination}"')

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
        Inserted = input("Please input a valid Trove directory:\n")
        if SanityCheck(Inserted, False):
            DirectoriesFound.append(Inserted)
            break
else:
    print(f"Detected {len(DirectoriesFound)} Trove directories\n")
    for Directory in DirectoriesFound:
        print(f"\t-> {Directory}\n")

Appdata = os.getenv('APPDATA')
AppdataTrove = os.path.join(Appdata, "Trove")
ModCfgs = os.path.join(AppdataTrove, "ModCfgs")
CreateDirectory(AppdataTrove, True)
CreateDirectory(ModCfgs, True)

CheckedMods = []
CurrentDirectory = os.getcwd()
ModCache = os.path.join(CurrentDirectory, "ModConfigsCache")
if not os.path.exists(ModCache):
    os.mkdir(ModCache)

for Directory in DirectoriesFound:
    os.chdir(Directory)
    ModsFolder = os.path.join(Directory, "mods")
    Mods = [(ModFile, os.path.join(ModsFolder, ModFile)) for ModFile in os.listdir(ModsFolder) if ModFile.endswith(".tmod")]
    i = 0
    for ModFile, ModPath in Mods:
        try:
            i += 1
            ModName = ".".join(ModFile.split(".")[:-1])
            print(f"Checking mod {i}/{len(Mods)} in {ModsFolder} >>> [{ModName}]")
            if ModName in CheckedMods:
                print(f" -> Skipped config (Already Checked) >>> {ModName}\n")
                continue
            ConfigFileName = os.path.join(ModCfgs, f"{ModName}.cfg")
            if os.path.isfile(ConfigFileName) and len(open(ConfigFileName, "r").read()):
                print(f" -> Skipped config (Already Exists) >>> {ModName}\n")
                continue
            ModDestination = os.path.join(ModCache, ModName)
            CreateDirectory(ModDestination)
            ExtractMod(ModPath, ModDestination)
            SWFFiles = []
            for File in GetAllFiles(ModDestination):
                if File.endswith(".swf"):
                    SWFFiles.append(File)
            if SWFFiles:
                with open(ConfigFileName, "w+") as ConfigFile:
                    ConfigFile.write("\n\n\n".join([f"[{SWFFile}]" for SWFFile in SWFFiles]))
                print(f" -> Created config >>> {ModName}\n")
            else:
                print(f" -> Skipped config (Doesn't contain UI files) >>> {ModName}\n")
            CheckedMods.append(ModName)
        except KeyboardInterrupt:
            shutil.rmtree(ModCache)
            exit()

shutil.rmtree(ModCache)
print("The mod configs were created successfully. You can now close this window.")
os.system("PAUSE")
