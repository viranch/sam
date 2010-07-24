#
# Author: Abhijeet Rastogi (http://www.google.com/profiles/abhijeet.1989)
# Modified: Viranch Mehta <viranch.mehta@gmail.com>
#

cyberroamIP = "10.100.56.55" #The IP of the Cyberoam site.
cyberroamPort = "8090" #Set to "" if not using.

import sys
import cookielib
import urllib2
import urllib, sgmllib, time

cyberroamAddress = cyberroamIP
if cyberroamPort != "":
	cyberroamAddress = cyberroamAddress+":"+cyberroamPort

class Timeout (Exception): pass
class WrongPassword (Exception): pass
class DataTransferLimitExceeded (Exception): pass

def netUsage(username, passwd):
	url = "http://"+cyberroamAddress+"/corporate/servlet/MyAccountManager"
	data = "mode=1&login_username=&secretkey=&js_autodetect_results=SMPREF_JS_OFF&just_logged_in=1&username="+username+"&password="+passwd+"&select=My+Account&soft_25.x=0&soft_25.y=0"
	cj = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	opener.addheaders = [('Referer','http://10.100.56.55:8090/myaccount.html')]
	usock = opener.open(url, data)
	the_page = usock.read()
	start = the_page.find('Cycle Download Data Transfer')
	the_page = the_page[start:]
	quota = []
	for i in range (0, 3):
		start = the_page.find('<TD align="left" class=texttd><font class=\'textfont\'>')
		the_page = the_page[start+53:]
		end = the_page.find('</')
		quota.append (the_page[:end])
	return quota[-2:]

class MyCyberroamParser(sgmllib.SGMLParser):
	"A simple parser class."

	def parse(self, s):
		"Parse the given string 's'."
		self.feed(s)
		self.close()

	def __init__(self, verbose=0):
		"Initialise an object, passing 'verbose' to the superclass."
	   	sgmllib.SGMLParser.__init__(self, verbose)
		self.required_entities = ['message','loginstatus','liverequesttime']
		self.frames_attr = []
		self.in_required_entity = False
		self.current_entity = ""
		self.entity_values = {}
	
	def do_frame(self, attributes):
		for name, value in attributes:
			if name == "src":
				self.frames_attr.append(value)

	def unknown_entityref(self,ref):
		self.current_entity = ref
		if ref in self.required_entities:
			self.in_required_entity=True

	def handle_data(self, data):
		"Try to get the value of entity &message. Used in 2nd pass of parsing."

		if self.in_required_entity:
			self.entity_values[self.current_entity] = data[1:] #To remove the preceeding =
			self.in_required_entity = False

	def get_src(self,index=-1):
		"Return the list of src targets."
		if index == -1:
			return self.frames_attr
		else:
			return self.frames_attr[index]

def login (username, passwd):
	try:
		f = urllib.urlopen("http://"+cyberroamAddress+"/corporate/servlet/CyberoamHTTPClient","mode=191&isAccessDenied=null&url=null&message=&username="+username+"&password="+passwd+"&saveinfo=saveinfo&login=Login")
	except IOError, (errno, strerror):
		raise Timeout
	s = f.read()
	# Try and process the page.
	# The class should have been defined first, remember.
	myparser = MyCyberroamParser()
	myparser.parse(s)
	
	# Get the the src targets. It contains the status message. And then parse it again for entity &message.
	qindex = myparser.get_src(1).index('?')
	srcstr = myparser.get_src(1)[:qindex+1]+'&'+myparser.get_src(1)[qindex+1:]
	
	myparser.parse(srcstr)
	message = myparser.entity_values['message']
	message = message.replace('+',' ')
	
	if message == "The system could not log you on. Make sure your password is correct":
		raise WrongPassword
	if message == "DataTransfer limit has been exceeded":
		raise DataTransferLimitExceeded
