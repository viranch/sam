from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Prompt (QDialog):

	def __init__(self, parent=None, uid=None):
		super (Prompt, self).__init__(parent)

		self.buttonBox = QDialogButtonBox (QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
		unameLabel = QLabel ('Username:')
		suffLabel = QLabel (parent.getSetting('Conf', 'Domain').toString())
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
