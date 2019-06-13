import sys, math
sys.path.append(u'../utils')
sys.path.append(u'./utils')

import utilsOs, utilsString, b000path, b003heuristics
import re
from scipy.stats import pearsonr

# import pandas as pd
# import numpy as np

# count the time the algorithm takes to run
startTime = utilsOs.countTime()

count = 0
total = 0
cogn = {}
lenT = {}
lenC = {}
tablMat = {'small':{'0.0-0.19':0, '0.2-0.39':0, '0.4-0.59':0, '0.6-0.79':0, '0.8-1.0':0},
           u'dashOrNb':{'0.0-0.19':0, '0.2-0.39':0, '0.4-0.59':0, '0.6-0.79':0, '0.8-1.0':0}}
count = {'small':0, 'dashOrNb':0}

addSeparators = [u'.', u',', u':', u'/', u'-', u'h', u"''", u"'"]

# srcTrgtFiles = utilsOs.goDeepGetFiles(b000path.getBtFolderPath(flagFolder=u'a'), format=u'.tmx')
srcTrgtFiles = [u'./002manuallyAnnotated/sample', u'./003negativeNaiveExtractors/000manualAnnotation/sample']

nbrs = re.compile(r'[0-9]')
for filePath in srcTrgtFiles:
    srcFilePath = u'{0}.en'.format(filePath) if u'en-fr' in filePath else u'{0}.fr'.format(filePath)
    trgtFilePath = u'{0}.fr'.format(filePath) if u'en-fr' in filePath else u'{0}.en'.format(filePath)
    refFilePath = filePath.replace('sample', 'sampleAnnotation.tsv')
    # open line by line and apply extractors
    try:
        with open(srcFilePath) as srcFile:
            srcLines = srcFile.readlines()
        with open(trgtFilePath) as trgtFile:
            trgtLines = trgtFile.readlines()
        with open(refFilePath) as refFile:
            refLines = refFile.readlines()

        for srcLnIndex, srcLn in enumerate(srcLines):
            trgtLn = trgtLines[srcLnIndex]
            docLoc = srcLnIndex / len(srcLines)

            # sizeSrc = len(srcLn)
            # sizeTrgt = len(trgtLn)
            # if abs(sizeSrc-sizeTrgt) not in lenC:
            #     lenC[abs(sizeSrc-sizeTrgt)] = 0
            # lenC[abs(sizeSrc-sizeTrgt)] += 1

            if len(utilsString.extractNumbersFromString(srcLn[:3])) != 0 or u'-' in srcLn[:3] or u'.' in srcLn[:3] :
                if docLoc < 0.2:
                    tablMat['dashOrNb']['0.0-0.19'] += 1
                elif docLoc < 0.4:
                    tablMat['dashOrNb']['0.2-0.39'] += 1
                elif docLoc < 0.6:
                    tablMat['dashOrNb']['0.4-0.59'] += 1
                elif docLoc < 0.8:
                    tablMat['dashOrNb']['0.6-0.79'] += 1
                else:
                    tablMat['dashOrNb']['0.8-1.0'] += 1
                if refLines[srcLnIndex] != u'1.0\n':
                    count[u'small'] += 1

            srcLn = utilsString.nltkTokenizer(srcLn, addSeparators)
            trgtLn = utilsString.nltkTokenizer(trgtLn, addSeparators)

            # # compile the cognates of each token for the source and target
            # srcCognates = b003heuristics.getCognates(srcLn, 4)
            # trgtCognates = set(b003heuristics.getCognates(trgtLn, 4))
            # # get intersection of cognates
            # intersection = [cog for cog in srcCognates if cog in trgtCognates]
            # lenin = len(intersection)
            # if lenin not in cogn:
            #     cogn[lenin] = 0
            # cogn[lenin] += 1

            # sizeSrc = len(srcLn)
            # sizeTrgt = len(trgtLn)
            # if abs(sizeSrc-sizeTrgt) not in lenT:
            #     lenT[abs(sizeSrc-sizeTrgt)] = 0
            # lenT[abs(sizeSrc-sizeTrgt)] += 1

            if len(srcLn) <= 4:
                if docLoc < 0.2:
                    tablMat['small']['0.0-0.19'] += 1
                elif docLoc < 0.4:
                    tablMat['small']['0.2-0.39'] += 1
                elif docLoc < 0.6:
                    tablMat['small']['0.4-0.59'] += 1
                elif docLoc < 0.8:
                    tablMat['small']['0.6-0.79'] += 1
                else:
                    tablMat['small']['0.8-1.0'] += 1
                if refLines[srcLnIndex] != u'1.0\n':
                    count[u'dashOrNb'] += 1

            total += 1
    except FileNotFoundError:
        pass

# print(111, total, lenC)
# print(222, total, lenT)
# print(333, total, cogn)
# print(444, tablMat)
print(len(refLines), count)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))