#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Base Vodafone librabry
# @author Tomas K. <iam@tomask.info>
#
# Usage:
# from VodafoneBase import *
# v = VodafoneBase("608123456", "MTIzNA==")
# if v.login():
#     print "Current bill: %.2f CZK" % (v.getCurrentSpending())
#     data = v.getDataUsage()
#     print "Used data: %.2f MB , remaining %.2f MB" % (data['used'], data['remain'])

import os, re, urllib, urllib2, json, socket, base64, Cookie;

""" urllib configuration """
class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
	def http_error_302(self, req, resp, code, msg, headers):
		return resp

	http_error_301 = http_error_303 = http_error_307 = http_error_302

""" Base Vodafone object """

class VodafoneBase:
	""" URL Constants """
	_lang = "en"
	_originUrl = "https://muj.vodafone.cz/en"
	_loginUrl = "https://muj.vodafone.cz/en/login"
	_loginPostUrl = "https://muj.vodafone.cz/login-check"

	_usageUrl = "https://muj.vodafone.cz/en/spending-and-billing/smart-overview"
	_dataUsageUrl = "https://muj.vodafone.cz/en/spending-and-billing/smart-overview/usage"

	""" User credentials"""
	_user = "608xxxxxx"
	_password = ""
	_session = ""
	_persistent = ""

	""" Contructor, define username (phone number) and decode password"""
	def __init__(self, user, password):
		self._user = user
		self._password = base64.decodestring(password)

		""" Disallow redirects """
		opener = urllib2.build_opener(MyHTTPRedirectHandler)
		urllib2.install_opener(opener)

	""" Parse session (WSCSID) and persistent cookie from response headers """
	def _getSession(self, headers):
		for (header, cont) in headers.items():
				if header == "set-cookie":
					cookies = Cookie.SimpleCookie(cont)
					if "WSCSID" in cookies:
						self._session = cookies["WSCSID"].value
						#print "Changed session id: %s" % (self._session)
					if "persistent" in cookies:
						self._persistent = cookies["persistent"].value
						#print "Changed persistent id: %s" % (self._persistent)
		return True

	""" Get CSRF token from login page """
	def _getLoginPageToken(self):
		try:
			socket.setdefaulttimeout(10)

			loginPageReq = urllib2.Request(self._loginUrl)
			loginPage = urllib2.urlopen(loginPageReq)
			self._getSession(loginPage.info())

			loginPageData = loginPage.read()
			token = re.findall(u'_csrf_token" value="([a-zA-Z0-9\-_]+)"', loginPageData.decode('utf-8'))
			if len(token) < 1:
				print loginPageData
				raise ValueError('Token was not found on login page.')
			return token[0]
		except:
			raise

	""" Perform login on page (requires csrf token) """
	def _postLoginCredentials(self, token):
		loginData = urllib.urlencode({
			'_username': self._user,
			'_password': self._password,
			'_type': 'login',
			'_csrf_token': token
		})
		loginPageReq = urllib2.Request(self._loginPostUrl)
		loginPageReq.add_header("Content-Type", "application/x-www-form-urlencoded")
		loginPageReq.add_header("Content-Length", len(loginData))
		loginPageReq.add_header("Origin", self._originUrl)
		loginPageReq.add_header("Referer", self._loginUrl)
		loginPageReq.add_header("Cookie", "hl=%s; persistent=%s; WSCSID=%s" % (self._lang, self._persistent, self._session))
		loginPageReq.add_header("Upgrade-Insecure-Requests", "1")
		loginPageReq.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36")
		loginPage = urllib2.urlopen(loginPageReq, loginData)
		loginPage.read()
		success =  self._getSession(loginPage.info())

		if success:
			""" Verify homepage """
			loginPageReq = urllib2.Request(self._originUrl)
			loginPageReq.add_header("Origin", self._originUrl)
			loginPageReq.add_header("Referer", self._loginUrl)
			loginPageReq.add_header("Cookie", "hl=%s; persistent=%s; WSCSID=%s" % (self._lang, self._persistent, self._session))
			loginPageReq.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36")
			loginPage = urllib2.urlopen(loginPageReq)
			return True

		return False

	""" Get spending in current month """
	def _getCurrentSpending(self):
		usagePageReq = urllib2.Request(self._usageUrl)
		usagePageReq.add_header("Origin", self._originUrl)
		usagePageReq.add_header("Referer", self._originUrl)
		usagePageReq.add_header("Cookie", "hl=%s; persistent=%s; WSCSID=%s" % (self._lang, self._persistent, self._session))
		usagePageReq.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36")
		usagePage = urllib2.urlopen(usagePageReq)
		usagePageData = usagePage.read()

		# <strong class="blue big vodafoneRgBd">1 096,10 CZK</strong>
		currentSpendingRe = re.findall(u'<strong class="blue big vodafoneRgBd">([0-9 ,]+) CZK<\/strong>', usagePageData.decode('utf-8'))
		currentSpending = float(currentSpendingRe[0].replace(" ", "").replace(",", "."))

		return currentSpending

	""" Get usage of data and remaining on data tariff """
	def _getDataUsage(self):
		usagePageReq = urllib2.Request(self._usageUrl)
		usagePageReq.add_header("Origin", self._originUrl)
		usagePageReq.add_header("Referer", self._originUrl)
		usagePageReq.add_header("Cookie", "hl=%s; persistent=%s; WSCSID=%s" % (self._lang, self._persistent, self._session))
		usagePageReq.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36")
		usagePage = urllib2.urlopen(usagePageReq)
		usagePage.read()

		""" Read data usage for main number """
		dataUsageData = urllib.urlencode({
			'codename': 'pc_basic',
			'detail': 1,
			'msisdn': "420%s" % (self._user)
		})
		dataUsageReq = urllib2.Request(self._dataUsageUrl)
		dataUsageReq.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
		dataUsageReq.add_header("Content-Length", len(dataUsageData))
		dataUsageReq.add_header("Referer", self._usageUrl)
		dataUsageReq.add_header("X-Requested-With", "XMLHttpRequest")
		dataUsageReq.add_header("Accept", "*/*")
		dataUsageReq.add_header("Origin", self._originUrl)
		dataUsageReq.add_header("Cookie", "hl=%s; persistent=%s; WSCSID=%s" % (self._lang, self._persistent, self._session))
		dataUsageReq.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36")
		usageDataPage = urllib2.urlopen(dataUsageReq, dataUsageData)
		self._getSession(usageDataPage.info())
		usageDataPageData = usageDataPage.read()

		# Used: <strong>5 818,71&nbsp;MB</strong>
		usedDataRe = re.findall(u'Used: <strong>([0-9 ,]*)&nbsp;MB<\/strong>', usageDataPageData.decode('utf-8'))
		usedData = float(usedDataRe[0].replace(" ", "").replace(",", "."))

		# Remains in CZ <strong class="nowrap">97 605,29&nbsp;MB</strong>
		remainsDataRe = re.findall(u'Remains in CZ <strong class="nowrap">([0-9 ,]*)&nbsp;MB</strong>', usageDataPageData.decode('utf-8'))
		remainsData = float(remainsDataRe[0].replace(" ", "").replace(",", "."))

		""" Parse data usage page """
		return {'used': usedData, 'remain': remainsData}

	""" Login to Vodafone.cz """
	def login(self):
		token = self._getLoginPageToken()
		return self._postLoginCredentials(token)

	""" Get current spending """
	def getCurrentSpending(self):
		return self._getCurrentSpending()

	""" Get data usage """
	def getDataUsage(self):
		return self._getDataUsage()
