#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs
from b003heuristics import *
import numpy as np
import pandas as pd


########################################################################
# QUALITY VERIFICATION
########################################################################

def populateConfMatrix(pred, real, confMatrix=[]):
    if len(confMatrix) == 0:
        content = np.zeros(shape=(2, 2))
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


def getPrecisionRecallAccuracy(confMatrix, verbose=True):
    precision = confMatrix[u'real pos'][u'pred pos'] / (confMatrix[u'real pos'][u'pred pos']+confMatrix[u'real neg'][u'pred pos'])
    recall = confMatrix[u'real pos'][u'pred pos'] / (confMatrix[u'real pos'][u'pred pos']+confMatrix[u'real pos'][u'pred neg'])
    f1 = 2 * ((precision*recall)/(precision+recall))
    truePosTrueNeg = confMatrix[u'real pos'][u'pred pos'] + confMatrix[u'real neg'][u'pred neg']
    everything = (confMatrix[u'real pos'][u'pred pos'] + confMatrix[u'real neg'][u'pred neg'] +
                  confMatrix[u'real pos'][u'pred neg'] + confMatrix[u'real neg'][u'pred pos'])
    accuracy = truePosTrueNeg / everything
    if verbose is True:
        print(u'PRECISION : ', precision)
        print(u'RECALL : ', recall)
        print(u'F1 : ', f1)
        print(u'ACCURACY : ', accuracy)
    return precision, recall, f1, accuracy


def getInversePrecisionRecallAccuracy(confMatrix, verbose=True):
    """ give the precision, recall, f1 and accuracy scores for a confusion matrix where we
    want all negatives to be taken as positives and all positives to be taken as negatives """
    precision = confMatrix[u'real neg'][u'pred neg'] / (confMatrix[u'real neg'][u'pred neg']+confMatrix[u'real pos'][u'pred neg'])
    recall = confMatrix[u'real neg'][u'pred neg'] / (confMatrix[u'real neg'][u'pred neg']+confMatrix[u'real neg'][u'pred pos'])
    f1 = 2 * ((precision*recall)/(precision+recall))
    truePosTrueNeg = confMatrix[u'real pos'][u'pred pos'] + confMatrix[u'real neg'][u'pred neg']
    everything = (confMatrix[u'real pos'][u'pred pos'] + confMatrix[u'real neg'][u'pred neg'] +
                  confMatrix[u'real pos'][u'pred neg'] + confMatrix[u'real neg'][u'pred pos'])
    accuracy = truePosTrueNeg / everything
    if verbose is True:
        print(u'INVERSE PRECISION : ', precision)
        print(u'INVERSE RECALL : ', recall)
        print(u'INVERSE F1 : ', f1)
        print(u'ACCURACY : ', accuracy)
    return precision, recall, f1, accuracy


def getAnnotationScore(manualAnnotationString, focus=u'all', negativesOnly=False):
    """ matches the multidimensional manual annotation to a
     boolean annotation depending on the desired focus:
     * returns True for
        - a: good alignment
        - q: good quality
        - qa: good alignment and good quality
        - g: no gibberish
        - qg: good quality and no gibberish
        - all: good alignment and good quality and no gibberish """
    manualAnnotationString = manualAnnotationString.replace(u'\n', u'')
    # verify the string nature of the annotation
    if type(manualAnnotationString) is float:
        manualAnnotationString = str(manualAnnotationString)
    elif type(manualAnnotationString) is int:
        manualAnnotationString = str(int(manualAnnotationString))
    # if there was a formatting error and the 1.0 became 1
    elif type(manualAnnotationString) is str and manualAnnotationString == u'1':
        manualAnnotationString = u'1.0'
    # get the right score - true = good qual and good align
    if focus == u'qa' or focus == u'aq':
        for badQualSc in [u'0.0', u'0.1', u'0.2', u'1.1', u'1.2', u'1.4']:
            if badQualSc in manualAnnotationString:
                return False
        # if we want only the negatives we replace true with None (silence)
        if negativesOnly == False:
            return True
        else:
            return None
    # get the right score - true = good align
    elif focus == u'a':
        if u'1.' in manualAnnotationString and manualAnnotationString != u'1.3':
            # if we want only the negatives we replace true with None (silence)
            if negativesOnly == False:
                return True
            else:
                return None
        else: return False
    # get the right score - true = good qual
    elif focus == u'q':
        for badQualSc in [u'1.1', u'1.2', u'1.4']:
            if badQualSc in manualAnnotationString:
                return False
        # if we want only the negatives we replace true with None (silence)
        if negativesOnly == False:
            return True
        else:
            return None
    # get the right score - true = no gibberish
    elif focus == u'g':
        if u'1.3' in manualAnnotationString:
            return False
        # if we want only the negatives we replace true with None (silence)
        if negativesOnly == False:
            return True
        else:
            return None
    # get the right score - true = good qual and no gibberish
    elif focus == u'qg' or focus == u'gq':
        for badQualSc in [u'1.1', u'1.2', u'1.3', u'1.4']:
            if badQualSc in manualAnnotationString:
                return False
        # if we want only the negatives we replace true with None (silence)
        if negativesOnly == False:
            return True
        else:
            return None
    # get the right score - true = good qual and good align and no gibberish
    elif focus == u'all':
        if u'1.0' in manualAnnotationString:
            if negativesOnly is False:
                return True
            # if we want only the negatives we replace true with None (silence)
            else:
                return None
        return False
    # raise error since we got the wrong argument
    else:
        raise ValueError('the focus arg is not among all supported values (qa, a, q, g, qg, all)')


def countAndPopulate(aFunction, functionId, ln1, ln2, annotScore, silenceRateDict, confMatrix, fcThreshold):
    if functionId == 1:
        funcScore = aFunction(ln1, ln2, onlyLongSentOfNPlusLen=10)
    else:
        funcScore = aFunction(ln1, ln2)
    # if the score is none (nothing allows to use the heuristic) add to the silence
    if funcScore is None:
        silenceRateDict[functionId] += 1
        return confMatrix, silenceRateDict, funcScore, None
    else:
        binaryScore = True if funcScore >= fcThreshold else False
        confMatrix = populateConfMatrix(binaryScore, annotScore, confMatrix)
        return confMatrix, silenceRateDict, funcScore, binaryScore


def getAllScoreProblematicOriented(binSc0, binSc1, binSc2, binSc3, binSc4, binSc5, binSc6, binSc7, binSc8, binSc9,
                                   binSc10, binSc11, binSc99, silenceRate):
    """ use a vote system divided in 3 categories of scores divided according to their precision and trustyness """
    mostPreciseScores = [bSc for bSc in [binSc1, binSc8, binSc11] if bSc is not None]
    highPreciseScores = [bSc for bSc in [binSc0, binSc4, binSc5, binSc6, binSc7, binSc9, binSc10, binSc99] if
                         bSc is not None]
    lowPreciseScores = [bSc for bSc in [binSc2] if bSc is not None]
    # this is problematic SP oriented
    nbFalseInHighScores = sum([1 if sc is False else 0 for sc in highPreciseScores])
    nbFalseInLowScores = sum([1 if sc is False else 0 for sc in lowPreciseScores])
    # one most-precise is enough
    if False in mostPreciseScores:
        scoreAll = False
        # print('most precise alone', annotScore)
    # three or more high-scores
    elif nbFalseInHighScores >= 3:
        scoreAll = False
        # print('three high', annotScore)
    # two high-score and one or more low-scores
    elif nbFalseInHighScores == 2 and nbFalseInLowScores >= 1:
        scoreAll = False
        # print('two high, one low', annotScore)
    # if no heuristic helps, add to the silence
    elif nbFalseInHighScores+nbFalseInLowScores == 0:
        silenceRate['all'] += 1
        scoreAll = None
        # print('silence', annotScore)
    else:
        scoreAll = True
        # if annotScore is False:
        #     print(srcLn)
        #     print(trgtLn)
    return scoreAll, silenceRate


def getAllScoreNotProblematicOriented(binSc0, binSc1, binSc2, binSc3, binSc4, binSc5, binSc6, binSc7, binSc9,
                                   binSc10, binSc11, binSc99, silenceRate):
    """ use a vote system divided in 3 categories of scores divided according to their precision and trust """
    mostPreciseScores = [bSc for bSc in [binSc0, binSc9] if bSc is not None]
    highPreciseScores = [bSc for bSc in [binSc4, binSc10] if bSc is not None]
    lowPreciseScores = [bSc for bSc in [binSc1, binSc2, binSc5, binSc6] if bSc is not None]
    # this is not-problematic SP oriented
    nbTrueInMostScores = sum([1 if sc is True else 0 for sc in mostPreciseScores])
    nbTrueInHighScores = sum([1 if sc is True else 0 for sc in highPreciseScores])
    nbTrueInLowScores = sum([1 if sc is True else 0 for sc in lowPreciseScores])

    # both the most-precise
    if nbTrueInMostScores >= 2:
        scoreAll = True
    # one most-precise and one high
    elif nbTrueInMostScores == 1 and nbTrueInHighScores >= 1:
        scoreAll = True

    # # one most-precise
    # if nbTrueInMostScores >= 1:
    #     scoreAll = True
    # # two high-scores
    # elif nbTrueInHighScores >= 2:
    #     scoreAll = True
    # # one high-score and one or more low-scores
    # elif nbTrueInHighScores == 1 and nbTrueInLowScores >= 1:
    #     scoreAll = True
    # # all the four low-scores
    # elif nbTrueInLowScores >= 4:
    #     scoreAll = True

    # if no heuristic helps, add to the silence
    elif nbTrueInHighScores + nbTrueInLowScores == 0:
        silenceRate['all'] += 1
        scoreAll = None
    else:
        scoreAll = False
    return scoreAll, silenceRate, nbTrueInMostScores, nbTrueInHighScores, nbTrueInLowScores


def checkHeuristicsAgainstAnnotatedCorpusFile(annotationFolderPath, discardTableOfContent=False, inverseScores=False):
    """ given the path to an annotated corpus, it checks if the extractors correspond to the annotation """
    confMatrix0, confMatrix1, confMatrix2, confMatrixAll = [], [], [], []
    confMatrix3, confMatrix4, confMatrix5, confMatrix6, confMatrix7, confMatrix8 = [], [], [], [], [], []
    confMatrix9, confMatrix10, confMatrix11, confMatrix99 = [], [], [], []
    validLine = True
    totalSpAnalyzed = 0
    silenceRate = {0: 0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0,  8:0, 9:0, 10:0, 11:0, 99:0, 'all':0}
    # if there is only one annotation path, put it in a list
    if type(annotationFolderPath) is str:
        annotationFolderPath = [annotationFolderPath]
    # get the file paths
    for annotPath in annotationFolderPath:
        annotationFilePath = u'{0}sampleAnnotation.tsv'.format(annotPath)
        referenceFilePath = u'{0}sampleReference.tsv'.format(annotPath)
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
                    # get the en-fr lines
                    enLn = srcLn if u'en-fr' in refPath else trgtLn
                    frLn = trgtLn if u'en-fr' in refPath else srcLn
                    # annotation score
                    annotScore = getAnnotationScore(annot, focus=u'all', negativesOnly=False)
                    if annotScore is not None:
                        # discard or not the table content and index`
                        if discardTableOfContent is not False:
                            cntxtScores = getContextScores(refIndex, srcLines, trgtLines)
                            docLoc = refIndex / len(srcLines)
                            contentTableScore = tableOfContents(srcLn, trgtLn, nTokens=4,
                                                                contextScores=cntxtScores, placeInDocument=docLoc)
                            validLine = False if contentTableScore < 0.2 else True
                        if validLine is True:
                            totalSpAnalyzed += 1
                            # number coincidence #######################
                            fcThreshold = 0.5 if inverseScores is not False else 1.0
                            confMatrix0, silenceRate, score0, binSc0 = countAndPopulate(nbMismatch, 0, srcLn, trgtLn,
                                                                        annotScore, silenceRate, confMatrix0,
                                                                        fcThreshold)
                            # disproportionate length #######################
                            fcThreshold = 0.35 if inverseScores is not False else 0.7
                            confMatrix1, silenceRate, score1, binSc1 = countAndPopulate(compareLengths, 1, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix1,
                                                                                fcThreshold)
                            # cognates #######################
                            fcThreshold = 0.1 if inverseScores is not False else 0.2
                            confMatrix2, silenceRate, score2, binSc2 = countAndPopulate(cognateCoincidence, 2, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix2,
                                                                                fcThreshold)
                            # faux-amis coincidence #######################
                            fcThreshold = float('-inf') if inverseScores is not False else 0.6
                            confMatrix3, silenceRate, score3, binSc3 = countAndPopulate(fauxAmis, 3, enLn, frLn,
                                                                                annotScore, silenceRate, confMatrix3,
                                                                                fcThreshold)
                            # ion suffixes mismatch #######################
                            fcThreshold = 0.5 if inverseScores is not False else 0.65
                            confMatrix4, silenceRate, score4, binSc4 = countAndPopulate(ionSuffixMismatch, 4, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix4,
                                                                                fcThreshold)
                            # stop words mismatch #######################
                            fcThreshold = 0.3 if inverseScores is not False else 0.9
                            confMatrix5, silenceRate, score5, binSc5 = countAndPopulate(stopWordsMismatch, 5, enLn, frLn,
                                                                                annotScore, silenceRate, confMatrix5,
                                                                                fcThreshold)
                            # spell check #######################
                            fcThreshold = 0.25 if inverseScores is not False else 0.85
                            confMatrix6, silenceRate, score6, binSc6 = countAndPopulate(spellingCheck, 6, enLn, frLn,
                                                                                annotScore, silenceRate, confMatrix6,
                                                                                fcThreshold)
                            # url detection #######################
                            fcThreshold = 0.9 if inverseScores is not False else 0.95
                            confMatrix7, silenceRate, score7, binSc7 = countAndPopulate(urlMismatch, 7, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix7,
                                                                                fcThreshold)
                            # monolingual sentences detection #######################
                            fcThreshold = 0.95 if inverseScores is not False else float('inf')
                            confMatrix8, silenceRate, score8, binSc8 = countAndPopulate(monoling, 8, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix8,
                                                                                fcThreshold)
                            # starbucks word by words translation mismatch #######################
                            fcThreshold = 0.25 if inverseScores is not False else 0.65
                            confMatrix9, silenceRate, score9, binSc9 = countAndPopulate(starbucksTranslationMismatch, 9, enLn, frLn,
                                                                                annotScore, silenceRate, confMatrix9,
                                                                                fcThreshold)
                            # punctuation and symbols mismatch #######################
                            fcThreshold = 0.5 if inverseScores is not False else 0.85
                            confMatrix10, silenceRate, score10, binSc10 = countAndPopulate(punctAndSymb, 10, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix10,
                                                                                fcThreshold)
                            # gibberish presence #######################
                            fcThreshold = 0.1 if inverseScores is not False else 0.85
                            confMatrix11, silenceRate, score11, binSc11 = countAndPopulate(gibberish, 11, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix11,
                                                                                fcThreshold)
                            # table of contents mismatch detector #######################
                            fcThreshold = 0.65 if inverseScores is not False else 0.75
                            confMatrix99, silenceRate, score99, binSc99 = countAndPopulate(tableOfContentsMismatch, 99, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix99,
                                                                                fcThreshold)
                            # all together #######################
                            if inverseScores is not False:
                                scoreAll, silenceRate = getAllScoreProblematicOriented(binSc0, binSc1,
                                                                                                    binSc2, binSc3,
                                                                                                    binSc4, binSc5,
                                                                                                    binSc6, binSc7,
                                                                                                    binSc8,
                                                                                                    binSc9, binSc10,
                                                                                                    binSc11, binSc99,
                                                                                                    silenceRate)
                                # populate the confusion matrix except if there is silence
                                if scoreAll is not None:
                                    confMatrixAll = populateConfMatrix(scoreAll, annotScore, confMatrixAll)
                            else:
                                scoreAll, silenceRate, most, high, low = getAllScoreNotProblematicOriented(binSc0, binSc1,
                                                                                                    binSc2, binSc3,
                                                                                                    binSc4, binSc5,
                                                                                                    binSc6, binSc7,
                                                                                                    binSc9, binSc10,
                                                                                                    binSc11, binSc99,
                                                                                                    silenceRate)
                                # populate the confusion matrix except if there is silence
                                if scoreAll is not None:
                                    # if scoreAll != annotScore:
                                    #     print(11111, index, scoreAll, annotScore, most, high, low)
                                    #     print(222, binSc0, binSc1, binSc2, binSc3, binSc4, binSc5, binSc6, binSc7, binSc9,
                                    #         binSc10, binSc11, binSc99)
                                    confMatrixAll = populateConfMatrix(scoreAll, annotScore, confMatrixAll)

    print(u'NUMBER COINCIDENCE')
    print(confMatrix0)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix0)
    else: getInversePrecisionRecallAccuracy(confMatrix0)
    print()
    print(u'DISPROPORTIONATE TOK LENGTH')
    print(confMatrix1)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix1)
    else: getInversePrecisionRecallAccuracy(confMatrix1)
    print()
    print(u'COGNATES COINCIDENCE')
    print(confMatrix2)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix2)
    else: getInversePrecisionRecallAccuracy(confMatrix2)
    print()
    print(u'FAUX AMIS COINCIDENCE')
    print(confMatrix3)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix3)
    else: getInversePrecisionRecallAccuracy(confMatrix3)
    print()
    print(u'ION SUFFIXES MISMATCH')
    print(confMatrix4)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix4)
    else: getInversePrecisionRecallAccuracy(confMatrix4)
    print()
    print(u'STOP WORDS MISMATCH')
    print(confMatrix5)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix5)
    else: getInversePrecisionRecallAccuracy(confMatrix5)
    print()
    print(u'SPELL CHECK')
    print(confMatrix6)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix6)
    else: getInversePrecisionRecallAccuracy(confMatrix6)
    print()
    print(u'URL DETECTION')
    print(confMatrix7)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix7)
    else: getInversePrecisionRecallAccuracy(confMatrix7)
    print()
    print(u'MONOLING. DETECTION')
    print(confMatrix8)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix8)
    else: getInversePrecisionRecallAccuracy(confMatrix8)
    print()
    print(u'STARBUCKS W-by-W TRANSLATION MISMATCH')
    print(confMatrix9)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix9)
    else: getInversePrecisionRecallAccuracy(confMatrix9)
    print()
    print(u'PUNCT. AND SYMB. MISMATCH')
    print(confMatrix10)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix10)
    else: getInversePrecisionRecallAccuracy(confMatrix10)
    print()
    print(u'GIBBERISH PRESENCE')
    print(confMatrix11)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix11)
    else: getInversePrecisionRecallAccuracy(confMatrix11)
    print()
    print(u'TABLE OF CONTENTS')
    print(confMatrix99)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix99)
    else: getInversePrecisionRecallAccuracy(confMatrix99)
    print()
    print(u'ALL MIXED')
    print(confMatrixAll)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrixAll)
    else: getInversePrecisionRecallAccuracy(confMatrixAll)
    print()
    print('SILENCE rate')
    print(silenceRate)
    print(u'\nTOTAL SP ANALYZED : ', totalSpAnalyzed)


def checkOneHeuristicQualAgainstManEval(annotFolderPathList, heuristicId, discardTableOfContent=False,
                                        thresholdLimit=0.5, focus=u'all', inverseScores=False):
    """ given the path to an annotated corpus, it checks if the extractors correspond to the annotation """
    confMatrix = []
    validLine = True
    silenceRate = 0
    totalLines = 0
    # check the annotation folder path is a list
    if type(annotFolderPathList) is str:
        annotFolderPathList = [annotFolderPathList]
    for annotationFolderPath in annotFolderPathList:
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
            # discard or not the table content and index
            if discardTableOfContent is not False:
                cntxtScores = getContextScores(refIndex, srcLines, trgtLines)
                docLoc = refIndex / len(srcLines)
                contentTableScore = tableOfContents(srcLn, trgtLn, nTokens=4,
                                        contextScores=cntxtScores, placeInDocument=docLoc)
                validLine = False if contentTableScore < 0.37 else True
            # calculate the score
            if validLine is True:
                # get the human annotation
                annot = annotationLines[index]
                # get the src-trgt lines
                srcLn = srcLines[refIndex].replace(u'\n', u'')
                trgtLn = trgtLines[refIndex].replace(u'\n', u'')
                # get the english-french lines
                enLn = srcLn if u'en-fr' in refPath else trgtLn
                frLn = trgtLn if u'en-fr' in refPath else srcLn
                # annotation score
                annotScore = getAnnotationScore(annot, focus, negativesOnly=False)
                if annotScore is not None:
                    # add to the total
                    totalLines += 1
                    # number coincidence
                    if heuristicId == 0:
                        score = nbMismatch(srcLn, trgtLn, includeNumberNames=True)
                    # disproportionate length
                    if heuristicId == 1:
                        score = compareLengths(srcLn, trgtLn, onlyLongSentOfNPlusLen=10)
                    # cognates
                    if heuristicId == 2:
                        score = cognateCoincidence(srcLn, trgtLn)
                    # faux amis
                    if heuristicId == 3:
                        score = fauxAmis(enLn, frLn)
                    # ion suffix
                    if heuristicId == 4:
                        score = ionSuffixMismatch(enLn, frLn)
                    # stop words translation mismatch
                    if heuristicId == 5:
                        score = stopWordsMismatch(enLn, frLn)
                    # spelling check
                    if heuristicId == 6:
                        score = spellingCheck(enLn, frLn)
                    # url presence
                    if heuristicId == 7:
                        score = urlMismatch(srcLn, trgtLn)
                    # monolinguistic content
                    if heuristicId == 8:
                        score = monoling(srcLn, trgtLn)
                    # word by word translation content
                    if heuristicId == 9:
                        score = starbucksTranslationMismatch(enLn, frLn)
                    # punctuation mismatch
                    if heuristicId == 10:
                        score = punctAndSymb(srcLn, trgtLn)
                    # gibberish presence
                    if heuristicId == 11:
                        score = gibberish(srcLn, trgtLn)
                    # table of content
                    if heuristicId == 99:
                        # cntxtScores = getContextScores(refIndex, srcLines, trgtLines)
                        # docLoc = refIndex / len(srcLines)
                        score = tableOfContentsMismatch(srcLn, trgtLn, nTokens=4)
                    # count the silence rate
                    if score is None:
                        silenceRate += 1
                    # populate the matrix
                    else:
                        score = True if score >= thresholdLimit else False
                        confMatrix = populateConfMatrix(score, annotScore, confMatrix)
    # print(confMatrix)
    if inverseScores is False:
        precision, recall, f1, accuracy = getPrecisionRecallAccuracy(confMatrix, verbose=False)
    # calculate the inverse scores
    else:
        precision, recall, f1, accuracy = getInversePrecisionRecallAccuracy(confMatrix, verbose=False)
    # get the silence rate
    silenceRate = silenceRate / totalLines
    print(u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}'.format(thresholdLimit, precision, recall, f1, accuracy, silenceRate))


# compare to human annot
def comparePredictionsToGoldStandard(pathPred, pathGold, countSilenceAsBadlyPredicted=True):
    confMatrix = []
    with open(pathPred) as predFile:
        with open(pathGold) as goldFile:
            pred = predFile.readline().replace(u"\n", u"")
            gold = goldFile.readline().replace(u"\n", u"")
            while pred:
                # make pred and gold comparable
                gold = getAnnotationScore(gold, focus=u'all', negativesOnly=False)
                # if the prediction is a silence
                if pred == u"na":
                    if countSilenceAsBadlyPredicted is True:
                        if gold is None:
                            pred = None
                        else:
                            pred = False if gold is True else True
                    else:
                        pred = None
                # if the prediction is a number
                elif int(pred) == 1:
                    pred = True
                else:
                    pred = False
                # compare the two
                confMatrix = populateConfMatrix(pred, gold, confMatrix)
                # next line
                pred = predFile.readline().replace(u"\n", u"")
                gold = goldFile.readline().replace(u"\n", u"")
    getPrecisionRecallAccuracy(confMatrix, True)
    getInversePrecisionRecallAccuracy(confMatrix, True)


def checkTmopAgainstAnnotatedCorpusFile(tmopPaths, annotationPath):
    # if there is only one tmop pred path, put it in a list
    if type(tmopPaths) is str:
        tmopPaths = [tmopPaths]
    # open the manual annotation file
    with open(annotationPath) as annotFile:
        # save the gold annot in a list
        annotList = []
        annotLn = annotFile.readline()
        while annotLn:
            # annotation score
            annotScore = getAnnotationScore(annotLn.replace(u"\n", u""))
            # add to the list
            annotList.append([annotScore, None])
            # next line
            annotLn = annotFile.readline()
    for tPath in tmopPaths:
        tmopPred = True if u"accept_" in tPath else False
        # open the tmop prediction file
        with open(tPath) as tmopPredFile:
            # get the index of the accepted/rejected lines
            tmopLn = tmopPredFile.readline()
            while tmopLn:
                index = int(tmopLn.split(u'\t')[0])
                annotList[index][1] = tmopPred
                # next line
                tmopLn = tmopPredFile.readline()
    # complete the annot list if one amongst accepter/rejected is missing
    if len(tmopPaths) != 1:
        tmopPred = False if tmopPred is True else True
        annotList = map(lambda x: [x[0], tmopPred] if x[1] is None else x, annotList)
    # make the confusion matrix
    confMatrx = []
    for annotPred in annotList:
        print(annotPred)
        confMatrx = populateConfMatrix(annotPred[1], annotPred[0], confMatrx)
    # print
    print(confMatrx, u'\n')
    print(getPrecisionRecallAccuracy(confMatrx), u'\n')
    print(getInversePrecisionRecallAccuracy(confMatrx))




# count the time the algorithm takes to run
startTime = utilsOs.countTime()

annotatedFolderPathList = [u'./002manuallyAnnotated/', u'./003negativeNaiveExtractors/000manualAnnotation/']

# # check for potential usable clues to make heuristics
# for heurTupl in [(u'nb', 0), (u'len', 1), (u'cog', 2), (u'fa', 3), (u'ion', 4), (u'sw', 5), (u'spell', 6), (u'url', 7),
#                  (u'mono', 8), (u'strBcks', 9), (u'punct', 10), (u'gibb', 11), (u'tabl', 99)]:
#     print(u'\n##################################   {0}   ######################################\n'.format(heurTupl[0]))
#     for threshold in np.arange(0.05, 1.05, 0.05):
#         # get the metrics to find the PROBLEMATIC SPs
#         # checkOneHeuristicQualAgainstManEval(annotatedFolderPathList, 0, False, threshold, focus=u'all', inverseScores=True)
#         # get the metrics to find the NON-PROBLEMATIC SPs
#         checkOneHeuristicQualAgainstManEval(annotatedFolderPathList, heurTupl[1], False, threshold, focus=u'all', inverseScores=False)

# check the extractors on the annotated corpus
# checkHeuristicsAgainstAnnotatedCorpusFile(annotatedFolderPathList, discardTableOfContent=False, inverseScores=True)

# check a prediction file against the annotated corpus 2021
# predFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/sample2021/train7Msample2021randSvmClassif.pred"
# goldFilePath = u"/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/wholeAnnotated2021SP/sampleAnnotation.tsv"
# comparePredictionsToGoldStandard(predFilePath, goldFilePath, countSilenceAsBadlyPredicted=True)

# check the TMOP results on the 2021 annotated corpus
tmopPathAccept = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/TMOP/output/output2021noWordAlign/accept_TwentyNo__sample.en"
tmopPathReject = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/TMOP/output/output2021noWordAlign/reject_TwentyNo__sample.en"
# tmopPathAccept = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/TMOP/output/accept_TwentyNo__sample.en"
# tmopPathReject = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/TMOP/output/reject_TwentyNo__sample.en"
annotPath = u"/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/wholeAnnotated2021SP/sampleAnnotation.tsv"
checkTmopAgainstAnnotatedCorpusFile([tmopPathAccept, tmopPathReject], annotPath)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))