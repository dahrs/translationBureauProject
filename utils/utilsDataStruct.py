#!/usr/bin/python
#-*- coding:utf-8 -*-  



##################################################################################
#DICTS
##################################################################################

def mergeDictsAddValues(dictA, dictB):
	'''
	give 2 dicts, it merges them and 
	adds the values
	and returns the first dict updated
	'''
	tempDict = dictB.copy()
	for keyB, valueB in dictB.items():
		if keyB not in dictA:
			dictA[keyB] = valueB
		else:
			dictA[keyB] = dictA[keyB] + valueB
	return dictA
