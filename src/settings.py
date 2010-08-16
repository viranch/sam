from PyQt4.QtCore import *
from PyQt4.QtGui import *

class SettingsDlg (QDialog):

	def __init__(self, parent):
		super (SettingsDlg, self).__init__(parent)
		self.parent = parent
		self.setWindowTitle ('Preferences')

		#grid1
		ipLabel = QLabel ('Cyberoam Server IP:')
		portLabel = QLabel ('Port:')
		self.ipEdit = QLineEdit (parent.settings.server)
		colonLabel = QLabel (':')
		self.portEdit = QLineEdit (parent.settings.port)
		grid1 = QGridLayout()
		grid1.addWidget (ipLabel, 0, 0)
		grid1.addWidget (portLabel, 0, 2)
		grid1.addWidget (self.ipEdit, 1, 0)
		grid1.addWidget (colonLabel, 1, 1)
		grid1.addWidget (self.portEdit, 1, 2)

		#autoLogin CheckBox
		self.autoLogin = QCheckBox ('Auto login on startup')
		self.autoLogin.setChecked (parent.settings.auto_login)

		#grid
		loginIntervalLabel = QLabel ('Re-login after every:')
		self.loginSpin = QSpinBox ()
		self.loginSpin.setSuffix (' minutes')
		self.loginSpin.setRange (1, 60)
		self.loginSpin.setValue (parent.settings.relogin_after/60)
		
		quotaIntervalLabel = QLabel ('Refresh Quota usage after every:')
		self.quotaSpin = QSpinBox()
		self.quotaSpin.setSuffix (' minutes')
		self.quotaSpin.setRange (1, 60)
		self.quotaSpin.setValue (parent.settings.update_quota_after/60)
		
		grid = QGridLayout()
		grid.addWidget (loginIntervalLabel, 0, 0)
		grid.addWidget (self.loginSpin, 0, 1)
		grid.addWidget (quotaIntervalLabel, 1, 0)
		grid.addWidget (self.quotaSpin, 1, 1)

		#autoSwitch CheckBox
		self.autoSwitchCheck = QCheckBox ('Enable Auto Switch')
		self.autoSwitchCheck.setChecked (parent.settings.auto_switch)

		#hbox
		self.criticalCheck = QCheckBox ('Switch when usage reaches:')
		self.criticalCheck.setChecked (parent.settings.switch_on_critical and parent.settings.auto_switch)
		self.criticalCheck.setEnabled (self.autoSwitchCheck.isChecked())
		self.criticalSpin = QDoubleSpinBox()
		self.criticalSpin.setSuffix (' MB')
		self.criticalSpin.setRange (5, 100)
		self.criticalSpin.setValue (parent.settings.critical_quota_limit/1024)
		self.criticalSpin.setEnabled (self.criticalCheck.isChecked())
		hbox = QHBoxLayout()
		hbox.addWidget (self.criticalCheck)
		hbox.addWidget (self.criticalSpin)

		#balloonPopup CheckBox
		self.balloonPopups = QCheckBox ( 'Enable balloon popups' )
		self.balloonPopups.setChecked ( parent.settings.balloons )

		#buttonBox
		buttonBox = QDialogButtonBox ( QDialogButtonBox.Ok | QDialogButtonBox.Cancel )
		
		vbox = QVBoxLayout()
		vbox.addLayout (grid1)
		vbox.addWidget (self.autoLogin)
		vbox.addWidget ( QLabel() )
		vbox.addLayout (grid)
		vbox.addWidget ( QLabel() )
		vbox.addWidget ( QLabel() )
		vbox.addWidget (self.autoSwitchCheck)
		vbox.addLayout (hbox)
		vbox.addWidget ( QLabel() )
		vbox.addWidget ( QLabel() )
		vbox.addWidget ( self.balloonPopups )
		vbox.addWidget (buttonBox)
		self.setLayout (vbox)
		
		self.connect (buttonBox, SIGNAL('accepted()'), self, SLOT('accept()'))
		self.connect (buttonBox, SIGNAL('rejected()'), self, SLOT('reject()'))
		self.connect (self.autoSwitchCheck, SIGNAL('toggled(bool)'), self.updateUi)
		self.connect (self.criticalCheck, SIGNAL('toggled(bool)'), self.criticalSpin.setEnabled)
		
	def updateUi (self, state):
		self.criticalCheck.setEnabled ( state )
		self.criticalSpin.setEnabled ( state and self.criticalCheck.isChecked() )

