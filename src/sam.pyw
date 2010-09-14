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
import thread
import qrc_icon

GREEN = ':/icons/ball-green.png'
RED = ':/icons/ball-red.png'
YELLOW = ':/icons/ball-yellow.png'

lck_file = '.sam.lck'
if 'win' in sys.platform:
	lck_file = os.getenv('appdata')+'\\'+lck_file
	def exists (pid):
		"""kill function for Win32"""
		import ctypes
		return ctypes.windll.kernel32.OpenProcess(1, 0, pid)!=0
else:
	lck_file = os.getenv('HOME')+'/.sam/'+lck_file
	def exists (pid):
		try:
			os.kill (pid, 0)
			return True
		except:
			return False

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
		self.rev = 'd4a7cf232d26'
		self.server = '10.100.56.55'
		self.port = '8090'
		self.domain = '@da-iict.org'

class Account ():

	def __init__ (self, parent, login_id='', passwd='', no=-1):
		self.username = login_id
		self.passwd = passwd
		self.acc_no = no
		self.parent = parent

	def login (self):
		try:
			Cyberoam.login (self.username+self.parent.settings.domain, self.passwd)
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
			Cyberoam.logout (self.username+self.parent.settings.domain, self.passwd)
			return True
		except IOError:
			return False

	def getQuota (self):
		try:
			quota = Cyberoam.netUsage (self.username+self.parent.settings.domain, self.passwd)
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
		#updateAction = self.createAction ('&Update', self.update, ':/icons/update.png', 'Update SAM')
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
		#helpMenu.addAction (updateAction)
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
		#self.toolbar.addAction ( updateAction )
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
		self.tray = QSystemTrayIcon (self)
		self.tray.setIcon ( QIcon(':/icons/logo.png') )
		self.tray.setVisible(True)
		self.trayMenu = QMenu ()
		self.trayMenu.addAction ( self.autoSwitchAction )
		self.trayMenu.addAction ( self.balloonAction )
		#self.trayMenu.addAction ( prefsAction )
		self.trayMenu.addSeparator()
		self.trayMenu.addAction ( loginAction )
		self.trayMenu.addAction ( logoutAction )
		self.trayMenu.addSeparator()
		self.trayMenu.addAction ( quitAction )
		self.tray.setContextMenu ( self.trayMenu )
	
		self.connect ( qApp, SIGNAL('commitDataRequest(QSessionManager)'),qApp.commitData)	
		self.connect ( self.tray, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), self.toggleWindow )
		self.connect ( self.table, SIGNAL('itemChanged(QTreeWidgetItem*,int)'), self.updateUi )
		self.connect ( self.table, SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'), self.login )
		self.connect ( self.loginTimer, SIGNAL('timeout()'), self.reLogin )
		self.connect ( self.quotaTimer, SIGNAL('timeout()'), self.refreshQuota )

	def loadPrefs (self):
		try:
			settings = QSettings("DA-IICT","SAM")
			point = settings.value("pos").toPoint()
			size = settings.value("size").toSize() 
			self.setGeometry(QRect(point,size))
			
			settings.beginGroup("Account")
			length = (settings.value("Length")).toInt()[0]
			for ac in range(0,length):
				temp1= "Account"+str(ac)
				temp = settings.value(temp1).toString()
				toks = temp.split('!@#$%')
				username = toks[0]
				password = toks[1]
				self.addAccount(str(username),str(password),True)
			
			settings.endGroup()

			settings.beginGroup("Conf")
			self.settings.auto_login=(settings.value("AutoLogin")).toBool()
			self.settings.auto_switch = (settings.value("AutoSwitch")).toBool()
			self.settings.switch_on_critical=(settings.value("SwitchOnCritical")).toBool()
			self.balloonAction.setChecked((settings.value("Ballons")).toBool())
			
			self.settings.update_quota_after = (settings.value("UpdateQuotaAfter")).toInt()[0]
			self.settings.relogin_after = (settings.value("ReloginAfter")).toInt()[0]
			self.settings.critical_quota_limit=(settings.value("CriticalQuotaLimit")).toFloat()[0]
			self.settings.server=str(settings.value("Server").toString())
			self.settings.port= str(settings.value("Port").toString())
			self.settings.rev=str(settings.value("Rev").toString())
			self.settings.domain=str(settings.value("Domain").toString())
			settings.endGroup()
			
			lck = open(lck_file, 'wb')
			lck.write ( str(os.getpid()) )
			lck.close()
			
			if self.settings.auto_login == True and len(self.accounts)>0:
					self.login()
			
		except:pass

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
			self.settings.domain = str(dlg.domainEdit.text())
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
			self.savePrefs(False, True)

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
			if item.text(1)=='Wrong Password' or item.text(1)=='Limit Reached' or item.text(1)=='Critical usage':
				item.setText (1, '')
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

	def addAccount (self, uid=None, pwd=None, auto=False):
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
			self.getQuota (new)
		else:
			dlg = prompt.Prompt(self)
			dlg.setWindowIcon (QIcon(':/icons/list-add-user.png'))
			if dlg.exec_():
				self.addAccount(str(dlg.unameEdit.text()), str(dlg.pwdEdit.text()), auto)
				if not auto:
					self.savePrefs (True, False)

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
			self.getQuota ( self.table.currentItem() )
			self.savePrefs (True, False)

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
		self.savePrefs (True, False)
		return popped, rm

	def clearList (self):
		if len(self.accounts)==0:
			self.status.showMessage ('List already clear!', 5000)
			return None
		b = QMessageBox.question (self, 'SAM', 'Are you sure you want to remove all users?', QMessageBox.Yes, QMessageBox.No)
		if b == QMessageBox.Yes:
			self.table.clear()
			self.accounts = []
			self.bars = []
			self.status.showMessage ('List cleared', 5000)
			self.savePrefs(True, False)

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
		self.savePrefs(True, True)
		qApp.quit()

	def savePrefs (self, acc, pref):
		
		try:
			settings= QSettings("DA-IICT","SAM")
			settings.setValue("size",self.size())
			settings.setValue("pos",self.pos())
			settings.beginGroup("Account")
			settings.setValue("Length",len(self.accounts))
			cnt=0
			for ac in self.accounts:
				
				temp = ac.username+'!@#$%'+ac.passwd
				temp1 = "Account"+str(cnt)
				settings.setValue(temp1,temp)
				cnt = cnt+1
			settings.endGroup()

			settings.beginGroup("Conf")
			settings.setValue("AutoLogin",int(self.settings.auto_login))
			settings.setValue("AutoSwitch",int(self.settings.auto_switch))
			settings.setValue("SwitchOnCritical",int(self.settings.switch_on_critical))
			settings.setValue("Ballons",int(self.settings.balloons))
			settings.setValue("UpdateQuotaAfter",self.settings.update_quota_after)
			settings.setValue("ReloginAfter",self.settings.relogin_after)
			settings.setValue("CriticalQuotaLimit",self.settings.critical_quota_limit)
			settings.setValue("Server",self.settings.server)
			settings.setValue("Port",self.settings.port)
			settings.setValue("Rev",self.settings.rev)
			settings.setValue("Domain",self.settings.domain)
			settings.endGroup()
		
			os.remove(lck_file)
		except:pass	

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

class QApplication(QApplication):
	def __init__(self,arg):
		super(QApplication,self).__init__(arg)

	def saveState(self,manager):
		lis = qApp.allWidgets()
		for l in lis:
			if type(l) == type(MainWindow()):
				l.loadPrefs()

	def commitData(self,manager):
		lis = qApp.allWidgets()
		for l in lis:
			if type(l) == type(MainWindow()):
				l.savePrefs()

def main():
	app = QApplication (sys.argv)
	window = MainWindow()
	window.show()
	if 'win' in sys.platform:
		window.loadPrefs()
	app.exec_()

if __name__=='__main__':
	if not os.access (lck_file, os.F_OK):
		main()
	else:
		pid = int ( open(lck_file, 'rb').read() )
		if exists(pid):
			app = QApplication (sys.argv)
			QMessageBox.information (None, 'SAM', 'SAM is already running.')
		else:
			main()
