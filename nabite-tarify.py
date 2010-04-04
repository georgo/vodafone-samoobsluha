#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Kontrola Vodafone CZ stavu prenesenych dat
# @author Tomas Kopecny <tomas@kopecny.info>

import urllib, urllib2, copy, os, sys, socket, re, smtplib, base64

def unicode_urlencode(params):
	if isinstance(params, dict):
		params = params.items()
		return urllib.urlencode([(k, isinstance(v, unicode) and v.encode('utf-8') or v) for k, v in params]).replace('%3A',':')


class samoobsluha:
	user		= "Your-Phone-Number"
	passwd		= "Base64-encoded-Passowrd"
	sendto		= ["Your-Mobile-Email@vodafonemail.cz"]
	sendfrom	= "Email-sender"

class Samoobsluha:
	def __init__(self):
		self.kernel = copy.deepcopy(samoobsluha())
		self.token = None # Token
		self.price = None
		self.traffic = None
		self.credit = None
		self.bill = None

	def login(self):
		pole = {
			'msisdn': self.kernel.user,
			'passwd': base64.decodestring(self.kernel.passwd),
			'lang': "cs",
			'search-submit': "1"
		}

		try:
			socket.setdefaulttimeout(10)
			request = urllib.urlopen("https://samoobsluha.vodafone.cz/login.php", unicode_urlencode(pole))
			data = request.read()
			self.token = re.findall(u'OSKWSCID=([0-9a-zA-Z]+)', data.decode('utf-8'))[0]
			return True
		except:
			raise

	def checkData(self):
		try:
			socket.setdefaulttimeout(10)
			request = urllib.urlopen("https://samoobsluha.vodafone.cz/data_tariff.php?OSKWSCID=%s" %(self.token))
			data = request.read()
			price = re.findall(u'</strong></td><td>([0-9]+),([0-9]{2}) Kč', data.decode('utf-8'))[0]
			self.price = "%s.%s" %(price[0], price[1])
			self.traffic = re.findall(u'dat<\/strong><\/td><td>([0-9,]+) MB<\/td>', data.decode('utf-8'))[0].replace(",",".")

			return True
		except:
			raise

	def checkBill(self):
		try:
			socket.setdefaulttimeout(10)
			request = urllib.urlopen("https://samoobsluha.vodafone.cz/account_status.php?OSKWSCID=%s" %(self.token))
			data = request.read()
			bill = re.findall(u'Celkem</th><td class="total second-col"[^>]*>([0-9]+)', data.decode('utf-8'))[0]
			self.bill = bill
			return True
		except:
			raise

	def checkCredit(self):
		try:
			socket.setdefaulttimeout(10)
			request = urllib.urlopen("https://samoobsluha.vodafone.cz/accbal.php?mode=1&show=2&OSKWSCID=%s" %(self.token))
			data = request.read()
			credit = re.findall(u'<strong>Zbývá vyčerpat</strong></td><td class="right">([0-9]+),([0-9]{2})', data.decode('utf-8'))[0]
			self.credit = "%s.%s" %(credit[0], credit[1])
			return True
		except:
			raise

	def send(self):
		try:
			server = smtplib.SMTP("localhost")
			msg = "From: %s\r\nSubject:Vodafone\r\n\r\nUcet: %s Kc, Kredit: %s Kc, Data: %s MB - %s Kc" %(self.kernel.sendfrom, self.bill, self.credit, self.traffic, self.price)
			server.sendmail(self.kernel.sendfrom, self.kernel.sendto, msg)
			server.quit()
		except:
			raise


vodafone = Samoobsluha()
if vodafone.login():
	if vodafone.checkBill():
		if vodafone.checkCredit():
			if vodafone.checkData():
				vodafone.send();
			else:
				sys.exit(4)
		else:
			sys.exit(3)
	else:
		sys.exit(2)
else:
	sys.exit(1)
sys.exit(0)
