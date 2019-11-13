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


def generateCmd(nHours=1, machineList=None):
    if machineList is None:
        machineList = [u'octal06', u'octal03', u'octal04', u'octal05', u'octal07', u'octal17', u'ilar01', u'ilar02',
                        u'bart2', u'bart3', u'bart4', u'bart5', u'bart6', u'bart7', u'bart10',  u'kakia1',
                        u'kakia2', u'kakib2', u'kakic2', u'kakid1', u'kakid2', u'kakie2', u'kakif1', u'kakif2']
    schedule = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/heurSchedule.json'
    scheduleDict = utilsOs.openJsonFileAsDict(schedule)
    scheduleIdList = list(scheduleDict.keys())
    commandLns = []
    for machine in machineList:
        commandLns.append(u'#########################################################')
        commandLns.append(u'ssh {0}'.format(machine))
        commandLns.append(u'source .bashrc')
        commandLns.append(u'cd ~/Documents/workRALI/004tradBureau')
        simultaneousRuns = 4
        # if the machine is high end, run more
        if machine in [u'bart2', u'bart3', u'bart4', u'bart5', u'bart6', u'bart7', u'bart10', u'kakid2']:
            simultaneousRuns = 6
        if machine in [u'kakia1', u'kakia2', u'kakic2', u'kakid1', u'kakie2', u'kakif1', u'kakif2']:
            simultaneousRuns = 8
        for n in range(simultaneousRuns):
            commandLns.append(u'python b009applyHeuristicsOnMC.py -ap True -w {0} -li {1} &'.format(n*20, u'*'.join(scheduleIdList[:nHours])))
            scheduleIdList = [nId for nId in scheduleIdList if nId not in scheduleIdList[:nHours]]
        # commandLns[-1] = commandLns[-1].replace(u' &', u'')
        commandLns.append(u'\nENDSSH\n')
    print(u'\n'.join(commandLns))