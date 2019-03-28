#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')

import b000path


def getLines(btFilePathsList, verbose=False):
    total = 0
    flagDict = {}
    langDict = {}
    domainDict = {}
    for index, filePath in enumerate(btFilePathsList):
        if index % 100000 == 0: #########################
            print(index) ######################
        fSplit = filePath.split(u'/')
        #open the score file and count
        with open(filePath) as file:
            # get to the actual data line
            line = file.readline()
            while line:
                # populate the total dict
                total += 1
                # populate the flag dict
                flagDict = populateDict1(fSplit[-4], flagDict)
                # populate the domain dict
                domainDict = populateDict1(fSplit[-3], domainDict)
                # populate the lang dict
                langDict = populateDict1(fSplit[-2], langDict)
                # get next line
                line = file.readline()
    if verbose != False:
        print(11111111, 'Total Dict')
        print(total)
        print(22222222, 'Flag Dict')
        print(flagDict)
        print(33333333, 'Domain Dict')
        print(domainDict)
        print(44444444, 'Lang Dict')
        print(langDict)
    return total, flagDict, domainDict, langDict


def populateDict1(key, aDict={}):
    if key not in aDict:
        aDict[key] = 1
    else:
        aDict[key] += 1
    return aDict


def populateDict2(key, score, aDict={}):
    if key not in aDict:
        aDict[key] = {'0': 0, '1': 0}
        aDict[key][score] += 1
    else:
        aDict[key][score] += 1
    return aDict


def getScoreParallel(btFilePathsList, verbose=False):
    """ get the scores of the right paralel correspondence """
    totalDict = {}
    flagDict = {}
    langDict = {}
    domainDict = {}
    # instead of censing the files in the scores folders, we make sure there is one file in shiv's folder per
    # original tmx file
    for filePath in btFilePathsList:
        fSplit = filePath.split(u'/')
        scorePath = u'/u/bhardwas/bt/{0}/{1}/{2}/{3}.en'.format(fSplit[-4], fSplit[-3], fSplit[-2], fSplit[-1])
        #open the score file and count
        with open(scorePath) as scoreFile:
            # pass the header line
            line = scoreFile.readline()
            # get to the actual data line
            line = scoreFile.readline()
            while line:
                # get the score
                score = line.replace(u'\n', u'').split(u',')[-1]
                # populate the total dict
                totalDict = populateDict1(score)
                # populate the flag dict
                flagDict = populateDict2(fSplit[-4], score, flagDict)
                # populate the domain dict
                domainDict = populateDict2(fSplit[-3], score, domainDict)
                # populate the lang dict
                langDict = populateDict2(fSplit[-2], score, langDict)
                # get next line
                line = scoreFile.readline()
    if verbose != False:
        print(11111111, 'Total Dict')
        print(totalDict)
        print(22222222, 'Flag Dict')
        print(flagDict)
        print(33333333, 'Domain Dict')
        print(domainDict)
        print(44444444, 'Lang Dict')
        print(langDict)
    return totalDict, flagDict, domainDict, langDict


# get the paths to the bt files
btFilePathsList = b000path.getBtFilePaths(fileFormat='tmx')


# get the lines stats
getLines(btFilePathsList, True)

# get the scores of the right paralel correspondence
#getScoreParallel(btFilePathsList, True)