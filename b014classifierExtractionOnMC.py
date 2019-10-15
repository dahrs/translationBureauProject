#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsML
from b003heuristics import *
import numpy as np
import pandas as pd


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# CLASSIFIERS
classifBinary = True
classifGroup = False

# TRAIN SET - NON PROBLEMATIC + PROBLEMATIC = 1721 SPs
pathsToFeaturesTsvFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/scoresAndMetaData.tsv",
                            "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/scoresAndMetaData.tsv",
                            "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/scoresAndMetaData.tsv"]
pathsToClassificationTsvFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/sampleAnnotation.tsv",
                                       "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/sampleAnnotation.tsv",
                            "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/sampleAnnotation.tsv"]

# paths
extractingPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2/'

# train the models
# svmClassif = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=13)
# RandFClassif = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=60)

# Dump the models
### utilsML.dumpModel(svmClassif, u'{0}svmBinMod.pickle'.format(outputPath))
### utilsML.dumpModel(RandFClassif, u'{0}rfBinMod.pickle'.format(outputPath))


# load the models
svmClassif = utilsML.loadModel(u'{0}svmBinMod.pickle'.format(outputPath))
RandFClassif = utilsML.loadModel(u'{0}rfBinMod.pickle'.format(outputPath))

# get the predictions, extract the sps
applyClassifierToExtract(RandFClassif, svmClassif, extractingPath, outputPath)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))