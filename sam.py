#
# Author: Viranch Mehta <viranch.mehta@gmail.com>
#

import sys
import time
import os
import Cyberoam
from PyQt4.QtCore import *
from PyQt4.QtGui import *

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
				this.setIcon (0, QIcon('icons/flag-green.png'))
				this.setText (1, 'Logged in')
				time.sleep (3000)
			except Cyberoam.DataTransferLimitExceeded:
				quota = Cyberoam.netUsage ( self.parent.accounts[self.curr].username+'@da-iict.org', self.parent.accounts[self.curr].passwd )
				this.setIcon (0, QIcon('icons/flag-red.png'))
				this.setText (1, 'Limit Reached')
				this.setText (2, quota[0])
				this.setText (3, quota[1])
				self.curr+=1
			except Cyberoam.WrongPassword:
				this.setIcon (0, 'icons/flag-red.png')
				this.setText (1, 'Wrong Password')
				self.curr+=1
		self.parent.quotaThread.exit()

class Account ():

	def __init__ (self, login_id, passwd):
		self.username = login_id
		self.passwd = passwd

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
		self.toolbar.addAction ( self.createAction ('Quit', self.quit, 'icons/application-exit.png', 'Quit CAM', 'Ctrl+Q') )

		self.table = QTreeWidget ()
		self.table.setRootIsDecorated (False)
		headers = self.table.headerItem()
		headers.setText (0, 'ID')
		headers.setText (1, 'Status')
		headers.setText (2, 'Used')
		headers.setText (3, 'Remaining')

		self.setCentralWidget (self.table)
		self.setWindowTitle ('Cyberoam Account Manager')
		
		try:
			conf = open ( os.getenv('HOME')+'/.sam.conf', 'r' )
			accounts = conf.readlines()
			conf.close()
			for ac in accounts:
				toks = ac.split('\t')
				self.addAccount ( toks[0], toks[1] )
		except: pass

	def login (self):
		if self.loginThread.isRunning():
			self.loginThread.exit()
			self.table.topLevelItem (self.loginThread.curr).setText (1, 'Logged out')
		self.loginThread.start()

	def refreshQuota (self):
		self.quotaThread.update (True)

	def addAccount (self, uid=None, pwd=None):
		if uid is not None and pwd is not None:
			self.table.addTopLevelItem ( QTreeWidgetItem([uid, '', '', '']) )
			self.accounts.append ( Account(uid, pwd) )
		else:
			new=QTreeWidgetItem(['200601049', '', '', ''])
			self.accounts.append ( Account('200601049', 'a') )
			self.table.addTopLevelItem (new)
			new=QTreeWidgetItem(['200801035', '', '', ''])
			self.accounts.append ( Account('200801035', 'poison007') )
			self.table.addTopLevelItem (new)

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
		for ac in self.accounts:
			conf.write ( ac.username+'\t'+ac.passwd+'\n' )
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
