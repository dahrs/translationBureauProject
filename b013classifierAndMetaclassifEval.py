#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys, argparse
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsML
from b003heuristics import *
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser()

parser.add_argument(u'-feat', u'--pathsToFeaturesTsv', type=str,
                    default=u'Predetermined',
                    help=u'path to the scores & metadata tsv files, if there are more than one: separate with a " , " ')
parser.add_argument(u'-clp', u'--pathsToClassificationTsv', type=str,
                    default=u'Predetermined',
                    help=u'path to the classification tsv files, if there are more than one: separate with a " , " ')
parser.add_argument(u'-vd', u'--vectorDimension', type=int, default=13,
                    help=u'dimensionality of the vectors, accepted values: 13 (upped to 15) or 60 (upped to 62)')
parser.add_argument(u'-cl', u'--classifier', type=str, default=u'rdmForest',
                    help=u'4 possible values for classifiers: rdmForest, svm, ffnn, linear')
parser.add_argument(u'-bin', u'--binaryClassification', type=bool, default=True,
                    help=u'whether the classification is binary or not')
parser.add_argument(u'-typ', u'--typeClassification', type=bool, default=False,
                    help=u'if the classification is not binary, then should it be regrouped by type')
parser.add_argument(u'-out', u'--modelOutputPath', type=str, default=u'None',
                    help=u"output to the folder where to dump the model's pickle file")
args = parser.parse_args()

# command line: python b013classifierAndMetaclassifEval.py -feat shivTrain -vd 13 -cl rdmForest

pathsToFeaturesTsvFiles = args.pathsToFeaturesTsv
pathsToClassificationTsvFiles = args.pathsToClassificationTsv
vectorDim = args.vectorDimension
classifierType = args.classifier
classifBinary = args.binaryClassification
classifType = args.typeClassification
modelOutputFolderPath = args.modelOutputPath if args.modelOutputPath != u'None' else None

# properly declare the path to the feat val
if pathsToFeaturesTsvFiles == u'Predetermined' and pathsToFeaturesTsvFiles == u'Predetermined':
    # TRAIN SET - NON PROBLEMATIC + PROBLEMATIC
    pathsToFeaturesTsvFiles = [
        "/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/scoresAndMetaData.tsv",
        "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/scoresAndMetaData.tsv",
        "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/scoresAndMetaData.tsv"]
    pathsToClassificationTsvFiles = [
        "/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/sampleAnnotation.tsv",
        "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/sampleAnnotation.tsv",
        "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/sampleAnnotation.tsv"]
elif pathsToFeaturesTsvFiles == u'shivTrain':
    # TRAIN SET - SHIVS SELECTION
    pathsToFeaturesTsvFiles = [
        u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_scoresAndMetaData"]
    pathsToClassificationTsvFiles = [
        u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_anno"]
    ###########################
    modelOutputFolderPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/bal_train_"
else:
    # NEW TRAIN SET
    pathsToFeaturesTsvFiles = pathsToFeaturesTsvFiles.split(u' , ') #.split(u', ').split(u' ,').split(u',')
    pathsToClassificationTsvFiles = pathsToClassificationTsvFiles.split(u' , ') #.split(u', ').split(u' ,').split(u',')


# count the time the algorithm takes to run
startTime = utilsOs.countTime()


# add metadata to the basic scores
# for foldPath in ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/",
#                  "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/",
#                  "/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/",
#                  "/u/alfonsda/Documents/workRALI/004tradBureau/003negativeNaiveExtractors/000manualAnnotation/",
#                  "/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/annotatedButUseless4Eval/"]:
#     addAndDumpMetaDataToScoreFeatures(foldPath)

# addAndDumpMetaDataToScoreFeatures(u'/u/alfonsda/Documents/workRALI/004tradBureau/002manuallyAnnotated/test/')


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

# TEST SET - RANDOM MIX OF PROBLEMATIC & NON PROBLEMATIC
# pathsToTestFeatureFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/mixed/scoresAndMetaData.tsv"]
# pathsToTestClassificationFiles = ["/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/mixed/sampleAnnotation.tsv"]

# CLASSIFIERS ########################################################################
acumulGoodPrecision, acumulGoodRecall, acumulAccuracy, acumulBadPrecision, acumulBadRecall = 0, 0, 0, 0, 0
# change the path of the feature files to the right ones if the dimension is 13 instead of 60
if vectorDim in [13, 15]:
    pathsToFeaturesTsvFiles = [fp.replace(u'scoresAndMetaData', u'scores') for fp in pathsToFeaturesTsvFiles]
    pathsToTestFeatureFiles = [fp.replace(u'scoresAndMetaData', u'scores') for fp in pathsToTestFeatureFiles]
    scoreType = u'scores'
else:
    scoreType = u'scoresAndMetaData'
# if we have to save the model, then make only one iteration (the overall score is not that important)
nbOfIter = 10 if modelOutputFolderPath is None else 1

# iterate multiple times to get a more reliable mean of all scores
for n in range(nbOfIter):
    verbose = True if n == 0 else False
    # before feeding the training set to the model, it will add 2 elements to the vector (see dataTrainPreparation() )
    if classifierType == u'ffnn':
        classifier = trainFeedForwardNNModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifType, vectorDim)
    elif classifierType == u'linear':
        classifier = trainMaxEntLinearModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifType, vectorDim)
    elif classifierType == u'svm':
        classifier = trainSvmModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifType, vectorDim)
    elif classifierType == u'rdmForest':
        classifier = trainRdmForestModel(pathsToFeaturesTsvFiles, pathsToClassificationTsvFiles, classifBinary, classifType, vectorDim)

    # dump the model
    if modelOutputFolderPath is not None:
        utilsML.dumpModel(classifier, "{0}{1}_{2}.pickle".format(modelOutputFolderPath, scoreType, classifierType))


    # getModelEval(pathsToTestFeatureFiles, pathsToTestClassificationFiles, classifier, classifBinary)
    gp, gr, a, bp, br = getModelEvalGoodAndBad(pathsToTestFeatureFiles, pathsToTestClassificationFiles, classifier, classifBinary, verbose)
    acumulGoodPrecision += gp
    acumulGoodRecall += gr
    acumulAccuracy += a
    acumulBadPrecision += bp
    acumulBadRecall += br

print(u'\n{0} - {1}_______________________________\n'.format(classifierType, scoreType))
print("GOOD MEAN precision : ", acumulGoodPrecision/nbOfIter)
print("GOOD MEAN recall : ", acumulGoodRecall/nbOfIter)
print("JUST MEAN accuracy : ", acumulAccuracy/nbOfIter)
print("BAD MEAN precision : ", acumulBadPrecision/nbOfIter)
print("BAD MEAN recall : ", acumulBadRecall/nbOfIter)


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))