#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import b000path, utilsOs
from b003heuristics import *
from b004localUtils import *

########################################################################
# ANNOTATION
########################################################################


def annotateFirstSP(beforeSentSource, duringSentSource, beforeSentTarget, duringSentTarget, listOfAnnotations, lineLength):
    """ """
    # color in red the during lines
    redBeforeSource = u'\033[1;31m{0}\033[0m'.format(beforeSentSource)
    redBeforeTarget = u'\033[1;31m{0}\033[0m'.format(beforeSentTarget)
    # print the sentences
    print(u'0 - {0}'.format(redBeforeSource))
    print(u'0 - {0}'.format(redBeforeTarget))
    print(u'1 - {0}'.format(duringSentSource))
    print(u'1 - {0}'.format(duringSentTarget))
    print()
    # count if the lines that take the space of 2 lines
    longLines = getNbLongLines([beforeSentSource, beforeSentTarget, duringSentSource, duringSentTarget], lineLength)
    # get the first part of the annotation (aligned or not)
    annotatorGeneralInput = input(u'Aligned-Misaligned annotation: ')
    # make sure to have the right general annotation
    while True:
        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2', u'0.3', u'1.0', u'1.1']:
            break
        else:
            utilsOs.moveUpAndLeftNLines(1, slowly=False)
            annotatorGeneralInput = input(u'Repeat annotation: ')
    # if we still need to specify what type of alignment or misalignment
    if annotatorGeneralInput in [u'0', u'1']:
        utilsOs.moveUpAndLeftNLines(1, slowly=False)
        # get the second part of the annotation (aligned or not)
        annotatorSpecificInput = input(u'Specific type annotation: ')
        typeAnswers = [u'0', u'1', u'2', u'3'] if annotatorGeneralInput == 0 else [u'0', u'1']
        # make sure to have the right specific annotation
        while True:
            if annotatorSpecificInput in typeAnswers:
                break
            else:
                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                annotatorSpecificInput = input(u'Repeat type annotation: ')
        # save to the list of annotations
        listOfAnnotations.append(float(u'{0}.{1}'.format(annotatorGeneralInput, annotatorSpecificInput)))
    # if the right answer was given in the right format right away
    else:
        # save to the list of annotations
        listOfAnnotations.append(float(annotatorGeneralInput))
    # remove the lines from the terminal before getting to the next pair
    utilsOs.moveUpAndLeftNLines(10, slowly=False)
    # erase all remainder of the previous sentences and go back up again
    for e in range(10 + longLines):
        print(u' ' * (lineLength-1))
    utilsOs.moveUpAndLeftNLines(10 + longLines, slowly=False)
    return listOfAnnotations


def correctionToAnnotation(listOfAnnotations):
    """ given a list of the annotations, asks the user which to correct and correct by what """
    utilsOs.moveUpAndLeftNLines(1, slowly=False)
    indexAnnotation = input(u'Give the index of the annotation : ')
    # make sure to have the right index
    while True:
        try:
            indexAnnotation = int(indexAnnotation)
            if indexAnnotation < len(listOfAnnotations):
                break
            else:
                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                indexAnnotation = input(u'Index out of bounds. Repeat : ')
        except ValueError:
            utilsOs.moveUpAndLeftNLines(1, slowly=False)
            indexAnnotation = input(u'Index given is not integral. Repeat : ')
    # get the new annotation element
    utilsOs.moveUpAndLeftNLines(1, slowly=False)
    annotatorGeneralInput = input(u"Old annotation is '{0}'. Give new annotation : ".format(listOfAnnotations[indexAnnotation]))
    # make sure to have the right general annotation
    while True:
        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2', u'0.3', u'1.0', u'1.1']:
            break
        else:
            utilsOs.moveUpAndLeftNLines(1, slowly=False)
            annotatorGeneralInput = input(u'Repeat annotation: ')
    # if we still need to specify what type of alignment or misalignment
    if annotatorGeneralInput in [u'0', u'1']:
        utilsOs.moveUpAndLeftNLines(1, slowly=False)
        # get the second part of the annotation (aligned or not)
        annotatorSpecificInput = input(u'Specific type annotation: ')
        typeAnswers = [u'0', u'1', u'2', u'3'] if annotatorGeneralInput == 0 else [u'0', u'1']
        # make sure to have the right specific annotation
        while True:
            if annotatorSpecificInput in typeAnswers:
                break
            else:
                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                annotatorSpecificInput = input(u'Repeat type annotation: ')
        # make the replacement
        listOfAnnotations[indexAnnotation] = float(u'{0}.{1}'.format(annotatorGeneralInput, annotatorSpecificInput))
    # if the right answer was given in the right format right away
    else:
       # make the replacement
       listOfAnnotations[indexAnnotation] = float(annotatorGeneralInput)
   # get back to the standard annotation
    utilsOs.moveUpAndLeftNLines(1, slowly=False)
    annotatorGeneralInput = input(u'Correctly replaced. Back to current annotation : ')
    if annotatorGeneralInput in [u'c', u'correct']:
        annotatorGeneralInput, listOfAnnotations = correctionToAnnotation(listOfAnnotations)
    return annotatorGeneralInput, listOfAnnotations


def annotateFiles(listOfFilesPath=None, annotatedOutputFolder=u'./002manuallyAnnotated/', dumpSP=True):
    """ given a list of paths, manually show and annotate the sentence pairs """
    referencePathLine = []
    listOfAnnotations = []
    # get the list containing the file paths
    if listOfFilesPath is None:
        listOfFilesPath = randomlySelectNDocsFromPath(b000path.getBtFolderPath(flagFolder=None), n=100)
        makeLocalFolderPaths(listOfFilesPath)
    elif type(listOfFilesPath) is str:
        if u'.json' in listOfFilesPath:
            listOfFilesPath = utilsOs.openJsonFileAsDict(listOfFilesPath)
        else:
            listOfFilesPath = [listOfFilesPath]
    # get rid of the files we have already annotated
    if utilsOs.theFileExists(u'{0}sampleReference.tsv'.format(annotatedOutputFolder)):
        refLines = utilsOs.readAllLinesFromFile(u'{0}sampleReference.tsv'.format(annotatedOutputFolder),
                                                noNewLineChar=True)
        annotatedFiles = set([line.split(u'\t')[0] for line in refLines])
        listOfFilesPath = [file for file in listOfFilesPath if file not in annotatedFiles]
    # print the annotator cheat sheet
    print(""""0 - badly aligned
        \n\t0.0 - AMPLIFICATION: compensation, description, repetition or lang tendency to hypergraphy
        \n\t0.1 - ELISION: absence, omission, reduction or lang tendency to micrography
        \n\t0.2 - DISPLACEMENT: modification of the line order also modifying the order of the following lines
        \n\t0.3 - MISALIGNED and FOIBLE: alignment and quality errors
        \n1 - well aligned
        \n\t1.0 - ALIGNED and GOOD QUALITY: is aligned and shows no evident sing of translation imperfections 
        \n\t1.1 - FOIBLE: imperfection in the translation quality""")
    # open each file in EN and FR and show it in the terminal
    for filePath in listOfFilesPath:
        print(u'############# {0} ##############'.format(filePath.replace(u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/', u'')))
        # get the path for the source and target
        fileSourcePath = u'{0}.fr'.format(filePath) if u'fr-en' in filePath else u'{0}.en'.format(filePath)
        fileTargetPath = u'{0}.en'.format(filePath) if u'fr-en' in filePath else u'{0}.fr'.format(filePath)
        with open(fileSourcePath) as fileSource:
            with open(fileTargetPath) as fileTarget:
                # show the context of the annotated sentence
                beforeSentSource = fileSource.readline()
                duringSentSource = fileSource.readline()
                beforeSentTarget = fileTarget.readline()
                duringSentTarget = fileTarget.readline()
                # annotate the first sentence pair
                listOfAnnotations = annotateFirstSP(beforeSentSource, duringSentSource, beforeSentTarget,
                                                    duringSentTarget, listOfAnnotations, lineLength=137)
                # save the reference
                # if the filepath is the reference
                if u'burtrad' in filePath:
                    referencePathLine.append(u'{0}\t{1}'.format(filePath, 0))
                # otherwise we get it from a reference file
                else:
                    with open(u'{0}.tsv'.format(filePath)) as refFile:
                        refLns = [ln.replace(u'\n', u'') for ln in refFile.readlines()]
                    referencePathLine.append(refLns[0])
                # dump the first SP
                if dumpSP is True:
                    enSent = beforeSentSource if u'.en' in fileSourcePath else beforeSentTarget
                    frSent = beforeSentTarget if u'.en' in fileSourcePath else beforeSentSource
                    utilsOs.appendLineToFile(enSent, u'{0}sample.en'.format(annotatedOutputFolder), addNewLine=False)
                    utilsOs.appendLineToFile(frSent, u'{0}sample.fr'.format(annotatedOutputFolder), addNewLine=False)
                duringIndex = 1
                # for each line
                while duringSentSource or duringSentTarget:
                    # get the correct terminal line length
                    lineLength = 137-len(str(len(listOfAnnotations)+1))
                    # get the sentences
                    afterSentSource = fileSource.readline()
                    afterSentTarget = fileTarget.readline()
                    # color in red the during lines
                    redDuringSource = u'\033[1;31m{0}\033[0m'.format(duringSentSource)
                    redDuringTarget = u'\033[1;31m{0}\033[0m'.format(duringSentTarget)
                    # print the sentences
                    print(u'{0} - {1}'.format(len(listOfAnnotations)-1, beforeSentSource))
                    print(u'{0} - {1}'.format(len(listOfAnnotations)-1, beforeSentTarget))
                    print(u'{0} - {1}'.format(len(listOfAnnotations), redDuringSource))
                    print(u'{0} - {1}'.format(len(listOfAnnotations), redDuringTarget))
                    print(u'{0} - {1}'.format(len(listOfAnnotations)+1, afterSentSource))
                    print(u'{0} - {1}'.format(len(listOfAnnotations)+1, afterSentTarget))
                    print()
                    # count if the lines that take the space of 2 lines
                    longLines = getNbLongLines([beforeSentSource, beforeSentTarget, duringSentSource,
                                                duringSentTarget, afterSentSource, afterSentTarget], lineLength)
                    # get the first part of the annotation (aligned or not)
                    annotatorGeneralInput = input(u'Aligned-Misaligned annotation: ')
                    # make sure to have the right general annotation
                    while True:
                        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2', u'0.3', u'1.0', u'1.1', u'c', u'correct']:
                            break
                        else:
                            utilsOs.moveUpAndLeftNLines(1, slowly=False)
                            annotatorGeneralInput = input(u'Repeat annotation: ')
                    if annotatorGeneralInput in [u'c', u'correct']:
                        annotatorGeneralInput, listOfAnnotations = correctionToAnnotation(listOfAnnotations)
                    # if we still need to specify what type of alignment or misalignment
                    if annotatorGeneralInput in [u'0', u'1']:
                        utilsOs.moveUpAndLeftNLines(1, slowly=False)
                        # get the second part of the annotation (aligned or not)
                        annotatorSpecificInput = input(u'Specific type annotation: ')
                        typeAnswers = [u'0', u'1', u'2', u'3'] if annotatorGeneralInput == 0 else [u'0', u'1']
                        # make sure to have the right specific annotation
                        while True:
                            if annotatorSpecificInput in typeAnswers:
                                break
                            else:
                                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                                annotatorSpecificInput = input(u'Repeat type annotation: ')
                        # save to the list of annotations
                        listOfAnnotations.append(float(u'{0}.{1}'.format(annotatorGeneralInput, annotatorSpecificInput)))
                    # if the right answer was given in the right format right away
                    else:
                        # save to the list of annotations
                        listOfAnnotations.append(float(annotatorGeneralInput))
                    # remove the lines from the terminal before getting to the next pair
                    utilsOs.moveUpAndLeftNLines(14+longLines, slowly=False)
                    # erase all remainder of the previous sentences and go back up again
                    for e in range(14+longLines):
                        print(u' '*(lineLength+4))
                    utilsOs.moveUpAndLeftNLines(14 + longLines, slowly=False)
                    # next line source
                    beforeSentSource = duringSentSource
                    duringSentSource = afterSentSource
                    # next line target
                    beforeSentTarget = duringSentTarget
                    duringSentTarget = afterSentTarget
                    # append the reference to the file
                    # if the filepath is the reference
                    if u'burtrad' in filePath:
                        referencePathLine.append(u'{0}\t{1}'.format(filePath, duringIndex))
                    # otherwise we get it from a reference file
                    else:
                        with open(u'{0}.tsv'.format(filePath)) as refFile:
                            refLns = [ln.replace(u'\n', u'') for ln in refFile.readlines()]
                        referencePathLine.append(refLns[duringIndex])
                    # add 1 to index
                    duringIndex += 1
                    # dump the file line by line, to be sure in case of error
                    # dump the reference
                    utilsOs.dumpRawLines(referencePathLine, u'{0}sampleReference.tsv'.format(annotatedOutputFolder),
                                         addNewline=True, rewrite=True)
                    # dump the annotation
                    utilsOs.dumpRawLines(listOfAnnotations, u'{0}sampleAnnotation.tsv'.format(annotatedOutputFolder),
                                         addNewline=True, rewrite=True)
                    # dump the SP
                    if dumpSP is True:
                        enSent = beforeSentSource if u'.en' in fileSourcePath else beforeSentTarget
                        frSent = beforeSentTarget if u'.en' in fileSourcePath else beforeSentSource
                        utilsOs.appendLineToFile(enSent, u'{0}sample.en'.format(annotatedOutputFolder), addNewLine=False)
                        utilsOs.appendLineToFile(frSent, u'{0}sample.fr'.format(annotatedOutputFolder), addNewLine=False)
        # clear part of terminal
        utilsOs.moveUpAndLeftNLines(2, slowly=False)


def mergeAnnotatedFiles(pathToPrimary, pathOrListOfPathsToSecondary):
    # get the path to the primary folder
    def dividePaths(pathAnnotFile):
        if u'sampleAnnotation.tsv' in pathAnnotFile:
            pathFolder = pathAnnotFile.replace(u'sampleAnnotation.tsv', u'')
        else:
            pathFolder = pathAnnotFile
            pathAnnotFile = u'{0}sampleAnnotation.tsv'.format(pathAnnotFile)
        return pathAnnotFile, pathFolder
    pathToPrimary, primaryFolder = dividePaths(pathToPrimary)
    # make secondary a list if it is string
    if type(pathOrListOfPathsToSecondary) is str:
        pathOrListOfPathsToSecondary = [pathOrListOfPathsToSecondary]
    # open primary
    primaryRefPath = u'{0}sampleReference.tsv'.format(primaryFolder)
    primaryAnnotDf, primaryRefDf = utilsOs.getDataFrameFromArgs(pathToPrimary, primaryRefPath, header=False)
    primaryEnPath = u'{0}sample.en'.format(primaryFolder)
    primaryFrPath = u'{0}sample.fr'.format(primaryFolder)
    primaryEnDf, primaryFrDf = utilsOs.getDataFrameFromArgs(primaryEnPath, primaryFrPath, header=False)
    # open the secondaries and merge
    for secondaryPath in pathOrListOfPathsToSecondary:
        pathToSec, secFolder = dividePaths(secondaryPath)
        # open secondary dataframe
        secAnnotDf, secRefDf = utilsOs.getDataFrameFromArgs(pathToSec,
                                                                    u'{0}sampleReference.tsv'.format(secFolder),
                                                                    header=False)
        secEnDf, secFrDf = utilsOs.getDataFrameFromArgs(u'{0}sample.en'.format(secFolder),
                                                                u'{0}sample.fr'.format(secFolder),
                                                               header=False)
        # concatenate the primary with the secondary
        primaryAnnotDf = utilsOs.concatenateDfsOrSeries([primaryAnnotDf, secAnnotDf])
        primaryRefDf = utilsOs.concatenateDfsOrSeries([primaryRefDf, secRefDf])
        primaryEnDf = utilsOs.concatenateDfsOrSeries([primaryEnDf, secEnDf])
        primaryFrDf = utilsOs.concatenateDfsOrSeries([primaryFrDf, secFrDf])
    # dump in the primary's path
    utilsOs.dumpDataFrame(primaryAnnotDf, pathToPrimary, header=False)
    utilsOs.dumpDataFrame(primaryRefDf, primaryRefPath, header=False)
    utilsOs.dumpDataFrame(primaryEnDf, primaryEnPath, header=False)
    utilsOs.dumpDataFrame(primaryFrDf, primaryFrPath, header=False)


# count the time the algorithm takes to run
startTime = utilsOs.countTime()

# annotate the SP
# listOfFilesPath = u'./randomSelected100MISALIGNED.json'
# annotateFiles(listOfFilesPath, anotatedOutputFolder=u'./002manuallyAnnotated/')


# annotate the randomly extracted misaligned SPs
# listOfPaths = [u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/MISALIGNED',
#                u'./003negativeNaiveExtractors/fewTokens/random100few/MISALIGNED',
#                u'./003negativeNaiveExtractors/cognates/random100cog/MISALIGNED',
#                u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/QUALITY',
#                u'./003negativeNaiveExtractors/fewTokens/random100few/QUALITY',
#                u'./003negativeNaiveExtractors/cognates/random100cog/QUALITY',
#                u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/ALIGNMENT-QUALITY',
#                u'./003negativeNaiveExtractors/fewTokens/random100few/ALIGNMENT-QUALITY',
#                u'./003negativeNaiveExtractors/cognates/random100cog/ALIGNMENT-QUALITY']
# annotateFiles(listOfFilesPath=listOfPaths, annotatedOutputFolder=u'./003negativeNaiveExtractors/')

# mergeAnnotatedFiles(u'./002manuallyAnnotated/sampleAnnotation.tsv', u'./003negativeNaiveExtractors/')


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))