#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# termiteOS
# Copyright (c) July 2018 Nacho Mas
'''
Test astronomy modules
'''
from __future__ import print_function
import time

def test_costellation():
        import termiteOS.astronomy.catCostellation as cat
        g=cat.costellation()
	b=g.costellationBounds()
	b=g.costellationFigures()
        UMAUMI=((122.12910149999999, 28.3038998), (343.51066649999996, 88.663887))
	b=g.getCostellationsLimits(['UMA','UMI'])
        assert(b==UMAUMI)
        costellations= ['AND', 'ANT', 'APS', 'AQR', 'AQL', 'ARA', 'ARI', 'AUR', 'BOO', 'CAE', 'CAM', 'CNC', 'CVN', 'CMA', 'CMI', 'CAP', 'CAR', 'CAS', 'CEN', 'CEP', 'CET', 'CHA', 'CIR', 'COL', 'COM', 'CRA', 'CRB', 'CRV', 'CRT', 'CRU', 'CYG', 'DEL', 'DOR', 'DRA', 'EQU', 'ERI', 'FOR', 'GEM', 'GRU', 'HER', 'HOR', 'HYA', 'HYI', 'IND', 'LAC', 'LEO', 'LMI', 'LEP', 'LIB', 'LUP', 'LYN', 'LYR', 'MEN', 'MIC', 'MON', 'MUS', 'NOR', 'OCT', 'OPH', 'ORI', 'PAV', 'PEG', 'PER', 'PHE', 'PIC', 'PSC', 'PSA', 'PUP', 'PYX', 'RET', 'SGE', 'SGR', 'SCO', 'SCL', 'SCT', 'SER1', 'SER2', 'SEX', 'TAU', 'TEL', 'TRI', 'TRA', 'TUC', 'UMA', 'UMI', 'VEL', 'VIR', 'VOL', 'VUL']
	b=g.getCostellations()
        assert(b==costellations)

def test_grids():
        import termiteOS.astronomy.catGrids as cat
        g=cat.grids()
        line={10: [(10, -10), (10, -9), (10, -8), (10, -7), (10, -6), (10, -5), (10, -4), (10, -3), (10, -2), (10, -1), (10, 0), (10, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (10, 8), (10, 9), (10, 10)]}
        b=g.lonLine(10,(-10,10))
        assert(b==line)

def test_cats():
        import termiteOS.astronomy.catLoadFits as cat
        g=cat.catLoadFits('BSC5')
	for c in g.catalogsDefinitions.keys():
		qq=cat.catLoadFits(c)
                print(c,qq.numrec,qq.coverage)

def test_tles():
        import termiteOS.astronomy.internetcatalogues as cat
        import ephem
	observer=ephem.city('Madrid')
	observer.date=ephem.Date('2018/07/06 20:00')
	i=cat.internetCatalogue()
	geo=i.geo('HISPASAT')
	geo.compute(observer)
	print(geo.ra,geo.dec)
