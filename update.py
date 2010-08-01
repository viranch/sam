import sys
import os
import urllib2
import feedparser
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Updater (QDialog):

	def __init__ (self, parent, rev):
		super (Updater, self).__init__(parent)
		self.rss = 'http://bitbucket.org/viranch/sam/rss'
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

		self.t = upThread(self)
		path = os.sep.join(sys.argv[0].split(os.sep)[:-1])
		if os.access ( path, os.W_OK ):
			self.t.start()
		else:
			self.status.setText ('Start SAM in super-user\nmode to update it.')

	def slot (self):
		if self.t.isRunning():
			self.reject()
		else:
			self.accept()

class upThread (QThread):

	def __init__ (self, parent):
		super (upThread, self).__init__(parent)
		self.parent = parent
		self.rss = 'http://bitbucket.org/viranch/sam/rss'

	def run (self):
		self.parent.status.setText ('Updating...')
		curr_rev = self.parent.rev
		f = feedparser.parse (self.rss)
		try:
			rev = f.entries[-1].link.split('/')[-1]
		except IndexError:
			self.parent.status.setText ('Error')
		if rev!=curr_rev:
			update_list = []
			content = f.entries[-1]['summary_detail']['value']
			while True:
				start = content.find('http://')
				if start<0:
					break
				content = content[start:]
				end = content.find('\"')
				update_list.append ( content[:end].replace('src', 'raw') )
				content = content[end:]
			for link in update_list:
				name = link.split('/')[-1]
				if 'TODO'==name:
					continue
				self.parent.status.setText ('Downloading '+name+'...')
				u = urllib2.urlopen ( link )
				path = os.sep.join(sys.argv[0].split(os.sep)[:-1])+os.sep+name+'.tmp'
				out = open(path, 'w')
				out.write ( u.read() )
				out.close()
				os.chmod (path, 64)
			self.parent.rev = rev
			self.parent.status.setText ('Done')
		else: self.parent.status.setText ('Up-to-date')
