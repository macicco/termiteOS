#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
from __future__ import print_function
import pyfits
import json
import numpy as np
from math import pi
import StringIO
import tempfile

import os
path=os.path.dirname(__file__)
data_path=path+'/data/'
print(data_path)


class catLoadFits:
	def __init__(self,conf,area=((0,0),(0,0)),jsonfile=data_path+'catLoadFits.json'):
		self.catalogsDefinitions=json.load(open(jsonfile))
		if conf in self.catalogsDefinitions.keys():
			self.conf=self.catalogsDefinitions[conf]
			f=self.conf['fits']		
		else:
			print (conf+" No Found")
			print ("Available catalogues:",self.catalogsDefinitions.keys())

		self.catname=conf
		f=self.conf['fits']
		#print(f['filename'][:9])
		self.loadFits(data_path+f['filename'],f['HDU'])
		self.fieldsDefinition()


	def loadFits(self,filename,table):
		hdulist = pyfits.open(filename)
		hdulist[table].verify('silentfix')
		self.data=hdulist[table].data
		self.fits_dt=self.data.dtype.descr


	def findtype(self,varname):
		i=self.data.names.index(varname)
		fmt=str(self.data.formats[i])
		print(fmt)
		a=self.data.formats[i][0]
		aa=self.data.formats[i][-1]
		dt=[item for item in self.fits_dt if varname in item] 
		if fmt=='char':
			return 'S50'		
		if fmt=='long' or fmt=='int':
			return 'i8'		
		if fmt=='float':
			return 'f8'		
		if fmt=='double':
			return 'f16'
		if a=='A':
			return dt[0][1]
		if a=='F':
			return "f8"
		if a=='D' or a=='E':
			return "f16"
		if a=='I':
			return "i8"
		if aa=='A':
			return "S"+fmt[0:-1]
		return 'S50'		

	def fieldsDefinition(self):
		if 'RAfields' in self.conf.keys():
			RAfields=self.conf['RAfields']
			DECfields=self.conf['DECfields']
			rad=self.conf['rad']
			fieldsname='RA,DEC'
			fieldsformat = 'f8, f8'.encode("ascii")
			if len(RAfields)==1:
				RA=self.data[RAfields[0]]		
			elif len(RAfields)==2:
				RAh,RAm=RAfields
				RA=(self.data[RAh]+self.data[RAm]/60.)*15
			else:
				RAh,RAm,RAs=RAfields
				RA=(self.data[RAh]+self.data[RAm]/60.+self.data[RAs]/3600.)*15
			if len(DECfields)==1:
				DEC=self.data[DECfields[0]]		
			elif len(DECfields)==3:
				DEsign,DEd,DEm=DECfields
				DEC=np.where(self.data[DEsign]=='-',-1,1)*(self.data[DEd]+self.data[DEm]/60.)
			else:
				DEsign,DEd,DEm,DEs=DECfields
				DEC=np.where(self.data[DEsign]=='-',-1,1)*(self.data[DEd]+self.data[DEm]/60.+self.data[DEs]/3600.)

			if rad:
				RA=RA*180/pi
				DEC=DEC*180/pi

			RAmax=round(max(RA),2)
			RAmin=round(min(RA),2)
			DECmax=round(max(DEC),2)
			DECmin=round(min(DEC),2)
			self.coverage=((RAmin,DECmin),(RAmax,DECmax))
			self.numrec=RA.size
			d=np.vstack((RA,DEC))
			dt=[('RA','f8'),('DEC','f8')]
		else:
			fieldsname=''
			fieldsformat = ''
			dt=[]

		self.prop=self.conf['prop']
		for key,p in self.prop.iteritems():
			datatype=self.data[p].dtype.descr[0][1]
			if len(p)!=0:
				dd=np.array(self.data[p])

				dt.append((str(key),datatype))
				try:
					d=np.vstack((d,dd))
					fieldsname += ',' + key
					fieldsformat += ','+datatype

				except:
					fieldsname = key
					fieldsformat = datatype
					d=dd
		fnames=fieldsname.encode("ascii")
		fformat=fieldsformat.encode("ascii")

		self.d=np.core.records.fromarrays(d,names=fnames,formats = fformat)

		if 'name' in self.prop:
			self.IDs=map(lambda x:x['name'],self.d)
		else:
			self.IDs=False

	def sanitize(self,array):
		dt=array.dtype
		if array.dtype.descr[0][1]=='<i4':
			d=['1' for x in array]
			print("SANITIZE",array.dtype.descr)
			return np.array(d,dtype=dt)
		return array
		
	def search(self,name):
		if not self.IDs:
			print ("No field \'name\' in prop dictionary")
			return None
		try:
			s=self.d[self.IDs.index(name)]
		except:
			s=None
		return s

	def filter(self,((ra0,dec0),(ra1,dec1))=((0,-90),(360,90)),mag=25):
		dt=self.d.dtype
		s=filter(lambda x:(x['RA']>ra0 and x['RA']<ra1) and  (x['DEC']>dec0 and x['DEC']<dec1 \
			 and x['mag']<mag),self.d)
		s=np.array(s,dtype=dt)
		return s


	def list(self):
		for c in self.catalogsDefinitions.keys():
			if c==self.catname:
				print ("*",c)
			else:
				print (" ",c)
	def info(self):
		print ("CATALOG NAME:\t",self.catname)
		print ("COVERAGE:\t",self.coverage)
		print ("NUM RECORDS:\t",self.numrec)
		VARS=''
		havemag=False
		for v in self.prop.keys():
			VARS += v+' '
			if v=='mag':
				havemag=True
		print ("ORIGINAL VARIABLES:",self.data.names)
		print ("SELECTED VARIABLES:",VARS)
		print ("FORMATS:",self.d.dtype.descr)
		if havemag:
			print("MAG max:",min(self.d['mag']),"min:",max(self.d['mag']))

if __name__=='__main__':
	q=catLoadFits('BSC5')
	for c in q.catalogsDefinitions.keys():
		#print('==================',c,'==================')
		qq=catLoadFits(c)
		#print(qq.info())
                print(c,qq.numrec,qq.coverage)


