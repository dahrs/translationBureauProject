#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import b000path, utilsOs
from b003heuristics import *
from b004localUtils import *


########################################################################
# SEARCH FUNCTION
########################################################################

def getPathWhereWeFind(stringToBeFound, verbose=True):
    srcTrgtFiles = utilsOs.goDeepGetFiles(b000path.getBtFolderPath(flagFolder=u'a'), format=u'.tmx')
    srcLinesContaining = set()
    pathsContaining = set()
    for filePath in srcTrgtFiles:
        srcFilePath = u'{0}.en'.format(filePath) if u'en-fr' in filePath else u'{0}.fr'.format(filePath)
        trgtFilePath = u'{0}.fr'.format(filePath) if u'en-fr' in filePath else u'{0}.en'.format(filePath)
        # open line by line and apply extractors
        try:
            with open(srcFilePath) as srcFile:
                srcLines = srcFile.readlines()
            with open(trgtFilePath) as trgtFile:
                trgtLines = trgtFile.readlines()
            for srcLnIndex, srcLn in enumerate(srcLines):
                trgtLn = trgtLines[srcLnIndex]
                if stringToBeFound in srcLn or stringToBeFound in trgtLn:
                    if verbose == True:
                        print(filePath)
                    srcLinesContaining.add(srcLn)
                    pathsContaining.add(filePath)
        except FileNotFoundError:
            pass
    print(len(srcLinesContaining), len(pathsContaining))


########################################################################
# ANNOTATION
########################################################################


def annotateFirstSP(beforeSentSource, duringSentSource, beforeSentTarget,
                    duringSentTarget, listOfAnnotations, lineLength):
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
        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2', u'1.0', u'1.1', u'1.2', u'1.3', u'1.4']:
            break
        else:
            utilsOs.moveUpAndLeftNLines(1, slowly=False)
            annotatorGeneralInput = input(u'Repeat annotation: ')
    # if we still need to specify what type of alignment or misalignment
    if annotatorGeneralInput in [u'0', u'1']:
        utilsOs.moveUpAndLeftNLines(1, slowly=False)
        # get the second part of the annotation (aligned or not)
        annotatorSpecificInput = input(u'Specific type annotation: ')
        typeAnswers = [u'0', u'1', u'2'] if annotatorGeneralInput == 0 else [u'0', u'1', u'2', u'3', u'4']
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
        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2', u'1.0', u'1.1', u'1.2', u'1.3', u'1.4']:
            break
        else:
            utilsOs.moveUpAndLeftNLines(1, slowly=False)
            annotatorGeneralInput = input(u'Repeat annotation: ')
    # if we still need to specify what type of alignment or misalignment
    if annotatorGeneralInput in [u'0', u'1']:
        utilsOs.moveUpAndLeftNLines(1, slowly=False)
        # get the second part of the annotation (aligned or not)
        annotatorSpecificInput = input(u'Specific type annotation: ')
        typeAnswers = [u'0', u'1', u'2'] if annotatorGeneralInput == 0 else [u'0', u'1', u'2', u'3', u'4']
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


def printCheatSheet():
    print(""""0 - badly aligned
        \n\t0.0 - AMPLIFICATION: compensation, description, repetition or lang tendency to hypergraphy
        \n\t0.1 - ELISION: absence, omission, reduction or lang tendency to micrography
        \n\t0.2 - DISPLACEMENT: modification of the line order showing no translation relation between the SP.
        \n1 - well aligned
        \n\t1.0 - ALIGNED and GOOD QUALITY: is aligned and shows no evident sing of translation imperfections 
        \n\t1.1 - ORTHOGRAPHIC/MORPHOSYNTAXTIC ERROR: imperfection in the translation quality 
        \n\t1.2 - MONOLINGUAL: no translation made in the target sentence
        \n\t1.3 - GIBBERISH: encoding or other problem rendering the SP unreadeable
        \n\t1.4 - OTHER: impossible to determine the nature of the error""")


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
    printCheatSheet()
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
                        if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2',
                                                     u'1.0', u'1.1', u'1.2', u'1.3', u'1.4', u'c', u'correction']:
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
                        typeAnswers = [u'0', u'1', u'2'] if annotatorGeneralInput == 0 else [u'0', u'1', u'2', u'3', u'4']
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


def annotateFilesAfterHeurAndSelection(inputFolderPath, outputFolderPath, dumpSP=True):
    """ given a folder path, where the reference, en line and fr line are alreade selected, annotate the SPs """
    # add a slash if needed
    if inputFolderPath[-1] != u'/':
        inputFolderPath = u'{0}/'.format(inputFolderPath)
    if outputFolderPath[-1] != u'/':
        outputFolderPath = u'{0}/'.format(outputFolderPath)
    # get the selected reference file lines
    with open(u'{0}sampleReference.Paths'.format(inputFolderPath)) as refPathsFile:
        referenceLines = refPathsFile.readlines()
    # get the en and fr input lines
    with open(u'{0}sample.en'.format(inputFolderPath)) as enFile:
        enLns = enFile.readlines()
    with open(u'{0}sample.fr'.format(inputFolderPath)) as frFile:
        frLns = frFile.readlines()
    with open(u'{0}scores.tsv'.format(inputFolderPath)) as scFile:
        scLns = scFile.readlines()
    # get rid of the files we have already annotated
    if utilsOs.theFileExists(u'{0}sampleReference.tsv'.format(outputFolderPath)):
        # get the already seen lines
        referencePathLine = utilsOs.readAllLinesFromFile(u'{0}sampleReference.tsv'.format(outputFolderPath),
                                                         noNewLineChar=True)
        listOfAnnotations = utilsOs.readAllLinesFromFile(u'{0}sampleAnnotation.tsv'.format(outputFolderPath),
                                                         noNewLineChar=True)
        # maintain only what we haven't saw
        annotatedFiles = set(referencePathLine)
        newRefLines = []
        for ind, file in enumerate(referenceLines):
            if file.replace(u'\n', u'') not in annotatedFiles:
                newRefLines.append( [ind, file.replace(u'\n', u'')] )
        referenceLines = newRefLines
        print(referenceLines)
    else:
        referencePathLine = []
        listOfAnnotations = []
        referenceLines = [(ind, file.replace(u'\n', u'')) for ind, file in enumerate(referenceLines)]
    # print the annotator cheat sheet
    printCheatSheet()
    # open each file in EN and FR and show it in the terminal
    for tupleRef in referenceLines:
        indRef, refLn = tupleRef[0], tupleRef[1]
        print(u'############# {0} ##############'.format(refLn.replace(u'\n', u'')))
        # get the path for the source and target
        lnsSource = enLns if u'en-fr' in refLn else frLns
        lnsTarget = frLns if u'en-fr' in refLn else enLns
        # get the correct terminal line length
        lineLength = 137-len(str(len(listOfAnnotations)+1))
        # color in red the during lines
        redDuringSource = u'\033[1;31m{0}\033[0m'.format(lnsSource[indRef])
        # print the sentences
        print(u'{0} - {1}'.format(len(listOfAnnotations), redDuringSource))
        print(u'{0} - {1}'.format(len(listOfAnnotations), lnsTarget[indRef]))
        print()
        # count the lines that take the space of 2 lines
        longLines = getNbLongLines([lnsSource[indRef], lnsTarget[indRef]], lineLength)
        # get the first part of the annotation (aligned or not)
        annotatorGeneralInput = input(u'Aligned-Misaligned annotation: ')
        # make sure to have the right general annotation
        while True:
            if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2',
                                         u'1.0', u'1.1', u'1.2', u'1.3', u'1.4', u'c', u'correction']:
                break
            else:
                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                annotatorGeneralInput = input(u'Repeat annotation: ')
        if annotatorGeneralInput in [u'c', u'correct']:
            annotatorGeneralInput, listOfAnnotations = correctionToAnnotation(listOfAnnotations)
        # save to the list of annotations
        listOfAnnotations.append(float(annotatorGeneralInput))
        # remove the lines from the terminal before getting to the next pair
        utilsOs.moveUpAndLeftNLines(7+longLines, slowly=False)
        # erase all remainder of the previous sentences and go back up again
        for e in range(14+longLines):
            print(u' '*(lineLength+4))
        utilsOs.moveUpAndLeftNLines(7 + longLines, slowly=False)
        # append the reference to the file
        referencePathLine.append(refLn)
        # dump the file line by line, to be sure in case of error
        # dump the reference
        utilsOs.dumpRawLines(referencePathLine, u'{0}sampleReference.tsv'.format(outputFolderPath),
                             addNewline=True, rewrite=True)
        # dump the annotation
        utilsOs.dumpRawLines(listOfAnnotations, u'{0}sampleAnnotation.tsv'.format(outputFolderPath),
                             addNewline=True, rewrite=True)
        # dump the SP
        if dumpSP is True:
            enSent = lnsSource[indRef] if u'en-fr' in refLn else lnsTarget[indRef]
            frSent = lnsTarget[indRef] if u'en-fr' in refLn else lnsSource[indRef]
            utilsOs.appendLineToFile(enSent, u'{0}sample.en'.format(outputFolderPath), addNewLine=False)
            utilsOs.appendLineToFile(frSent, u'{0}sample.fr'.format(outputFolderPath), addNewLine=False)
            utilsOs.appendLineToFile(scLns[indRef], u'{0}scores.tsv'.format(outputFolderPath), addNewLine=False)
        # clear part of terminal
        utilsOs.moveUpAndLeftNLines(7, slowly=False)


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
    # bug fix to avoid the 1.0 and 0.0 transforming into 1 and 0
    with open(pathToPrimary) as annotFile:
        annotLines = annotFile.readlines()
        for aIndex, aLine in enumerate(annotLines):
            if u'1\n' == aLine:
                annotLines[aIndex] = aLine.replace(u'1\n', u'1.0\n')
            elif u'0\n' == aLine:
                annotLines[aIndex] = aLine.replace(u'0\n', u'0.0\n')
    utilsOs.dumpRawLines(annotLines, pathToPrimary, addNewline=False)


def extractLineData(sentEnPath, sentFrPath, sentRefPath, sentAnnotPath,
                      enList=[], frList=[], refList=[], annotList=[]):
    """ open the files, extract the lines into lists """
    # get the sentences and annotations
    with open(sentEnPath) as enFile:
        enList = enList + [s.replace(u'\n', u'') for s in enFile.readlines()]
    with open(sentFrPath) as frFile:
        frList = frList + [s.replace(u'\n', u'') for s in frFile.readlines()]
    with open(sentRefPath) as refFile:
        refList = refList + [s.replace(u'\n', u'') for s in refFile.readlines()]
    with open(sentAnnotPath) as annotFile:
        sentAnnotList = annotFile.readlines()
        dic = {u'0\n': u'0.0', u'1\n': u'1.0', u'1.1.0\n': u'1.1', u'0.1.0\n': u'0.1'}
        tempList = []
        for annot in sentAnnotList:
            if annot in dic:
                tempList.append(dic[annot])
            else:
                tempList.append(annot.replace(u'\n', u''))
        annotList = annotList + tempList
    return enList, frList, refList, annotList


def getAnnotationData(annotatedFolderPathList):
    """ given a list of paths where the annotations are, return a liost of each type of data """
    enList, frList, refList, annotList = [], [], [], []
    # be sure the format is right
    if type(annotatedFolderPathList) is str:
        annotatedFolderPathList = [annotatedFolderPathList]
    # get the lists of annotations and sentences
    for path in annotatedFolderPathList:
        sentEnPath = u'{0}sample.en'.format(path)
        sentFrPath = u'{0}sample.fr'.format(path)
        sentAnnotPath = u'{0}sampleAnnotation.tsv'.format(path)
        sentRefPath = u'{0}sampleReference.tsv'.format(path)
        enList, frList, refList, annotList = extractLineData(sentEnPath, sentFrPath, sentRefPath, sentAnnotPath,
                                                             enList, frList, refList, annotList)
    return enList, frList, refList, annotList


def changeAnnotations(folderPathToReannotate, annotationTochange=[u'0.3', u'1.1']):
    """ given a path where to find the annotation files, change the annotation (new)
    for the with a specific annotation (old) """
    # transform the annotation into a list if need be
    if type(annotationTochange) is str:
        annotationTochange = [annotationTochange]
    # get the annotation data
    sentEnList, sentFrList, sentRefList, sentAnnotList = getAnnotationData(folderPathToReannotate)
    # print the annotator cheat sheet
    printCheatSheet()
    # annotate only when we find the problematic old annotation
    for indexAnnot, oldAnnot in enumerate(list(sentAnnotList)):
        if oldAnnot in annotationTochange:
            src = sentEnList[indexAnnot] if u'en-fr' in sentRefList[indexAnnot] else sentFrList[indexAnnot]
            trgt = sentFrList[indexAnnot] if u'en-fr' in sentRefList[indexAnnot] else sentEnList[indexAnnot]
            print(u'{0} - {1}'.format(indexAnnot+1, src))
            print(u'{0} - {1}'.format(indexAnnot+1, trgt))
            # get the first part of the annotation (aligned or not)
            annotatorGeneralInput = input(u'Old annotation is {0}, what is the new one: '.format(oldAnnot))
            # make sure to have the right general annotation
            while True:
                if annotatorGeneralInput in [u'0', u'1', u'0.0', u'0.1', u'0.2',
                                             u'1.0', u'1.1', u'1.2', u'1.3', u'1.4', u'c', u'correction']:
                    break
                else:
                    utilsOs.moveUpAndLeftNLines(1, slowly=False)
                    annotatorGeneralInput = input(u'Repeat annotation: ')
            if annotatorGeneralInput in [u'c', u'correct']:
                annotatorGeneralInput, sentAnnotList = correctionToAnnotation(sentAnnotList)
            # if we still need to specify what type of alignment or misalignment
            if annotatorGeneralInput in [u'0', u'1']:
                utilsOs.moveUpAndLeftNLines(1, slowly=False)
                # get the second part of the annotation (aligned or not)
                annotatorSpecificInput = input(u'Specific type annotation: ')
                typeAnswers = [u'0', u'1', u'2'] if annotatorGeneralInput == 0 else [u'0', u'1', u'2', u'3', u'4']
                # make sure to have the right specific annotation
                while True:
                    if annotatorSpecificInput in typeAnswers:
                        break
                    else:
                        utilsOs.moveUpAndLeftNLines(1, slowly=False)
                        annotatorSpecificInput = input(u'Repeat type annotation: ')
                # save to the list of annotations
                sentAnnotList[indexAnnot] = u'{0}.{1}'.format(annotatorGeneralInput, annotatorSpecificInput)
            # if the right answer was given in the right format right away
            else:
                # save to the list of annotations
                sentAnnotList[indexAnnot] = str(annotatorGeneralInput)
            # remove the lines from the terminal before getting to the next pair
            utilsOs.moveUpAndLeftNLines(3, slowly=False)
            # erase all remainder of the previous sentences and go back up again
            for e in range(2):
                print(u' ' * (max([len(src), len(trgt)]) + 6))
            utilsOs.moveUpAndLeftNLines(2, slowly=False)
    # remove format problematic annotations
    sentAnnotList = [annot if annot != u'1.1.0' else u'1.1' for annot in sentAnnotList]
    sentAnnotList = [annot if annot != u'0.1.0' else u'0.1' for annot in sentAnnotList ]
    # dump new annotation
    sentAnnotPath = u'{0}sampleAnnotation.tsv'.format(folderPathToReannotate)
    utilsOs.dumpRawLines(sentAnnotList, sentAnnotPath, addNewline=True, rewrite=True)


def showAnnotationsExamples(annotation=1.0, showTotalOnly=False):
    """ given an annotation, shows one by one all the manually annotated elements corresponding to said annotation """
    total = 0
    # get the right annotation
    if type(annotation) is float:
        annotation = str(annotation)
    # get the lists of annotations and sentences
    annotatedFolderPathList = [u'./002manuallyAnnotated/', u'./003negativeNaiveExtractors/000manualAnnotation/']
    enList, frList, refList, annotList = getAnnotationData(annotatedFolderPathList)
    # print one by one the SP corresponding to the searched annotation
    for indexAnnot, annot in enumerate(annotList):
        if annot == annotation:
            src = enList[indexAnnot] if u'en-fr' in refList[indexAnnot] else frList[indexAnnot]
            trgt = frList[indexAnnot] if u'en-fr' in refList[indexAnnot] else enList[indexAnnot]
            total += 1
            if showTotalOnly is False:
                print(u'{0} - {1}'.format(indexAnnot + 1, src))
                print(u'{0} - {1}'.format(indexAnnot + 1, trgt))
                print()
    print('TOTAL : ', total)
    return



# count the time the algorithm takes to run


startTime = utilsOs.countTime()

# annotate the randomly extracted files
# listOfFilesPath = u'./randomSelected100MISALIGNED.json'
# annotateFiles(listOfFilesPath, anotatedOutputFolder=u'./002manuallyAnnotated/')


# annotate the randomly extracted SPs
# listOfPaths = [u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/MISALIGNED',
#               u'./003negativeNaiveExtractors/fewTokens/random100few/MISALIGNED',
#               u'./003negativeNaiveExtractors/cognates/random100cog/MISALIGNED',
#               u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/QUALITY',
#               u'./003negativeNaiveExtractors/fewTokens/random100few/QUALITY',
#               u'./003negativeNaiveExtractors/cognates/random100cog/QUALITY',
#               u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/ALIGNMENT-QUALITY',
#               u'./003negativeNaiveExtractors/fewTokens/random100few/ALIGNMENT-QUALITY',
#               u'./003negativeNaiveExtractors/cognates/random100cog/ALIGNMENT-QUALITY']

# listOfPaths = [u'./003negativeNaiveExtractors/numberCoincidence/random100Nb/ALIGNMENT-QUALITY',
#                u'./003negativeNaiveExtractors/fewTokens/random100few/ALIGNMENT-QUALITY',
#                u'./003negativeNaiveExtractors/cognates/random100cog/ALIGNMENT-QUALITY']

# annotateFiles(listOfFilesPath=listOfPaths, annotatedOutputFolder=u'./003negativeNaiveExtractors/')

# mergeAnnotatedFiles(u'./002manuallyAnnotated/sampleAnnotation.tsv', u'./003negativeNaiveExtractors/')


# annotate the sample of already selected lines post-heuristic-application-and-extraction
inputFolderPrblm = u'/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/sampleSelection/problematic/'
outputFolderPrblm = u'/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/problematic/'
annotateFilesAfterHeurAndSelection(inputFolderPrblm, outputFolderPrblm)

# inputFolderNoPrblm = u'/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/sampleSelection/noProblematic/'
# outputFolderNoPrblm = u'/u/alfonsda/Documents/workRALI/004tradBureau/007corpusExtraction/000manualAnnotation/noProblematic/'
# annotateFilesAfterHeurAndSelection(inputFolderNoPrblm, outputFolderNoPrblm)


# change one type of annotation
# listOfFolderPathsToReannotate = [u'./002manuallyAnnotated/', u'./003negativeNaiveExtractors/000manualAnnotation/']
# for folderPath in listOfFolderPathsToReannotate:
#     changeAnnotations(folderPath, [u'1.1', u'0.3'])


# look at the sentences annotated with a specific annotation
# annotation = 0.0
# showAnnotationsExamples(annotation)

# find the paths containing a specific string
# getPathWhereWeFind(u'0', verbose=True)

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))
