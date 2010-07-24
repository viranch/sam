#
# Author: Viranch Mehta <viranch.mehta@gmail.com>
#

import sys
import time
import os
import Cyberoam
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Crypto.Cipher import AES

class UpdateQuota (QThread):

	def __init__(self, parent=None):
		super (UpdateQuota, self).__init__(parent)
		self.parent = parent
		self.acc_no = -1

	def run (self):
		self.update()

	def update (self, once=False):
		while True:
			if self.acc_no==-1:
				if once:
					break
				continue
			this = self.parent.table.topLevelItem(self.acc_no)
			uname = self.parent.accounts[self.acc_no].username+'@da-iict.org'
			passwd = self.parent.accounts[self.acc_no].passwd
			quota = Cyberoam.netUsage ( uname, passwd )
			this.setText (2, quota[0])
			this.setText (3, quota[1])
			if once:
				break
			time.sleep (59)

class StayLogin (QThread):
	
	def __init__(self, parent=None):
		super (StayLogin, self).__init__(parent)
		self.parent = parent
		self.curr = -1

	def run (self):
		self.curr = self.parent.table.indexOfTopLevelItem ( self.parent.table.currentItem() )
		if self.curr<0:
			return None
		while self.curr<len(self.parent.accounts):
			this = self.parent.table.topLevelItem(self.curr)
			this.setText(1, 'Logging in')
			try:
				uname = self.parent.accounts[self.curr].username+'@da-iict.org'
				passwd = self.parent.accounts[self.curr].passwd
				Cyberoam.login ( uname, passwd )
				self.parent.quotaThread.acc_no = self.curr
				if not self.parent.quotaThread.isRunning():
					self.parent.quotaThread.start()
				self.parent.quotaThread.update(True)
				this.setText (1, 'Logged in')
				time.sleep (3000)
			except Cyberoam.DataTransferLimitExceeded:
				quota = Cyberoam.netUsage ( self.parent.accounts[self.curr].username+'@da-iict.org', self.parent.accounts[self.curr].passwd )
				this.setText (1, 'Limit Reached')
				this.setText (2, quota[0])
				this.setText (3, quota[1])
				self.curr+=1
			except Cyberoam.WrongPassword:
				this.setText (1, 'Wrong Password')
				self.curr+=1
		self.parent.quotaThread.exit()

class Account ():

	def __init__ (self, login_id='', passwd=''):
		self.username = login_id
		self.passwd = passwd

class Prompt (QDialog):
	def __init__(self, parent=None):
		super (Prompt, self).__init__(parent)
		self.acc = Account()
		
		self.buttonBox = QDialogButtonBox (QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
		unameLabel = QLabel ('Username:')
		pwdLabel = QLabel ('Password:')
		self.unameEdit = QLineEdit()
		self.pwdEdit = QLineEdit()
		self.pwdEdit.setEchoMode (QLineEdit.Password)

		grid = QGridLayout ()
		grid.addWidget (unameLabel, 0, 0)
		grid.addWidget (self.unameEdit, 0, 1)
		grid.addWidget (pwdLabel, 1, 0)
		grid.addWidget (self.pwdEdit, 1, 1)
		grid.addWidget (self.buttonBox, 2, 0, 1, 2)
		self.setLayout (grid)
		self.setWindowTitle ('Add Account')

		self.connect (self.buttonBox, SIGNAL("accepted()"), self, SLOT('accept()'))
		self.connect (self.buttonBox, SIGNAL("rejected()"), self, SLOT('reject()'))
		self.connect (self.unameEdit, SIGNAL("editingFinished()"), self.showUser)
		self.connect (self.pwdEdit, SIGNAL("editingFinished()"), self.showPass)

	def showPass(self):
		self.acc.passwd = str(self.pwdEdit.text())
	
	def showUser(self):
		self.acc.username = str(self.unameEdit.text())

class MainWindow (QMainWindow):

	def __init__(self, parent=None):
		super (MainWindow, self).__init__(parent)

		self.accounts = []
		self.loginThread = StayLogin (self)
		self.quotaThread = UpdateQuota (self)

		self.toolbar = self.addToolBar ('Toolbar')
		self.status = self.statusBar()
		self.status.setSizeGripEnabled (False)

		self.toolbar.addAction ( self.createAction ('Log In', self.login, None, 'Log In') )
		self.toolbar.addAction ( self.createAction ('Refresh', self.refreshQuota, 'icons/view-refresh.png', 'Refresh Quota', 'F5') )
		self.toolbar.addSeparator()
		self.toolbar.addAction ( self.createAction ('Add', self.addAccount, 'icons/list-add.png', 'Add account') )
		self.toolbar.addAction ( self.createAction ('Remove', self.rmAccount, 'icons/list-remove.png', 'Remove account') )
		self.toolbar.addAction ( self.createAction ('Clear', self.clearList, 'icons/edit-clear-list.png', 'Clear account list') )
		self.toolbar.addSeparator()
		self.toolbar.addAction ( self.createAction ('Top', self.top, 'icons/go-top.png', 'Move to top') )
		self.toolbar.addAction ( self.createAction ('Up', self.up, 'icons/go-up.png', 'Move up') )
		self.toolbar.addAction ( self.createAction ('Down', self.down, 'icons/go-down.png', 'Move down') )
		self.toolbar.addAction ( self.createAction ('Bottom', self.bottom, 'icons/go-bottom.png', 'Move to bottom') )
		self.toolbar.addSeparator()
		self.toolbar.addAction ( self.createAction ('Quit', self.quit, 'icons/application-exit.png', 'Quit SAM', 'Ctrl+Q') )
		
		key = 'qwertyashhjgoreiuqhwlv32184!!@3$'
		mode = AES.MODE_CBC
		self.encryptor = AES.new(key,mode)
		self.decryptor = AES.new(key,mode)
		

		self.table = QTreeWidget ()
		self.table.setRootIsDecorated (False)
		headers = self.table.headerItem()
		headers.setText (0, 'ID')
		headers.setText (1, 'Status')
		headers.setText (2, 'Used')
		headers.setText (3, 'Remaining')

		self.setCentralWidget (self.table)
		self.setWindowTitle ('Syberoam Account Manager')
		
		try:
			conf = open ( os.getenv('HOME')+'/.sam.conf', 'r' )
			print "hellofasdfsa"
			accounts = conf.read()
			conf.close()
			###print accounts
			toks = accounts.split('\n\n\n',1)
			length = int(toks[0])
			print length
			data = toks[1].split('!@#$%^&*')
			i=0
			while i!= 2*length:
				user = data[i]
				
				crypt_passwd = data[i+1]
				passwd = self.decryptor.decrypt(crypt_passwd)
				index = len(passwd)/16
				
				passwd = passwd[0:index]
				
				self.addAccount(user,passwd)
				i = i+2
		except: pass
		
		self.connect ( self.table, SIGNAL('itemChanged(QTreeWidgetItem*,int)'), self.setRedIcon )

	def setRedIcon (self, item, column):
		if column==1:
			status = str(item.text(1))
			if status == 'Logged in':
				item.setIcon (0, QIcon('icons/flag-green.png'))
			elif status == 'Logged out':
				item.setIcon (0, QIcon('icons/flag-yellow.png'))
			elif status == 'Limit Reached' or status == 'Wrong Password':
				item.setIcon (0, QIcon('icons/flag-red.png'))

	def login (self):
		if self.loginThread.isRunning():
			self.loginThread.exit()
			self.table.topLevelItem (self.loginThread.curr).setText (1, 'Logged out')
		self.loginThread.start()

	def refreshQuota (self):
		self.quotaThread.update (True)

	def addAccount (self, uid=None, pwd=None):
		if uid is not None and pwd is not None:
			new = QTreeWidgetItem([uid, '', '', ''])
			new.setIcon (0, QIcon('icons/flag-yellow.png'))
			self.table.addTopLevelItem ( new )
			self.accounts.append ( Account(uid, pwd) )
		else:
			dlg = Prompt()
			if dlg.exec_():
				self.addAccount(dlg.acc.username, dlg.acc.passwd)

	def rmAccount (self):
		if len(self.accounts) == 0:
			self.status.showMessage ('Nothing to remove!', 5000)
			return None
		current = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		popped = self.table.takeTopLevelItem (current)
		rm = self.accounts.pop (current)
		self.status.showMessage (rm.username+' removed', 5000)
		return popped, rm

	def clearList (self):
		if len(self.accounts)==0:
			self.status.showMessage ('List already clear!', 5000)
			return None
		self.table.clear()
		self.accounts = []
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
		tmp1 = self.table.takeTopLevelItem (current)
		tmp2 = self.accounts.pop (current)
		self.table.insertTopLevelItem ( toPos, tmp1 )
		self.accounts.insert ( toPos, tmp2 )
		self.table.setCurrentItem ( self.table.topLevelItem(toPos) )

	def top (self): self.move (0)

	def up (self): self.move (1)

	def down (self): self.move (2)

	def bottom (self): self.move (3)

	def quit (self):
		conf = open ( os.getenv('HOME')+'/.sam.conf', 'w' )
		length = str(len(self.accounts))
		conf.write(length+'\n\n\n')
		for ac in self.accounts:
			print 'main'
			temp = ac.passwd*16
			ciphertext = self.encryptor.encrypt(temp)
			temp = ac.username+'!@#$%^&*'+ciphertext+'!@#$%^&*'
			conf.write(temp)
		
		conf.close()
		self.loginThread.exit()
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
