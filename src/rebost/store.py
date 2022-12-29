#!/usr/bin/env python3
import sys,os,time
import zlib
import subprocess
import json
import signal
import ast
import dbus,dbus.exceptions
import logging
import getpass

class client():
	def __init__(self,*args,**kwargs):
		self.dbg=False
		logging.basicConfig(format='%(message)s')
		self.user=''
		self.n4dkey=''
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
		try:
			rebost=bus.get_object("net.lliurex.rebost","/net/lliurex/rebost")
			self.rebost=dbus.Interface(rebost,"net.lliurex.rebost")
		except Exception as e:
			print("Could not connect to bus: %s\nAborting"%e)
			print("2nd attempt...")
			time.sleep(2)
			try:
				rebost=bus.get_object("net.lliurex.rebost","/net/lliurex/rebost")
				self.rebost=dbus.Interface(rebost,"net.lliurex.rebost")
			except:
				print("Could not reconnect to bus: %s\nAborting"%e)
				sys.exit(1)
	
	def execute(self,action,args='',extraParms=''):
		self._testConnection()
		procId=0
		if isinstance(args,str):
			args=[args]
		if args:
			for arg in args:
				if ":" in arg:
					package=arg.split(":")
					extraParms=package[-1]
					package=package.pop(0)
				else:
					package=arg
				try:
				#	if "-" in package:
				#		package=package.replace("-","_")

					if action=='install':
						procId=self.installApp(package,extraParms)
					elif action=='remove':
						procId=self.removeApp(package,extraParms)
					elif action=='test':
						procId=self.testInstall(package,extraParms)
					elif action=='remote_install':
						procId=self.remoteInstall(package,extraParms)
					elif action=='search':
						procId=self.searchApp(package)
					elif action=='getCategories':
						procId=self.getCategories()
					elif action=='list':
						procId=self.getAppsInCategory(package,extraParms)
					elif action=='show':
						procId=self.showApp(package)
					elif action=='enableGui':
						procId=self.enableGui(arg)
				except dbus.exceptions.DBusException as e:
					desc=e.get_dbus_name()
					if desc!="org.freedesktop.DBus.Error.AccessDenied":
						print("Dbus Error: %s"%e)
					procId=0
				except Exception as e:
					procId=0
					print("Err: %s"%e)
				finally:
					self.rebost=None
		else:
			try:
				if action=='update':
					procId=self.rebost.update()
				#if action=='fullupdate':
				#	procId=self.rebost.fullUpdate()
				elif action=='load':
					procId=self.rebost.load(package,extraParms)
			except dbus.exceptions.DBusException as e:
				procId=0
				print("Dbus Error: %s"%e)
			except Exception as e:
				procId=0
				print("Err: %s"%e)
			finally:
				self.rebost=None
		if isinstance(procId,str)==False:
			procId=str(procId)
		return(procId)

	def _testConnection(self):
		if self.n4dkey=='':
			self.n4dkey=self._getN4dKey()
		self._connect()
	#def _testConnection

	def getCategories(self):
		self._testConnection()
		categories=self.rebost.getCategories()
		return(str(categories))
	#def getCategories(self):

	def getAppsInCategory(self,category,limit=0):
		self._testConnection()
		bappsInCategory=0
		appsInCategory={}
		if isinstance(limit,int)==False:
			limit=0
		if limit>0:
			bappsInCategory=self.rebost.search_by_category_limit(category,limit)
		else:
			bappsInCategory=self.rebost.search_by_category(category)

		if bappsInCategory:
			appsInCategory=zlib.decompress(bytes(bappsInCategory)).decode()
		return(str(appsInCategory))
	#def getAppsInCategory

	def getInstalledApps(self):
		self._testConnection()
		installedApps=self.rebost.getInstalledApps()
		return(str(installedApps))
	#def getInstalledApps

	def getUpgradableApps(self,user=''):
		self._testConnection()
		if user=='':
			user=self.user
		upgradableApps=self.rebost.getUpgradableApps(user)
		return(str(upgradableApps))
	#def getInstalledApps

	def searchApp(self,app):
		self._testConnection()
		bapps=0
		apps={}
		bapps=self.rebost.search(app)
		if bapps:
			apps=zlib.decompress(bytes(bapps)).decode()
		return(str(apps))
	#def searchApp

	def showApp(self,package):
		self._testConnection()
		package=self.rebost.show(package,self.user)
		return(str(package))
	#def searchApp

	def getAppStatus(self,package,bundle):
		self._testConnection()
		package=self.testInstall(package,bundle,self.user)
		try:
			package=json.loads(package)[0]
		except:
			package={}
		epiFile=package.get('script','')
		status="1"
		if os.path.isfile(epiFile):
			status=self.getEpiPkgStatus(epiFile)
			#os.remove(epiFile)
		return(status)

	def installApp(self,package,bundle):
		self._testConnection()
		if bundle=="zomando":
			zmdPath=os.path.join("/usr/share/zero-center/zmds","{}.zmd".format(package))
			if os.path.isfile(zmdPath)==True:
				installResult=subprocess.run([zmdPath]).returncode
		else:
			installResult=self.rebost.install(package,bundle,self.user,self.n4dkey)
		return(str(installResult))
	#def installApp

	def testInstall(self,package,bundle,user=''):
		self._testConnection()
		if user=='':
			user=self.user
		try:
			testResult=self.rebost.test(package,bundle,user)
		except Exception as e:
			testResult=[("-1",{'pid':"{}",'package':package,'done':1,'status':'','msg':'User has no  permissions'})]
		return(str(testResult))
	#def testInstall

	def removeApp(self,package,bundle):
		self._testConnection()
		if bundle=="zomando":
			bundle="package"
		removeResult=self.rebost.remove(package,bundle,self.user,self.n4dkey)
		return(str(removeResult))
	#def removeApp

	def commitInstall(self,package,bundle,state):
		self._testConnection()
		commitResult=self.rebost.commitInstall(package,bundle,state)
		return(str(commitResult))
	#def commitInstall

	def getEpiPkgStatus(self,epiScript):
		self._testConnection()
		pkgStatus=self.rebost.getEpiPkgStatus(epiScript)
		return(str(pkgStatus))
	#def getEpiPkgStatus

	def remoteInstall(self,package,bundle,user=''):
		self._testConnection()
		if user=='':
			user=self.user
		remoteResult=self.rebost.remote_install(package,bundle,user)
		return(str(remoteResult))
	#def commitInstall

	def enableGui(self,enable):
		self._testConnection()
		enable=False
		if isinstance(enable,str):
			if enable.lower()!="false":
				enable=True
		elif isinstance(enable,int)==True:
			enable=bool(enable)
		#enabled=self.rebost.enableGui(enable)
		enabled="true"
		return(str(enabled))
	#def enableGui(self,enable):

	def forceUpdate(self,procId=0):
		self._connect()
		return({})
		bus=self.rebost.fullUpdate()
		progressDict=json.loads(bus)
		self.rebost=None
		return(progressDict)

	def update(self,force=False):
		self._testConnection()
		updateResult={}
		try:
			updateResult=self.rebost.update(force)
		except Exception as e:
			time.sleep(10)
			print(e)
		return(str(updateResult))

	def restart(self):
		self._testConnection()
		restartResult=self.rebost.restart()
		return(str(restartResult))

	def getProgress(self,procId=0):
		self._connect()
		bus=self.rebost.getResults()
		progressDict=json.loads(bus)
		self.rebost=None
		return(progressDict)
	
	def getResults(self,procId=0):
		self._connect()
		bus=self.rebost.getResults()
		results=json.loads(bus)
		self.rebost=None
		return(results)
	
	def getPlugins(self):
		pass
	
	def _getN4dKey(self):
		n4dkey=''
		try:
			with open('/etc/n4d/key') as file_data:
				n4dkey = file_data.readlines()[0].strip()
		except:
			pass
		return(n4dkey)
