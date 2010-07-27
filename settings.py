from PyQt4.QtCore import *
from PyQt4.QtGui import *

class SettingsDlg (QDialog):

	def __init__(self, parent):
		super (SettingsDlg, self).__init__(parent)
		self.parent = parent
		self.setWindowTitle ('Preferences')
		
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
		
		self.autoSwitchCheck = QCheckBox ('Enable Auto Switch to next account in the list')
		self.autoSwitchCheck.setChecked (parent.settings.switch_on_critical or parent.settings.switch_on_limit)
		
		self.quotaSwitchCheck = QRadioButton ('When Data Transfer Limit exceeds', self)
		self.quotaSwitchCheck.setChecked (parent.settings.switch_on_critical)
		
		self.criticalSwitchCheck = QRadioButton ('When usage reaches', self)
		self.criticalSwitchCheck.setChecked (parent.settings.switch_on_critical)
		self.criticalSpin = QDoubleSpinBox()
		self.criticalSpin.setSuffix (' MB')
		self.criticalSpin.setRange (5, 100)
		self.criticalSpin.setValue (parent.settings.critical_quota_limit)
		self.criticalSpin.setEnabled (self.criticalSwitchCheck.isChecked())
		hbox = QHBoxLayout()
		hbox.addWidget (self.criticalSwitchCheck)
		hbox.addWidget (self.criticalSpin)

		self.balloonCheck = QCheckBox ( 'Show balloon-popup when usage reaches' )
		self.balloonCheck.setChecked (parent.settings.balloon_popups)
		self.balloonSpin = QDoubleSpinBox()
		self.balloonSpin.setSuffix (' MB')
		self.balloonSpin.setValue ( parent.settings.balloon_limit )
		self.balloonSpin.setEnabled ( self.balloonCheck.isChecked() )
		hbox_1 = QHBoxLayout()
		hbox_1.addWidget (self.balloonCheck)
		hbox_1.addWidget (self.balloonSpin)

		buttonBox = QDialogButtonBox ( QDialogButtonBox.Ok | QDialogButtonBox.Cancel )
		
		vbox = QVBoxLayout()
		vbox.addLayout (grid)
		vbox.addWidget ( QLabel() )
		vbox.addWidget ( QLabel() )
		vbox.addWidget (self.autoSwitchCheck)
		vbox.addWidget (self.quotaSwitchCheck)
		vbox.addLayout (hbox)
		vbox.addWidget ( QLabel() )
		vbox.addWidget ( QLabel() )
		vbox.addLayout ( hbox_1 )
		vbox.addWidget (buttonBox)
		self.setLayout (vbox)
		
		self.connect (buttonBox, SIGNAL('accepted()'), self, SLOT('accept()'))
		self.connect (buttonBox, SIGNAL('rejected()'), self, SLOT('reject()'))
		self.connect (self.autoSwitchCheck, SIGNAL('toggled(bool)'), self.updateUi)
		self.connect (self.criticalSwitchCheck, SIGNAL('toggled(bool)'), self.criticalSpin.setEnabled)
		self.connect (self.balloonCheck, SIGNAL('toggled(bool)'), self.balloonSpin.setEnabled)
		
		if not self.quotaSwitchCheck.isChecked() and not self.criticalSwitchCheck.isChecked():
			self.quotaSwitchCheck.setChecked (True)
		self.updateUi(self.autoSwitchCheck.isChecked())

	def updateUi (self, state):
		self.quotaSwitchCheck.setEnabled ( state )
		self.criticalSwitchCheck.setEnabled ( state )
		self.criticalSpin.setEnabled ( self.criticalSwitchCheck.isChecked() and state )
