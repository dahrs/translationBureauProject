#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys, os
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsString
import subprocess

# TMOP
# cd ~/Documents/workRALI/004tradBureau/TMOP-master/
# CHANGE config.json if necessary
# python main.py


# MGIZA++

def getLang(langCode, pathToFile=None):
    # get the language
    if langCode is None:
        lang = u"french" if u".fr" in pathToFile or u"_fr" in pathToFile else u"english"
        return lang
    elif langCode in [u"en", u"fr"]:
        lang = u"french" if langCode == u"fr" else u"english"
        return lang


def prepareOutPutFile(pathToFile, fileName=u"source.vcb"):
    output = pathToFile.split(u"/")
    output = u"/".join(output[:-1]) if output[-1] != u"" else u"/".join(output[:-2])
    output = u"{0}/GIZA/".format(output)
    utilsOs.createEmptyFolder(output)
    output = u"{0}{1}".format(output, fileName)
    return output


def makeFreqDict(pathToFile, lang=None):
    freqTokDict = {}
    with open(pathToFile) as outFile:
        # first line
        outLn = outFile.readline()
        while outLn:
            outLn = outLn.replace(u"\n", u"")
            # get the language in the right format
            lang = getLang(lang, pathToFile)
            # tokenize
            # outToks = utilsString.naiveRegexTokenizer(outLn, language=lang,
            #                                           capturePunctuation=True, captureSymbols=True)
            outToks = utilsString.nltkTokenizer(outLn)
            # add to the token freq dict
            for tok in outToks:
                if tok not in freqTokDict:
                    freqTokDict[tok] = 0
                freqTokDict[tok] += 1
            # next line
            outLn = outFile.readline()
    return freqTokDict


def makeSPfreqDict(pathToEn, pathToFr):
    spFreq = {}
    with open(pathToEn) as enFile:
        with open(pathToFr) as frFile:
            enLn = enFile.readline()
            frLn = frFile.readline()
            while enLn:
                enLn = enLn.replace(u"\n", u"")
                frLn = frLn.replace(u"\n", u"")
                sentKey = u"{0}***---***{1}".format(enLn, frLn)
                # put into dict
                if sentKey not in spFreq:
                    spFreq[sentKey] = 0
                spFreq[sentKey] += 1
                # next line
                enLn = enFile.readline()
                frLn = frFile.readline()
    return spFreq


def transformStringToGizaFormat(string, tokDict, lang, pathToFile):
    # get the language in the right format
    lang = getLang(lang, pathToFile)
    # tokenize
    # tokList = utilsString.naiveRegexTokenizer(string, language=lang,
    #                                           capturePunctuation=True, captureSymbols=True)
    tokList = utilsString.nltkTokenizer(string)
    # remake a string using the token ids instead of the actual tokens
    idString = []
    for tok in tokList:
        try:
            idString.append(tokDict[tok])
        except KeyError:
            try:
                idString.append(tokDict[u"{0}'".format(tok)])
            except KeyError:
                try:
                    idString.append(tokDict[u"'{0}".format(tok)])
                except KeyError:
                    try:
                        idString.append(tokDict[tok.replace(u"'", u"")])
                    except KeyError:
                        print(tok, 11111, repr(tok), type(tok))
    idString = [str(id) for id in idString]
    return u" ".join(idString)


def appendToDumpInGizaFormat(pathToEnFile, pathToFrFile, outPutPath, tokEnDict, tokFrDict, spFreqDict):
    with open(pathToEnFile) as enFile:
        with open(pathToFrFile) as frFile:
            enLn = enFile.readline()
            frLn = frFile.readline()
            while enLn:
                enLn = enLn.replace(u"\n", u"")
                frLn = frLn.replace(u"\n", u"")
                # get the freq of the sp
                spFreq = spFreqDict[u"{0}***---***{1}".format(enLn, frLn)]
                # get the sp in the form os id codes
                enIdString = transformStringToGizaFormat(enLn, tokEnDict, u"en", pathToEnFile)
                frIdString = transformStringToGizaFormat(frLn, tokFrDict, u"fr", pathToFrFile)
                # dump
                stringLine = u"{0}\n{1}\n{2}".format(spFreq, enIdString, frIdString)
                utilsOs.appendLineToFile(stringLine, outPutPath, addNewLine=True)
                # next line
                enLn = enFile.readline()
                frLn = frFile.readline()


def reformatFilesToGiza(pathToEnFile, pathToFrFile, overwrite=True):
    """
    make 2 vocabulary files (occurrence dict) in the format needed by giza++ or mgiza++
    then reformats the corpus into a the format needed by giza++ or mgiza++
    :param pathToEnFile: path to the english sentences file
    :param pathToFrFile: path to the french sentences file
    :return: None
    """
    # prepare the output paths
    outputEnPath = prepareOutPutFile(pathToEnFile, fileName=u"sourceEn.vcb")
    outputFrPath = prepareOutPutFile(pathToFrFile, fileName=u"targetFr.vcb")
    outputPathGizaFormatCorpus = prepareOutPutFile(pathToEnFile, fileName=u"sentenceFile.giza")
    outputEnDictPath = prepareOutPutFile(pathToEnFile, fileName=u"en.json")
    outputFrDictPath = prepareOutPutFile(pathToEnFile, fileName=u"fr.json")
    outputSpDictPath = prepareOutPutFile(pathToEnFile, fileName=u"sp.json")
    # if there is not a file there yet, open the corpus Files, count the frequency of each token
    if overwrite is True or os.path.isfile(outputEnDictPath) is False:
        enTokFreqDict = makeFreqDict(pathToEnFile, lang=u"en")
        frTokFreqDict = makeFreqDict(pathToFrFile, lang=u"fr")
        # open the corpus files count the frequency of the sentence pairs
        spFreqDict = makeSPfreqDict(pathToEnFile, pathToFrFile)
        # dump dicts
        utilsOs.dumpDictToJsonFile(enTokFreqDict, outputEnDictPath, overwrite)
        utilsOs.dumpDictToJsonFile(frTokFreqDict, outputFrDictPath, overwrite)
        utilsOs.dumpDictToJsonFile(spFreqDict, outputSpDictPath, overwrite)
    # if the file already exists or if overwrite is false
    else:
        enTokFreqDict = utilsOs.openJsonFileAsDict(outputEnDictPath)
        frTokFreqDict = utilsOs.openJsonFileAsDict(outputFrDictPath)
        spFreqDict = utilsOs.openJsonFileAsDict(outputSpDictPath)
        # dump the empty tok voc file
    if overwrite is True:
        firstLine = u"1\tUNK\t0"
        utilsOs.createEmptyFile(outputEnPath, headerLine=firstLine)
        utilsOs.createEmptyFile(outputFrPath, headerLine=firstLine)
        utilsOs.createEmptyFile(outputPathGizaFormatCorpus)
    # sort the dict by freq
    orderedKeysValuesEn = sorted(enTokFreqDict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    orderedKeysValuesFr = sorted(frTokFreqDict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    # dump the dict in the tok voc file
    for indKv, kv in enumerate(orderedKeysValuesEn):
        stringLine = u"{0}\t{1}\t{2}".format(indKv+2, kv[0], kv[1])
        utilsOs.appendLineToFile(stringLine, outputEnPath, addNewLine=True)
    for indKv, kv in enumerate(orderedKeysValuesFr):
        stringLine = u"{0}\t{1}\t{2}".format(indKv+2, kv[0], kv[1])
        utilsOs.appendLineToFile(stringLine, outputFrPath, addNewLine=True)
    # transform and dump the corpus into the GIZA format
    appendToDumpInGizaFormat(pathToEnFile, pathToFrFile, outputPathGizaFormatCorpus,
                             enTokFreqDict, frTokFreqDict, spFreqDict)


###############################################################################
if __name__ == "__main__":
    # gizafy the 14M corpus
    pathToEnFile = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/train_14M_en"
    pathToFrFile = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/train_14M_fr"
    reformatFilesToGiza(pathToEnFile, pathToFrFile)
