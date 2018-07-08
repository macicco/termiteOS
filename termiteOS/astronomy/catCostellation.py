#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
from __future__ import print_function
import numpy as np
import os
path=os.path.dirname(__file__)
data_path=path+'/data/'
print(data_path)

class costellation:
	consZodiac=['ARI','TAU','GEM','CNC','LEO','VIR','LIB','SCO','SGR','CAP','AQR','PSC']
	consCircumpolar=['CEP','DRA','UMI','UMA','CAM','CAS','LYN']
	consEquatorial=['CMI','HYA','MON','ORI','TAU','CET','PSC','ARI','AQL','SER2','OPH','SER1','VIR','LEO','SEX']
	consGalactic=['CAS','CEP','CYG','PER','AUR','TAU','SER2','CAM','ORI','MON','CMA','PUP','VEL','CRU','SCO',\
			'SGR','SCT','AQL','VUL','SGE','NOR','CIR','CEN','CAR','ARA']
	def getCostellations(self):
		fi=open(data_path+'costellations_bound_20.dat')
		p=[]
		old_costellation=''
		for l in fi.readlines():
			ra_,dec_,costellation,dummy=l.split()
			if old_costellation=='':
				p.append(costellation)
				old_costellation=costellation
			if (old_costellation!=costellation):
				p.append(costellation)
			old_costellation=costellation
		fi.close()	
		return p
				

	def costellationBounds(self,costellation_list='all'):
	#Data from stellarium 0.8 sources
		#print costellation_list
		fi=open(data_path+'costellations_bound_20.dat')
		p={}
		old_costellation=''
		for l in fi.readlines():
			ra_,dec_,costellation,dummy=l.split()
			ra,dec=float(ra_)*15,float(dec_)
			pp=(ra,dec)
			if old_costellation=='':
				primer=pp
				p[costellation]=[]
				old_costellation=costellation
			if (old_costellation!=costellation):
				p[old_costellation].append(primer)
				primer=pp
				p[costellation]=[]

			p[costellation].append(pp)

			old_costellation=costellation
		fi.close()	
		if costellation_list=='all':
			return p
		else:
			for k in p.keys():
				if k not in costellation_list:
					del p[k]
		return p


	def costellationFigures(self,costellation_list='all'):
	#Data from stellarium 0.8 sources. ra/dec values. 
	#./data/constellationship.fab preprocessed
		import json
		p=json.load(open(data_path+'figures.json'))
		for k in p.keys():
			new_key=k.upper()
			p[new_key] = p.pop(k)
		if costellation_list=='all':
			return p
		else:
			for k in p.keys():
				if k not in costellation_list:
					del p[k]
		return p

	def getCostellationsLimits(self,costellation_list='all'):
		if costellation_list == 'all':
			return (0,-90),(360,90)
		bounds=self.costellationBounds()
		data=[]
		for k in costellation_list:
			d=bounds[k]
			data.extend(d)
		lons=map(lambda x:x[0],data)
		lats=map(lambda x:x[1],data)
		return (min(lons),min(lats)),(max(lons),max(lats))



if __name__=='__main__':
	g=costellation()
	b=g.costellationBounds()
	#print(b)
	b=g.costellationFigures()
	#print(b)
	print(g.getCostellationsLimits(['UMA','UMI']))
	print(g.getCostellations())

