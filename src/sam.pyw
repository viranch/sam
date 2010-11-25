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
from base64 import *

GREEN = ':/icons/ball-green.png'
RED = ':/icons/ball-red.png'
YELLOW = ':/icons/ball-yellow.png'

lck_file = '.sam.lck'

if "linux2" in sys.platform:
	def set_proc_name(newname):
		from ctypes import cdll, byref, create_string_buffer
		libc = cdll.LoadLibrary('libc.so.6')    #Loading a 3rd party library C
		buff = create_string_buffer(len(newname)+1) #Note: One larger than the name (man prctl says that)
		buff.value = newname                            #Null terminated string as it should be
		libc.prctl(15, byref(buff), 0, 0, 0) #Refer to "#define" of "/usr/include/linux/prctl.h" & arg[3..5] are zero as the man page says.
	set_proc_name("SAM")


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
			self.thread.emit (SIGNAL('gotQuota(int)'), self.acc_no)
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
		updateAction = self.createAction ('&Update', self.update, ':/icons/update.png', 'Update SAM')
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
		self.autoSwitchAction.setChecked (settings.value("AutoSwitch").toBool())
		self.balloonAction.setChecked((settings.value("Balloons")).toBool())
		self.loginTimer.setInterval ( settings.value("ReloginAfter").toInt()[0]*1000 )
		self.quotaTimer.setInterval ( settings.value("UpdateQuotaAfter").toInt()[0]*1000 )
		settings.endGroup()
		
		settings.beginGroup("Accounts")
		length = (settings.value("Length")).toInt()[0]
		for ac in range(length):
			temp1= "Account"+str(ac)
			temp = settings.value(temp1).toString()
			username, password = temp.split('!@#$%')
			pasw = b64decode(str(password))
			self.addAccount(str(username),str(pasw))
		settings.endGroup()

		lck = open(lck_file, 'w')
		lck.write ( str(os.getpid()) )
		lck.close()
			
		if self.getSetting('Conf', 'AutoLogin').toBool() and self.table.topLevelItemCount()>0:
			self.login()

	def setAutoSwitch (self, checked):
		self.setSetting ('Conf', 'AutoSwitch', int(checked))

	def setBalloon (self, checked):
		self.setSetting ('Conf', 'Balloons', int(checked))

	def closeEvent(self, event):
		if self.isVisible():
			self.hide()
		event.ignore()

	def selectItem (self):
		self.table.setCurrentItem (self.table.currentItem(), 2)

	def toggleWindow (self, reason):
		if reason == QSystemTrayIcon.Trigger:
			self.hide() if self.isVisible() else self.show()

	def addAccount (self, uid=None, pwd=None):
		import prompt
		if uid is not None and pwd is not None:
			new = Account (self.table, uid+str(self.getSetting('Conf', 'Domain').toString()), uid, pwd, self.table.topLevelItemCount())
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
			self.getQuota (new)
			self.status.showMessage (uid+' added', 5000)
			self.setSetting ('Accounts', 'Length', self.table.topLevelItemCount())
			self.setSetting ('Accounts', 'Account'+str(self.table.indexOfTopLevelItem(new)), new.text(0)+'!@#$%'+b64encode(str(new.passwd)))
		else:
			dlg = prompt.Prompt(self)
			dlg.setWindowIcon (QIcon(':/icons/list-add-user.png'))
			if dlg.exec_():
				self.addAccount(str(dlg.unameEdit.text()), str(dlg.pwdEdit.text()))

	def editAccount (self):
		import prompt
		item = self.table.currentItem()
		dlg = prompt.Prompt(self, item.text(0))
		dlg.setWindowIcon (QIcon(':/icons/user-properties.png'))
		if dlg.exec_():
			item.username = str(dlg.unameEdit.text())+str(self.getSetting('Conf', 'Domain').toString())
			item.setText (0, str(dlg.unameEdit.text()))
			if str(dlg.pwdEdit.text()) != '':
				item.passwd = str( dlg.pwdEdit.text() )
			if self.table.indexOfTopLevelItem(item) == self.currentLogin:
				self.reLogin()
			else:
				self.getQuota ( item )
			self.setSetting ('Accounts', 'Account'+str(self.table.indexOfTopLevelItem(item)), item.text(0)+'!@#$%'+ b64encode(str(item.passwd)))

	def configure (self):
		import settings
		dlg = settings.SettingsDlg(self)
		if dlg.exec_():
			s = QSettings ('DA-IICT', 'SAM')
			s.beginGroup("Conf")
			s.setValue("AutoLogin", int(dlg.autoLogin.isChecked()))
			s.setValue("AutoSwitch", int(dlg.autoSwitchCheck.isChecked()))
			s.setValue("SwitchOnCritical", int(dlg.criticalCheck.isChecked() and dlg.autoSwitchCheck.isChecked()))
			s.setValue("Balloons", int(dlg.balloonPopups.isChecked()))
			s.setValue("UpdateQuotaAfter", dlg.quotaSpin.value()*60)
			s.setValue("ReloginAfter", dlg.loginSpin.value()*60)
			s.setValue("CriticalQuotaLimit", dlg.criticalSpin.value()*1024)
			s.setValue("Server", str (dlg.ipEdit.text()))
			s.setValue("Port", str (dlg.portEdit.text()))
			s.setValue("Domain", str(dlg.domainEdit.text()))
			s.endGroup()
			
			Cyberoam.cyberroamIP = str(dlg.ipEdit.text())
			Cyberoam.cyberroamPort = str(dlg.portEdit.text())
			self.autoSwitchAction.setChecked ( dlg.autoSwitchCheck.isChecked() )
			self.balloonAction.setChecked ( dlg.balloonPopups.isChecked() )
			
			# Reinitiate timers
			self.loginTimer.stop()
			self.quotaTimer.stop()
			self.loginTimer.setInterval ( dlg.loginSpin.value()*60*1000 )
			self.quotaTimer.setInterval ( dlg.quotaSpin.value()*60*1000 )
			self.loginTimer.start()
			self.quotaTimer.start()

	def setSetting (self, group, key, value):
		s = QSettings ('DA-IICT', 'SAM')
		s.beginGroup (group)
		s.setValue (key, value)
		s.endGroup()

	def getSetting (self, group, key):
		s = QSettings ('DA-IICT', 'SAM')
		s.beginGroup (group)
		r = s.value (key)
		s.endGroup()
		return r

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
		if self.getSetting('Conf', 'Balloons').toBool():
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
		if self.getSetting ('Conf', 'SwitchOnCritical').toBool():
			item = self.table.topLevelItem (acc_no)
			used = item.pbar.value()
			if used >= int(round(self.getSetting('Conf','CriticalQuotaLimit').toInt()[0]/1024.0)):
				item.setText (1, 'Critical usage')
				item.setIcon (0, QIcon (RED))
				if acc_no == self.currentLogin:
					if acc_no == self.table.topLevelItemCount()-1:
						self.tray.showMessage ('SAM', 'Critical usage of last account reached.')
					else:
						self.switch (acc_no)
	

	def switch (self, switch_from):
		if self.currentLogin != switch_from:
			return
		if not self.getSetting('Conf', 'AutoSwitch').toBool():
			self.currentLogin = -1
			return
		if switch_from == self.table.topLevelItemCount()-1 and self.table.topLevelItem(switch_from).text(1)=='Limit Reached':
			self.currentLogin = -1
			self.tray.showMessage('SAM', 'Data transfer limit for last account exceeded.')
			return
		self.login ( self.table.topLevelItem(switch_from+1) )

	def onNetworkError (self):
		self.status.showMessage ('Network Error')
		self.tray.showMessage ('SAM', 'Network Error')

	def update (self):
		import update
		o = update.Updater( self, str( self.getSetting('Conf', 'rev').toString() ) )
		path = os.path.dirname(__file__)
		ls = os.listdir ( path )
		if o.exec_():
			for item in ls:
				if item[-4:]=='.tmp':
					try:
						os.remove ( path+os.sep+item[:-4] )
					except: pass
					os.rename ( path+os.sep+item, path+os.sep+item[:-4] )
			self.setSetting ('Conf', 'rev', o.rev)
		else:
			for item in ls:
				if item.endswith('.tmp'):
					os.remove ( path+os.sep+item )

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
		self.updateList(values)
		for i in [current, current+to]:
			item = self.table.topLevelItem(i)
			self.setSetting ('Accounts', 'Account'+str(i), str(item.text(0))+'!@#$%'+b64encode(str(item.passwd)))

	def up (self): self.move (-1)

	def down (self): self.move (1)

	def sort (self):
		curr = self.table.topLevelItem(self.currentLogin).text(0)
		self.table.sortItems (0, Qt.AscendingOrder)
		for i in range (self.table.topLevelItemCount()):
			item = self.table.topLevelItem(i)
			item.acc_no = i
			if item.text(0) == curr:
				self.currentLogin = i
		self.saveAccounts()

	def updateList (self, values=[]):
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
		pop = self.table.takeTopLevelItem (current)
		self.status.showMessage (pop.text(0)+' removed', 5000)
		for i in range (current, self.table.topLevelItemCount()):
			item = self.table.topLevelItem(i)
			self.setSetting ('Accounts', 'Account'+str(i), str(item.text(0))+'!@#$%'+b64encode(str(item.passwd)))
		s = QSettings ('DA-IICT', 'SAM')
		s.beginGroup ('Accounts')
		s.remove ( 'Account'+str(self.table.topLevelItemCount()) )
		
		self.setSetting ('Accounts', 'Length', self.table.topLevelItemCount())
		return pop

	def clearList (self):
		if self.table.topLevelItemCount()==0:
			self.status.showMessage ('List already clear!', 5000)
			return None
		b = QMessageBox.question (self, 'SAM', 'Are you sure you want to remove all accounts?', QMessageBox.Yes | QMessageBox.No)
		if b == QMessageBox.Yes:
			self.table.clear()
			self.status.showMessage ('List cleared', 5000)
			self.saveAccounts()

	def saveAccounts (self):
		settings = QSettings('DA-IICT', 'SAM')
		settings.beginGroup("Accounts")
		settings.setValue("Length", self.table.topLevelItemCount())
		for i in range(self.table.topLevelItemCount()):
			ac = self.table.topLevelItem(i)
			temp = str(ac.text(0))+'!@#$%'+ b64encode(str(ac.passwd))
			temp1 = "Account"+str(i)
			settings.setValue(temp1, temp)
		settings.endGroup()

	def about (self):
		import about
		dlg = about.About()
		dlg.exec_()

	def quit (self):
		self.loginTimer.stop()
		self.quotaTimer.stop()
		settings= QSettings ("DA-IICT", "SAM")
		settings.setValue ("size", self.size())
		settings.setValue ("pos", self.pos())
		os.remove(lck_file)
		qApp.quit()

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
		os.remove(lck_file)

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
