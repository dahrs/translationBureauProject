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
                    default=u'NOT-FLAGGED',
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
                    default=u'none',
                    help=u'list of the ids where we must apply the heuristics for the no-flagged corpus, i.e.: octal06')
parser.add_argument(u'-w', u'--wait', type=int,
                    default=0,
                    help=u'time to wait before launching the heuristics')
args = parser.parse_args()


def getRightCorpus(corpusString):
    if corpusString == u'all':
        corpus = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']
    elif corpusString == u'p' or args.corpus == u'probl':
        corpus = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY']
    elif corpusString == u'nf' or args.corpus == u'np' or args.corpus == u'n':
        corpus = [u'NOT-FLAGGED']
    elif corpusString == u'aq' or args.corpus == u'qa':
        corpus = [u'ALIGNMENT-QUALITY']
    elif corpusString == u'q':
        corpus = [u'QUALITY']
    elif corpusString == u'm' or args.corpus == u'a':
        corpus = [u'MISALIGNED']
    else:
        corpus = [corpusString]
    return corpus


def getRightHeuristic(heuristicString):
    if heuristicString == u'all':
        corpus = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'strBcks', u'punct',
                  u'gibb', u'tabl']
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
                 placeInDocument=None, stopWordsEnFrDict=None, enLex=None, frLex=None, fauxAmisEn=None,
                 fauxAmisFr=None, starbucksExprDict=None, starbucksWordDict=None):
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
        score, totalIntersect, totalSrc, totalTrgt = fauxAmis(enLn, frLn, addInfo=True,
                                                              fauxAmisEn=fauxAmisEn, fauxAmisFr=fauxAmisFr)
    # ion suffix heuristic
    elif heurName == u'ion':
        score, totalSrc, totalTrgt = ionSuffixMismatch(srcLn, trgtLn, addInfo=True)
    # stop words heuristic
    elif heurName == u'sw':
        score, totalSrc, totalTrgt = stopWordsMismatch(enLn, frLn, addInfo=True, stopWordsEnFrDict=stopWordsEnFrDict)
    # spelling check heuristic
    elif heurName == u'spell':
        score, totalElSrc, totalElTrgt, totalSrc, totalTrgt = spellingCheck(enLn, frLn, addInfo=True,
                                                                            enLexicon=enLex, frLexicon=frLex)
    # url and folder paths detector heuristic
    elif heurName == u'url':
        score, totalElSrc, totalElTrgt, totalSrc, totalTrgt = urlMismatch(srcLn, trgtLn, addInfo=True)
    # monolinguistic presence heuristic
    elif heurName == u'mono':
        score, totalElSrc, totalElTrgt, totalSrc, totalTrgt = monoling(srcLn, trgtLn, addInfo=True)
    # content table heuristic
    elif heurName == u'tabl':
        score, totalElSrc, totalElTrgt, totalSrc, totalTrgt = tableOfContentsMismatch(srcLn, trgtLn, addInfo=True)
    # content table heuristic
    elif heurName == u'gibb':
        score, totalElSrc, totalElTrgt, totalSrc, totalTrgt = gibberish(srcLn, trgtLn, addInfo=True)
    # starbucks word by word translation
    elif heurName == u'strBcks':
        score, totalSrc, totalTrgt = starbucksTranslationMismatch(enLn, frLn, addInfo=True,
                                                                  starbucksExprDict=starbucksExprDict,
                                                                  starbucksWordDict=starbucksWordDict)
    # punctuation and symbol heuristic
    elif heurName == u'punct':
        score, totalIntersect, totalSrc, totalTrgt = punctAndSymb(srcLn, trgtLn, addInfo=True)
    else:
        raise TypeError('wrong heuristic code name given in the argument')
    # get the silence
    score = u'na' if score is None else score
    # dump to files
    if heurName == u'nb':
        return u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n'.format(score, scAb, totalIntersect, totalSrc, totalTrgt,
                                                               ttInterAb, ttSrcAb, ttTrgtAb)
    elif heurName in [u'len']:
        return (u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n'.format(score, scCh, totalSrc,
                                                                 totalTrgt, ttSrcCh, ttTrgtCh))
    elif heurName in [u'mono', u'spell', u'tabl', u'url', u'gibb']:
        return u'{0}\t{1}\t{2}\t{3}\t{4}\n'.format(score, totalElSrc, totalElTrgt, totalSrc, totalTrgt)
    elif heurName in [u'sw', u'ion', u'strBcks']:
        return u'{0}\t{1}\t{2}\n'.format(score, totalSrc, totalTrgt)
    else:
        return u'{0}\t{1}\t{2}\t{3}\n'.format(score, totalIntersect, totalSrc, totalTrgt)


def applyHeuristicOnCorpus(corpus=None, heuristic=None, out=None):
    """ given a corpus and heuristic indication, it applies the heuristic to that corpus and dumps the result """
    if corpus is None:
        corpus = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY']
    if heuristic is None:
        heuristic = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', u'strBcks',
                     u'punct', u'gibb']
    if out is None:
        out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    # get the heuristic needed objects
    starbucksExprDict, starbucksWordDict = utilsString.openEn2FrStarbucksDict()
    fauxAmisEn = utilsString.openFauxAmisDict(enToFr=True, withDescription=False, reducedVersion=True)
    fauxAmisFr = utilsString.openFauxAmisDict(enToFr=False, withDescription=False, reducedVersion=True)
    stopWordsEnFrDict = utilsString.openEn2FrStopWordsDict()
    enLexicon = utilsString.getWiki1000MostCommonLexicon(u'en')
    frLexicon = utilsString.getWiki1000MostCommonLexicon(u'fr')
    # get the file paths and get sure we don't take into account the file we have already seen
    filePathList = getFilePathsLists(corpus)
    # start anew by erasing the previous files for the reference and scores
    for flag in corpus:
        # make the folder
        utilsOs.createEmptyFolder(u'{0}{1}/'.format(out, flag))
        outputRefPath = u'{0}{1}/reference.tsv'.format(out, flag)
        # erase content of previous reference file
        with open(outputRefPath, u'w') as refFile:
            refFile.write(u'')
        # erase content of previous score file
        for heurName in heuristic:
            # make the folder
            utilsOs.createEmptyFolder(u'{0}{1}/{2}/'.format(out, flag, heurName))
            # make the output files
            outputScorePath = u'{0}{1}/{2}/score.tsv'.format(out, flag, heurName)
            with open(outputScorePath, u'w') as scoreFile:
                scoreFile.write(u'')
    # for each file in the list
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
            # append to the file
            with open(outputRefPath, u'a') as refFile:
                # apply the heuristics
                for heurName in heuristic:
                    # make the output files
                    outputScorePath = u'{0}{1}/{2}/score.tsv'.format(out, flag, heurName)
                    # append to the score files
                    with open(outputScorePath, u'a') as scoreFile:
                        scoreFile.write(getLnToWrite(heurName, srcLn, trgtLn, enLn, frLn,
                                                     placeInDocument=float(i)/float(len(enLines)),
                                                     starbucksExprDict=starbucksExprDict,
                                                     starbucksWordDict=starbucksWordDict,
                                                     fauxAmisEn=fauxAmisEn, fauxAmisFr=fauxAmisFr,
                                                     stopWordsEnFrDict=stopWordsEnFrDict,
                                                     enLex=enLexicon, frLex=frLexicon))
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


def applyHeuristicsOnNotFlaggedCorpus(filesIndexes, launchId, heuristicsList=None):
    """ given a corpus and heuristic indication, it applies the heuristic to that corpus and dumps the result """
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/{0}/'.format(launchId)
    if heuristicsList is None:
        heuristicsList = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl',
                          u'strBcks', u'punct', u'gibb']
    starbucksExprDict, starbucksWordDict = utilsString.openEn2FrStarbucksDict()
    # make the folder
    utilsOs.createEmptyFolder(out)
    # reference file
    outputRefPath = u'{0}reference.tsv'.format(out)
    referenceAlreadyExists = utilsOs.theFileExists(outputRefPath)
    # get the list of ALL the file paths
    filePathList, subsetIndexes = getSubsetOfFiles(filesIndexes)
    # open the reference files
    with open(outputRefPath, u'a') as refFile:
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
                    # apply the heuristics
                    for heurName in heuristicsList:
                        heurFolder = u'{0}{1}/'.format(out, heurName)

                        # make the folder
                        utilsOs.createEmptyFolder(heurFolder)
                        # make the output files
                        outputScorePath = u'{0}score.tsv'.format(heurFolder)
                        # add the scores to the files
                        with open(outputScorePath, u'a') as scoreFile:
                            scoreFile.write(getLnToWrite(heurName, srcLn, trgtLn, enLn, frLn,
                                                         placeInDocument=float(i)/float(len(enLines)),
                                                         starbucksExprDict=starbucksExprDict,
                                                         starbucksWordDict=starbucksWordDict))
                    # if the reference output already exists, don't write on it
                    if referenceAlreadyExists is True:
                        pass
                    else:
                        # write the ref line
                        refFile.write(u'{0}\t{1}\n'.format(b000path.anonymizePath(tmxFilePath), i))
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


def applyOnSpecificId(idList):
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
            heurs = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', u'strBcks',
                    u'punct', u'gibb']
            applyHeuristicsOnNotFlaggedCorpus(indexesToApply, nId, heuristicsList=heurs)
        except KeyError:
            print('ATTENTION: KEYERROR with id {0} #####'.format(nId))
    print(u'FINISHED {0}...'.format(idList[0]))


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


def joinNotFlaggedFolder(notFlaggedPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/NOT-FLAGGED/'):
    """ given a path to the separated not-flagged corpus, joins it in single score and ref files """
    tot = 0
    notFound = 0
    # make the output path
    refPathOut = u'{0}reference.tsv'.format(notFlaggedPath)
    nbPathOut = u'{0}nb/score.tsv'.format(notFlaggedPath)
    cogPathOut = u'{0}cog/score.tsv'.format(notFlaggedPath)
    lenPathOut = u'{0}len/score.tsv'.format(notFlaggedPath)
    faPathOut = u'{0}fa/score.tsv'.format(notFlaggedPath)
    ionPathOut = u'{0}ion/score.tsv'.format(notFlaggedPath)
    swPathOut = u'{0}sw/score.tsv'.format(notFlaggedPath)
    spellPathOut = u'{0}spell/score.tsv'.format(notFlaggedPath)
    urlPathOut = u'{0}url/score.tsv'.format(notFlaggedPath)
    monoPathOut = u'{0}mono/score.tsv'.format(notFlaggedPath)
    tablPathOut = u'{0}tabl/score.tsv'.format(notFlaggedPath)
    strBcksPathOut = u'{0}strBcks/score.tsv'.format(notFlaggedPath)
    punctPathOut = u'{0}punct/score.tsv'.format(notFlaggedPath)
    gibbPathOut = u'{0}gibb/score.tsv'.format(notFlaggedPath)
    # delete the existing file content
    for folderPath in [refPathOut, nbPathOut, cogPathOut, lenPathOut, faPathOut, ionPathOut, swPathOut, spellPathOut,
                       urlPathOut, monoPathOut, tablPathOut, strBcksPathOut, punctPathOut, gibbPathOut]:
        utilsOs.deleteFileContent(folderPath)
    # open each n segmentation file in order to join them in a single file
    for n in range(3013):
        # make the input paths
        refPath = u'{0}{1}/reference.tsv'.format(notFlaggedPath, n)
        nbPath = u'{0}{1}/nb/score.tsv'.format(notFlaggedPath, n)
        cogPath = u'{0}{1}/cog/score.tsv'.format(notFlaggedPath, n)
        lenPath = u'{0}{1}/len/score.tsv'.format(notFlaggedPath, n)
        faPath = u'{0}{1}/fa/score.tsv'.format(notFlaggedPath, n)
        ionPath = u'{0}{1}/ion/score.tsv'.format(notFlaggedPath, n)
        swPath = u'{0}{1}/sw/score.tsv'.format(notFlaggedPath, n)
        spellPath = u'{0}{1}/spell/score.tsv'.format(notFlaggedPath, n)
        urlPath = u'{0}{1}/url/score.tsv'.format(notFlaggedPath, n)
        monoPath = u'{0}{1}/mono/score.tsv'.format(notFlaggedPath, n)
        tablPath = u'{0}{1}/tabl/score.tsv'.format(notFlaggedPath, n)
        strBcksPath = u'{0}{1}/strBcks/score.tsv'.format(notFlaggedPath, n)
        punctPath = u'{0}{1}/punct/score.tsv'.format(notFlaggedPath, n)
        gibbPath = u'{0}{1}/gibb/score.tsv'.format(notFlaggedPath, n)
        # join them in a single file
        try:
            with open(refPath) as refFile:
                refLns = refFile.readlines()
            heurLnsList = []
            for hPath in [nbPath, cogPath, lenPath, faPath, ionPath, swPath, spellPath, urlPath, monoPath,
                          tablPath, strBcksPath, punctPath, gibbPath]:
                try:
                    with open(hPath) as hFile:
                        heurLnsList.append(hFile.readlines())
                except FileNotFoundError:
                    heurLnsList.append(None)
            # pass each line into a single output file
            with open(refPathOut, u'a') as refOut:
                with open(nbPathOut, u'a') as nbOut:
                    with open(cogPathOut, u'a') as cogOut:
                        with open(lenPathOut, u'a') as lenOut:
                            with open(faPathOut, u'a') as faOut:
                                with open(ionPathOut, u'a') as ionOut:
                                    with open(swPathOut, u'a') as swOut:
                                        with open(spellPathOut, u'a') as spellOut:
                                            with open(urlPathOut, u'a') as urlOut:
                                                with open(monoPathOut, u'a') as monoOut:
                                                    with open(tablPathOut, u'a') as tablOut:
                                                        with open(strBcksPathOut, u'a') as strBcksOut:
                                                            with open(punctPathOut, u'a') as punctOut:
                                                                with open(gibbPathOut, u'a') as gibbOut:
                                                                    # dump the ref lines
                                                                    for indRef, refLn in enumerate(refLns):
                                                                        refOut.write(refLn)
                                                                        # dump lines for each heuristic - Nb
                                                                        if heurLnsList[0] is not None:
                                                                            nbOut.write(heurLnsList[0][indRef])
                                                                        else:
                                                                            nbOut.write(u'NA\n')
                                                                        # cog
                                                                        if heurLnsList[1] is not None:
                                                                            cogOut.write(heurLnsList[1][indRef])
                                                                        else:
                                                                            cogOut.write(u'NA\n')
                                                                        # len
                                                                        if heurLnsList[2] is not None:
                                                                            lenOut.write(heurLnsList[2][indRef])
                                                                        else:
                                                                            lenOut.write(u'NA\n')
                                                                        # fa
                                                                        if heurLnsList[3] is not None:
                                                                            faOut.write(heurLnsList[3][indRef])
                                                                        else:
                                                                            faOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # ion
                                                                        if heurLnsList[4] is not None:
                                                                            ionOut.write(heurLnsList[4][indRef])
                                                                        else:
                                                                            ionOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # sw
                                                                        if heurLnsList[5] is not None:
                                                                            swOut.write(heurLnsList[5][indRef])
                                                                        else:
                                                                            swOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # spell
                                                                        if heurLnsList[6] is not None:
                                                                            spellOut.write(heurLnsList[6][indRef])
                                                                        else:
                                                                            spellOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # url
                                                                        if heurLnsList[7] is not None:
                                                                            urlOut.write(heurLnsList[7][indRef])
                                                                        else:
                                                                            urlOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # mono
                                                                        if heurLnsList[8] is not None:
                                                                            monoOut.write(heurLnsList[8][indRef])
                                                                        else:
                                                                            monoOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # tabl
                                                                        if heurLnsList[9] is not None:
                                                                            tablOut.write(heurLnsList[9][indRef])
                                                                        else:
                                                                            tablOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # strBcks
                                                                        if heurLnsList[10] is not None:
                                                                            strBcksOut.write(heurLnsList[10][indRef])
                                                                        else:
                                                                            strBcksOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # punct
                                                                        if heurLnsList[11] is not None:
                                                                            punctOut.write(heurLnsList[11][indRef])
                                                                        else:
                                                                            punctOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # gibb
                                                                        if heurLnsList[12] is not None:
                                                                            gibbOut.write(heurLnsList[12][indRef])
                                                                        else:
                                                                            gibbOut.write(u'NA\n')
                                                                            notFound += 1
                                                                        # count the total
                                                                        tot += 1
        # if there is no reference file
        except FileNotFoundError:
            print(u'NO REFERENCE FILE IN THE FOLDER ', n)
    print(u'TOTAL SPs : ', tot)
    print(u'total not found files : ', notFound)


def repairHeuristicsScore(heuristicName, corpus=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']):
    """ rewrite the score in order to correct some problems
    u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', 'strBcks', 'punct', 'gibb' """
    basePath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    for name in corpus:
        scorePath = u'{0}{1}/{2}/score.tsv'.format(basePath, name, heuristicName)
        with open(scorePath) as scoreFile:
            scoreLines = scoreFile.readlines()
        # line by line
        for lnIndex, scoreLn in enumerate(scoreLines):
            scoreList = scoreLn.replace(u'\n', u'').split(u'\t')
            if scoreList[0] != u'na':
                # change depending on heuristic
                if heuristicName in [u'url']:
                    smallest = min([int(scoreList[3]), int(scoreList[4])])
                    greatest = max([int(scoreList[3]), int(scoreList[4])])
                    if int(scoreList[3]) + int(scoreList[4]) != 0:
                        scoreList[0] = str(float(smallest) / float(greatest))
                        scoreLines[lnIndex] = u'{0}\n'.format(u'\t'.join(scoreList))
                elif heuristicName in [u'mono']:
                    smallest = min([int(scoreList[1]), int(scoreList[2])])
                    greatest = max([int(scoreList[1]), int(scoreList[2])])
                    if int(scoreList[1]) + int(scoreList[2]) != 0:
                        scoreList[0] = str(float(smallest) / float(greatest))
                        scoreLines[lnIndex] = u'{0}\n'.format(u'\t'.join(scoreList))
                elif heuristicName in [u'ion']:
                    if int(scoreList[1]) + int(scoreList[2]) <= 2:
                        scoreList[0] = u'na'
                        scoreLines[lnIndex] = u'{0}\n'.format(u'\t'.join(scoreList))
        utilsOs.dumpRawLines(scoreLines, scorePath, addNewline=False, rewrite=True)


def applyHeurAndDumpScoresAndMetadata(inEnPath, inFrPath, outScMdPath):
    """
    Applies the heuristics and dumps in a file all the scores with their respective metadata.
    :param inEnPath: path to the english sentences of the SP
    :param inFrPath: path to the french sentences of the SP
    :param outScMdPath: path to the SP's scores and metadata output
    :return: None
    """
    scoresList = []
    scoresAndMetadataList = []
    heuristicsList = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', u'strBcks', 
                      u'punct', u'gibb']
    outScPath = outScMdPath.replace(u'AndMetaData', u'')
    # delete the previous files
    utilsOs.deleteFileContent(outScPath)
    utilsOs.deleteFileContent(outScMdPath)
    # get the heuristic needed objects
    starbucksExprDict, starbucksWordDict = utilsString.openEn2FrStarbucksDict()
    fauxAmisEn = utilsString.openFauxAmisDict(enToFr=True, withDescription=False, reducedVersion=True)
    fauxAmisFr = utilsString.openFauxAmisDict(enToFr=False, withDescription=False, reducedVersion=True)
    stopWordsEnFrDict = utilsString.openEn2FrStopWordsDict()
    enLexicon = utilsString.getWiki1000MostCommonLexicon(u'en')
    frLexicon = utilsString.getWiki1000MostCommonLexicon(u'fr')
    # open the SP files
    with open(inEnPath) as enFile:
        with open(inFrPath) as frFile:
            # first line
            enLn = enFile.readline().replace(u'\n', u'')
            frLn = frFile.readline().replace(u'\n', u'')
            while enLn or frLn:
                scString = u''
                scMdString = u''
                for heurName in heuristicsList:
                    # get the all scores string
                    allScores = getLnToWrite(heurName, enLn, frLn, enLn, frLn,
                                             placeInDocument=None, stopWordsEnFrDict=stopWordsEnFrDict, 
                                             enLex=enLexicon, frLex=frLexicon, fauxAmisEn=fauxAmisEn,
                                             fauxAmisFr=fauxAmisFr, starbucksExprDict=starbucksExprDict, 
                                             starbucksWordDict=starbucksWordDict)
                    # if it's the first line, we do not add a tabulation to separate
                    sep = u'' if scString == u'' else u'\t'
                    # add to the recollection of scores string
                    scString = u'{0}{1}{2}'.format(scString, sep, allScores.split(u'\t')[0])
                    # add to the scores and metadata string
                    scMdString = u'{0}{1}{2}'.format(scMdString, sep, allScores.replace(u'\n', u''))
                # add to the scores list
                scoresList.append(scString)
                scoresAndMetadataList.append(scMdString)
                # dump after a 1000 elements
                if len(scoresList) >= 1000:
                    utilsOs.appendMultLinesToFile(scoresList, outScPath, addNewLine=True)
                    utilsOs.appendMultLinesToFile(scoresAndMetadataList, outScMdPath, addNewLine=True)
                    scoresList = []
                    scoresAndMetadataList = []
                # next line
                enLn = enFile.readline().replace(u'\n', u'')
                frLn = frFile.readline().replace(u'\n', u'')
                # print(bool(enLn), bool(frLn))
            # make the last dump with the remaining elements
            utilsOs.appendMultLinesToFile(scoresList, outScPath, addNewLine=True)
            utilsOs.appendMultLinesToFile(scoresAndMetadataList, outScMdPath, addNewLine=True)
                



# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# make a changement in the heuristics score
## repairHeuristicsScore(u'mono')


# if args.apply is False:
#     # makeHourlyIndexDict()
#     generateCmd(nHours=26,
#                 machineList=[u'octal05', u'octal10', u'bart2', u'bart3', u'bart4', u'bart5', u'bart6',
#                              u'bart7', u'bart10', u'kakia1', u'kakia2', u'kakib2', u'kakic2', u'kakid1',
#                              u'kakid2', u'kakie2', u'kakif1', u'kakif2', u'octal06'])
# else:
#     if args.listIds == u'none':
#         if args.corpus not in [u'nf', u'np', u'n', u'NOT-FLAGGED']:
#             # apply on the flagged corpus
#             applyHeuristicOnCorpus(getRightCorpus(args.corpus), getRightHeuristic(args.heuristic))
#         else:
#             # apply on the non-flagged corpus
#             applyOnNotFlaggedForNHours(args.nhours)
#     else:
#         # apply on the divided non-flagged corpus
#         time.sleep(args.wait)
#         applyOnSpecificId(args.listIds.split(u'*'))


# # join the divided files of the not-flagged corpus
# joinNotFlaggedFolder()



# # apply the heuristics score to shivendra's train set
# 7M train dataset
# inEnPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_en'
# inFrPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_fr'
# outPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_scoresAndMetaData'
# 17M train dataset
# inEnPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/train_en'
# inFrPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/train_fr'
# outPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/train_scoresAndMetaData'
# # 17K BT-annotated as bad
# inEnPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.en'
# inFrPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.fr'
# outPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.scoresAndMetaData'
# applyHeurAndDumpScoresAndMetadata(inEnPath, inFrPath, outPath)

# # apply the heuristics score to 17K randomly extracted fron D1 "no problematic"
# inEnPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D1/noProblematic/17kRandom/extracted.en'
# inFrPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D1/noProblematic/17kRandom/extracted.fr'
# outPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D1/noProblematic/17kRandom/extracted.scoresAndMetaData'
# applyHeurAndDumpScoresAndMetadata(inEnPath, inFrPath, outPath)


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))