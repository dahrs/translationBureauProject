#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys, argparse, time, json
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsString
import b000path
from b003heuristics import *
from tqdm import tqdm


parser = argparse.ArgumentParser()

parser.add_argument(u'-c', u'--corpus', type=str,
                    default=u'all',
                    help=u'corpus where to apply the heuristic : ALIGNMENT-QUALITY, MISALIGNED, QUALITY, NOT-FLAGGED')
parser.add_argument(u'-heur', u'--heuristic', type=str,
                    default=u'all',
                    help=u'corpus where to apply the heuristic')
parser.add_argument(u'-n', u'--nhours', type=int,
                    default=12,
                    help=u'how many hours to apply the heuristics and dumpt the scores with the not-flagged corpus')
parser.add_argument(u'-ap', u'--apply', type=bool,
                    default=False,
                    help=u'applies or not the heuristics')
parser.add_argument(u'-li', u'--listIds', type=str,
                    default=u'octal06',
                    help=u'list of the ids where we must apply the heuristics for the no-flagged corpus')
parser.add_argument(u'-w', u'--wait', type=int,
                    default=0,
                    help=u'time to wait before launching the heuristics')
args = parser.parse_args()


def getRightCorpus(corpusString):
    if corpusString == u'all':
        corpus = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']
    elif corpusString == u'problematic' or args.corpus == u'probl':
        corpus = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY']
    else:
        corpus = [corpusString]
    return corpus


def getRightHeuristic(heuristicString):
    if heuristicString == u'all':
        corpus = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', u'strBcks']
    else:
        corpus = heuristicString.split(u'*')
    return corpus


def getFilePathsLists(folderPaths=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']):
    """  """
    finalList = []
    for folder in folderPaths:
        refPathsList = b000path.getBtFilePaths(folders=[folder], fileFormat=u'tmx')
        finalList += refPathsList
    return finalList


def getLines(i, enLinesList, frLinesList, tmxPath):
    enLn = enLinesList[i]
    frLn = frLinesList[i]
    srcLn = enLn if u'en-fr' in tmxPath else frLn
    trgtLn = frLn if u'en-fr' in tmxPath else enLn
    return srcLn, trgtLn, enLn, frLn


def getFlag(tmxPath):
    for flag in [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']:
        if flag in tmxPath:
            return flag


def getLnToWrite(heurName, srcLn, trgtLn, enLn, frLn,
                 placeInDocument=None, starbucksExprDict=None, starbucksWordDict=None):
    # nb match heuristic
    if heurName == u'nb':
        score, totalIntersect, totalSrc, totalTrgt = nbMismatch(srcLn, trgtLn, includeNumberNames=False, addInfo=True)
        scAb, ttInterAb, ttSrcAb, ttTrgtAb = nbMismatch(srcLn, trgtLn, includeNumberNames=True, addInfo=True)
        scAb = u'na' if scAb is None else scAb
    # cognate match heuristic
    elif heurName == u'cog':
        score, totalIntersect, totalSrc, totalTrgt = cognateCoincidence(srcLn, trgtLn, addInfo=True)
    # tok length heuristic
    elif heurName == u'len':
        score, totalIntersect, totalSrc, totalTrgt = compareLengths(srcLn, trgtLn, addInfo=True, onlyLongSentOfNPlusLen=10)
        scCh, ttInterCh, ttSrcCh, ttTrgtCh = compareLengths(srcLn, trgtLn, useCharInsteadOfTokens=True, addInfo=True)
        scCh = u'na' if scCh is None else scCh
    # faux amis heuristic
    elif heurName == u'fa':
        score, totalIntersect, totalSrc, totalTrgt = fauxAmis(enLn, frLn, addInfo=True)
    # ion suffix heuristic
    elif heurName == u'ion':
        score, totalSrc, totalTrgt = ionSuffixMismatch(srcLn, trgtLn, addInfo=True)
    # stop words heuristic
    elif heurName == u'sw':
        score, totalSrc, totalTrgt = stopWordsMismatch(enLn, frLn, addInfo=True)
    # spelling check heuristic
    elif heurName == u'spell':
        score, totalScSrc, totalScTrgt, totalSrc, totalTrgt = spellingCheck(enLn, frLn, addInfo=True)
    # url and folder paths detector heuristic
    elif heurName == u'url':
        score, totalUrlsSrc, totalUrlsTrgt, totalSrc, totalTrgt = urlMismatch(srcLn, trgtLn, addInfo=True)
    # monolinguistic presence heuristic
    elif heurName == u'mono':
        score, totalSrc, totalTrgt = monoling(srcLn, trgtLn, addInfo=True)
    # content table heuristic
    elif heurName == u'tabl':
        score, totalScSrc, totalScTrgt, totalSrc, totalTrgt = tableOfContentsMismatch(srcLn, trgtLn, addInfo=True)
    # starbucks word by word translation
    elif heurName == u'strBcks':
        score, totalSrc, totalTrgt = starbucksTranslationMismatch(enLn, frLn, addInfo=True,
                                                                  starbucksExprDict=starbucksExprDict,
                                                                  starbucksWordDict=starbucksWordDict)
    else:
        raise TypeError('wrong heuristic code name given in the argument')
    # get the silence
    score = u'na' if score is None else score
    # dump to files
    if heurName == u'nb':
        return u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n'.format(score, scAb, totalIntersect, totalSrc, totalTrgt,
                                                               ttInterAb, ttSrcAb, ttTrgtAb)
    elif heurName == u'len':
        return (u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n'.format(score, scCh, totalSrc,
                                                                 totalTrgt, ttSrcCh, ttTrgtCh))
    elif heurName in [u'spell', u'tabl']:
        return u'{0}\t{1}\t{2}\t{3}\t{4}\n'.format(score, totalScSrc, totalScTrgt, totalSrc, totalTrgt)
    elif heurName == u'url':
        return u'{0}\t{1}\t{2}\t{3}\t{4}\n'.format(score, totalUrlsSrc, totalUrlsTrgt, totalSrc, totalTrgt)
    elif heurName in [u'mono', u'sw', u'ion', u'strBcks']:
        return u'{0}\t{1}\t{2}\n'.format(score, totalSrc, totalTrgt)
    else:
        return u'{0}\t{1}\t{2}\t{3}\n'.format(score, totalIntersect, totalSrc, totalTrgt)


def applyHeuristicOnCorpus(corpus=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY'],
                           heuristic=[u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', u'strBcks']):
    """ given a corpus and heuristic indication, it applies the heuristic to that corpus and dumps the result """
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    filePathList = getFilePathsLists(corpus)
    starbucksExprDict, starbucksWordDict = utilsString.openEn2FrStarbucksDict()
    for tmxFilePath in tqdm(filePathList):
        flag = getFlag(tmxFilePath)
        # get the list of lines
        with open(u'{0}.en'.format(tmxFilePath)) as enFile:
            enLines = enFile.readlines()
        with open(u'{0}.fr'.format(tmxFilePath)) as frFile:
            frLines = frFile.readlines()
        # get each line
        for i in range(len(enLines)):
            srcLn, trgtLn, enLn, frLn = getLines(i, enLines, frLines, tmxFilePath)
            outputRefPath = u'{0}{1}/reference.tsv'.format(out, flag)
            with open(outputRefPath, u'a') as refFile:
                # apply the heuristics
                for heurName in heuristic:
                    # make the folder
                    utilsOs.createEmptyFolder(u'{0}{1}/{2}/'.format(out, flag, heurName))
                    # make the output files
                    outputScorePath = u'{0}{1}/{2}/score.tsv'.format(out, flag, heurName)
                    with open(outputScorePath, u'a') as scoreFile:
                        scoreFile.write(getLnToWrite(heurName, srcLn, trgtLn, enLn, frLn,
                                                     placeInDocument=float(i)/float(len(enLines)),
                                                     starbucksExprDict=starbucksExprDict,
                                                     starbucksWordDict=starbucksWordDict))
                # dump to ref file
                refFile.write(u'{0}\t{1}\n'.format(b000path.anonymizePath(tmxFilePath), i))
    return None


def saveNotFlaggedList():
    # save the files path list in an external file
    filePathList = getFilePathsLists([u'NOT-FLAGGED'])
    filePathList = [b000path.anonymizePath(p) for p in filePathList]
    utilsOs.dumpRawLines(filePathList,
                     u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/files.paths')
    return None


def getSubsetOfFiles(filesIndexes):
    subSet = []
    indexes = []
    ci = 0
    with open(u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/files.paths') as setFile:
        ln = setFile.readline().replace(u'\n', u'')
        while ln:
            if ci in filesIndexes:
                subSet.append(ln)
                indexes.append(ci)
            # next line
            ln = setFile.readline().replace(u'\n', u'')
            ci += 1
    return subSet, indexes


def rewriteFileIfExists(path):
    # remove the file if it already exists
    if utilsOs.theFileExists(path) is True:
        with open(path, u'w') as file:
            file.write(u'')


def applyHeuristicsOnNotFlaggedCorpus(filesIndexes, launchId, deletePrevious=False,
                                      heuristicsList=[u'nb', u'cog', u'len', u'fa', u'ion', u'sw',
                                                      u'spell', u'url', u'mono', u'tabl', u'strBcks']):
    """ given a corpus and heuristic indication, it applies the heuristic to that corpus and dumps the result """
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/{0}/'.format(launchId)
    starbucksExprDict, starbucksWordDict = utilsString.openEn2FrStarbucksDict()
    # make the folder
    utilsOs.createEmptyFolder(out)
    # reference file
    outputRefPath = u'{0}reference.tsv'.format(out)
    # open the reference file
    if utilsOs.theFileExists(outputRefPath) is not True:
        refFile = open(outputRefPath, u'a')
        filePathList, subsetIndexes = getSubsetOfFiles(filesIndexes)
    # if it already exists, then use that list
    else:
        with open(outputRefPath) as existingRefFile:
            tempPathList = [refLn.split(u'\t')[0] for refLn in existingRefFile.readlines()]
            filePathList = []
            for refPath in tempPathList:
                if refPath not in filePathList:
                    filePathList.append(refPath)
    # for each tmx file
    for indexTmx, tmxFilePath in tqdm(enumerate(filePathList)):
        tmxFilePath = b000path.desAnonymizePath(tmxFilePath)
        fileNotFound = False
        # get the list of lines
        try:
            with open(u'{0}.en'.format(tmxFilePath)) as enFile:
                enLines = enFile.readlines()
            with open(u'{0}.fr'.format(tmxFilePath)) as frFile:
                frLines = frFile.readlines()
        except FileNotFoundError:
            print(u'FILE NOT FOUND IN : {0}'.format(tmxFilePath))
            fileNotFound = True
        if fileNotFound is False:
            # get each line
            for i in range(len(enLines)):
                srcLn, trgtLn, enLn, frLn = getLines(i, enLines, frLines, tmxFilePath)

                # # erase content of file if it already exists
                # rewriteFileIfExists(outputRefPath)

                # apply the heuristics
                for heurName in heuristicsList:
                    heurFolder = u'{0}{1}/'.format(out, heurName)
                    # delete the contents of the previous folder if needed
                    if deletePrevious != False:
                        try:
                            utilsOs.removeFolderAndContent(heurFolder)
                        except FileNotFoundError:
                            pass
                    # make the folder
                    utilsOs.createEmptyFolder(heurFolder)
                    # make the output files
                    outputScorePath = u'{0}score.tsv'.format(heurFolder)
                    # erase content of file if it already exists
                    rewriteFileIfExists(outputScorePath)
                    # add the scores to the files
                    with open(outputScorePath, u'a') as scoreFile:
                        scoreFile.write(getLnToWrite(heurName, srcLn, trgtLn, enLn, frLn,
                                                     placeInDocument=float(i)/float(len(enLines)),
                                                     starbucksExprDict=starbucksExprDict,
                                                     starbucksWordDict=starbucksWordDict))
                # write the ref line if it doesn't already exists
                if utilsOs.theFileExists(outputRefPath) is not True:
                    refFile.write(u'{0}\t{1}\n'.format(b000path.anonymizePath(tmxFilePath), i))
    if utilsOs.theFileExists(outputRefPath) is not True:
        refFile.close()
    return None


def makeHourlyIndexDict():
    folderPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/'
    with open(u'{0}files.paths'.format(folderPath)) as pathsFile:
        nbPaths = len(pathsFile.readlines())
    id = 0
    lastIdx = 0
    aDict = {}
    for idx in range(0, nbPaths, 600):  # range(364949, nbPaths, 600)
        aDict[id] = list(range(lastIdx, idx))
        lastIdx = idx
        id += 1
    aDict[id] = list(range(lastIdx, 394949))
    schedule = u'{0}heurSchedule.json'.format(folderPath)
    utilsOs.dumpDictToJsonFile(aDict, pathOutputFile=schedule, overwrite=True)


def applyOnNotFlaggedForNHours(n=1):
    schedule = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/heurSchedule.json'
    scheduleDict = utilsOs.openJsonFileAsDict(schedule)
    # apply for n hours
    for nId in list(scheduleDict.keys()[:n]):
        indexesToApply = scheduleDict[nId]
        applyHeuristicsOnNotFlaggedCorpus(indexesToApply, nId)
        # remove from the dict once we dump the scores
        del scheduleDict[nId]
    # save the remaining schedule dict
    utilsOs.dumpDictToJsonFile(scheduleDict, pathOutputFile=schedule, overwrite=True)


def applyOnSpecificId(idList, deletePrevious=False):
    schedule = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/heurSchedule.json'
    while True:
        try:
            scheduleDict = utilsOs.openJsonFileAsDict(schedule)
            break
        except json.decoder.JSONDecodeError:
            print(u'Try again to access the json. {0}'.format(idList[0]))
            time.sleep(7)
    for nId in idList:
        try:
            indexesToApply = scheduleDict[nId]
            # apply
            applyHeuristicsOnNotFlaggedCorpus(indexesToApply, nId, deletePrevious,
                                          heuristicsList=[u'nb', u'cog', u'len', u'fa', u'url', u'tabl', u'strBcks'])

            ######################################## TEST not to save the progress
            # # reopen the dict in case it changed since last time
            # for x in range(20):
            #     try:
            #         scheduleDict = utilsOs.openJsonFileAsDict(schedule)
            #         break
            #     except json.decoder.JSONDecodeError:
            #         time.sleep(7)
            # # remove from the dict once we dump the scores
            # del scheduleDict[nId]
            # # save the remaining schedule dict
            # utilsOs.dumpDictToJsonFile(scheduleDict, pathOutputFile=schedule, overwrite=True)

        except KeyError:
            print('ATTENTION: KEYERROR with id {0} #####'.format(nId))
    print(u'FINISHED {0}...'.format(idList[0]))


def generateCmd(nHours=1, machineList=None):
    if machineList is None:
        machineList = [u'octal06', u'octal03', u'octal04', u'octal05', u'octal07', u'octal17', u'ilar01', u'ilar02',
                        u'bart2', u'bart3', u'bart4', u'bart5', u'bart6', u'bart7', u'bart10',  u'kakia1',
                        u'kakia2', u'kakib1', u'kakib2', u'kakic1', u'kakic2', u'kakid1', u'kakid2', u'kakie1',
                        u'kakie2', u'kakif1', u'kakif2']
    schedule = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/heurSchedule.json'
    scheduleDict = utilsOs.openJsonFileAsDict(schedule)
    scheduleIdList = list(scheduleDict.keys())
    commandLns = []
    for machine in machineList:
        commandLns.append(u'#########################################################')
        commandLns.append(u'ssh {0}'.format(machine))
        commandLns.append(u'source .bashrc')
        commandLns.append(u'cd ~/Documents/workRALI/004tradBureau')
        for n in range(4):
            commandLns.append(u'python b009applyHeuristicsOnMC.py -ap True -w {0} -li {1} &'.format(n*20, u'*'.join(scheduleIdList[:nHours])))
            scheduleIdList = [nId for nId in scheduleIdList if nId not in scheduleIdList[:nHours]]
        # commandLns[-1] = commandLns[-1].replace(u' &', u'')
        commandLns.append(u'\nENDSSH\n')
    print(u'\n'.join(commandLns))


def joinNotFlaggedFolder(notFlaggedPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/'):
    """ given a path to the separated not-flagged corpus, joins it in single score and ref files """
    tot = 0
    notFound = 0
    # make the output path
    refPathOut = u'{0}reference.tsv'.format(notFlaggedPath)
    for n in range(3013):
        theresRef = True
        # make the input paths
        refPath = u'{0}{1}/reference.tsv'.format(notFlaggedPath, n)
        try:
            with open(refPath) as refFile:
                refLns = refFile.readlines()
                # pass each line into a single output file
                with open(refPathOut, u'a') as refOut:
                    for refLn in refLns:
                        refOut.write(refLn)
                # count the total
                tot += len(refLns)
        # if there is no reference file
        except FileNotFoundError:
            theresRef = False
            print(u'NO REFERENCE FILE IN THE FOLDER ', n)
        # get the lines for each heuristic
        if theresRef is True:
            # fill the heuristic score files
            for hName in [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', u'strBcks']:
                # make the paths
                heurPath = u'{0}{1}/{2}/score.tsv'.format(notFlaggedPath, n, hName)
                # make the folder
                utilsOs.createEmptyFolder(u'{0}{1}/'.format(notFlaggedPath, hName))
                heurPathOut = u'{0}{1}/score.tsv'.format(notFlaggedPath, hName)
                # open the input files
                try:
                    with open(heurPath) as heurFile:
                        heurLns = heurFile.readlines()
                    with open(heurPathOut, u'a') as heurOut:
                        for heurLn in heurLns:
                            heurOut.write(heurLn)
                except FileNotFoundError:
                    # fill the heuristic file with NA, so the heuristics and reference indexes correspond
                    with open(heurPathOut, u'a') as heurOut:
                        for nb in range(len(refLns)):
                            heurOut.write(u'NA\n')
                    notFound += 1
                    pass
    print(u'TOTAL SPs : ', tot)
    print(u'total not found files : ', notFound)


def changeHeuristicsScore(heuristicName, corpus=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']):
    """ rewrite the score in order to correct some problems
    u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', 'strBcks' """
    basePath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    for name in corpus:
        scorePath = u'{0}{1}/{2}/score.tsv'.format(basePath, name, heuristicName)
        with open(scorePath) as scoreFile:
            scoreLines = scoreFile.readlines()
        # line by line
        for lnIndex, scoreLn in enumerate(scoreLines):
            scoreList = scoreLn.replace(u'\n', u'').split(u'\t')
            # change depending on heuristic
            if heuristicName == u'url':
                if int(scoreList[1]) + int(scoreList[2]) != 0:
                    smallest = min([int(scoreList[1]), int(scoreList[2])])
                    greatest = max([int(scoreList[1]), int(scoreList[2])])
                    scoreList[0] = str(float(smallest) / float(greatest))
                    scoreLines[lnIndex] = u'{0}\n'.format(u'\t'.join(scoreList))
        utilsOs.dumpRawLines(scoreLines, scorePath, addNewline=False, rewrite=True)


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# apply on the problematic corpus
# applyHeuristicOnCorpus()
# applyHeuristicOnCorpus(getRightCorpus(args.corpus), getRightHeuristic(args.heuristic))

# apply on the non problematic corpus
# applyOnNotFlaggedForNHours(args.nhours)

if args.apply is False:
    # makeHourlyIndexDict()
    generateCmd(nHours=40,
                machineList=[ u'octal03', u'octal10', u'bart2', u'bart3', u'bart4', u'bart5', u'bart6',
                             u'bart7', u'bart10', u'kakia1', u'kakia2', u'kakib1', u'kakib2', u'kakic2', u'kakid1',
                             u'kakid2', u'kakie2', u'kakif1', u'kakif2',
                             u'ilar01', u'ilar02', u'octal04', u'octal05', u'octal07', u'octal06', u'octal17'])
else:
    time.sleep(args.wait)
    applyOnSpecificId(args.listIds.split(u'*'), deletePrevious=True)

## join the divided files of the not-flagged corpus
# joinNotFlaggedFolder()


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))