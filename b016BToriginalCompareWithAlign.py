#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys

sys.path.append(u'../utils')
# sys.path.append(u'./utils')
import subprocess, argparse, os, re
import b000path, utilsOs, utilsString
from bs4 import BeautifulSoup
from random import randint
from shutil import copyfile
from tqdm import tqdm
import spacy
from nltk.metrics import distance


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
                        # replace nonbreaking hyphens and spaces
                        yield flagType, indChild, enSent, frSent, segmentNb, flagDate
                    except UnboundLocalError:
                        yield None
        except ET.ParseError:
            yield None


def selectNRandomFlaggedOrigDocs(n=10,
                         newFolder=u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/FLAGGED/'):
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
    for selected in selectedFiles:
        for filePath in regroupDict[selected]:
            fList = filePath.split(u'/')
            newFolderPath = u'{0}{1}*{2}*{3}*{4}/'.format(newFolder, fList[-5], fList[-4], fList[-3], fList[-2])
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


def cleanStr(string, removeSpaces=False):
    string = string.replace(u'\n', u' ').replace(u'\t', u' ')
    if removeSpaces:
        string = re.sub(r"""[-/*+.,!?@#$%^&()_–=\[\]\{\}\\<>:"|'“”‘’«»  \r\n¿]+""", u"", string)
    # replace non breaking chars
    string = string.replace("‑", "-").replace(" ", " ")
    for n in reversed(range(2, 51)):
        string = string.replace(u' ' * n, u' ')
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
            outputPath = u'{0}{1}'.format(folderPath, re.sub(r"\.doc[x]?", u"", docFile))
            if not os.path.isdir(outputPath):
                outputPath = u'{0}{1}'.format(folderPath, docFile.replace(u".doc", ""))
            # convert and dump
            if dump is True:
                subprocess.call(['libreoffice', '--headless', '--convert-to', fileFormat, inputPath,
                                 '--outdir', outputPath])
            # save path to html index file into list
            htmlPathList.append(u'{0}/{1}'.format(outputPath, re.sub(r"\.doc[x]?", u'.{0}'.format(fileFormat), docFile)))
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


def guessLang(htmlLns, enLns, frLns, counter, flaggedEn, flaggedFr, removeSpaces=False):
    enLns = [cleanStr(ln, removeSpaces) for ln in enLns]
    frLns = [cleanStr(ln, removeSpaces) for ln in frLns]
    enSet = list2Set(enLns)
    frSet = list2Set(frLns)
    for htLn in htmlLns:
        cleanHtLn = cleanStr(htLn, removeSpaces)
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


def useBeautifulSoup(htmlFilePath, lnList, alignedPathEn, alignedPathFr, counter, flaggedEn, flaggedFr,
                     removeSpaces=False):
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
        enLns = [cleanStr(ln, removeSpaces) for ln in enFile.readlines()]
    with open(alignedPathFr) as frFile:
        frLns = [cleanStr(ln, removeSpaces) for ln in frFile.readlines()]
    # guess the language
    htmlLns = [cleanStr(ln, removeSpaces) for ln in soup.get_text().split(u'\n')]
    # ## langLns, langSet, langFlagged, counter, lang = guessLang(htmlLns, enLns, frLns, counter, flaggedEn, flaggedFr,
    #                                                          removeSpaces)
    if re.search(r"[0-9]{1,2}_EN[_\.]", htmlFilePath.split("/")[-2]) is not None:
        langLns, langSet, langFlagged, lang = enLns, list2Set(enLns), set(flaggedEn), "en"
    else:
        langLns, langSet, langFlagged, lang = frLns, list2Set(frLns), set(flaggedFr), "fr"
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
            cleanElemStr = cleanStr(elemString, removeSpaces)
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
                   flaggedEn, flaggedFr, removeSpaces=False):
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
    if alignedPathEn is None:
        enLns = []
    else:
        with open(alignedPathEn) as enFile:
            enLns = [cleanStr(ln, removeSpaces) for ln in enFile.readlines()]
    if alignedPathFr is None:
        frLns = []
    else:
        with open(alignedPathFr) as frFile:
            frLns = [cleanStr(ln, removeSpaces) for ln in frFile.readlines()]
    # get html lines
    with open(htmlFilePath) as hfp:
        htmlLns = [cleanStr(hln, removeSpaces) for hln in hfp.readlines()]
    ##################################################################
    total = len(enLns)
    aligned = 0
    ##################################################################
    # quess the language
    # ## langLns, langSet, langFlagged, counter, lang = guessLang(htmlLns, enLns, frLns, counter, flaggedEn, flaggedFr,
    #                                                          removeSpaces)
    if re.search(r"[0-9]{1,2}_EN[_\.]", htmlFilePath.split("/")[-2]) is not None:
        langLns, langSet, langFlagged, lang = enLns, list2Set(enLns), set(flaggedEn), "en"
    else:
        langLns, langSet, langFlagged, lang = frLns, list2Set(frLns), set(flaggedFr), "fr"
    # highlight in the html the sentences appearing in the aligned file
    for elemString in htmlLns:
        # check if it appears in the aligned files
        if elemString is not u"":
            if elemString in set(langLns):
                # if the sentence is one of the flagged lines put the string between highlight tags
                typeOfHighlight = u'highlightFlagged' if elemString in langFlagged else u'highlightMatch{0}'.format(
                    hlNb)
                hlNb = hlNb + 1 if hlNb < 4 else 0
                # put the string between highlight tags
                origElemString = elemString
                elemString = u'<p><span class="{0}">{1}</span></p>'.format(typeOfHighlight, elemString)
                ##################################################################
                total += 1
                aligned += 1
                ##################################################################
                # remove from the aligned list
                try:
                    langLns.remove(origElemString)
                except ValueError:
                    pass
            else:
                # verify there is no partial match
                subElemString = u'<p>'
                # dejavu marker: so we do not take into account what was already <mark>ed
                dejavu = float(u'-inf')
                # search for a partial match
                for i in range(len(elemString)):
                    for n in reversed(range(6, len(elemString))):
                        if i > dejavu:
                            if elemString[i:i + n + 1] in set(langLns):
                                start = 0 if dejavu == float(u'-inf') else dejavu + 1
                                # if the sentence is one of the flagged lines put the string between highlight tags
                                typeOfHighlight = u'highlightFlagged' if elemString[
                                                                         i:i + n + 1] in langFlagged else u'highlightMatch{0}'.format(
                                    hlNb)
                                hlNb = hlNb + 1 if hlNb < 4 else 0
                                # add the partial element (perhaps preceded by the not found segment)
                                subElemString = u'{0}{1}{2}'.format(subElemString, elemString[start:i],
                                                                    u'<span class="{0}">{1}</span>'.format(
                                                                        typeOfHighlight, elemString[i:i + n + 1]))
                                ##################################################################
                                total += 1
                                aligned += 1
                                dejavu = i + n
                                ##################################################################
                                # remove from the aligned list
                                try:
                                    langLns.remove(elemString[i:i + n + 1])
                                except ValueError:
                                    pass
                # if there wasn't even a partial match
                ##################################################################
                total += 1
                ##################################################################
                if dejavu == float(u'-inf'):
                    elemString = u'<p>{0}</p>'.format(elemString)
                # if there was a partial match, add the remainder
                else:
                    elemString = u'{0}{1}</p>'.format(subElemString, elemString[dejavu + 1:])
            lnList.append(elemString)
    ##################################################################
    # print(22222, total, aligned, lang)
    ##################################################################
    return lnList, langLns, counter


def copyTmxToSampleFolder(listOfOutputFolderPaths):
    from shutil import copyfile
    for outFold in tqdm(listOfOutputFolderPaths):
        fpSplit = outFold.split(u'/')
        lang = "en" if re.search(r"[0-9]{1,2}_EN[_\.]", fpSplit[-2]) is not None else "fr"
        tmxPath = "{0}{1}/".format(b000path.getBtFolderPath(), u"/".join(fpSplit[-3].split("*")[:-1]))
        tmxFiles = ["{0}{1}".format(tmxPath, f) for f in os.listdir(tmxPath) if (fpSplit[-3].split("*")[-1] in f and "tmx.{0}".format(lang) in f)]
        if len(tmxFiles) == 1:
            copyfile(tmxFiles[0], "{0}{1}".format(outFold, tmxFiles[0].split("/")[-1]))
        else:
            print(outFold)



def highlightHtmlAlign(listOfHtmlFilePaths, removeSpaces=False, alignUsed=""):
    """
    open the html file and highlights the sentences that were aligned
    :param listOfHtmlFilePaths: list containing the file paths to the html version of the original docs
    :param removeSpaces :
    :return: None
    """
    for htmlFilePath in tqdm(listOfHtmlFilePaths):
        fpSplit = htmlFilePath.split(u'/')
        lnList = []
        counter = [0, 0]
        encounteredError = False
        # overwrite old files
        with open(u'{0}.highlight{1}.html'.format(htmlFilePath, alignUsed), "w") as highFile:
            highFile.write("")
        with open(u'{0}.remnant{1}'.format(htmlFilePath, alignUsed), "w") as remnFile:
            remnFile.write("")
        # get the path to the aligned files
        if alignUsed == "":
            alignedPathEn, alignedPathFr = findTheAlignFiles(htmlFilePath)
        elif alignUsed == "spacy":
            alignPath = "{0}/".format("/".join(fpSplit[:-1]))
            alignPathFile = ["{0}{1}".format(alignPath, f) for f in os.listdir(alignPath) if ".spacy_split" in f]
            # if there is no file then return none ang write the path to an error log
            if len(alignPathFile) == 0:
                with open("./errorLog", "a") as errorLog:
                    errorLog.write("{0}\n".format(listOfHtmlFilePaths))
                encounteredError = True
            else:
                alignedPathEn = alignPathFile[0] if re.search(r"[0-9]{1,2}_EN[_\.]", fpSplit[-2]) is not None else None
                alignedPathFr = alignPathFile[0] if alignedPathEn is None else None
        elif alignUsed == "nltk":
            alignPath = "{0}/".format("/".join(fpSplit[:-1]))
            alignPathFile = ["{0}{1}".format(alignPath, f) for f in os.listdir(alignPath) if ".nltk_split" in f]
            # if there is no file then return none ang write the path to an error log
            if len(alignPathFile) == 0:
                with open("./errorLog", "a") as errorLog:
                    errorLog.write("{0}\n".format(alignPathFile))
                encounteredError = True
            else:
                alignedPathEn = alignPathFile[0] if re.search(r"[0-9]{1,2}_EN[_\.]", fpSplit[-2]) is not None else None
                alignedPathFr = alignPathFile[0] if alignedPathEn is None else None
        else:
            alignPath = "{0}/".format("/".join(fpSplit[:-1]))
            alignPathFile = ["{0}{1}".format(alignPath, f) for f in os.listdir(alignPath) if ".tmx." in f]
            # if there is no file then return none ang write the path to an error log
            if len(alignPathFile) == 0:
                with open("./errorLog", "a") as errorLog:
                    errorLog.write("{0}\n".format(alignPathFile))
                encounteredError = True
            else:
                alignedPathEn = alignPathFile[0] if re.search(r"[0-9]{1,2}_EN[_\.]", fpSplit[-2]) is not None else None
                alignedPathFr = alignPathFile[0] if alignedPathEn is None else None
        # if there are multiple choices, unable to choose amongst them, pass to the next one
        if alignedPathEn is None and alignedPathFr is None:
            pass
        # if there was no file to be found, pass tot he next one
        elif encounteredError is True:
            pass
        else:
            flaggedEn, flaggedFr = [], []
            # if there is a flagged sentence file
            try:
                # get the FLAGGED SENTENCE along with the rest of the tmx sentences
                lang = "en" if re.search(r"[0-9]{1,2}_EN[_\.]", fpSplit[-2]) is not None else "fr"
                tmxPath = "{0}DC-24/{1}/".format(b000path.getBtOriginalDocsPath(), u"/".join(fpSplit[-3].split("*")[:-1]))
                flaggedFilePaths = ["{0}{1}".format(tmxPath, f) for f in os.listdir(tmxPath) if
                                    (fpSplit[-3].split("*")[-1] in f and ".tmx." not in f)]
                if len(flaggedFilePaths) != 0:
                    for infoTupl in getTmxFlaggedData(flaggedFilePaths):
                        if infoTupl is not None:
                            flagType, indChild, enSent, frSent, segmentNb, flagDate = infoTupl
                            flaggedEn.append(cleanStr(enSent, removeSpaces))
                            flaggedFr.append(cleanStr(frSent, removeSpaces))
            # if there is no flagged sentence file
            except FileNotFoundError:
                pass
            try:
                # open the html file as a beautiful soup object
                if u'.html' in htmlFilePath:
                    lnList, langLns, counter = useBeautifulSoup(htmlFilePath, lnList, alignedPathEn, alignedPathFr,
                                                                counter, flaggedEn, flaggedFr, removeSpaces)
                # open the txt file and make it a highlighted html file
                elif u'.txt' in htmlFilePath:
                    lnList, langLns, counter = getLinesAsHtml(htmlFilePath, lnList, alignedPathEn, alignedPathFr,
                                                              counter, flaggedEn, flaggedFr, removeSpaces)
                lnList.append(u'</body>')
                lnList.append(u'</html>')

                # dump the html in a different html file
                utilsOs.dumpRawLines(lnList, u'{0}.highlight{1}.html'.format(htmlFilePath, alignUsed), addNewline=True, rewrite=True)
                # dump the lines we did not find
                utilsOs.dumpRawLines(langLns, u'{0}.remnant{1}'.format(htmlFilePath, alignUsed), addNewline=True, rewrite=True)
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


def findNbOfTagsInHtml(htmlFilePath, tagStringName, findInHtmlSection=(1, 1), countInChars=True):
    allSent, tagSent = [], []
    with open(htmlFilePath) as htmlFile:
        html = htmlFile.read()
    soup = BeautifulSoup(html, 'html.parser')
    # if only count tads in the first one third use (1,3), in the first half (1,2), in the last quarter (4,4)
    if findInHtmlSection != (1, 1):
        body = soup.find('body')
        bodyContent = body.findChildren(recursive=False)
        sectionSize = int(len(bodyContent) / findInHtmlSection[1])
        start = (findInHtmlSection[0] - 1) * sectionSize
        end = (findInHtmlSection[0]) * sectionSize if findInHtmlSection[0] != findInHtmlSection[1] else len(bodyContent)
        sectionContent = bodyContent[start:end]
        sectionContent = "\n".join(["<html>", "<body>"] + [str(t) for t in sectionContent] + ["</body>", "</html>"])
        soup = BeautifulSoup(sectionContent, 'html.parser')
    allTags = soup.find_all(tagStringName)
    # eliminate empty spaces
    for tagEl in list(allTags):
        tagText = tagEl.text
        nonWhiteSpaceText = (tagText).replace(u" ", u"").replace(u"\t", u"").replace(u"\n", u"").replace(u"\ufeff", u"")
        if bool(nonWhiteSpaceText) is False:
            allTags.remove(tagEl)
    # count the sub-sentences inside the paragraphs
    if tagStringName == u"p":
        nbSent = 0
        for tagEl in list(allTags):
            tagText = tagEl.text
            allSpans = tagEl.find_all(u"span")
            # count span sentences and in-between sentences
            for spanEl in allSpans:
                allSent.append(spanEl.text)
                tagSent.append((spanEl.text))
                tagText = tagText.replace(spanEl.text, u"***---***")
            tagList = tagText.split(u"***---***")
            allSent += [s for s in tagList if s not in [u"", " ", "  ", "\t", "\n"]]
            if u"***---***" in tagText:
                if countInChars != True:
                    nbSent += len(tagList) - 1
                else:
                    nbSent += sum([len(clearSent) for clearSent in tagList]+[len(spanSent.text) for spanSent in allSpans])
            else:
                nbSent += 1
                allSent.append(tagText)
        return nbSent
    # return the nb of tags
    if countInChars != True:
        nbSent = len(allTags)
    else:
        nbSent = sum([len(spanSent.text) for spanSent in allTags])
    return nbSent


def findLengthOfTagSentInHtml(htmlFilePath, tagStringName, findInHtmlSection=(1, 1)):
    allSent, tagSent = [], []
    with open(htmlFilePath) as htmlFile:
        html = htmlFile.read()
    soup = BeautifulSoup(html, 'html.parser')
    # if only count tads in the first one third use (1,3), in the first half (1,2), in the last quarter (4,4)
    if findInHtmlSection != (1, 1):
        body = soup.find('body')
        bodyContent = body.findChildren(recursive=False)
        sectionSize = int(len(bodyContent) / findInHtmlSection[1])
        start = (findInHtmlSection[0] - 1) * sectionSize
        end = (findInHtmlSection[0]) * sectionSize if findInHtmlSection[0] != findInHtmlSection[1] else len(bodyContent)
        sectionContent = bodyContent[start:end]
        sectionContent = "\n".join(["<html>", "<body>"] + [str(t) for t in sectionContent] + ["</body>", "</html>"])
        soup = BeautifulSoup(sectionContent, 'html.parser')
    allTags = soup.find_all(tagStringName)
    # eliminate empty spaces
    for tagEl in list(allTags):
        tagText = tagEl.text
        nonWhiteSpaceText = (tagText).replace(u" ", u"").replace(u"\t", u"").replace(u"\n", u"").replace(u"\ufeff", u"")
        if bool(nonWhiteSpaceText) is False:
            allTags.remove(tagEl)
    allTags = [t.text for t in allTags]
    # return the nb of characters
    return [len(s) for s in allTags]


def getSentences(htmlFilePath):
    allSent, commonSent = [], []
    with open(htmlFilePath) as htmlFile:
        html = htmlFile.read()
    soup = BeautifulSoup(html, 'html.parser')
    allTags = soup.find_all(u"p")
    # eliminate empty spaces
    for tagEl in list(allTags):
        tagText = tagEl.text
        nonWhiteSpaceText = (tagText).replace(u" ", u"").replace(u"\t", u"").replace(u"\n", u"").replace(u"\ufeff", u"")
        if bool(nonWhiteSpaceText) is False:
            allTags.remove(tagEl)
    # count the sub-sentences inside the paragraphs
    for tagEl in list(allTags):
        tagText = tagEl.text
        allSpans = tagEl.find_all(u"span")
        # get span sentences
        for spanEl in allSpans:
            allSent.append(spanEl.text)
            commonSent.append((spanEl.text))
        # get in-between sentences
        tagList = tagText.split(u"***---***")
        if len(tagList) != 0 and len([s for s in tagList if s not in [u"", " ", "  ", "\t", "\n"]]) != 0:
            allSent += [s for s in tagList if s not in [u"", " ", "  ", "\t", "\n"]]
        # get non span sentences
        else:
            allSent.append(tagText)
    # get remnant sentences
    with open(htmlFilePath.replace(".highlight.html", ".remnant").replace(".highlightnltk.html", ".remnantnltk").replace(".highlightspacy.html", ".remnantspacy")) as remnFile:
        tmxExclusivSent = [s.replace("\n", "") for s in remnFile.readlines()]
    # finish adding to sent
    origExclusivSent = [s for s in allSent if s not in set(commonSent)]
    allSent += tmxExclusivSent
    # return the nb of tags
    return allSent, origExclusivSent, commonSent, tmxExclusivSent


def getTypeOfMismatch(htmlFilePath):
    typeOfMismatch = {"elision in tmx": 0, "augmentation in tmx": 0, "displacement": 0, "deletion in tmx": 0}
    allSent, origExclusivSent, commonSent, tmxExclusivSent = getSentences(htmlFilePath)
    origExclusivSent, tmxExclusivSent = set(origExclusivSent), set(tmxExclusivSent)
    for origSent in origExclusivSent:
        mostSimilarTmxSent = [float("-inf"), None, 0]
        the = None
        for tmxSent in tmxExclusivSent:
            # origTmxDist = distance.edit_distance(origSent, tmxSent)
            correspond, origNgrams, tmxNgrams = utilsString.makeNgramInterceptionList(origSent, tmxSent, ngramSize=6,
                                                                                      returnNgramsLists=True)
            origTmxSimil = len(correspond)
            if origTmxSimil > mostSimilarTmxSent[0]:
                mostSimilarTmxSent = [origTmxSimil, tmxSent, origNgrams, tmxNgrams]
                the = tmxSent
        if mostSimilarTmxSent[1] is not None and len(origNgrams) != 0:
            # both orig and tmx sent have more than 80% ngrams in common
            ngramSimilSc = (mostSimilarTmxSent[0] * 2) / (len(mostSimilarTmxSent[2]) + len(mostSimilarTmxSent[3]))
            if ngramSimilSc >= 0.8:
                if len(tmxSent) in range(len(origSent) - 3, len(origSent) + 4) and tmxNgrams[0] != origNgrams[0] and \
                        tmxNgrams[-1] != origNgrams[-1]:
                    typeOfMismatch["displacement"] += 1
                elif len(tmxSent) <= len(origSent):
                    typeOfMismatch["elision in tmx"] += 1
                elif len(tmxSent) > len(origSent):
                    typeOfMismatch["augmentation in tmx"] += 1
            # the orig and tmx sents ressemble somehow, between 50 and 79%:
            elif ngramSimilSc >= 0.5:
                typeOfMismatch["displacement"] += 1
            # if they're are too dissimilar classify them as a deletion
            else:
                typeOfMismatch["deletion in tmx"] += 1
        else:
            typeOfMismatch["deletion in tmx"] += 1
    return typeOfMismatch


def tenMoreLines(ln, openFile, ind, fileIndexes, fileSentences):
    for x in range(10):
        if ln:
            fileIndexes.append(ind)
            fileSentences.append(ln)
            # next line
            ind += 1
            ln = openFile.readline()
        else:
            pass
    return ln, openFile, ind, fileIndexes, fileSentences


def getData(alignaInd, i, aFileIndexes, aFileSentences, aCuts, aSent, aRef, aLn, aFile, aIndex):
    if alignaInd is None:
        aSent.append(u"***∅***")
        return float("inf"), aFileIndexes, aFileSentences, aCuts, aSent, aRef
    if alignaInd in aFileIndexes:
        whereItIs = aFileIndexes.index(alignaInd)
        # get data
        if i != 0:
            aCuts.append(len(" ".join(aSent)))
        aSent.append(aFileSentences[whereItIs].replace(u"\n", u""))
        aRef.append(alignaInd)
        # delete gotten data
        del aFileIndexes[whereItIs]
        del aFileSentences[whereItIs]
    else:
        while alignaInd not in aFileIndexes:
            aLn, aFile, aIndex, aFileIndexes, aFileSentences = tenMoreLines(aLn, aFile,
                                                                            aIndex,
                                                                            aFileIndexes,
                                                                            aFileSentences)
            if alignaInd == 30:
                raise Exception

            if len(aFileIndexes) >= 500:
                break
        try:
            whereItIs = aFileIndexes.index(alignaInd)
            # get data
            if i != 0:
                aCuts.append(len(" ".join(aSent)))
            aSent.append(aFileSentences[whereItIs].replace(u"\n", u""))
            aRef.append(alignaInd)
            # delete gotten data
            del aFileIndexes[whereItIs]
            del aFileSentences[whereItIs]
        except ValueError:
            whereItIs = None
    return whereItIs, aFileIndexes, aFileSentences, aCuts, aSent, aRef


def getYasaAlign(srcFilePath, trgtFilePath, outputFolderPath):
    """
    use YASA to align two parallel files and output the result in a human readeable fashion
    :param srcFilePath: path to the source file
    :param trgtFilePath: path to the target file
    :param outputFolderPath:
    :return:
    """
    utilsOs.createEmptyFolder(outputFolderPath)
    # apply the yasa script
    subprocess.call(["/u/demorali/bin/64/yasa", "-i", "o", "-o", "a",
                     srcFilePath, trgtFilePath, u"{0}yasa.output.arcadeformat".format(outputFolderPath)])
    subprocess.call(["/u/demorali/bin/64/yasa", "-i", "o", "-o", "r",
                     srcFilePath, trgtFilePath, u"{0}yasa.output.raliformat".format(outputFolderPath)])
    # open the arcade format and get the index of the aligned sentences
    indexInfo = []
    with open(u"{0}yasa.output.arcadeformat".format(outputFolderPath)) as arcadeFile:
        with open(u"{0}yasa.output.raliformat".format(outputFolderPath)) as raliFile:
            # first line
            arcadeLn = arcadeFile.readline()
            raliLn = raliFile.readline()
            while arcadeLn:
                # split the different sections of the output data
                arcadeSplit = arcadeLn.split(u'"')
                raliSplit = raliLn.split(u" ")
                # get the line indexes and score
                indexSect = arcadeSplit[1].split(";")
                indexSrc = [int(s.replace(u",", "")) - 1 if s != "" else None for s in indexSect[0].split(" ")]
                indexTgrt = [int(s.replace(u",", "")) - 1 if s != "" else None for s in indexSect[1].split(" ")]
                arcadeScore = float(arcadeSplit[3].replace(u",", ""))
                raliScore = float(raliSplit[1].replace(u"\n", "").replace(u",", ""))
                indexInfo.append({u"src": indexSrc, "trgt": indexTgrt, "scores": [arcadeScore, raliScore]})
                # next line
                arcadeLn = arcadeFile.readline()
                raliLn = raliFile.readline()
    # prepare the output files
    srcRefOutputPath = u"{0}yasa.output.source.reference".format(outputFolderPath)
    srcOutputPath = u"{0}yasa.output.source".format(outputFolderPath)
    srcOutputPathCutIndex = u"{0}yasa.output.source.cut.index".format(outputFolderPath)
    trgtRefOutputPath = u"{0}yasa.output.target.reference".format(outputFolderPath)
    trgtOutputPath = u"{0}yasa.output.target".format(outputFolderPath)
    trgtOutputPathCutIndex = u"{0}yasa.output.target.cut.index".format(outputFolderPath)
    scoreOutputPath = u"{0}yasa.output.score".format(outputFolderPath)
    for filePath in [srcRefOutputPath, srcOutputPath, srcOutputPathCutIndex, trgtRefOutputPath, trgtOutputPath,
                     trgtOutputPathCutIndex, scoreOutputPath]:
        with open(filePath, u"w") as openFile:
            openFile.write("")
    # browse the index list
    srcFileIndexes, srcFileSentences, srcIndex = [], [], 0
    trgtFileIndexes, trgtFileSentences, trgtIndex = [], [], 0
    with open(srcFilePath) as srcFile:
        with open(trgtFilePath) as trgtFile:
            # get lines of source file
            srcLns = [s.replace(u"\n", "") for s in srcFile.readlines()]
            # get lines of target file
            trgtLns = [s.replace(u"\n", "") for s in trgtFile.readlines()]
            # browse the alingment indexes data
            for alignDict in indexInfo:
                # src data
                srcSent, srcCuts = "", []
                for i, alignSrcInd in enumerate(alignDict["src"]):
                    # match to a sentence
                    if alignSrcInd is not None:
                        srcSent = u"{0}{1} ".format(srcSent, srcLns[alignSrcInd])
                        srcCuts.append(len(srcSent))
                    else:
                        srcSent = u"{0} ".format(srcSent)
                        srcCuts.append(None)
                srcRef = [e for e in alignDict["src"] if e is not None]
                srcSent = srcSent[:-1]
                srcCuts = srcCuts[:-1]
                # dump src data
                with open(srcRefOutputPath, "a") as refFile:
                    refFile.write(u"{0}\t{1}\n".format(srcFilePath, srcRef))
                with open(srcOutputPath, "a") as srcSentFile:
                    srcSentFile.write(u"{0}\n".format(srcSent))
                with open(srcOutputPathCutIndex, "a") as cutsFile:
                    cutsFile.write(u"{0}\n".format(srcCuts))
                # trgt data
                trgtSent, trgtCuts = "", []
                for i, aligntrgtInd in enumerate(alignDict["trgt"]):
                    # match to a sentence
                    if aligntrgtInd is not None:
                        trgtSent = u"{0}{1} ".format(trgtSent, trgtLns[aligntrgtInd])
                        trgtCuts.append(len(trgtSent))
                    else:
                        trgtSent = u"{0} ".format(trgtSent)
                        trgtCuts.append(None)
                trgtRef = [e for e in alignDict["trgt"] if e is not None]
                trgtSent = trgtSent[:-1]
                trgtCuts = trgtCuts[:-1]
                # dump all trgt data
                with open(trgtRefOutputPath, "a") as refFile:
                    refFile.write(u"{0}\t{1}\n".format(trgtFilePath, trgtRef))
                with open(trgtOutputPath, "a") as trgtSentFile:
                    trgtSentFile.write(u"{0}\n".format(trgtSent))
                with open(trgtOutputPathCutIndex, "a") as cutsFile:
                    cutsFile.write(u"{0}\n".format(trgtCuts))
                # dump the scores
                with open(scoreOutputPath, "a") as refFile:
                    refFile.write(u"{0}\n".format(alignDict["scores"]))
    return srcOutputPath, trgtOutputPath


def getLenData(counter, htmlFilePath, ind, howMuchTmxIsInOrig, section=None, countInChars=True):
    counter += 1
    section = (1, 1) if section is None else section
    # get the rough number of elements
    inOrig = findNbOfTagsInHtml(htmlFilePath, u"p", section, countInChars)
    inOrigAndTmx = findNbOfTagsInHtml(htmlFilePath, u"span", section, countInChars)
    inOrigNotTmx = inOrig - inOrigAndTmx
    # get the average length of the tag sentences
    lengthInOrig = findLengthOfTagSentInHtml(htmlFilePath, u"p", section)
    lengthInOrigAndTmx = findLengthOfTagSentInHtml(htmlFilePath, u"span", section)
    # just get the length number, not a list
    lengthInOrigNotTmx = sum(lengthInOrig) - sum(lengthInOrigAndTmx)
    if countInChars != True:
        # calculate how many sentences from the tmx appear in the orig file
        if inOrigAndTmx != 0 and inOrig != 0:
            ratioTmxInOrig = float(inOrigAndTmx)/float(inOrig)
        else:
            ratioTmxInOrig = 0.0
    else:
        # calculate how many characters from the tmx appear in the orig file
        if len(lengthInOrig) != 0 and len(lengthInOrigAndTmx) != 0:
            ratioTmxInOrig = float(sum(lengthInOrigAndTmx)) / float(sum(lengthInOrig))
        else:
            ratioTmxInOrig = 0.0
    print(u"file{0}\t{1}".format(ind, ratioTmxInOrig))
    howMuchTmxIsInOrig.append(ratioTmxInOrig)
    return counter, howMuchTmxIsInOrig, lengthInOrig, lengthInOrigAndTmx, lengthInOrigNotTmx


def dumpYasaOut(srcPath, trgtPath, tPath, currentFolder, otherFolder, sentSegmenter="spacy"):
    with open(srcPath) as srcSpa:
        with open("{0}.{1}_split".format(tPath, sentSegmenter), "w") as outSrcSpa:
            outSrcSpa.write("")
            for ln in [l for l in srcSpa.readlines() if l not in ["***∅***\n", "***∅***"]]:
                outSrcSpa.write(ln)
    with open(trgtPath) as trgtSpa:
        otherTPath = [f for f in os.listdir("{0}/{1}/".format(currentFolder, otherFolder))]
        otherTPath = [f for f in otherTPath if f[-4:] == ".txt"][0]
        otherTPath = "{0}/{1}/{2}".format(currentFolder, otherFolder, otherTPath)
        with open("{0}.{1}_split".format(otherTPath, sentSegmenter), "w") as outTrgtSpa:
            outTrgtSpa.write("")
            for ln in [l for l in trgtSpa.readlines() if l not in ["***∅***\n", "***∅***"]]:
                outTrgtSpa.write(ln)


def segmentAndYasaAlign(in_folder):
    # sentence segmentation
    txtPaths = utilsOs.goDeepGetFiles(in_folder, fileList=[], format=u".txt")
    nlpFr = spacy.load("fr")
    nlpEn = spacy.load("en")
    for tPath in tqdm(txtPaths):
        outFolder, fileName = "/".join(tPath.split("/")[:-1]), tPath.split("/")[-1]
        # guess language
        if re.search(r"[0-9]{1,2}_EN[_\.]", fileName) is not None:
            nlp, lang = nlpEn, "en"
        else:
            nlp, lang = nlpFr, "fr"
        # split sentences
        currentFolder = "/".join(tPath.split("/")[:-2])
        splitSpacyPath = "{0}/{1}.{2}.spacy.split".format(currentFolder, tPath.split("/")[-2], lang)
        splitNltkPath = "{0}/{1}.{2}.nltk.split".format(currentFolder, tPath.split("/")[-2], lang)
        sntSpacyList, outSpacySplitPath = utilsString.sentSegmenterSpacy(tPath, splitSpacyPath, nlp)
        sntNltkList, outNltkSplitPath = utilsString.sentSegmenterNltk(tPath, splitNltkPath)
        # align using yasa
        otherLang = "fr" if lang == "en" else "en"
        otherSpacySplitFile = [f for f in os.listdir(currentFolder) if ".{0}.spacy".format(otherLang) in f]
        otherSpacySplitFile = [f for f in otherSpacySplitFile if ".reference" not in f]
        otherNltkSplitFile = [f for f in os.listdir(currentFolder) if ".{0}.nltk".format(otherLang) in f]
        otherNltkSplitFile = [f for f in otherNltkSplitFile if ".reference" not in f]
        outYasaFolder = "{0}/yasa/".format(currentFolder)
        utilsOs.createEmptyFolder(outYasaFolder)
        if len(otherSpacySplitFile) == 1:
            otherSpacySplitFile = "{0}/{1}".format(currentFolder, otherSpacySplitFile[0])
            otherNltkSplitFile = "{0}/{1}".format(currentFolder, otherNltkSplitFile[0])
            otherFolder = [f for f in os.listdir(currentFolder) if os.path.isdir("{0}/{1}".format(currentFolder, f))]
            otherFolder = [f for f in otherFolder if f not in ["yasa", tPath.split("/")[-2]]][0]
            if lang == "en":
                srcSpacyPath, trgtSpacyPath = getYasaAlign(outSpacySplitPath, otherSpacySplitFile, "{0}spacy/".format(outYasaFolder))
                srcNltkPath, trgtNltkPath = getYasaAlign(outNltkSplitPath, otherNltkSplitFile, "{0}nltk/".format(outYasaFolder))
            else:
                trgtSpacyPath, srcSpacyPath = getYasaAlign(otherSpacySplitFile, outSpacySplitPath, "{0}spacy/".format(outYasaFolder))
                trgtNltkPath, srcNltkPath = getYasaAlign(otherNltkSplitFile, outNltkSplitPath, "{0}nltk/".format(outYasaFolder))
            # dump in txt file folder
            dumpYasaOut(srcSpacyPath, trgtSpacyPath, tPath, currentFolder, otherFolder, sentSegmenter="spacy")
            dumpYasaOut(srcNltkPath, trgtNltkPath, tPath, currentFolder, otherFolder, sentSegmenter="nltk")


def getLengthRemnant(htmlFilePath, remnList=None):
    remnantFilePath = htmlFilePath.replace(".highlight.html", ".remnant").replace(".highlightnltk.html", ".remnantnltk").replace(".highlightspacy.html", ".remnantspacy")
    with open(remnantFilePath) as remnantFile:
        # get the lengths
        lnLengths = [len(ln.replace("\n", "")) for ln in remnantFile.readlines()]
        if remnList is None:
            return lnLengths
        return remnList + lnLengths


def getAlignDataStats(intersectionPaths, classifyByMismatchType=False, sourceLang=None, section=None,
                      countInChars=True):
    howMuchTmxIsInOrig = []
    wholeMismatch = {"elision in tmx": 0, "augmentation in tmx": 0, "displacement": 0, "deletion in tmx": 0}
    counter = 0
    totalOrigLenths = []
    totalBothLengths = []
    totalNotTmxLengths = []
    totalLenTmxBefore, totalLenTmxAfter = [], []
    for ind, htmlFilePath in enumerate(intersectionPaths):
        # launch only for files of one lang
        fileName = htmlFilePath.split("/")[-1]
        if sourceLang == "en":
            catch, notCatch, srcLang, trgtLang = r"[0-9]{1,2}_EN[_\.]", r"[0-9]{1,2}_FR[_\.]", "_EN", "_FR"
            if re.search(catch, fileName) is not None:
                if trgtLang not in fileName or fileName.index(srcLang) < fileName.index(trgtLang):
                    counter, howMuchTmxIsInOrig, origLenths, bothLengths, notTmxLengths = getLenData(counter, htmlFilePath,
                                                                                                  ind,
                                                                                                  howMuchTmxIsInOrig,
                                                                                                  section,
                                                                                                  countInChars)
                    totalNotTmxLengths.append(notTmxLengths)  # notTmxLength is an int not a list
                    totalOrigLenths.append(sum(origLenths))
                    totalBothLengths.append(sum(bothLengths))
                    notOrigLen = getLengthRemnant(htmlFilePath)
                    totalLenTmxBefore.append(sum(bothLengths) + sum(notOrigLen))
                    totalLenTmxAfter.append(sum(notOrigLen))
        elif sourceLang == "fr":
            catch, notCatch, srcLang, trgtLang = r"[0-9]{1,2}_[Ff][Rr][_\.]", r"[0-9]{1,2}_EN[_\.]", "_FR", "_EN"
            if re.search(catch, fileName) is not None:
                if trgtLang not in fileName or fileName.index(srcLang) < fileName.index(trgtLang):
                    counter, howMuchTmxIsInOrig, origLenths, bothLengths, notTmxLengths = getLenData(counter, htmlFilePath,
                                                                                                  ind,
                                                                                                  howMuchTmxIsInOrig,
                                                                                                  section,
                                                                                                  countInChars)
                    totalNotTmxLengths.append(notTmxLengths)  # notTmxLength is an int not a list
                    totalOrigLenths.append(sum(origLenths))
                    totalBothLengths.append(sum(bothLengths))
                    notOrigLen = getLengthRemnant(htmlFilePath)
                    totalLenTmxBefore.append(sum(bothLengths) + sum(notOrigLen))
                    totalLenTmxAfter.append(sum(notOrigLen))
            elif re.search(r"[0-9]{1,2}_EN[_\.]", fileName) is not None:
                pass
            else:
                counter, howMuchTmxIsInOrig, origLenths, bothLengths, notTmxLengths = getLenData(counter, htmlFilePath,
                                                                                                 ind,
                                                                                                 howMuchTmxIsInOrig,
                                                                                                 section,
                                                                                                 countInChars)
                totalNotTmxLengths.append(notTmxLengths)  # notTmxLength is an int not a list
                totalOrigLenths.append(sum(origLenths))
                totalBothLengths.append(sum(bothLengths))
                notOrigLen = getLengthRemnant(htmlFilePath)
                totalLenTmxBefore.append(sum(bothLengths) + sum(notOrigLen))
                totalLenTmxAfter.append(sum(notOrigLen))
        elif sourceLang in [None, False, ""]:
            counter, howMuchTmxIsInOrig, origLenths, bothLengths, notTmxLengths = getLenData(counter, htmlFilePath, ind,
                                                                                          howMuchTmxIsInOrig, section)
            totalNotTmxLengths.append(notTmxLengths)  # notTmxLength is an int not a list
            totalOrigLenths.append(sum(origLenths))
            totalBothLengths.append(sum(bothLengths))
            notOrigLen = getLengthRemnant(htmlFilePath)
            totalLenTmxBefore.append(sum(bothLengths) + sum(notOrigLen))
            totalLenTmxAfter.append(sum(notOrigLen))

            # # show the filepaths with disbalance (probably)
            # if ind != 0 and ind % 2 == 0:
            #     if abs(howMuchTmxIsInOrig[ind - 2] - howMuchTmxIsInOrig[-1]) > 0.25:
            #         print(howMuchTmxIsInOrig[ind - 2], intersectionPaths[ind - 2])
            #         print(howMuchTmxIsInOrig[-1], intersectionPaths[ind - 1])
        if classifyByMismatchType is not False:
            # get the sentences and compare them to see what is the nature of the non match
            mismatch = getTypeOfMismatch(htmlFilePath)
            wholeMismatch["elision in tmx"] += mismatch["elision in tmx"]
            wholeMismatch["augmentation in tmx"] += mismatch["augmentation in tmx"]
            wholeMismatch["displacement"] += mismatch["displacement"]
            wholeMismatch["deletion in tmx"] += mismatch["deletion in tmx"]
    if classifyByMismatchType is not False:
        print(u"TYPE OF MISMATCH : ", wholeMismatch)
    print()
    print(u"AVG RATIO = ", sum(howMuchTmxIsInOrig) / len(howMuchTmxIsInOrig))
    print(u"SUM % = ", sum(totalBothLengths) / sum(totalOrigLenths))
    print(u"TOTAL FILES = ", counter)
    print(u"MEAN LENGTH OF ORIG CONTENT = ", sum(totalOrigLenths) / len(totalOrigLenths))
    print(u"MEAN LENGTH OF TMX CONTENT = ", (sum(totalLenTmxBefore)) / (len(totalLenTmxBefore)))
    print(u"MEAN LENGTH OF ORIG AND TMX CONTENT = ", sum(totalBothLengths) / len(totalBothLengths))
    print(u"MEAN LENGTH OF CONTENT NOT IN TMX = ", sum(totalNotTmxLengths) / len(totalNotTmxLengths))
    print(u"MEAN LENGTH OF CONTENT NOT IN ORIG = ", sum(totalLenTmxAfter) / len(totalLenTmxAfter))
    print(u"RATIO OF CONTENT (char) REMAINING IN THE TMX = ", sum(totalLenTmxAfter)/sum(totalLenTmxBefore))


########################################################################
def launchTask(task, inputPath, outputPath, option):
    # GET A SAMPLE OF ORIGINAL DOCS (does not require inputPath)
    if task in ["getOriginals"]:
        # select n random flagged docs, default is 10
        option = 10 if option not in [""] else option
        selectNRandomFlaggedOrigDocs(option, outputPath)
    # HIGHLIGHT THE SENT IN THE TMX APPEARING IN THE ORIGINAL (does not require outputPath)
    elif task in ["highlight", "highlights"]:
        option = re.split(r"[ ]?,[ ]?", option)
        convert = True if option[0].lower() in ["convert", "conv"] else False
        removeSpaces = False if option[1] in [False, "False", "false", "f"] else True
        if option[2] in ["t", "tmx", "Tmx", "TMX", ""]:
            alignUsed = ""
        elif option[2] in ["s", "spa", "spacy", "Spacy"]:
            alignUsed = "spacy"
        elif option[2] in ["n", "nltk", "NLTK"]:
            alignUsed = "nltk"
        else:
            raise TypeError("option argument not in the choices")
        if convert:
            # inputPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/NOT-FLAGGED/'
            # inputPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/FLAGGED/'
            # inputPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23/'
            pathList = convertDocFilesToHtml(inputPath, dump=False, fileFormat=u"txt")
        else:
            # # get the path of the files in the sample
            # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_exact_match/"
            # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_nonbreaking_remove"
            # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23/"
            pathList = utilsOs.goDeepGetFiles(inputPath, fileList=[], format=u".txt")
            # pathsList = utilsOs.goDeepGetFiles(u'/data/rali8/Tmp/rali/bt/burtrad/archive2/DC-24/', fileList=[], format=None)
            # pathsList = [f for f in pathsList if u'.tmx' not in f]
            # pathsList = [f for f in pathsList if u'flagging-' not in f]
            # pathsList = [f for f in pathsList if u'QUALITY' in f]
            # # countNbSpInTmx(pathsList)
        highlightHtmlAlign(pathList, removeSpaces, alignUsed)
    # COUNT THE NB OF SP/CHARS, NOT FOUND SENT and REMNANTS (does not require outputPath)
    elif task in ["stats", "stat"]:
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_exact_match/"
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_nonbreaking_remove/"
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23/"
        #  get the options right
        sourceLang = ""
        section = (1,1)
        form = ""
        if option not in [""]:
            option = re.split(r"[ ]?,[ ]?", option)
            sourceLang = "" if option[0] in ["", "both", "all", "fr-en", "en-fr", "fren", "enfr"] else option[0]
            try:
                section = (int(option[1]), int(option[2]))
                if len(option) == 4:
                    form = option[3].lower() if option[3].lower() not in ["t", "tmx", "Tmx", "TMX"] else ""
            except TypeError:
                raise TypeError("option argument not in the choices")
        # get the paths to highlighted files
        intersectionPaths = utilsOs.goDeepGetFiles(inputPath, fileList=[], format=u"txt.highlight{0}.html".format(form))
        getAlignDataStats(intersectionPaths, classifyByMismatchType=False, sourceLang=sourceLang, section=section,
                          countInChars=True)
    # SENTENCE SEGMENTATION (does not require option)
    elif task in ["segmentation", "segment"]:
        # outSpacy = "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_exact_match/a_spacy_sent_split_docs/"
        # outNltk = "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_exact_match/a_nltk_sent_split_docs/"
        outSpacy = "{0}a_spacy_sent_split_docs/".format(outputPath)
        outNltk = "{0}a_nltk_sent_split_docs/".format(outputPath)
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_exact_match/"
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_nonbreaking_remove/"
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23/"
        txtPaths = utilsOs.goDeepGetFiles(inputPath, fileList=[], format=u".txt")
        nlp = spacy.load("fr")
        for tPath in txtPaths:
            sntSpacyList, outSpacySplitPath = utilsString.sentSegmenterSpacy(tPath, outSpacy, nlp)
            sntNltkList, outNltkSplitPath = utilsString.sentSegmenterNltk(tPath, outNltk)
    # SENTENCE SEGMENTATION AND YASA ALIGN (does not require outputPath)
    elif task in ["yasa"]:
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_exact_match/"
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23_nonbreaking_remove/"
        # inputPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/008originalDocumentsBt/sampleNOT-FLAGGEDinDC23/"
        segmentAndYasaAlign(inputPath)
    else:
        raise ValueError("the task is not recognized")


########################################################################
########################################################################


# count the time the algorithm takes to run
startTime = utilsOs.countTime()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", default="highlight", type=str,
                        help="Task to launch. Choices: getOriginals, highlight, stats, segmentation, yasa")
    parser.add_argument("-in", "--input", default="", type=str, help="path to the input folder or file")
    parser.add_argument("-out", "--output", default="", type=str, help="path to the output folder or file")
    parser.add_argument("-opt", "--option", default="", type=str,
                        help="optional argument to send to the task function, if multiple, separate using a comma ','")
    args = parser.parse_args()

    task = args.task
    inputPath = args.input
    outputPath = args.output
    option = args.option
    launchTask(task, inputPath, outputPath, option)


# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))
