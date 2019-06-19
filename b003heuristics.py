#!/usr/bin/python
# -*- coding:utf-8 -*-

import re, math

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import b000path, utilsOs, utilsString

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


def tooFewTokens(stringSrc, stringTrgt, nTokens=4):
    """ given a string sentence pair return 0 if there are less
    than N tokens on either the src or the trgt and return 1 otherwise """
    # if it's not already tokenized
    stringSrc, stringTrgt = heuristTokenize(stringSrc, stringTrgt)
    # count the tokens
    if len(stringSrc) <= nTokens or len(stringTrgt) <= nTokens:
        return 0
    return 1


def tableOfContents(stringSrc, stringTrgt, nTokens=4, contextScores=None, placeInDocument=None, addInfo=False):
    """ given a string sentence pair return a score of the ratio
    of small sentence pairs in the context of the current sp """
    # if it's not already tokenized
    stringSrc, stringTrgt = heuristTokenize(stringSrc, stringTrgt)
    # get scores
    scores = [tooFewTokens(stringSrc, stringTrgt, nTokens)]
    # re make the token list a string so we can check the first characters
    origSrcString = u' '.join(stringSrc)
    if len(origSrcString) > 4:
        # if there is a number or a symbol indicating a table of contents at the start of the string
        extractedNmbrs = utilsString.extractNumbersFromString(origSrcString[:3])
        srcStart = origSrcString[:3]
        if len(extractedNmbrs) != 0 or u'-' in srcStart or u'.' in srcStart or u'*' in srcStart:
            scores.append(0)
        else:
            scores.append(1)
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
    if len(intersection) == 0:
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
    sc = 1.0 - (diff/max([srcLength, trgtLength]))
    if addInfo is False:
        return sc
    return sc, int(diff), srcLength, trgtLength


def fauxAmis(stringEn, stringFr, addInfo=False):
    """ given the SP separated in english and french, returns a score between 0 and 1 representing the quality of the
    translation according to the presence or absence of faux amis (false cognates), 0.0 being bad and 1.0 being good"""
    fauxAmisEn = utilsString.openFauxAmisDict(enToFr=True, withDescription=False)
    fauxAmisFr = utilsString.openFauxAmisDict(enToFr=False, withDescription=False).keys()
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
    if len(englishFA) == 0 or len(frenchFA) == 0:
        if addInfo is False:
            return None
        return None, 0, len(englishFA), len(frenchFA)
    # otherwise return the score and metadata
    avgFaLen = (float(len(englishFA)) + float(len(englishFA))) / 2.0
    scFa = float(len(totalFA)) / avgFaLen
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
    if len(ionInSrc)+len(ionInTrgt) == 0:
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


def stopWordsMismatch(stringEn, stringFr, addInfo=False):
    """ given the english and french sentences, it returns a score of how many the presence of
     english stopwords is reflected in the french sentence """
    stopWEn, stopWEnFr = [], []
    stopWordsEnFrDict = utilsString.openEn2FrStopWordsDict()
    # tokenize if not already
    stringEn, stringFr = heuristTokenize(stringEn, stringFr)
    # search for the stopwords in english
    for tokEn in stringEn:
        if tokEn in stopWordsEnFrDict:
            stopWEn.append(tokEn)
            # search the french tokens for a translation of the english stop words
            for tokFr in stringFr:
                if tokFr in stopWordsEnFrDict[tokEn]:
                    stopWEnFr.append(tokFr)
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


def spellingCheck(stringEn, stringFr, addInfo=False):
    """ returns a score of the general spelling of both sentences (mean of both),
     0.0 being awful spelling, 1.0 being perfect spelling """
    # tokenize if not already
    stringEn, stringFr = heuristTokenize(stringEn, stringFr)
    # get the score for each token in english and french
    tokenScoreEn = utilsString.detectBadSpelling(stringEn, lang=u'en')
    tokenScoreFr = utilsString.detectBadSpelling(stringFr, lang=u'fr')
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


def hasUrl(stringSrc, stringTrgt, addInfo=False):
    """ 1.0 = has no url
     0.5 = half the tokens are urls
     0.0 = the string is one big url"""
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
    # if there is no url, there is no problem
    if srcContainsUrl is False and trgtContainsUrl is False:
        if addInfo is False:
            return None
        return None, 0, 0, len(tokensSrc), len(tokensTrgt)
    # the more the url englobes the totality of the sentence, the more its probability of being an error
    scUrl = 1.0 - float(len(srcUrlList)+len(trgtUrlList))/float(len(tokensSrc)+len(tokensTrgt))
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
    if len(tokensSrc) <= 10:
        if addInfo is False:
            return None
        return None, len(stringSrc), len(stringTrgt)
    scMono = float(len(stringSrc)) / float(len(stringTrgt))
    # compare
    if stringSrc == stringTrgt:
        if addInfo is False:
            return 0.0
        return 0.0, len(stringSrc), len(stringTrgt)
    elif stringSrc in stringTrgt:
        if addInfo is False:
            return scMono
        return scMono, len(stringSrc), len(stringTrgt)
    elif stringTrgt in stringSrc:
        if addInfo is False:
            return scMono
        return scMono, len(stringSrc), len(stringTrgt)
    # if there is no exact similarity return silence (could be perfected by measuring the edit distance)
    else:
        if addInfo is False:
            return None
        return None, len(stringSrc), len(stringTrgt)


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