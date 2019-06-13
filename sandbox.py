import sys, math
sys.path.append(u'../utils')
sys.path.append(u'./utils')

import utilsOs, utilsString, b000path, b003heuristics
import re
from scipy.stats import pearsonr

# import pandas as pd
# import numpy as np

count = 0
total = 0
cogn = {}
lenT = {}
lenC = {}
srcTrgtFiles = utilsOs.goDeepGetFiles(b000path.getBtFolderPath(flagFolder=u'a'), format=u'.tmx')
addSeparators = [u'.', u',', u':', u'/', u'-', u'h', u"''", u"'"]
# srcTrgtFiles = [u'./002manuallyAnnotated/sample', u'./003negativeNaiveExtractors/000manualAnnotation/sample']
nbrs = re.compile(r'[0-9]')
for filePath in srcTrgtFiles:
    srcFilePath = u'{0}.en'.format(filePath) if u'en-fr' in filePath else u'{0}.fr'.format(filePath)
    trgtFilePath = u'{0}.fr'.format(filePath) if u'en-fr' in filePath else u'{0}.en'.format(filePath)
    # open line by line and apply extractors
    try:
        with open(srcFilePath) as srcFile:
            srcLines = srcFile.readlines()
        with open(trgtFilePath) as trgtFile:
            trgtLines = trgtFile.readlines()
        for srcLnIndex, srcLn in enumerate(srcLines):
            trgtLn = trgtLines[srcLnIndex]

            sizeSrc = len(srcLn)
            if sizeSrc not in lenC:
                lenC[sizeSrc] = 0
            lenC[sizeSrc] += 1
            sizeTrgt = len(trgtLn)
            if sizeTrgt not in lenC:
                lenC[sizeTrgt] = 0
            lenC[sizeTrgt] += 1

            srcLn = utilsString.nltkTokenizer(srcLn, addSeparators)
            trgtLn = utilsString.nltkTokenizer(trgtLn, addSeparators)


            sizeSrc = len(srcLn)
            if sizeSrc not in lenT:
                lenT[sizeSrc] = 0
            lenT[sizeSrc] += 1
            sizeTrgt = len(trgtLn)
            if sizeTrgt not in lenT:
                lenT[sizeTrgt] = 0
            lenT[sizeTrgt] += 1

            total += 1
    except FileNotFoundError:
        pass
print(total, lenC)
print(total, lenT)