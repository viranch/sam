#!/usr/bin/env python
#
# Authors: 		Viranch Mehta <viranch.mehta@gmail.com>
#			Mohit Kothari <mohitrajkothari@gmail.com>
#
# Source Website: 	http://www.bitbucket.org/viranch/sam

import sys
import os
import Cyberoam
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import bz2
import qrc_icon

DOMAIN = '@da-iict.org'

GREEN = ':/icons/ball-green.png'
RED = ':/icons/ball-red.png'
YELLOW = ':/icons/ball-yellow.png'

acc_file = '.samacc.conf'
conf_file = '.samconf.conf'
lck_file = '.sam.lck'
if 'win' in sys.platform:
	acc_file = os.getenv('appdata')+'\\'+acc_file
	conf_file = os.getenv('appdata')+'\\'+conf_file
	lck_file = os.getenv('appdata')+'\\'+lck_file
else:
	acc_file = os.getenv('HOME')+'/.sam/'+acc_file
	conf_file = os.getenv('HOME')+'/.sam/'+conf_file
	lck_file = os.getenv('HOME')+'/.sam/'+lck_file

def get_err ( err_code ):
	return ['Logged in', 'Limit Reached', 'Wrong Password', 'Account in use'][err_code]

class Config ():

	def __init__ (self):
		self.auto_login = True
		self.auto_switch = True
		self.switch_on_critical = False
		self.balloons = True
		self.update_quota_after = 360 #seconds = 6 mins
		self.relogin_after = 3000 #seconds = 50 mins
		self.critical_quota_limit = 95.0*1024 #KB = 95MB
		self.rev = 'e1e1bfd30e3b'
		self.server = '10.100.56.55'
		self.port = '8090'
		self.DOMAIN = DOMAIN

class Account ():

	def __init__ (self, parent, login_id='', passwd='', no=-1):
		self.username = login_id
		self.passwd = passwd
		self.acc_no = no
		self.parent = parent

	def login (self):
		try:
			Cyberoam.login (self.username+DOMAIN, self.passwd)
			return 0
		except Cyberoam.DataTransferLimitExceeded:
			return 1
		except Cyberoam.WrongPassword:
			return 2
		except Cyberoam.MultipleLoginError:
			return 3
		except IOError:
			return 4

	def logout (self):
		try:
			Cyberoam.logout (self.username+DOMAIN, self.passwd)
			return True
		except IOError:
			return False

	def getQuota (self):
		try:
			quota = Cyberoam.netUsage (self.username+DOMAIN, self.passwd)
			return 0, quota
		except Cyberoam.DataTransferLimitExceeded:
			return 1, None
		except Cyberoam.WrongPassword:
			return 2, None
		except IOError:
			return 4, None

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

		loginAction = self.createAction ('Log &In', self.login, ':/icons/network-connect.png', 'Log In')
		logoutAction = self.createAction ('Log &Out', self.logout, ':/icons/network-disconnect.png', 'Log Out')
		quotaAction = self.createAction ('Get Usage', self.getQuota, ':/icons/view-refresh.png', 'Refresh Quota', QKeySequence.Refresh)
		newUserAction = self.createAction ('&New...', self.addAccount, ':/icons/user-add-icon.png', 'Create User', QKeySequence.New)
		rmUserAction = self.createAction ('Remove', self.rmAccount, ':/icons/user-remove-icon.png', 'Remove User', QKeySequence.Delete)
		editUserAction = self.createAction ('&Edit...', self.editAccount, ':/icons/user-icon.png', 'Edit User')
		clearAction = self.createAction ('&Clear All', self.clearList, ':/icons/edit-clear-list.png', 'Clear Users list')
		upAction = self.createAction ('Up', self.up, ':/icons/up-icon.png', 'Move up')
		downAction = self.createAction ('Down', self.down, ':/icons/down-icon.png', 'Move down')
		self.autoSwitchAction = self.createAction ('Enable auto-switch', self.setAutoSwitch, ':/icons/switch-user.png', 'Enable/Disable the auto switch function', None, True)
		self.autoSwitchAction.setChecked (self.settings.auto_switch)
		self.balloonAction = self.createAction ('Enable balloon popups', self.setBalloon, None, 'Enable balloon popups', None, True)
		self.balloonAction.setChecked (self.settings.balloons)
		prefsAction = self.createAction ('&Configure', self.configure, ':/icons/configure.png', 'Configure SAM', QKeySequence.Preferences)
		updateAction = self.createAction ('&Update', self.update, ':/icons/update.png', 'Update SAM')
		aboutAction = self.createAction ('&About', self.about, ':/icons/help-about.png', 'About SAM')
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
		settingsMenu.addAction (self.autoSwitchAction)
		settingsMenu.addAction (self.balloonAction)
		settingsMenu.addAction (prefsAction)
		helpMenu = menubar.addMenu ('&Help')
		helpMenu.addAction (updateAction)
		helpMenu.addAction (aboutAction)
		
		self.toolbar.addAction ( newUserAction )
		self.toolbar.addAction ( editUserAction )
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
		self.toolbar.addAction ( updateAction )
		self.toolbar.addAction ( aboutAction )
		self.toolbar.addAction ( quitAction )

		self.table = QTreeWidget ()
		self.table.setRootIsDecorated (False)
		headers = self.table.headerItem()
		headers.setText (0, 'ID')
		headers.setText (1, 'Status')
		headers.setText (2, 'Usage')
		headers.setText (3, 'Remaining')
		self.table.header().resizeSection (0, 120)
		self.table.header().resizeSection (2, 160)

		self.setCentralWidget (self.table)
		self.setWindowIcon (QIcon(':/icons/logo.png'))
		self.setWindowTitle ('SAM - Syberoam Account Manager')
		self.resize(498, self.size().height())
		self.tray = QSystemTrayIcon ()
		self.tray.setIcon ( QIcon(':/icons/logo.png') )
		self.tray.setVisible(True)
		self.trayMenu = QMenu ()
		self.trayMenu.addAction ( self.autoSwitchAction )
		self.trayMenu.addAction ( self.balloonAction )
		self.trayMenu.addAction ( prefsAction )
		self.trayMenu.addSeparator()
		self.trayMenu.addAction ( loginAction )
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
			lck = open(lck_file, 'wb')
			lck.write ( str(os.getpid()) )
			lck.close()
			conf = open(conf_file,'r')
			pref = conf.read().split('\n')
			
			bools = pref[0]
			self.settings.auto_login = bool(int(bools[0]))
			self.autoSwitchAction.setChecked ( bool(int(bools[1])) )
			self.settings.switch_on_critical = bool(int(bools[2]))
			self.balloonAction.setChecked ( bool(int(bools[3])) )
			
			self.settings.update_quota_after = int(pref[1])
			self.settings.relogin_after = int(pref[2])
			self.settings.critical_quota_limit = float(pref[3])
			toks = pref[4].split(':')
			self.settings.server = toks[0]
			Cyberoam.cyberroamIP = toks[0]
			self.settings.port = toks[1]
			Cyberoam.cyberroamPort = toks[1]
			self.settings.rev = pref[5].replace('\n','')
			conf.close()
			
			conf = open ( acc_file, 'rb' )
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
			if self.settings.auto_login == True and len(self.accounts)>0:
				self.login()

		except: pass

	def setAutoSwitch (self, checked):
		self.settings.auto_switch = checked

	def setBalloon (self, checked):
		self.settings.balloons = checked

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
					self.tray.showMessage ('SAM', item.text(0)+': '+status)
			elif status == 'Logged out' or status == '':
				item.setIcon (0, QIcon(YELLOW))
			else:
				item.setIcon (0, QIcon(RED))
				if self.settings.balloons:
					self.tray.showMessage ('SAM', item.text(0)+': '+status)
				if status=='Limit Reached':
					item.setText (3, '0.00 KB')
		elif column == 3:
			quota = str(item.text(3)).split()
			rem = float(quota[0]) if quota[1] == 'KB' else float(quota[0])*1024
			used = 102400 - rem
			self.bars[self.table.indexOfTopLevelItem(item)][1] = int(round(used))
			self.table.itemWidget (item, 2).setValue(int(round(used)))

	def configure (self):
		import settings
		dlg = settings.SettingsDlg(self)
		if dlg.exec_():
			self.settings.server = str ( dlg.ipEdit.text() )
			self.settings.port = str ( dlg.portEdit.text() )
			Cyberoam.cyberroamIP = self.settings.server
			Cyberoam.cyberroamPort = self.settings.port
			self.settings.auto_login = dlg.autoLogin.isChecked()
			self.settings.relogin_after = dlg.loginSpin.value()*60
			self.settings.update_quota_after = dlg.quotaSpin.value()*60
			self.loginTimer.stop()
			self.quotaTimer.stop()
			self.loginTimer.start ( self.settings.relogin_after*1000 )
			self.quotaTimer.start ( self.settings.update_quota_after*1000 )
			self.autoSwitchAction.setChecked ( dlg.autoSwitchCheck.isChecked() )
			self.settings.switch_on_critical = dlg.criticalCheck.isChecked() and dlg.autoSwitchCheck.isChecked()
			if self.settings.switch_on_critical:
				self.settings.critical_quota_limit = dlg.criticalSpin.value()*1024
			self.balloonAction.setChecked ( dlg.balloonPopups.isChecked() )

	def switch (self, to=None):
		if not (self.settings.auto_switch):
			self.currentLogin = -1
			return None
		if to is None:
			to  = self.table.topLevelItem (self.currentLogin+1)
		if to is not None:
			self.login ( to, -1, True )

	def login (self, item=None, column=-1, switch=False):
		if item is None:
			item = self.table.currentItem()
			if item is None:
				item = self.table.itemAt(0,0)
				self.table.setCurrentItem(item)
		elif switch:
			self.table.setCurrentItem (item)
		curr = self.table.indexOfTopLevelItem ( item )
		prev = self.currentLogin
		if curr<0:
			return None
		c = self.accounts[curr].login()
		if c<4:
			item.setText (1, get_err(c))
		if c == 0:
			self.currentLogin = curr
			if self.getQuota ( item ): # if getQuota() did not perform a switch
				if switch:
					self.loginTimer.stop()
					self.quotaTimer.stop()
				self.loginTimer.start ( self.settings.relogin_after*1000 )
				if not self.quotaTimer.isActive():
					self.quotaTimer.start ( self.settings.update_quota_after*1000 )
			if prev!=-1 and prev!=curr and not switch:
				self.table.topLevelItem (prev).setText (1, 'Logged out')
		elif c != 4 and self.settings.auto_switch and curr!=len(self.accounts)-1:
			self.switch( self.table.topLevelItem(curr+1) )
		elif c==4:
			self.status.showMessage ('Network Error')
			self.tray.showMessage ('SAM', 'Network Error')
			self.loginTimer.stop()
			if item.text (1)=='Logged in' or item.text(1)=='Limit Reached' or item.text(1)=='Wrong Password':
				item.setText (1, '')

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
		c, quota = self.accounts[curr].getQuota()
		if c==0:
			item.setText (3, quota[1])
			if self.currentLogin>=0 and not self.loginTimer.isActive():
				self.loginTimer.start ( self.settings.relogin_after*1000 )
				self.login (self.table.topLevelItem(self.currentLogin))
			if self.settings.switch_on_critical:
				q = quota[0].split()
				used = float(q[0])*1024 if 'MB' in q[1] else float(q[0])
				if used>=self.settings.critical_quota_limit:
					item.setText (1, 'Critical usage')
					if curr==self.currentLogin and self.currentLogin<len(self.accounts)-1:
						self.switch ()
						return False
		else:
			if c!=4:
				item.setText (1, get_err(c))
			if curr==self.currentLogin and c!=4 and self.settings.auto_switch:
				if self.currentLogin < len(self.accounts)-1:
					self.switch()
					return False
				else:
					self.currentLogin=-1
			elif c==4 and curr==self.currentLogin:
				self.loginTimer.stop()
				self.status.showMessage ('Network Error')
				self.tray.showMessage ('SAM', 'Network Error')
				if item.text (1)=='Logged in' or item.text(1)=='Limit Reached' or item.text(1)=='Wrong Password':
					item.setText (1, '')
		return True

	def addAccount (self, uid=None, pwd=None):
		import prompt
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
			dlg = prompt.Prompt(self)
			dlg.setWindowIcon (QIcon(':/icons/list-add-user.png'))
			if dlg.exec_():
				self.addAccount(str(dlg.unameEdit.text()), str(dlg.pwdEdit.text()))

	def editAccount (self):
		import prompt
		current = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		dlg = prompt.Prompt(self, self.accounts[current].username)
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

	def update (self):
		import update
		o = update.Updater(self, self.settings.rev)
		if o.exec_():
			path = os.sep.join(sys.argv[0].split(os.sep)[:-1])
			ls = os.listdir ( path )
			for item in ls:
				if item[-4:]=='.tmp':
					try:
						os.remove ( path+os.sep+item[:-4] )
					except: pass
					os.rename ( path+os.sep+item, path+os.sep+item[:-4] )
			self.settings.rev = o.rev
		else:
			path = os.sep.join(sys.argv[0].split(os.sep)[:-1])
			ls = os.listdir ( path )
			for item in ls:
				if item[-4:]=='.tmp':
					os.remove ( path+os.sep+item )

	def about (self):
		import about
		dlg = about.About()
		dlg.exec_()

	def quit (self):
		self.loginTimer.stop()
		self.quotaTimer.stop()
		
		conf = open ( acc_file, 'wb' )
		length = str(len(self.accounts))
		conf.write(length+'\n\n\n')
		for ac in self.accounts:
			temp = ac.passwd
			ciphertext = bz2.compress(temp)
			temp = ac.username+'!@#$%^&*'+ciphertext+'!@#$%^&*'
			conf.write(temp)
		conf.close()
		
		conf = open(conf_file,'w')
		conf.write (str(int(self.settings.auto_login)))
		conf.write (str(int(self.settings.auto_switch)))
		conf.write (str(int(self.settings.switch_on_critical)))
		conf.write (str(int(self.settings.balloons))+'\n')
		conf.write (str(self.settings.update_quota_after)+'\n')
		conf.write (str(self.settings.relogin_after)+'\n')
		conf.write (str(self.settings.critical_quota_limit)+'\n')
		conf.write (self.settings.server+':'+self.settings.port+'\n')
		conf.write (self.settings.rev+'\n')
		conf.close()
		
		try:
			os.remove (lck_file)
		except: pass
		qApp.quit()

	def toggleWindow (self, reason):
		if reason == QSystemTrayIcon.Trigger:
			self.hide() if self.isVisible() else self.show()

	def createAction (self, text, slot=None, icon=None, tip=None, shortcut=None, checkable=None):
		action = QAction (text, self)
		if icon is not None:
			action.setIcon (QIcon (icon))
		if shortcut is not None:
			action.setShortcut (shortcut)
		if tip is not None:
			action.setToolTip (tip)
			action.setStatusTip (tip)
		if slot is not None:
			if checkable:
				action.setCheckable (True)
				self.connect (action, SIGNAL('toggled(bool)'), slot)
			else:
				self.connect (action, SIGNAL('triggered()'), slot)
		return action

def main():
	app = QApplication (sys.argv)
	window = MainWindow()
	window.show()
	window.readConfs()
	app.exec_()

if __name__=='__main__':
	if not os.access (lck_file, os.F_OK):
		main()
	else:
		app = QApplication (sys.argv)
		b = QMessageBox.question (None, 'SAM', 'SAM seems to be already running.\nAre you sure SAM is not running?', QMessageBox.Yes, QMessageBox.No)
		if b==QMessageBox.Yes:
			pid = int ( open(lck_file, 'rb').read() )
			try:
				os.kill (pid, 3)
			except: pass
			main()
