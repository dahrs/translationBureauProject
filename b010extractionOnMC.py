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


def extractVeryProblematic(folderPaths=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY', u'NOT-FLAGGED'],
                           maxScore=[0.25, 0.45, 0.05], appendToExisting=True):
    """  """
    appendToExisting = u'a' if appendToExisting is True else 'w'
    inp = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
    out = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/problematic/'
    countDict = None
    for folder in folderPaths:
        # get the paths
        scorePathNb = u'{0}{1}/nb/score.tsv'.format(inp, folder)
        scorePathLen = u'{0}{1}/len/score.tsv'.format(inp, folder)
        scorePathCog = u'{0}{1}/cog/score.tsv'.format(inp, folder)
        refPath = u'{0}{1}/reference.tsv'.format(inp, folder)
        # open the files
        scNbFile = open(scorePathNb)
        scLenFile = open(scorePathLen)
        scCogFile = open(scorePathCog)
        with open(refPath) as refFile:
            # open the output files
            with open(u'{0}reference.tsv'.format(out), appendToExisting) as refOutputFile:
                with open(u'{0}extracted.en'.format(out), appendToExisting) as enOutputFile:
                    with open(u'{0}extracted.fr'.format(out), appendToExisting) as frOutputFile:
                        with open(u'{0}scores.tsv'.format(out), appendToExisting) as scOutputFile:
                            # get the lines
                            refLn = refFile.readline()
                            while refLn:
                                scNbLn = (scNbFile.readline()).split(u'\t')
                                scLenLn = scLenFile.readline().split(u'\t')
                                scCogLn = scCogFile.readline().split(u'\t')
                                refList = refLn.replace(u'\n', u'').split(u'\t')
                                # get the scores
                                scNb = float(scNbLn[0]) if scNbLn[0] != u'na' else scNbLn[0]
                                scLen = float(scLenLn[0]) if scLenLn[0] != u'na' else scLenLn[0]
                                scCog = float(scCogLn[0]) if scCogLn[0] != u'na' else scCogLn[0]
                                # if there is a silence in one of the scores, we pass through it
                                if u'na' not in u'{0}.{1}.{2}'.format(scNb, scLen, scCog):
                                    # extract a sentence if the three scores indicate a problematic SP
                                    if scNb <= maxScore[0] and scLen <= maxScore[1]: # and scCog <= maxScore[2]:
                                        # get the actual sentences
                                        enLn, frLn = getEnAndFrLines(refList[1], refList[0])
                                        # dump to files
                                        refOutputFile.write(refLn)
                                        enOutputFile.write(enLn)
                                        frOutputFile.write(frLn)
                                        scOutputFile.write(u'{0}\t{1}\t{2}\n'.format(scNb, scLen, scCog))
                                        # count
                                        countDict = countHeur(scNb, scLen, scCog, maxScore, countDict)
                                # get the next ref line
                                refLn = refFile.readline()
        scNbFile.close()
        scLenFile.close()
        scCogFile.close()
    print(countDict)
    return None


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

extractVeryProblematic(folderPaths=[u'ALIGNMENT-QUALITY', u'MISALIGNED', u'QUALITY'])

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))