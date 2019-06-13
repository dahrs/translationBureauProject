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


def countAndPopulate(aFunction, functionId, ln1, ln2, annotScore, silenceRateDict, threshold, confMatrix):
    funcScore = aFunction(ln1, ln2)
    # if the score is none (nothing allows to use the heuristic) add to the silence
    if funcScore is None:
        silenceRateDict[functionId] += 1
    else:
        funcScore = True if funcScore >= threshold else False
        confMatrix = populateConfMatrix(funcScore, annotScore, confMatrix)
    return confMatrix, silenceRateDict


def checkHeuristicsAgainstAnnotatedCorpusFile(annotationFolderPath, discardTableOfContent=False, inverseScores=False):
    """ given the path to an annotated corpus, it checks if the extractors correspond to the annotation """
    confMatrix0, confMatrix1, confMatrix2, confMatrix0and1, confMatrixAll = [], [], [], [], []
    confMatrix3, confMatrix4, confMatrix5, confMatrix6, confMatrix99 = [], [], [], [], []
    validLine = True
    totalSpAnalyzed = 0
    silenceRate = {0: 0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 99:0}
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
                            score0 = nbMismatch(srcLn, trgtLn)
                            # if the score is none (nothing allows to use the heuristic) add to the silence
                            if score0 is None:
                                silenceRate[0] += 1
                            else:
                                score0Threshold = 0.2
                                score0 = True if score0 >= score0Threshold else False
                                confMatrix0 = populateConfMatrix(score0, annotScore, confMatrix0)
                            # disproportionate length #######################
                            score1 = compareLengths(srcLn, trgtLn)
                            # if the score is none (nothing allows to use the heuristic) add to the silence
                            if score1 is None:
                                silenceRate[1] += 1
                            else:
                                score1Threshold = 0.25
                                score1 = True if score1 >= score1Threshold else False
                                confMatrix1 = populateConfMatrix(score1, annotScore, confMatrix1)
                            # cognates #######################
                            score2 = cognateCoincidence(srcLn, trgtLn)
                            # if the score is none (nothing allows to use the heuristic) add to the silence
                            if score2 is None:
                                silenceRate[2] += 1
                            else:
                                score2Threshold = 0.05
                                score2 = True if score2 >= score2Threshold else False
                                confMatrix2 = populateConfMatrix(score2, annotScore, confMatrix2)
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
                            score3 = fauxAmis(enLn, frLn)
                            # if the score is none (nothing allows to use the heuristic) add to the silence
                            if score3 is None:
                                silenceRate[3] += 1
                            else:
                                score3Threshold = 0.2
                                score3 = True if score3 >= score3Threshold else False
                                confMatrix3 = populateConfMatrix(score3, annotScore, confMatrix3)
                            # ion suffixes mismatch #######################
                            score4 = ionSuffixMismatch(srcLn, trgtLn)
                            # if the score is none (nothing allows to use the heuristic) add to the silence
                            if score4 is None:
                                silenceRate[4] += 1
                            else:
                                score4Threshold = 0.2
                                score4 = True if score4 >= score4Threshold else False
                                confMatrix4 = populateConfMatrix(score4, annotScore, confMatrix4)
                            # stop words mismatch #######################
                            score5 = stopWordsMismatch(enLn, frLn)
                            # if the score is none (nothing allows to use the heuristic) add to the silence
                            if score5 is None:
                                silenceRate[5] += 1
                            else:
                                score5Threshold = 0.25
                                score5 = True if score5 >= score5Threshold else False
                                confMatrix5 = populateConfMatrix(score5, annotScore, confMatrix5)
                            # spell check #######################
                            score6 = spellingCheck(enLn, frLn)
                            # if the score is none (nothing allows to use the heuristic) add to the silence
                            if score6 is None:
                                silenceRate[6] += 1
                            else:
                                score6Threshold = 0.2
                                score6 = True if score6 >= score6Threshold else False
                                confMatrix6 = populateConfMatrix(score6, annotScore, confMatrix6)
                            # table of contents detector #######################
                            score99 = tableOfContents(srcLn, trgtLn)
                            # if the score is none (nothing allows to use the heuristic) add to the silence
                            if score99 is None:
                                silenceRate[99] += 1
                            else:
                                score99Threshold = 0.2
                                score99 = True if score99 >= score99Threshold else False
                                confMatrix99 = populateConfMatrix(score99, annotScore, confMatrix99)
                            # all together #######################
                            scores = [score0, score1, score2]
                            majority = int(len(scores) / 2) + 1
                            absolute = len(scores)
                            howManyFalse = sum([1 for e in scores if e is False])
                            if howManyFalse >= absolute:
                                scoreAll = False
                            else:
                                scoreAll = True
                            confMatrixAll = populateConfMatrix(scoreAll, annotScore, confMatrixAll)
    print(u'NUMBER COINCIDENCE')
    # print(confMatrix0)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix0)
    else: getInversePrecisionRecallAccuracy(confMatrix0)
    print()
    print(u'DISPROPORTIONATE TOK LENGTH')
    # print(confMatrix1)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix1)
    else: getInversePrecisionRecallAccuracy(confMatrix1)
    print()
    print(u'COGNATES COINCIDENCE')
    # print(confMatrix2)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix2)
    else: getInversePrecisionRecallAccuracy(confMatrix2)
    print()
    print(u'NUMBER COINCIDENCE AND DISPROPORTIONATE TOK LENGTH')
    # print(confMatrix0and1)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix0and1)
    else: getInversePrecisionRecallAccuracy(confMatrix0and1)
    print()
    print(u'FAUX AMIS COINCIDENCE')
    # print(confMatrix3)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix3)
    else: getInversePrecisionRecallAccuracy(confMatrix3)
    print()
    print(u'ION SUFFIXES MISMATCH')
    # print(confMatrix4)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix4)
    else: getInversePrecisionRecallAccuracy(confMatrix4)
    print()
    print(u'STOP WORDS MISMATCH')
    # print(confMatrix5)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix5)
    else: getInversePrecisionRecallAccuracy(confMatrix5)
    print()
    print(u'SPELL CHECK')
    # print(confMatrix6)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix6)
    else: getInversePrecisionRecallAccuracy(confMatrix6)
    print()
    print(u'TABLE OF CONTENTS')
    # print(confMatrix99)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrix99)
    else: getInversePrecisionRecallAccuracy(confMatrix99)
    print()
    print(u'ALL MIXED')
    print(confMatrixAll)
    if inverseScores is False:
        getPrecisionRecallAccuracy(confMatrixAll)
    else: getInversePrecisionRecallAccuracy(confMatrixAll)
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
                        score = compareLengths(srcLn, trgtLn, onlyLongSentOfNLen=10)
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
annotatedFolderPathList = [u'./002manuallyAnnotated/', u'./003negativeNaiveExtractors/000manualAnnotation/']
for threshold in np.arange(0.05, 1.05, 0.05):
    checkOneHeuristicQualAgainstManEval(annotatedFolderPathList, 6, False, threshold, focus=u'all', inverseScores=True)

# check the extractors on the annotated corpus
# annotList = [u'./002manuallyAnnotated/', u'./003negativeNaiveExtractors/000manualAnnotation/']
# checkHeuristicsAgainstAnnotatedCorpusFile(annotList, discardTableOfContent=True, inverseScores=True)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))