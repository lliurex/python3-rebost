#!usr/bin/env python3
import sys,os,time
import zlib
import subprocess
import json
import signal
import ast
import dbus,dbus.exceptions
from _dbus_bindings import BUS_DAEMON_IFACE, BUS_DAEMON_NAME, BUS_DAEMON_PATH
import logging
import getpass

class client():
	def __init__(self,*args,**kwargs):
		self.dbg=True
		logging.basicConfig(format='%(message)s')
		self.user=''
		if kwargs:
			self.user=kwargs.get('user','')
		if self.user=='':
			self.user=getpass.getuser()
		if self.user=='root':
		#check that there's no sudo
			sudo_user=os.environ.get("SUDO_USER",'')
			if sudo_user:
				self.user=sudo_user
		self._debug("Selected user: {}".format(self.user))
		self.rebost=None

	def _debug(self,msg):
		if self.dbg:
			logging.warning("rebost: %s"%str(msg))
			print("rebostClient: {}".format(msg))
	#def _debug

	def _connect(self):
		try:
			bus=dbus.SystemBus()
		except Exception as e:
			print("Could not get session bus: %s\nAborting"%e)
			sys.exit(1)
		#Five attempts within 60sec
		current=int(time.time())
		end=current+60
		waitFor=1
		rebost=None
		while end>current:
			try:
				rebost=bus.get_object("net.lliurex.rebost","/net/lliurex/rebost")
				current=end+1
			except Exception as e:
				print("Could not connect to bus: {}\nAborting".format(e))
				print("2nd attempt...")
				time.sleep(waitFor)
				current=int(time.time())
				rebost=bus.get_object("net.lliurex.rebost","/net/lliurex/rebost")

		if rebost==None:
			print("Could not reconnect to bus: %s\nAborting"%e)
			sys.exit(1)
		self.rebost=dbus.Interface(rebost,"net.lliurex.rebost")
	#def _connect
	
	def _testConnection(self):
		self._connect()
	#def _testConnection

	def toggleLock(self):
		self._testConnection()
		config=self.rebost.toggleLock()
		return(config)
	#def toggleLock

	def getConfig(self):
		self._testConnection()
		config=self.rebost.getConfig()
		return(config)
	#def getConfig

	def getSupportedFormats(self):
		self._testConnection()
		formats=self.rebost.getSupportedFormats()
		return(formats)
	#def getSupportedFormats(

	def getFreedesktopCategories(self):
		self._testConnection()
		categories=self.rebost.getFreedesktopCategories()
		return(categories)
	#def getFreedesktopCategories(self):

	def getCategories(self):
		self._testConnection()
		categories=self.rebost.getCategories()
		return(categories)
	#def getCategories(self):

	def getAppsPerCategory(self):
		self._testConnection()
		apps=self.rebost.getAppsPerCategory()
		return(apps)
	#def getAppsPerCategory

	def getAppsInCategory(self,category,limit=0):
		self._testConnection()
		appsInCategory=self.rebost.getAppsInCategory(category)
		return(appsInCategory)
	#def getAppsInCategory

	def getAppsInstalled(self):
		self._testConnection()
		installedApps=self.rebost.getAppsInstalled()
		return(installedApps)
	#def getInstalledApps

	def getAppsInstalledPerCategory(self):
		apps=self.getAppsInstalled()
		installedApps={}
		categories=self.rebost.getFreedesktopCategories()
		for cat in categories:
			installedApps[cat]=[]
		apps=json.loads(self.rebost.getAppsInstalled())
		for app in apps:
			for cat in app["categories"]:
				if cat in installedApps.keys():
					installedApps[cat].append(app)
		return(installedApps)
	#def getAppsInstalledPerCategory

	def getUpgradableApps(self,user=''):
		self._testConnection()
		if user=='':
			user=self.user
		upgradableApps=self.rebost.getUpgradableApps(user)
		return(str(upgradableApps))
	#def getInstalledApps

	def getApps(self):
		self._testConnection()
		apps=self.rebost.getApps()
		return(apps)
	#def getInstalledApps

	def searchApp(self,app):
		self._testConnection()
		apps=self.rebost.search(app)
		return(apps)
	#def searchApp

	def searchAppByUrl(self,url):
		self._testConnection()
		apps=self.rebost.searchAppByUrl(url)
		return(apps)
	#def searchApp

	def showApp(self,package):
		self._testConnection()
		try:
			package=self.rebost.showApp(package)
		except Exception as e:
			print(e)
		return(package)
	#def searchApp

	def refreshApp(self,package):
		self._testConnection()
		try:
			package=self.rebost.refreshApp(package)
		except Exception as e:
			print(e)
		return(package)
	#def searchApp

	def setAppState(self,appId,state,bundle,temp=True):
		self._testConnection()
		try:
			if temp==False:
				package=self.rebost.setAppState(appId,state,bundle)
			else:
				package=self.rebost.setAppStateTmp(appId,state)
		except Exception as e:
			print(e)
		return(package)

	def export(self):
		self._testConnection()
		try:
			self.rebost.export("")
		except Exception as e:
			print(e)
		return("")
	#def searchApp

	def getExternalInstaller(self):
		self._testConnection()
		installer=""
		try:
			installer=self.rebost.getExternalInstaller()
		except Exception as e:
			print(e)
		return(installer)
	#def installPpp

	def remoteInstall(self,package,bundle,user=''): #PENDING (remote-installer)
		return()
		self._testConnection()
		if user=='':
			user=self.user
		remoteResult=self.rebost.remote_install(package,bundle,user)
		return(str(remoteResult))
	#def remoteInstall

	def lock(self):
		self._connect()
		result=self.rebost.lock()
		return(result)
	#def lock

	def unlock(self):
		self._connect()
		result=self.rebost.unlock()
		return(result)
	#def unlock
	
