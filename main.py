import asyncio
import os
import sys
import winreg
from copy import copy
from pathlib import Path

from asyncqt import QEventLoop
from binary_reader import BinaryReader
from PyQt5 import QtCore, QtGui, QtWidgets

from about import Ui_About

Hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
Nodes = ["WOW6432Node\\"]
TrovePath = "Microsoft\\Windows\\CurrentVersion\\Uninstall\\"
TroveKey = "Glyph Trove"
TroveInstallValue = "InstallLocation"
SteamPath = "Valve\\"
SteamKey = "Steam"
SteamInstallValue = "InstallPath"
SteamTroveID = "304050"

# Helper Functions

def isNullOrWhiteSpace(str=None):
  return not str or str.isspace()

def decode_from_7bit(data):
    result = 0
    for i, byte in enumerate(data):
        result |= (byte & 0x7f) << (7 * i)
        if byte & 0x80 == 0:
            break
    return result

def ReadVarInt7Bit(buffer: BinaryReader, pos):
    result = 0
    shift = 0
    while 1:
        buffer.seek(pos)
        b = buffer.read_bytes()
        for i, byte in enumerate(b):
            result |= ((byte & 0x7f) << shift)
            pos += 1
            if not (byte & 0x80):
                result &= (1 << 32) - 1
                result = int(result)
                return (result, pos)
            shift += 7
            if shift >= 64:
                raise Exception('Too many bytes when decoding varint.')
    return result

# Main UI

class SlyTroveConfigGenerator(object):
    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow
        self.loop = asyncio.get_event_loop()
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(720, 519)
        MainWindow.setFixedSize(720, 519)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(str(Path(sys._MEIPASS).joinpath("images", "AppLogo.png"))), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setStyleSheet("background:#313233;color:#ccc")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.listView = QtWidgets.QListView(self.centralwidget)
        self.listView.setGeometry(QtCore.QRect(10, 30, 551, 161))
        self.listView.setObjectName("listView")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(570, 260, 141, 21))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setEnabled(False)
        self.refreshButton = QtWidgets.QPushButton(self.centralwidget)
        self.refreshButton.setGeometry(QtCore.QRect(460, 160, 75, 23))
        self.refreshButton.setObjectName("refreshButton")
        self.cfgFolderButton = QtWidgets.QPushButton(self.centralwidget)
        self.cfgFolderButton.setGeometry(QtCore.QRect(450, 260, 111, 21))
        self.cfgFolderButton.setObjectName("cfgFolderButton")
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setGeometry(QtCore.QRect(570, 40, 141, 17))
        self.checkBox.setObjectName("checkBox")
        self.checkBox.setChecked(True)
        self.liveCheck = QtWidgets.QCheckBox(self.centralwidget)
        self.liveCheck.setGeometry(QtCore.QRect(610, 202, 41, 17))
        self.liveCheck.setObjectName("liveCheck")
        self.ptsCheck = QtWidgets.QCheckBox(self.centralwidget)
        self.ptsCheck.setGeometry(QtCore.QRect(670, 202, 41, 17))
        self.ptsCheck.setObjectName("ptsCheck")
        self.steamliveCheck = QtWidgets.QCheckBox(self.centralwidget)
        self.steamliveCheck.setGeometry(QtCore.QRect(610, 230, 41, 17))
        self.steamliveCheck.setObjectName("steamliveCheck")
        self.steamptsCheck = QtWidgets.QCheckBox(self.centralwidget)
        self.steamptsCheck.setGeometry(QtCore.QRect(670, 230, 41, 17))
        self.steamptsCheck.setObjectName("steamptsCheck")
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(20, 230, 541, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(570, 90, 141, 22))
        self.comboBox.setObjectName("comboBox")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(570, 70, 91, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(10, 270, 47, 13))
        self.label_2.setObjectName("label_2")
        self.logLabel = QtWidgets.QLabel(self.centralwidget)
        self.logLabel.setGeometry(QtCore.QRect(10, 290, 701, 181))
        font = QtGui.QFont()
        font.setFamily("Consolas")
        self.logLabel = QtWidgets.QTextEdit(self.centralwidget)
        self.logLabel.setGeometry(QtCore.QRect(10, 290, 701, 181))
        self.logLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.logLabel.setReadOnly(True)
        self.logLabel.setObjectName("textEdit")
        self.logLabel.setFont(font)
        self.logLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.logLabel.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.logLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.logLabel.setObjectName("logLabel")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(10, 10, 47, 13))
        self.label_4.setObjectName("label_4")
        self.currentLabel = QtWidgets.QLabel(self.centralwidget)
        self.currentLabel.setGeometry(QtCore.QRect(20, 210, 541, 16))
        self.currentLabel.setText("")
        self.currentLabel.setObjectName("currentLabel")
        self.warningLabel = QtWidgets.QLabel(self.centralwidget)
        self.warningLabel.setEnabled(False)
        self.warningLabel.setGeometry(QtCore.QRect(570, 130, 131, 61))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.warningLabel.sizePolicy().hasHeightForWidth())
        self.warningLabel.setSizePolicy(sizePolicy)
        self.warningLabel.setStyleSheet("color:rgba(255,0,0,0)")
        self.warningLabel.setObjectName("warningLabel")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 720, 21))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionAbout = QtWidgets.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuHelp.menuAction())
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(580, 201, 16, 19))
        self.label_3.setText("")
        self.label_3.setPixmap(QtGui.QPixmap(str(Path(sys._MEIPASS).joinpath("images", "GlyphLogo.png"))))
        self.label_3.setScaledContents(True)
        self.label_3.setObjectName("label_3")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(580, 230, 16, 16))
        self.label_5.setText("")
        self.label_5.setPixmap(QtGui.QPixmap(sys._MEIPASS+"/images/SteamLogo.png"))
        self.label_5.setScaledContents(True)
        self.label_5.setObjectName("label_5")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(71, 10, 491, 20))
        self.lineEdit.setObjectName("lineEdit")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(570, 10, 141, 21))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.setEnabled(False)
        # Fill UI
        self.comboBox.addItem("Overwrite empty files")
        self.comboBox.addItem("No Overwrites")
        self.comboBox.addItem("Overwrite all files")
        # Connections
        self.comboBox.currentTextChanged.connect(self.comboBoxChanged)
        self.pushButton.clicked.connect(self.runGenerateButton)
        self.refreshButton.clicked.connect(self.refreshMods)
        self.steamliveCheck.stateChanged.connect(self.SteamLiveCheckChanged)
        self.steamptsCheck.stateChanged.connect(self.SteamPTSCheckChanged)
        self.liveCheck.stateChanged.connect(self.LiveCheckChanged)
        self.ptsCheck.stateChanged.connect(self.PTSCheckChanged)
        self.lineEdit.textChanged.connect(self.CustomFoldersChanged)
        self.actionAbout.triggered.connect(self.aboutDialog)
        self.pushButton_2.clicked.connect(self.addCustomFolders)
        self.cfgFolderButton.clicked.connect(self.cfgFolderButtonClicked)
        # Startup
        self.startup()
        # translate UI
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def startup(self):
        self.running = False
        self.Appdata = Path(os.getenv('APPDATA'))
        self.AppdataTrove = self.Appdata.joinpath("Trove")
        self.ModCache = self.Appdata.joinpath("TroveConfigGenerator")
        self.ModCfgs = self.AppdataTrove.joinpath("ModCfgs")
        self.CreateDirectory(self.AppdataTrove, True)
        self.CreateDirectory(self.ModCfgs, True)
        self.refreshMods()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Trove Mod Config Generator"))
        self.pushButton.setText(_translate("MainWindow", "Generate Configs"))
        self.refreshButton.setText(_translate("MainWindow", "Refresh"))
        self.cfgFolderButton.setText(_translate("MainWindow", "Open Config Folder"))
        self.checkBox.setText(_translate("MainWindow", "Generate Missing Config"))
        self.liveCheck.setText(_translate("MainWindow", "Live"))
        self.ptsCheck.setText(_translate("MainWindow", "PTS"))
        self.steamliveCheck.setText(_translate("MainWindow", "Live"))
        self.steamptsCheck.setText(_translate("MainWindow", "PTS"))
        self.progressBar.setFormat(_translate("MainWindow", "%p%"))
        self.label.setText(_translate("MainWindow", "Overwrite options"))
        self.label_2.setText(_translate("MainWindow", "Logs"))
        self.label_4.setText(_translate("MainWindow", "Mod List"))
        self.warningLabel.setText(_translate("MainWindow", "This option will generate\nclean files and overwrite\nany existing ones\nThis will clear settings of\n generated files"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionAbout.setText(_translate("MainWindow", "About"))
        self.lineEdit.setPlaceholderText(_translate("MainWindow", "Custom mod folders, separate multiple with ; Folders must contain tmod files."))
        self.pushButton_2.setText(_translate("MainWindow", "Add Custom Folders"))

    def Log(self, Message, clear=False):
        if clear:
            self.logLabel.setText("")
        text = self.logLabel.toPlainText()
        self.logLabel.setText(text+f"{Message}\n")
        self.logLabel.moveCursor(QtGui.QTextCursor.End)

  # Connections

    def cfgFolderButtonClicked(self):
        os.startfile(self.ModCfgs)

    def addCustomFolders(self):
        self.refreshMods()

    def aboutDialog(self):
        self.MainWindow.setEnabled(False)
        About = QtWidgets.QDialog()
        ui = Ui_About()
        ui.setupUi(About)
        About.exec()
        self.MainWindow.setEnabled(True)

    def CustomFoldersChanged(self):
        self.pushButton_2.setEnabled(False)
        if not self.lineEdit.text():
            self.pushButton_2.setText("Add Custom Folders")
            return self.pushButton_2.setStyleSheet("background-color: #313233")
        self.pushButton_2.setText("Invalid Custom Folders")
        self.pushButton_2.setStyleSheet("background-color: rgb(128, 0, 0);")
        if self.ValidateCustomDirectories():
            self.pushButton_2.setText("Add Custom Folders")
            self.pushButton_2.setStyleSheet("background-color: rgb(0, 128, 0);")
            self.pushButton_2.setEnabled(True)

    def SteamLiveCheckChanged(self):
        self.steamptsCheck.setChecked(self.steamliveCheck.isChecked())
        self.refreshMods(True)

    def SteamPTSCheckChanged(self):
        self.steamliveCheck.setChecked(self.steamptsCheck.isChecked())
        self.refreshMods(True)

    def LiveCheckChanged(self):
        self.refreshMods(True)
    
    def PTSCheckChanged(self):
        self.refreshMods(True)

    def refreshMods(self, nocheck=False):
        if nocheck:
            GamePaths = self.GamePaths
        else:
            GamePaths = self.GamePaths = self.checkAvailableDirectories()
        if not GamePaths:
            self.pushButton.setEnabled(False)
            self.Log("Are you sure you installed Trove correctly?")
            return
        self.Log(f"Detected {len(GamePaths)} Trove directories", clear=True)
        for Type, Directory in GamePaths:
            self.Log(f"\t-> {Directory}")
        self.Mods = []
        for Type, ModsFolder in GamePaths:
            self.Mods.extend(
                [
                    [Type if Type != "Glyph" else str(m).replace(str(m.parent.parent.parent), "").replace(SteamTroveID, "Steam").split("\\")[1], m] 
                    for m in (self.GetAllFiles(ModsFolder) if Type == "Steam" else ModsFolder.iterdir())
                    if m.suffix == ".tmod"
                ]
            )
        model = QtGui.QStandardItemModel()
        self.listView.setModel(model)
        self.Mods.sort(key=lambda x: [x[0].lower(), x[1].name.lower()])
        for ModType, ModFile in copy(self.Mods):
            if ModType == "Live" and not self.liveCheck.isChecked():
                self.Mods.remove([ModType, ModFile])
                continue
            elif ModType == "PTS" and not self.ptsCheck.isChecked():
                self.Mods.remove([ModType, ModFile])
                continue
            elif ModType == "Steam" and not self.steamliveCheck.isChecked():
                self.Mods.remove([ModType, ModFile])
                continue
            ModName = f"{ModType}/{ModFile.name}"
            item = QtGui.QStandardItem(ModName)
            model.appendRow(item)

    def comboBoxChanged(self):
        if self.comboBox.currentText() == "Overwrite all files":
            self.warningLabel.setStyleSheet("color:rgba(255,0,0,1)")
        else:
            self.warningLabel.setStyleSheet("color:rgba(255,0,0,0)")

    def runGenerateButton(self):
        asyncio.create_task(self.generateButtonClicked())

    async def generateButtonClicked(self):
        if self.running:
            self.pushButton.setText("Stopping...")
            self.pushButton.setStyleSheet("background-color:rgb(128,128,0)")
            self.pushButton.setEnabled(False)
            self.running = False
            return
        self.running = True
        self.pushButton.setText("Stop Generating")
        self.pushButton.setStyleSheet("background-color:rgb(128,0,0)")
        self.CheckedMods = []
        if not self.ModCache.exists():
            self.ModCache.mkdir()
        for i, (ModType, ModPath) in enumerate(self.Mods, 1):
            if not self.running:
                self.pushButton.setText("Generate Configs")
                self.pushButton.setStyleSheet("background-color:rgb(0,128,0)")
                self.pushButton.setEnabled(True)
                self.Log("Stopped generating. Operation cancelled by user.")
                return
            self.currentLabel.setText(f"{ModPath.name}")
            self.CheckModConfig(ModType, ModPath)
            self.progressBar.setValue(int(i / len(self.Mods) * 100))
        self.pushButton.setText("Generate Configs")
        self.pushButton.setStyleSheet("background-color:rgb(0,128,0)")
        self.running = False
        self.Log("Finished generating logs.")
                    
    def CheckModConfig(self, ModType, ModPath):
        ModName = ModPath.stem
        ConfigFileName = self.ModCfgs.joinpath(f"{ModName}.cfg")
        if ModName in self.CheckedMods:
            return self.Log(f"[{ModType}] Skipped mod (Already generated): " + ModName)
        if ConfigFileName.exists():
            if self.comboBox.currentText == "Overwrite all files":
                self.Log(f"[{ModType}] Overwriting mod config: " + ModName)
            elif self.comboBox.currentText() == "Overwrite empty files" and len(ConfigFileName.read_text()) == 0:
                self.Log(f"[{ModType}] Overwriting mod config (Config is empty): " + ModName)
            elif self.comboBox.currentText() == "No Overwrites":
                return self.Log(f"[{ModType}] Skipped mod (Already exists): " + ModName)
            else:
                return self.Log(f"[{ModType}] Skipped mod (Already exists): " + ModName)
        try:
            TModMetadata = self.ReadTMod(ModPath)
        except UnicodeDecodeError:
            return self.Log(f"[{ModType}] Skipped mod (Unicode error): " + ModName)
        SWFFiles = [Path(File) for File in TModMetadata["Files"] if File.endswith(".swf")]
        if SWFFiles:
            with open(ConfigFileName, "w+") as ConfigFile:
                ConfigFile.write("\n\n\n".join([f"[{SWFFile.name}]" for SWFFile in SWFFiles]))
                self.Log(f"[{ModType}] Generated config for: " + ModName)
        self.CheckedMods.append(ModName)
        return

    def ReadTMod(self, ModPath):
        Metadata = {}
        reader = BinaryReader(ModPath.read_bytes())
        Metadata["HeaderSize"] = reader.read_uint64()
        Metadata["TModVersion"] = reader.read_uint16()
        Metadata["PropertyCount"] = reader.read_uint16()
        Metadata["Properties"] = {}
        for _ in range(Metadata["PropertyCount"]):
            key = reader.read_str(reader.read_uint8()) 
            value = reader.read_str(reader.read_uint8())
            if not isNullOrWhiteSpace(key) and not isNullOrWhiteSpace(value):
                Metadata["Properties"][key] = value
        Metadata["Files"] = []
        while reader.pos() < Metadata["HeaderSize"]:
            FileName = reader.read_str(reader.read_uint8())
            Metadata["FileIndex"] = ReadVarInt7Bit(reader, reader.pos())
            Metadata["FileOffset"] = ReadVarInt7Bit(reader, reader.pos())
            Metadata["FileSize"] = ReadVarInt7Bit(reader, reader.pos())
            Metadata["FileHash"] = ReadVarInt7Bit(reader, reader.pos())
            Metadata["Files"].append(FileName)
        return Metadata

    def SanityCheck(self, Path, Registry=True):
        """
        This checks if directories exist and are valid.
        Returns alerts when invalid directories are found.
        """
        ModsFolder = Path.joinpath("mods")
        if not ModsFolder.exists():
            if Registry:
                self.Log("Directory found in Registry but 'mods' folder wasn't found:\n\t-> "+str(ModsFolder.absolute())+"\n\n")
            else:
                self.Log("Directory found but 'mods' folder wasn't found:\n\t -> "+str(ModsFolder.absolute())+"\n\n")
            return False
        return True

    def CreateDirectory(self, Path: Path, Warn=False):
        """
        Creates a directory if it doesn't exist
        """
        if not Path.exists():
            Path.mkdir()
            if Warn:
                self.Log(f"Created necessary directory:\n\t-> '{Path}'")

    def GetKeys(self, key, path, look_for):
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

    def SearchGlyphRegistry(self):
        """
        Looks for the 'Uninstall' path where Glyph keys are stored
        """
        for Hive in Hives:
            for Node in Nodes:
                try:
                    LookPath = "SOFTWARE\\"+Node+TrovePath
                    RegistryKeyPath = winreg.OpenKeyEx(Hive, LookPath)
                    Keys = self.GetKeys(RegistryKeyPath, LookPath, TroveKey)
                    for Key in Keys:
                        yield winreg.OpenKeyEx(Hive, Key)
                except WindowsError:
                    ...

    def SearchSteamRegistry(self):
        """
        Looks for the steam path where Trove is installed
        """
        for Hive in Hives:
            for Node in Nodes:
                try:
                    LookPath = "SOFTWARE\\"+Node+SteamPath
                    RegistryKeyPath = winreg.OpenKeyEx(Hive, LookPath)
                    Keys = self.GetKeys(RegistryKeyPath, LookPath, SteamKey)
                    for Key in Keys:
                        yield winreg.OpenKeyEx(Hive, Key)
                except WindowsError:
                    ...

    def GetTroveLocations(self):
        """
        This is a generator that returns Trove Directories found in registry.
        """
        for Key in self.SearchGlyphRegistry():
            try:
                GamePath = winreg.QueryValueEx(Key, TroveInstallValue)[0] # Extracts path out of value in Glyph keys
            except WindowsError:
                continue
            if self.SanityCheck(Path(GamePath)):
                yield ["Glyph", Path(GamePath).joinpath("mods")]
        self.SteamPath = None
        for Key in self.SearchSteamRegistry():
            try:
                self.SteamPath = Path(winreg.QueryValueEx(Key, SteamInstallValue)[0]) # Extracts path out of value in Steam keys
            except WindowsError:
                continue
        if self.SteamPath.exists():
            GamePath = Path(self.SteamPath).joinpath("steamapps", "workshop", "content", SteamTroveID)
            if not GamePath.exists():
                self.Log("Steam path found but no mods are present.")
            else:
                yield ["Steam", GamePath]

    def checkAvailableDirectories(self):
        self.liveCheck.setEnabled(False)
        self.ptsCheck.setEnabled(False)
        self.steamliveCheck.setEnabled(False)
        self.steamptsCheck.setEnabled(False)
        self.GamePaths = GamePaths = [[t,f] for t, f in self.GetTroveLocations()]
        for GamePath in GamePaths:
            self.pushButton.setEnabled(True)
            self.pushButton.setStyleSheet("background-color: rgb(0, 128, 0)")
            if GamePath[0] == "Glyph":
                getattr(self, f"{GamePath[1].parent.stem.lower()}Check").setEnabled(True)
                getattr(self, f"{GamePath[1].parent.stem.lower()}Check").setChecked(True)
            elif GamePath[0] == "Steam":
                getattr(self, f"steamliveCheck").setEnabled(True)
                getattr(self, f"steamliveCheck").setChecked(True)
                getattr(self, f"steamptsCheck").setEnabled(True)
                getattr(self, f"steamptsCheck").setChecked(True)
        return GamePaths + self.ListCustomDirectories()[0]

    def ValidateCustomDirectories(self):
        return self.ListCustomDirectories()[1]

    def ListCustomDirectories(self):
        if not self.lineEdit.text():
            return list(), 0
        folders = self.lineEdit.text().split(";")
        valid = []
        for i, folder in enumerate(folders, 1):
            if (ModsFolder := Path(folder)).exists() and ModsFolder.is_dir():
                for File in ModsFolder.iterdir():
                    if File.suffix == ".tmod":
                        valid.append([f"Custom{i}", ModsFolder])
                        break
        return valid, len(folders) == len(valid)

    def GetAllFiles(self, Folder):
        """
        Gets all files in a directory
        """
        for File in Folder.iterdir():
            FilePath = Folder.joinpath(File)
            if FilePath.is_dir():
                for i in self.GetAllFiles(FilePath):
                    yield i
            else:
                yield File

    
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        MainWindow = QtWidgets.QMainWindow()
        ui = SlyTroveConfigGenerator()
        ui.setupUi(MainWindow)
        MainWindow.show()
        loop.run_forever()
