#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')

import b000path, utilsOs
from random import randint


def getRandomIntNerverseenBefore(listLength, dejaVus=[]):
    """  """
    # If we have more in dejavu than what we can produce
    if len(dejaVus) >= listLength:
        return None
    # get a random int
    r = randint(0, listLength)
    while r in dejaVus:
        r = randint(0, listLength)
    return r


def randomlySelectNDocsFromPath(folderPath, n=100):
    """ given a folder path, return a list of n randomly selected file paths """
    dejaVus = set()
    randomSelected = set()
    # get all the tmx files in the folder
    wholeFolderContent = utilsOs.goDeepGetFiles(folderPath, format=u'.tmx')
    # if there are less files in the folder path as in n then return them all
    if len(wholeFolderContent) <= n:
        return wholeFolderContent
    # get n randomly selected files from the whole
    for e in range(n):
        index = getRandomIntNerverseenBefore(len(wholeFolderContent), dejaVus)
        # add to dejavus and to the random selected list
        dejaVus.add(index)
        randomSelected.add(wholeFolderContent[index])
    # get the domain
    if folderPath[-1] == u'/' :
        domain = folderPath[:-1].split(u'/')[-1]
    elif u'.' in folderPath.split(u'/')[-1]:
        path = folderPath.replace(u'/{0}'.format(folderPath.split(u'/')[-1]), u'')
        domain = path.split(u'/')[-1]
    else:
        domain = folderPath.split(u'/')[-1]
    # dump the set
    utilsOs.dumpDictToJsonFile(list(randomSelected), pathOutputFile='./randomSelected{0}{1}.json'.format(n, domain), overwrite=True)
    return randomSelected


def makeLocalFolderPaths(listOfFilePaths):
    """ given a list of file paths, creates the equivalent in the local path """
    for filePath in listOfFilePaths:
        localFilePath = filePath.replace(u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/', u'./manuallyAnnotated/')
        localFileList = localFilePath.split(u'/')
        folderPath = localFilePath.replace(localFileList[-1], u'')
        utilsOs.createEmptyFolder(folderPath)


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
    # remove the lines from the terminal before guetting to the next pair
    utilsOs.moveUpAndLeftNLines(10, slowly=False)
    # erase all remainder of the previous sentences and go back up again
    for e in range(10 + longLines):
        print(u' ' * (lineLength-1))
    utilsOs.moveUpAndLeftNLines(10 + longLines, slowly=False)
    return listOfAnnotations


def getNbLongLines(listOfSent, n=141):
    ''' returns the number of long lines that exceed n characters '''
    longLines = 0
    for sent in listOfSent:
        # make sure the sentence has no red keywords in it
        sent = sent.replace(u'\033[1;31m', u'').replace(u'\033[0m', u'')
        if len(sent) > n:
            longLines += 1
    return longLines


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


def annotateFiles(listOfFilesPath=None, anotatedOutputFolder=u'./manuallyAnnotated/'):
    """ given a list of paths, manually show and annotate the sentence pairs """
    # get the list containing the file paths
    if listOfFilesPath == None:
        listOfFilesPath = randomlySelectNDocsFromPath(b000path.getBtFolderPath(flagFolder=None), n=100)
        makeLocalFolderPaths(listOfFilesPath)
    elif type(listOfFilesPath) is str:
        listOfFilesPath = utilsOs.openJsonFileAsDict(listOfFilesPath)
    # do not include the files that have already been annotated
    alreadyAnnotated = ([localFile.replace(u'./manuallyAnnotated/', u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/') for localFile in utilsOs.goDeepGetFiles(anotatedOutputFolder, format=u'.tmx')])
    listOfFilesPath = [filePath for filePath in listOfFilesPath if filePath not in alreadyAnnotated]
    # print the annotator cheat sheet
    print(""""0 - badly aligned
        \n\t0.0 - AMPLIFICATION: compensation, description, repetition or lang tendency to hypergraphy
        \n\t0.1 - ELISION: absence, omision, reduction or lang tendency to micrography
        \n\t0.2 - DISPLACEMENT: modification of the line order also modifying the order of the following lines
        \n\t0.3 - MISALIGNED and FOIBLE: alignment and quality errors
        \n1 - well aligned
        \n\t1.0 - ALIGNED and GOOD QUALITY: is aligned and shows no evident sing of translation imperfections 
        \n\t1.1 - FOIBLE: imperfection in the translation quality""")
    # open each file in EN and FR and show it in the terminal
    for filePath in listOfFilesPath:
        print(u'############# {0} ##############'.format(filePath.replace(u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/', u'')))
        listOfAnnotations = []
        # get the path for the source and target
        fileSourcePath = u'{0}.en'.format(filePath) if u'en-fr' in filePath else u'{0}.fr'.format(filePath)
        fileTargetPath = u'{0}.fr'.format(filePath) if u'en-fr' in filePath else u'{0}.en'.format(filePath)
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
                    # dump the file line by line, to be sure in case of error
                    localFilePath = filePath.replace(u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/',
                                                     u'./manuallyAnnotated/')
                    utilsOs.dumpRawLines(listOfAnnotations, localFilePath, addNewline=True, rewrite=True)
        # dump the file result
        localFilePath = filePath.replace(u'/data/rali8/Tmp/rali/bt/burtrad/corpus_renamed/', u'./manuallyAnnotated/')
        utilsOs.dumpRawLines(listOfAnnotations, localFilePath, addNewline=True, rewrite=True)
        utilsOs.moveUpAndLeftNLines(2, slowly=False)



listOfFilesPath = u'./randomSelected100MISALIGNED.json'
annotateFiles(listOfFilesPath, anotatedOutputFolder=u'./manuallyAnnotated/')