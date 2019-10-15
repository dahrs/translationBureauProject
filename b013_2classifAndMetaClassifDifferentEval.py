#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsML
from b003heuristics import *


acumulGoodPrecision, acumulGoodRecall, acumulAccuracy, acumulBadPrecision, acumulBadRecall = 0, 0, 0, 0, 0
# model path
classifModelPaths = [u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_scores_rdmForest.pickle"]
# test paths
testFeatureFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/scoresAndMetaData.tsv",
                           "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/scoresAndMetaData.tsv",
                           "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/scoresAndMetaData.tsv",
                           "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/scoresAndMetaData.tsv"]
pathsToTestClassificationFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/sampleAnnotation.tsv",
                                  "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/sampleAnnotation.tsv",
                                  "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/sampleAnnotation.tsv",
                                  "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/sampleAnnotation.tsv"]

for classifModelPath in classifModelPaths:
    vectorDim = 60 if "scoresAndMetaData" in classifModelPath else 13
    print(u"\n", classifModelPath.split(u"/")[-1].replace(u".pickle", u""), u"\tvector dimension: {0}".format(vectorDim))
    # change the path of the feature files to the right ones if the dimension is 13 instead of 60
    if vectorDim in [13, 15]:
        pathsToTestFeatureFiles = [fp.replace(u'scoresAndMetaData', u'scores') for fp in testFeatureFiles]

    # load classifier
    classifier = utilsML.loadModel(classifModelPath)
    # getModelEval(pathsToTestFeatureFiles, pathsToTestClassificationFiles, classifier, classifBinary)
    gp, gr, a, bp, br = getModelEvalGoodAndBad(pathsToTestFeatureFiles, pathsToTestClassificationFiles, classifier,
                                                   makeClassifBinary=True, verbose=True)
