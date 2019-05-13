#!/usr/bin/python
# -*- coding:utf-8 -*-

from random import randint

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsString


def getRandomIntNeverseenBefore(listLength, dejaVus=[]):
    """  """
    # If we have more in dejavu than what we can produce
    if len(dejaVus) >= listLength:
        return None
    # get a random int
    r = randint(0, listLength)
    while r in dejaVus:
        r = randint(0, listLength)
    return r


def randomlySelectNDocsFromPath(folderPath, n=100):
    """ given a folder path, return a list of n randomly selected file paths """
    dejaVus = set()
    randomSelected = set()
    # get all the tmx files in the folder
    wholeFolderContent = utilsOs.goDeepGetFiles(folderPath, format=u'.tmx')
    # if there are less files in the folder path as in n then return them all
    if len(wholeFolderContent) <= n:
        return wholeFolderContent
    # get n randomly selected files from the whole
    for e in range(n):
        index = getRandomIntNeverseenBefore(len(wholeFolderContent), dejaVus)
        # add to dejavus and to the random selected list
        dejaVus.add(index)
        randomSelected.add(wholeFolderContent[index])
    # get the domain
    if folderPath[-1] == u'/' :
        domain = folderPath[:-1].split(u'/')[-1]
    elif u'.' in folderPath.split(u'/')[-1]:
        path = folderPath.replace(u'/{0}'.format(folderPath.split(u'/')[-1]), u'')
        domain = path.split(u'/')[-1]
    else:
        domain = folderPath.split(u'/')[-1]
    # dump the set
    utilsOs.dumpDictToJsonFile(list(randomSelected), pathOutputFile='./randomSelected{0}{1}.json'.format(n, domain), overwrite=True)
    return randomSelected


def makeLocalFolderPaths(listOfFilePaths):
    """ given a list of file paths, creates the equivalent in the local path """
    for filePath in listOfFilePaths:
        localFilePath = filePath.replace(u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/', u'./002manuallyAnnotated/')
        localFileList = localFilePath.split(u'/')
        folderPath = localFilePath.replace(localFileList[-1], u'')
        utilsOs.createEmptyFolder(folderPath)
