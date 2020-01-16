#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys, os
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs, utilsString
import subprocess, re, json


# MGIZA++ #####################################################

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


def reformatFilesPreGiza(pathToEnFile, pathToFrFile, overwrite=True):
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
    return outputEnPath, outputFrPath, outputPathGizaFormatCorpus, outputEnDictPath, outputFrDictPath, outputSpDictPath


def joinIntoPharaohFormat(mgizaBaseFilePath):
    outputPharaohFilePath = u"{0}.pharaoh".format(mgizaBaseFilePath)
    outputTokFilePath = u"{0}_tok".format(mgizaBaseFilePath)
    # erase previous existing
    with open(outputPharaohFilePath, 'w') as tokAlignoutFile:
        tokAlignoutFile.write('')
    with open(outputTokFilePath, 'w') as tokAlignoutFile:
        tokAlignoutFile.write('')
    allDataDict = {}
    # open the output of mgiza (different format)
    for nb in range(99):
        if len(str(nb)) == 1:
            outFilePath = '{0}.A3.final.part00{1}'.format(mgizaBaseFilePath, nb)
        else:
            outFilePath = '{0}.A3.final.part0{1}'.format(mgizaBaseFilePath, nb)
        try:
            with open(outFilePath) as outDiffFormFile:
                ln0 = outDiffFormFile.readline()
                while ln0:
                    if ln0[0] == '#':
                        # read lines
                        ln1 = outDiffFormFile.readline()
                        ln2 = outDiffFormFile.readline()
                        # get data
                        sentInd = ln0.split('# Sentence pair (')[1].split(')')[0]
                        frSent = ln1.replace(' \n', '').replace('\n', '')
                        numRanges = re.findall(r' \(\{.*?\}\) ', ln2)
                        # get the nbs
                        fromEnToFrInd = [i.replace(' ({ ', '').replace(' }) ', '').replace('}) ', '') for i in
                                         numRanges]
                        fromEnToFrInd = [i.split(' ') for i in fromEnToFrInd]
                        fromEnToFrInd = [i if i != [''] else ['0'] for i in fromEnToFrInd]
                        #  get the english sentence
                        enSent = ln2
                        for nbRang in numRanges:
                            enSent = enSent.replace(nbRang, ' ')
                        enSent = enSent.replace(' \n', '').replace('\n', '').replace('NULL ', '')
                        # prepare to save to dict output en sent [tab] fr sent
                        sentLn = '{0}\t{1}\n'.format(enSent, frSent)
                        # prepare to save to dict output align tokens
                        alignLn = ''
                        for iEn, frIndexes in enumerate(fromEnToFrInd):
                            for iFr in frIndexes:
                                alignLn = '{0}{1}-{2} '.format(alignLn, iEn, iFr)
                        alignLn = '{0}\n'.format(alignLn[:-1])
                        # save to dict
                        allDataDict[int(sentInd)] = [alignLn, sentLn]
                    # next
                    ln0 = outDiffFormFile.readline()
                    # break when gets to end
                    if ln0 in ['', '\n']:
                        break
        except FileNotFoundError:
            break
    # prepare files for output
    with open(outputPharaohFilePath, 'a') as tokAlignoutFile:
        with open(outputTokFilePath, 'a') as tokFile:
            # browse dict and append to file
            for nb in range(len(allDataDict) + 118):
                try:
                    alignLn, sentLn = allDataDict[nb]
                    tokAlignoutFile.write(alignLn)
                    tokFile.write(sentLn)
                except KeyError:
                    pass
    return outputPharaohFilePath, outputTokFilePath


def applyMgiza(mgizaMasterEnvPath, pathToEnFile, pathToFrFile, overwrite=True):
    """
    Use Mgiza++ on the bilingual files
    :param pathToEnFile:
    :param pathToFrFile:
    :param overwrite:
    :return:
    """
    # make sure the mgiza environment folder is right
    mgizaSplit = mgizaMasterEnvPath[:-1] if mgizaMasterEnvPath[-1] == u"/" else mgizaMasterEnvPath
    mgizaMasterEnvPath = u"{0}/".format(mgizaMasterEnvPath) if mgizaMasterEnvPath[-1] != u"/" else mgizaMasterEnvPath
    mgizaSplit = mgizaSplit.split(u"/")
    if mgizaSplit[-1] == u"mgizapp":
        pass
    elif mgizaSplit[-1] == u"mgiza-master":
        mgizaMasterEnvPath = u"{0}mgizapp/".format(mgizaMasterEnvPath)
    # make paths to specific Mgiza tool scripts to use in terminal
    mgizaCom = u"{0}/bin/mgiza".format(mgizaMasterEnvPath)
    mkclsCom = u"{0}/bin/mkcls".format(mgizaMasterEnvPath)
    snt2coocCom = u"{0}bin/snt2cooc".format(mgizaMasterEnvPath)
    # make the vocabulary, sentence and frequency files
    vcbEnPath, vcbFrPath, sentPath, enFreqPath, frFreqPath, spFreqPath = reformatFilesPreGiza(pathToEnFile,
                                                                                                    pathToFrFile,
                                                                                                    overwrite)
    generalPath = u"{0}MGIZA/".format(sentPath.replace(u"sentenceFile.giza", ""))
    utilsOs.createEmptyFolder(generalPath)
    # make classes for hmm and ibm4 models
    classesEnPath = u"{0}{1}.classes".format(generalPath, vcbEnPath.split(u"/")[-1])
    classesFrPath = u"{0}{1}.classes".format(generalPath, vcbFrPath.split(u"/")[-1])
    subprocess.run([mkclsCom, u"-p{0}".format(vcbEnPath), u"-V{0}".format(classesEnPath)])
    subprocess.run([mkclsCom, u"-p{0}".format(vcbFrPath), u"-V{0}".format(classesFrPath)])
    # make the sentence coocurrence files
    coocurrencePath = u"{0}.cooc".format(generalPath, sentPath.split(u"/")[-1])
    subprocess.run([snt2coocCom, coocurrencePath, vcbEnPath, vcbEnPath, sentPath])
    # run mgiza and output the files
    outputMgiza = u"{0}mgiza_output/".format(generalPath)
    utilsOs.createEmptyFolder(outputMgiza)
    outputMgiza = u"{0}{1}_{2}".format(outputMgiza, vcbEnPath.split(u"/")[-1].split(u".")[0],
                                       vcbFrPath.split(u"/")[-1].split(u".")[0])
    subprocess.run([mgizaCom, u"-s", vcbEnPath, u"-t", vcbFrPath, u"-c", sentPath, u"-CoocurrenceFile", coocurrencePath, u"-o", outputMgiza])
    # u"-m1", "-1", u"-m2", u"1", u"-m3", u"-1", u"-m4", u"-1", u"-m5", u"-1", u"-m6", u"-1", u"-mh", u"-1"]) #############################################
    pharaohFilePath, tokFilePath = joinIntoPharaohFormat(outputMgiza)
    return pharaohFilePath, tokFilePath


# TMOP #################################################################################

def getConfigTemplate():
    d = {"options": {"input file": "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/test_en",
        "align file": "test.pharaoh",
        "token file": "test_tok",
        "output folder": "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/TMOP/output/test",
        "source language": "en",
        "target language": "fr",
        "normalize scores":	"true",
        "emit scores": "true",
        "no out files": "false",
        "max decision":	-1},
        "policies": [
            ["OneNo", "on"],
            ["TwentyNo", "on"],
            ["MajorityVoting", "on"]],
        "filters": [
        ["SampleFilter", "on"],
        ["LengthStats", "on"],
        ["LengthRatio",	"on"],
        ["ReverseLengthRatio", "on"],
        ["WordRatio", "on"],
        ["ReverseWordRatio", "on"],
        ["WordLength", "on"],
        ["TagFinder", "on"],
        ["RepeatedChars", "on"],
        ["RepeatedWords", "on"],
        ["Lang_Identifier",	"on"],
        ["AlignedProportion", "on"],
        ["BigramAlignedProportion", "on"],
        ["NumberOfUnalignedSequences", "on"],
        ["LongestAlignedSequence", "on"],
        ["LongestUnalignedSequence", "on"],
        ["AlignedSequenceLength", "on"],
        ["UnalignedSequenceLength",	"on"],
        ["FirstUnalignedWord", "on"],
        ["LastUnalignedWord", "on"],
        ["WE_Average", "on"],
        ["WE_Median", "on"],
        ["WE_BestAlignScore", "on"],
        ["WE_ScoreOtherAlignment", "on"],
        ["WE_ScoreAlign_BestForRest", "on"]]}
    return d


def launchTmop(inputFilePath, pharaohFilePath, tokFilePath, outputFolderPath, **kwargs):
    utilsOs.createEmptyFolder(outputFolderPath)
    # get and modif the config file
    configDict = getConfigTemplate()
    configDict["options"]["input file"] = inputFilePath
    configDict["options"]["align file"] = pharaohFilePath
    configDict["options"]["token file"] = tokFilePath
    configDict["options"]["output folder"] = outputFolderPath
    for k, v in kwargs:
        configDict["options"][k] = v
    # dump the config.json file
    tmopFolder = "/data/rali5/Tmp/alfonsda/workRali/004tradBureau/TMOP-master"
    utilsOs.dumpDictToJsonFile(configDict, "{0}/config.json".format(tmopFolder), overwrite=True)
    # launch tmop ###### ERROR launch manually
    # sys.path.append(tmopFolder)
    # subprocess.run(["python", "{0}/main.py".format(tmopFolder)])
    # # cd ~/Documents/workRALI/004tradBureau/TMOP-master/ ou # cd /data/rali5/Tmp/alfonsda/workRali/004tradBureau/TMOP-master/
    # # python main.py

###############################################################################
if __name__ == "__main__":
    mgizaMaster = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/MGIZA++/mgiza-master/"
    # gizafy a sample
    pathToEnFile = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/018gizMtopSample/sample_en"
    pathToFrFile = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/018gizMtopSample/sample_fr"
    outputFolderPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/018gizMtopSample/TMOP_output"

    # gizafy the 14M corpus
    # pathToEnFile = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/train_14M_en"
    # pathToFrFile = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/009ShivsTrainSubset/train/train_14M_fr"
    # outputFolderPath = u"/data/rali5/Tmp/alfonsda/workRali/004tradBureau/018gizMtopSample/TMOP_output_14M"

    pharaohFilePath, tokFilePath = applyMgiza(mgizaMaster, pathToEnFile, pathToFrFile)
    launchTmop(pathToEnFile, pharaohFilePath, tokFilePath, outputFolderPath)
