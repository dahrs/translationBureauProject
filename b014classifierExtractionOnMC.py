#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsML
from b003heuristics import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(u'-s', u'--section', type=int, default=-1,
                    help=u'section of the data to apply the algorithm')
args = parser.parse_args()

if args.section == -1:
    args.section = None

# join the different sections of the random forest model extraction
def openAndAppend(sctPath, totalPath):
    with open(sctPath) as sctFile:
        sctLns = sctFile.readlines()
        utilsOs.appendMultLinesToFile(sctLns, totalPath, addNewLine=False)


def unifier(noProblm, problm):
    npExtrEn, pExtrEn = u"{0}extracted.en".format(noProblm), u"{0}extracted.en".format(problm)
    npExtrFr, pExtrFr = u"{0}extracted.fr".format(noProblm), u"{0}extracted.fr".format(problm)
    npRef, pRef = u"{0}reference.tsv".format(noProblm), u"{0}reference.tsv".format(problm)
    npSc, pSc = u"{0}scores.tsv".format(noProblm), u"{0}scores.tsv".format(problm)
    npScMt, pScMt = u"{0}scoresAndMetaData.tsv".format(noProblm), u"{0}scoresAndMetaData.tsv".format(problm)
    for nb in range(12):
        print(nb / 12.0, nb)
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
        npScMtNb, pScMtNb = u"{0}scoresAndMetaData{1}.tsv".format(noProblm, nb), u"{0}scoresAndMetaData{1}.tsv".format(
            problm, nb)
        openAndAppend(npScMtNb, npScMt)
        openAndAppend(pScMtNb, pScMt)


##################################################################################################################
# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# CLASSIFIERS
classifBinary = True
classifGroup = False

# TRAIN SET - NON PROBLEMATIC + PROBLEMATIC = 1721 SPs
# trainName = u"train1721-"
# pathsToFeaturesTsvFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/scoresAndMetaData.tsv",
#                             "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/scoresAndMetaData.tsv",
#                             "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/scoresAndMetaData.tsv"]
# pathsToClassificationTsvFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/sampleAnnotation.tsv",
#                                        "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/sampleAnnotation.tsv",
#                             "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/sampleAnnotation.tsv"]


# train the models
# RandFClassif13 = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=13)
# RandFClassif60 = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=60)
# svmClassif13 = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=13)

# Dump the models
### utilsML.dumpModel(RandFClassif13, u'{0}{1}rfBinMod13.pickle'.format(outputPath, trainName))
### utilsML.dumpModel(RandFClassif60, u'{0}{1}rfBinMod60.pickle'.format(outputPath, trainName))
### utilsML.dumpModel(svmClassif13, u'{0}{1}svmBinMod13.pickle'.format(outputPath, trainName))

# # load the models
# randFClassif13 = utilsML.loadModel(u'{0}{1}rfBinMod13.pickle'.format(outputPath, trainName))
# randFClassif60 = utilsML.loadModel(u'{0}{1}rfBinMod60.pickle'.format(outputPath, trainName))
# svmClassif13 = utilsML.loadModel(u'{0}{1}svmBinMod13.pickle'.format(outputPath, trainName))


# # paths
# extractingPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
# outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2/'
# outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2randForest/'

# get the predictions, extract the sps
# applyClassifierToExtract(randFClassif, svmClassif, extractingPath, outputPath,
#                          featDim=(60,13), applyOnSection=args.section)
# applyClassifierToExtract(randFClassif, randFClassif, extractingPath, outputPath,
#                          featDim=(60,60), applyOnSection=args.section)

################################################################
# # TRAIN SET - NON PROBLEMATIC + PROBLEMATIC = 7M balanced Shiv
# pathsToFeaturesTsvFiles = ["/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_scoresAndMetaData"]
# pathsToClassificationTsvFiles = ["/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_anno"]
#
# # paths
# outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/'

# train the models
# RandFClassif13 = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=13)
# RandFClassif60 = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=60)
# svmClassif13 = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=13)
# svmClassif60 = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=60)

# Dump the models
### utilsML.dumpModel(RandFClassif13, u'{0}bal_train_scores_rdmForest.pickle'.format(outputPath))
### utilsML.dumpModel(RandFClassif60, u'{0}bal_train_scoresAndMetaData_rdmForest.pickle'.format(outputPath))
### utilsML.dumpModel(svmClassif13, u'{0}bal_train_scores_svm.pickle'.format(outputPath))
### utilsML.dumpModel(svmClassif60, u'{0}bal_train_scoresAndMetaData_svm.pickle'.format(outputPath))


# # load the models
# randFClassif13 = utilsML.loadModel(u'{0}bal_train_scores_rdmForest.pickle'.format(outputPath))
# randFClassif60 = utilsML.loadModel(u'{0}bal_train_scoresAndMetaData_rdmForest.pickle'.format(outputPath))
# svmClassif13 = utilsML.loadModel(u'{0}bal_train_scores_svm.pickle'.format(outputPath))
# svmClassif60 = utilsML.loadModel(u'{0}bal_train_scoresAndMetaData_svm.pickle'.format(outputPath))


# # paths
# extractingPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
# outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2/'
# outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2randForest/'

# get the predictions, extract the sps
# applyClassifierToExtract(randFClassif, svmClassif, extractingPath, outputPath,
#                          featDim=(60,13), applyOnSection=args.section)
# applyClassifierToExtract(randFClassif, randFClassif, extractingPath, outputPath,
#                          featDim=(60,60), applyOnSection=args.section)


# predict and dump the predict on the BT2 17K-SPs corpus instead of extracting
# inputScFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.scores"
# inputScMetaFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.scoresAndMetaData"
# outputFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT2/problematic/extracted.randSvmClassif.pred"

# applyClassifierToGetPred(randFClassif, svmClassif,
#                              inputScFilePath, inputScMetaFilePath, outputFilePath, featDim=(60,13))


###############################################################
# # TRAIN SET - NON PROBLEMATIC + PROBLEMATIC = 35K balanced (17,5k probl from bt tanslators annotations, 17,5k no probl from output heuristics)
# pathsToFeaturesTsvFiles = ["/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/35K/extracted.scoresAndMetaData"]
# pathsToClassificationTsvFiles = ["/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/35K/extracted.annot"]
#
# # paths
# outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/35K/'

# # train random forest models
# RandFClassif13 = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=13)
# RandFClassif60 = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=60)
#
# # Dump the random forest models
# utilsML.dumpModel(RandFClassif13, u'{0}train_35K_scores_rdmForest.pickle'.format(outputPath))
# utilsML.dumpModel(RandFClassif60, u'{0}train_35K_scoresAndMetaData_rdmForest.pickle'.format(outputPath))

# # train svm models
# svmClassif13 = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=13)
# svmClassif60 = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifGroup, vectorDim=60)
#
# # Dump the svm models
# utilsML.dumpModel(svmClassif13, u'{0}train_35K_scores_svm.pickle'.format(outputPath))
# utilsML.dumpModel(svmClassif60, u'{0}train_35K_scoresAndMetaData_svm.pickle'.format(outputPath))


# # load the models
# randFClassif13 = utilsML.loadModel(u'{0}train_35K_scores_rdmForest.pickle'.format(outputPath))
# randFClassif60 = utilsML.loadModel(u'{0}train_35K_scoresAndMetaData_rdmForest.pickle'.format(outputPath))
# svmClassif13 = utilsML.loadModel(u'{0}train_35K_scores_svm.pickle'.format(outputPath))
# svmClassif60 = utilsML.loadModel(u'{0}train_35K_scoresAndMetaData_svm.pickle'.format(outputPath))
#
# # paths
# extractingPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/006appliedHeuristics/'
# outputPathRdmFrst=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D3randForest/'
# outputPath=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D3/'
#
# # get the predictions, extract the sps
# applyClassifierToExtract(randFClassif60, randFClassif60, extractingPath, outputPathRdmFrst,
#                          featDim=(60,60), applyOnSection=args.section)
# applyClassifierToExtract(randFClassif60, svmClassif13, extractingPath, outputPath,
#                          featDim=(60,13), applyOnSection=args.section)

###############################################################



# # get the predictions for the 2021 eval corpus and dump it
# inputScFilePath = u"/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/wholeAnnotated2021SP/scores.tsv"
# inputScMetaFilePath = u"/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/wholeAnnotated2021SP/scoresAndMetaData.tsv"
# # outputFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/sample2021/train1721sample2021randSvmClassif.pred"
# # outputFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/sample2021/train7Msample2021randSvmClassif.pred"
# outputFilePath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/sample2021/train35Ksample2021randSvmClassif.pred"
#
# applyClassifierToGetPred(randFClassif60, randFClassif60,
#                              inputScFilePath, inputScMetaFilePath, outputFilePath, featDim=(60,13))


# open the divided the data to join it an unique file
# noProblm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2/noProblematic/"
# problm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2/problematic/"
# noProblm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2randForest/noProblematic/"
# problm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D2randForest/problematic/"
# noProblm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D3/noProblematic/"
# problm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D3/problematic/"
noProblm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D3randForest/noProblematic/"
problm = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/D3randForest/problematic/"

unifier(noProblm, problm)


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))