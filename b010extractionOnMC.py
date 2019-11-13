#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs
import b000path, b003heuristics


def getEnAndFrLines(i, tmxPath):
    tmxPath = b000path.desAnonymizePath(tmxPath)
    i = int(i.replace(u'\n', u''))
    enLinesPath = u'{0}.en'.format(tmxPath)
    frLinesPath = u'{0}.fr'.format(tmxPath)
    with open(enLinesPath) as enFile:
        enLinesList = enFile.readlines()
    with open(frLinesPath) as frFile:
        frLinesList = frFile.readlines()
    return enLinesList[i], frLinesList[i]


def countHeur(scNb, scLen, scCog, maxScore, d=None):
    if d is None:
        d = {'nb':0, 'len':0, 'cog':0, 'nb-len':0, 'nborlen':0, 'all':0, '2/3':0}
    ##########################################
    if scNb <= maxScore[0]:
        d['nb'] += 1
    if scLen <= maxScore[1]:
        d['len'] += 1
    if scCog <= maxScore[2]:
        d['cog'] += 1
    if scNb <= maxScore[0] and scLen <= maxScore[1]:
        d['nb-len'] += 1
    if scNb <= maxScore[0] or scLen <= maxScore[1]:
        d['nborlen'] += 1
    if scNb <= maxScore[0] and scLen <= maxScore[1] and scCog <= maxScore[2]:
        d['all'] += 1
    if scNb <= maxScore[0] and scLen <= maxScore[1]:
        d['2/3'] += 1
    elif scNb <= maxScore[0] and scCog <= maxScore[2]:
        d['2/3'] += 1
    elif scLen <= maxScore[1] and scCog <= maxScore[2]:
        d['2/3'] += 1
    ##########################################
    return d


def delEmptyLinesAndDump(inPath, outPath):
    with open(u'{0}extracted.fr'.format(inPath)) as ff:
        with open(u'{0}extracted.en'.format(inPath)) as ef:
            with open(u'{0}reference.tsv'.format(inPath)) as rf:
                with open(u'{0}scores.tsv'.format(inPath)) as sf:
                    frLn = ff.readline()
                    enLn = ef.readline()
                    refLn = rf.readline()
                    scLn = sf.readline()
                    while frLn:
                        copyFrLn = frLn.replace(u'\n', u'').replace(u'\t', u'').replace(u' ', u'')
                        copyEnLn = enLn.replace(u'\n', u'').replace(u'\t', u'').replace(u' ', u'')
                        if copyFrLn == u'' or copyEnLn == u'':
                            pass
                        else:
                            utilsOs.appendLineToFile(frLn, u'{0}extracted.fr'.format(outPath), addNewLine=False)
                            utilsOs.appendLineToFile(enLn, u'{0}extracted.en'.format(outPath), addNewLine=False)
                            utilsOs.appendLineToFile(refLn, u'{0}reference.tsv'.format(outPath), addNewLine=False)
                            utilsOs.appendLineToFile(scLn, u'{0}scores.tsv'.format(outPath), addNewLine=False)
                        # next line
                        frLn = ff.readline()
                        enLn = ef.readline()
                        refLn = rf.readline()
                        scLn = sf.readline()
    return None




def binaryPredThreeLevelVoting(scoresNonProblmList=None, scoresProblmList=None):
    """
    :param scoresNonProblmList: [nbOfbestScTrues, nbOfHighScTrues]
    :param scoresProblmList: [nbOfbestScFalses, nbOfHighScFalses, nbOfLowScFalses]
    :return: 0 if the SP is predicted BAD, 1 if it's predicted GOOD, None if there is silence
    """
    # predict bads
    if scoresProblmList is not None:
        if scoresProblmList[0] >= 1 or scoresProblmList[1] >= 3:
            return 0
        elif scoresProblmList[1] == 2 and scoresProblmList[2] >= 1:
            return 0
    # predict goods
    if scoresNonProblmList is not None:
        if scoresNonProblmList[0] >= 2:
            return 1
        # if one of the most-precise scores and at least one high-precision score is higher
        # than the threshold, infer the SP is True
        if scoresNonProblmList[0] == 1 and scoresNonProblmList[1] >= 1:
            return 1
    # if nothing can be predicted, return silence
    return None


def getHeurScCount4False(scoreDict, maxScoreForFalse=None):
    if maxScoreForFalse is None:
        trash, maxScoreForFalse = b003heuristics.getMaxScores()
    # if score dict is a list instead of a dict
    if type(scoreDict) is list:
        aDict = {}
        heuristicsList = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl', u'strBcks',
                          u'punct', u'gibb']
        for heurName, sc in zip(heuristicsList, scoreDict):
            aDict[heurName] = float(sc)
        scoreDict = aDict
    # make sure the silence scores were replaced by +inf not -inf
    for k, v in scoreDict.items():
        if v == float('-inf') or v == u'na':
            scoreDict[k] = float('inf')
    # get best, high, and low score count
    bestHeurSc = [u'len', u'fa', u'mono', u'gibb']
    highHeurSc = [u'nb', u'ion', u'sw', u'spell', u'url', u'mono', u'strBcks', u'punct', u'tabl']
    lowHeurSc = [u'cog']
    # get nb of scores
    nbOfbestScFalses = sum([1 for hn in bestHeurSc if scoreDict[hn] < maxScoreForFalse[hn]])
    nbOfHighScFalses = sum([1 for hn in highHeurSc if scoreDict[hn] < maxScoreForFalse[hn]])
    nbOfLowScFalses = sum([1 for hn in lowHeurSc if scoreDict[hn] < maxScoreForFalse[hn]])
    return nbOfbestScFalses, nbOfHighScFalses, nbOfLowScFalses


def extractVeryProblematic(folderPaths=None, maxScoreForFalse=None, appendToExisting=True):
    """extracts the SPs that our heuristics show as having some kind of problem in alignement or quality
    Not to be confused with the "flagged" or "not flagged" corpus   """
    if folderPaths is None:
        folderPaths = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']
    if maxScoreForFalse is None:
        trash, maxScoreForFalse = b003heuristics.getMaxScores()
    fileDict = {}
    heurDetectDict = {u'nb': 0, u'len': 0, u'cog': 0, u'fa': 0, u'ion': 0, u'sw': 0, u'spell': 0,
                    u'url': 0, u'mono': 0, u'strBcks': 0, u'punct': 0, u'gibb': 0, u'tabl': 0, u'all': 0, u'total': 0}
    appendToExisting = u'a' if appendToExisting is True else 'w'
    inp = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    # save to "PROBLEMATIC" because we are extracting the problematic sentence pairs, no matter the flag of the file
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D1/problematic/'
    for folder in folderPaths:
        # get the reference path
        refPath = u'{0}{1}/reference.tsv'.format(inp, folder)
        # open the score files
        for heurName in maxScoreForFalse:
            fileDict[heurName] = open(u'{0}{1}/{2}/score.tsv'.format(inp, folder, heurName))
        with open(refPath) as refFile:
            # open the output files
            with open(u'{0}reference.tsv'.format(out), appendToExisting) as refOutputFile:
                with open(u'{0}extracted.en'.format(out), appendToExisting) as enOutputFile:
                    with open(u'{0}extracted.fr'.format(out), appendToExisting) as frOutputFile:
                        with open(u'{0}scores.tsv'.format(out), appendToExisting) as scOutputFile:
                            # get the lines
                            refLn = refFile.readline()
                            while refLn:
                                allSilence = True
                                refList = refLn.replace(u'\n', u'').split(u'\t')
                                # count total nb of lines
                                heurDetectDict[u'total'] += 1
                                # make a dict to save all the different scores
                                scoreDict = {}
                                # open the score files
                                for heurName, dictFile in fileDict.items():
                                    heurLn = (dictFile.readline()).split(u'\t')
                                    # get the scores
                                    scHeur = float(heurLn[0]) if heurLn[0] != u'na' else float('inf')
                                    scoreDict[heurName] = float(scHeur)
                                    # count nb of lines each heur detected as problematic
                                    if float(scHeur) < maxScoreForFalse[heurName]:
                                        heurDetectDict[heurName] += 1
                                # apply the 3-level-voting system score mix
                                nbOfbestScFalses, nbOfHighScFalses, nbOfLowScFalses = getHeurScCount4False(scoreDict, maxScoreForFalse)
                                # if one of the most-precise scores is lower than his threshold, infer the SP is false
                                prediction = binaryPredThreeLevelVoting(
                                    scoresProblmList=[nbOfbestScFalses, nbOfHighScFalses, nbOfLowScFalses])
                                # if the line scores indicate a problematic SP
                                if prediction == 0:
                                    # get the actual sentences
                                    enLn, frLn = getEnAndFrLines(refList[1], refList[0])
                                    # dump to files
                                    refOutputFile.write(refLn)
                                    enOutputFile.write(enLn)
                                    frOutputFile.write(frLn)
                                    # change back the infinity values to NA
                                    for heurName in fileDict.keys():
                                        if scoreDict[heurName] in [float('inf'), float('-inf')]:
                                            scoreDict[heurName] = u'na'
                                    # get the score line
                                    scLine = u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\t{12}\n'.format(
                                        scoreDict[u'nb'], scoreDict[u'len'], scoreDict[u'cog'], scoreDict[u'fa'],
                                        scoreDict[u'ion'], scoreDict[u'sw'], scoreDict[u'spell'], scoreDict[u'url'],
                                        scoreDict[u'mono'], scoreDict[u'strBcks'], scoreDict[u'punct'],
                                        scoreDict[u'gibb'], scoreDict[u'tabl'])
                                    scOutputFile.write(scLine)
                                    # count nb of lines the mix of heur detected as problematic
                                    heurDetectDict[u'all'] += 1
                                # get the next ref line
                                refLn = refFile.readline()
        # close the score files
        for heurName, heurDict in fileDict.items():
            heurDict.close()
        print(heurDetectDict)
        # save the same SPs but deleting the empty lines and dump them in a separate folder
        delEmptyLinesAndDump(out, u'{0}withoutEmptyLines/'.format(out))
    return None


def getHeurScCount4True(scoreDict, maxScore=None):
    if maxScore is None:
        maxScore, trash = b003heuristics.getMaxScores()
    # if score dict is a list instead of a dict
    if type(scoreDict) is list:
        aDict = {}
        heuristicsList = [u'nb', u'cog', u'len', u'fa', u'ion', u'sw', u'spell', u'url', u'mono', u'tabl',
                          u'strBcks',
                          u'punct', u'gibb']
        for heurName, sc in zip(heuristicsList, scoreDict):
            aDict[heurName] = float(sc)
        scoreDict = aDict
    # make sure the silence scores were replaced by -inf not +inf
    for k, v in scoreDict.items():
        if v == float('inf') or v == u'na':
            scoreDict[k] = float('-inf')
    # get nb of scores
    bestHeurSc = [u'nb', u'strBcks']
    highHeurSc = [u'ion', u'punct']
    nbOfbestScTrues = sum([1 for hn in bestHeurSc if scoreDict[hn] >= maxScore[hn]])
    nbOfHighScTrues = sum([1 for hn in highHeurSc if scoreDict[hn] >= maxScore[hn]])
    return nbOfbestScTrues, nbOfHighScTrues


def extractVeryNonProblematic(folderPaths=None, maxScore=None, appendToExisting=True):
    """ extracts the SPs that our heuristics show as having no problem in alignement or quality
    Not to be confused with the "flagged" or "not flagged" corpus   """
    if folderPaths is None:
        folderPaths = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']
    if maxScore is None:
        maxScore, trash = b003heuristics.getMaxScores()
    trash, maxScoreForFalse = b003heuristics.getMaxScores()
    fileDict = {}
    heurDetectDict = {u'nb': 0, u'len': 0, u'cog': 0, u'fa': 0, u'ion': 0, u'sw': 0, u'spell': 0,
                    u'url': 0, u'mono': 0, u'strBcks': 0, u'punct': 0, u'gibb': 0, u'tabl': 0, u'all': 0, u'total': 0}
    appendToExisting = u'a' if appendToExisting is True else 'w'
    inp = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    # save to "NO PROBLEMATIC" because we are extracting the non-problematic sentence pairs, no matter the flag
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D1/noProblematic/'
    for folder in folderPaths:
        # get the reference path
        refPath = u'{0}{1}/reference.tsv'.format(inp, folder)
        # open the score files
        for heurName in maxScore:
            fileDict[heurName] = open(u'{0}{1}/{2}/score.tsv'.format(inp, folder, heurName))
        with open(refPath) as refFile:
            # open the output files
            with open(u'{0}reference.tsv'.format(out), appendToExisting) as refOutputFile:
                with open(u'{0}extracted.en'.format(out), appendToExisting) as enOutputFile:
                    with open(u'{0}extracted.fr'.format(out), appendToExisting) as frOutputFile:
                        with open(u'{0}scores.tsv'.format(out), appendToExisting) as scOutputFile:
                            # get the lines
                            refLn = refFile.readline()
                            while refLn:
                                allSilence = True
                                refList = refLn.replace(u'\n', u'').split(u'\t')
                                # count total nb of lines
                                heurDetectDict[u'total'] += 1
                                # make a dict to save all the different scores
                                scoreDict = {}
                                # open the score files
                                for heurName, dictFile in fileDict.items():
                                    heurLn = (dictFile.readline()).split(u'\t')
                                    # get the scores
                                    scHeur = float(heurLn[0]) if heurLn[0] != u'na' else float('-inf')
                                    scoreDict[heurName] = float(scHeur)
                                    # count nb of lines each heur detected as not-problematic
                                    if float(scHeur) >= maxScore[heurName]:
                                        heurDetectDict[heurName] += 1
                                # apply the 3-level-voting system score mix
                                nbOfbestScTrues, nbOfHighScTrues = getHeurScCount4True(scoreDict, maxScore)
                                nbOfbestScFalses, nbOfHighScFalses, nbOfLowScFalses = getHeurScCount4False(scoreDict,
                                                                                                    maxScoreForFalse)
                                # make sure there is no high score indicating a problematic SP
                                prediction = binaryPredThreeLevelVoting(
                                    scoresNonProblmList=[nbOfbestScTrues, nbOfHighScTrues],
                                    scoresProblmList=[nbOfbestScFalses, nbOfHighScFalses, nbOfLowScFalses])
                                # if the line scores indicate a not-problematic SP
                                if prediction == 1:
                                    # get the actual sentences
                                    enLn, frLn = getEnAndFrLines(refList[1], refList[0])
                                    # dump to files
                                    refOutputFile.write(refLn)
                                    enOutputFile.write(enLn)
                                    frOutputFile.write(frLn)
                                    # change back the infinity values to NA
                                    for heurName in fileDict.keys():
                                        if scoreDict[heurName] in [float('inf'), float('-inf')]:
                                            scoreDict[heurName] = u'na'
                                    # get the score line
                                    scLine = u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\t{12}\n'.format(
                                        scoreDict[u'nb'], scoreDict[u'len'], scoreDict[u'cog'], scoreDict[u'fa'],
                                        scoreDict[u'ion'], scoreDict[u'sw'], scoreDict[u'spell'], scoreDict[u'url'],
                                        scoreDict[u'mono'], scoreDict[u'strBcks'], scoreDict[u'punct'],
                                        scoreDict[u'gibb'], scoreDict[u'tabl'])
                                    scOutputFile.write(scLine)
                                    # count nb of lines the mix of heur detected as problematic
                                    heurDetectDict[u'all'] += 1
                                # get the next ref line
                                refLn = refFile.readline()
        # close the score files
        for heurName, heurDict in fileDict.items():
            heurDict.close()
        print(heurDetectDict)
    return None


def getAndDumpHeurPredictions(inputFilePath, outputFilePath=None):
    dictCount = {u"total": 0, u"zeros": 0, u"ones": 0, u"silences": 0}
    with open(inputFilePath) as scFile:
        # delete the previous files if need to dump
        if outputFilePath is not None:
            utilsOs.deleteAFile(outputFilePath)
        else:
            outputFilePath = u"./test"
        maxScore, maxScoreForFalse = b003heuristics.getMaxScores()
        with open(outputFilePath, "a") as predFile:
            # open the score line
            scLn = scFile.readline()
            while scLn:
                # transform string line into score list
                scList = [float(sc) if sc != u"na" else float("-inf") for sc in scLn.replace(u"\n", u"").split(u'\t')]
                # apply the 3-level-voting system score mix
                nbOfbestScTrues, nbOfHighScTrues = getHeurScCount4True(scList, maxScore)
                nbOfbestScFalses, nbOfHighScFalses, nbOfLowScFalses = getHeurScCount4False(scList,
                                                                                           maxScoreForFalse)
                # make sure there is no high score indicating a problematic SP
                prediction = binaryPredThreeLevelVoting(
                    scoresNonProblmList=[nbOfbestScTrues, nbOfHighScTrues],
                    scoresProblmList=[nbOfbestScFalses, nbOfHighScFalses, nbOfLowScFalses])
                # dump to external file
                writablePred = u'{0}\n'.format(prediction) if prediction is not None else u"na\n"
                if outputFilePath is not None:
                    predFile.write(writablePred)
                # count everything
                dictCount[u"total"] += 1
                if prediction is None:
                    dictCount[u"silences"] += 1
                elif prediction == 0:
                    dictCount[u"zeros"] += 1
                elif prediction == 1:
                    dictCount[u"ones"] += 1
                # next line
                scLn = scFile.readline()
    print(dictCount)




# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# extract the very problematic

# print("PROBLEMATIC - FLAGGED")
# extractVeryProblematic(folderPaths=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY'])
# print("PROBLEMATIC - NOT-FLAGGED")
# extractVeryProblematic(folderPaths=[u'NOT-FLAGGED'])

# extract the not problematic at all

# print("NOT-PROBLEMATIC - FLAGGED")
# extractVeryNonProblematic(folderPaths=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY'])
# print("NOT-PROBLEMATIC - NOT-FLAGGED")
# extractVeryNonProblematic(folderPaths=[u'NOT-FLAGGED'])

# just dump in separate files the SPs without the empty lines
# spPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D1/problematic/'
# delEmptyLinesAndDump(spPath, u'{0}withoutEmptyLinesWithoutFAheur/'.format(spPath))

# get the prediction for a specific file in a separate dumped file
inputFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.scores"
outputFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.heur.pred"
getAndDumpHeurPredictions(inputFilePath, outputFilePath)


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))