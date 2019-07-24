#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs
import b000path


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


def extractVeryProblematic(folderPaths=None, maxScore=None, appendToExisting=True):
    """extracts the SPs that our heuristics show as having some kind of problem in alignement or quality
    Not to be confused with the "flagged" or "not flagged" corpus   """
    if folderPaths is None:
        folderPaths = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']
    if maxScore is None:
        maxScore = {u'nb': 0.5, u'len': 0.35, u'cog': 0.1, u'fa': 0.3, u'ion': 0.5, u'sw': 0.3, u'spell': 0.25,
                    u'url': 0.9, u'mono': 0.95, u'strBcks': 0.25, u'punct': 0.5,  u'gibb': 0.1, u'tabl': 0.65}
    fileDict = {}
    heurDetectDict = {u'nb': 0, u'len': 0, u'cog': 0, u'fa': 0, u'ion': 0, u'sw': 0, u'spell': 0,
                    u'url': 0, u'mono': 0, u'strBcks': 0, u'punct': 0, u'gibb': 0, u'tabl': 0, u'all': 0, u'total': 0}
    appendToExisting = u'a' if appendToExisting is True else 'w'
    inp = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    # save to "PROBLEMATIC" because we are extracting the problematic sentence pairs, no matter the flag of the file
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/problematic/'
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
                                    scHeur = float(heurLn[0]) if heurLn[0] != u'na' else float('inf')
                                    scoreDict[heurName] = float(scHeur)
                                    # count nb of lines each heur detected as problematic
                                    if float(scHeur) < maxScore[heurName]:
                                        heurDetectDict[heurName] += 1
                                # apply the 3-level-voting system score mix
                                bestHeurSc = [u'len', u'fa', u'mono', u'gibb']
                                highHeurSc = [u'nb', u'ion', u'sw', u'spell', u'url', u'mono', u'strBcks', u'punct', u'tabl']
                                lowHeurSc = [u'cog']
                                nbOfbestScFalses = sum([1 for hn in bestHeurSc if scoreDict[hn] < maxScore[hn]])
                                nbOfHighScFalses = sum([1 for hn in highHeurSc if scoreDict[hn] < maxScore[hn]])
                                nbOfLowScFalses = sum([1 for hn in lowHeurSc if scoreDict[hn] < maxScore[hn]])
                                # if one of the most-precise scores is lower than his threshold, infer the SP is false
                                if nbOfbestScFalses >= 1:
                                    allSilence = False
                                # if at least 3 of the high-precision scores is lower than thresh, infer the SP is false
                                elif nbOfHighScFalses >= 3:
                                    allSilence = False
                                elif nbOfHighScFalses == 2 and nbOfLowScFalses >= 1:
                                    allSilence = False
                                # if the line scores indicate a problematic SP
                                if not allSilence:
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
        # open the score files
        for heurName, heurDict in fileDict.items():
            heurDict.close()
        print(heurDetectDict)
    return None


def extractVeryNonProblematic(folderPaths=None, maxScore=None, appendToExisting=True):
    """ extracts the SPs that our heuristics show as having no problem in alignement or quality
    Not to be confused with the "flagged" or "not flagged" corpus   """
    if folderPaths is None:
        folderPaths = [u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED']
    if maxScore is None:
        maxScore = {u'nb': 1.0, u'len': 0.7, u'cog': 0.2, u'fa': 0.6, u'ion': 0.65, u'sw': 0.9, u'spell': 0.85,
                    u'url': 0.95, u'mono': float(u'inf'), u'strBcks': 0.65, u'punct': 0.85,  u'gibb': 0.85,
                    u'tabl': 0.75}
    fileDict = {}
    heurDetectDict = {u'nb': 0, u'len': 0, u'cog': 0, u'fa': 0, u'ion': 0, u'sw': 0, u'spell': 0,
                    u'url': 0, u'mono': 0, u'strBcks': 0, u'punct': 0, u'gibb': 0, u'tabl': 0, u'all': 0, u'total': 0}
    appendToExisting = u'a' if appendToExisting is True else 'w'
    inp = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    # save to "NO PROBLEMATIC" because we are extracting the non-problematic sentence pairs, no matter the flag
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/noProblematic/'
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
                                bestHeurSc = [u'nb', u'strBcks']
                                highHeurSc = [u'ion', u'punct']
                                nbOfbestScTrues = sum([1 for hn in bestHeurSc if scoreDict[hn] >= maxScore[hn]])
                                nbOfHighScTrues = sum([1 for hn in highHeurSc if scoreDict[hn] >= maxScore[hn]])
                                # if two of the most-precise scores is higher than its threshold, infer the SP is True
                                if nbOfbestScTrues >= 2:
                                    allSilence = False
                                # if one of the most-precise scores and at least one high-precision score is higher
                                # than the threshold, infer the SP is True
                                elif nbOfbestScTrues == 1 and nbOfHighScTrues >= 1:
                                    allSilence = False
                                # if the line scores indicate a not-problematic SP
                                if not allSilence:
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
        # open the score files
        for heurName, heurDict in fileDict.items():
            heurDict.close()
        print(heurDetectDict)
    return None


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# extract the very problematic

print("PROBLEMATIC - FLAGGED")
extractVeryProblematic(folderPaths=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY'])
print("PROBLEMATIC - NOT-FLAGGED")
extractVeryProblematic(folderPaths=[u'NOT-FLAGGED'])

# extract the not problematic at all

print("NOT-PROBLEMATIC - FLAGGED")
extractVeryNonProblematic(folderPaths=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY'])
print("NOT-PROBLEMATIC - NOT-FLAGGED")
extractVeryNonProblematic(folderPaths=[u'NOT-FLAGGED'])

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))