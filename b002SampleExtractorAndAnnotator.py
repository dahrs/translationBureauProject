#!/usr/bin/python
# -*- coding:utf-8 -*-

import re, math
from random import randint
import pandas as pd
import numpy as np

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import b000path, utilsOs, utilsString


########################################################################
# GENERAL TOOLS
########################################################################

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


########################################################################
# HEURISTICS
########################################################################

def getNbsAlone(tokList):
    finalList = []
    for tok in tokList:
        numbersIntok = utilsString.extractNumbersFromString(tok, digitByDigit=False)
        finalList += numbersIntok
    return finalList


def nbMismatch(stringSrc, stringTrgt, includeNumberNames=True, useEditDistance=True):
    """ given a string sentence pair, returns a score indicating how much a the
    numbers in the source appear in the target """
    # if it's not already tokenized
    if type(stringSrc) is str and type(stringTrgt) is str:
        stringSrc, stringTrgt = stringSrc.lower().replace(u' pm', u'pm'), stringTrgt.lower().replace(u' pm', u'pm')
        addSeparators = [u'.', u',', u':', u'/', u'-', u'h', u"''", u"'"]
        stringSrc = utilsString.nltkTokenizer(stringSrc, addSeparators)
        stringTrgt = utilsString.nltkTokenizer(stringTrgt, addSeparators)
    # transform all number names in actual numbers
    if includeNumberNames is True:
        stringSrcList = utilsString.transformNbNameToNb(stringSrc)
        stringTrgtList = utilsString.transformNbNameToNb(stringTrgt)
    # get the tokens containing a digit
    nbrs = re.compile(r'[0-9]')
    stringSrcList = [tok for tok in stringSrc if len(re.findall(nbrs, tok)) != 0]
    stringTrgtList = [tok for tok in stringTrgt if len(re.findall(nbrs, tok)) != 0]
    # if there were no numbers, return the max score (we can't use this heuristic to evaluate)
    if len(stringSrcList) + len(stringTrgtList) == 0:
        return 1.0
    # if we want to search for the exact same numbers
    if useEditDistance == False:
        # extract the figures from the tokens
        numbersInSrc = set(getNbsAlone(stringSrcList))
        numbersInTrgt = set(getNbsAlone(stringTrgtList))
        # if there were no numbers, return the max score (we can't use this heuristic to evaluate)
        if len(numbersInSrc) + len(numbersInTrgt) == 0:
            return 1.0
        # calculate the score of src-trgt coincidence
        nbIntersection = numbersInSrc.intersection(numbersInTrgt)
        print(1000, len(nbIntersection) / ((len(stringSrcList) + len(stringTrgtList)) / 2), nbIntersection)
        return len(nbIntersection) / ((len(numbersInSrc) + len(numbersInTrgt))/2)
    # if we want to use the edit distance to match the source digit tokens with the target ones
    else:
        nbIntersection = []
        # sort the digitfull src token list by decreasing length
        stringSrcList.sort(key=lambda tok: len(tok), reverse=True)
        # make a copy of the target list
        trgtList = stringTrgtList.copy()
        for srcTok in stringSrcList:
            # find the most similar trgt token
            mostSimil = [None, None, None, 1]
            for trgtInd, trgtTok in enumerate(trgtList):
                editDistScore = utilsString.getNormalizedEditDist(srcTok, trgtTok)
                # get the less distant in the trgt tokens
                if editDistScore < 0.5 and editDistScore < mostSimil[-1]:
                    mostSimil = [srcTok, trgtTok, trgtInd, editDistScore]
            # remove the most similar from the trgt list
            if mostSimil[0] is not None:
                del trgtList[mostSimil[-2]]
                nbIntersection.append(tuple(mostSimil[:2]))
        return len(nbIntersection) / ((len(stringSrcList)+len(stringTrgtList))/2)


def tooFewTokens(stringSrc, stringTrgt, nTokens=4):
    """ given a string sentence pair return 0 if there are less
    than N tokens on either the src or the trgt and return 1 otherwise """
    # if it's not already tokenized
    if type(stringSrc) is str and type(stringTrgt) is str:
        stringSrc, stringTrgt = stringSrc.lower(), stringTrgt.lower()
        addSeparators = [u'.', u',', u':', u'/', u'-', u"''", u"'"]
        stringSrc = utilsString.nltkTokenizer(stringSrc, addSeparators)
        stringTrgt = utilsString.nltkTokenizer(stringTrgt, addSeparators)
    # count the tokens
    if len(stringSrc) <= nTokens or len(stringTrgt) <= nTokens:
        return 0
    return 1


def tableOfContents(stringSrc, stringTrgt, nTokens=4, contextScores=None, placeInDocument=None):
    """ given a string sentence pair return a score of the ratio
    of small sentence pairs in the context of the current sp """
    # change the place in the doc to obtain low metric in the beginning and end of doc and a high one at the middle
    placeInDocument = math.sqrt(placeInDocument-(placeInDocument**2))*2
    # if it's not already tokenized
    if type(stringSrc) is str and type(stringTrgt) is str:
        stringSrc, stringTrgt = stringSrc.lower(), stringTrgt.lower()
        addSeparators = [u'.', u',', u':', u'/', u'-', u"''", u"'"]
        stringSrc = utilsString.nltkTokenizer(stringSrc, addSeparators)
        stringTrgt = utilsString.nltkTokenizer(stringTrgt, addSeparators)
    scores = [tooFewTokens(stringSrc, stringTrgt, nTokens)]
    # re make the token list a string so we can check the first characters
    origSrcString = u' '.join(stringSrc)
    if len(origSrcString) > 4:
        # if there is a number or a symbol indicating a table of contents at the start of the string
        extractedNmbrs = utilsString.extractNumbersFromString(origSrcString[:3])
        if len(extractedNmbrs) != 0 or u'-' in origSrcString[:3] or u'.' in origSrcString[:3]:
            scores.append(0)
        else:
            scores.append(1)
    # add the context to the current scores
    if contextScores is not None:
        scores = scores + contextScores
    # add the location of the sentence in the document to the current scores
    if placeInDocument is not None:
        scores = scores + [placeInDocument]
    return sum(scores) / len(scores)


def getNbLongLines(listOfSent, n=141):
    ''' returns the number of long lines that exceed n characters '''
    longLines = 0
    for sent in listOfSent:
        # make sure the sentence has no red keywords in it
        sent = sent.replace(u'\033[1;31m', u'').replace(u'\033[0m', u'')
        long = len(sent)
        while long > n:
            longLines += 1
            long -= n
    return longLines


def getCognates(tokensList, cognateSize):
    cognates = []
    for token in tokensList:
        if len(token) > cognateSize:
            cognates.append(token[:cognateSize])
    return cognates


def cognateCoincidence(stringSrc, stringTrgt, cognateSize=4):
    """ given a string sentence pair return the ratio of coincidence
     between the cognates (start of word char ngram) between source and target"""
    # if it's not already tokenized
    if type(stringSrc) is str and type(stringTrgt) is str:
        stringSrc, stringTrgt = stringSrc.lower(), stringTrgt.lower()
        addSeparators = [u'.', u',', u':', u'/', u'-', u"''", u"'"]
        stringSrc = utilsString.nltkTokenizer(stringSrc, addSeparators)
        stringTrgt = utilsString.nltkTokenizer(stringTrgt, addSeparators)
    # sort by decreasing length of the original word
    stringSrc.sort(key=lambda tok: len(tok), reverse=True)
    stringTrgt.sort(key=lambda tok: len(tok), reverse=True)
    # compile the cognates of each token for the source and target
    srcCognates = getCognates(stringSrc, cognateSize)
    trgtCognates = set(getCognates(stringTrgt, cognateSize))
    # get intersection of cognates
    intersection = [cog for cog in srcCognates if cog in trgtCognates]
    smallerLength = min(len(srcCognates), len(trgtCognates))
    if smallerLength == 0:
        return 0
    return len(intersection)/smallerLength


def applyExtractor(extractFunct, maxAllowedScore, srcTokens, trgtTokens,
                   extractedSp, filePath, extractorType, srcLnIndex, **kwargs):
    """ given an extractor it applies it and if needed, saves the ref in the dict """
    # application of extractor
    score = extractFunct(srcTokens, trgtTokens, **kwargs)
    if score < maxAllowedScore:
        return addToDict(extractedSp, filePath, srcLnIndex, extractorType), score
    return extractedSp, score


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


def getRandomIndex(iterableObj):
    # if there is no element in the dict
    if len(iterableObj) == 0:
        return None
    # if there is only one element in the dict
    elif len(iterableObj) == 1:
        rdmIndex = 0
    else:
        # randomly select an index
        rdmIndex = randint(0, len(iterableObj) - 1)
    return rdmIndex


def randomlyExtractAndDump(extractedSp, extractionSize, subsetName):
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


def getContextScores(srcLnIndex, srcLines, trgtLines):
    pre0 = 1 if srcLnIndex < 2 else tooFewTokens(srcLines[srcLnIndex - 2], trgtLines[srcLnIndex - 2])
    pre1 = 1 if srcLnIndex < 1 else tooFewTokens(srcLines[srcLnIndex - 1], trgtLines[srcLnIndex - 1])
    post0 = 1 if srcLnIndex >= (len(srcLines)-1) else tooFewTokens(srcLines[srcLnIndex + 1], trgtLines[srcLnIndex + 1])
    post1 = 1 if srcLnIndex >= (len(srcLines)-2) else tooFewTokens(srcLines[srcLnIndex + 2], trgtLines[srcLnIndex + 2])
    return [pre0, pre1, post0, post1]


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
    utilsOs.dumpDictToJsonFile(extractedSp, pathOutputFile=u'./003negativeNaiveExtractors/000extractedSp.json', overwrite=True)
    # randomly extract and dump the file path and the line index for the extracted SP
    randomlyExtractAndDump(extractedSp, 100, subsetName)


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


########################################################################
# ANNOTATION
########################################################################

def annotateFirstSP(beforeSentSource, duringSentSource, beforeSentTarget, duringSentTarget, listOfAnnotations, lineLength):
    """ """
    # color in red the during lines
    redBeforeSource = u'\033[1;31m{0}\033[0m'.format(beforeSentSource)
    redBeforeTarget = u'\033[1;31m{0}\033[0m'.format(beforeSentTarget)
    # print the sentences
    print(u'0 - {0}'.format(redBeforeSource))
    print(u'0 - {0}'.format(redBeforeTarget))
    print(u'1 - {0}'.format(duringSentSource))
    print(u'1 - {0}'.format(duringSentTarget))
    print()
    # count if the lines that take the space of 2 lines
    longLines = getNbLongLines([beforeSentSource, beforeSentTarget, duringSentSource, duringSentTarget], lineLength)
    # get the first part of the annotation (aligned or not)
    annotatorGeneralInput = input(u'Aligned-Misaligned annotation: ')
    # make sure to have the right general annotation
    while True:
        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2', u'0.3', u'1.0', u'1.1']:
            break
        else:
            utilsOs.moveUpAndLeftNLines(1, slowly=False)
            annotatorGeneralInput = input(u'Repeat annotation: ')
    # if we still need to specify what type of alignment or misalignment
    if annotatorGeneralInput in [u'0', u'1']:
        utilsOs.moveUpAndLeftNLines(1, slowly=False)
        # get the second part of the annotation (aligned or not)
        annotatorSpecificInput = input(u'Specific type annotation: ')
        typeAnswers = [u'0', u'1', u'2', u'3'] if annotatorGeneralInput == 0 else [u'0', u'1']
        # make sure to have the right specific annotation
        while True:
            if annotatorSpecificInput in typeAnswers:
                break
            else:
                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                annotatorSpecificInput = input(u'Repeat type annotation: ')
        # save to the list of annotations
        listOfAnnotations.append(float(u'{0}.{1}'.format(annotatorGeneralInput, annotatorSpecificInput)))
    # if the right answer was given in the right format right away
    else:
        # save to the list of annotations
        listOfAnnotations.append(float(annotatorGeneralInput))
    # remove the lines from the terminal before getting to the next pair
    utilsOs.moveUpAndLeftNLines(10, slowly=False)
    # erase all remainder of the previous sentences and go back up again
    for e in range(10 + longLines):
        print(u' ' * (lineLength-1))
    utilsOs.moveUpAndLeftNLines(10 + longLines, slowly=False)
    return listOfAnnotations


def correctionToAnnotation(listOfAnnotations):
    """ given a list of the annotations, asks the user which to correct and correct by what """
    utilsOs.moveUpAndLeftNLines(1, slowly=False)
    indexAnnotation = input(u'Give the index of the annotation : ')
    # make sure to have the right index
    while True:
        try:
            indexAnnotation = int(indexAnnotation)
            if indexAnnotation < len(listOfAnnotations):
                break
            else:
                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                indexAnnotation = input(u'Index out of bounds. Repeat : ')
        except ValueError:
            utilsOs.moveUpAndLeftNLines(1, slowly=False)
            indexAnnotation = input(u'Index given is not integral. Repeat : ')
    # get the new annotation element
    utilsOs.moveUpAndLeftNLines(1, slowly=False)
    annotatorGeneralInput = input(u"Old annotation is '{0}'. Give new annotation : ".format(listOfAnnotations[indexAnnotation]))
    # make sure to have the right general annotation
    while True:
        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2', u'0.3', u'1.0', u'1.1']:
            break
        else:
            utilsOs.moveUpAndLeftNLines(1, slowly=False)
            annotatorGeneralInput = input(u'Repeat annotation: ')
    # if we still need to specify what type of alignment or misalignment
    if annotatorGeneralInput in [u'0', u'1']:
        utilsOs.moveUpAndLeftNLines(1, slowly=False)
        # get the second part of the annotation (aligned or not)
        annotatorSpecificInput = input(u'Specific type annotation: ')
        typeAnswers = [u'0', u'1', u'2', u'3'] if annotatorGeneralInput == 0 else [u'0', u'1']
        # make sure to have the right specific annotation
        while True:
            if annotatorSpecificInput in typeAnswers:
                break
            else:
                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                annotatorSpecificInput = input(u'Repeat type annotation: ')
        # make the replacement
        listOfAnnotations[indexAnnotation] = float(u'{0}.{1}'.format(annotatorGeneralInput, annotatorSpecificInput))
    # if the right answer was given in the right format right away
    else:
       # make the replacement
       listOfAnnotations[indexAnnotation] = float(annotatorGeneralInput)
   # get back to the standard annotation
    utilsOs.moveUpAndLeftNLines(1, slowly=False)
    annotatorGeneralInput = input(u'Correctly replaced. Back to current annotation : ')
    if annotatorGeneralInput in [u'c', u'correct']:
        annotatorGeneralInput, listOfAnnotations = correctionToAnnotation(listOfAnnotations)
    return annotatorGeneralInput, listOfAnnotations


def annotateFiles(listOfFilesPath=None, annotatedOutputFolder=u'./002manuallyAnnotated/', dumpSP=True):
    """ given a list of paths, manually show and annotate the sentence pairs """
    referencePathLine = []
    listOfAnnotations = []
    # get the list containing the file paths
    if listOfFilesPath is None:
        listOfFilesPath = randomlySelectNDocsFromPath(b000path.getBtFolderPath(flagFolder=None), n=100)
        makeLocalFolderPaths(listOfFilesPath)
    elif type(listOfFilesPath) is str:
        if u'.json' in listOfFilesPath:
            listOfFilesPath = utilsOs.openJsonFileAsDict(listOfFilesPath)
        else:
            listOfFilesPath = [listOfFilesPath]
    # get rid of the files we have already annotated
    if utilsOs.theFileExists(u'{0}sampleReference.tsv'.format(annotatedOutputFolder)):
        refLines = utilsOs.readAllLinesFromFile(u'{0}sampleReference.tsv'.format(annotatedOutputFolder),
                                                noNewLineChar=True)
        annotatedFiles = set([line.split(u'\t')[0] for line in refLines])
        listOfFilesPath = [file for file in listOfFilesPath if file not in annotatedFiles]
    # print the annotator cheat sheet
    print(""""0 - badly aligned
        \n\t0.0 - AMPLIFICATION: compensation, description, repetition or lang tendency to hypergraphy
        \n\t0.1 - ELISION: absence, omission, reduction or lang tendency to micrography
        \n\t0.2 - DISPLACEMENT: modification of the line order also modifying the order of the following lines
        \n\t0.3 - MISALIGNED and FOIBLE: alignment and quality errors
        \n1 - well aligned
        \n\t1.0 - ALIGNED and GOOD QUALITY: is aligned and shows no evident sing of translation imperfections 
        \n\t1.1 - FOIBLE: imperfection in the translation quality""")
    # open each file in EN and FR and show it in the terminal
    for filePath in listOfFilesPath:
        print(u'############# {0} ##############'.format(filePath.replace(u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/', u'')))
        # get the path for the source and target
        fileSourcePath = u'{0}.fr'.format(filePath) if u'fr-en' in filePath else u'{0}.en'.format(filePath)
        fileTargetPath = u'{0}.en'.format(filePath) if u'fr-en' in filePath else u'{0}.fr'.format(filePath)
        with open(fileSourcePath) as fileSource:
            with open(fileTargetPath) as fileTarget:
                # show the context of the annotated sentence
                beforeSentSource = fileSource.readline()
                duringSentSource = fileSource.readline()
                beforeSentTarget = fileTarget.readline()
                duringSentTarget = fileTarget.readline()
                # annotate the first sentence pair
                listOfAnnotations = annotateFirstSP(beforeSentSource, duringSentSource, beforeSentTarget,
                                                    duringSentTarget, listOfAnnotations, lineLength=137)
                # save the reference
                # if the filepath is the reference
                if u'burtrad' in filePath:
                    referencePathLine.append(u'{0}\t{1}'.format(filePath, 0))
                # otherwise we get it from a reference file
                else:
                    with open(u'{0}.tsv'.format(filePath)) as refFile:
                        refLns = [ln.replace(u'\n', u'') for ln in refFile.readlines()]
                    referencePathLine.append(refLns[0])
                # dump the first SP
                if dumpSP is True:
                    enSent = beforeSentSource if u'.en' in fileSourcePath else beforeSentTarget
                    frSent = beforeSentTarget if u'.en' in fileSourcePath else beforeSentSource
                    utilsOs.appendLineToFile(enSent, u'{0}sample.en'.format(annotatedOutputFolder), addNewLine=False)
                    utilsOs.appendLineToFile(frSent, u'{0}sample.fr'.format(annotatedOutputFolder), addNewLine=False)
                duringIndex = 1
                # for each line
                while duringSentSource or duringSentTarget:
                    # get the correct terminal line length
                    lineLength = 137-len(str(len(listOfAnnotations)+1))
                    # get the sentences
                    afterSentSource = fileSource.readline()
                    afterSentTarget = fileTarget.readline()
                    # color in red the during lines
                    redDuringSource = u'\033[1;31m{0}\033[0m'.format(duringSentSource)
                    redDuringTarget = u'\033[1;31m{0}\033[0m'.format(duringSentTarget)
                    # print the sentences
                    print(u'{0} - {1}'.format(len(listOfAnnotations)-1, beforeSentSource))
                    print(u'{0} - {1}'.format(len(listOfAnnotations)-1, beforeSentTarget))
                    print(u'{0} - {1}'.format(len(listOfAnnotations), redDuringSource))
                    print(u'{0} - {1}'.format(len(listOfAnnotations), redDuringTarget))
                    print(u'{0} - {1}'.format(len(listOfAnnotations)+1, afterSentSource))
                    print(u'{0} - {1}'.format(len(listOfAnnotations)+1, afterSentTarget))
                    print()
                    # count if the lines that take the space of 2 lines
                    longLines = getNbLongLines([beforeSentSource, beforeSentTarget, duringSentSource,
                                                duringSentTarget, afterSentSource, afterSentTarget], lineLength)
                    # get the first part of the annotation (aligned or not)
                    annotatorGeneralInput = input(u'Aligned-Misaligned annotation: ')
                    # make sure to have the right general annotation
                    while True:
                        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2', u'0.3', u'1.0', u'1.1', u'c', u'correct']:
                            break
                        else:
                            utilsOs.moveUpAndLeftNLines(1, slowly=False)
                            annotatorGeneralInput = input(u'Repeat annotation: ')
                    if annotatorGeneralInput in [u'c', u'correct']:
                        annotatorGeneralInput, listOfAnnotations = correctionToAnnotation(listOfAnnotations)
                    # if we still need to specify what type of alignment or misalignment
                    if annotatorGeneralInput in [u'0', u'1']:
                        utilsOs.moveUpAndLeftNLines(1, slowly=False)
                        # get the second part of the annotation (aligned or not)
                        annotatorSpecificInput = input(u'Specific type annotation: ')
                        typeAnswers = [u'0', u'1', u'2', u'3'] if annotatorGeneralInput == 0 else [u'0', u'1']
                        # make sure to have the right specific annotation
                        while True:
                            if annotatorSpecificInput in typeAnswers:
                                break
                            else:
                                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                                annotatorSpecificInput = input(u'Repeat type annotation: ')
                        # save to the list of annotations
                        listOfAnnotations.append(float(u'{0}.{1}'.format(annotatorGeneralInput, annotatorSpecificInput)))
                    # if the right answer was given in the right format right away
                    else:
                        # save to the list of annotations
                        listOfAnnotations.append(float(annotatorGeneralInput))
                    # remove the lines from the terminal before getting to the next pair
                    utilsOs.moveUpAndLeftNLines(14+longLines, slowly=False)
                    # erase all remainder of the previous sentences and go back up again
                    for e in range(14+longLines):
                        print(u' '*(lineLength+4))
                    utilsOs.moveUpAndLeftNLines(14 + longLines, slowly=False)
                    # next line source
                    beforeSentSource = duringSentSource
                    duringSentSource = afterSentSource
                    # next line target
                    beforeSentTarget = duringSentTarget
                    duringSentTarget = afterSentTarget
                    # append the reference to the file
                    # if the filepath is the reference
                    if u'burtrad' in filePath:
                        referencePathLine.append(u'{0}\t{1}'.format(filePath, duringIndex))
                    # otherwise we get it from a reference file
                    else:
                        with open(u'{0}.tsv'.format(filePath)) as refFile:
                            refLns = [ln.replace(u'\n', u'') for ln in refFile.readlines()]
                        referencePathLine.append(refLns[duringIndex])
                    # add 1 to index
                    duringIndex += 1
                    # dump the file line by line, to be sure in case of error
                    # dump the reference
                    utilsOs.dumpRawLines(referencePathLine, u'{0}sampleReference.tsv'.format(annotatedOutputFolder),
                                         addNewline=True, rewrite=True)
                    # dump the annotation
                    utilsOs.dumpRawLines(listOfAnnotations, u'{0}sampleAnnotation.tsv'.format(annotatedOutputFolder),
                                         addNewline=True, rewrite=True)
                    # dump the SP
                    if dumpSP is True:
                        enSent = beforeSentSource if u'.en' in fileSourcePath else beforeSentTarget
                        frSent = beforeSentTarget if u'.en' in fileSourcePath else beforeSentSource
                        utilsOs.appendLineToFile(enSent, u'{0}sample.en'.format(annotatedOutputFolder), addNewLine=False)
                        utilsOs.appendLineToFile(frSent, u'{0}sample.fr'.format(annotatedOutputFolder), addNewLine=False)
        # clear part of terminal
        utilsOs.moveUpAndLeftNLines(2, slowly=False)


def mergeAnnotatedFiles(pathToPrimary, pathOrListOfPathsToSecondary):
    # get the path to the primary folder
    def dividePaths(pathAnnotFile):
        if u'sampleAnnotation.tsv' in pathAnnotFile:
            pathFolder = pathAnnotFile.replace(u'sampleAnnotation.tsv', u'')
        else:
            pathFolder = pathAnnotFile
            pathAnnotFile = u'{0}sampleAnnotation.tsv'.format(pathAnnotFile)
        return pathAnnotFile, pathFolder
    pathToPrimary, primaryFolder = dividePaths(pathToPrimary)
    # make secondary a list if it is string
    if type(pathOrListOfPathsToSecondary) is str:
        pathOrListOfPathsToSecondary = [pathOrListOfPathsToSecondary]
    # open primary
    primaryRefPath = u'{0}sampleReference.tsv'.format(primaryFolder)
    primaryAnnotDf, primaryRefDf = utilsOs.getDataFrameFromArgs(pathToPrimary, primaryRefPath, header=False)
    primaryEnPath = u'{0}sample.en'.format(primaryFolder)
    primaryFrPath = u'{0}sample.fr'.format(primaryFolder)
    primaryEnDf, primaryFrDf = utilsOs.getDataFrameFromArgs(primaryEnPath, primaryFrPath, header=False)
    # open the secondaries and merge
    for secondaryPath in pathOrListOfPathsToSecondary:
        pathToSec, secFolder = dividePaths(secondaryPath)
        # open secondary dataframe
        secAnnotDf, secRefDf = utilsOs.getDataFrameFromArgs(pathToSec,
                                                                    u'{0}sampleReference.tsv'.format(secFolder),
                                                                    header=False)
        secEnDf, secFrDf = utilsOs.getDataFrameFromArgs(u'{0}sample.en'.format(secFolder),
                                                                u'{0}sample.fr'.format(secFolder),
                                                               header=False)
        # concatenate the primary with the secondary
        primaryAnnotDf = utilsOs.concatenateDfsOrSeries([primaryAnnotDf, secAnnotDf])
        primaryRefDf = utilsOs.concatenateDfsOrSeries([primaryRefDf, secRefDf])
        primaryEnDf = utilsOs.concatenateDfsOrSeries([primaryEnDf, secEnDf])
        primaryFrDf = utilsOs.concatenateDfsOrSeries([primaryFrDf, secFrDf])
    # dump in the primary's path
    utilsOs.dumpDataFrame(primaryAnnotDf, pathToPrimary, header=False)
    utilsOs.dumpDataFrame(primaryRefDf, primaryRefPath, header=False)
    utilsOs.dumpDataFrame(primaryEnDf, primaryEnPath, header=False)
    utilsOs.dumpDataFrame(primaryFrDf, primaryFrPath, header=False)


########################################################################
# QUALITY VERIFICATION
########################################################################

def populateConfMatrix(pred, real, confMatrix=[]):
    if len(confMatrix) == 0:
        content = np.zeros(shape=(2,2))
        confMatrix = pd.DataFrame(content, index=[u'pred pos', u'pred neg'], columns=[u'real pos', u'real neg'])
    if pred == real:
        if pred == False:
            # true negative
            confMatrix[u'real neg'][u'pred neg'] += 1
        else:
            # true positive
            confMatrix[u'real pos'][u'pred pos'] += 1
    else:
        if pred == False:
            # false negative
            confMatrix[u'real pos'][u'pred neg'] += 1
        else:
            # false positive
            confMatrix[u'real neg'][u'pred pos'] += 1
    return confMatrix


def printPrecisionRecallAccuracy(confMatrix):
    precision = confMatrix[u'real pos'][u'pred pos'] / (confMatrix[u'real pos'][u'pred pos']+confMatrix[u'real pos'][u'pred neg'])
    recall = confMatrix[u'real pos'][u'pred pos'] / (confMatrix[u'real pos'][u'pred pos']+confMatrix[u'real neg'][u'pred pos'])
    accuracy = (confMatrix[u'real pos'][u'pred pos']+confMatrix[u'real neg'][u'pred neg']) / (confMatrix[u'real pos'][u'pred pos']+confMatrix[u'real neg'][u'pred neg']+confMatrix[u'real pos'][u'pred neg']+confMatrix[u'real neg'][u'pred pos'])
    f1 = 2 * ((precision*recall)/(precision+recall))
    print(u'PRECISION : ', precision)
    print(u'RECALL : ', recall)
    print(u'F1 : ', f1)
    print(u'ACCURACY : ', accuracy)


def getAnnotationScore(manualAnnotationString, focus=u'qa'):
    """ matches the multidimensional manual annotation to a
     boolean annotation depending on the desired focus:
     * returns True for
        - a: good alignment
        - q: good quality
        - qa: good alignment and quality
        - qora: good alignment OR good quality"""
    # verify the string nature of the annotation
    if type(manualAnnotationString) is float:
        manualAnnotationString = str(manualAnnotationString)
    elif type(manualAnnotationString) is int:
        manualAnnotationString = str(int(manualAnnotationString))
    # if there was a formatting error and the 1.0 became 1
    elif type(manualAnnotationString) is str and manualAnnotationString == u'1':
        manualAnnotationString = u'1.0'
    # get the right score
    if focus == u'qa':
        return True if u'1.0' in manualAnnotationString else False
    elif focus == u'a':
        return True if u'1.' in manualAnnotationString else False
    elif focus == u'q':
        for badQualSc in [u'0.3', u'1.1']:
            if badQualSc in manualAnnotationString:
                return False
        return True
    elif focus == u'qora':
        return False if u'1.1' in manualAnnotationString else True


def checkExtractorsAgainstAnnotatedCorpusFile(annotationFolderPath):
    """ given the path to an annotated corpus, it checks if the extractors correspond to the annotation """
    confMatrix0, confMatrix1, confMatrix2, confMatrixAll = [], [], [], []
    temp0, temp1, temp2 = 0, 0, 0
    # get the file paths
    annotationFilePath = u'{0}sampleAnnotation.tsv'.format(annotationFolderPath)
    referenceFilePath = u'{0}sampleReference.tsv'.format(annotationFolderPath)
    with open(referenceFilePath) as referenceFile:
        referenceLines = referenceFile.readlines()
        with open(annotationFilePath) as annotationFile:
            annotationLines = annotationFile.readlines()
            # get the lines
            for index, refLine in enumerate(referenceLines):
                refLineList = (refLine.replace(u'\n', '')).split(u'\t')
                refPath = refLineList[0]
                refIndex = int(refLineList[1])
                # get the original source and target lines
                srcFilePath = u'{0}.en'.format(refPath) if u'en-fr' in refPath else u'{0}.fr'.format(refPath)
                trgtFilePath = u'{0}.fr'.format(refPath) if u'en-fr' in refPath else u'{0}.en'.format(refPath)
                with open(srcFilePath) as srcFile:
                    srcLines = srcFile.readlines()
                with open(trgtFilePath) as trgtFile:
                    trgtLines = trgtFile.readlines()
                # get the human annotation
                annot = annotationLines[index]
                # get the src-trgt lines
                srcLn = srcLines[refIndex].replace(u'\n', u'')
                trgtLn = trgtLines[refIndex].replace(u'\n', u'')
                # annotation score
                annotScore = getAnnotationScore(annot, focus=u'a')
                # number coincidence
                score0 = nbMismatch(srcLn, trgtLn)
                score0 = False if score0 < 0.75 else True
                confMatrix0 = populateConfMatrix(score0, annotScore, confMatrix0)
                # too few words
                cntxtScores = getContextScores(refIndex, srcLines, trgtLines)
                docLoc = refIndex / len(srcLines)
                score1 = tableOfContents(srcLn, trgtLn, nTokens=4,
                                         contextScores=cntxtScores, placeInDocument=docLoc)
                score1 = False if score1 < 0.32 else True
                confMatrix1 = populateConfMatrix(score1, annotScore, confMatrix1)
                # cognates
                score2 = cognateCoincidence(srcLn, trgtLn)
                score2 = False if score2 < 0.1 else True
                confMatrix2 = populateConfMatrix(score2, annotScore, confMatrix2)
                # all together
                scoreAll = False if sum([1 for e in [score0, score1, score2] if e is True]) < 2 else True
                confMatrixAll = populateConfMatrix(scoreAll, annotScore, confMatrixAll)
    print(u'NUMBER COINCIDENCE')
    print(confMatrix0)
    printPrecisionRecallAccuracy(confMatrix0)
    print()
    print(u'TOO FEW TOK')
    print(confMatrix1)
    printPrecisionRecallAccuracy(confMatrix1)
    print()
    print(u'COGNATES COINCIDENCE')
    print(confMatrix2)
    printPrecisionRecallAccuracy(confMatrix2)
    print()
    print(u'ALL MIXED')
    print(confMatrixAll)
    printPrecisionRecallAccuracy(confMatrixAll)


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# annotate the SP
# listOfFilesPath = u'./randomSelected100MISALIGNED.json'
# annotateFiles(listOfFilesPath, anotatedOutputFolder=u'./002manuallyAnnotated/')


# extract naive heuristic detected random SPs
# extractMisalignedSP(b000path.getBtFolderPath(flagFolder=u'a'), extractionSize=100, typeOfExtractors=[0,1,2])
# extractMisalignedSP(b000path.getBtFolderPath(flagFolder=u'aq'), extractionSize=100, typeOfExtractors=[0,1,2])
# extractMisalignedSP(b000path.getBtFolderPath(flagFolder=u'q'), extractionSize=100, typeOfExtractors=[0,1,2])
# extractMisalignedSP(b000path.getBtFolderPath(flagFolder=u'n'), extractionSize=100, typeOfExtractors=[0,1,2])


# annotate the randomly extracted misaligned SPs
# listOfPaths = [u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/MISALIGNED',
#                u'./003negativeNaiveExtractors/fewTokens/random100few/MISALIGNED',
#                u'./003negativeNaiveExtractors/cognates/random100cog/MISALIGNED',
#                u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/QUALITY',
#                u'./003negativeNaiveExtractors/fewTokens/random100few/QUALITY',
#                u'./003negativeNaiveExtractors/cognates/random100cog/QUALITY',
#                u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/ALIGNMENT-QUALITY',
#                u'./003negativeNaiveExtractors/fewTokens/random100few/ALIGNMENT-QUALITY',
#                u'./003negativeNaiveExtractors/cognates/random100cog/ALIGNMENT-QUALITY']
# annotateFiles(listOfFilesPath=listOfPaths, annotatedOutputFolder=u'./003negativeNaiveExtractors/')

# mergeAnnotatedFiles(u'./002manuallyAnnotated/sampleAnnotation.tsv', u'./003negativeNaiveExtractors/')


# check the extractors on the annotated corpus
checkExtractorsAgainstAnnotatedCorpusFile(u'./002manuallyAnnotated/')


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))