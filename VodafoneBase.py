#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os, re, urllib, socket, base64

class VodafoneBase:
	""" Constants """
	_loginUrl = "https://muj.vodafone.cz/prihlaseni"

	""" User credentials"""
	_user = "608123456"
	_password = ""

	""" Contructor, define username (phone number) and decode password"""
	def __init__(self, user, password):
		self._user = user
		self._password = base64.decodestring(password)
	
	def _getLoginPageToken(self):
		try:
			socket.setdefaulttimeout(10)
			loginPage = urllib.urlopen(self._loginUrl)
			loginPageData = loginPage.read()
			token = re.findall(u'_csrf_token" value="([a-zA-Z0-9\-]+)"', loginPageData.decode('utf-8'))
			if len(a) < 1:
				
			print token
		except:
			raise

	def login(self):
		token = self._getLoginPageToken()



