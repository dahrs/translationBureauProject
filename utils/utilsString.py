#!/usr/bin/python
# -*- coding:utf-8 -*-

import re, codecs, nltk, itertools, time, datetime, random
from langdetect import detect
from nltk.metrics import distance
from nltk.tokenize import word_tokenize
from tqdm import tqdm
from functools import partial
from contextlib import closing
import numpy as np
import multiprocessing as mp
import utilsDataStruct
import utilsOs
from tkinter import Tk
from tkinter import TclError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from googletrans import Translator
import spacy


##################################################################################
# ENCODING
##################################################################################

def toUtf8(stringOrUnicode):
    '''
	Returns the argument in utf-8 encoding
	Unescape html entities???????
	'''
    typeArg = type(stringOrUnicode)
    try:
        if typeArg is str:
            return stringOrUnicode.decode(u'utf8')
        elif typeArg is unicode:
            return stringOrUnicode.encode(u'utf8').decode(u'utf8', u'replace')
    except AttributeError:
        return stringOrUnicode


def fromHexToDec(hexCode):
    '''
	transforms a unicode hexadecimal code given in string form
	into a decimal code as an integral
	'''
    if type(hexCode) is int:
        return hexCode
    # delete all possible unicode affixes given to the hex code
    hexCode = hexCode.lower().replace(u' ', u'')
    for affix in [u'u+', u'u', u'u-']:
        hexCode = hexCode.replace(affix, u'')
    return int(hexCode, 16)


def unicodeCodeScore(string, countSpaces=False, unicodeBlocksList=[(0, 128)]):
    '''
	Returns a normalized score of the proportion of
	characters between the integer-code block-frontiers 
	over all the characters of the word.
	(the element of the list can be a tuple or a list if 
	we want a start and an end frontier, or it can be a
	string or an integral if we want to add only one 
	specific code)
	e.g., 
		for an ascii frontier(U+0-U+128) == unicodeBlocksList=[(0, 128)] :
			'touche' = 1.0 
			'touché' = 0.833333			
			'ключ' = 0.0
		for an ascii frontier (U+0-U+128) + the french loan-character 'é' (U+00E9) == unicodeBlocksList=[(0, 128), [233] :
			'touche' = 1.0 
			'touché' = 1.0			
			'ключ' = 0.0
		for an cyrilic frontier (U+0400-U+04FF) == unicodeBlocksList=[[1024, 1279], ('0500', '052F'), 1280] :
			'touche' = 0.0 
			'touché' = 0.0
			'ключ' = 1.0
	https://en.wikipedia.org/wiki/List_of_Unicode_characters
	'''
    totalOfAcceptedChars = 0
    acceptedUnicodeCodes = set()
    # delete spaces if needed
    if countSpaces == False:
        string = string.replace(u' ', u'')
    # make a list of accepted unicode codes
    for frontierElement in unicodeBlocksList:
        # if the element is a lone code
        if type(frontierElement) is int or type(frontierElement) is str:
            # if the code is in hexadecimal, transform to decimal code and add it to the accepted set
            acceptedUnicodeCodes.add(fromHexToDec(frontierElement))
        # if the element is only one code
        elif len(frontierElement) == 1:
            # if the code is in hexadecimal, transform to decimal code and add it to the accepted set
            acceptedUnicodeCodes.add(fromHexToDec(frontierElement[0]))
        # if the element is 2 codes (start and end)
        elif len(frontierElement) == 2:
            # if the frontiers are in hexadecimal, transform to decimal code and union the set of all intervals between the start and end frontier
            acceptedUnicodeCodes = acceptedUnicodeCodes.union(
                set(range(fromHexToDec(frontierElement[0]), fromHexToDec(frontierElement[1]) + 1)))
    # if it's bigger than 2, it's not taken into account
    # verify if the characters of the strings are in the accepted set
    for char in string:
        if ord(char) in acceptedUnicodeCodes:
            totalOfAcceptedChars += 1
    return float(totalOfAcceptedChars) / float(len(string))


##################################################################################
# REGEX
##################################################################################


def removeStopwords(tokenList, language=u'english'):
    from nltk.corpus import stopwords
    # stopwords
    to_remove = set(stopwords.words("english") + ['', ' ', '&'])
    return list(filter(lambda tok: tok not in to_remove, tokenList))


def findAcronyms(string):
    '''
	Returns the acronyms found in the string.
	variant : 
	acronyms = re.compile(r'((?<![A-Z])(([A-Z][\.][&]?){2,}|([A-Z][&]?){2,5})(?![a-z])(?=\b)+)')
	'''
    # we make the regex of acronyms, all uppercase tokens and plain tokens
    acronyms = re.compile(
        r'((?<![A-Z])(([A-Z]([\.]|[&])?){2,4})(?![a-z])(?=(\b|\n))+)')  # 2-4 uppercase characters that might be separated by . or &
    upperTokens = re.compile(r'(\b([A-Z0-9&-][\.]?)+\b)')
    plainTokens = re.compile(r'(\b\w+\b)')
    # if the whole sent is all in caps then we discard it
    if len(re.findall(plainTokens, string)) != len(re.findall(upperTokens, string)) and len(
            re.findall(plainTokens, string)) >= 2:
        return re.findall(acronyms, string)
    return None


def detectNbChar(string):
    ''' detects if there is a char in the string that is a number '''
    pattern = re.compile(r'[0-9]')
    s = pattern.search(string)
    if s == None:
        return False
    return True


def detectUrlAndFolderPaths(string):
    """ given a string detects if there is an url or folder path
    in the string and returns in a list the parts of the string with the urls """
    urlAndFolderPaths = re.compile(r'((?!\s)((([A-Z]:|\/|(~|\.)\/|http:\/\/|https:\/\/|www\.)(.(?!\s))+.)|(((?!\s)[a-z](\/|\\|\.)*)+\.([a-z]{2,4})(\/)*)))')
    allUrlsAndPaths = re.findall(urlAndFolderPaths, string)
    if len(allUrlsAndPaths) == 0:
        return False, []
    return True, allUrlsAndPaths


def extractNumbersFromString(string, digitByDigit=False):
    """ given a string, extract all the digit characters in the string in list form as integrals """
    if digitByDigit == False:
        nbPattern = re.compile(r'[0-9]+')
    else:
        nbPattern = re.compile(r'[0-9]')
    numbers = re.findall(nbPattern, string)
    return [int(nb) for nb in numbers]


def transformNbNameToNb(stringOrStringList):
    """ given a string or a string list, if we find a number name, we replace it with the number
	 (function to be perfected) """
    nbToNbName = {0.5: {u'half', u'demi', u'moitié', u'semi', u'mid', u'mi'},
                  0: {u'zero', u'zéro', u'null', u'none'},
                  1: {u'january', u'janvier', 'first', u'premier', u'première', u'1rst', u'1st', u'1er',
                      u'1ere', u'1ère', u'ist', u'ier'},
                  2: {u'two', u'deux', u'february', u'février', u'square', u'carré', u'second', u'seconde',
                      u'deuxième', u'ii', u'2nd', u'2nd', u'2nde', u'2eme', u'2ème', u'iind', u'iinde', u'iième'},
                  3: {u'three', u'trois', u'tri', u'march', u'mars', u'third', u'tiers', u'troisième', u'cube',
                      u'1pm', u'11pm', u'iii', u'3rd', u'3eme', u'3ieme', u'3ième', u'3ème', u'iiird', u'iiieme',
                      u'iième'},
                  4: {u'four', u'quatre', u'fourty', u'quarante', u'april', u'avril', u'fourth', u'quart',
                      u'quatrième', u'iiii', u'4th', u'4eme', u'4ieme', u'4ième', u'4ème', u'ivth', u'iveme',
                      u'ivème', u'ivième'},
                  5: {u'five', u'cinq', u'fifty', u'cinquante', u'mai', u'fifth',
                      u'cinquième', u'5th', u'5eme', u'5ieme', u'5ième', u'5ème', u'vth', u'veme', u'vème'},
                  6: {u'six', u'sixty', u'soixante', u'sixtieth', u'sixième', u'june', u'juin', u'6th', u'6eme',
                      u'6ieme', u'6ième', u'6ème', u'vith', u'vieme', u'vième'},
                  7: {u'seven', u'sept', u'seventy', u'septante', u'seventh', u'septième', u'july', u'juillet', u'vii',
                      u'7th', u'7eme', u'7ieme', u'7ième', u'7ème', u'viith', u'viieme', u'viième'},
                  8: {u'eight', u'huit', u'eighty', u'octante', u'eighth', u'huitième', u'august', u'aout', u'août',
                      u'viii', u'8th', u'8eme', u'8ieme', u'8ième', u'8ème', u'viiith', u'viiieme', u'viiième'},
                  9: {u'nine', u'neuf', u'ninety', u'nonante', u'ninth', u'neuvième', u'september', u'septembre',
                      u'9th', u'9eme', u'9ieme', u'9ième', u'9ème', u'ixth', u'ixeme', u'ixème', u'ixième'},
                  10: {u'ten', u'dix', u'october', u'octobre', u'tenth', u'dixième', u'10th', u'10eme', u'10ieme',
                       u'10ième', u'10ème', u'xth', u'xeme', u'xème'},
                  11: {u'eleven', u'onze', u'november', u'novembre', u'11th', u'11eme', u'11ieme', u'11ième',
                       u'11ème', u'xith', u'xieme', u'xième', u'xième'},
                  12: {u'twelve', u'douze', u'december', u'decembre', u'décembre', u'midday', u'noon', u'midi', u'dozen',
                       u'douzaine', u'xii', u'12th', u'12eme', u'12ieme', u'12ième', u'12ème', u'xiith', u'xiieme',
                       u'xiième'},
                  13: {u'thirteen', u'treize', u'1pm', u'xiii', u'13th', u'13eme', u'13ieme', u'13ième', u'13ème',
                       u'xiiith', u'xiiieme', u'xiiième'},
                  14: {u'fourteen', u'quatorze', u'2pm', u'xiv', u'14th', u'14eme', u'14ieme', u'14ième', u'14ème',
                       u'xivth', u'xiveme', u'xivème', u'xivième'},
                  15: {u'fifteen', u'quinze', u'3pm', u'15th', u'15eme', u'15ieme', u'15ième', u'15ème',
                       u'xvth', u'xveme', u'xvème'},
                  16: {u'sixteen', u'seize', u'4pm', u'xvi', u'16th', u'16eme', u'16ieme', u'16ième', u'16ème',
                       u'xvith', u'xvieme', u'xvième'},
                  17: {u'seventeen', u'5pm', u'xvii', u'17th', u'17eme', u'17ieme', u'17ième', u'17ème', u'xviith',
                       u'xviieme', u'xviième'},
                  18: {u'eighteen', u'6pm', u'xviii', u'18th', u'18eme', u'18ieme', u'18ième', u'18ème', u'xviiith',
                       u'xviiieme', u'xviiième'},
                  19: {u'nineteen', u'7pm', u'xix', u'19th', u'19eme', u'19ieme', u'19ième', u'19ème', u'xixth',
                       u'xixeme', u'xixème', u'xixième'},
                  20: {u'twenty', u'vingt', u'8pm', u'xx', u'20th', u'20eme', u'20ieme', u'20ième', u'20ème', u'20th',
                       u'xxeme', u'xxème'},
                  21: {u'9pm', u'xxi', u'21th', u'21eme', u'21ieme', u'21ième', u'21ème', u'xxith', u'xxieme',
                       u'xxième'},
                  22: {u'10pm', u'22nd', u'22eme', u'22ieme', u'22ième', u'22ème'},
                  23: {u'11pm', u'23rd', u'23eme', u'23ieme', u'23ième', u'22ème'},
                  24: {u'midnight', u'minuit', u'24th', u'24eme', u'24ieme', u'24ième', u'24ème'},
                  25: {u'25th', u'25eme', u'25ieme', u'25ième', u'25ème'},
                  26: {u'26th', u'26eme', u'26ieme', u'26ième', u'26ème'},
                  27: {u'27th', u'27eme', u'27ieme', u'27ième', u'27ème'},
                  28: {u'28th', u'28eme', u'28ieme', u'28ième', u'28ème'},
                  29: {u'29th', u'29eme', u'29ieme', u'29ième', u'29ème'},
                  30: {u'thirty', u'trente', u'30th', u'30eme', u'30ieme', u'30ième', u'30ème'},
                  31: {u'31st', u'31rst', u'31eme', u'31ieme', u'31ième', u'31ème'},
                  40: {u'forty', u'quarante'}, 50: {u'fifty', u'cinquante'},
                  60: {u'sixty', u'soixante'}, 70: {u'seventy'}, 80: {u'eighty'}, 90: {u'ninety'},
                  100: {u'hundred', u'cent'}, 1000: {u'thousand', u'mille', u'mil'},
                  1000000: {u'million', u'millions'}, 1000000000: {u'billion', u'milliard', u'billions', u'milliards'}
                  }
    # (eliminated because of ambiguity mismatches) u'uni', u'mono', u'bi', u'score', u'one', u'un', u'may',
    #                                              u'i', u'v', u'x', u'iv', u'vi', u'xv', u'ix', u'xi',
    # get a set containing all the number names
    def fromDict(aDict):
        for v in aDict.values():
            for elem in v:
                yield elem
    allNbNames = set(fromDict(nbToNbName))
    # if the stringOrStringList arg is a string
    if type(stringOrStringList) is str:
        stringOrStringList = stringOrStringList.lower()
        for intNb, nameSet in nbToNbName.items():
            for name in nameSet:
                stringOrStringList = ((stringOrStringList.replace(u'{0} '.format(name), u'{0} '.format(intNb))).replace(
                    u' {0}'.format(name), u' {0}'.format(intNb))).replace(name, str(intNb))
    # if the stringOrStringList arg is a list of strings
    elif type(stringOrStringList) is list:
        # verify if there is a nb name among the tokens
        intersectNames = set(stringOrStringList).intersection(allNbNames)
        if len(intersectNames) != 0:
            for index, token in enumerate(stringOrStringList):
                # if the token corresponds to a number, we replace it
                if token in intersectNames:
                    for nb, nbNames in nbToNbName.items():
                        # replace the nb name with the number
                        if token in nbNames:
                            stringOrStringList[index] = str(nb)
    return stringOrStringList


def makeAbbreviations(token, unusualOnly=False):
    ''' given a string token, it makes a list of non-acronymic abbreviations of the following kinds:
	credit -> cr		science -> sci		dept -> dept
	monsieur -> mr		madame -> mme		mademoiselle -> mlle		mistress -> miss'''
    if unusualOnly != False:
        if len(token) == 5:
            abbrList = [token[:3]]
        elif len(token) > 6:
            abbrList = [token[:n] for n in range(3, int(len(token) / 2.0) + 2)]
        else:
            abbrList = []
    else:
        if len(token) == 5:
            abbrList = [token[:n] for n in range(1, 4)]
            abbrList += [u'{0}{1}'.format(token[0], token[-1]), u'{0}{1}'.format(token[0], token[-2:])]
        elif len(token) > 4 and len(token) > 6:
            abbrList = [token[:n] for n in range(1, 5)]
            abbrList += [u'{0}{1}'.format(token[0], token[-1]), u'{0}{1}'.format(token[0], token[-2:]),
                         u'{0}{1}'.format(token[0], token[-3:]), u'{0}{1}'.format(token[:2], token[-2:])]
        else:
            abbrList = [
                token.replace(u'a', u'').replace(u'e', u'').replace(u'i', u'').replace(u'o', u'').replace(u'u', u'')]
    return abbrList


def indicator2in1(string):
    '''
	detects if a string has '/', '\', ',', ':', ';', ' - ' and '&' between words
	if it does it returns true, otherwise it returns false
	'''
    # we make the regex of 2 in 1 substrings
    twoInOneSubstring = re.compile(
        r'([\w]{2,}([\s|\t]?)&([\s|\t]?)[\w]{2,})|([\w]+([\s|\t]?)(\\|\/|,|:|;)([\s|\t]?)[\w]+)|([\w]+[\s]+-[\s]*[\w]+)|([\w]+-[\s]+[\w]+)')
    # if we find at least one substring indicating a 2 in 1, return true
    if len(re.findall(twoInOneSubstring, string)) != 0:
        return True
    return False


def indicator3SameLetters(string):
    '''
	detects if the string contains a substring composed ot the same 3 characters or more (type of characters limited)
	'''
    # we make the regex of 3 same letters
    threeCharRepetition = re.compile(
        r'(a){3,}|(b){3,}|(c){3,}|(d){3,}|(e){3,}|(f){3,}|(g){3,}|(h){3,}|(i){3,}|(j){3,}|(k){3,}|(l){3,}|(m){3,}|(n){3,}|(o){3,}|(p){3,}|(q){3,}|(r){3,}|(s){3,}|(t){3,}|(u){3,}|(v){3,}|(w){3,}|(x){3,}|(y){3,}|(z){3,}|(,){3,}|(\.){3,}|(:){3,}|(;){3,}|(\?){3,}|(!){3,}|(\'){3,}|(\"){3,}|(-){3,}|(\+){3,}|(\*){3,}|(\/){3,}|(\\){3,}|(\$){3,}|(%){3,}|(&){3,}|(@){3,}|(#){3,}|(<){3,}|(>){3,}|(\|){3,}')
    # if we find at least one substring indicating a 2 in 1, return true
    if len(re.findall(threeCharRepetition, string.lower())) != 0:
        return True
    return False


def isItAlphaNumeric(char):
    """ given a character, returns True if it's alphanumeric ( ASCII alone: [a-zA-Z0-1] ), False otherwise """
    alphaNumericDecimalCodes = set([32] + list(range(48, 58)) + list(range(65, 91)) + list(range(97, 123)))
    if ord(char) not in alphaNumericDecimalCodes:
        return False
    return True


def isItGibberish(string, gibberishTreshold=0.49, exoticCharSensitive=False):
    '''
	Detect if the string is composed of mostly gibberish (non-alphanumerical symbols)
	and repetition of the same letter.
	it returns true if the gibberish treshold is surpassed, false otherwise
	if exoticCharSensitive is False, it will treat non-latin-based characters as gibberish too
	'''
    nonGibberishCharsList = []
    latinExtChars = set(list(range(48, 58)) + list(range(65, 91)) + list(range(97, 123)) + list(range(192, 215)) + list(
        range(216, 247)) + list(range(248, 384)) + list(range(536, 540)))
    symbolsChars = set(
        list(range(0, 48)) + list(range(58, 65)) + list(range(91, 97)) + list(range(123, 192)) + [215, 247, 884, 885,
                                                                                                  894, 903])
    # detect if there is a repetition of the same 3 letters
    if indicator3SameLetters(string) == True:
        return True
    string = string.replace(u' ', u'')
    # treat non-latin-based characters as gibberish too
    if exoticCharSensitive == False:
        # detect accepted characters, append non-acepted to list
        for char in string:
            if ord(char) in latinExtChars:
                nonGibberishCharsList.append(char)
    # treat non-latin-based characters as an alphabet
    else:
        # detect non accepted characters
        for char in string:
            if ord(char) not in symbolsChars:
                nonGibberishCharsList.append(char)
    # calculate the ratio of non-gibberish in the string
    nonGibberishRatio = float(len(nonGibberishCharsList)) / float(len(string))
    if (1.0 - nonGibberishRatio) >= gibberishTreshold:
        # for very small labels, symbols are not that uncommon, so we do not apply the same rigor
        if len(string) <= 4:
            if (1.0 - nonGibberishRatio) == 0.0:
                return True
            return False
        return True
    return False


def eliminateMultipleSpaces(string):
    """"""
    if type(string) is int or type(string) is float:
        return string
    # find all multiple spaces
    listSpaces = re.findall(r'[ ]{2,}', string)
    for spaceChars in listSpaces:
        string = string.replace(spaceChars, u'')
    return string


##################################################################################
# NON-REGEX INDICATOR OR EXTRACTOR
##################################################################################

def tokenEditDist(string1, string2):
    """"""
    if type(string1) is str:
        string1 = [t for t in string1.split(" ") if t != ""]
    if type(string2) is str:
        string2 = [t for t in string2.split(" ") if t != ""]
    commonTok, exclusiveTok = [], []
    # get all tokens in string1 not in string2
    string2Temp = list(string2)
    for tok1 in string1:
        if tok1 in string2Temp:
            commonTok.append(tok1)
            string2Temp.remove(tok1)
        else:
            exclusiveTok.append(tok1)
    # get all tokens in string2 not in string1
    commonTokTemp = list(commonTok)
    for tok2 in string2:
        if tok2 not in commonTokTemp:
            exclusiveTok.append(tok2)
        else:
            commonTokTemp.remove(tok2)
    return len(exclusiveTok), len(exclusiveTok)/(len(exclusiveTok)+len(commonTok))


def makeNgramList(string, ngramSize=2):
    """"""
    ngramList = []
    for indexString in range(0, len(string)-(ngramSize - 1)):
        stringNgram = string[indexString:indexString+ngramSize]
        ngramList.append(stringNgram)
    return ngramList


def makeNgramInterceptionList(string1, string2, ngramSize=2,returnNgramsLists=False):
    """"""
    interceptionList = []
    string1NgramList = makeNgramList(string1, ngramSize)
    string2NgramList = makeNgramList(string2, ngramSize)
    for string1Ngram in string1NgramList:
        for string2Ngram in string2NgramList:
            if string1Ngram == string2Ngram:
                interceptionList.append(string1Ngram)
                break
    if returnNgramsLists is False:
        return interceptionList
    else:
        return interceptionList, string1NgramList, string2NgramList



def fillCorrespondenceList(string1, string2, ngramSize=2):
    """"""
    correspondenceList = []
    for indexChar, char in enumerate(string1[:len(string1) - (ngramSize - 1)]):
        # if the string2 has not yet got to the end of the string
        if len(string2) - (ngramSize - 1) > indexChar:
            # get each ngram in the string1 and string2
            ngramString1 = char if ngramSize == 1 else string1[indexChar:indexChar + ngramSize]
            ngramString2 = string2[indexChar] if ngramSize == 1 else string2[indexChar:indexChar + ngramSize]
            # if there is a correspondence
            if ngramString1 == ngramString2:
                correspondenceList.append(1)
            else:
                correspondenceList.append(0)
        # if there is no possible correspondence because the string2 has no more ngrams
        else:
            correspondenceList.append(None)
    return correspondenceList


def isStringTruncated(string1, string2, caseSensitive=True):
    ''' detects if the string2 is a truncated version of the string1 and returns a boolean decision indicating
	if it is (True) or not (False) truncated as well as a normalized score indicating the degree of truncation (the higher the 
	score the more truncated the string2 is, compared to the string1) '''
    if caseSensitive != True:
        string1, string2 = string1.lower(), string2.lower()
    # the string1 must be the full version and the string 2 the "supposedly" truncated one, not the other way around
    if len(string1) < len(string2):
        return False, 0.0
    # special case for the very small words of lenght 2 or 3
    elif len(string1) in [2, 3]:
        correspondenceList = fillCorrespondenceList(string1, string2, ngramSize=1)
    # normal cases
    else:
        correspondenceList = fillCorrespondenceList(string1, string2, ngramSize=2)
    # case where there is no correspondence at all, which means the strings are not in a
    # truncation situation, they are just completely different strings from the start
    if 1 not in correspondenceList:
        return False, 0.0
    # case where everything corresponds, which means the strings are not truncated
    elif None not in correspondenceList:
        return False, 0.0
    # case where there is a non-correspondence instead of an truncation
    # (there is an element there, but it doesn't correspond)
    elif 0 in correspondenceList:
        return False, 0.0
    # analysis of the correspondence list
    for indexCorresp, correspScore in enumerate(correspondenceList):
        if correspScore == None:
            # if there was a non-correspondence in the middle of the word but there is a
            # correspondence further ahead, then it's not a truncation is a correction
            if 1 in correspondenceList[indexCorresp:]:
                return False, 0.0
    # analysis of the degree of truncation
    trueCorrespondence = [score for score in correspondenceList if score == 1]
    return True, float(len(trueCorrespondence)) / float(len(correspondenceList))


##################################################################################
# LANGUAGE
##################################################################################

def englishOrFrench(string):
    '''guesses the language of a string between english and french'''
    from langdetect.lang_detect_exception import LangDetectException
    # if the string is only made of numbers and non alphabetic characters we return 'unknown'
    if re.fullmatch(re.compile(r'([0-9]|-|\+|\!|\#|\$|%|&|\'|\*|\?|\.|\^|_|`|\||~|:|@)+'), string) != None:
        return u'unknown'
    # if more than 30% of the string characters is outside the ascii block and the french block, then it must be another language and we return 'unknown'
    if unicodeCodeScore(string, countSpaces=False, unicodeBlocksList=[[0, 255]]) < 0.7:
        return u'unknown'
    # if the string has a presence of unicode characters of french specific diacritics
    diacritics = [192, 194, [199, 203], 206, 207, 212, 140, 217, 219, 220, 159, 224, 226, [231, 235], 238, 239, 244,
                  156, 250, 251, 252, 255]
    if unicodeCodeScore(string, countSpaces=False, unicodeBlocksList=diacritics) > 0.0:
        return u'fr'
    # putting the string in lowercase improves the language detection functions
    string = string.lower()
    # use langdetect except if it returns something else than "en" or "fr", if the string is too short it's easy to mistake the string for another language
    try:
        lang = detect(string)
        if lang in [u'en', u'fr']:
            return lang
    # if there is an encoding or character induced error, we try the alternative language detection
    except LangDetectException:
        pass
    # alternative language detection
    # token detection
    unkTokendict = tokenDictMaker(string)
    # ngram char detection
    unkNgramDict = trigramDictMaker(string.replace(u'\n', u' ').replace(u'\r', u''))
    # if the obtained dict is empty, unable to detect (probably just noise)
    if len(unkTokendict) == 0 or len(unkNgramDict) == 0:
        return u'unknown'
    # token scores
    frenchTokScore = langDictComparison(unkTokendict, utilsOs.openJsonFileAsDict(u'./resources/tokDict/frTok.json'))
    englishTokScore = langDictComparison(unkTokendict, utilsOs.openJsonFileAsDict(u'./resources/tokDict/enTok.json'))
    # ngram scores
    frenchNgramScore = langDictComparison(unkNgramDict,
                                          utilsOs.openJsonFileAsDict(u'./resources/charDict/frChar3gram.json'))
    englishNgramScore = langDictComparison(unkNgramDict,
                                           utilsOs.openJsonFileAsDict(u'./resources/charDict/enChar3gram.json'))
    # the smaller the string (in tokens), the more we want to prioritize the token score instead of the ngram score
    if len(unkTokendict) < 5:
        ratioNgram = float(len(unkTokendict)) / 10.0
        frenchTokScore = frenchTokScore * (1.0 - ratioNgram)
        frenchNgramScore = frenchNgramScore * ratioNgram
        englishTokScore = englishTokScore * (1.0 - ratioNgram)
        englishNgramScore = englishNgramScore * ratioNgram
    # we compare the sum of the language scores
    if (frenchTokScore + frenchNgramScore) < (englishTokScore + englishNgramScore):
        return u'fr'
    return u'en'


def googleTranslateLangDetection(string):
    translator = Translator()
    return translator.detect(string)


##################################################################################
# TRANSFORM TO NLP UNITS (SENTENCE, TOKENS, NGRAM, POS, LEMMA, STEM, etc.)
##################################################################################

def sentSegmenterSpacy(inputPath, outputFolder=None, spacyNlpObj=None):
    if spacyNlpObj is None:
        nlp = spacy.load("fr")
    else:
        nlp = spacyNlpObj
    sentList = []
    with open(inputPath) as txtFile:
        for paragraph in txtFile.readlines():
            doc = nlp(paragraph)
            sentList += [(sent.text).replace("\n", "") for sent in doc.sents]
    if outputFolder is not None:
        fileName = inputPath.split("/")[-1]
        with open(u"{0}{1}".format(outputFolder, fileName), "w") as outFile:
            outFile.write("")
            for sent in [s for s in sentList if s not in ["\n", "\t", " ", ""]]:
                outFile.write("{0}\n".format(sent))
        with open(u"{0}{1}.reference".format(outputFolder, fileName), "w") as outFile:
            outFile.write(inputPath)
        return sentList, u"{0}{1}".format(outputFolder, fileName)
    return sentList


def sentSegmenterNltk(inputPath, outputFolder=None):
    sentList = []
    with open(inputPath) as txtFile:
        for paragraph in txtFile.readlines():
            doc = nltk.sent_tokenize(paragraph)
            sentList += [(sent.text).replace("\n", "") for sent in doc]
    if outputFolder is not None:
        fileName = inputPath.split("/")[-1]
        with open(u"{0}{1}".format(outputFolder, fileName), "w") as outFile:
            outFile.write("")
            for sent in [s for s in sentList if s not in ["\n", "\t", " ", ""]]:
                outFile.write("{0}\n".format(sent))
        with open(u"{0}{1}.reference".format(outputFolder, fileName), "w") as outFile:
            outFile.write(inputPath)
        return sentList, u"{0}{1}".format(outputFolder, fileName)
    return sentList


def copyOfString(string):
    return u'{0}*'.format(string)[:-1]


def words(string): return re.findall(r'\w+', string.lower().replace(u'\n',
                                                                    u' '))  # extracted from peter norvig spell post : https://norvig.com/spell-correct.html


def getTokenRegex(capturePunctuation=False, captureSymbols=False, language=None):
    '''
    returns a specific regex string in order to tokenize a string
    :param capturePunctuation: wether to capture punctuation or not => true, false, string or list of punct
    :param captureSymbols: wether to capture symbols or not => true, false, string or list of symbols
    :param language:
    :return: the right regex (string)
    '''
    infix, punctuation, symbols, punctAndSymb = r'', r'', r'', r''
    # gets some possible punctuation
    if capturePunctuation is True:
        punctuation = r'\。\.\?\!\:\;\¡\¿\(\)\[\]\{\}'
    # put all the given puntuation characters in a list, then in a regex string
    elif capturePunctuation is not False:
        # put all the punct in a list then transform it into a string
        punctList = [punct for punct in capturePunctuation]
        punctuation = r''.join(punctList) if len(punctList) > 0 else r''
    punctStr = r'\b[{0}]+|'.format(punctuation) if punctuation != r'' else r''
    # adds the apostrophe at the start of the word in english and at the end of the word in other languages
    if captureSymbols is not False:
        if language in ['english', 'en']:
            infix = r"[o]\'[\w]+|[\w]*[nsxz]\'(t)?|\'[mrsv][\w]*|"
        elif language in ['french', 'fr']:
            infix = r"[\w]*[cdnmjlstu]\'|"
        else:
            infix = r"[o]\'[\w]+|[\w]*[cdnmjlstu]\'(t)?|\'[mrsv][\w]*|"
    # list the symbols
    if captureSymbols is not False and captureSymbols is True:
        symbols = r'\-\+\#\$\%\&\'\*\^\_\`\|\~\:\@\<\>\/'
    elif captureSymbols is not False:
        # put all the symbols in a list then transform it into a string
        symbList = [symb for symb in captureSymbols if symb != u"'"]
        symbols = r''.join(symbList) if len(symbList) > 0 else r''
    symbStr = r'|[{0}]+'.format(symbols) if symbols != r'' else r''
    # list the isolated punctuation and symbols
    if punctuation != r'' or symbols != r'':
        optPuncSymb = u'|'.join([u'[\\{0}]+'.format(ps) for ps in u"{0}{1}".format(punctuation, symbols).replace(u'\\', u'')])
        punctAndSymb = r'|{0}'.format(optPuncSymb)
    return r"({0}{1}([\w\-\/]+\b{2}){3})".format(punctStr, infix, symbStr, punctAndSymb)


def naiveRegexTokenizer(string, caseSensitive=True, eliminateStopwords=False, language=u'english',
                        capturePunctuation=False, captureSymbols=False):
    """
	returns the token list using a very naive regex tokenizer
	does not return the punctuation symbols nor the newline
	if captureSymbols is a string or a list of strings then those strings will also be captured
	(ie, captureSymbols="'" , then r"(\b\w+(\b   |'   ))")
    :param string:
    :param caseSensitive:
    :param eliminateStopwords:
    :param language:
    :param capturePunctuation:
    :param captureSymbols:
    :return:
    """
    # make the regex
    regex = getTokenRegex(capturePunctuation, captureSymbols, language)
    # make list of tokens
    plainWords = re.compile(regex, re.UNICODE)
    tokens = re.findall(plainWords, string.replace(u'\r', u'').replace(u'\n', u' '))
    if len(tokens) == 0:
        return u''
    elif type(tokens[0]) is str:
        tokens = [tokTupl for tokTupl in tokens]
    else:
        tokens = [tokTupl[0] for tokTupl in tokens]
    # if we don't want to be case sensitive
    if caseSensitive != True:
        tokens = [tok.lower() for tok in tokens]
    # if we don't want the stopwords
    if eliminateStopwords != False:
        tokens = removeStopwords(tokens, language=language)
    return tokens


def nltkTokenizer(string, additionalSeparators=None):
    if additionalSeparators == None:
        return word_tokenize(string)

    def separate(listTok, sep):
        for index, tok in enumerate(list(listTok)):
            tokL = [to for to in tok.split(sep) if to != u'']
            newTokL = []
            for t in tokL:
                newTokL.append(t)
                newTokL.append(sep)
            listTok = listTok[:index] + newTokL[:-1] + listTok[index + 1:]
        return listTok

    # first tokenize as nltk would
    tokenizedString = word_tokenize(string)
    newTokenizedString = []
    # tokenize each token using the additional separators
    for token in word_tokenize(string):
        temp = copyOfString(token)
        additionalTokenization = [temp]
        # tokenize using the separators
        for separator in additionalSeparators:
            additionalTokenization = separate(additionalTokenization, separator)
        # add individual tokens if we got an additional tokenization
        if len(additionalTokenization) > 1:
            newTokenizedString = newTokenizedString + additionalTokenization
        else:
            newTokenizedString.append(token)
    return newTokenizedString


def spacyLoadModel(lang='fr'):
    ''' load the spacy model outside the tokenizing function, that way the
	model is charged once while the tokenizer can be launched multiple times '''
    if lang in [u'en', u'fr']:
        typeCore = u'web' if lang == u'en' else u'news'
    return spacy.load(u'{0}_core_{1}_sm'.format(lang, typeCore), disable=['parser', 'tagger', 'ner'])


def spacyTokenizer(string, spacyModel):
    return list([tok.text for tok in spacyModel(string)])


def ngrams(string, n=3):
    '''
	given a string, tokenizes and groups by token n-grams
	it returns a list of ngrams, each in string format 
	separated by a space
	'''
    ngramList = []
    tokens = naiveRegexTokenizer(string, caseSensitive=True, eliminateStopwords=False, language=u'english')
    # go through the list of tokens
    for startIndex in range(len(tokens) - (n - 1)):
        # prepare the string n-gram to add to the ngramlist (depending on n)
        for subN in range(n):
            if subN == 0:
                stringedNgram = u'{0}'.format(tokens[startIndex])
            else:
                stringedNgram += u' {0}'.format(tokens[startIndex + subN])
        # add to the ngram list
        ngramList.append(stringedNgram)
    return ngramList


def charNgramArray(string, n=3):
    ''' given a string, returns a list containing the character ngrams '''
    ngramList = []
    for i in range(len(string) - (n-1)):
        ngramList.append(string[i:i + n])
    return ngramList


def tokenizeAndExtractSpecificPos(string, listOfPosToReturn, caseSensitive=True, eliminateStopwords=False):
    '''
	using nltk pos tagging, tokenize a string and extract the
	tokens corresponding to the specified pos
	The pos labels are:	
		- cc coordinating conjunction
		- cd cardinal digit
		- dt determiner
		- in preposition/subordinating conjunction
		- j adjective
		- n noun
		- np proper noun
		- p pronoun
		- rb adverb
		- vb verb
	'''
    posDict = {u'cc': [u'CC'], u'cd': [u'CD'], u'dt': [u'DT', u'WDT'], u'in': [u'IN'], u'j': [u'JJ', u'JJR', u'JJS'],
               u'n': [u'NN', u'NNS'], u'np': [u'NNP', u'NNPS'], u'p': [u'PRP', u'PRP$', u'WP$'],
               u'rb': [u'RB', u'RBR', u'RBS', u'WRB'], u'vb': [u'MD', u'VB', u'VBD', u'VBG', u'VBN', u'VBZ']}
    listPos = []
    # tokenize
    tokens = nltk.word_tokenize(string)
    # we replace the general pos for the actual nltk pos
    for generalPos in listOfPosToReturn:
        listPos = listPos + posDict[generalPos]
    # pos tagging
    tokensPos = nltk.pos_tag(tokens)
    # reseting the tokens list
    tokens = []
    # selection of the pos specified tokens
    for tupleTokPos in tokensPos:
        # if they have the right pos
        if tupleTokPos[1] in listPos:
            tokens.append(tupleTokPos[0])
    # if we don't want to be case sensitive
    if caseSensitive != True:
        tokens = [tok.lower() for tok in tokens]
    # if we don't want the stopwords
    if eliminateStopwords != False:
        tokens = removeStopwords(tokens, language='english')
    return tokens


def naiveStemmer(string, caseSensitive=True, eliminateStopwords=False, language=u'english'):
    '''
	returns the stemmed token list using nltk
	where a stem is a word of a sentence converted to its non-changing portions
	possible stemmer argument options are 'snowball', 'lancaster', 'porter'
	'''
    from nltk.tokenize import word_tokenize
    from nltk.stem.snowball import SnowballStemmer as stemmer
    # tokenize
    tokens = word_tokenize(string)
    # if we don't want to be case sensitive
    if caseSensitive != True:
        tokens = [tok.lower() for tok in tokens]
    # if we don't want the stopwords
    if eliminateStopwords != False:
        tokens = removeStopwords(tokens, language=language)
    # get stems
    stems = [stemmer(language).stem(tok) for tok in tokens]
    return tokens


def naiveEnLemmatizer(string, caseSensitive=True, eliminateStopwords=False):
    '''
	returns the lemmatized token list using nltk
	where a lemma is a word of a sentence converted to its dictionnary standard form
	works only for english text
	'''
    from nltk.tokenize import word_tokenize
    from nltk import WordNetLemmatizer
    lemmatizer = WordNetLemmatizer()
    # tokenize
    tokens = word_tokenize(string)
    # if we don't want to be case sensitive
    if caseSensitive != True:
        tokens = [tok.lower() for tok in tokens]
    # if we don't want the stopwords
    if eliminateStopwords != False:
        tokens = removeStopwords(tokens, language=u'english')
    # get lemmas
    lemmas = [lemmatizer.lemmatize(tok) for tok in tokens]
    return tokens


##################################################################################
# SPELL CHECKING
##################################################################################

def getEditDistance(str1, str2):
    return distance.edit_distance(str1, str2)

def getNormalizedEditDist(str1, str2, lowerCase=True):
    """ returns a score corresponding to a naive normalizaton of
     the edit dist, the closer to 1, the more distant the 2 strings are"""
    if lowerCase:
        str1, str2 = str1.lower(), str2.lower()
    return getEditDistance(str1, str2)/max(len(str1), len(str2))


def wordProbability(word, wordCountDict, N=None):
    '''Probability of `word`.
	based on peter norvig spell post : https://norvig.com/spell-correct.html'''
    # if the word is not in the dict
    if word not in wordCountDict:
        return 0
    # if the word is present in the dict
    if N == None:
        N = sum(wordCountDict.values())
    return wordCountDict[word] / N


def correction(word, lang=u'en', returnProbabilityScore=False, wordCountDict=None):
    '''Most probable spelling correction for word.
	based on statistical token frequency from peter norvig spell post : 
	https://norvig.com/spell-correct.html
	'''
    if wordCountDict != None:
        wordCountDict = utilsOs.openJsonFileAsDict(
            u'/u/alfonsda/Documents/workRALI/utils/resources/tokDict/{0}TokReducedLessThan100Instances.json'.format(lang))
    cadidatesList = candidates(word, wordCountDict)
    maxValWord = (word, 0)
    # evaluate for all candidates wich is most probable
    for candidate in cadidatesList:
        val = wordProbability(candidate, wordCountDict)
        if val > maxValWord[1]:
            maxValWord = (candidate, val)
    # if both the candidate and score are needed
    if returnProbabilityScore != False:
        # return most probable word and its score
        return maxValWord
    # if only the candidate is needed
    else:
        # return most probable
        return maxValWord[0]


def getWiki1000MostCommonLexicon(lang=u'en'):
    pth = u'/u/alfonsda/Documents/workRALI/utils/resources/tokDict/{0}TokReducedLessThan1000Instances.json'.format(
        lang)
    orthDictOrSet = utilsOs.openJsonFileAsDict(pth)
    return set(orthDictOrSet.keys())


def detectBadSpelling(tokenList, orthDictOrSet=None, lang=u'en'):
    """ given a list of tokens it returns a list containing the word and a score:
     - 0 if the token is not in the orth dict
     - 1 if it's in the orth dict """
    output = []
    if orthDictOrSet is None:
        pth = u'/u/alfonsda/Documents/workRALI/utils/resources/tokDict/{0}TokReducedLessThan1000Instances.json'.format(
            lang)
        orthDictOrSet = utilsOs.openJsonFileAsDict(pth)
        orthDictOrSet = set(orthDictOrSet.keys())
    # get rid of numbers and symbols
    nbAndSymb = re.compile(r"""[\.,:;?!\(\)\[\]\{\}"'«»`´@#$%&*+\-=<>_\\/0-9]+""")
    for indexTok, tok in enumerate(tokenList):
        tokenList[indexTok] = nbAndSymb.sub('', tok)
    tokenList = [tok for tok in tokenList if tok != u'']
    # compare to the orth dict
    for tok in tokenList:
        # lowercase it before searching in the dict
        if tok.lower() in orthDictOrSet:
            output.append(tuple([tok, 1]))
        else:
            output.append(tuple([tok, 0]))
    return output



def correctionNgram(ngram, lang=u'en', ngramCountDict=None):
    '''Most probable spelling correction for ngram.
	based on statistical ngram frequency
		- 'hybrid' : using ngram frequency and if it doesn't find it, uses token frequency
	based on from peter norvig spell post : https://norvig.com/spell-correct.html
	'''
    if ngramCountDict != None:
        ngramCountDict = utilsOs.openJsonFileAsDict(u'./resources/tokDict/{0}Tok.json'.format(lang))
    cadidatesList = candidatesNgram(ngram, ngramCountDict)
    maxValNgram = (ngram, 0)
    # evaluate for all candidates wich is most probable
    for candidate in cadidatesList:
        val = wordProbability(candidate, ngramCountDict)
        if val > maxValNgram[1]:
            maxValNgram = (candidate, val)
    # return most probable
    return maxValNgram


def candidates(word, wordCountDict):
    '''Generate possible spelling corrections for word.
	based on peter norvig spell post : https://norvig.com/spell-correct.html'''
    return (known([word], wordCountDict) or known(edits1(word), wordCountDict) or known(edits2(word),
                                                                                        wordCountDict) or [word])


def candidatesNgram(ngram, ngramCountDict):
    '''Generate possible spelling corrections for word.
	based on peter norvig spell post : https://norvig.com/spell-correct.html'''
    return (known([ngram], ngramCountDict)
            or known(editsTrigram(ngram), ngramCountDict)
            or [ngram])


def known(words, wordCountDict):
    '''The subset of `words` that appear in the dictionary of wordCountDict.
	based on peter norvig spell post : https://norvig.com/spell-correct.html'''
    return set(w for w in words if w in wordCountDict)


def edits1(word, lang=u'fr'):
    '''All edits that are one edit away from `word`.
	extracted from peter norvig spell post : https://norvig.com/spell-correct.html'''
    letters = u'abcdefghijklmnopqrstuvwxyz'
    if lang == u'fr': letters += u'àâçéèêïîôùüû'
    # make all possible 1-distance changes
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def edits2(word):
    '''All edits that are two edits away from `word`.
	extracted from peter norvig spell post : https://norvig.com/spell-correct.html'''
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))


def edits3(word):
    '''All edits that are three edits away from `word`.
	based on peter norvig spell post : https://norvig.com/spell-correct.html'''
    return (e3 for e1 in edits1(word) for e3 in edits2(e1))


def edits4(word):
    '''All edits that are three edits away from `word`.
	based on peter norvig spell post : https://norvig.com/spell-correct.html'''
    return (e4 for e2 in edits2(word) for e4 in edits2(e2))


def getAllEditsOfToken(token):
    ''' Generate all spelling variations for token '''
    return edits1(token).union(edits2(token)).union(set([token]))


def editsTrigram(ngram):
    ''' given an ngram, tokenizes, applies the edits to each token,
	then returns the ngram '''
    with closing(mp.Pool(processes=4)) as pool:
        ngramTokens = naiveRegexTokenizer(ngram)
        token1Edits = pool.apply_async(getAllEditsOfToken, [ngramTokens[0]])
        # token1Edits = getAllEditsOfToken(ngramTokens[0])
        token2Edits = pool.apply_async(getAllEditsOfToken, [ngramTokens[1]])
        # token2Edits = getAllEditsOfToken(ngramTokens[1])
        token3Edits = pool.apply_async(getAllEditsOfToken, [ngramTokens[2]])
        # token3Edits = getAllEditsOfToken(ngramTokens[2])
        setProducts = itertools.product(token1Edits.get(), token2Edits.get(), token3Edits.get())
    return {u' '.join(editSet) for editSet in setProducts}


def getElemsNotInIterObj(elemDict, iterObj, replaceKeyForValue=False):
    '''given a dict of elements and an iterable object, if the elements are
	found in the iterable object, it replaces the None value with the iterable element '''
    # if it's not a dict, make it a dict
    if type(elemDict) is not dict:
        elemList, elemDict = list(elemDict), {}
        for index, key in enumerate(elemList):
            # if the token appears multiple times in the list
            if key in elemDict:
                elemDict[key] = (None, elemDict[key][1] + [index])
            else:
                elemDict[key] = (None, [index])
    # if the element is in the iterable object
    for keyElem, valueElem in elemDict.items():
        if valueElem[0] == None and keyElem in iterObj:
            # if the iterable object is a dict and we want the value, not the key
            if type(iterObj) is dict and replaceKeyForValue != False:
                elemDict[keyElem] = (iterObj[keyElem], valueElem[1])
            else:
                elemDict[keyElem] = (keyElem, valueElem[1])
        # if there is a numeric or ascii symbol character in the token we take it as is
        elif len(re.findall(re.compile(r'([0-9]|-|\+|\!|\#|\$|%|&|\'|\*|\?|\.|\^|_|`|\||~|:|@)'), keyElem)) > 0:
            elemDict[keyElem] = (keyElem, valueElem[1])
    return elemDict


def applyNaiveStatCorrection(notPresentList, elemDict, lang, wordCountDict, dejavuDict):
    ''' given a list of uncorrected tokens, applies a naive statistic spell correction
	and saves the result to the dict '''
    # multi threading
    with closing(mp.Pool(processes=4)) as pool:
        # put in a variable the function correction with a constant argument lang
        correctionWithConstantLangVar = partial(correction, lang=lang, returnProbabilityScore=False,
                                                wordCountDict=wordCountDict)
        # correct each token and put it in a different list using multiprocessing to go faster
        correctedStringTokenList = pool.map(correctionWithConstantLangVar, list(notPresentList))
    # dump into dict
    for index, notCorrectedTok in enumerate(notPresentList):
        # into the element dict
        elemDict[notCorrectedTok] = (correctedStringTokenList[index], elemDict[notCorrectedTok][1])
        # and into the deja vu dict
        dejavuDict[notCorrectedTok] = correctedStringTokenList[index]
    return elemDict, dejavuDict


def gethigherIndex(aDict):
    higherIndex = 0
    for valTupl in aDict.values():
        for ind in valTupl[1]:
            if ind > higherIndex:
                higherIndex = ind
    return higherIndex


def elemDictToList(elemDict):
    """"""
    correctedStringTokenList = [None] * (gethigherIndex(elemDict) + 1)
    changedTokenCounter = 0
    for keyTok, valTok in elemDict.items():
        if valTok[0] != None:
            for valIndex in valTok[1]:
                correctedStringTokenList[valIndex] = valTok[0]
            changedTokenCounter += 1
        else:
            correctedStringTokenList[valTok[1]] = keyTok
    return correctedStringTokenList


def naiveSpellChecker(string, dejavuDict={}, lang=u'en', wordCountDict=None, returnCorrectedTokenScore=False,
                      captureSymbols=False):
    '''
	for each token in the string, it returns the most statistically 
	closely	related and most counted token in the big data
	'''

    def getGreaterVal(listOfLists):
        greater = [None, 0]
        for aList in listOfLists:
            if aList[1] > greater[1]:
                greater = aList
        return greater[0]

    # get the tokens from the string
    stringTokenList = naiveRegexTokenizer(string, caseSensitive=False, eliminateStopwords=False,
                                          captureSymbols=captureSymbols)
    # get the most common (and probably correctly written) tokens from wikipedia
    setOfMostCommon = set([key.lower() for key in utilsOs.openJsonFileAsDict(
        u'./resources/tokDict/{0}TokReducedLessThan1000Instances.json'.format(lang))])
    # get the abbreviation dict
    abbreviationDict = {key: getGreaterVal(value) for key, value in utilsOs.openJsonFileAsDict(
        u'./resources/tokDict/{0}AbbrevDictReducedLess1000.json'.format(lang)).items()}
    # verify if the tokens are not already well written
    elemDict = getElemsNotInIterObj(stringTokenList, setOfMostCommon)
    # verify if not in dejavus
    elemDict = getElemsNotInIterObj(elemDict, dejavuDict, replaceKeyForValue=True)
    # verify if it's not an abbreviation
    elemDict = getElemsNotInIterObj(elemDict, abbreviationDict, replaceKeyForValue=True)
    # if there are still tokens that have not yet been seen
    notPresentList = [k for k, v in elemDict.items() if v[0] == None]
    if len(notPresentList) != 0:
        # apply correction
        elemDict, dejavuDict = applyNaiveStatCorrection(notPresentList, elemDict, lang, wordCountDict, dejavuDict)
    # make a list of the final elements to return
    correctedStringTokenList = elemDictToList(elemDict)
    # give a normalized score representing how many tokens in the whole string needed some level of correction
    if returnCorrectedTokenScore != False:
        correctedTokenScore = float(len([tok for tok in elemDict if tok not in setOfMostCommon])) / float(len(elemDict))
        return u' '.join(correctedStringTokenList), correctedTokenScore, dejavuDict
    # otherwise
    return u' '.join(correctedStringTokenList), dejavuDict


def naiveSpellCheckerOrora(string, dejavuDict={}, lang=u'en', wordCountDict=None, returnCorrectedTokenScore=False,
                           capturePunctuation=False,
                           captureSymbols=[r'\+', r'\#', r'\$', r'%', r'&', r'\'', r'\*', r'`', r'\|', r'~', r':', r'-', r'¤']):
    '''
	for each token in the string, it returns the most statistically 
	closely	related and most counted token in the big data
	'''

    def getGreaterVal(listOfLists):
        greater = [None, 0]
        for aList in listOfLists:
            if aList[1] > greater[1]:
                greater = aList
        return greater[0]

    # get the tokens from the string
    stringTokenList = naiveRegexTokenizer(string, caseSensitive=False, eliminateStopwords=False,
                                          capturePunctuation=capturePunctuation, captureSymbols=captureSymbols)
    # get the most common (and probably correctly written) tokens from wikipedia, if there is a number or symbol in the set of most commons, eliminate it
    nbAndSymbols = re.compile(r'([0-9]|-|\+|\!|\#|\$|%|&|\'|\*|\?|\.|\^|_|`|\||~|:|@)')
    setOfMostCommon = set([key.lower() for key in utilsOs.openJsonFileAsDict(
        u'./resources/tokDict/{0}TokReducedLessThan1000Instances.json'.format(lang)) if
                           len(re.findall(nbAndSymbols, key)) == 0])
    # get the abbreviation dict
    abbreviationDict = {key: getGreaterVal(value) for key, value in utilsOs.openJsonFileAsDict(
        u'./resources/tokDict/{0}AbbrevDictORORA.json'.format(lang)).items()}
    # verify if the tokens are not already well written
    elemDict = getElemsNotInIterObj(stringTokenList, setOfMostCommon)
    # verify if not in dejavus
    elemDict = getElemsNotInIterObj(elemDict, dejavuDict, replaceKeyForValue=True)
    # verify if it's not an abbreviation
    elemDict = getElemsNotInIterObj(elemDict, abbreviationDict, replaceKeyForValue=True)
    # if there are still tokens that have not yet been seen
    notPresentList = [k for k, v in elemDict.items() if v[0] == None]
    if len(notPresentList) != 0:
        # apply correction
        elemDict, dejavuDict = applyNaiveStatCorrection(notPresentList, elemDict, lang, wordCountDict, dejavuDict)
    # make a list of the final elements to return
    correctedStringTokenList = elemDictToList(elemDict)
    # give a normalized score representing how many tokens in the whole string needed some level of correction
    if returnCorrectedTokenScore != False:
        correctedTokenScore = float(len([tok for tok in elemDict if tok not in setOfMostCommon])) / float(len(elemDict))
        return u' '.join(correctedStringTokenList), correctedTokenScore, dejavuDict
    # otherwise
    return u' '.join(correctedStringTokenList), dejavuDict


def naiveNgramSpellChecker(string, n=3, lang=u'en'):
    '''
	for each ngram in the string, it returns the most closely 
	related and most counted ngram in the big data
	'''
    stringTok3gramList = ngrams(string, n)
    correctedStringNgramList = []
    # correct each ngram and put it in a different list
    for ngram in stringTok3gramList:
        correctedStringNgramList.append(correctionNgram(ngram, lang)[0])
    # give a normalized score representing how many ngrams in the whole string needed some level of correction
    correctedNgramScore = float(
        len([ngrm for ngrm in correctedStringNgramList if ngrm not in stringTok3gramList])) / float(
        len(stringTok3gramList))
    return u' '.join(correctedStringNgramList), correctedNgramScore


##################################################################################
# TRANSLATORS
##################################################################################

def googletransLibTransl(string, srcLang=u"en", trgtLang=u"fr"):
    """
    translates a string from a src language to a target language
    the language codes appear in googletrans.LANGUAGES
    :param string: string to be translated
    :param srcLang: language code for the source (e.g., 'en', 'fr', 'es', 'de', 'it', 'ja', 'la', 'hi', 'zh-cn')
    :param trgtLang: language code for the target
    :return: the string translated into the target language
    """
    translator = Translator()
    return translator.translate(string, src=srcLang, dest=trgtLang).text


def langSelectClicker(session, langSelectXpath, langOptionXpath):
    # click on the language selector
    langSelector = session.find_element_by_xpath(langSelectXpath)
    langSelector.click()
    time.sleep(random.uniform(0.7, 1.1))
    # click on the english language option
    lang = session.find_element_by_xpath(langOptionXpath)
    lang.click()
    time.sleep(random.uniform(0.9, 1.5))
    return session


def selectLangDeepL(session, srcLang=u'en'):
    """
    given a language and its classification as src or trgt
    selects the right language for the combination en-fr or fr-en
    :param session: selenium opened session
    :param srcLang: language to click on as source
    :return: session: selenium session with the selection made
    """
    srcLangSelectXpath = u"/html/body/div[2]/div[1]/div[1]/div[2]/div[1]/div/button/div"
    trgtLangSelectXpath = u"/html/body/div[2]/div[1]/div[1]/div[3]/div[1]/div/button/div"
    if srcLang == u"en":
        srcXpath = u"//div[2]/div[1]/div/div/button[@dl-value='EN']"
        trgtXpath = u"//div[3]/div[1]/div/div/button[@dl-value='FR']"
    elif srcLang == u"fr":
        srcXpath = u"//div[2]/div[1]/div/div/button[@dl-value='FR']"
        trgtXpath = u"//div[3]/div[1]/div/div/button[@dl-value='EN']"
    # select language for the source
    session = langSelectClicker(session, srcLangSelectXpath, srcXpath)
    # select language for the target
    session = langSelectClicker(session, trgtLangSelectXpath, trgtXpath)
    return session


def deepLSeleniumTranslEnFr(stringOrListOfString, sourceLang=u"en", noAlternatives=True):
    """
    Given a string of list of strings returns the translation
    :param stringOrListOfString: string or list of strings to be translated
    :param sourceLang: language of the source string(s) (en or fr)
    :return: the string(s) translated
    """
    finalTranslations = []
    if type(stringOrListOfString) is str:
        stringOrListOfString = [stringOrListOfString]
    # count the time
    start = utilsOs.countTime()
    # info
    deepLUrl = u"https://www.deepl.com/translator"
    # open the driver
    session = webdriver.Firefox()
    session.get(deepLUrl)
    time.sleep(random.uniform(1.3, 3.1))
    # select english as source in deepL
    session = selectLangDeepL(session, sourceLang)
    for srcString in stringOrListOfString:
        translAndAlt = []
        # click on the source text area and paste the english sentence
        textArea = session.find_element_by_xpath(u"/html/body/div[2]/div[1]/div[1]/div[2]/div[2]/div/textarea")
        textArea.click()
        time.sleep(random.uniform(0.4, 0.9))
        textArea.clear()
        textArea.send_keys(srcString)
        # click on the copy to clipboard button to copy the target text
        cpButton = session.find_element_by_xpath(u"/html/body/div[2]/div[1]/div[1]/div[3]/div[3]/div[3]/div[1]/button")
        time.sleep(random.uniform(0.2, 0.7))
        cpButton.click()
        mainTransl = None
        # close the tkinter window
        tkinterRoot = Tk()
        tkinterRoot.withdraw()
        while mainTransl is None:
            time.sleep(random.uniform(0.5, 0.8))
            cpButton.click()
            time.sleep(random.uniform(1.2, 1.9))
            try:
                mainTransl = tkinterRoot.clipboard_get()
                break
            except TclError:
                pass
        # get the text from the clipboard
        mainTransl = tkinterRoot.clipboard_get()
        print(1111, mainTransl)
        if noAlternatives is True:
            translAndAlt = mainTransl
        else:
            translAndAlt.append(mainTransl)
            # look for alternative translations
            for n in range(2, 10):
                try:
                    alt = session.find_element_by_xpath(
                        u"/html/body/div[2]/div[1]/div[1]/div[3]/div[3]/div[2]/p[{0}]/button[1]".format(n))
                    translAndAlt.append(alt.text)
                    print(2222, translAndAlt)
                except NoSuchElementException:
                    break
        # take a coffee break if it's been near half an hour
        if utilsOs.countTime(start) >= 1650:
            session.close()
            time.sleep(random.uniform(60, 80))
            start = utilsOs.countTime()
            # open the driver
            session = webdriver.Firefox()
            session.get(deepLUrl)
            time.sleep(random.uniform(1.3, 3.1))
            # select english as source in deepL
            session = selectLangDeepL(session, sourceLang)
        # delete the content of the text area
        textArea.click()
        time.sleep(random.uniform(0.3, 0.6))
        textArea.clear()
        # add to the final list of translations
        finalTranslations.append(translAndAlt)
    session.close()
    return finalTranslations


def googleTranslateSeleniumEnFr(stringOrListOfString, sourceLang=u"en", noAlternatives=True):
    """
    Given a string of list of strings returns the translation
    :param stringOrListOfString: string or list of strings to be translated
    :param sourceLang: language of the source string(s) (en or fr)
    :return: the string(s) translated
    """
    finalTranslations = []
    if type(stringOrListOfString) is str:
        stringOrListOfString = [stringOrListOfString]
    # count the time
    start = utilsOs.countTime()
    # info
    deepLUrl = u"https://www.deepl.com/translator"
    # open the driver
    session = webdriver.Firefox()
    session.get(deepLUrl)
    time.sleep(random.uniform(1.3, 3.1))
    # select english as source in deepL
    session = selectLangDeepL(session, sourceLang)
    for srcString in stringOrListOfString:
        translAndAlt = []
        # click on the source text area and paste the english sentence
        textArea = session.find_element_by_xpath(u"/html/body/div[2]/div[1]/div[1]/div[2]/div[2]/div/textarea")
        textArea.click()
        time.sleep(random.uniform(0.4, 0.9))
        textArea.clear()
        textArea.send_keys(srcString)
        # click on the copy to clipboard button to copy the target text
        cpButton = session.find_element_by_xpath(u"/html/body/div[2]/div[1]/div[1]/div[3]/div[3]/div[3]/div[1]/button")
        time.sleep(random.uniform(0.2, 0.7))
        cpButton.click()
        mainTransl = None
        # close the tkinter window
        tkinterRoot = Tk()
        tkinterRoot.withdraw()
        while mainTransl is None:
            time.sleep(random.uniform(0.5, 0.8))
            cpButton.click()
            time.sleep(random.uniform(1.2, 1.9))
            try:
                mainTransl = tkinterRoot.clipboard_get()
                break
            except TclError:
                pass
        # get the text from the clipboard
        mainTransl = tkinterRoot.clipboard_get()
        if noAlternatives is True:
            translAndAlt = mainTransl
        else:
            translAndAlt.append(mainTransl)
            # look for alternative translations
            for n in range(2, 10):
                try:
                    alt = session.find_element_by_xpath(
                        u"/html/body/div[2]/div[1]/div[1]/div[3]/div[3]/div[2]/p[{0}]/button[1]".format(n))
                    translAndAlt.append(alt.text)
                    print(2222, translAndAlt)
                except NoSuchElementException:
                    break
        # take a coffee break if it's been near half an hour
        if utilsOs.countTime(start) >= 1650:
            session.close()
            time.sleep(random.uniform(60, 80))
            start = utilsOs.countTime()
            # open the driver
            session = webdriver.Firefox()
            session.get(deepLUrl)
            time.sleep(random.uniform(1.3, 3.1))
            # select english as source in deepL
            session = selectLangDeepL(session, sourceLang)
        # delete the content of the text area
        textArea.click()
        time.sleep(random.uniform(0.3, 0.6))
        textArea.clear()
        # add to the final list of translations
        finalTranslations.append(translAndAlt)
    session.close()
    return finalTranslations



##################################################################################
# LINGUISTIC DICTS AND RESOURCES
##################################################################################

def openFauxAmisDict(enToFr=True, withDescription=False, reducedVersion=False):
    """ opens the faux amis (false cognates) dict """
    path = u'/u/alfonsda/Documents/workRALI/utils/resources/fauxAmis/fauxAmis'
    if withDescription is not False:
        path = u'{0}AndDescrip'.format(path)
    if reducedVersion is not False:
        path = u'{0}Reduced'.format(path)
    if enToFr is True:
        path = u'{0}En-Fr.json'.format(path)
    else:
        path = u'{0}Fr-En.json'.format(path)
    return utilsOs.openJsonFileAsDict(path)


def openEn2FrStopWordsDict():
    """ opens the stop words dict """
    path = u'/u/alfonsda/Documents/workRALI/utils/resources/litteralTranslationDict/stopWordsEn-Fr.json'
    return utilsOs.openJsonFileAsDict(path)


def dumpStarbucksWordAndExpressionDicts():
    """ takes the web-scrapped starbucks en-fr dict and dumps it as a json """
    inputExprPath = u'/u/demorali/corpora/dict/starbucks/lexicons/expr_lexicon.txt'
    inputWordPath = u'/u/demorali/corpora/dict/starbucks/lexicons/word_lexicon.txt'
    outputExprPath = u'/u/alfonsda/Documents/workRALI/utils/resources/litteralTranslationDict/starbucksEn-FrExpr.json'
    outputWordPath = u'/u/alfonsda/Documents/workRALI/utils/resources/litteralTranslationDict/starbucksEn-FrWord.json'
    exprDict, wordDict = {}, {}
    # open the expression txt file
    with open(inputExprPath) as exprFile:
        exprLns = [ln.replace(u'\n', u'') for ln in exprFile.readlines()]
    # make the expression dict
    for expr in exprLns:
        exprList = expr.split(u'\t')
        if exprList[0] not in exprDict:
            exprDict[exprList[0]] = [exprList[1]]
        else:
            exprDict[exprList[0]].append(exprList[1])
    # open the word txt file
    with open(inputWordPath) as wordFile:
        wordLns = [ln.replace(u'\n', u'') for ln in wordFile.readlines()]
    # make the expression dict
    for word in wordLns:
        wordList = word.split(u'\t')
        if wordList[0] not in wordDict:
            wordDict[wordList[0]] = [wordList[1]]
        else:
            wordDict[wordList[0]].append(wordList[1])
    # dump the dicts
    utilsOs.dumpDictToJsonFile(exprDict, outputExprPath, overwrite=True)
    utilsOs.dumpDictToJsonFile(wordDict, outputWordPath, overwrite=True)


def openEn2FrStarbucksDict():
    """ opens and returns the starbucks expression and word dicts """
    exprPath = u'/u/alfonsda/Documents/workRALI/utils/resources/litteralTranslationDict/starbucksEn-FrExpr.json'
    wordPath = u'/u/alfonsda/Documents/workRALI/utils/resources/litteralTranslationDict/starbucksEn-FrWord.json'
    return utilsOs.openJsonFileAsDict(exprPath), utilsOs.openJsonFileAsDict(wordPath)


##################################################################################
# SPECIAL DICTS - TOKENS
##################################################################################

def tokenDictMaker(string):
    '''
	takes a string, makes a dict of tokens with their count
	'''
    tokenDict = {}
    for token in naiveRegexTokenizer(string):
        tokenDict[token] = tokenDict.get(token, 0.0) + 1.0
    return tokenDict


def makeTokenCountDictFromText(inputPath, outputPath):
    '''
	given the path to a text file, tokenizes and 
	counts the intances of each token and dumps the
	dict into a jsonfile
	VERY SIMILAR TO tokenDictMakerFromFile() BUT LESS TIME CONSUMING AND SLIGHTLY LESS HANDS-ON
	'''
    import json
    from collections import Counter
    # open text file as string
    with codecs.open(inputPath, 'r', encoding='utf8') as bigDataFile:
        tokenCountDict = {}
        # read one line at a time
        bigDataLine = bigDataFile.readline()
        while bigDataLine:
            lineTokCountDict = Counter(
                naiveRegexTokenizer(bigDataLine, caseSensitive=True, eliminateStopwords=False, language=u'english'))
            tokenCountDict = utilsDataStruct.mergeDictsAddValues(tokenCountDict, lineTokCountDict)
            # next line
            bigDataLine = bigDataFile.readline()
    # dumping
    with codecs.open(outputPath, u'wb', encoding=u'utf8') as dictFile:
        dictFile.write('')
        json.dump(tokenCountDict, dictFile)
    return tokenCountDict


def tokenDictMakerFromFile(inputFilePath, outputFilePath=None):
    '''
	###NEED TO ANALYSE IF REMOVE IT AND REPLACE IT WITH makeTokenCountDictFromText() DEFINITELY
	######################################################################
	takes a corpus file, makes a dict of tokens with their count
	and dumps the result in a json file
	VERY SIMILAR TO makeTokenCountDictFromText() BUT MORE HANDS-ON AND SELF-BUILT
	'''
    tokenDict = {}
    stringList = utilsOs.readAllLinesFromFile(inputFilePath, True)
    for string in stringList:
        tokenList = naiveRegexTokenizer(string.replace(u'/', u' '))
        for token in tokenList:
            tokenDict[token] = tokenDict.get(token, 0.0) + (1.0 / len(stringList))
            # we also add the lowercase version if there is an uppercase in the token
            if any(c.isupper() for c in token):
                tokenDict[token.lower()] = tokenDict.get(token.lower(), 0.0) + (1.0 / len(stringList))
    if outputFilePath == None:
        outputFilePath = utilsOs.safeFilePath(inputFilePath.replace(inputFilePath.split(u'/')[-1], 'tokens.json'))
    utilsOs.dumpDictToJsonFile(tokenDict, outputFilePath)
    return tokenDict


def makeTokNgramCountDictFromText(inputPath, outputPath, n):
    '''
	given the path to a text file, tokenizes, groups by n-grams and
	counts the intances of each ngram and dumps the resulting
	dict into a jsonfile
	'''
    import json
    from collections import Counter
    # first dump an empty dict
    utilsOs.dumpDictToJsonFile({}, outputPath, overwrite=True)

    # dumping function
    def overwriteAndDump(outputPath, tokNgramCountDict):
        oldDict = utilsOs.openJsonFileAsDict(outputPath)
        bothDicts = utilsDataStruct.mergeDictsAddValues(tokNgramCountDict, oldDict)
        utilsOs.dumpDictToJsonFile(bothDicts, outputPath, overwrite=True)
        # unnecessary ?
        oldDict, bothDicts = {}, {}

    # count the total of lines in the file
    with codecs.open(inputPath, 'r', encoding='utf8') as bigDataFile:
        totalLines = utilsOs.countLines(bigDataFile)
        onePercentOfLines = int(float(totalLines) / 100.0)
        print(u'{0}/{1}'.format(0, totalLines))
    # open text file as string
    with codecs.open(inputPath, 'r', encoding='utf8') as bigDataFile:
        tokNgramCountDict = {}
        # read one line at a time
        bigDataLine = bigDataFile.readline()
        counter = 1
        while bigDataLine:
            # for jsonData in tqdm(jsonFile, total=utilsOs.countLines(jsonFile))
            lineTokCountDict = Counter(ngrams(bigDataLine, n))
            tokNgramCountDict = utilsDataStruct.mergeDictsAddValues(tokNgramCountDict, lineTokCountDict)
            # chronical dump every 1%
            if counter % onePercentOfLines == 0:
                overwriteAndDump(outputPath, tokNgramCountDict)
                tokNgramCountDict = {}
                print(u'{0}/{1}'.format(counter, totalLines))
            # next line
            bigDataLine = bigDataFile.readline()
            counter += 1
    # final dumping
    overwriteAndDump(outputPath, tokNgramCountDict)
    return tokNgramCountDict


def getBigDataDict(ressourceType=u'token',
                   lang=u'en'):  ########################should work but not tested#######################
    '''
	given a language code, searchs for the corresponding 
	a big data text file and returns a instance counter dict.
	The ressource arument must have the values:
		- 'token' : token frequency dict
		- 'ngram' : ngram frequency dict
		- 'hybrid' : both token and ngram frequency dicts
	Accepted languages:
		- u'en': english
		- u'fr': french
	'''
    import json
    # language error
    if lang not in [u'en', u'fr']:
        raise TypeError('The given language is not in our database, choose among: ["en", "fr"]')
    # assign a path to the big data ressource corresponding to the language
    if ressourceType == u'token':
        # data is also available at u'/data/rali5/Tmp/alfonsda/wikiDump/outputWikidump/tokDict'
        bigDataPath = u'./resources/{0}Tok.json'.format(lang)
    elif ressourceType == u'ngram':
        bigDataPath = u'./resources/{0}Tok3gram.json'.format(lang)
    elif ressourceType == u'hybrid':
        bigDataPath1 = u'./resources/{0}Tok.json'.format(lang)
        bigDataPath2 = u'./resources/{0}Tok3gram.json'.format(lang)
        # return a collections.counter dict of the counted instances of the words
        with codecs.open(bigDataPath1, u'r', encoding=u'utf8') as openedFile1:
            with codecs.open(bigDataPath2, u'r', encoding=u'utf8') as openedFile2:
                return json.load(openedFile1), json.load(openedFile2)
    # return a collections.counter dict of the counted instances of the words
    with codecs.open(bigDataPath, u'r', encoding=u'utf8') as openedFile:
        return json.load(openedFile)


def removeLessFrequentFromBigDataDict(inputFilePath, outputFilePath=None, minValue=1, removeNumbers=True):
    ''' makes a new dict but removing the hapax legomenon and less frequent tokens '''
    bigDataDict = utilsOs.openJsonFileAsDict(inputFilePath)
    print('BEFORE removing the less frequent tokens: ', len(bigDataDict))
    # delete the keys with values under the min value limit
    for key, value in list(bigDataDict.items()):
        if value <= minValue:
            del bigDataDict[key]
        # also remove numbers
        elif removeNumbers == True:
            try:
                nb = float(key)
                del bigDataDict[key]
            except ValueError:
                pass
    # dumping
    if outputFilePath != None:
        utilsOs.dumpDictToJsonFile(bigDataDict, outputFilePath, overwrite=True)
    print('AFTER removing the less frequent tokens: ', len(bigDataDict))
    return bigDataDict


def makeBigDataDictOfArtificialErrorsAndAbbreviations(inputFilePath, outputFilePath=None, errorsEditDist=1,
                                                      abbreviations=True, unusualAbbrOnly=False):
    ''' Makes a new dict containing tokens with artificially induced errors with a specified
	edit distance (must not be greater than 4) and each token's possible abreviations.
	The original token will not appear in the error and abbreviation dict.'''
    errorAndAbbrDict = {}
    emptyList = []
    dataDict = utilsOs.openJsonFileAsDict(inputFilePath)

    def attributeEdits(token, errorsEditDist):
        if errorsEditDist == 1:
            return edits1(token)
        elif errorsEditDist == 0 or errorsEditDist == None:
            return [token]
        elif errorsEditDist == 2:
            return edits2(token)
        elif errorsEditDist == 3:
            return edits3(token)
        else:
            return edits4(token)

    # browse the original dict
    for index, (token, value) in enumerate(dataDict.items()):
        if index % 5000 == 0:
            print(index, len(dataDict))
        # get artificial errors of specified distance
        errorsList = list(attributeEdits(token, errorsEditDist))
        # get artificial abbreviations
        if abbreviations == True:
            abbrList = makeAbbreviations(token, unusualAbbrOnly)
        else:
            abbrList = []
        # browse the error and abbr list
        for artificialToken in set(errorsList + abbrList):
            errorAndAbbrDict[artificialToken] = errorAndAbbrDict.get(artificialToken, list(emptyList)) + [
                (token, value)]
    # dumping
    if outputFilePath != None:
        utilsOs.dumpDictToJsonFile(errorAndAbbrDict, outputFilePath, overwrite=True)
    return errorAndAbbrDict


##################################################################################
# SPECIAL DICTS - CHARACTERS
##################################################################################


def trigramDictMaker(string):
    '''
	takes a string, makes a dict of character 3grams with their count
	'''
    trigramDict = {}
    for i in range(len(string) - 2):
        trigramDict[string[i:i + 3]] = trigramDict.get(string[i:i + 3], 0.0) + 1.0
    return trigramDict


def quadrigramDictMaker(string):
    '''
	takes a string, makes a dict of character 4grams with their count
	'''
    quadrigramDict = {}
    for i in range(len(string) - 3):
        quadrigramDict[string[i:i + 4]] = quadrigramDict.get(string[i:i + 4], 0.0) + 1.0
    return quadrigramDict


def trigramDictMakerFromFile(inputFilePath, outputFilePath=None):
    '''
	takes a corpus file, makes a dict of character 3grams with their count
	and dumps the result in a json file
	'''
    trigramDict = {}
    stringList = utilsOs.readAllLinesFromFile(inputFilePath, True)
    langString = u' '.join(stringList)
    for i in range(len(langString) - 2):
        trigramDict[langString[i:i + 3]] = trigramDict.get(langString[i:i + 3], 0.0) + (1.0 / len(stringList))
    if outputFilePath == None:
        outputFilePath = utilsOs.safeFilePath(inputFilePath.replace(inputFilePath.split(u'/')[-1], 'trigrams.json'))
    utilsOs.dumpDictToJsonFile(trigramDict, outputFilePath)
    return trigramDict


def quadrigramDictMakerFromFile(inputFilePath, outputFilePath=None):
    '''
	takes a corpus file, makes a dict of character 4grams with their count
	and dumps the result in a json file
	'''
    quadrigramDict = {}
    stringList = utilsOs.readAllLinesFromFile(inputFilePath, True)
    langString = u' '.join(stringList)
    for i in range(len(langString) - 3):
        quadrigramDict[langString[i:i + 4]] = quadrigramDict.get(langString[i:i + 4], 0.0) + (1.0 / len(stringList))
    if outputFilePath == None:
        outputFilePath = utilsOs.safeFilePath(inputFilePath.replace(inputFilePath.split(u'/')[-1], 'quadrigrams.json'))
    utilsOs.dumpDictToJsonFile(quadrigramDict, outputFilePath)
    return quadrigramDict


##################################################################################
# COMPARISONS AND EVALUATIONS
##################################################################################

def langDictComparison(dictUnk, dictLang):
    '''
	compares 2 dictionnaries and returns the distance between 
	its keys (using the scores in the values)
	'''
    distance = 0
    weight = 1
    # get the greatest value so we can use it as a divisor
    maxUnk = float(max(dictUnk.values()))
    # we make the sum of all the distances
    for key in dictUnk:
        # distance calculation
        distance += abs((dictUnk[key] / maxUnk) - dictLang.get(key, 0))
    return distance


##################################################################################
# TEXT ALIGNMENT
##################################################################################

def vecinityAlignmentMatch(tokenList1, tokenList2, alignList1, alignList2, ind1, ind2, endInd2):
    ''' return the modified alignment lists if the token in "a" is found in a nearby index in "b"'''
    ind2Temp = int(ind2)
    if tokenList1[ind1] in tokenList2[ind2:endInd2]:
        # look in the vecinity of the string2
        while ind2Temp != endInd2:
            # if it's not that particular element in the window, we add an empty element to the alignment
            if tokenList1[ind1] != tokenList2[ind2Temp]:
                alignList1.append(u'∅')
                alignList2.append(tokenList2[ind2Temp])
                ind2 = ind2 + 1 if ind2 + 1 != len(tokenList2) else None
                ind2Temp += 1
            # if we find the rigth element
            else:
                alignList1.append(tokenList1[ind1])
                alignList2.append(tokenList2[ind2Temp])
                # change both indices
                ind1 = ind1 + 1 if ind1 + 1 != len(tokenList1) else None
                ind2 = ind2 + 1 if ind2 + 1 != len(tokenList2) else None
                # we stop to avoid going further than  the found element
                break
    return alignList1, alignList2, ind1, ind2


def makeSimilarityList4FirstTok1(tokens1, tokens2):
    ''' given 2 list of tokens, creates an ordered list containing all distances between the first token1 and all the tokens2 '''
    similList = []
    nonMatchTokens2 = []
    # only compare for the immediate tokens2-neighbours that do not appear in tokens1
    for tok2 in tokens2:
        if tok2 not in tokens1:
            nonMatchTokens2.append(tok2)
        else:
            break
    # make the similarity list with the other tokens
    for i2, tok2 in enumerate(nonMatchTokens2):
        similList.append([distance.edit_distance(tokens1[0], tok2), tok2, i2])
    # order the list
    similList = sorted(similList, key=lambda distList: distList[0])
    return similList


def addTokToALign(immediateSimilList1, immediateSimilList2, tokenList1, tokenList2, alignList1, alignList2, ind1, ind2):
    """"""
    # we add to the token1
    emptyTokens = [u'∅'] * immediateSimilList1[0][2]
    alignList1 = alignList1 + emptyTokens + [tokenList1[ind1]]
    ind1 = ind1 + 1 if ind1 + 1 != len(tokenList1) else None
    # we add the token2
    alignList2 = alignList2 + tokenList2[ind2:(ind2 + immediateSimilList1[0][2] + 1)]
    ind2 = ind2 + (1 + immediateSimilList1[0][2]) if ind2 + (1 + immediateSimilList1[0][2]) != len(tokenList2) else None
    return alignList1, alignList2, ind1, ind2


def getMostSimilarAlignment(tokenList1, tokenList2, alignList1, alignList2, ind1, ind2, endInd1, endInd2):
    ''' looks at the context window of the token and populates the alignString list to match the most similar to the token '''
    immediateSimilList1 = makeSimilarityList4FirstTok1(tokenList1[ind1:endInd1], tokenList2[ind2:endInd2])
    immediateSimilList2 = makeSimilarityList4FirstTok1(tokenList2[ind2:endInd2], tokenList1[ind1:endInd1])
    # decide which token (the first one from the first list or form the second list) has better similarity
    if immediateSimilList1[0][0] == immediateSimilList2[0][0]:  # if the distance is the same
        # if there is a cross, e.g., l1 = [7, 8] ; l2 = [8, 9]    and the distance is the same
        if immediateSimilList1[0][0] == immediateSimilList2[0][0] and immediateSimilList1[0][2] != 0 and \
                immediateSimilList2[0][2] != 0 and immediateSimilList1[0][2] == immediateSimilList2[0][2]:
            # we return the first token of both lists
            alignList1.append(tokenList1[ind1])
            alignList2.append(tokenList2[ind2])
            # change both indices
            ind1 = ind1 + 1 if ind1 + 1 != len(tokenList1) else None
            ind2 = ind2 + 1 if ind2 + 1 != len(tokenList2) else None
        # take the first appearing one
        elif immediateSimilList1[0][2] <= immediateSimilList2[0][2]:
            alignList1, alignList2, ind1, ind2 = addTokToALign(immediateSimilList1, immediateSimilList2, tokenList1,
                                                               tokenList2, alignList1, alignList2, ind1, ind2)
        else:
            alignList2, alignList1, ind2, ind1 = addTokToALign(immediateSimilList2, immediateSimilList1, tokenList2,
                                                               tokenList1, alignList2, alignList1, ind2, ind1)
    # if the distance for the token1 is smaller
    elif immediateSimilList1[0][0] < immediateSimilList2[0][0]:
        alignList1, alignList2, ind1, ind2 = addTokToALign(immediateSimilList1, immediateSimilList2, tokenList1,
                                                           tokenList2, alignList1, alignList2, ind1, ind2)
    # if the distance for the token 2 is smaller
    else:
        alignList2, alignList1, ind2, ind1 = addTokToALign(immediateSimilList2, immediateSimilList1, tokenList2,
                                                           tokenList1, alignList2, alignList1, ind2, ind1)
    return alignList1, alignList2, ind1, ind2


def align2SameLangStrings(string1, string2, windowSize=2, alignMostSimilar=False, tokenizingFunct=None, *args):
    ''' given 2 strings in the same language, it aligns them in a table of tuples '''
    alignString1 = []
    alignString2 = []
    # replace repetition of space characters with a distinctive symbol
    for nbSpace in reversed(range(3, 10)):
        if u' ' * nbSpace in string1:
            string1 = string1.replace(u' ' * nbSpace, u' {0} '.format(u'¤*¤¤¤¤' * nbSpace))
        if u' ' * nbSpace in string2:
            string2 = string2.replace(u' ' * nbSpace, u' {0} '.format(u'¤*¤¤¤¤' * nbSpace))
    # tokenize (we don't use the naive regex tokenizer to avoid catching the  "-" and "'" and so on)
    if tokenizingFunct == None:
        string1Tok = string1.split(u' ')
        string2Tok = string2.split(u' ')
    # if there is a particular tokenizing function we wish to use
    else:
        string1Tok = tokenizingFunct(string1, *args)
        string2Tok = tokenizingFunct(string2, *args)
    # replace back the distinctive characters replacing the spaces with actual spaces
    string1Tok = [elem.replace(u'¤*¤¤¤¤', u' ') for elem in string1Tok]
    string2Tok = [elem.replace(u'¤*¤¤¤¤', u' ') for elem in string2Tok]
    # prepare the alignment indexes
    ind1, ind2 = 0, 0
    # start aligning
    while ind1 != len(string1Tok) and ind2 != len(string2Tok):
        # if ind1 and 2 are None
        if ind1 == None and ind2 == None:
            break
        # if ind1 is None
        elif ind1 == None:
            alignString1 = alignString1 + ([u'∅'] * len(string2Tok[ind2:]))
            alignString2 = alignString2 + string2Tok[ind2:]
            break
        # if ind2 is None
        elif ind2 == None:
            alignString2 = alignString2 + ([u'∅'] * len(string1Tok[ind1:]))
            alignString1 = alignString1 + string1Tok[ind1:]
            break
        # get the end index
        endInd1 = ind1 + windowSize + 1 if ind1 + windowSize + 1 < len(string1Tok) else len(string1Tok)
        endInd2 = ind2 + windowSize + 1 if ind2 + windowSize + 1 < len(string2Tok) else len(string2Tok)
        # if they correspond
        if string1Tok[ind1] == string2Tok[ind2]:
            # add them to the aligned list
            alignString1.append(string1Tok[ind1])
            alignString2.append(string2Tok[ind2])
            # change both indices
            ind1 = ind1 + 1 if ind1 + 1 != len(string1Tok) else None
            ind2 = ind2 + 1 if ind2 + 1 != len(string2Tok) else None
        # if the token in string1 is found in a nearby index in string2 or vice-versa
        elif string1Tok[ind1] in string2Tok[ind2:endInd2]:
            alignString1, alignString2, ind1, ind2 = vecinityAlignmentMatch(string1Tok, string2Tok, alignString1,
                                                                            alignString2, ind1, ind2, endInd2)
        # if the token in string2 is found in a nearby index in string1
        elif string2Tok[ind2] in string1Tok[ind1:endInd1]:
            alignString2, alignString1, ind2, ind1 = vecinityAlignmentMatch(string2Tok, string1Tok, alignString2,
                                                                            alignString1, ind2, ind1, endInd1)
        # if we want to try and match the most similar in each vecinity
        elif alignMostSimilar != False:
            alignString1, alignString2, ind1, ind2 = getMostSimilarAlignment(string1Tok, string2Tok, alignString1,
                                                                             alignString2, ind1, ind2, endInd1, endInd2)
        # if the token is nowhere to be found
        else:
            # add them to the aligned list
            alignString1.append(string1Tok[ind1])
            alignString2.append(string2Tok[ind2])
            # change both indices
            ind1 = ind1 + 1 if ind1 + 1 != len(string1Tok) else None
            ind2 = ind2 + 1 if ind2 + 1 != len(string2Tok) else None
    return alignString1, alignString2


def getcorrespondingTokensAndEditDist(string1, string2, caseSensitive=False):
    ''' given 2 similar strings, it detects for each token in string1
	the corresponding token in string 2. It returns a tuple of each
	correspondence and its edit distance '''
    errorCorrespList = []
    # replace repetition of space characters with a distinctive symbol
    for nbSpace in reversed(range(3, 10)):
        if u' ' * nbSpace in string1:
            string1 = string1.replace(u' ' * nbSpace, u' {0} '.format(u'¤*¤¤¤¤' * nbSpace))
        if u' ' * nbSpace in string2:
            string1 = string2.replace(u' ' * nbSpace, u' {0} '.format(u'¤*¤¤¤¤' * nbSpace))
    # tokenize (we don't use the naive regex tokenizer to avoid catching the  "-" and "'" and so on)
    string1Tok = string1.split(u' ')
    string2Tok = string2.split(u' ')
    # replace back the distinctive characters replacing the spaces with actual spaces
    string1Tok = [elem.replace(u'¤*¤¤¤¤', u' ') for elem in string1Tok]
    string2Tok = [elem.replace(u'¤*¤¤¤¤', u' ') for elem in string2Tok]
    # indicator of which one has greater length
    longer = 1 if len(string1Tok) >= len(string2Tok) else 2
    # order the objects
    main = list(string1Tok if longer == 1 else string2Tok)
    sub = list(string1Tok if longer == 2 else string2Tok)
    # first get rid of the exact matches
    mainTemp = list(main)
    main = [mainElem for mainElem in main if mainElem not in sub]
    sub = [subElem for subElem in sub if subElem not in mainTemp]
    # initiate the multiple tokens verificator
    joined = False
    # detect the corresponding element to each token
    for indexMain, mainElem in enumerate(main):
        # if the previous element was a
        if joined == u'main':
            joined = False
        else:
            leftInd = (indexMain - 3) if (indexMain - 3) >= 0 else 0
            rightInd = (indexMain + 3) if (indexMain + 3) < len(sub) else len(sub)
            # list the context window edit distance
            bestCandidate = (u'na', float(u'inf'))
            # join the main token with its main neighbour, in case in one case the tokens are separated in one set and joined in the other
            mainElemAndRightElem = u'{0} {1}'.format(mainElem, main[indexMain + 1]) if indexMain + 1 < len(
                main) else None
            # get the edit distance
            for indexSub, subElem in enumerate(sub):
                # get the edit distance for elements in the context window
                if indexSub in range(leftInd, rightInd):
                    # get the edit distance for potential tokens separated in THE MAIN set and joined in THE SUB set
                    if mainElemAndRightElem != None:
                        editDist = distance.edit_distance(mainElemAndRightElem, subElem)
                        # compare edit dist
                        if editDist <= bestCandidate[1]:
                            bestCandidate = (subElem, editDist, indexSub, mainElemAndRightElem)
                            joined = u'main'
                    # get the edit distance for potential tokens separated in THE SUB set and joined in THE MAIN set
                    if indexSub + 1 < len(sub) and indexSub + 1 < rightInd:
                        subElemAndRightElem = u'{0} {1}'.format(subElem, sub[indexSub + 1])
                        editDist = distance.edit_distance(mainElem, subElemAndRightElem)
                        # compare edit dist
                        if editDist <= bestCandidate[1]:
                            bestCandidate = (subElemAndRightElem, editDist, indexSub)
                            joined = u'sub'
                    # get the edit distance for each individual token coupled with a token present in the context window
                    editDist = distance.edit_distance(mainElem, subElem)
                    # get the best candidate using the edit distance between the main and sub elem
                    if editDist <= bestCandidate[1]:
                        bestCandidate = (subElem, editDist, indexSub)
                        joined = False
            # save the corresponding error candidate
            # if the best candidate is 2 main tokens
            if joined == u'main':
                errorCorrespList.append(tuple([bestCandidate[3], bestCandidate[0], bestCandidate[1]]))
            # if the best candidate is 1 token or 2 sub tokens
            else:
                errorCorrespList.append(tuple([mainElem, bestCandidate[0], bestCandidate[1]]))
            # pop the recently added element from sub
            if bestCandidate[1] != float(u'inf'):
                # delete 2 elements if the best candidate is 2 sub tokens
                if joined == u'sub':
                    sub.pop(bestCandidate[2] + 1)
                # delete the best candidate element from the sub set
                sub.pop(bestCandidate[2])
    # if there are still elements in the sub list
    for subElem in sub:
        errorCorrespList.append(tuple([u'na', subElem, float(u'inf')]))
    # return the list if the argument order is the same as the length order
    if longer == 1:
        return errorCorrespList
    # if not, we invert the order
    return [tuple([errorTuple[1], errorTuple[0], errorTuple[2]]) for errorTuple in errorCorrespList]
