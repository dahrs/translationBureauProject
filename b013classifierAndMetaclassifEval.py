#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs
from b003heuristics import *
import numpy as np
import pandas as pd


# count the time the algorithm takes to run
startTime = utilsOs.countTime()


# for foldPath in ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/",
#                  "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/",
#                  "/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/",
#                  "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/",
#                  "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/"]:
#     addAndDumpMetaDataToScoreFeatures(foldPath)

# addAndDumpMetaDataToScoreFeatures(u'/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/test/')


# TRAIN SET - NON PROBLEMATIC + PROBLEMATIC
pathsToFeaturesTsvFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/scoresAndMetaData.tsv",
                            "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/scoresAndMetaData.tsv",
                            "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/scoresAndMetaData.tsv"]
pathsToClassificationTsvFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/sampleAnnotation.tsv",
                                       "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/sampleAnnotation.tsv",
                            "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/sampleAnnotation.tsv"]


# TEST SET - NON PROBLEMATIC + PROBLEMATIC
pathsToTestFeatureFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/scoresAndMetaData.tsv",
                                 "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/scoresAndMetaData.tsv"]
pathsToTestClassificationFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/sampleAnnotation.tsv",
                                        "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/sampleAnnotation.tsv"]

# TEST SET - PROBLEMATIC
# pathsToTestFeatureFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/scoresAndMetaData.tsv"]
# pathsToTestClassificationFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/sampleAnnotation.tsv"]

# TEST SET - NON PROBLEMATIC
# pathsToTestFeatureFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/scoresAndMetaData.tsv"]
# pathsToTestClassificationFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/sampleAnnotation.tsv"]

# TEST SET - RANOMD MIX OF PROBLEMATIC & NON PROBLEMATIC
# pathsToTestFeatureFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/mixed/scoresAndMetaData.tsv"]
# pathsToTestClassificationFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/mixed/sampleAnnotation.tsv"]

# CLASSIFIERS
classifBinary = True
classifType = False

acumulGoodPrecision, acumulGoodRecall, acumulAccuracy, acumulBadPrecision, acumulBadRecall = 0, 0, 0, 0, 0
vectorDim = 60  # = 13
# change the feature files if the dimension is 13 instead of 60
if vectorDim in [13, 15]:
    pathsToFeaturesTsvFiles = [fp.replace(u'scoresAndMetaData', u'scores') for fp in pathsToFeaturesTsvFiles]
    pathsToTestFeatureFiles = [fp.replace(u'scoresAndMetaData', u'scores') for fp in pathsToTestFeatureFiles]
# iterate multiple times to get a more reliable mean of all scores
for n in range(10):
    verbose = True if n == 0 else False
    # classifier = trainFeedForwardNNModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifType, vectorDim)
    # classifier = trainMaxEntLinearModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifType, vectorDim)
    classifier = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifType, vectorDim)
    # classifier = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifType, vectorDim)

    # getModelEval(pathsToTestFeatureFiles, pathsToTestClassificationFiles, classifier, classifBinary)
    gp, gr, a, bp, br = getModelEvalGoodAndBad(pathsToTestFeatureFiles, pathsToTestClassificationFiles, classifier, classifBinary, verbose)
    acumulGoodPrecision += gp
    acumulGoodRecall += gr
    acumulAccuracy += a
    acumulBadPrecision += bp
    acumulBadRecall += br
print()
print("GOOD MEAN precision : ", acumulGoodPrecision/10.0)
print("GOOD MEAN recall : ", acumulGoodRecall/10.0)
print("JUST MEAN accuracy : ", acumulAccuracy/10.0)
print("BAD MEAN precision : ", acumulBadPrecision/10.0)
print("BAD MEAN recall : ", acumulBadRecall/10.0)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))