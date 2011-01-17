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

def cyberroamAddress():
	add = cyberroamIP
	if cyberroamPort != "":
		add += ":"+cyberroamPort
	return add

class WrongPassword (Exception): pass
class DataTransferLimitExceeded (Exception): pass
class MultipleLoginError (Exception): pass

def netUsage(username, passwd):
	url = "http://"+cyberroamAddress()+"/corporate/servlet/MyAccountManager"
	data = "mode=1&login_username=&secretkey=&js_autodetect_results=SMPREF_JS_OFF&just_logged_in=1&username="+username+"&password="+passwd+"&select=My+Account&soft_25.x=0&soft_25.y=0"
	cj = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	opener.addheaders = [('Referer','http://10.100.56.55:8090/myaccount.html')]
	usock = opener.open(url, data)
	the_page = usock.read()
	start = the_page.find('Cycle Download Data Transfer')
	if start<0:
		raise WrongPassword
	the_page = the_page[start:]
	quota = []
	for i in range (0, 3):
		start = the_page.find('<TD align="left" class=texttd><font class=\'textfont\'>')
		the_page = the_page[start+53:]
		end = the_page.find('</')
		quota.append (the_page[:end])
	quota = quota[-2:]
	if '0.00 KB' in quota[1]:
		raise DataTransferLimitExceeded
	return quota

def login (username, passwd):
	f = urllib.urlopen("http://"+cyberroamAddress()+"/corporate/servlet/CyberoamHTTPClient","mode=191&isAccessDenied=null&url=null&message=&username="+username+"&password="+passwd+"&saveinfo=saveinfo&login=Login")
	s = f.read()
	f.close()
	
	if 'Make+sure+your+password+is+correct' in s:
		raise WrongPassword
	if 'DataTransfer+limit+has+been+exceeded' in s:
		raise DataTransferLimitExceeded
	if 'Multiple+login+not+allowed' in s:
		raise MultipleLoginError

def logout (username, passwd):
	f = urllib.urlopen("http://"+cyberroamAddress()+"/corporate/servlet/CyberoamHTTPClient","mode=193&isAccessDenied=null&url=null&message=&username="+username+"&password="+passwd+"&saveinfo=saveinfo&logout=Logout")
	s = f.read()
	f.close()
