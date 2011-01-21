import sys
import os
import urllib2
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Updater (QDialog):

	def __init__ (self, parent, rev):
		super (Updater, self).__init__(parent)
		self.rev = rev
		self.update_rev = ''

		vbox = QVBoxLayout()
		self.status = QLabel('')
		vbox.addWidget (self.status)
		buttonBox = QDialogButtonBox ( QDialogButtonBox.Close )
		vbox.addWidget (buttonBox)
		self.setLayout (vbox)
		self.setWindowTitle ('Update SAM')

		self.connect ( buttonBox, SIGNAL('rejected()'), self.slot )

		self.t = QThread()
		self.t.run = self.update
		path = os.sep.join(sys.argv[0].split(os.sep)[:-1])
		if os.access ( path, os.W_OK ):
			self.t.start()
		else:
			self.status.setText ('You do not have apprppriate\npermissions to update SAM.')

	def slot (self):
		if self.t.isRunning() or 'Error' in self.status.text():
			self.reject()
		else:
			self.accept()

	def update (self):
		self.status.setText ('Looking for updates...')
		
		f = urllib2.urlopen ('http://bitbucket.org/viranch/sam')
		rev = f.read()
		f.close()
		
		b = rev.find('/graph/') + len('/graph/')
		rev = rev[b:]
		rev = rev[:rev.find('\"')]
		
		if rev==self.rev:
			self.status.setText ('Up-to-date')
			return
		
		self.status.setText ('Updating...')
		
		for name in ['Cyberoam.py', 'about.py', 'prompt.py', 'qrc_icon.py', 'sam.pyw', 'settings.py', 'update.py']:
			link = 'http://bitbucket.org/viranch/sam/raw/'+rev+'/src/'+name
			try:
				u = urllib2.urlopen ( link )
			except urllib2.HTTPError as err:
				self.status.setText ('Error: '+str(err))
				return
			path = os.sep.join(sys.argv[0].split(os.sep)[:-1])+os.sep+name+'.tmp'
			out = open (path, 'wb')
			out.write ( u.read() )
			out.close()
			u.close()
		self.rev = rev
		self.status.setText ('Done')
