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

class Account (QTreeWidgetItem):

	def __init__ (self, parent, login_id, uid, passwd, no):
		super(Account, self).__init__(parent, [uid, '', '', ''])
		self.username = login_id
		self.passwd = passwd
		self.acc_no = no
		self.parent = parent
		self.setIcon (0, QIcon(YELLOW))
		self.pbar = QProgressBar()
		self.pbar.setRange (0, 100)
		self.thread = QThread()

	def login (self):
		try:
			Cyberoam.login (self.username, self.passwd)
			self.setText (1, 'Logged in')
			self.thread.emit (SIGNAL('setIcon(QString)'), GREEN)
			self.thread.emit (SIGNAL('loggedIn(int)'), self.acc_no)
			return
		except Cyberoam.DataTransferLimitExceeded:
			self.setText (3, '0.00 MB')
			self.thread.emit (SIGNAL('usage(int)'), self.pbar.maximum())
			self.thread.emit (SIGNAL('limitExceeded()'))
			self.setText (1, 'Limit Reached')
		except Cyberoam.WrongPassword:
			self.thread.emit (SIGNAL('wrongPassword()'))
			self.setText (1, 'Wrong Password')
		except Cyberoam.MultipleLoginError:
			self.thread.emit (SIGNAL('multipleLogin()'))
			self.setText (1, 'Account in use')
		except IOError:
			self.thread.emit (SIGNAL('networkError()'))
			#self.setText (1, 'Network Error')
			return
		self.thread.emit (SIGNAL('setIcon(QString)'), RED)
		self.thread.emit(SIGNAL('switch(int)'), self.acc_no)

	def logout (self):
		try:
			Cyberoam.logout (self.username, self.passwd)
			self.setText (1, 'Logged out')
			self.thread.emit (SIGNAL('setIcon(QString)'), YELLOW)
			self.thread.emit (SIGNAL('loggedOut()'))
		except IOError:
			self.thread.emit (SIGNAL('networkError()'))
			#self.setText (1, 'Network Error')
			self.thread.emit (SIGNAL('setIcon(QString)'), RED)

	def getQuota (self):
		try:
			quota = Cyberoam.netUsage (self.username, self.passwd)
			self.setText (3, quota[1])
			used, suff = quota[0].split()
			used = round(float(used)/1024) if suff=='KB' else round(float(used))
			self.thread.emit (SIGNAL('usage(int)'), int(used))
			self.thread.emit (SIGNAL('gotGuota(int)'), self.acc_no)
			if self.text(1) != 'Logged in':
				self.setText (1, '')
				self.thread.emit (SIGNAL('setIcon(QString)'), YELLOW)
			return
		except Cyberoam.DataTransferLimitExceeded:
			self.setText (3, '0.00 MB')
			self.thread.emit (SIGNAL('usage(int)'), self.pbar.maximum())
			self.thread.emit (SIGNAL('limitExceeded()'))
			self.setText (1, 'Limit Reached')
		except Cyberoam.WrongPassword:
			self.thread.emit (SIGNAL('wrongPassword()'))
			self.setText (1, 'Wrong Password')
		except IOError:
			self.thread.emit (SIGNAL('networkError()'))
			#self.setText (1, 'Network Error')
			return
		self.thread.emit(SIGNAL('switch(int)'), self.acc_no)
		self.thread.emit (SIGNAL('setIcon(QString)'), RED)

	def _setIcon (self, icon):
		self.setIcon (0, QIcon(icon))

class MainWindow (QMainWindow):

	def __init__(self, parent=None):
		super (MainWindow, self).__init__(parent)
		
		
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
		sortAction = self.createAction ('&Sort', self.sort, '', 'Sort accounts by ID')
		upAction = self.createAction ('Up', self.up, ':/icons/up-icon.png', 'Move up')
		downAction = self.createAction ('Down', self.down, ':/icons/down-icon.png', 'Move down')
		self.autoSwitchAction = self.createAction ('Enable auto-switch', self.setAutoSwitch, ':/icons/switch-user.png', 'Enable/Disable the auto switch function', None, True)
		self.balloonAction = self.createAction ('Enable balloon popups', self.setBalloon, None, 'Enable balloon popups', None, True)
		prefsAction = self.createAction ('&Configure', self.configure, ':/icons/configure.png', 'Configure SAM', QKeySequence.Preferences)
		#updateAction = self.createAction ('&Update', self.update, ':/icons/update.png', 'Update SAM')
		aboutAction = self.createAction ('&About', self.about, ':/icons/help-about.png', 'About SAM')
		quitAction = self.createAction ('&Quit', self.quit, ':/icons/application-exit.png', 'Quit SAM', QKeySequence.Quit)
		
		menubar = self.menuBar()
		userMenu = menubar.addMenu ('&Users')
		userMenu.addAction (newUserAction)
		userMenu.addAction (sortAction)
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

		self.table = QTreeWidget (self)
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
		self.connect ( self.table, SIGNAL('itemSelectionChanged()'), self.selectItem )
		self.connect ( self.table, SIGNAL('itemClicked(QTreeWidgetItem*,int)'), self.selectItem )
		self.connect ( self.table, SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'), self.login )
		self.connect ( self.loginTimer, SIGNAL('timeout()'), self.reLogin )
		self.connect ( self.quotaTimer, SIGNAL('timeout()'), self.refreshQuota )

	def loadPrefs (self):
		settings = QSettings("DA-IICT","SAM")
		point = settings.value("pos").toPoint()
		size = settings.value("size").toSize() 
		self.setGeometry(QRect(point,size))
		
		settings.beginGroup("Conf")
		self.settings.auto_login=(settings.value("AutoLogin")).toBool()
		self.settings.auto_switch = (settings.value("AutoSwitch")).toBool()
		self.autoSwitchAction.setChecked (self.settings.auto_switch)
		self.settings.switch_on_critical=(settings.value("SwitchOnCritical")).toBool()
		self.balloonAction.setChecked((settings.value("Ballons")).toBool())
		
		self.settings.update_quota_after = (settings.value("UpdateQuotaAfter")).toInt()[0]
		self.settings.relogin_after = (settings.value("ReloginAfter")).toInt()[0]
		self.loginTimer.setInterval ( self.settings.relogin_after*1000 )
		self.quotaTimer.setInterval ( self.settings.update_quota_after*1000 )
		self.settings.critical_quota_limit=(settings.value("CriticalQuotaLimit")).toFloat()[0]
		self.settings.server=str(settings.value("Server").toString())
		self.settings.port= str(settings.value("Port").toString())
		self.settings.rev=str(settings.value("Rev").toString())
		self.settings.domain=str(settings.value("Domain").toString())
		settings.endGroup()
		
		settings.beginGroup("Account")
		length = (settings.value("Length")).toInt()[0]
		for ac in range(length):
			temp1= "Account"+str(ac)
			temp = settings.value(temp1).toString()
			username, password = temp.split('!@#$%')
			self.addAccount(str(username),str(password),True)
		settings.endGroup()

		lck = open(lck_file, 'w')
		lck.write ( str(os.getpid()) )
		lck.close()
			
		if self.settings.auto_login == True and self.table.topLevelItemCount()>0:
			self.login()

	def setAutoSwitch (self, checked):
		self.settings.auto_switch = checked
		self.savePrefs()

	def setBalloon (self, checked):
		self.settings.balloons = checked
		self.savePrefs()

	def minimizeEvent(self, event):
		if self.isVisible():
			self.hide()
		event.ignore()

	def closeEvent(self, event):
		if self.isVisible():
			self.hide()
		event.ignore()

	def selectItem (self):
		self.table.setCurrentItem (self.table.currentItem(), 2)

	def toggleWindow (self, reason):
		if reason == QSystemTrayIcon.Trigger:
			self.hide() if self.isVisible() else self.show()

	def addAccount (self, uid=None, pwd=None, auto=False):
		import prompt
		if uid is not None and pwd is not None:
			new = Account (self.table, uid+self.settings.domain, uid, pwd, self.table.topLevelItemCount())
			self.table.setItemWidget (new, 2, new.pbar)
			#self.connect (new.thread, SIGNAL('limitExceeded()'), self.onLimitExceed)
			#self.connect (new.thread, SIGNAL('wrongPassword()'), self.onWrongPassword)
			#self.connect (new.thread, SIGNAL('multipleLogin()'), self.onMultipleLogin)
			self.connect (new.thread, SIGNAL('networkError()'), self.onNetworkError)
			self.connect (new.thread, SIGNAL('usage(int)'), new.pbar.setValue)
			self.connect (new.thread, SIGNAL('setIcon(QString)'), new._setIcon)
			self.connect (new.thread, SIGNAL('switch(int)'), self.switch)
			self.connect (new.thread, SIGNAL('loggedIn(int)'), self.onLoggedIn)
			self.connect (new.thread, SIGNAL('loggedOut()'), self.onLoggedOut)
			self.connect (new.thread, SIGNAL('gotQuota(int)'), self.onGotQuota)
			self.status.showMessage (uid+' added', 5000)
			self.getQuota (new)
		else:
			dlg = prompt.Prompt(self)
			dlg.setWindowIcon (QIcon(':/icons/list-add-user.png'))
			if dlg.exec_():
				self.addAccount(str(dlg.unameEdit.text()), str(dlg.pwdEdit.text()), auto)
				if not auto:
					self.savePrefs ()

	def editAccount (self):
		import prompt
		item = self.table.currentItem()
		dlg = prompt.Prompt(self, item.text(0))
		dlg.setWindowIcon (QIcon(':/icons/user-properties.png'))
		if dlg.exec_():
			item.username = str(dlg.unameEdit.text())+self.settings.domain
			item.setText (0, str(dlg.unameEdit.text()))
			if str(dlg.pwdEdit.text()) != '':
				item.passwd = str( dlg.pwdEdit.text() )
			if self.table.indexOfTopLevelItem(item) == self.currentLogin:
				self.reLogin()
			else:
				self.getQuota ( item )
			self.savePrefs ()

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
			self.settings.balloons = dlg.balloonPopups.isChecked()
			self.balloonAction.setChecked ( self.settings.balloons )
			self.settings.relogin_after = dlg.loginSpin.value()*60
			self.settings.update_quota_after = dlg.quotaSpin.value()*60
			
			# Reinitiate timers
			self.loginTimer.stop()
			self.quotaTimer.stop()
			self.loginTimer.setInterval ( self.settings.relogin_after*1000 )
			self.quotaTimer.setInterval ( self.settings.update_quota_after*1000 )
			self.loginTimer.start()
			self.quotaTimer.start()
			
			self.settings.auto_switch = dlg.autoSwitchCheck.isChecked()
			self.autoSwitchAction.setChecked ( self.settings.auto_switch )
			self.settings.switch_on_critical = dlg.criticalCheck.isChecked() and dlg.autoSwitchCheck.isChecked()
			if self.settings.switch_on_critical:
				self.settings.critical_quota_limit = dlg.criticalSpin.value()*1024
			self.savePrefs()

	def login (self, item=None):
		if item is None:
			item = self.table.currentItem()
			if item is None:
				item = self.table.topLevelItem(0)
				self.table.setCurrentItem(item)
		if item.thread.isRunning():
			item.thread.wait()
		item.thread.run = item.login
		self.currentLogin = self.table.indexOfTopLevelItem(item) #experimental
		item.thread.start()

	def onLoggedIn (self, acc_no):
		self.loginTimer.stop()
		self.quotaTimer.stop()
		self.currentLogin = acc_no
		self.loginTimer.start ()
		self.quotaTimer.start ()
		self.getQuota (self.table.topLevelItem(acc_no))
		if self.settings.balloons:
			self.tray.showMessage ('SAM', self.table.topLevelItem(acc_no).text(0)+': Logged in')
		for i in range (self.table.topLevelItemCount()):
			item = self.table.topLevelItem(i)
			if item.text(1) == 'Logged in' and self.currentLogin!=i:
				item.setText (1, '')
				item.setIcon (0, QIcon(YELLOW))

	def reLogin (self):
		self.login (self.table.topLevelItem(self.currentLogin))

	def logout (self):
		item = self.table.topLevelItem (self.currentLogin)
		if item.thread.isRunning():
			item.thread.wait()
		item.thread.run = item.logout
		item.thread.start()

	def onLoggedOut (self):
		self.loginTimer.stop()
		self.quotaTimer.stop()
		self.currentLogin = -1

	def refreshQuota (self):
		self.getQuota( self.table.topLevelItem(self.currentLogin) )

	def getQuota (self, item=None):
		if item is None:
			item = self.table.currentItem()
		if item.thread.isRunning():
			item.thread.wait()
		item.thread.run = item.getQuota
		item.thread.start()

	def onGotQuota (self, acc_no):
		if self.settings.switch_on_critical:
			item = self.table.topLevelItem (acc_no)
			used = item.pbar.value()
			if used >= int(round(self.settings.critical_quota_limit/1024.0)):
				item.setText (1, 'Critical usage')
				item.setIcon (0, QIcon (RED))
				if acc_no == self.currentLogin:
					self.switch (acc_no)

	def switch (self, switch_from):
		if self.currentLogin != switch_from:
			return
		if not self.settings.auto_switch or switch_from == self.table.topLevelItemCount()-1:
			self.currentLogin = -1
			return
		self.login ( self.table.topLevelItem(switch_from+1) )

	def onNetworkError (self):
		self.status.showMessage ('Network Error')
		self.tray,showMessage ('Network Error')

	def move (self, to):
		if self.table.topLevelItemCount()<2:
			return None
		current = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		bound = (to>0) * (self.table.topLevelItemCount()-1)
		if current == bound:
			return None
		
		values=[]
		for i in range (self.table.topLevelItemCount()):
			values.append (self.table.topLevelItem(i).pbar.value())
		values.insert (current+to, values.pop(current))
		self.table.insertTopLevelItem ( current+to, self.table.takeTopLevelItem (current) )
		
		if current == self.currentLogin:
			self.currentLogin += to
		elif current+to == self.currentLogin:
			self.currentLogin -= to

		self.table.setCurrentItem ( self.table.topLevelItem(current+to) )
		self.updateBars(values)

	def up (self): self.move (-1)

	def down (self): self.move (1)

	def sort (self):
		curr = self.table.topLevelItem(self.currentLogin).text(0)
		self.table.sortItems (0, Qt.AscendingOrder)
		for i in range (self.table.topLevelItemCount()):
			if self.table.topLevelItem(i).text(0) == curr:
				self.currentLogin = i
				break

	def updateBars (self, values=[]):
		if len(values)!=self.table.topLevelItemCount():
			return
		for i in range(0, self.table.topLevelItemCount()):
			item = self.table.topLevelItem(i)
			item.acc_no = i
			item.pbar = QProgressBar()
			item.pbar.setRange (0, 100)
			item.pbar.setValue (values[i])
			self.table.setItemWidget(item, 2, item.pbar)

	def rmAccount (self):
		if self.table.topLevelItemCount() == 0:
			self.status.showMessage ('Nothing to remove!', 5000)
			return None
		current = self.table.indexOfTopLevelItem ( self.table.currentItem() )
		item = self.table.takeTopLevelItem (current)
		self.status.showMessage (item.text(0)+' removed', 5000)
		#self.updateBars()
		self.savePrefs ()
		return item

	def clearList (self):
		if self.table.topLevelItemCount()==0:
			self.status.showMessage ('List already clear!', 5000)
			return None
		b = QMessageBox.question (self, 'SAM', 'Are you sure you want to remove all accounts?', QMessageBox.Yes | QMessageBox.No)
		if b == QMessageBox.Yes:
			self.table.clear()
			self.status.showMessage ('List cleared', 5000)
			self.savePrefs()

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
		self.savePrefs()
		os.remove(lck_file)
		qApp.quit()

	def savePrefs (self):
		settings= QSettings("DA-IICT","SAM")
		settings.setValue("size",self.size())
		settings.setValue("pos",self.pos())
		
		settings.beginGroup("Account")
		settings.setValue("Length", self.table.topLevelItemCount())
		for i in range(self.table.topLevelItemCount()):
			ac = self.table.topLevelItem(i)
			temp = str(ac.text(0))+'!@#$%'+ac.passwd
			temp1 = "Account"+str(i)
			settings.setValue(temp1, temp)
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

	def commitData(self,manager):
		lis = qApp.allWidgets()
		for l in lis:
			if type(l) == type(MainWindow()):
				l.savePrefs()

def main():
	app = QApplication (sys.argv)
	window = MainWindow()
	window.show()
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
