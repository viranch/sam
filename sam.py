#!/usr/bin/env python
#
# Author: Viranch Mehta <viranch.mehta@gmail.com>
#

import sys
import time
import os
import Cyberoam
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import bz2
from prompt import *
from settings import *
from about import *
import qrc_icon

DOMAIN = '@da-iict.org'
GREEN = ':/icons/ball-green.png'
RED = ':/icons/ball-red.png'
YELLOW = ':/icons/ball-yellow.png'
acc_file = '.samacc.conf'
conf_file = '.samconf.conf'

class Config ():

	def __init__ (self):
		self.switch_on_limit = False
		self.switch_on_critical = False
		self.switch_on_wrongPass = False
		self.balloons = True
		self.balloon_notify_critical = True
		self.balloon_limit = 95.0 #MB
		self.update_quota_after = 360 #seconds = 6 mins
		self.relogin_after = 3000 #seconds = 50 mins
		self.critical_quota_limit = 95.0 #MB
		self.DOMAIN = '@da-iict.org'

class Account ():

	def __init__ (self, parent, login_id='', passwd='', no=-1):
		self.username = login_id
		self.passwd = passwd
		self.acc_no = no
		self.parent = parent

	def login (self):
		try:
			self.parent.table.topLevelItem(self.acc_no).setText (1, 'Logging in')
			Cyberoam.login (self.username+DOMAIN, self.passwd)
			return True
		except Cyberoam.DataTransferLimitExceeded:
			self.parent.table.topLevelItem(self.acc_no).setText (1, 'Limit Reached')
		except Cyberoam.WrongPassword:
			self.parent.table.topLevelItem(self.acc_no).setText (1, 'Wrong Password')
		except IOError:
			self.parent.table.topLevelItem(self.acc_no).setText (1, 'Network Error')
			QMessageBox.critical (self.parent, 'Network Error', 'Error with network connection.')
		return False

	def logout (self):
		try:
			self.getQuota ()
			Cyberoam.logout (self.username+DOMAIN, self.passwd)
			return True
		except IOError:
			QMessageBox.critical (self.parent, 'Network Error', 'Error with network connection.')
		return False

	def getQuota (self):
		try:
			self.parent.table.topLevelItem(self.acc_no).setText (1, 'Checking usage')
			quota = Cyberoam.netUsage (self.username+DOMAIN, self.passwd)
			self.parent.table.topLevelItem(self.acc_no).setText (3, quota[1])
			return True
		except Cyberoam.DataTransferLimitExceeded:
			self.parent.table.topLevelItem(self.acc_no).setText (1, 'Limit Reached')
			self.parent.table.topLevelItem(self.acc_no).setText (3, '0.00 KB')
		except Cyberoam.WrongPassword:
			self.parent.table.topLevelItem(self.acc_no).setText (1, 'Wrong Password')
		except IOError:
			self.parent.table.topLevelItem(self.acc_no).setText (1, 'Network Error')
			QMessageBox.critical (self.parent, 'Network Error', 'Error with network connection.')
		return False

class MainWindow (QMainWindow):

	def __init__(self, parent=None):
		super (MainWindow, self).__init__(parent)

		self.accounts = []
		self.bars = []
		self.settings = Config()
		self.loginTimer = QTimer()
		self.quotaTimer = QTimer()
		self.currentLogin = -1

		self.toolbar = self.addToolBar ('Toolbar')
		self.status = self.statusBar()
		self.status.setSizeGripEnabled (False)

		loginAction = self.createAction ('Log &In', self.login, ':/icons/network-connect.png', 'Log In')
		logoutAction = self.createAction ('Log &Out', self.logout, ':/icons/network-disconnect.png', 'Log Out')
		quotaAction = self.createAction ('Get Usage', self.getQuota, ':/icons/view-refresh.png', 'Refresh Quota', QKeySequence.Refresh)
		newUserAction = self.createAction ('&New...', self.addAccount, ':/icons/user-add-icon.png', 'Create User', QKeySequence.New)
		rmUserAction = self.createAction ('Remove', self.rmAccount, ':/icons/user-remove-icon.png', 'Remove User', QKeySequence.Delete)
		editUserAction = self.createAction ('&Edit...', self.editAccount, ':/icons/user-icon.png', 'Edit User')
		clearAction = self.createAction ('&Clear All', self.clearList, ':/icons/edit-clear-list.png', 'Clear Users list')
		upAction = self.createAction ('Up', self.up, ':/icons/up-icon.png', 'Move up')
		downAction = self.createAction ('Down', self.down, ':/icons/down-icon.png', 'Move down')
		balloonAction = self.createAction ('Enable balloon popups', self.setBalloon, None, 'Enable balloon popups', None, True)
		balloonAction.setChecked (self.settings.balloons)
		prefsAction = self.createAction ('&Configure SAM', self.configure, ':/icons/configure.png', 'Configure SAM', QKeySequence.Preferences)
		aboutAction = self.createAction ('&About SAM', self.about, ':/icons/help-about.png', 'About SAM')
		quitAction = self.createAction ('&Quit', self.quit, ':/icons/application-exit.png', 'Quit SAM', QKeySequence.Quit)
		
		menubar = self.menuBar()
		userMenu = menubar.addMenu ('&Users')
		userMenu.addAction (newUserAction)
		userMenu.addSeparator()
		userMenu.addAction (editUserAction)
		userMenu.addAction (rmUserAction)
		userMenu.addAction (clearAction)
		userMenu.addSeparator()
		userMenu.addAction (quitAction)
		actionsMenu = menubar.addMenu ('&Actions')
		actionsMenu.addAction (loginAction)
		actionsMenu.addAction (quotaAction)
		actionsMenu.addAction (logoutAction)
		settingsMenu = menubar.addMenu ('&Settings')
		settingsMenu.addAction (balloonAction)
		settingsMenu.addAction (prefsAction)
		helpMenu = menubar.addMenu ('&Help')
		helpMenu.addAction (aboutAction)
		
		self.toolbar.addAction ( newUserAction )
		self.toolbar.addAction ( rmUserAction )
		self.toolbar.addSeparator()
		self.toolbar.addAction ( loginAction )
		self.toolbar.addAction ( quotaAction )
		self.toolbar.addAction ( logoutAction )
		self.toolbar.addSeparator()
		self.toolbar.addAction ( upAction )
		self.toolbar.addAction ( downAction )
		self.toolbar.addSeparator()
		self.toolbar.addAction ( prefsAction )
		self.toolbar.addAction ( aboutAction )
		self.toolbar.addAction ( quitAction )

		self.table = QTreeWidget ()
		self.table.setRootIsDecorated (False)
		headers = self.table.headerItem()
		headers.setText (0, 'ID')
		headers.setText (1, 'Status')
		headers.setText (2, 'Usage')
		headers.setText (3, 'Remaining')
		self.table.header().resizeSection (0, 160)

		self.setCentralWidget (self.table)
		self.setWindowIcon (QIcon(':/icons/logo.png'))
		self.setWindowTitle ('SAM - Syberoam Account Manager')
		self.resize(498, self.size().height())
		self.tray = QSystemTrayIcon ()
		self.tray.setIcon ( QIcon(':/icons/logo.png') )
		self.tray.setVisible(True)
		self.trayMenu = QMenu ()
		self.trayMenu.addAction ( balloonAction )
		self.trayMenu.addSeparator()
		self.trayMenu.addAction ( loginAction )
		self.trayMenu.addAction ( quotaAction )
		self.trayMenu.addAction ( logoutAction )
		self.trayMenu.addSeparator()
		self.trayMenu.addAction ( quitAction )
		self.tray.setContextMenu ( self.trayMenu )
		
		self.connect ( self.tray, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), self.toggleWindow )
		self.connect ( self.table, SIGNAL('itemChanged(QTreeWidgetItem*,int)'), self.updateUi )
		self.connect ( self.table, SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'), self.login )
		self.connect ( self.loginTimer, SIGNAL('timeout()'), self.reLogin )
		self.connect ( self.quotaTimer, SIGNAL('timeout()'), self.refreshQuota )

	def readConfs (self):
		try:
			conf = open(os.getenv('HOME')+'/'+conf_file,'r')
			pref = conf.readlines()
			
			bools = pref[0]
			self.settings.switch_on_limit = bool(int(bools[0]))
			self.settings.switch_on_critical = bool(int(bools[1]))
			self.settings.switch_on_wrongPass = bool(int(bools[2]))
			self.settings.balloon_notify_critical = bool(int(bools[3]))
			self.settings.balloons = bool(int(bools[4]))
			
			self.settings.update_quota_after = int(pref[1])
			self.settings.relogin_after = int(pref[2])
			self.settings.critical_quota_limit = float(pref[3])
			self.settings.balloon_limit = float(pref[4])
			conf.close()
			
			conf = open ( os.getenv('HOME')+'/'+acc_file, 'r' )
			accounts = conf.read()
			conf.close()
			toks = accounts.split('\n\n\n',1)
			length = int(toks[0])
			data = toks[1].split('!@#$%^&*')
			i=0
			while i!= 2*length:
				user = data[i]
				crypt_passwd = data[i+1]
				passwd = bz2.decompress(crypt_passwd)
				index = len(passwd)
				passwd = passwd[0:index]
				self.addAccount(user,passwd)
				i = i+2
			conf.close()
		except: pass

	def setBalloon (self):
		self.settings.balloons = not self.settings.balloons

	def closeEvent(self, event):
		if self.isVisible():
			self.hide()
		event.ignore()

	def updateUi (self, item, column):
		if column==1:
			status = str(item.text(1))
			if status == 'Logged in':
				item.setIcon (0, QIcon(GREEN))
				if self.settings.balloons:
					self.tray.showMessage ('Message from Cyberoam', item.text(0)+': '+status)
			elif status == 'Logged out' or status == 'Checking usage' or status == '' or status=='Logging in':
				if status != 'Checking usage' or self.currentLogin != self.table.indexOfTopLevelItem(item):
					item.setIcon (0, QIcon(YELLOW))
			else:
				item.setIcon (0, QIcon(RED))
				self.loginTimer.stop()
				self.quotaTimer.stop()
				if self.settings.balloons:
					self.tray.showMessage ('Message from Cyberoam', item.text(0)+': '+status)
				if status=='Critical Quota' and self.settings.switch_on_critical:
					self.switch(2)
				elif status=='Limit Reached' and (self.settings.switch_on_limit or self.settings.switch_on_critical):
					self.switch(1)
				else:
					self.currentLogin = -1
		elif column == 3:
			quota = str(item.text(3)).split()
			rem = float(quota[0]) if quota[1] == 'KB' else float(quota[0])*1024
			used = 102400 - rem
			self.bars[self.table.indexOfTopLevelItem(item)][1] = int(round(used))
			self.table.itemWidget (item, 2).setValue(int(round(used)))
			if self.settings.switch_on_critical and used>=self.settings.critical_quota_limit and rem>0:
				item.setText(1, 'Critical quota')

	def configure (self):
		dlg = SettingsDlg(self)
		if dlg.exec_():
			self.settings.relogin_after = dlg.loginSpin.value()*60
			self.settings.update_quota_after = dlg.quotaSpin.value()*60
			self.settings.switch_on_limit = dlg.quotaSwitchCheck.isChecked() and dlg.usageCheck.isChecked() and dlg.autoSwitchCheck.isChecked()
			self.settings.switch_on_critical = dlg.criticalSwitchCheck.isChecked() and dlg.usageCheck.isChecked() and  dlg.autoSwitchCheck.isChecked()
			self.settings.critical_quota_limit = dlg.criticalSpin.value()*1024
			self.settings.switch_on_wrongPass = dlg.wrongPassCheck.isChecked() and dlg.autoSwitchCheck.isChecked()
			self.settings.balloons = dlg.balloonPopups.isChecked()
			self.settings.balloon_notify_critical = dlg.balloonCheck.isChecked() and self.settings.balloons
			self.settings.balloon_limit = dlg.balloonSpin.value()*1024

	def switch (self, reason=0):
		if not (self.settings.switch_on_limit or self.settings.switch_on_critical) or self.currentLogin<0:
			self.currentLogin = -1
			return None
		next = self.table.topLevelItem (self.currentLogin+1)
		if next is not None:
			if reason == 2: #Critical quota
				self.logout ()
			self.login ( next, 0, True )

	def login (self, item=None, column=-1, switch=False):
		self.loginTimer.stop()
		self.quotaTimer.stop()
		if item is None:
			item = self.table.currentItem()
		elif switch:
			self.table.setCurrentItem (item)
		curr = self.table.indexOfTopLevelItem ( item )
		if curr<0:
			return None
		prev = self.currentLogin
		self.currentLogin = curr
		if self.accounts[curr].login():
			if self.accounts[curr].getQuota():
				item.setText (1, 'Logged in')
			self.loginTimer.start ( self.settings.relogin_after*1000 )
			self.quotaTimer.start ( self.settings.update_quota_after*1000 )
			if prev!=-1 and prev!=self.currentLogin and not switch:
				self.table.topLevelItem(prev).setText (1, 'Logged out')
		elif curr == (len(self.accounts)-1):
			self.currentLogin = -1

	def reLogin (self):
		self.login (self.table.topLevelItem(self.currentLogin))

	def logout (self, acc_no=None):
		if acc_no is None:
			acc_no = self.currentLogin
 		if acc_no<0:
			return None
		if self.accounts[acc_no].logout():
			self.table.topLevelItem(acc_no).setText (1, 'Logged out')
		self.loginTimer.stop()
		self.quotaTimer.stop()
		self.currentLogin = -1

	def refreshQuota (self):
		self.getQuota( self.table.topLevelItem(self.currentLogin) )

	def getQuota (self, item=None):
		if item is None:
			item = self.table.currentItem()
		curr = self.table.indexOfTopLevelItem ( item )
		if curr == self.currentLogin:
			if self.accounts[curr].getQuota():
				item.setText (1, 'Logged in')
			return False
		return self.accounts[curr].getQuota()

	def addAccount (self, uid=None, pwd=None):
		if uid is not None and pwd is not None:
			new = QTreeWidgetItem ([uid, '', '', ''])
			new.setIcon (0, QIcon(YELLOW))
			self.table.addTopLevelItem ( new )
			self.bars.append( [QProgressBar(), 0] )
			self.bars[-1][0].setRange (0, 102400)
			self.table.setItemWidget (new, 2, self.bars[-1][0])
			self.accounts.append ( Account(self, uid, pwd, len(self.accounts)) )
			self.status.showMessage (uid+' added', 5000)
			if self.getQuota ( new ):
				new.setText (1, '')
		else:
			dlg = Prompt(self)
			dlg.setWindowIcon (QIcon(':/icons/list-add-user.png'))
			if dlg.exec_():
				self.addAccount(str(dlg.unameEdit.text()), str(dlg.pwdEdit.text()))

	def editAccount (self):
		current = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		dlg = Prompt(self, self.accounts[current].username)
		dlg.setWindowIcon (QIcon(':/icons/user-properties.png'))
		if dlg.exec_():
			self.table.currentItem().setText (0, dlg.unameEdit.text())
			self.accounts[current].username = str(dlg.unameEdit.text())
			if str(dlg.pwdEdit.text()) is not '':
				self.accounts[current].passwd = str( dlg.pwdEdit.text() )
			if current == self.currentLogin:
				self.reLogin()
			elif self.getQuota ( self.table.currentItem() ):
				self.table.currentItem().setText (1, '')

	def rmAccount (self):
		if len(self.accounts) == 0:
			self.status.showMessage ('Nothing to remove!', 5000)
			return None
		current = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		popped = self.table.takeTopLevelItem (current)
		rm = self.accounts.pop (current)
		self.status.showMessage (rm.username+' removed', 5000)
		self.bars.pop (current)
		self.updateBars()
		return popped, rm

	def clearList (self):
		if len(self.accounts)==0:
			self.status.showMessage ('List already clear!', 5000)
			return None
		self.table.clear()
		self.accounts = []
		self.bars = []
		self.status.showMessage ('List cleared', 5000)

	def move (self, to):
		if len(self.accounts)<2:
			return None
		current = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		bound = (to>0) * (len(self.accounts)-1)
		if current == bound:
			return None
		if current == self.currentLogin:
			self.currentLogin += to
		elif current+to == self.currentLogin:
			self.currentLogin -= to

		self.bars[current][1] = self.bars[current+to][0].value()
		self.bars[current+to][1] = self.bars[current][0].value()

		self.table.insertTopLevelItem ( current+to, self.table.takeTopLevelItem (current) )
		self.accounts.insert ( current+to, self.accounts.pop (current) )
		self.table.setCurrentItem ( self.table.topLevelItem(current+to) )
		self.updateBars()

	def up (self): self.move (-1)

	def down (self): self.move (1)

	def updateBars (self):
		for i in range(0,len(self.bars)):
			self.bars[i][0] = QProgressBar()
			self.bars[i][0].setRange(0,102400)
			self.bars[i][0].setValue(self.bars[i][1])
			self.table.setItemWidget(self.table.topLevelItem(i),2,self.bars[i][0])
			self.accounts[i].acc_no = i

	def about (self):
		dlg = About()
		dlg.exec_()

	def quit (self):
		self.loginTimer.stop()
		self.quotaTimer.stop()
		
		conf = open ( os.getenv('HOME')+'/'+acc_file, 'w' )
		length = str(len(self.accounts))
		conf.write(length+'\n\n\n')
		for ac in self.accounts:
			temp = ac.passwd
			ciphertext = bz2.compress(temp)
			temp = ac.username+'!@#$%^&*'+ciphertext+'!@#$%^&*'
			conf.write(temp)
		conf.close()
		
		conf = open(os.getenv('HOME')+'/'+conf_file,'w')
		conf.write (str(int(self.settings.switch_on_limit)))
		conf.write (str(int(self.settings.switch_on_critical)))
		conf.write (str(int(self.settings.switch_on_wrongPass)))
		conf.write (str(int(self.settings.balloon_notify_critical)))
		conf.write (str(int(self.settings.balloons))+'\n')
		conf.write (str(self.settings.update_quota_after)+'\n')
		conf.write (str(self.settings.relogin_after)+'\n')
		conf.write (str(self.settings.critical_quota_limit)+'\n')
		conf.write (str(self.settings.balloon_limit)+'\n')
		conf.close()
		
		qApp.quit()

	def toggleWindow (self, reason):
		if reason == QSystemTrayIcon.Trigger:
			self.hide() if self.isVisible() else self.show()

	def createAction (self, text, slot=None, icon=None, tip=None, shortcut=None, checkable=None, signal='triggered()'):
		action = QAction (text, self)
		if icon is not None:
			action.setIcon (QIcon (icon))
		if shortcut is not None:
			action.setShortcut (shortcut)
		if tip is not None:
			action.setToolTip (tip)
			action.setStatusTip (tip)
		if slot is not None:
			self.connect (action, SIGNAL(signal), slot)
		if checkable:
			action.setCheckable (True)
		return action

if __name__=='__main__':
	app = QApplication (sys.argv)
	window = MainWindow()
	window.show()
	window.readConfs()
	app.exec_()
