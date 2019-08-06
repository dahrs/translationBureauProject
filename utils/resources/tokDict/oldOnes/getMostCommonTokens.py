#!/usr/bin/python
#-*- coding:utf-8 -*-

import operator, json, codecs


def openJson(pathToFile):
	''''''
	with open(pathToFile, u'r', encoding=u'utf8') as openedFile:
		return json.load(openedFile)


def dumpListAsJson(aDict, pathOutputFile):
	''''''
	with codecs.open(pathOutputFile, u'wb', encoding=u'utf8') as dictFile:
		dictFile.write('')
		json.dump(aDict, dictFile)





wordCountDict = openJson(u'./frTok.json')

sortedKeysList = [ x[0] for x in sorted(wordCountDict.items(), key=operator.itemgetter(1), reverse=True)]

print(sortedKeysList[:5])


dumpListAsJson(sortedKeysList[:5000], pathOutputFile='./listOfMostCommon5000tok.json')

dumpListAsJson(sortedKeysList[:10000], pathOutputFile='./listOfMostCommon10000tok.json')

