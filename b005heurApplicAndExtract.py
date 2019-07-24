#!/usr/bin/python
# -*- coding:utf-8 -*-

from random import randint

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import b000path, utilsOs, utilsString
from b003heuristics import *

########################################################################
# HEURISTIC APPLICATION
########################################################################


def addToDict(extractedSp, filePath, index, extrType=0):
    if filePath not in extractedSp[extrType]:
        extractedSp[extrType][filePath] = [index]
    else: extractedSp[extrType][filePath].append(index)
    return extractedSp


def dumpReferenceToLangFiles(listOfRef, outputGeneralFilePath):
    """ given a lof of the references (original path, line index)
    dump the original lines into lang separated files """
    outputGeneralFilePath = outputGeneralFilePath.replace(u'.tsv', u'')
    enOutputPath = u'{0}.en'.format(outputGeneralFilePath)
    frOutputPath = u'{0}.fr'.format(outputGeneralFilePath)
    # open each ref and get each line by lang
    for ref in listOfRef:
        pathIndex = ref.split(u'\t')
        enPath = u'{0}.en'.format(pathIndex[0])
        frPath = u'{0}.fr'.format(pathIndex[0])
        with open(enPath) as enFile:
            enLines = [line.replace(u'\n', u'') for line in enFile.readlines()]
        with open(frPath) as frFile:
            frLines = [line.replace(u'\n', u'') for line in frFile.readlines()]
        enLine = enLines[int(pathIndex[1])]
        frLine = frLines[int(pathIndex[1])]
        utilsOs.appendLineToFile(enLine, enOutputPath, addNewLine=True)
        utilsOs.appendLineToFile(frLine, frOutputPath, addNewLine=True)


def getRandomIndex(iterableObjOrLength):
    # get the total length
    if type(iterableObjOrLength) is int:
        lenIter = iterableObjOrLength
    else:
        lenIter = len(iterableObjOrLength)
    # if there is no element in the dict
    if lenIter == 0:
        return None
    # if there is only one element in the dict
    elif lenIter == 1:
        rdmIndex = 0
    else:
        # randomly select an index
        rdmIndex = randint(0, lenIter - 1)
    return rdmIndex


def getQuasiRandomIndexForcingOnSpecificRange(lenIter, rangeMin=0, rangeMax=None):
    """ returns a random index but forcing on the appearance of and index in a specific range 1/4 of the time """
    if rangeMax is None:
        rangeMax = int(lenIter/2)
    decision = randint(0, 4)
    if decision == 0:
        return randint(rangeMin, rangeMax)
    return getRandomIndex(lenIter)


def randomlyExtractAndDumpHeuristicallyExtracted(extractedSp, extractionSize, subsetName):
    """ given a dict with all the heuristically extracted """
    outputDict = {0: u'./003negativeNaiveExtractors/numberCoincidence/random100Nb{0}.tsv'.format(subsetName),
                    1: u'./003negativeNaiveExtractors/fewTokens/random100few{0}.tsv'.format(subsetName),
                    2: u'./003negativeNaiveExtractors/cognates/random100cog{0}.tsv'.format(subsetName)}
    for extrType, fileDict in extractedSp.items():
        # maintain a census of which index we have already used
        dejaVu = []
        # count the total lines
        print(u"-  EXTRACTION TYPE : ", extrType, u'NUMBER OF FILES : ', len(fileDict))
        nbLines = 0
        for path, lineList in fileDict.items():
            nbLines += len(lineList)
        print(u'\tNUMBER OF EXTRACTED LINES : ', nbLines)
        dictPaths = list(fileDict.keys())
        # we stop if we achieve our limit
        while len(dejaVu) < extractionSize:
            # get the file path index if it's empty then abort
            rdmFileIndex = getRandomIndex(dictPaths)
            if rdmFileIndex is None:
                break
            # get the list of the lines
            lineList = fileDict[dictPaths[rdmFileIndex]]
            rdmLineIndex = getRandomIndex(lineList)
            # if it's empty, abort
            if rdmLineIndex is None:
                break
            # otherwise
            while u'{0}\t{1}'.format(dictPaths[rdmFileIndex], rdmLineIndex) in dejaVu:
                rdmFileIndex = getRandomIndex(dictPaths)
                lineList = fileDict[dictPaths[rdmFileIndex]]
                rdmLineIndex = getRandomIndex(lineList)
            # add to the deja vu
            dejaVu.append(u'{0}\t{1}'.format(dictPaths[rdmFileIndex], lineList[rdmLineIndex]))
        # dump
        utilsOs.dumpRawLines(dejaVu, outputDict[extrType], addNewline=True, rewrite=True)
        dumpReferenceToLangFiles(dejaVu, outputDict[extrType])
    return dejaVu


def extractMisalignedSP(pathToSrcTrgtFiles, extractionSize=100, typeOfExtractors=[0,1,2]):
    """ given a path to the original source and target files, and the types of
    extractors to be used returns SP (sentence pairs) extracted as misaligned
    extractor types:
    - 0 : same number presence in src and trgt
    - 1 : 4 or less than 4 tokens
    - 2 : """
    extractedSp = {0: {}, 1: {}, 2: {}}
    totalLines = 0

    # get name of subset
    for subset in [u'/ALIGNMENT-QUALITY', u'/MISALIGNED', u'/NOT-FLAGGED', u'/QUALITY']:
        if subset in pathToSrcTrgtFiles:
            subsetName = subset
    # type 1 block
    output1Path = u'./003negativeNaiveExtractors/numberCoincidence/'
    utilsOs.createEmptyFolder(output1Path)
    # type 2 block
    output1Path = u'./003negativeNaiveExtractors/fewTokens/'
    utilsOs.createEmptyFolder(output1Path)
    # type 3 block
    output2Path = u'./003negativeNaiveExtractors/cognates/'
    utilsOs.createEmptyFolder(output2Path)
    # get the path to the src and trgt files
    srcTrgtFiles = utilsOs.goDeepGetFiles(pathToSrcTrgtFiles, format=u'.tmx')
    print(u'TOTAL FILES : ', len(srcTrgtFiles))
    for filePath in srcTrgtFiles:
        srcFilePath = u'{0}.en'.format(filePath) if u'en-fr' in filePath else u'{0}.fr'.format(filePath)
        trgtFilePath = u'{0}.fr'.format(filePath) if u'en-fr' in filePath else u'{0}.en'.format(filePath)
        # open line by line and apply extractors
        try:
            with open(srcFilePath) as srcFile:
                with open(trgtFilePath) as trgtFile:
                    srcLines = srcFile.readlines()
                    trgtLines = trgtFile.readlines()
                    for srcLnIndex, srcLn in enumerate(srcLines):
                        trgtLn = trgtLines[srcLnIndex]
                        # tokenize
                        srcLn = srcLn.lower().replace(u' pm', u'pm')
                        trgtLn = trgtLn.lower().replace(u' pm', u'pm')
                        addSeparators = [u'.', u',', u':', u'/', u'-', u"''", u"'"]
                        srcTokens = utilsString.nltkTokenizer(srcLn, addSeparators)
                        trgtTokens = utilsString.nltkTokenizer(trgtLn, addSeparators)
                        # apply the extractors
                        if 0 in typeOfExtractors:
                            extractedSp, score = applyExtractor(nbMismatch, 0.75, srcTokens, trgtTokens,
                                                                extractedSp, filePath, 0, int(srcLnIndex))
                        if 1 in typeOfExtractors:
                            # get context scores and location in doc
                            cntxtScores = getContextScores(srcLnIndex, srcLines, trgtLines)
                            docLoc = srcLnIndex/len(srcLines)
                            extractedSp, score = applyExtractor(tableOfContents, 0.32, srcTokens, trgtTokens,
                                                                extractedSp, filePath, 1, int(srcLnIndex),
                                                                contextScores=cntxtScores, placeInDocument=docLoc)
                        if 2 in typeOfExtractors:
                            extractedSp, score = applyExtractor(cognateCoincidence, 0.1, srcTokens, trgtTokens,
                                                                extractedSp, filePath, 2, int(srcLnIndex))
                    totalLines += len(srcLines)
        # some folders have no .en and .fr to each .tmx file
        # (e.g.: '/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/MISALIGNED/241-CAN_CENT_OCC_HEALTH/SAFE/en-fr/')
        except FileNotFoundError:
            pass
    print(u'TOTAL LINES : ', totalLines)
    # dump the extracted sp dict into a json file
    utilsOs.dumpDictToJsonFile(extractedSp, pathOutputFile=u'./003negativeNaiveExtractors/005extractedSp{0}.json'.format(subsetName), overwrite=False)
    # randomly extract and dump the file path and the line index for the extracted SP
    randomlyExtractAndDumpHeuristicallyExtracted(extractedSp, extractionSize, subsetName)


def changeStructure():
    annotationFiles = utilsOs.goDeepGetFiles(u'./002manuallyAnnotated/oldOnes/MISALIGNED/', format=u'.tmx')
    for annotationPath in annotationFiles:
        origPath = u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/MISALIGNED/' + annotationPath.split(u'MISALIGNED/')[-1]
        srcPath = origPath + u'.en'
        trgtPath = origPath + u'.fr'
        with open(annotationPath) as file:
            fileLines = file.readlines()
        with open(srcPath) as src:
            srcLines = src.readlines()
        with open(trgtPath) as trgt:
            trgtLines = trgt.readlines()
        for i, anot in enumerate(fileLines):
            srcLn = srcLines[i]
            tgrtLn = trgtLines[i]
            # dump the reference
            referencePathLine = u'{0}\t{1}\n'.format(origPath, i)
            utilsOs.appendLineToFile(referencePathLine, u'./002manuallyAnnotated/sampleReference.tsv', addNewLine=False)
            # dump the annotation
            utilsOs.appendLineToFile(anot, u'./002manuallyAnnotated/sampleAnnotation.tsv', addNewLine=False)
            # dump the SP
            utilsOs.appendLineToFile(srcLn, u'./002manuallyAnnotated/sampleEn.tsv', addNewLine=False)
            utilsOs.appendLineToFile(tgrtLn, u'./002manuallyAnnotated/sampleFr.tsv', addNewLine=False)


def getEnFrLnsForIndex(index, refPath, enPath, frPath, scPath):
    # open the en and fr files
    refFile = open(refPath, u'r')
    enFile = open(enPath, u'r')
    frFile = open(frPath, u'r')
    scFile = open(scPath, u'r')
    # get the ref
    refLn = refFile.readline()
    refI = 0
    while refI != index:
        refLn = refFile.readline()
        refI += 1
    # get the en line
    enLn = enFile.readline()
    enI = 0
    while enI != index:
        enLn = enFile.readline()
        enI += 1
    # get the fr line
    frLn = frFile.readline()
    frI = 0
    while frI != index:
        frLn = frFile.readline()
        frI += 1
    # get the score line
    scLn = scFile.readline()
    scI = 0
    while scI != index:
        scLn = scFile.readline()
        scI += 1
    # close the en and fr files
    enFile.close()
    frFile.close()
    scFile.close()
    return refLn, enLn, frLn, scLn


def randomSPselectionForAnnotation(enPath, frPath, refPath, scPath, outputFolderPath, nbSp=150):
    """ given a path to the tsv files in english, french and reference (probably where the heur. were applied),
    selects randomly and extracts to an output folder, ready to be annotated """
    dejavus = set([])
    if outputFolderPath[-1] != u'/':
        outputFolderPath = u'{0}/'.format(outputFolderPath)
    # open the output Files, overwrite previous if it already exists
    utilsOs.deleteAFile(u'{0}sample.en'.format(outputFolderPath))
    utilsOs.deleteAFile(u'{0}sample.fr'.format(outputFolderPath))
    utilsOs.deleteAFile(u'{0}sampleReference.Paths'.format(outputFolderPath))
    utilsOs.deleteAFile(u'{0}scores.tsv'.format(outputFolderPath))
    # get the reference lines
    with open(refPath) as refFile:
        refLns = refFile.readlines()
        lengthRef = len(refLns)
        refLns = None
    for n in range(nbSp):
        # select a random index that is not yet in dejavus
        rdmInd = getQuasiRandomIndexForcingOnSpecificRange(lengthRef, rangeMin=0, rangeMax=200000)
        while rdmInd in dejavus:
            rdmInd = getQuasiRandomIndexForcingOnSpecificRange(lengthRef, rangeMin=0, rangeMax=200000)
        dejavus.add(rdmInd)
        # search for that index in the en files
        refLn, enLn, frLn, scLn = getEnFrLnsForIndex(rdmInd, refPath, enPath, frPath, scPath)
        # dump in the output folder path
        utilsOs.appendLineToFile(enLn, u'{0}sample.en'.format(outputFolderPath), addNewLine=False)
        utilsOs.appendLineToFile(frLn, u'{0}sample.fr'.format(outputFolderPath), addNewLine=False)
        utilsOs.appendLineToFile(refLn, u'{0}sampleReference.Paths'.format(outputFolderPath), addNewLine=False)
        utilsOs.appendLineToFile(scLn, u'{0}scores.tsv'.format(outputFolderPath), addNewLine=False)
        print(1000000, rdmInd)
        print(11111111, scLn)
        print(enLn)
        print(frLn)
        print(refLn)
    return None

    # count the time the algorithm takes to run
startTime = utilsOs.countTime()

## extract naive heuristic detected random SPs
# extractMisalignedSP(b000path.getBtFolderPath(flagFolder=u'a'), extractionSize=100, typeOfExtractors=[0,1,2])
# extractMisalignedSP(b000path.getBtFolderPath(flagFolder=u'aq'), extractionSize=100, typeOfExtractors=[0,1,2])
# extractMisalignedSP(b000path.getBtFolderPath(flagFolder=u'q'), extractionSize=100, typeOfExtractors=[0,1,2])
### extractMisalignedSP(b000path.getBtFolderPath(flagFolder=u'n'), extractionSize=100, typeOfExtractors=[0,1,2])


## if we have already detected the SP, we just load them and randomly extract and dump
# for subsetName in [u'MISALIGNED', u'QUALITY', u'ALIGNMENT-QUALITY']:
#     extractedSp = utilsOs.openJsonFileAsDict(u'./003negativeNaiveExtractors/005extractedSp{0}.json'.format(subsetName))
#     randomlyExtractAndDumpHeuristicallyExtracted(extractedSp, extractionSize=100, subsetName=subsetName)


# if we already tuned the heuristics, applied them to the MC and now we wish to select random SPs to annotate them
paths = [u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/problematic/',
         u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/noProblematic/']
outFoldPaths = [u'/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/sampleSelection/problematic/',
                u'/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/sampleSelection/noProblematic/']
randomSPselectionForAnnotation(u'{0}extracted.en'.format(paths[0]), u'{0}extracted.fr'.format(paths[0]),
                               u'{0}reference.tsv'.format(paths[0]), u'{0}scores.tsv'.format(paths[0]),
                               outFoldPaths[0], nbSp=150)

# randomSPselectionForAnnotation(u'{0}extracted.en'.format(paths[1]), u'{0}extracted.fr'.format(paths[1]),
#                                u'{0}reference.tsv'.format(paths[1]), u'{0}scores.tsv'.format(paths[1]),
#                                outFoldPaths[1], nbSp=150)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))
