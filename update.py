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
			self.status.setText ('You do not have apprppriate\npermissions to update SAM.')

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
		update_list = []
		
		try:
			rev = f.entries[-1].link.split('/')[-1]
		except KeyError:
			self.parent.setText ('Error')
			return None
		
		for en in f.entries[::-1]:
			if en.link.split('/')[-1] == curr_rev:
				break
			tmp_list = self.parse_contents (en)
			ctr = 0
			for i in range ( len(tmp_list) ):
				name = tmp_list[i].split('/')[-1]
				flag = False
				for link in update_list:
					if name == link.split('/')[-1]:
						flag = True
						break
				if not flag:
					update_list.insert (ctr, tmp_list[i])
					ctr += 1
		
		for link in update_list:
			name = link.split('/')[-1]
			if 'TODO'==name or 'install.sh'==name or 'sam'==name:
				continue
			self.parent.status.setText ('Downloading '+name+'...')
			try:
				u = urllib2.urlopen ( link )
			except urllib2.HTTPError:
				continue
			path = os.sep.join(sys.argv[0].split(os.sep)[:-1])+os.sep+name+'.tmp'
			out = open(path, 'w')
			out.write ( u.read() )
			out.close()
		self.parent.rev = rev
		
		if len(update_list)==0:
			self.parent.status.setText ('Up-to-date')
		else:
			self.parent.status.setText ('Done')

	def parse_contents (self, en):
		content = en['summary_detail']['value']
		up_list = []
		while True:
			start = content.find('http://')
			if start<0:
				break
			content = content[start:]
			end = content.find('\"')
			up_list.append ( content[:end].replace('/src/', '/raw/') )
			content = content[end:]
		return up_list