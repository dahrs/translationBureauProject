#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys, argparse, time, json
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs
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
        corpus = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl']
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


def getLnToWrite(heurName, srcLn, trgtLn, enLn, frLn, placeInDocument=None):
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
        score, totalUrlsSrc, totalUrlsTrgt, totalSrc, totalTrgt = hasUrl(srcLn, trgtLn, addInfo=True)
    # monolinguistic presence heuristic
    elif heurName == u'mono':
        score, totalSrc, totalTrgt = monoling(srcLn, trgtLn, addInfo=True)
    # content table heuristic
    elif heurName == u'tabl':
        score, totalSrc, totalTrgt = tableOfContents(srcLn, trgtLn, addInfo=True, placeInDocument=placeInDocument)
    # get the silence
    score = u'na' if score is None else score
    # dump to files
    if heurName == u'nb':
        return u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n'.format(score, scAb, totalIntersect, totalSrc, totalTrgt,
                                                               ttInterAb, ttSrcAb, ttTrgtAb)
    elif heurName == u'len':
        return (u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n'.format(score, scCh, totalSrc,
                                                                 totalTrgt, ttSrcCh, ttTrgtCh))
    elif heurName == u'spell':
        return u'{0}\t{1}\t{2}\t{3}\t{4}\n'.format(score, totalScSrc, totalScTrgt, totalSrc, totalTrgt)
    elif heurName == u'url':
        return u'{0}\t{1}\t{2}\t{3}\t{4}\n'.format(score, totalUrlsSrc, totalUrlsTrgt, totalSrc, totalTrgt)
    elif heurName == u'mono' or heurName == u'sw' or heurName == u'ion' or heurName == u'tabl':
        return u'{0}\t{1}\t{2}\n'.format(score, totalSrc, totalTrgt)
    else:
        return u'{0}\t{1}\t{2}\t{3}\n'.format(score, totalIntersect, totalSrc, totalTrgt)


def applyHeuristicOnCorpus(corpus=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY'],
                           heuristic=[u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl']):
    """ given a corpus and heuristic indication, it applies the heuristic to that corpus and dumps the result """
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    filePathList = getFilePathsLists(corpus)
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
                                                     placeInDocument=float(i)/float(len(enLines))))
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


def applyHeuristicsOnNotFlaggedCorpus(filesIndexes, launchId, deletePrevious=False):
    """ given a corpus and heuristic indication, it applies the heuristic to that corpus and dumps the result """
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/{0}/'.format(launchId)
    # delete the contents of the previous folder if needed
    if deletePrevious != False:
        try:
            utilsOs.removeFolderAndContent(out)
        except FileNotFoundError:
            pass
    # make the folder
    utilsOs.createEmptyFolder(out)
    filePathList, subsetIndexes = getSubsetOfFiles(filesIndexes)
    for indexTmx, tmxFilePath in tqdm(enumerate(filePathList)):
        tmxFilePath = b000path.desAnonymizePath(tmxFilePath)
        # get the list of lines
        try:
            with open(u'{0}.en'.format(tmxFilePath)) as enFile:
                enLines = enFile.readlines()
            with open(u'{0}.fr'.format(tmxFilePath)) as frFile:
                frLines = frFile.readlines()
            # get each line
            for i in range(len(enLines)):
                srcLn, trgtLn, enLn, frLn = getLines(i, enLines, frLines, tmxFilePath)
                # reference file
                outputRefPath = u'{0}reference.tsv'.format(out)
                # erase content of file if it already exists
                rewriteFileIfExists(outputRefPath)
                with open(outputRefPath, u'a') as refFile:
                    # apply the heuristics
                    for heurName in [u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl']: # [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl']
                        # make the folder
                        utilsOs.createEmptyFolder(u'{0}{1}/'.format(out, heurName))
                        # make the output files
                        outputScorePath = u'{0}{1}/score.tsv'.format(out, heurName)
                        # erase content of file if it already exists
                        rewriteFileIfExists(outputScorePath)
                        # add the scores to the files
                        with open(outputScorePath, u'a') as scoreFile:
                            scoreFile.write(getLnToWrite(heurName, srcLn, trgtLn, enLn, frLn,
                                                         placeInDocument=float(i)/float(len(enLines))))
                    refFile.write(u'{0}\t{1}\n'.format(b000path.anonymizePath(tmxFilePath), i))
        except FileNotFoundError:
            pass
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
            applyHeuristicsOnNotFlaggedCorpus(indexesToApply, nId, deletePrevious)

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
    # make the output paths
    refPathOut = u'{0}reference.tsv'.format(notFlaggedPath)
    nbPathOut = u'{0}nb/score.tsv'.format(notFlaggedPath)
    lenPathOut = u'{0}len/score.tsv'.format(notFlaggedPath)
    cogPathOut = u'{0}cog/score.tsv'.format(notFlaggedPath)
    for n in range(3500):
        # make the input paths
        refPath = u'{0}{1}/reference.tsv'.format(notFlaggedPath, n)
        nbPath = u'{0}{1}/nb/score.tsv'.format(notFlaggedPath, n)
        lenPath = u'{0}{1}/len/score.tsv'.format(notFlaggedPath, n)
        cogPath = u'{0}{1}/cog/score.tsv'.format(notFlaggedPath, n)
        try:
            with open(refPath) as refFile:
                refLns = refFile.readlines()
                tot += len(refLns)
            with open(nbPath) as nbFile:
                nbLns = nbFile.readlines()
            with open(lenPath) as lenFile:
                lenLns = lenFile.readlines()
            with open(cogPath) as cogFile:
                cogLns = cogFile.readlines()
            # pass each lino into a single output file
            with open(refPathOut, u'a') as refOut:
                for refLn in refLns:
                    refOut.write(refLn)
            with open(nbPathOut, u'a') as nbOut:
                for nbLn in nbLns:
                    nbOut.write(nbLn)
            with open(lenPathOut, u'a') as lenOut:
                for lenLn in lenLns:
                    lenOut.write(lenLn)
            with open(cogPathOut, u'a') as cogOut:
                for cogLn in cogLns:
                    cogOut.write(cogLn)
        except FileNotFoundError:
            pass
    print(tot)


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# apply on the problematic corpus
# applyHeuristicOnCorpus(heuristic=[u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl'])
# applyHeuristicOnCorpus(getRightCorpus(args.corpus), getRightHeuristic(args.heuristic))

# apply on the non problematic corpus
# applyOnNotFlaggedForNHours(args.nhours)

if args.apply is False:
    # makeHourlyIndexDict()
    generateCmd(nHours=50,
                machineList=[u'octal06', u'octal03', u'bart2', u'bart3', u'bart4', u'bart5', u'bart6', u'bart7',
                             u'bart10', u'octal04', u'octal05', u'octal07', u'octal17', u'octal10', u'ilar01',
                             u'ilar02', u'kakia1', u'kakia2', u'kakib1', u'kakib2', u'kakic2', u'kakid1', u'kakid2',
                             u'kakie2', u'kakif1', u'kakif2'])
else:
    time.sleep(args.wait)
    applyOnSpecificId(args.listIds.split(u'*'), deletePrevious=True)

## join the divided files of the not-flagged corpus
# joinNotFlaggedFolder()


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))