#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import subprocess, os
import b000path, utilsOs
from bs4 import BeautifulSoup
from random import randint
from shutil import copyfile
import xml.etree.ElementTree as ET


def getTmxFlaggedData(tmxFilePathList):
    """
    Returns the data from the tmx files
    :param tmxFilePathList:
    :return: the flagged info
    """
    try:
        d = ET
    except NameError:
        import xml.etree.ElementTree as ET
    for tmxFilePath in tmxFilePathList:
        try:
            tree = ET.parse(tmxFilePath)
            root = tree.getroot()
            for indChild, child in enumerate(root[1]):
                if child.get('flag_type') is not None:
                    flagType = child.get('flag_type')
                    segmentNb = child.get('segment_number')
                    flagDate = child.get('flag_date')
                    for tuv in child.findall('tuv'):
                        lang = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                        if lang == u'en':
                            enSent = tuv[0].text
                        else:
                            frSent = tuv[0].text
                    try:
                        yield flagType, indChild, enSent, frSent, segmentNb, flagDate
                    except UnboundLocalError:
                        yield None
        except ET.ParseError:
            yield None


def selectNRandomFlaggedOrigDocs(n=10):
    """
    Randomly selects a N number of original docs and places them in a specific folder to be treated later
    :param n: number of docs to randomly select from the original flagged docs
    :return:
    """
    regroupDict = {}
    selectedFiles = set([])
    path = u'{0}DC-24/'.format(b000path.getBtOriginalDocsPath())
    # get deep list of files
    fileList = utilsOs.goDeepGetFiles(path, fileList=[], format=None)
    # get rid of everything that is not a .doc file
    fileList = [file for file in fileList if u'.doc' in file]
    # get rid of the .docx files
    fileList = [file for file in fileList if u'.docx' not in file]
    # regroup according to the file paths
    for filePath in fileList:
        fileKey = filePath.split(u'/')
        pathKey = u'{0}/{1}/{2}/{3}'.format(fileKey[-5], fileKey[-4], fileKey[-3], fileKey[-2])
        if pathKey not in regroupDict:
            regroupDict[pathKey] = []
        regroupDict[pathKey].append(filePath)
    # regroup the docs 2 by 2 : fr and en
    for fp in list(regroupDict.keys()):
        pl = regroupDict[fp]
        if len(pl) != 2:
            del regroupDict[fp]
    # select randomly
    pathList = list(regroupDict.keys())
    for nb in range(n):
        randomIndex = randint(0, len(pathList))
        while pathList[randomIndex] in selectedFiles:
            randomIndex = randint(0, len(pathList))
        selectedFiles.add(pathList[randomIndex])
    # dump in different folder
    new = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/FLAGGED/'
    for selected in selectedFiles:
        for filePath in regroupDict[selected]:
            fList = filePath.split(u'/')
            newFolderPath = u'{0}{1}*{2}*{3}*{4}/'.format(new, fList[-5], fList[-4], fList[-3], fList[-2])
            newFolderPath = newFolderPath.replace(u' ', u'_')
            utilsOs.createEmptyFolder(newFolderPath)
            newFilePath = u'{0}{1}'.format(newFolderPath, fList[-1])
            newFilePath = newFilePath.replace(u' ', u'_')
            copyfile(filePath, newFilePath)
            # get the tmx file
            tmxFilePath = [f for f in utilsOs.getContentOfFolder(filePath.replace(fList[-1], u'')) if u'.tmx' in f][0]
            tmxFilePath = filePath.replace(fList[-1], tmxFilePath)
            copyfile(tmxFilePath, newFilePath.replace(fList[-1], tmxFilePath.split(u'/')[-1]))
            # get the flagging details file
            copyfile(filePath.replace(fList[-1], u'flagging-details.txt'),
                     newFilePath.replace(fList[-1], u'flagging-details.txt'))


def cleanStr(string):
    string = string.replace(u'\n', u' ').replace(u'\t', u' ')
    for n in reversed(range(2, 51)):
        string = string.replace(u' '*n, u' ')
    if string is None:
        string = u''
    return string


def convertDocFilesToHtml(docsFolderPath, dump=True, fileFormat=u"html"):
    """
    go in deep searching for the original doc files
    :param docsFolderPath: path to the parent folder where the original docs are
    :return: htmlPathList: list of path strings to the converted html files
    """
    htmlPathList = []
    for origDocFolder in [fold for fold in os.listdir(docsFolderPath) if u'*' in fold]:
        folderPath = u'{0}{1}/'.format(docsFolderPath, origDocFolder)
        for docFile in [file for file in os.listdir(folderPath) if u'.doc' in file]:
            inputPath = u'{0}{1}'.format(folderPath, docFile)
            outputPath = u'{0}{1}'.format(folderPath, docFile.replace(u'.doc', u''))
            # convert and dump
            if dump is True:
                subprocess.call(['libreoffice', '--headless', '--convert-to', fileFormat, inputPath,
                                 '--outdir', outputPath])
            # save path to html index file into list
            htmlPathList.append(u'{0}/{1}'.format(outputPath, docFile.replace(u'.doc', u'.{0}'.format(fileFormat))))
    return htmlPathList


def list2Set(aList):
    try:
        aSet = set(aList).remove(u'')
    except KeyError:
        aSet = set(aList)
    if aSet is None:
        aSet = set([u'***-*-**-*-****'])
    return aSet


def findTheAlignFiles(path):
    commandId = path.split(u'*')[-1].split(u'/')[0]
    alignedFolderPath = u'**--**/{0}'.format((path.split(u'/')[-3]).replace(u'*', u'/')).replace(commandId, u'')
    alignedFolderPath = b000path.desAnonymizePath(alignedFolderPath).replace(commandId, u'')
    # get the content of the aligned folder and get the doc id
    try:
        folderContent = [file for file in os.listdir(alignedFolderPath) if u'.tmx.en' in file]
        folderContent = [file.replace(u'.tmx.en', u'').replace(alignedFolderPath, u'') for file in folderContent]
    # if there is no folder in the first sent corpus return none
    except FileNotFoundError:
        return None, None
    # find the one resembling most to the commandId
    fileNames = []
    for orderId in folderContent:
        if u"-" in commandId:
            idCodes = orderId
        else:
            idCodes = orderId.split(u'-')[0]
        if idCodes == commandId:
            fileNames.append(orderId)
    # if we found one, we return the path to the english and french files
    if len(fileNames) == 1:
        alignedPathEn = u'{0}{1}.tmx.en'.format(alignedFolderPath, fileNames[0])
        alignedPathFr = u'{0}{1}.tmx.fr'.format(alignedFolderPath, fileNames[0])
        return alignedPathEn, alignedPathFr
    # if we found more than one, return None
    return None, None

def guessLang(htmlLns, enLns, frLns, counter, flaggedEn, flaggedFr):
    enSet = list2Set(enLns)
    frSet = list2Set(frLns)
    for htLn in htmlLns:
        cleanHtLn = cleanStr(htLn)
        if cleanHtLn in enSet:
            counter[0] += 1
        if cleanHtLn in frSet:
            counter[1] += 1
    if counter[0] >= counter[1]:
        langLns = list(enLns)
        langSet = enSet
        langFlagged = set(flaggedEn)
        lang = u"en"
    else:
        langLns = list(frLns)
        langSet = frSet
        langFlagged = set(flaggedFr)
        lang = u"fr"
    return langLns, langSet, langFlagged, counter, lang


def useBeautifulSoup(htmlFilePath, lnList, alignedPathEn, alignedPathFr, counter, flaggedEn, flaggedFr):
    with open(htmlFilePath) as hf:
        htmlContent = hf.read()
    soup = BeautifulSoup(htmlContent, 'html.parser')
    # add the header data and metadata
    ### lnList.append(str(soup.doctype))
    lnList.append(u'<html>')
    lnList.append(str(soup.head))
    # add the css internal stylesheet
    lnList.append(u'''<style>\n.highlightMatch { background-color:#9FD2EF; }\n
    .highlightFlagged { background-color:#EFAC9F; }\n</style>''')
    lnList.append(u'<body>')
    # open the alignment files
    with open(alignedPathEn) as enFile:
        enLns = [cleanStr(ln.replace(u'\n', u'')) for ln in enFile.readlines()]
    with open(alignedPathFr) as frFile:
        frLns = [cleanStr(ln.replace(u'\n', u'')) for ln in frFile.readlines()]
    # guess the language
    htmlLns = soup.get_text().split(u'\n')
    langLns, langSet, langFlagged, counter, lang = guessLang(htmlLns, enLns, frLns, counter, flaggedEn, flaggedFr)
    # highlight in the html the sentences appearing in the aligned file
    for bs4Elem in soup.find_all(u'p'):
        elemString = [bs4Elem.string]
        # check if the string is in the children instead of in the paragraph directly
        descendList = bs4Elem.children
        for descend in descendList:
            if descend.string is not None:
                elemString.append(descend.string)
        # join the strings
        if elemString is not None:
            elemString = u''.join([e for e in elemString if e is not None])
        # check if it appears in the aligned files
        if elemString is not None:
            cleanElemStr = cleanStr(elemString)
            if cleanElemStr in langSet:
                # if the sentence is one of the flagged lines put the string between highlight tags
                typeOfHighlight = u'highlightFlagged' if cleanElemStr in langFlagged else u'highlightMatch'
                # put the string between highlight tags
                elemString = u'<p><span class="{0}">{1}</span></p>'.format(typeOfHighlight, cleanElemStr)
                # remove from the aligned list
                try:
                    langLns.remove(cleanElemStr)
                except ValueError:
                    pass
            else:
                # verify there is no partial match
                subElemString = u'<p>'
                # dejavu marker: so we do not take into account what was already <mark>ed
                dejavu = float(u'-inf')
                # search for a partial match
                for i in range(len(cleanElemStr)):
                    for n in reversed(range(6, len(cleanElemStr))):
                        if i > dejavu:
                            if cleanElemStr[i:i + n + 1] in langSet:
                                start = 0 if dejavu == float(u'-inf') else dejavu + 1
                                # if the sentence is one of the flagged lines put the string between highlight tags
                                typeOfHighlight = u'highlightFlagged' if cleanElemStr[
                                                                         i:i + n + 1] in langFlagged else u'highlightMatch'
                                # add the partial element (perhaps preceded by the not found segment)
                                subElemString = u'{0}{1}{2}'.format(subElemString, cleanElemStr[start:i],
                                                                    u'<span class="{0}">{1}</span>'.format(
                                                                        typeOfHighlight, cleanElemStr[i:i + n + 1]))
                                dejavu = i + n
                                # remove from the aligned list
                                try:
                                    langLns.remove(cleanElemStr[i:i + n + 1])
                                except ValueError:
                                    pass
                # if there wasn't even a partial match
                if dejavu == float(u'-inf'):
                    elemString = u'<p>{0}</p>'.format(elemString)
                # if there was a partial match, add the remainder
                else:
                    elemString = u'{0}{1}</p>'.format(subElemString, cleanElemStr[dejavu + 1:])
            lnList.append(elemString)
    return lnList, langLns, counter


def getLinesAsHtml(htmlFilePath, lnList, alignedPathEn, alignedPathFr, counter,
                                                       flaggedEn, flaggedFr):
    hlNb = 0
    # add the header data
    lnList.append(u'<html>')
    # add the css internal stylesheet
    lnList.append(u'''<style>\n.highlightMatch0 { background-color:#9FD2EF; }\n
        .highlightMatch1 { background-color:#99CCFF; }\n
        .highlightMatch2 { background-color:#99FFFF; }\n
        .highlightMatch3 { background-color:#66FFFF; }\n
        .highlightMatch4 { background-color:#66CCCC; }\n
        .highlightFlagged { background-color:#EFAC9F; }\n</style>''')
    lnList.append(u'<body>')
    # open the alignment files
    with open(alignedPathEn) as enFile:
        enLns = [cleanStr(ln.replace(u'\n', u'')) for ln in enFile.readlines()]
    with open(alignedPathFr) as frFile:
        frLns = [cleanStr(ln.replace(u'\n', u'')) for ln in frFile.readlines()]
    # guess the language
    with open(htmlFilePath) as hfp:
        htmlLns = [hln.replace(u"\n", u"") for hln in hfp.readlines()]
    ##################################################################
    total = len(enLns)
    aligned = 0
    ##################################################################
    langLns, langSet, langFlagged, counter, lang = guessLang(htmlLns, enLns, frLns, counter, flaggedEn, flaggedFr)
    # highlight in the html the sentences appearing in the aligned file
    for elemString in htmlLns:
        # check if it appears in the aligned files
        if elemString is not u"":
            cleanElemStr = cleanStr(elemString)
            if cleanElemStr in set(langLns):
                # if the sentence is one of the flagged lines put the string between highlight tags
                typeOfHighlight = u'highlightFlagged' if cleanElemStr in langFlagged else u'highlightMatch{0}'.format(hlNb)
                hlNb = hlNb + 1 if hlNb < 4 else 0
                # put the string between highlight tags
                elemString = u'<p><span class="{0}">{1}</span></p>'.format(typeOfHighlight, cleanElemStr)
                ##################################################################
                total+=1
                aligned+=1
                ##################################################################
                # remove from the aligned list
                try:
                    langLns.remove(cleanElemStr)
                except ValueError:
                    pass
            else:
                # verify there is no partial match
                subElemString = u'<p>'
                # dejavu marker: so we do not take into account what was already <mark>ed
                dejavu = float(u'-inf')
                # search for a partial match
                for i in range(len(cleanElemStr)):
                    for n in reversed(range(6, len(cleanElemStr))):
                        if i > dejavu:
                            if cleanElemStr[i:i + n + 1] in set(langLns):
                                start = 0 if dejavu == float(u'-inf') else dejavu + 1
                                # if the sentence is one of the flagged lines put the string between highlight tags
                                typeOfHighlight = u'highlightFlagged' if cleanElemStr[
                                                                         i:i + n + 1] in langFlagged else u'highlightMatch{0}'.format(hlNb)
                                hlNb = hlNb + 1 if hlNb < 4 else 0
                                # add the partial element (perhaps preceded by the not found segment)
                                subElemString = u'{0}{1}{2}'.format(subElemString, cleanElemStr[start:i],
                                                                    u'<span class="{0}">{1}</span>'.format(
                                                                        typeOfHighlight, cleanElemStr[i:i + n + 1]))
                                ##################################################################
                                total+=1
                                aligned+=1
                                dejavu = i + n
                                ##################################################################
                                # remove from the aligned list
                                try:
                                    langLns.remove(cleanElemStr[i:i + n + 1])
                                except ValueError:
                                    pass
                # if there wasn't even a partial match
                ##################################################################
                total+=1
                ##################################################################
                if dejavu == float(u'-inf'):
                    elemString = u'<p>{0}</p>'.format(elemString)
                # if there was a partial match, add the remainder
                else:
                    elemString = u'{0}{1}</p>'.format(subElemString, cleanElemStr[dejavu + 1:])
            lnList.append(elemString)
    ##################################################################
    print(22222, total, aligned, lang)
    ##################################################################
    return lnList, langLns, counter


def highlightHtmlAlign(listOfHtmlFilePaths):
    """
    open the html file and highlights the sentences that were aligned
    :param listOfHtmlFilePaths: list containing the file paths to the html version of the original docs
    :return: None
    """
    for htmlFilePath in listOfHtmlFilePaths:
        print(10000, htmlFilePath)
        lnList = []
        counter = [0, 0]
        # get the path to the aligned files
        alignedPathEn, alignedPathFr = findTheAlignFiles(htmlFilePath)
        # if there are multiple choices, unable to choose amongst them, pass to the next one
        if alignedPathEn is None:
            pass
        else:
            try:
                # get the flagged lines from the tmx file
                fpSplit = htmlFilePath.split(u'/')
                flagSect = u'{0}/{1}'.format(fpSplit[-2], fpSplit[-1])
                flaggedFilePaths = [file for file in os.listdir(htmlFilePath.replace(flagSect, u'')) if u'.tmx' in file]
                flaggedFilePaths = [u'{0}{1}'.format(htmlFilePath.replace(flagSect, u''), flaggedFile) for flaggedFile in flaggedFilePaths]
                flaggedEn, flaggedFr = [], []
                if len(flaggedFilePaths) != 0:
                    for infoTupl in getTmxFlaggedData(flaggedFilePaths):
                        if infoTupl is not None:
                            flagType, indChild, enSent, frSent, segmentNb, flagDate = infoTupl
                            flaggedEn.append(cleanStr(enSent.replace(u'\n', u'')))
                            flaggedFr.append(cleanStr(frSent.replace(u'\n', u'')))
                # open the html file as a beautiful soup object
                if u'.html' in htmlFilePath:
                    lnList, langLns, counter = useBeautifulSoup(htmlFilePath, lnList, alignedPathEn, alignedPathFr,
                                                                counter, flaggedEn, flaggedFr)
                # open the txt file and make it a highlighted html file
                elif u'.txt' in htmlFilePath:
                    lnList, langLns, counter = getLinesAsHtml(htmlFilePath, lnList, alignedPathEn, alignedPathFr,
                                                              counter, flaggedEn, flaggedFr)
                lnList.append(u'</body>')
                lnList.append(u'</html>')
                # dump the html in a different html file
                utilsOs.dumpRawLines(lnList, u'{0}.highlight.html'.format(htmlFilePath), addNewline=True, rewrite=True)
                # dump the lines we did not find
                utilsOs.dumpRawLines(langLns, u'{0}.remnant'.format(htmlFilePath), addNewline=True, rewrite=True)
            except FileNotFoundError:
                pass


def countNbSpInTmx(pathsList):
    """
    opens the tmx files and counts the number of en-fr and fr-en SPs
    :param pathsList: list containing the paths to files amongst which the tmx are
    :return: None
    """
    tmxFilePathList = [file for file in pathsList if u'.tmx' in file]
    try:
        d = ET
    except NameError:
        import xml.etree.ElementTree as ET
    sps = 0
    for tmxFilePath in tmxFilePathList:
        # open the tmx
        try:
            tree = ET.parse(tmxFilePath)
            root = tree.getroot()
            for indChild, child in enumerate(root[1].findall('tu')):
                sps += 1
        except ET.ParseError:
            pass
    print(sps)


########################################################################

# count the time the algorithm takes to run
startTime = utilsOs.countTime()


# docsPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/NOT-FLAGGED/'
# docsPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/FLAGGED/'
docsPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23/'

# selectNRandomFlaggedOrigDocs(n=10)

pathList = convertDocFilesToHtml(docsPath, dump=False, fileFormat=u"txt")

# highlightHtmlAlign([u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/FLAGGED/QUALITY*032-IND_AFF_AND_NORTH_DEV*en-fr*9550529/9550529_001_FR_NCR-#9522375-v4-ESDPP_-_AIAI_NR_JOINT/9550529_001_FR_NCR-#9522375-v4-ESDPP_-_AIAI_NR_JOINT.txt',
#                     u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/FLAGGED/QUALITY*032-IND_AFF_AND_NORTH_DEV*en-fr*9550529/9550529_001_EN_NCR-#9522375-v4-ESDPP_-_AIAI_NR_JOINT/9550529_001_EN_NCR-#9522375-v4-ESDPP_-_AIAI_NR_JOINT.txt"])

highlightHtmlAlign(pathList)

########################################################################3
# pathsList = utilsOs.goDeepGetFiles(u'/data/rali8/Tmp/rali/bt/burtrad/archive2/DC-24/', fileList=[], format=None)
# pathsList = [f for f in pathsList if u'.tmx' not in f]
# pathsList = [f for f in pathsList if u'flagging-' not in f]
# pathsList = [f for f in pathsList if u'QUALITY' in f]
# print(len(pathsList))
# # countNbSpInTmx(pathsList)
#########################################################################3

# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))