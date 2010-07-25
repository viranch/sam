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

DOMAIN = '@da-iict.org'
GREEN = 'icons/ball-green.png'
RED = 'icons/ball-red.png'
YELLOW = 'icons/ball-yellow.png'

class Config ():

	def __init__ (self):
		self.update_quota_after = 900 #seconds = 15 mins
		self.relogin_after = 3000 #seconds = 50 mins
		self.critical_quota_limit = 95.0 #MB

class UpdateQuota (QThread):

	def __init__(self, parent=None):
		super (UpdateQuota, self).__init__(parent)
		self.parent = parent
		self.acc_no = -1
		self.kill = False
		self.doNow = False

	def run (self, acc_no=None):
		once = True
		if acc_no is None:
			acc_no = self.acc_no
			once = False
		while not self.kill:
			if acc_no==-1:
				continue
			this = self.parent.table.topLevelItem(acc_no)
			uname = self.parent.accounts[acc_no].username+'@da-iict.org'
			passwd = self.parent.accounts[acc_no].passwd
			quota = Cyberoam.netUsage ( uname, passwd )
			#this.setText (2, quota[0])
			this.setText (3, quota[1])
			if self.parent.switch:
				used=quota[0].split()
				if used[1]=='MB' and float(used[0])>=critical_quota_limit:
					self.parent.table.topLevelItem(acc_no).setText(1, 'Critical quota')
					self.parent.login (self.parent.table.topLevelItem(acc_no+1))
			if once:
				break
			self.sleep (self.parent.settings.update_quota_after)

	def sleep (self, sec):
		i = 0
		while not self.kill and i<sec and not self.doNow:
			time.sleep(1)
			i += 1
		self.doNow = False

class StayLogin (QThread):
	
	def __init__(self, parent=None):
		super (StayLogin, self).__init__(parent)
		self.parent = parent
		self.curr = -1
		self.kill = False
		self.doNow = False

	def run (self):
		self.parent.quotaThread.kill = False
		if self.curr<0:
			return None
		while self.curr<len(self.parent.accounts) and not self.kill:
			this = self.parent.table.topLevelItem(self.curr)
			this.setText(1, 'Logging in')
			try:
				uname = self.parent.accounts[self.curr].username+'@da-iict.org'
				passwd = self.parent.accounts[self.curr].passwd
				Cyberoam.login ( uname, passwd )
				self.parent.quotaThread.acc_no = self.curr
				if not self.parent.quotaThread.isRunning():
					self.parent.quotaThread.start()
				else:
					self.parent.quotaThread.doNow = True
				this.setText (1, 'Logged in')
				self.sleep (self.parent.settings.relogin_after)
			except Cyberoam.DataTransferLimitExceeded:
				self.parent.quotaThread.run (self.curr)
				this.setText (1, 'Limit Reached')
				if not self.parent.switch:
					break
				self.curr+=1
			except Cyberoam.WrongPassword:
				this.setText (1, 'Wrong Password')
				if not self.parent.switch:
					break
				self.curr+=1
		self.parent.quotaThread.kill = True
		self.curr = -1

	def sleep (self, sec):
		i = 0
		while not self.kill and i<sec and not self.doNow:
			time.sleep(1)
			i += 1
		self.doNow = False

class Account ():

	def __init__ (self, login_id='', passwd=''):
		self.username = login_id
		self.passwd = passwd

class Prompt (QDialog):

	def __init__(self, parent=None, uid=None):
		super (Prompt, self).__init__(parent)
		self.acc = Account()
		
		self.buttonBox = QDialogButtonBox (QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
		unameLabel = QLabel ('Username:')
		suffLabel = QLabel (DOMAIN)
		pwdLabel = QLabel ('Password:')
		self.unameEdit = QLineEdit()
		if uid is not None:
			self.unameEdit.setText ( uid )
			self.unameEdit.selectAll()
		self.pwdEdit = QLineEdit()
		self.pwdEdit.setEchoMode (QLineEdit.Password)

		grid = QGridLayout ()
		grid.addWidget (unameLabel, 0, 0)
		grid.addWidget (self.unameEdit, 0, 1)
		grid.addWidget (suffLabel, 0, 2)
		grid.addWidget (pwdLabel, 1, 0)
		grid.addWidget (self.pwdEdit, 1, 1, 1, 2)
		grid.addWidget (self.buttonBox, 2, 0, 1, 3)
		self.setLayout (grid)
		title = 'Add User' if uid is None else 'Edit User'
		self.setWindowTitle (title)

		self.connect (self.buttonBox, SIGNAL("accepted()"), self, SLOT('accept()'))
		self.connect (self.buttonBox, SIGNAL("rejected()"), self, SLOT('reject()'))
		self.connect (self.unameEdit, SIGNAL("editingFinished()"), self.showUser)
		self.connect (self.pwdEdit, SIGNAL("editingFinished()"), self.showPass)

	def showPass(self):
		self.acc.passwd = str(self.pwdEdit.text())
	
	def showUser(self):
		self.acc.username = str(self.unameEdit.text())

class SettingsDlg (QDialog):

	def __init__(self, parent):
		super (SettingsDlg, self).__init__(parent)
		
		self.setWindowTitle ('Preferences')
		loginIntervalLabel = QLabel ('Login after every:')
		loginSpin = QSpinBox ()
		loginSpin.setRange (1, 60)
		loginSpin.setValue (self.parent.settings.relogin_after/60)
		minLabel = QLabel ('minutes')
		quotaIntervalLabel = QLabel ('Refresh Quota usage every:')
		quotaSpin = QSpinBox()
		quotaSpin.setRange (1, 60)
		quotaSpin.setValue (self.parent.settings.update_quota_after/60)
		buttonBox = QDialogButtonBox ( QDialogButtonBox.Ok | QDialogButtonBox.Cancel )
		
		hbox1 = QHBoxLayout()
		hbox1.addWidget (loginIntervalLabel)
		hbox1.addWidget (loginSpin)
		hbox1.addWidget (minLabel)
		hbox2 = QHBoxLayout()
		hbox2.addWidget (quotaIntervalLabel)
		hbox2.addWidget (quotaSpin)
		hbox2.addWidget (minLabel)
		vbox = QVBoxLayout()
		vbox.addLayout (hbox1, 0, 0)
		vbox.addLayout (hbox2, 2, 0)
		vbox.addWidget (buttonbox, 5, 0)
		self.setLayout (vbox)
		
		self.connect (buttonBox, SIGNAL("accepted()"), self, SLOT('accept()'))
		self.connect (buttonBox, SIGNAL("rejected()"), self, SLOT('reject()'))

class MainWindow (QMainWindow):

	def __init__(self, parent=None):
		super (MainWindow, self).__init__(parent)

		self.accounts = []
		self.loginThread = StayLogin (self)
		self.quotaThread = UpdateQuota (self)
		self.settings = Config()
		self.switch = False
		self.bars = []

		self.toolbar = self.addToolBar ('Toolbar')
		self.status = self.statusBar()
		self.status.setSizeGripEnabled (False)

		loginAction = self.createAction ('Log In', self.login, 'icons/network-connect.png', 'Log In')
		switchAction = self.createAction ('Auto Switch', self.setAutoSwitch, 'icons/switch-user.png', 'Auto switch to user in queue in case of error', None, True)
		quotaAction = self.createAction ('Get Quota Usage', self.refreshQuota, 'icons/view-refresh.png', 'Refresh Quota', QKeySequence.Refresh)
		newUserAction = self.createAction ('&New...', self.addAccount, 'icons/list-add-user.png', 'Create User', QKeySequence.New)
		rmUserAction = self.createAction ('Remove', self.rmAccount, 'icons/list-remove-user.png', 'Remove User', QKeySequence.Delete)
		editUserAction = self.createAction ('&Edit...', self.editAccount, 'icons/user-properties.png', 'Edit User')
		clearAction = self.createAction ('&Clear All', self.clearList, 'icons/edit-clear-list.png', 'Clear Users list')
		topAction = self.createAction ('Top', self.top, 'icons/go-top.png', 'Move to top')
		upAction = self.createAction ('Up', self.up, 'icons/go-up.png', 'Move up')
		downAction = self.createAction ('Down', self.down, 'icons/go-down.png', 'Move down')
		bottomAction = self.createAction ('Bottom', self.bottom, 'icons/go-bottom.png', 'Move to bottom')
		prefsAction = self.createAction ('&Configure SAM', self.configure, 'icons/', 'Configure SAM', QKeySequence.Preferences)
		quitAction = self.createAction ('Quit', self.quit, 'icons/application-exit.png', 'Quit SAM', QKeySequence.Quit)
		
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
		actionsMenu.addAction (switchAction)
		settingsMenu = menubar.addMenu ('&Settings')
		settingsMenu.addAction (prefsAction)
		
		self.toolbar.addAction ( newUserAction )
		self.toolbar.addAction ( rmUserAction )
		self.toolbar.addAction ( editUserAction )
		self.toolbar.addAction ( clearAction )
		self.toolbar.addSeparator()
		self.toolbar.addAction ( loginAction )
		self.toolbar.addAction ( quotaAction )
		self.toolbar.addSeparator()
		self.toolbar.addAction ( topAction )
		self.toolbar.addAction ( upAction )
		self.toolbar.addAction ( downAction )
		self.toolbar.addAction ( bottomAction )
		self.toolbar.addSeparator()
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
		self.setWindowIcon (QIcon('icons/cyberoam.png'))
		self.setWindowTitle ('Syberoam Account Manager')
		self.tray = QSystemTrayIcon ()
		self.tray.setIcon ( QIcon('icons/cyberoam.png') )
		self.tray.show()
		
		try:
			conf = open ( os.getenv('HOME')+'/.sam.conf', 'r' )
			accounts = conf.read()
			conf.close()
			###print accounts
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
			self.status.showMessage ('Users loaded', 5000)
		except: pass
		
		self.connect ( self.table, SIGNAL('itemChanged(QTreeWidgetItem*,int)'), self.updateUi )
		self.connect ( self.table, SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'), self.login )
		#self.connect ( self.table, SIGNAL('itemActivated(QTreeWidgetItem*,int)'), self.login )

	def updateUi (self, item, column):
		if column==1:
			status = str(item.text(1))
			if status == 'Logged in':
				item.setIcon (0, QIcon(GREEN))
			elif status == 'Logging in' or status == 'Logged out':
				item.setIcon (0, QIcon(YELLOW))
			elif status == 'Limit Reached' or status == 'Wrong Password' or status == 'Critical Quota':
				item.setIcon (0, QIcon(RED))
		elif column==3:
			quota = str(item.text(3)).split()
			rem = float(quota[0]) if quota[1] is 'KB' else float(quota[0])*1024
			used = 102400 - rem
			used = int(round(used))
			self.table.itemWidget (item, 2).setValue(used)

	def configure (self):
		dlg = SettingsDlg(self)

	def setAutoSwitch (self):
		self.switch = not self.switch

	def login (self, item=None, column=None):
		if item is None:
			acc_no = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		else:
			acc_no = self.table.indexOfTopLevelItem ( item )
		if self.loginThread.isRunning():
			self.table.topLevelItem (self.loginThread.curr).setText (1, 'Logged out')
			self.loginThread.curr = acc_no
			self.loginThread.doNow = True
		else:
			self.loginThread.curr = acc_no
			self.loginThread.start()

	def refreshQuota (self):
		self.status.showMessage ('Refreshing quota...')
		curr = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		self.quotaThread.run (curr)
		self.status.showMessage ('Quota refreshed', 5000)

	def addAccount (self, uid=None, pwd=None):
		if uid is not None and pwd is not None:
			new = QTreeWidgetItem ([uid, '', '', ''])
			new.setIcon (0, QIcon(YELLOW))
			self.table.addTopLevelItem ( new )
			pbar = QProgressBar()
			pbar.setRange (0, 102400)
			self.bars.append (pbar)
			self.table.setItemWidget (new, 2, self.bars[-1])
			self.accounts.append ( Account(uid, pwd) )
			self.status.showMessage (uid+' added', 5000)
		else:
			dlg = Prompt(self)
			dlg.setWindowIcon (QIcon('icons/list-add-user.png'))
			if dlg.exec_():
				self.addAccount(dlg.acc.username, dlg.acc.passwd)

	def editAccount (self):
		current = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		dlg = Prompt(self.accounts[current].username)
		dlg.setWindowIcon (QIcon('icons/user-properties.png'))
		if dlg.exec_():
			self.table.currentItem().setText (0, dlg.acc.username)
			self.accounts[current].username = dlg.acc.username
			if dlg.acc.passwd is not '':
				self.accounts[current].passwd = dlg.acc.passwd
			if current == self.loginThread.curr:
				self.loginThread.doNow = True

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
		bound = (to>1) * (len(self.accounts)-1)
		if current == bound:
			return None
		toPos = [0, current-1, current+1, len(self.accounts)-1][to]
		if self.loginThread.curr==current:
			self.loginThread.curr = toPos
		elif self.loginThread.curr<current and self.loginThread.curr>=toPos:
			self.loginThread += 1
		elif self.loginThread.curr>current and self.loginThread.curr<=toPos:
			self.loginThread.curr -= 1
		pbars=[]
		tmp1 = self.table.takeTopLevelItem (current)
		tmp2 = self.accounts.pop (current)
		tmpbar = self.bars.pop (current)
		self.table.insertTopLevelItem ( toPos, tmp1 )
		self.accounts.insert ( toPos, tmp2 )
		self.bars.insert ( toPos, tmpbar)
		self.table.setCurrentItem ( self.table.topLevelItem(toPos) )
		self.updateBars()

	def top (self): self.move (0)

	def up (self): self.move (1)

	def down (self): self.move (2)

	def bottom (self): self.move (3)

	def updateBars (self):
		for i in range ( len(self.bars) ):
			self.table.setItemWidget ( self.table.topLevelItem(i), 2, self.bars[i] )

	def quit (self):
		conf = open ( os.getenv('HOME')+'/.sam.conf', 'w' )
		length = str(len(self.accounts))
		conf.write(length+'\n\n\n')
		for ac in self.accounts:
			temp = ac.passwd
			ciphertext = bz2.compress(temp)
			temp = ac.username+'!@#$%^&*'+ciphertext+'!@#$%^&*'
			conf.write(temp)
		
		conf.close()
		self.loginThread.kill = True
		self.close()

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
	app.exec_()
