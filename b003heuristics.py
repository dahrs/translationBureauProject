#!/usr/bin/python
# -*- coding:utf-8 -*-

import re, math

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import b000path, utilsOs, utilsString, utilsML
from collections import Counter
import numpy as np
from sklearn import preprocessing
import torch.tensor as tensor
import torch.nn as nn
import torch


########################################################################
# HEURISTIC TOOLS
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


def heuristTokenize(string1, string2, addSeparators=[u'.', u'?', u'!', u',', u':', u'/', u'-', u"''", u"'", u"%"]):
    # tokenize if not already
    if type(string1) is str:
        string1 = string1.lower()
        string1 = utilsString.nltkTokenizer(string1, addSeparators)
    if type(string2) is str:
        string2 = string2.lower()
        string2 = utilsString.nltkTokenizer(string2, addSeparators)
    return string1, string2


def tableOfContentStart(aString, separateNbAndSymbScores=False):
    # if there is a number or a symbol indicating a table of contents at the start of the string
    extractedNmbrs = utilsString.extractNumbersFromString(aString[:3])
    if separateNbAndSymbScores is False:
        strStart = aString[:3]
        if len(extractedNmbrs) != 0 or u'-' in strStart or u'.' in strStart or u'*' in strStart or u'•' in strStart:
            return [0]
        else:
            return [1]
    # separate the number and the symbol appearance scores
    strStart = aString[:5]
    scrs = []
    if len(extractedNmbrs) != 0 :
        scrs.append(0)
    else:
        scrs.append(1)
    if u'-' in strStart or u'.' in strStart or u'*' in strStart or u'•' in strStart:
        scrs.append(0)
    else:
        scrs.append(1)
    return scrs


def makeListIntersection(iterElem1, iterElem2):
    return list((Counter(iterElem1) & Counter(iterElem2)).elements())


def isCharNgramGibberish(charTrigram):
    """ returns a boolean indicating the presence of non-alphanumeric (+ space) characters in the character-ngram
    TRUE means more than 2/3 of the chars in the trigram are non-alphanumeric"""
    # if the trigram is a repetition of the same char trice, it's possibly gibberish
    if charTrigram == charTrigram[0]*3:
        return True
    # measure the number of potential gibberish characters
    gibbScore = 0.0
    for char in charTrigram:
        if utilsString.isItAlphaNumeric(char) is False:
            gibbScore += 1.0
    # if there is 1 or more not alphanumeric character in the trigram, the trigram is classified as gibberish
    if gibbScore >= 1:
        return True
    return False


########################################################################
# HEURISTICS
########################################################################

def nbMismatch(stringSrc, stringTrgt, includeNumberNames=True, useEditDistance=True, addInfo=False):
    """ given a string sentence pair, returns a score indicating how much the
    numbers in the source appear in the target """
    # if it's not already tokenized
    addSeparators = [u'.', u',', u':', u'/', u'-', u"''", u"'"]
    if type(stringSrc) is str:
        stringSrc = stringSrc.lower().replace(u' pm', u'pm')
        stringSrc = utilsString.nltkTokenizer(stringSrc, addSeparators)
    if type(stringTrgt) is str:
        stringTrgt = stringTrgt.lower().replace(u' pm', u'pm')
        stringTrgt = utilsString.nltkTokenizer(stringTrgt, addSeparators)
    # transform all number names in actual numbers
    if includeNumberNames is True:
        stringSrc = utilsString.transformNbNameToNb(stringSrc)
        stringTrgt = utilsString.transformNbNameToNb(stringTrgt)
    # get the tokens containing a digit
    nbrs = re.compile(r'[0-9]')
    stringSrcList = [tok for tok in stringSrc if len(re.findall(nbrs, tok)) != 0]
    stringTrgtList = [tok for tok in stringTrgt if len(re.findall(nbrs, tok)) != 0]
    # if there were no numbers, return silence
    if len(stringSrcList) + len(stringTrgtList) == 0:
        if addInfo is False:
            return None
        return None, 0, 0, 0
    # if we want to search for the exact same numbers
    elif useEditDistance == False:
        # extract the figures from the tokens
        numbersInSrc = set(getNbsAlone(stringSrcList))
        numbersInTrgt = set(getNbsAlone(stringTrgtList))
        # calculate the score of src-trgt coincidence
        nbIntersection = numbersInSrc.intersection(numbersInTrgt)
        print(1000, len(nbIntersection) / ((len(stringSrcList) + len(stringTrgtList)) / 2), nbIntersection)
        sc = len(nbIntersection) / ((len(numbersInSrc) + len(numbersInTrgt))/2)
        if addInfo is False:
            return sc
        return sc, len(nbIntersection), len(numbersInSrc), len(numbersInTrgt)
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
        sc = len(nbIntersection) / ((len(stringSrcList)+len(stringTrgtList))/2)
        if addInfo is False:
            return sc
        return sc, len(nbIntersection), len(stringSrcList), len(stringTrgtList)


def tooFewTokens(stringSrc, stringTrgt=None, nTokens=4):
    """ given a string sentence pair return 0 if there are less
    than N tokens on either the src or the trgt and return 1 otherwise """
    # if it's not already tokenized
    stringSrc, stringTrgt = heuristTokenize(stringSrc, stringTrgt)
    # count the tokens
    if stringTrgt != None:
        if len(stringSrc) <= nTokens or len(stringTrgt) <= nTokens:
            return 0
        return 1
    score = 0 if len(stringSrc) <= nTokens else 1
    return score


def tableOfContents(stringSrc, stringTrgt, nTokens=4, contextScores=None, placeInDocument=None, addInfo=False):
    """ given a string sentence pair return a score of the ratio
    of small sentence pairs in the context of the current sp """
    # if it's not already tokenized
    stringSrc, stringTrgt = heuristTokenize(stringSrc, stringTrgt)
    # get scores
    scores = [tooFewTokens(stringSrc, stringTrgt, nTokens)]
    # re make the token list a string so we can check the first characters
    origSrcString = u' '.join(stringSrc)
    origTrgtString = u' '.join(stringTrgt)
    # if the string is longer than 4 char
    if len(origSrcString) > 4:
        # if there is a number or a symbol indicating a table of contents at the start of the string
        scores += tableOfContentStart(origSrcString)
    # add the context to the current scores
    if contextScores is not None:
        scores = scores + contextScores
    # add the location of the sentence in the document to the current scores
    if placeInDocument is not None:
        # change the place in the doc to obtain low metric in the beginning and end of doc and a high one at the middle
        placeInDocument = math.sqrt(placeInDocument - (placeInDocument ** 2)) * 2
        scores = scores + [placeInDocument]
    if addInfo == False:
        return sum(scores) / len(scores)
    return sum(scores)/len(scores), sum(scores), len(scores)


def tableOfContentsMismatch(stringSrc, stringTrgt, nTokens=4, addInfo=False):
    """ given a string sentence pair return a score of the probability
    that one of the sentences is a table of content and the other not
    0.0 : one is and the other not
    1.0 : they are both table of contents of neither of them are"""
    # if it's not already tokenized
    stringSrc, stringTrgt = heuristTokenize(stringSrc, stringTrgt)
    # get scores
    scoresSrc = [tooFewTokens(stringSrc, nTokens=nTokens)]
    scoresTrgt = [tooFewTokens(stringTrgt, nTokens=nTokens)]
    # re make the token list a string so we can check the first characters
    origSrcString = u' '.join(stringSrc)
    origTrgtString = u' '.join(stringTrgt)
    # if the string is longer than 4 char
    if len(origSrcString) > 4:
        # if there is a number or a symbol indicating a table of contents at the start of the string
        scoresSrc += tableOfContentStart(origSrcString, separateNbAndSymbScores=True)
    if len(origTrgtString) > 4:
        # if there is a number or a symbol indicating a table of contents at the start of the string
        scoresTrgt += tableOfContentStart(origTrgtString, separateNbAndSymbScores=True)
    # calculate the difference between the src and target scores
    scSrc = float(sum(scoresSrc)) / float(len(scoresSrc))
    scTrgt = float(sum(scoresTrgt)) / float(len(scoresTrgt))
    # if return the score difference between them, 0.0 = they are very different and 1.0 = they are exactly alike
    if addInfo == False:
        return 1.0 - abs(scSrc-scTrgt)
    return 1.0 - abs(scSrc-scTrgt), sum(scoresSrc), sum(scoresTrgt), len(scoresSrc), len(scoresTrgt)


def cognateCoincidence(stringSrc, stringTrgt, cognateSize=4, addInfo=False):
    """ given a string sentence pair return the ratio of coincidence
     between the cognates (start of word char ngram) between source and target"""
    # if it's not already tokenized
    stringSrc, stringTrgt = heuristTokenize(stringSrc, stringTrgt)
    # sort by decreasing length of the original word
    stringSrc.sort(key=lambda tok: len(tok), reverse=True)
    stringTrgt.sort(key=lambda tok: len(tok), reverse=True)
    # compile the cognates of each token for the source and target
    srcCognates = getCognates(stringSrc, cognateSize)
    trgtCognates = set(getCognates(stringTrgt, cognateSize))
    # get intersection of cognates
    intersection = [cog for cog in srcCognates if cog in trgtCognates]
    # if there is nothing in the intersection, return silence, we can't infer anything
    if len(intersection) == 0 :
        if addInfo is False:
            return None
        return None, len(intersection), len(srcCognates), len(trgtCognates)
    smallerLength = min(len(srcCognates), len(trgtCognates))
    # if there are no cognates to be found in at least one of the sentences
    if smallerLength == 0:
        if addInfo is False:
            return None, len(intersection), len(srcCognates), len(trgtCognates)
        return 0
    # if there are cognates
    sc = len(intersection)/smallerLength
    if addInfo is False:
        return sc
    return sc, len(intersection), len(srcCognates), len(trgtCognates)


def compareLengths(stringSrc, stringTrgt, useCharInsteadOfTokens=False, addInfo=False, onlyLongSentOfNPlusLen=None):
    """ given a string sentence pair return a score of how comparable the lengths of
     the source and target are. 0.0 being very dissimilar lengths and 1.0 being similar lengths """
    # use the token size instead of the char size
    if useCharInsteadOfTokens == False:
        stringSrc, stringTrgt = heuristTokenize(stringSrc, stringTrgt)
    elif type(stringSrc) is list and type(stringTrgt) is list:
        stringSrc, stringTrgt = u' '.join(stringSrc), u' '.join(stringTrgt)
    # get the lengths
    srcLength = len(stringSrc)
    trgtLength = len(stringTrgt)
    diff = float(abs(srcLength-trgtLength))
    # get the silence
    if srcLength + trgtLength == 0:
        if addInfo is False:
            return None
        return None, int(diff), srcLength, trgtLength
    # if we take only the long sentences into account, short sentences are returned as silence
    if onlyLongSentOfNPlusLen != None:
        if srcLength <= onlyLongSentOfNPlusLen and trgtLength <= onlyLongSentOfNPlusLen:
            if addInfo is False:
                return None
            return None, 0, 0, 0
    # get the score
    sc = min([srcLength, trgtLength])/max([srcLength, trgtLength])
    if addInfo is False:
        return sc
    return sc, int(diff), srcLength, trgtLength


def fauxAmis(stringEn, stringFr, addInfo=False, fauxAmisEn=None, fauxAmisFr=None):
    """ given the SP separated in english and french, returns a score between 0 and 1 representing the quality of the
    translation according to the presence or absence of faux amis (false cognates), 0.0 being bad and 1.0 being good"""
    if fauxAmisEn is None:
        fauxAmisEn = utilsString.openFauxAmisDict(enToFr=True, withDescription=False, reducedVersion=True)
    if fauxAmisFr is None:
        fauxAmisFr = utilsString.openFauxAmisDict(enToFr=False, withDescription=False, reducedVersion=True)
    # tokenize if not already
    stringEn, stringFr = heuristTokenize(stringEn, stringFr)
    # get the singulars too
    singular = [e[:-1] for e in stringEn if e[-1] == u's']
    stringEn = stringEn + singular
    singular1 = [e[:-1] for e in stringFr if e[-1] == u's']
    singular2 = [u'{0}al'.format(e[:-3]) for e in stringFr if e[-3:] == u'aux']
    stringFr = stringFr + singular1 + singular2
    # if we find a faux-ami in the english string we check if the french counterpart is in the target
    englishFA = []
    frenchFA = []
    totalFA = []
    # get the english faux amis
    for enTok in stringEn:
        if enTok in fauxAmisEn:
            # add it to the english faux amis
            englishFA.append(enTok)
            # we check if the corresponding french faux ami is there too
            if fauxAmisEn[enTok] in stringFr:
                totalFA.append(enTok)
    # get the french faux amis
    for frTok in stringFr:
        if frTok in fauxAmisFr:
            # add it to the english faux amis
            frenchFA.append(frTok)
    # if there were no FA, return silence
    if len(englishFA) == 0 or len(frenchFA) == 0 :
        if addInfo is False:
            return None
        return None, 0, len(englishFA), len(frenchFA)
    # otherwise return the score and metadata
    avgFaLen = (float(len(englishFA)) + float(len(frenchFA))) / 2.0
    scFa = 1.0 - (float(len(totalFA)) / avgFaLen)
    if addInfo is False:
        return scFa
    return scFa, len(totalFA), len(englishFA), len(frenchFA)


def ionSuffixMismatch(stringSrc, stringTrgt, addInfo=False):
    """ given the source and target strings, counts how many -ion words appear in both sides
     the more different these numbers are, the less likely to be aligned """
    # tokenize if not already
    stringSrc, stringTrgt = heuristTokenize(stringSrc, stringTrgt)
    # count how many ion words there are

    def hasIonSuffix(token):
        if token[-3:] == u'ion':
            return True
        elif token[-4:] == u'ions':
            return True
        return False

    ionInSrc = [tok for tok in stringSrc if hasIonSuffix(tok) is True]
    ionInTrgt = [tok for tok in stringTrgt if hasIonSuffix(tok) is True]
    # take the silence into account
    if len(ionInSrc)+len(ionInTrgt) <= 2:
        if addInfo is False:
            return None
        return None, 0, 0
    # return the score: the smallest of the src/trgt divided by the greater
    smallest = min([len(ionInSrc), len(ionInTrgt)])
    greatest = max([len(ionInSrc), len(ionInTrgt)])
    scIon = float(smallest)/float(greatest)
    if addInfo is False:
        return scIon
    return scIon, len(ionInSrc), len(ionInTrgt)


def stopWordsMismatch(stringEn, stringFr, addInfo=False, stopWordsEnFrDict=None):
    """ given the english and french sentences, it returns a score of how many the presence of
     english stopwords is reflected in the french sentence """
    stopWEn, stopWEnFr = [], []
    if stopWordsEnFrDict is None:
        stopWordsEnFrDict = utilsString.openEn2FrStopWordsDict()
    # tokenize if not already
    stringEn, stringFr = heuristTokenize(stringEn, stringFr)
    # search for the stopwords in english
    for tokEn in stringEn:
        if tokEn in stopWordsEnFrDict:
            stopWEn.append(tokEn)
            # search the french tokens for a translation of the english stop words
            stringFrCopy = list(stringFr)
            for tokFr in stopWordsEnFrDict[tokEn]:
                if tokFr in stringFrCopy:
                    stopWEnFr.append(tokFr)
                    stringFrCopy.remove(tokFr)
                    break
    # take the silence into account
    if len(stopWEnFr) + len(stopWEn) == 0:
        if addInfo is False:
            return None
        return None, 0, 0
    # we use the english as the base because of its lack of genre liaison and lexic simplicity
    scSW = float(len(stopWEnFr)) / float(len(stopWEn))
    if addInfo is False:
        return scSW
    return scSW, len(stopWEn), len(stopWEnFr)


def spellingCheck(stringEn, stringFr, addInfo=False, enLexicon=None, frLexicon=None):
    """ returns a score of the general spelling of both sentences (mean of both),
     0.0 being awful spelling, 1.0 being perfect spelling """
    # tokenize if not already
    stringEn, stringFr = heuristTokenize(stringEn, stringFr)
    # get the score for each token in english and french
    tokenScoreEn = utilsString.detectBadSpelling(stringEn, lang=u'en', orthDictOrSet=enLexicon)
    tokenScoreFr = utilsString.detectBadSpelling(stringFr, lang=u'fr', orthDictOrSet=frLexicon)
    # get one score for the whole sentence pair
    sumScEn = 0
    sumScFr = 0
    for tokScTupl in tokenScoreEn:
        if tokScTupl[1] == 1:
            sumScEn += 1
    for tokScTupl in tokenScoreFr:
        if tokScTupl[1] == 1:
            sumScFr += 1
    # take the silence into account
    if len(tokenScoreEn) == 0 or len(tokenScoreFr) == 0:
        if addInfo is False:
            return None
        return None, sumScEn, sumScFr, len(tokenScoreEn), len(tokenScoreFr)
    # get the score
    scSpell = float(sumScEn+sumScFr)/float(len(tokenScoreEn)+len(tokenScoreFr))
    if addInfo is False:
        return scSpell
    return scSpell, sumScEn, sumScFr, len(tokenScoreEn), len(tokenScoreFr)


def urlMismatch(stringSrc, stringTrgt, addInfo=False):
    """ 1.0 = has the same number of url in src and trgt
     0.5 = has twice as many urls in one side
     0.0 = has urls on one side and not the other"""
    # if the src and trgt strings are tokenized, join them in order to get the urls
    if type(stringSrc) is list:
        tokensSrc = list(stringSrc)
        stringSrc = u' '.join(stringSrc)
    else:
        tokensSrc = stringSrc.replace(u'\n', u'').replace(u'\t', u' ').split(u' ')
    if type(stringTrgt) is list:
        tokensTrgt = list(stringTrgt)
        stringTrgt = u' '.join(stringTrgt)
    else:
        tokensTrgt = stringTrgt.replace(u'\n', u'').replace(u'\t', u' ').split(u' ')
    # get the urls
    srcContainsUrl, srcUrlList = utilsString.detectUrlAndFolderPaths(stringSrc)
    trgtContainsUrl, trgtUrlList = utilsString.detectUrlAndFolderPaths(stringTrgt)
    # if there is no url, we return the silence
    if srcContainsUrl is False and trgtContainsUrl is False:
        if addInfo is False:
            return None
        return None, 0, 0, len(tokensSrc), len(tokensTrgt)
    # score the mismatch of urls on each side
    smallest = min([len(srcUrlList), len(trgtUrlList)])
    greatest = max([len(srcUrlList), len(trgtUrlList)])
    scUrl = float(smallest)/float(greatest)
    if addInfo is False:
        return scUrl
    return scUrl, len(srcUrlList), len(trgtUrlList), len(tokensSrc), len(tokensTrgt)


def monoling(stringSrc, stringTrgt, addInfo=False):
    """ verifies if part of the source is in the target or if part of the target is in the source
     and returns a score of how much of one is in the other
     1.0 = no part of the string is shared
     0.0 = the source and target are exactly the same"""
    # if the src and trgt strings are tokenized, join them in order to get the urls
    if type(stringSrc) is list and type(stringTrgt) is list:
        tokensSrc = list(stringSrc)
        stringSrc = u' '.join(stringSrc)
        tokensTrgt = list(stringTrgt)
        stringTrgt = u' '.join(stringTrgt)
    else:
        tokensSrc, tokensTrgt = heuristTokenize(stringSrc, stringTrgt)
    # take the silence into account
    if len(tokensSrc) <= 10 or len(tokensTrgt) <= 10:
        if addInfo is False:
            return None
        return None, len(stringSrc), len(stringTrgt), len(tokensSrc), len(tokensTrgt)
    smallest = min([len(stringSrc), len(stringTrgt)])
    greatest = max([len(stringSrc), len(stringTrgt)])
    scMono = float(smallest) / float(greatest)
    # compare
    if stringSrc == stringTrgt:
        if addInfo is False:
            return 0.0
        return 0.0, len(stringSrc), len(stringTrgt), len(tokensSrc), len(tokensTrgt)
    elif stringSrc in stringTrgt:
        if addInfo is False:
            return scMono
        return scMono, len(stringSrc), len(stringTrgt), len(tokensSrc), len(tokensTrgt)
    elif stringTrgt in stringSrc:
        if addInfo is False:
            return scMono
        return scMono, len(stringSrc), len(stringTrgt), len(tokensSrc), len(tokensTrgt)
    # if there is no exact similarity return silence (could be perfected by measuring the edit distance)
    else:
        if addInfo is False:
            return None
        return None, len(stringSrc), len(stringTrgt), len(tokensSrc), len(tokensTrgt)


def starbucksTranslationMismatch(stringEn, stringFr, addInfo=False, starbucksExprDict=None, starbucksWordDict=None):
    """ given the english and french sentences, it returns a score of how close
    is the english sentence to its word-by-word french translation,
     - 0.0 : the french sentence has no token in common with the english sentence
     - 1.0 : the french sentence is very similar to the english sentence """
    tokensEn, intersectionTokens = set([]), set([])
    if starbucksExprDict is None or starbucksWordDict is None:
        starbucksExprDict, starbucksWordDict = utilsString.openEn2FrStarbucksDict()
    # untokenize the english string if needed
    if type(stringEn) is list:
        stringEn, stringFr = u' '.join(stringEn.lower()), u' '.join(stringFr.lower())
    # the expressions first
    for starbExpr in starbucksExprDict:
        starbExprLw = starbExpr.lower()
        # search for the expression in the english sentence
        if starbExprLw in stringEn:
            # remove from the english string
            stringEn = stringEn.replace(starbExprLw, u'')
            # add to the english tokens set
            tokensEn.add(starbExprLw)
            # add to the intersection if the expression translation appears also in the french string
            for frencExpr in starbucksExprDict[starbExpr]:
                if frencExpr.lower() in stringFr:
                    # remove from the french string
                    stringFr = stringFr.replace(frencExpr.lower(), u'')
                    # add to the intersection token set
                    intersectionTokens.add(frencExpr.lower())
    # tokenize
    stringEn, stringFr = heuristTokenize(stringEn, stringFr)
    # lowercase all the word keys
    for wordKey in dict(starbucksWordDict):
        if wordKey.lower() != wordKey:
            starbucksWordDict[wordKey.lower()] = starbucksWordDict[wordKey]
    # the words
    for enTok in stringEn:
        if enTok in starbucksWordDict:
            # add to the english token set
            tokensEn.add(enTok)
            # if it also appears in french
            for possibleTranslation in starbucksWordDict[enTok]:
                if possibleTranslation in stringFr:
                    # add it to the french token set
                    intersectionTokens.add(possibleTranslation)
                    # remove it from the french
                    stringFr.remove(possibleTranslation)
    # take the silence into account
    if len(tokensEn) + len(intersectionTokens) == 0 or len(stringEn) <= 10 or len(stringFr) <= 10:
        if addInfo is False:
            return None
        return None, 0, 0
    # we use the english as the base because of its lack of genre liaison and lexic simplicity
    scSB = float(len(intersectionTokens)) / float(len(tokensEn))
    if addInfo is False:
        return scSB
    return scSB, len(tokensEn), len(intersectionTokens)


def punctAndSymb(stringSrc, stringTrgt, addInfo=False):
    """ given the SP source and target, returns a score between 0 and 1 representing the
    presence of punctuation and symbols, 0.0 being not having any in common
     and 1.0 being havging the exact same type and number of punct.&symb. in common """
    # un-tokenize if not already
    if type(stringSrc) is list:
        stringSrc = u' '.join(stringSrc)
    if type(stringTrgt) is list:
        stringTrgt = u' '.join(stringTrgt)
    # define the punct and symb to look for
    punctSymb = {u'!', u'"', u"'", u',', u'.', u':', u';', u'?', u'-', u'(', u')', u'[', u']', u'{', u'}', u'#', u'$',
                 u'%', u'&', u'*', u'+', u'/', u'\\', u'<', u'>', u'=', u'@', u'^', u'_', u'`', u'|', u'~'}
    # we look-up for punctuation and symbols in the src and trgt
    srcPunctAndSymb = []
    trgtPunctAndSymb = []
    for char in stringSrc:
        # in the src
        if char in punctSymb:
            srcPunctAndSymb.append(char)
    for char in stringTrgt:
        # in the trgt
        if char in punctSymb:
            trgtPunctAndSymb.append(char)
    intersection = makeListIntersection(srcPunctAndSymb, trgtPunctAndSymb)
    # if there is no or very low intersection, return silence
    if len(intersection) <= 2:
        if addInfo is False:
            return None
        return None, len(intersection), len(srcPunctAndSymb), len(trgtPunctAndSymb)
    # otherwise return the score and metadata
    avgPunctSymbLen = (float(len(srcPunctAndSymb)) + float(len(trgtPunctAndSymb))) / 2.0
    scPs = (float(len(intersection)) / avgPunctSymbLen)
    if addInfo is False:
        return scPs
    return scPs, len(intersection), len(srcPunctAndSymb), len(trgtPunctAndSymb)


def gibberish(stringSrc, stringTrgt, addInfo=False):
    """ given the SP source and target, returns a score between 0 and 1 representing the presence of "gibberish"
     (unreadeable and incomprehensible text) inside the 2 strings
     0.0 being it's very probably gibberish
     1.0 being it's very unlikely to be gibberish"""
    # un-tokenize if not already
    if type(stringSrc) is list:
        stringSrc = (u''.join(stringSrc))
    if type(stringTrgt) is list:
        stringTrgt = (u''.join(stringTrgt))
    stringSrc = stringSrc.replace(u' ', u'').replace(u'\t', u'').replace(u'\n', u'')
    stringTrgt = stringTrgt.replace(u' ', u'').replace(u'\t', u'').replace(u'\n', u'')
    # get the trigram set of the source
    srcTrigramSet = set(utilsString.charNgramArray(stringSrc, n=3))
    srcGibb3grams = []
    trgtGibb3grams = []
    if len(srcTrigramSet) == 0:
        scGibbSrc = 0
    else:
        # get the source trigrams that appear to be gibberish
        for src3gram in srcTrigramSet:
            if isCharNgramGibberish(src3gram) is True:
                srcGibb3grams.append(src3gram)
        scGibbSrc = float(len(srcGibb3grams))/float(len(srcTrigramSet))
    # get the trigram set of the target
    trgtTrigramSet = set(utilsString.charNgramArray(stringTrgt, n=3))
    if len(trgtTrigramSet) == 0:
        scGibbTrgt = 0
    else:
        # get the target trigrams that appear to be gibberish
        for trgt3gram in trgtTrigramSet:
            if isCharNgramGibberish(trgt3gram) is True:
                trgtGibb3grams.append(trgt3gram)
        scGibbTrgt = float(len(trgtGibb3grams))/float(len(trgtTrigramSet))
    # if the strings are too short (less than 10 char), return silence
    if len(stringSrc) <= 10 or len(stringTrgt) <= 10:
        if addInfo is False:
            return None
        return None, len(srcGibb3grams), len(trgtGibb3grams), len(srcTrigramSet), len(trgtTrigramSet)
    # get the score
    scGibb = 1.0 - ((scGibbSrc + scGibbTrgt) / 2)
    # return the score
    if addInfo is False:
        return scGibb
    return scGibb, len(srcGibb3grams), len(trgtGibb3grams), len(srcTrigramSet), len(trgtTrigramSet)


########################################################################
# USE HEURISTICS TO EXTRACT
########################################################################

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


def getMaxScores():
    maxScoreForTrue = {u'nb': 1.0, u'len': 0.7, u'cog': 0.2, u'fa': 0.6, u'ion': 0.65, u'sw': 0.9, u'spell': 0.85,
                u'url': 0.95, u'mono': float(u'inf'), u'strBcks': 0.65, u'punct': 0.85, u'gibb': 0.85,
                u'tabl': 0.75}
    maxScoreForFalse = {u'nb': 0.5, u'len': 0.35, u'cog': 0.1, u'fa': float(u'-inf'), u'ion': 0.5, u'sw': 0.3,
                        u'spell': 0.25, u'url': 0.9, u'mono': 0.95, u'strBcks': 0.25, u'punct': 0.5, u'gibb': 0.1,
                        u'tabl': 0.65}
    return maxScoreForTrue, maxScoreForFalse

########################################################################
# META-HEURISTICS TOOLS
########################################################################

def makeClassificationBinary(annotArray):
    # if we want to use a binary system of classes
    annotArray = np.equal(annotArray, [1.0])
    annotArray = annotArray.astype(int)
    return np.array(annotArray).reshape(-1, 1)


def makeClassificationByType(annotArray):
    """ use a type based classification system where [0.0, 0.1, 0.2], [1.1, 1.2, 1.4], [1.3], [1.0] are the classes
    at output:
    0 = not aligned
    1 = good
    2 = bad qual
    3 = gibberish"""
    notBadAlignArray = np.greater_equal(annotArray, [1.0]).astype(int)
    notGood = np.greater(annotArray, [1.0]).astype(int)
    notGibbArray = np.equal(annotArray, [1.3]).astype(int)
    annotArray = notBadAlignArray+notGood+notGibbArray
    return np.array(annotArray).reshape(-1, 1)


def makeLabelClasses(annotArray):
    try:
        labelEncoder = preprocessing.LabelEncoder()
    except NameError:
        from sklearn import preprocessing
        labelEncoder = preprocessing.LabelEncoder()
    annotationClasses = labelEncoder.fit_transform(annotArray)
    return annotationClasses.reshape(-1, 1)


def getRightClasses(annotArray, makeClassifBinary=False, makeClassifByGroup=False):
    # use label as classes
    if makeClassifBinary is False and makeClassifByGroup is False:
        annotArray = makeLabelClasses(annotArray)
    # use group labels into 2+ classes
    elif makeClassifBinary is False:
        annotArray = makeClassificationByType(annotArray)

    else:
        # use a binary system of classes
        annotArray = makeClassificationBinary(annotArray)
    return annotArray


def concatContentTrain(listOfFilePaths, vectorDim=60):
    concatenated = None
    for fPath in listOfFilePaths:
        # decide wether to train on the 13D or the 60D data
        if vectorDim in [13, 15]:
            fPath = fPath.replace(u'scoresAndMetaData', u'scores')
        # concatenate the right data
        if concatenated is None:
            concatenated = utilsML.fromTsvToMatrix(fPath)
        else:
            concatenated = np.vstack((concatenated, utilsML.fromTsvToMatrix(fPath)))
    return concatenated


def concatContent(listOfFilePaths, vectorDim=60):
    concatenated = None
    for fPath in listOfFilePaths:
        if concatenated is None:
            if vectorDim in [60, 62]:
                concatenated = utilsML.fromTsvToMatrix(fPath)
            elif vectorDim in [13, 15]:
                concatenated = utilsML.fromTsvToMatrix(fPath, justTheNFirstColumns=1)
            else:
                raise ValueError(u'the function accepts only 2 values: 13 and 60 (15 and 62 when added 2 arbitrary)')
        else:
            if vectorDim in [60, 62]:
                concatenated = np.vstack((concatenated, utilsML.fromTsvToMatrix(fPath)))
            else:
                concatenated = np.vstack((concatenated, utilsML.fromTsvToMatrix(fPath, justTheNFirstColumns=1)))
    return concatenated


def naiveOversampling(featArray, classesArray):
    """ oversampling randomly until all classes have the same number of elements
    (exceeding even the max of the most common class) """
    unq, unq_idx = np.unique(classesArray, return_inverse=True)
    unq_cnt = np.bincount(unq_idx)
    cnt = np.max(unq_cnt)
    cnt = int(cnt*1.5)
    out = np.empty((cnt * len(unq),) + featArray.shape[1:], featArray.dtype)
    outClasses = []
    for j in range(len(unq)):
        indices = np.random.choice(np.where(unq_idx == j)[0], cnt)
        outClasses += [j] * len(indices)
        out[j * cnt:(j + 1) * cnt] = featArray[indices]
    outClasses = np.asarray(outClasses).reshape(-1, 1)
    return out, outClasses


def appendAdditionalFeat(featList):
    """ return the feature list with 2 more features :
    the nb of features indicating good and nb of features indicating bad """
    goodThreshold = [1.0, 0.65]
    badThreshold = [0.35, 0.3, 0.95, 0.1]
    nbGood = 0
    nbBad = 0
    # count the goods
    for i, feat in enumerate([featList[0], featList[9]]):
        if feat >= goodThreshold[i]:
            nbGood += 1
    # count the bads
    for i, feat in enumerate([featList[1], featList[3], featList[8], featList[11]]):
        if feat < badThreshold[i]:
            nbBad += 1
    return np.append(featList, [nbGood, nbBad])


def addArbitraryFeatures(features):
    # add two arbitrary features : the nb of features indicating good and nb of features indicating bad
    arrayList = []
    for ind, featList in enumerate(features):
        arrayList.append(appendAdditionalFeat(featList))
    return np.asarray(arrayList)


def dataTrainPreparation(listOfPathsToFeaturesTsvFiles, listOfPathsToClassificationTsvFiles,
                         makeClassifBinary=False, makeClassifGroup=False, vectorDim=60):
    # be sure the list of paths are lists of paths and not strings
    if type(listOfPathsToFeaturesTsvFiles) is str:
        listOfPathsToFeaturesTsvFiles = [listOfPathsToFeaturesTsvFiles]
    if type(listOfPathsToClassificationTsvFiles) is str:
        listOfPathsToClassificationTsvFiles = [listOfPathsToClassificationTsvFiles]
    # concatenate the content of all the feature paths
    features = concatContentTrain(listOfPathsToFeaturesTsvFiles, vectorDim)
    # add two arbitrary features : the nb of features indicating good and nb of features indicating bad
    features = addArbitraryFeatures(features)
    # concatenate the content of all the classifications paths
    annotationClasses = concatContentTrain(listOfPathsToClassificationTsvFiles)
    # if we want to use multiple classes
    annotationClasses = getRightClasses(annotationClasses, makeClassifBinary, makeClassifGroup)
    # oversample
    features, annotationClasses = naiveOversampling(features, annotationClasses)
    return features, annotationClasses


def addAndDumpMetaDataToScoreFeatures(folderPath):
    """ instead of using the basic heuristic scores alone, use the scores and all metadata (intermeadiary)
    So get the metadata and dump it to a separate file """
    path = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics'
    # get the reference for each score
    with open(u"{0}sampleReference.tsv".format(folderPath)) as rf:
        refLn = rf.readline()
        while refLn:
            refLn = b000path.anonymizePath(refLn.replace(u'\n', u''))
            # find the right flag folder where to search for the reference
            for flagFold in [u"ALIGNMENT-QUALITY", u"QUALITY", u"MISALIGNED", u"NOT-FLAGGED"]:
                if flagFold in refLn:
                    break
            # get the count index of the line of interest
            countInd = 0
            # match the subset ref line to the ref line of the whole dataset
            with open(u"{0}/{1}/reference.tsv".format(path, flagFold)) as wholeFile:
                # try to match the reference to the whole
                wholeLn = wholeFile.readline()
                while wholeLn:
                    wholeLn = wholeLn.replace(u'\n', u'')
                    if wholeLn == refLn:
                        break
                    # next
                    wholeLn = wholeFile.readline()
                    countInd += 1
            # look in the scores files at the right index and make a line containing all scores and metadata
            allScores = u''
            for heurName in [u'cog', u'fa', u'gibb', u'ion', u'len', u'mono', u'nb', u'punct', u'spell', u'strBcks',
                             u'sw', u'tabl', u'url']:
                with open(u"{0}/{1}/{2}/score.tsv".format(path, flagFold, heurName)) as scoreFile:
                    # get to the right index
                    heurCount = 0
                    heurScLn = scoreFile.readline()
                    while heurCount != countInd:
                        heurCount += 1
                        heurScLn = scoreFile.readline()
                    # add the scores to the all scores list
                    if allScores == u'':
                        allScores = heurScLn.replace(u'\n', u'')
                    else:
                        allScores = u'{0}\t{1}'.format(allScores, heurScLn.replace(u'\n', u''))
            # append to the output score file (where each line is one collection of the scores and metadata)
            utilsOs.appendLineToFile(allScores, u"{0}scoresAndMetaData.tsv".format(folderPath), addNewLine=True)
            # next Line
            refLn = rf.readline()


def giveStartFinishIndexes(totalLength, section=0, numberOfSections=12):
    girth = int(totalLength/numberOfSections)
    start = section*girth if section != 0 else 0
    finish = (section+1)*girth
    if finish+(girth-1) > totalLength:
        finish = totalLength
    return start, finish


def getHeurScoresAsList(scoreFolderPath, applyToSection=None):
    """ given a path to the folder containing the score files or sub folders, returns an array
    containing all 13 or 60 elements (vector dim) as a feature vector """
    scoreFolderPathList = []
    openedFilesDict = {}
    flagList = [u'ALIGNMENT-QUALITY', u'QUALITY', u'MISALIGNED', u'NOT-FLAGGED']
    # make sure the folder path ends in a /
    if scoreFolderPath[-1] != u'/':
        scoreFolderPath = u'{0}/'.format(scoreFolderPath)
    # if we are given a supra folder, make a list of all its contained subfolders
    if len(set(flagList).intersection(set(utilsOs.getContentOfFolder(scoreFolderPath)))) > 0 :
        for flag in flagList:
            scoreFolderPathList.append(u'{0}{1}/'.format(scoreFolderPath, flag))
    else:
        scoreFolderPathList.append(scoreFolderPath)
    # look into each heuristic folder for the heuristic score file
    for flagFolder in scoreFolderPathList:
        if flagFolder not in openedFilesDict:
            openedFilesDict[flagFolder] = {}
        for heur in [u'cog', u'fa', u'gibb', u'ion', u'len', u'mono', u'nb', u'punct', u'spell', u'strBcks', u'sw',
                     u'tabl', u'url']:
            openedFilesDict[flagFolder][heur] = open(u'{0}{1}/score.tsv'.format(flagFolder, heur))
    # go line by line, opening the files and appending the scores
    for flagFolder in openedFilesDict:
        # get the total number of lines in the heuristics files
        with open(u'{0}cog/score.tsv'.format(flagFolder)) as openedFile:
            totalLength = utilsOs.countLines(openedFile)
        # get the indexes to apply to just a part of the whole list
        if applyToSection is None:
            start, finish = 0, totalLength
        else:
            start, finish = giveStartFinishIndexes(totalLength, applyToSection, numberOfSections=12)
        # counter
        c = 0
        # get the first line of an heuristic file, any heuristic (they all have the same length)
        cogLn = openedFilesDict[flagFolder][u'cog'].readline()
        while cogLn:
            # start once we see the start index
            if c >= start:
                #########################################################################
                # get an approximation of how much time there is left
                currentPlace = c-start
                if currentPlace % 100000:
                    finalPlace = finish - start
                    with open(u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2randForest/temp{0}".format(applyToSection), u"w") as f:
                        f.write(u"{0}\t{1}\t{2}\t{3}\t{4}\t{5}".format(currentPlace/finalPlace, c, start, finish, currentPlace, finalPlace))
                #########################################################################
                # get the heur score for cog
                scAsFeat13 = [float(cogLn.replace(u'\n', u'').replace(u'na', u'-1.0').split(u'\t')[0])]
                scAsFeat60 = [float(e) for e in cogLn.replace(u'\n', u'').replace(u'na', u'-1.0').split(u'\t')]
                # get the heur score for all other features
                for heur in [u'fa', u'gibb', u'ion', u'len', u'mono', u'nb', u'punct', u'spell', u'strBcks', u'sw',
                             u'tabl', u'url']:
                    heurLn = openedFilesDict[flagFolder][heur].readline()
                    features = [float(e) for e in heurLn.replace(u'\n', u'').replace(u'na', u'-1.0').split(u'\t')]
                    scAsFeat13 = scAsFeat13+[float(features[0])]
                    scAsFeat60 = scAsFeat60+features
                # yield the list of feat
                yield scAsFeat13, scAsFeat60
            # next line
            cogLn = openedFilesDict[flagFolder][u'cog'].readline()
            c += 1
            # break the loop once if the finish index is achieved
            if c >= finish:
                break
        # close each opened file
        for heur in openedFilesDict[flagFolder]:
            openedFilesDict[flagFolder][heur].close()


def getHeurScoresAsFeatures(folderPath, applyToSection=None):
    '''
    given a path to a folder, returns a list of vectors where
    each heuristic score transformed is transformed into a numpy array
    '''
    for heurFeat13D, heurFeat60D in getHeurScoresAsList(folderPath, applyToSection):
        feat13DArray = np.asarray(heurFeat13D)
        feat60DArray = np.asarray(heurFeat60D)
        # add 2 arbitrarily chose features: number of bad feat total, nb of good feat total
        feat13DArray = appendAdditionalFeat(feat13DArray)
        feat60DArray = appendAdditionalFeat(feat60DArray)
        yield feat13DArray, feat60DArray


def getSentPairFromRefFile(folderPath, applyToSection=None):
    """ returns the sentence pair corresponding to the reference """
    refFolderPathList = []
    flagList = [u'ALIGNMENT-QUALITY', u'QUALITY', u'MISALIGNED', u'NOT-FLAGGED']
    # if we are given a supra folder, make a list of all its contained subfolders
    if len(set(flagList).intersection(set(utilsOs.getContentOfFolder(folderPath)))) > 0:
        for flag in flagList:
            refFolderPathList.append(u'{0}{1}/'.format(folderPath, flag))
    else:
        refFolderPathList.append(folderPath)
    for refFoldPath in refFolderPathList:
        # make the path to the ref file
        if u'.' not in refFoldPath[-5:]:
            if refFoldPath[-1] == u'/':
                refFoldPath = u'{0}reference.tsv'.format(refFoldPath)
            else:
                refFoldPath = u'{0}/reference.tsv'.format(refFoldPath)
        # get the total number of lines in the ref file
        with open(refFoldPath) as openedFile:
            totalLength = utilsOs.countLines(openedFile)
        # get the indexes to apply to just a part of the whole list
        if applyToSection is None:
            start, finish = 0, float(u"inf")
        else:
            start, finish = giveStartFinishIndexes(totalLength, applyToSection, numberOfSections=12)
        # open the ref file
        with open(refFoldPath) as refFile:
            refLn = refFile.readline()
            # counter
            c = 0
            while refLn:
                # start once we see the start index
                if c >= start:
                    refList = refLn.replace(u'\n', u'').split(u'\t')
                    pathToSps = b000path.desAnonymizePath(refList[0])
                    indSp = int(refList[1])
                    with open(u'{0}.en'.format(pathToSps)) as enFile:
                        with open(u'{0}.fr'.format(pathToSps)) as frFile:
                            indexFile = 0
                            enLn = enFile.readline()
                            frLn = frFile.readline()
                            while indexFile != indSp:
                                # next line
                                enLn = enFile.readline()
                                frLn = frFile.readline()
                                # update index
                                indexFile += 1
                            yield enLn.replace(u'\n', u''), frLn.replace(u'\n', u''), refLn.replace(u'\n', u'')
                # next line
                refLn = refFile.readline()
                c += 1
                # break the loop once if the finish index is achieved
                if c >= finish:
                    break


########################################################################
# META-HEURISTICS (classifiers)
########################################################################

def trainSvmModel(listOfPathsToFeaturesTsvFiles, listOfPathsToClassificationTsvFiles,
                  makeClassifBinary=False, makeClassifGroup=False, vectorDim=60):
    """ given a list of paths leading to the features files and the classification (one per vector of features)
     returns a simple trained SVM """
    from sklearn import svm
    # be sure the list of paths are lists of paths and not strings
    if type(listOfPathsToFeaturesTsvFiles) is str:
        listOfPathsToFeaturesTsvFiles = [listOfPathsToFeaturesTsvFiles]
    if type(listOfPathsToClassificationTsvFiles) is str:
        listOfPathsToClassificationTsvFiles = [listOfPathsToClassificationTsvFiles]
    # concatenate the content of all the feature paths
    features = concatContentTrain(listOfPathsToFeaturesTsvFiles, vectorDim)
    features = addArbitraryFeatures(features)
    # concatenate the content of all the classifications paths
    annotationClasses = concatContent(listOfPathsToClassificationTsvFiles)
    # if we want to use multiple classes
    annotationClasses = getRightClasses(annotationClasses, makeClassifBinary, makeClassifGroup)
    # make and train the classifier
    classifier = svm.SVC(gamma='scale', kernel='rbf')
    classifier.fit(features, annotationClasses.ravel())
    return classifier


def trainRdmForestModel(listOfPathsToFeaturesTsvFiles, listOfPathsToClassificationTsvFiles,
                        makeClassifBinary=False, makeClassifType=False, vectorDim=60):
    """ given a list of paths leading to the features files and the classification (one per vector of features)
        returns a simply trained random forest classifier """
    from sklearn.ensemble import RandomForestClassifier
    features, annotationClasses = dataTrainPreparation(listOfPathsToFeaturesTsvFiles,
                                                       listOfPathsToClassificationTsvFiles,
                                                       makeClassifBinary, makeClassifType, vectorDim)
    # make and train the classifier
    classifier = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=0)
    classifier.fit(features, annotationClasses.ravel())
    return classifier


def trainMaxEntLinearModel(listOfPathsToFeaturesTsvFiles, listOfPathsToClassificationTsvFiles,
                           makeClassifBinary=False, makeClassifType=False, vectorDim=60):
    """ given a list of paths leading to the features files and the classification (one per vector of features)
            returns a simply trained maximum entropy model """
    from sklearn.linear_model import LogisticRegression
    features, annotationClasses = dataTrainPreparation(listOfPathsToFeaturesTsvFiles,
                                                       listOfPathsToClassificationTsvFiles,
                                                       makeClassifBinary, makeClassifType, vectorDim)
    # make and train the classifier
    classifier = LogisticRegression(random_state=0, solver='liblinear', fit_intercept=False)
    classifier.fit(features, annotationClasses.ravel())
    return classifier


def trainFeedForwardNNModel(listOfPathsToFeaturesTsvFiles, listOfPathsToClassificationTsvFiles,
                            makeClassifBinary=False, makeClassifType=False, vectorDim=60):
    """ given a list of paths leading to the features files and the classification (one per vector of features)
            returns a simply trained random forest classifier """
    features, annotationClasses = dataTrainPreparation(listOfPathsToFeaturesTsvFiles,
                                                       listOfPathsToClassificationTsvFiles,
                                                       makeClassifBinary, makeClassifType, vectorDim)
    # make tensors for NN
    featTensor = tensor(features).float()
    annotTensor = tensor([e[0] for e in annotationClasses])
    # (based on www.deeplearningwizard.com/deep_learning/practical_pytorch/pytorch_feedforward_neuralnetwork/)
    # hyperparams and preparation
    input_dim = len(featTensor[0])
    hidden_dim = 100
    if makeClassifBinary != False:
        output_dim = 2
    elif makeClassifType != False:
        output_dim = 4
    else:
        output_dim = 2
    model = utilsML.FeedforwardNeuralNetModel(input_dim, hidden_dim, output_dim)
    criterion = nn.CrossEntropyLoss()
    learning_rate = 0.1
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
    numEpochs = 100
    # train the model
    for epoch in range(numEpochs):
        # Clear gradients w.r.t. parameters
        optimizer.zero_grad()
        # Forward pass to get output/logits
        outputs = model(featTensor)
        # Calculate Loss: softmax --> cross entropy loss
        loss = criterion(outputs, annotTensor.squeeze())
        # Getting gradients w.r.t. parameters
        loss.backward()
        # Updating parameters
        optimizer.step()
    return model, loss


def getModelPredictions(modelClassifier, listOfPathsToTestFeatureFiles, vectorDim=60):
    """ given a list of paths where to find the validation/test set features, returns a prediction of the class
    it belongs to"""
    if type(listOfPathsToTestFeatureFiles) is str:
        listOfPathsToTestFeatureFiles = [listOfPathsToTestFeatureFiles]
    # concatenate the content of all the feature paths
    testFeatures = concatContent(listOfPathsToTestFeatureFiles, vectorDim)
    testFeatures = addArbitraryFeatures(testFeatures)
    # simple ml classifier
    try:
        predictions = modelClassifier.predict(testFeatures)
        return predictions
    # pytorch classifier model
    except AttributeError:
        modelClassifier, loss = modelClassifier
        modelClassifier.eval()
        testFeatures = tensor(testFeatures).float()
        predictions = modelClassifier(testFeatures)
        return predictions, loss


########################################################################
# META-HEURISTICS RUSTIC EVALUATION
########################################################################

def getModelEval(listOfPathsToTestFeatureFiles, listOfPathsToTestClassificationFiles, modelClassifier,
                 makeClassifBinary=False, vectorDim=60):
    # test set
    predictions = getModelPredictions(modelClassifier, listOfPathsToTestFeatureFiles, vectorDim)
    realClasses = concatContent(listOfPathsToTestClassificationFiles)
    realClasses = getRightClasses(realClasses, makeClassifBinary)
    # if the predictions are not pytorch tensors + loss
    if type(predictions) is not tuple:
        # count
        total = 0
        good = 0
        for n in range(len(predictions)):
            if predictions[n] == realClasses[n][0]:
                # print(predictions[n], int(realClasses[n][0]))
                good += 1
            else:
                # print(predictions[n], (realClasses[n][0]))
                pass
            total += 1
        print("ACCURACY : ", good / total, "CORRECT and TOTAL : ", good, total)
    # if the predictions are torch tensors (we used an NN)
    else:
        predictions, loss = predictions
        # Calculate Accuracy
        correct = 0
        total = 0
        # Iterate through test dataset
        annotCl = tensor([e[0] for e in realClasses])
        # Get predictions from the maximum value
        _, predicted = torch.max(predictions.data, 1)
        # Total number of labels
        total += annotCl.size(0)
        # Total correct predictions
        correct += (predicted == annotCl).sum()
        accuracy = 100 * correct / total
        # Print Loss
        print('Iteration: {}. Loss: {}. Accuracy: {}'.format(iter, loss.item(), accuracy))
    return None


def getModelEvalGoodAndBad(listOfPathsToTestFeatureFiles, listOfPathsToTestClassificationFiles, modelClassifier,
                 makeClassifBinary=False, verbose=True):
    """ compare the predictions given by the classifier and the human annotations
    print accuracy and precision-recall depending on wether we are analyzing the capacity of the model
    to predict bad or good annotations"""
    # make empty conf matrix
    confMatrix = []
    # test set
    predictions = getModelPredictions(modelClassifier, listOfPathsToTestFeatureFiles)
    realClasses = concatContent(listOfPathsToTestClassificationFiles)
    realClasses = getRightClasses(realClasses, makeClassifBinary)
    # if the predictions are torch tensors (we used an NN)
    if type(predictions) is tuple:
        model, loss = predictions
        # Get predictions from the maximum value
        _, predicted = torch.max(model.data, 1)
        predictions = predicted.tolist()
    # populate binary confusion matrix
    for n in range(len(predictions)):
        ################################## binary matrix ONLY (to be expanded) ########################################
        confMatrix = utilsML.populateBinaryConfMatrix(predictions[n], realClasses[n][0], confMatrix)
    # get results
    truePos = confMatrix[u'real pos'][u'pred pos']
    trueNeg = confMatrix[u'real neg'][u'pred neg']
    falsePos = confMatrix[u'real neg'][u'pred pos']
    falseNeg = confMatrix[u'real pos'][u'pred neg']
    all = (truePos + trueNeg + falsePos + falseNeg)
    # calculate the GOOD precision and recall
    goodPrecision = truePos / (truePos + falsePos)
    goodRecall = truePos / (truePos + falseNeg)
    # calculate the BAD precision and recall
    badPrecision = trueNeg / (trueNeg + falseNeg)
    badRecall = trueNeg / (trueNeg + falsePos)
    # calculate the accuracy
    accuracy = (truePos + trueNeg) / all
    # print the results
    if verbose is True:
        print("GOOD precision : ", goodPrecision, "    BASELINE : ", (truePos+falseNeg) / all)
        print("GOOD recall : ", goodRecall, "    BASELINE : ", (truePos + falseNeg) / (truePos + falseNeg))
        print("JUST accuracy : ", accuracy)
        print("BAD precision : ", badPrecision, "    BASELINE : ", (trueNeg+falsePos) / all)
        print("BAD recall : ", badRecall, "    BASELINE : ", (trueNeg+falsePos) / (trueNeg+falsePos))
    return goodPrecision, goodRecall, accuracy, badPrecision, badRecall


def applyClassifierToExtract(modelClassifierGood, modelClassifierBad,
                             extractingPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/',
                             outputPath=None, featDim=(60,13), applyOnSection=None):
    """
    apply the trained classifier and extract the good and bad SPs from the corpus
    """
    if outputPath is None:
        outputPath = extractingPath
    if applyOnSection is None:
        section = ''
    else:
        section = int(applyOnSection)
    # get scores and metadata, browse the lists and arrays
    for (feat13D, feat60D), (enSent, frSent, ref) in zip(getHeurScoresAsFeatures(extractingPath, applyOnSection),
                                                         getSentPairFromRefFile(extractingPath, applyOnSection)):
        # if we want to change the dimensions
        if featDim[0] == 13:
            feat60D = feat13D
        if featDim[1] == 60:
            feat13D = feat60D
        # get the predictions if there is only one model for good and bad
        if modelClassifierGood == modelClassifierBad:
            predictForGood = modelClassifierGood.predict(np.asarray([feat60D]))
            predictForBad = predictForGood
        # get the predictions if there are two models for good and bad
        else:
            predictForGood = modelClassifierGood.predict(np.asarray([feat60D]))
            predictForBad = modelClassifierBad.predict(np.asarray([feat13D]))
        # use the trained model to detect the bad SPs
        if predictForBad[0] == 0:
            # if the sp is detected as BAD by the model for bad, dump the data
            utilsOs.appendLineToFile(enSent, u'{0}problematic/extracted{1}.en'.format(outputPath, section), addNewLine=True)
            utilsOs.appendLineToFile(frSent, u'{0}problematic/extracted{1}.fr'.format(outputPath, section), addNewLine=True)
            utilsOs.appendLineToFile(ref, u'{0}problematic/reference{1}.tsv'.format(outputPath, section), addNewLine=True)
            sc13 = u'\t'.join([str(f) for f in feat13D.tolist()])
            sc60 = u'\t'.join([str(f) for f in feat60D.tolist()])
            utilsOs.appendLineToFile(sc13, u'{0}problematic/scores{1}.tsv'.format(outputPath, section), addNewLine=True)
            utilsOs.appendLineToFile(sc60, u'{0}problematic/scoresAndMetaData{1}.tsv'.format(outputPath, section), addNewLine=True)
        # if not use the trained model to detect good SPs
        else:
            if predictForGood[0] == 1:
                # if the sp is detected as GOOD by the model for good, dump the data
                utilsOs.appendLineToFile(enSent, u'{0}noProblematic/extracted{1}.en'.format(outputPath, section), addNewLine=True)
                utilsOs.appendLineToFile(frSent, u'{0}noProblematic/extracted{1}.fr'.format(outputPath, section), addNewLine=True)
                utilsOs.appendLineToFile(ref, u'{0}noProblematic/reference{1}.tsv'.format(outputPath, section), addNewLine=True)
                sc13 = u'\t'.join([str(f) for f in feat13D.tolist()])
                sc60 = u'\t'.join([str(f) for f in feat60D.tolist()])
                utilsOs.appendLineToFile(sc13, u'{0}noProblematic/scores{1}.tsv'.format(outputPath, section), addNewLine=True)
                utilsOs.appendLineToFile(sc60, u'{0}noProblematic/scoresAndMetaData{1}.tsv'.format(outputPath, section), True)


def applyClassifierToGetPred(modelClassifierGood, modelClassifierBad,
                             inputScFilePath, inputScMetaFilePath, outputFilePath=None, featDim=(60,13)):
    """
    apply the trained classifier, predict the good and bad SPs from the corpus and dump the resulting prediction
    """
    dictCount = {u"total": 0, u"zeros": 0, u"ones": 0, u"silences": 0}
    with open(inputScFilePath) as scFile:
        scoresInList = [scLn.replace(u"\n", u"").split(u"\t") for scLn in scFile.readlines()]
        for i, scList in enumerate(scoresInList):
            for ie, sc in enumerate(scList):
                scoresInList[i][ie] = float(sc) if sc != u"na" else float(-1.0)
            # transform into array and add 2 arbitrarily chose features: number of bad feat total, nb of good feat total
            scoresInList[i] = appendAdditionalFeat(np.asarray(scoresInList[i]))
    with open(inputScMetaFilePath) as scFile:
        scoresMetaDataInList = [scLn.replace(u"\n", u"").split(u"\t") for scLn in scFile.readlines()]
        for i, scMtList in enumerate(scoresMetaDataInList):
            for ie, scMt in enumerate(scMtList):
                scoresMetaDataInList[i][ie] = float(scMt) if scMt != u"na" else float(-1.0)
            # transform into array and add 2 arbitrarily chose features: number of bad feat total, nb of good feat total
            scoresMetaDataInList[i] = appendAdditionalFeat(np.asarray(scoresMetaDataInList[i]))
    # open the ouput file
    utilsOs.deleteAFile(outputFilePath)
    with open(outputFilePath, u"a") as outFile:
        # get scores and metadata, browse the lists and arrays
        for feat13D, feat60D in zip(scoresInList, scoresMetaDataInList):
            # if we want to change the dimensions
            if featDim[0] == 13:
                feat60D = feat13D
            if featDim[1] == 60:
                feat13D = feat60D
            # get the predictions if there is only one model for good and bad
            if modelClassifierGood == modelClassifierBad:
                predictForGood = modelClassifierGood.predict(np.asarray([feat60D]))
                predictForBad = predictForGood
            # get the predictions if there are two models for good and bad
            else:
                predictForGood = modelClassifierGood.predict(np.asarray([feat60D]))
                predictForBad = modelClassifierBad.predict(np.asarray([feat13D]))
            # count
            dictCount[u"total"] += 1
            # use the trained model to detect the bad SPs
            if predictForBad[0] == 0:
                # if the sp is detected as GOOD
                outFile.write(u"0\n")
                # count
                dictCount[u"zeros"] += 1
            # if not use the trained model to detect good SPs
            else:
                if predictForGood[0] == 1:
                    # if the sp is detected as GOOD
                    outFile.write(u"1\n")
                    # count
                    dictCount[u"ones"] += 1
                else:
                    # if the sp is silence
                    outFile.write(u"na\n")
                    dictCount[u"silences"] += 1
    print(dictCount)

