#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsML
from b003heuristics import *
import argparse
parser = argparse.ArgumentParser()
parser.add_argument(u'-s', u'--section', type=int, default=0,
                    help=u'section of the data to apply the algorithm')
args = parser.parse_args()


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
outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2randForest/'

# train the models
# svmClassif = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=13)
# RandFClassif = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=60)

# Dump the models
### utilsML.dumpModel(svmClassif, u'{0}svmBinMod.pickle'.format(outputPath))
### utilsML.dumpModel(RandFClassif, u'{0}rfBinMod.pickle'.format(outputPath))


# load the models
# svmClassif = utilsML.loadModel(u'{0}svmBinMod.pickle'.format(outputPath))
# randFClassif = utilsML.loadModel(u'{0}rfBinMod.pickle'.format(outputPath))

# get the predictions, extract the sps
# applyClassifierToExtract(randFClassif, randFClassif, extractingPath, outputPath,
#                          featDim=(60,60), applyOnSection=args.section)

# predict and dump the predict on the BT2 17K-SPs corpus instead of extracting
# inputScFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.scores"
# inputScMetaFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.scoresAndMetaData"
# outputFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.randSvmClassif.pred"
# applyClassifierToGetPred(randFClassif, svmClassif,
#                              inputScFilePath, inputScMetaFilePath, outputFilePath, featDim=(60,13))

# join the different sections of the random forest model extraction
def openAndAppend(sctPath, totalPath):
    with open(sctPath) as sctFile:
        sctLns = sctFile.readlines()
        utilsOs.appendMultLinesToFile(sctLns, totalPath, addNewLine=False)

noProblm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2randForest/noProblematic/"
problm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2randForest/problematic/"
npExtrEn, pExtrEn = u"{0}extracted.en".format(noProblm), u"{0}extracted.en".format(problm)
npExtrFr, pExtrFr = u"{0}extracted.fr".format(noProblm), u"{0}extracted.fr".format(problm)
npRef, pRef = u"{0}reference.tsv".format(noProblm), u"{0}reference.tsv".format(problm)
npSc, pSc = u"{0}scores.tsv".format(noProblm), u"{0}scores.tsv".format(problm)
npScMt, pScMt = u"{0}scoresAndMetaData.tsv".format(noProblm), u"{0}scoresAndMetaData.tsv".format(problm)
for nb in range(12):
    npExtrEnNb, pExtrEnNb = u"{0}extracted{1}.en".format(noProblm, nb), u"{0}extracted{1}.en".format(problm, nb)
    openAndAppend(npExtrEnNb, npExtrEn)
    openAndAppend(pExtrEnNb, pExtrEn)
    npExtrFrNb, pExtrFrNb = u"{0}extracted{1}.fr".format(noProblm, nb), u"{0}extracted{1}.fr".format(problm, nb)
    openAndAppend(npExtrFrNb, npExtrFr)
    openAndAppend(pExtrFrNb, pExtrFr)
    npRefNb, pRefNb = u"{0}reference{1}.tsv".format(noProblm, nb), u"{0}reference{1}.tsv".format(problm, nb)
    openAndAppend(npRefNb, npRef)
    openAndAppend(pRefNb, pRef)
    npScNb, pScNb = u"{0}scores{1}.tsv".format(noProblm, nb), u"{0}scores{1}.tsv".format(problm, nb)
    openAndAppend(npScNb, npSc)
    openAndAppend(pScNb, pSc)
    npScMtNb, pScMtNb = u"{0}scoresAndMetaData{1}.tsv".format(noProblm, nb), u"{0}scoresAndMetaData{1}.tsv".format(problm, nb)
    openAndAppend(npScMtNb, npScMt)
    openAndAppend(pScMtNb, pScMt)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))