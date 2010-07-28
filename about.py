# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class About(QDialog):
	
    def __init__(self, parent=None):
	super (About,self).__init__(parent)
        self.setObjectName("Dialog")
        self.resize(349, 261)
        verticalLayout = QVBoxLayout(self)
        verticalLayout.setObjectName("verticalLayout")
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setObjectName("horizontalLayout")
        self.label = QLabel(self)
        self.label.setObjectName("label")
        horizontalLayout.addWidget(self.label)
        self.label_2 = QLabel(self)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        horizontalLayout.addWidget(self.label_2)
        verticalLayout.addLayout(horizontalLayout)
        self.pushButton = QPushButton(self)
        self.pushButton.setObjectName("pushButton")
        verticalLayout.addWidget(self.pushButton)

        self.retranslateUi()
        QObject.connect(self.pushButton, SIGNAL("clicked()"), self.close)

    def retranslateUi(self):
        self.setWindowTitle(QApplication.translate("Dialog", "About", None, QApplication.UnicodeUTF8))
        self.label.setText(QApplication.translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\"icons/logo.png\" /></p></body></html>", None, QApplication.UnicodeUTF8))

        self.label_2.setText(QApplication.translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">SAM (Syberoam Account Manager) is an application which manages multiple cyberoam accounts with features like auto-switching to subsequent cyberoam accounts as soon as internet usage reaches critical value or data transfer limit exceeds enabling students (mainly) to download large files without getting disconnected from the internet.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Version 1.0</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">(C) 2010 Viranch Mehta and Mohit Kothari</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a href=\"http://www.bitbucket.org/viranch/sam\"><span style=\" text-decoration: underline; color:#0057ae;\">Source Code</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p></body></html>", None, QApplication.UnicodeUTF8))
        self.pushButton.setText(QApplication.translate("Dialog", "OK", None, QApplication.UnicodeUTF8))
