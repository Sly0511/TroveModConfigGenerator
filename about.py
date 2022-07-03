import sys
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_About(object):
    def setupUi(self, About):
        About.setObjectName("About")
        About.resize(506, 154)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(About.sizePolicy().hasHeightForWidth())
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(str(Path(sys._MEIPASS).joinpath("images", "AppLogo.png"))), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        About.setWindowIcon(icon)
        About.setSizePolicy(sizePolicy)
        About.setStyleSheet("background: #313233;color: #bbb")
        self.label = QtWidgets.QLabel(About)
        self.label.setGeometry(QtCore.QRect(10, 100, 71, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(About)
        self.label_2.setGeometry(QtCore.QRect(20, 125, 47, 13))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(About)
        self.label_3.setGeometry(QtCore.QRect(10, 10, 47, 13))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(About)
        self.label_4.setGeometry(QtCore.QRect(40, 30, 451, 61))
        self.label_4.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_4.setWordWrap(True)
        self.label_4.setObjectName("label_4")
        self.label_6 = QtWidgets.QLabel(About)
        self.label_6.setGeometry(QtCore.QRect(120, 100, 71, 16))
        self.label_6.setObjectName("label_6")
        self.label_5 = QtWidgets.QLabel(About)
        self.label_5.setGeometry(QtCore.QRect(130, 125, 191, 16))
        self.label_5.setStyleSheet("")
        self.label_5.setOpenExternalLinks(True)
        self.label_5.setObjectName("label_5")

        self.retranslateUi(About)
        QtCore.QMetaObject.connectSlotsByName(About)

    def retranslateUi(self, About):
        _translate = QtCore.QCoreApplication.translate
        About.setWindowTitle(_translate("About", "Dialog"))
        self.label.setText(_translate("About", "Developed by"))
        self.label_2.setText(_translate("About", "Sly"))
        self.label_3.setText(_translate("About", "About"))
        self.label_4.setText(_translate("About", "This tool was made to make it easier to generate configuration files for User Interface (UI)\nmods in Trove, it also can correct empty files or completely recreate said configuration files\n\nThis app is 100% free to use and code is open-source"))
        self.label_6.setText(_translate("About", "Github"))
        self.label_5.setText(_translate("About", "<a href=\"https://github.com/Sly0511/TroveModConfigGenerator\">Github/TroveModConfigGenerator</a>"))
