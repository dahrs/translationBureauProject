#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs
from b003heuristics import *
from scipy.stats import pearsonr
import numpy as np
import pandas as pd


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


def getPrecisionRecallAccuracy(confMatrix, verbose=True):
    precision = confMatrix[u'real pos'][u'pred pos'] / (confMatrix[u'real pos'][u'pred pos']+confMatrix[u'real pos'][u'pred neg'])
    recall = confMatrix[u'real pos'][u'pred pos'] / (confMatrix[u'real pos'][u'pred pos']+confMatrix[u'real neg'][u'pred pos'])
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
        - all: good alignment and good quality and no gibberish"""
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
            # if we want only the negatives we replace true with None (silence)
            if negativesOnly == False:
                return True
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


def checkHeuristicsAgainstAnnotatedCorpusFile(annotationFolderPath, discardTableOfContent=False, inverseScores=False):
    """ given the path to an annotated corpus, it checks if the extractors correspond to the annotation """
    confMatrix0, confMatrix1, confMatrix2, confMatrix0and1, confMatrixAll = [], [], [], [], []
    confMatrix3, confMatrix4, confMatrix5, confMatrix6, confMatrix7, confMatrix8 = [], [], [], [], [], []
    confMatrix99 = []
    validLine = True
    totalSpAnalyzed = 0
    silenceRate = {0: 0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0,  7:0,  8:0, 99:0,  'all':0}
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
                        # discard or not the table content and index
                        if discardTableOfContent != False:
                            cntxtScores = getContextScores(refIndex, srcLines, trgtLines)
                            docLoc = refIndex / len(srcLines)
                            contentTableScore = tableOfContents(srcLn, trgtLn, nTokens=4,
                                                                contextScores=cntxtScores, placeInDocument=docLoc)
                            validLine = False if contentTableScore < 0.2 else True
                        if validLine == True:
                            totalSpAnalyzed += 1
                            # number coincidence #######################
                            confMatrix0, silenceRate, score0, binSc0 = countAndPopulate(nbMismatch, 0, srcLn, trgtLn,
                                                                        annotScore, silenceRate, confMatrix0,
                                                                        fcThreshold=0.25)
                            # disproportionate length #######################
                            confMatrix1, silenceRate, score1, binSc1 = countAndPopulate(compareLengths, 1, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix1,
                                                                                fcThreshold=0.45)
                            # cognates #######################
                            confMatrix2, silenceRate, score2, binSc2 = countAndPopulate(cognateCoincidence, 2, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix2,
                                                                                fcThreshold=0.05)
                            # nb mismatch and length #######################
                            scores = [score0, score1]
                            absolute = len(scores)
                            howManyFalse = sum([1 for e in scores if e is False])
                            if howManyFalse == absolute:
                                score0and1 = False
                            else:
                                score0and1 = True
                            confMatrix0and1 = populateConfMatrix(score0and1, annotScore, confMatrix0and1)
                            # faux-amis coincidence #######################
                            confMatrix3, silenceRate, score3, binSc3 = countAndPopulate(fauxAmis, 3, enLn, frLn,
                                                                                annotScore, silenceRate, confMatrix3,
                                                                                fcThreshold=0.5)
                            # ion suffixes mismatch #######################
                            confMatrix4, silenceRate, score4, binSc4 = countAndPopulate(ionSuffixMismatch, 4, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix4,
                                                                                fcThreshold=0.5)
                            # stop words mismatch #######################
                            confMatrix5, silenceRate, score5, binSc5 = countAndPopulate(stopWordsMismatch, 5, enLn, frLn,
                                                                                annotScore, silenceRate, confMatrix5,
                                                                                fcThreshold=0.3)
                            # spell check #######################
                            confMatrix6, silenceRate, score6, binSc6 = countAndPopulate(spellingCheck, 6, enLn, frLn,
                                                                                annotScore, silenceRate, confMatrix6,
                                                                                fcThreshold=0.25)
                            # url detection #######################
                            confMatrix7, silenceRate, score6, binSc7 = countAndPopulate(hasUrl, 7, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix7,
                                                                                fcThreshold=0.85)
                            # monolingual sentences detection #######################
                            confMatrix8, silenceRate, score6, binSc8 = countAndPopulate(monoling, 8, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix8,
                                                                                fcThreshold=1.0)
                            # table of contents detector #######################
                            confMatrix99, silenceRate, score99, binSc99 = countAndPopulate(tableOfContents, 99, srcLn, trgtLn,
                                                                                annotScore, silenceRate, confMatrix99,
                                                                                fcThreshold=0.2)
                            # all together #######################
                            mostPreciseScores = [bSc for bSc in [binSc2, binSc1, binSc8] if bSc is not None]
                            highPreciseScores = [bSc for bSc in [binSc0, binSc5, binSc6, binSc7] if bSc is not None]
                            lowPreciseScores = [bSc for bSc in [binSc3, binSc4, binSc99] if bSc is not None]
                            # this is problematic SP oriented
                            nbFalseInHighScores = sum([1 if sc is False else 0 for sc in highPreciseScores])
                            nbFalseInLowScores = sum([1 if sc is False else 0 for sc in lowPreciseScores])
                            if False in mostPreciseScores:
                                scoreAll = False
                                # print('most precise alone', annotScore)
                            elif nbFalseInHighScores >= 2:
                                scoreAll = False
                                # print('two high', annotScore)
                            elif nbFalseInHighScores == 1 and nbFalseInLowScores >= 1:
                                scoreAll = False
                                # print('one high, one low', annotScore)
                            elif nbFalseInLowScores == 3:
                                scoreAll = False
                                # print('three low', annotScore)
                            # if no heuristic helps, add to the silence
                            elif nbFalseInHighScores+nbFalseInLowScores == 0:
                                silenceRate['all'] += 1
                                # print('silence', annotScore)
                            else:
                                scoreAll = True
                                # if annotScore is False:
                                #     print(srcLn)
                                #     print(trgtLn)
                            # populate the confusion matrix except if there is silence
                            if nbFalseInHighScores+nbFalseInLowScores != 0:
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
    print(u'NUMBER COINCIDENCE AND DISPROPORTIONATE TOK LENGTH')
    print(confMatrix0and1)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix0and1)
    else: getInversePrecisionRecallAccuracy(confMatrix0and1)
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
                                        threshold=0.5, focus=u'all', inverseScores=False):
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
            if discardTableOfContent != False:
                cntxtScores = getContextScores(refIndex, srcLines, trgtLines)
                docLoc = refIndex / len(srcLines)
                contentTableScore = tableOfContents(srcLn, trgtLn, nTokens=4,
                                        contextScores=cntxtScores, placeInDocument=docLoc)
                validLine = False if contentTableScore < 0.37 else True
            #calculate the score
            if validLine == True:
                # get the human annotation
                annot = annotationLines[index]
                # get the src-trgt lines
                srcLn = srcLines[refIndex].replace(u'\n', u'')
                trgtLn = trgtLines[refIndex].replace(u'\n', u'')
                # get the enfglish-french lines
                enLn = srcLn if u'en-fr' in refPath else trgtLn
                frLn = trgtLn if u'en-fr' in refPath else srcLn
                # annotation score
                annotScore = getAnnotationScore(annot, focus, negativesOnly=False)
                if annotScore != None:
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
                        score = ionSuffixMismatch(srcLn, trgtLn)
                    # stop words translation mismatch
                    if heuristicId == 5:
                        score = stopWordsMismatch(enLn, frLn)
                    # spelling check
                    if heuristicId == 6:
                        score = spellingCheck(enLn, frLn)
                    # spelling check
                    if heuristicId == 6:
                        score = spellingCheck(enLn, frLn)
                    # url presence
                    if heuristicId == 7:
                        score = hasUrl(srcLn, trgtLn)
                    # monolinguistic content
                    if heuristicId == 8:
                        score = monoling(srcLn, trgtLn)
                    # table of content
                    if heuristicId == 99:
                        cntxtScores = getContextScores(refIndex, srcLines, trgtLines)
                        docLoc = refIndex / len(srcLines)
                        score = tableOfContents(srcLn, trgtLn, nTokens=4,
                                                contextScores=cntxtScores, placeInDocument=docLoc)
                    # count the silence rate
                    if score is None:
                        silenceRate += 1
                    # populate the matrix
                    else:
                        score = True if score >= threshold else False
                        confMatrix = populateConfMatrix(score, annotScore, confMatrix)
    # print(confMatrix)
    if inverseScores is False:
        precision, recall, f1, accuracy = getPrecisionRecallAccuracy(confMatrix, verbose=False)
    # calculate the inverse scores
    else:
        precision, recall, f1, accuracy = getInversePrecisionRecallAccuracy(confMatrix, verbose=False)
    # get the silence rate
    silenceRate = silenceRate / totalLines
    print(u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}'.format(threshold, precision, recall, f1, accuracy, silenceRate))


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# check for potential usable clues to make heuristics
# annotatedFolderPathList = [u'./002manuallyAnnotated/', u'./003negativeNaiveExtractors/000manualAnnotation/']
# for threshold in np.arange(0.05, 1.05, 0.05):
#     checkOneHeuristicQualAgainstManEval(annotatedFolderPathList, 1, False, threshold, focus=u'all', inverseScores=True)

# check the extractors on the annotated corpus
annotList = [u'./002manuallyAnnotated/', u'./003negativeNaiveExtractors/000manualAnnotation/']
checkHeuristicsAgainstAnnotatedCorpusFile(annotList, discardTableOfContent=True, inverseScores=True)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))