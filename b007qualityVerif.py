#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys, os
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs
from b003heuristics import *

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


def checkHeuristicsAgainstAnnotatedCorpusFile(annotationFolderPath):
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

print(os.path.realpath(__file__))
# check the extractors on the annotated corpus
checkHeuristicsAgainstAnnotatedCorpusFile(u'./002manuallyAnnotated/')

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))