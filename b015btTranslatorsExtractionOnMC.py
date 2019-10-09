#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(u'../utils')
sys.path.append(u'./utils')
import utilsOs
import b000path
from b003heuristics import *
import xml.etree.ElementTree as ET


def getTmxFlaggedData(tmxFilePathList):
    """
    Returns the data from the tmx files
    :param tmxFilePathList:
    :return:
    """
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


def getTxtFlaggedData(txtFilePathList, onlyOne=False):
    """
    Returns the data from the txt metadata files
    :param tmxFilePathList:
    :return:
    """
    if onlyOne is not False and len(txtFilePathList) != 1:
        yield None
    else:
        for txtPath in txtFilePathList:
            with open(u'{0}'.format(txtPath)) as metaFile:
                # get the meta data
                metaLns = metaFile.readlines()
                for metaLn in metaLns[1:]:
                    metaData = metaLn.replace(u'\n', u'').split(u'\t')
                    origDocName, flaggedAs, timestamp, flaggedAtInd = metaData
                    # get the index of flagged SP
                    flaggedAtInd = int(flaggedAtInd)
                    yield origDocName, flaggedAs, timestamp, flaggedAtInd


def getInfoFromArchiv1File(archive1Path):
    archiveList = archive1Path.split(u'/')
    archive1Files = utilsOs.getContentOfFolder(u'/'.join(archiveList[:-1]))
    # if there is no folder with that name
    if archive1Files is None:
        return None
    if archiveList[-1] not in archive1Files:
        # if the file is not in the folder, return None
        return None
    try:
        with open(u'{0}.en'.format(archive1Path)) as enFile:
            with open(u'{0}.fr'.format(archive1Path)) as frFile:
                enLns = [enLn.replace(u'\n', u'') for enLn in enFile.readlines()]
                frLns = [frLn.replace(u'\n', u'') for frLn in frFile.readlines()]
                # check if we find a match
                for indLn, (enLn, frLn) in enumerate(zip(enLns, frLns)):
                    if enLn == enSent and frLn == frSent:
                        return enLn, frLn, archive1Path, indLn
                # if we found nothing, return None
                return None
    # if there is no language file ('.tmx.en', '.tmx.fr' ) with that name, return None
    except FileNotFoundError:
        return None


docsPath = u'{0}DC-24/'.format(b000path.getBtOriginalDocsPath())
btExtractPath = u'/data/rali5/Tmp/alfonsda/workRali/004tradBureau/007corpusExtraction/BT1/'

for flag in utilsOs.getContentOfFolder(docsPath):
    flagPath = u'{0}{1}/'.format(docsPath, flag)
    for client in utilsOs.getContentOfFolder(flagPath):
        clientPath = u'{0}{1}/'.format(flagPath, client)
        thereAreSubclients = True
        for subClient in utilsOs.getContentOfFolder(clientPath):
            if thereAreSubclients:
                # if there is not really any sub client then ommit this part
                if subClient in [u'en-fr', 'fr-en']:
                    subClient = u''
                    clientPath = clientPath
                    thereAreSubclients = False
                else:
                    subClient = u'{0}/'.format(subClient)
                subClientPath = u'{0}{1}'.format(clientPath, subClient)
                for lang in utilsOs.getContentOfFolder(subClientPath):
                    langPath = u'{0}{1}/'.format(subClientPath, lang)
                    for command in utilsOs.getContentOfFolder(langPath):
                        commandPath = u'{0}{1}/'.format(langPath, command)
                        fileNames = utilsOs.getContentOfFolder(commandPath)

                        # get the path to the tmx file
                        tmxFileNames = [e for e in fileNames if u'.tmx' in e]
                        tmxFilePaths = [u'{0}{1}'.format(commandPath, fn) for fn in tmxFileNames]
                        # get the metadata from the tmxFile
                        for tmxData, tmxPath in zip(getTmxFlaggedData(tmxFilePaths), tmxFilePaths):
                            # if there is no flagging data in the tmx, pass
                            if tmxData is None:
                                pass
                            # get and dump the flagging data
                            else:
                                (flagType, index, enSent, frSent, segmentNb, flagDate) = tmxData
                                utilsOs.appendLineToFile(enSent, u'{0}problematic/extracted.en'.format(btExtractPath))
                                utilsOs.appendLineToFile(frSent, u'{0}problematic/extracted.fr'.format(btExtractPath))
                                utilsOs.appendLineToFile(u'{0}\t{1}'.format(commandPath, index),
                                                         u'{0}problematic/referenceDC24Corpus.tsv'.format(btExtractPath))
                                utilsOs.appendLineToFile(u'{0}\t{1}\t{2}'.format(flagType, segmentNb, flagDate),
                                                         u'{0}problematic/other.tsv'.format(btExtractPath))
                                # map the DC24 to the archive1 files
                                archive1Path = b000path.transformPathArchiv1To2And2To1(tmxPath)
                                # if there are multiple possibilities of files, it's returned as a list
                                if type(archive1Path) is list:
                                    if len(archive1Path) == 1:
                                        # open the files to find a matching SP
                                        dataArch1 = getInfoFromArchiv1File(archive1Path[0])
                                    else:
                                        for filePath in archive1Path:
                                            dataArch1 = getInfoFromArchiv1File(filePath)
                                            if dataArch1 is not None:
                                                break
                                elif archive1Path is None:
                                    dataArch1 = None
                                else:
                                    # open the files to find a matching SP
                                    dataArch1 = getInfoFromArchiv1File(archive1Path)
                                if dataArch1 is None:
                                    utilsOs.appendLineToFile(u'{0}\tNA'.format(archive1Path),
                                                             u'{0}problematic/reference.tsv'.format(btExtractPath))
                                else:
                                    enLn, frLn, archive1Path, indLn = dataArch1
                                    utilsOs.appendLineToFile(u'{0}\t{1}'.format(archive1Path, indLn),
                                                             u'{0}problematic/reference.tsv'.format(btExtractPath))

                        # # get the path to the metadata file
                        # txtFiles = [e for e in fileNames if u'flagging-details' in e]
                        # # get the metadata from the txtFile
                        # for txtData in getTxtFlaggedData([u'{0}{1}'.format(commandPath, tf) for tf in txtFiles]):
                        #     (origDocName, flaggedAs, timestamp, flaggedAtInd) = txtData





# count the time the algorithm takes to run
startTime = utilsOs.countTime()





# print the time the algorithm took to run
print(u'\nTIME IN SECONDS ::', utilsOs.countTime(startTime))

