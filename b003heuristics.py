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
# HEURISTICS
########################################################################


def addToDict(extractedSp, filePath, index, extrType=0):
    if filePath not in extractedSp[extrType]:
        extractedSp[extrType][filePath] = [index]
    else:
        extractedSp[extrType][filePath].append(index)
    return extractedSp


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


def getContextScores(srcLnIndex, srcLines, trgtLines):
    pre0 = 1 if srcLnIndex < 2 else tooFewTokens(srcLines[srcLnIndex - 2], trgtLines[srcLnIndex - 2])
    pre1 = 1 if srcLnIndex < 1 else tooFewTokens(srcLines[srcLnIndex - 1], trgtLines[srcLnIndex - 1])
    post0 = 1 if srcLnIndex >= (len(srcLines)-1) else tooFewTokens(srcLines[srcLnIndex + 1], trgtLines[srcLnIndex + 1])
    post1 = 1 if srcLnIndex >= (len(srcLines)-2) else tooFewTokens(srcLines[srcLnIndex + 2], trgtLines[srcLnIndex + 2])
    return [pre0, pre1, post0, post1]