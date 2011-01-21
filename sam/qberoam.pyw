#!/usr/bin/env python2
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import base64
import sys
import urllib2
import qrc_icon

class WrongPassword (Exception): pass
class DataTransferLimitExceeded (Exception): pass
class MultipleLoginError (Exception): pass

class Prompt (QDialog):

	def __init__(self, parent=None):
		super (Prompt, self).__init__(parent)
		
		self.timer = QTimer()
		self.timer.setInterval (3600000)
		
		unameLabel = QLabel ('Username:')
		self.unameEdit = QLineEdit()
		suffLabel = QLabel ('@da-iict.org')
		pwdLabel = QLabel ('Password:')
		self.pwdEdit = QLineEdit()
		self.pwdEdit.setEchoMode (QLineEdit.Password)
		self.pwdEdit.setText ('aaaa')
		self.buttonBox = QDialogButtonBox (QDialogButtonBox.Ok | QDialogButtonBox.Close)

		grid = QGridLayout ()
		grid.addWidget (unameLabel, 0, 0)
		grid.addWidget (self.unameEdit, 0, 1)
		grid.addWidget (suffLabel, 0, 2)
		grid.addWidget (pwdLabel, 1, 0)
		grid.addWidget (self.pwdEdit, 1, 1, 1, 2)
		grid.addWidget (self.buttonBox, 2, 0, 1, 3)
		self.setLayout (grid)
		self.setWindowTitle ('Qberoam')
		
		loginAction = self.createAction ('Log &In', self.login, ':/icons/network-connect.png')
		logoutAction = self.createAction ('Log &Out', self.logout, ':/icons/network-disconnect.png')
		quitAction = self.createAction ('&Quit', qApp.quit, ':/icons/application-exit.png', None, QKeySequence.Quit)
		
		self.tray = QSystemTrayIcon (self)
		self.tray.setIcon ( QIcon(':/icons/logo.png') )
		self.tray.setVisible(True)
		self.trayMenu = QMenu ()
		self.trayMenu.addAction ( loginAction )
		self.trayMenu.addAction ( logoutAction )
		self.trayMenu.addSeparator()
		self.trayMenu.addAction ( quitAction )
		self.tray.setContextMenu ( self.trayMenu )

		self.connect (self.buttonBox, SIGNAL('accepted()'), self.login)
		self.connect (self.buttonBox, SIGNAL('rejected()'), self.close)
		self.connect (self.timer, SIGNAL('timeout()'), self.relogin)
		self.connect (self.tray, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), self.toggleWindow)
		
		self.loadPrefs()

	def loadPrefs (self):
		settings = QSettings("DA-IICT","SAM")
		
		settings.beginGroup("Accounts")
		length = settings.value("Length").toInt()[0]
		username, password = str(settings.value("Account0").toString()).split('!@#$%')
		self.unameEdit.setText (str(username))
		self.pwdEdit.setText (base64.b64decode(str(password)))
		settings.endGroup()
		
	def relogin (self):
		self.login (True)

	def login (self, timerLogin=False):
		uid = str(self.unameEdit.text())
		pwd = str(self.pwdEdit.text())
		settings = QSettings('DA-IICT','SAM')
		settings.beginGroup('Accounts')
		settings.setValue ('Account0', uid+'!@#$%'+base64.b64encode(pwd))
		settings.endGroup()
		try:
			self._login(str(self.unameEdit.text()), str(pwd))
			self.timer.start()
			if not timerLogin:
				QMessageBox.information (self, 'Login successful', 'You have successfully logged in.')
		except DataTransferLimitExceeded:
			if not timerLogin:
				QMessageBox.critical (self, 'Limit Reached', 'The data transfer limit on this account has been exceeded.')
		except WrongPassword:
			if not timerLogin:
				QMessageBox.critical (self, 'Wrong Password', 'Could not authenticate. Make sure the username and password are correct.')
		except MultipleLoginError:
			if not timerLogin:
				QMessageBox.critical (self, 'Account in use', 'Someone is already using this account.')
		except IOError:
			if not timerLogin:
				QMessageBox.critical (self, 'Connection Error', 'Cannot contact the server. Please check your network connection.')

        def _login (self, uid, pwd):
		f = urllib2.urlopen("http://10.100.56.55:8090/corporate/servlet/CyberoamHTTPClient","mode=191&isAccessDenied=null&url=null&message=&username="+uid+"@da-iict.org&password="+pwd+"&saveinfo=saveinfo&login=Login", timeout=3)
		s = f.read()
		f.close()

                if 'Make+sure+your+password+is+correct' in s:
			raise WrongPassword
		if 'DataTransfer+limit+has+been+exceeded' in s:
			raise DataTransferLimitExceeded
		if 'Multiple+login+not+allowed' in s:
			raise MultipleLoginError
	
	def logout (self):
		uid = str(self.unameEdit.text())
		pwd = str(self.pwdEdit.text())
		try:
			f = urllib2.urlopen("http://10.100.56.55:8090/corporate/servlet/CyberoamHTTPClient","mode=193&isAccessDenied=null&url=null&message=&username="+uid+"@da-iict.org&password="+pwd+"&saveinfo=saveinfo&logout=Logout")
			s = f.read()
			f.close()
		except:
			pass
		self.timer.stop()
	
	def toggleWindow (self, reason):
		if reason == QSystemTrayIcon.Trigger:
			self.hide() if self.isVisible() else self.show()
	
	def closeEvent(self, event):
		if self.isVisible():
			self.hide()
		event.ignore()

	def createAction (self, text, slot=None, icon=None, tip=None, shortcut=None):
		action = QAction (text, self)
		if icon is not None:
			action.setIcon (QIcon (icon))
		if shortcut is not None:
			action.setShortcut (shortcut)
		if tip is not None:
			action.setToolTip (tip)
		if slot is not None:
			self.connect (action, SIGNAL('triggered()'), slot)
		return action

app = QApplication (sys.argv)
p = Prompt()
p.show()
app.exec_()
