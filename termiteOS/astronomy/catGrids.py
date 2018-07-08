#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
from __future__ import print_function
import numpy as np

class grids:

	def latLine(self,lat,(lon0,lon1)=(0,360),step=1,name=''):
		#equal lat lines
		p=[]
		for lon in range (lon0,lon1+step,step):
			pp=(lon,lat)
			p.append(pp)
		s={}
		if name=='':
			name=lat
		s[name]=p
		return s

	def lonLine(self,lon,(lat0,lat1)=(-90,90),step=1,name=''):
		#equal lon lines
		p=[]
		for lat in range (lat0,lat1+step,step):
			pp=(lon,lat)
			p.append(pp)
		s={}
		if name=='':
			name=lon
		s[name]=p
		return s

	def grid(self,area=((0,-90),(360,90)),steps=(10,10)):
		((lon0,lat0),(lon1,lat1))=area		
		(steplon,steplat)=steps

		s={}
		p={}
		for lon in range (lon0,lon1+steplon,steplon):
			p[lon]=self.lonLine(lon,(lat0,lat1))[lon]
		s['lonLines']=p
		p={}
		for lat in range (lat0,lat1+steplat,steplat):
			p[lat]=self.latLine(lat,(lon0,lon1))[lat]
		s['latLines']=p
		return s
		

if __name__=='__main__':
	g=grids()
	print(g.lonLine(10,(-10,10)))


