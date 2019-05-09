#!/usr/bin/python
#-*- coding:utf-8 -*-


import os, sys, json, codecs, gzip, time
import pandas as pd

##################################################################################
# FOLDERS
##################################################################################

def emptyTheFolder(directoryPath, fileExtensionOrListOfExtensions=u'*'):
	'''
	Removes all files corresponding to the specified file(s) extension(s).
	If the fil estension is '*' the function will remove all files except
	the system files (ie: '.p', '.java', '.txt') and folders
	'''
	#we first delete the content of the folder to make place to the new content
	try:
		if type(fileExtensionOrListOfExtensions) is list:
			filelist = []
			for extension in fileExtensionOrListOfExtensions:
				fileExtensionList = [file for file in os.listdir(directoryPath) if file.endswith(".%s" %(fileExtensionOrListOfExtensions)) ]
				filelist = filelist + fileExtensionList
		#the '*' implies we want all files deleted
		elif fileExtensionOrListOfExtensions == u'*':
			filelist = [file for file in os.listdir(directoryPath)]
		else:
			#get rid of the dot if there is one
			fileExtensionOrListOfExtensions = fileExtensionOrListOfExtensions[1:] if fileExtensionOrListOfExtensions[0] == u'.' else fileExtensionOrListOfExtensions
			#make list of files finishong with  '.[format]'
			filelist = [file for file in os.listdir(directoryPath) if file.endswith(u".%s" %(fileExtensionOrListOfExtensions)) ]
		#we delete the files
		for file in filelist:
			os.remove(directoryPath + file)
	except OSError:
		pass


def getContentOfFolder(folderPath):
	'''
	Gets a list of all the files present in a specific folder
	'''
	return [file for file in os.listdir(folderPath)]


def goDeepGetFiles(folderPath, fileList=[], format=None):
	'''
	recusively looks into any subsolder of the given folder until it finds some files
	'''
	files = [u'{0}{1}'.format(folderPath, file) for file in os.listdir(folderPath) if os.path.isfile(u'{0}{1}'.format(folderPath, file))]
	if format != None:
		indexFormat = -1 * len(format)
		files = [ path for path in files if path[indexFormat:] == format ]
	#we stop going deep as soon as we find at least one file
	if len(files) == 0:
		subfolderContent = []
		for subfolderPath in [u'{0}{1}/'.format(folderPath, subF) for subF in os.listdir(folderPath) if not os.path.isfile(u'{0}{1}'.format(folderPath, subF))]:
			subfolderContent = goDeepGetFiles(subfolderPath, subfolderContent, format)
		return fileList + subfolderContent
	finalList = fileList + files
	return finalList


def getIntersectionOf2Folders(aFolder, bFolder):
	'''
	Browses the files contained in 2 folders and returns a 
	list of those files present in both folders 
	It DOES NOT take into account the extensions
	'''
	aFileList = [file for file in os.listdir(aFolder)]
	bFileList = [file for file in os.listdir(bFolder)]
	intersectionFiles = []
	for fileA in aFileList:
		for fileB in bFileList:
			if fileA.split('.')[0] == fileB.split('.')[0]:
				intersectionFiles.append(tuple([fileA, fileB]))
				break
	return intersectionFiles


def createEmptyFolder(folderPath):
	""" given a non existing folder path, creates the necessary folders so the path exists """
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)


##################################################################################
#FILES
##################################################################################

def createEmptyFile(filePath, headerLine=None):
	'''
	we dump an empty string to make sure the file is empty
	and we return the handle to the ready to append file
	'''
	openFile = codecs.open(filePath, u'w', encoding=u'utf8')
	openFile.write(u'')
	openFile.close()
	openFile = open(filePath, 'a', encoding='utf8', buffering=1)
	#if needed we add a header
	if headerLine != None:
		openFile.write(u'{0}\n'.format(headerLine))
	return openFile


def getLastLineIndexOfExistingFile(filePath):
	'''
	opens an existing file and returns the index of the last line
	useful if, for example, we want to know where we left off in an append file
	'''
	if theFileExists(filePath, nameOfFile=None, fileExtension=None) == False:
		return None
	with codecs.open(filePath, 'r', encoding='utf8') as openedFile:
		return len(openedFile.readlines()) - 1 #we count starting with 0


def theFileExists(directoryOrWholeFilePath, nameOfFile=None, fileExtension=None):
	'''
	Returns false if the file does not exists at the directory
	and returns true if the file exists
	'''
	import utilsString
	#if the directory path is actually the file path
	if nameOfFile == None and fileExtension == None:
		return os.path.isfile(directoryOrWholeFilePath)
	#if the path is correctly written at the end
	if directoryOrWholeFilePath[-1] !=u'/':
		directoryOrWholeFilePath = u'%s/' %(directoryOrWholeFilePath)
	#all extensions
	if fileExtension == None:
		filelist = os.listdir(directoryOrWholeFilePath)
		for file in filelist:
			splittedFileName = file.split('.')
			#if there was more than one '.'
			if len(splittedFileName) > 2:
				splittedFileName = ['.'.join(splittedFileName[:len(splittedFileName)-1])]
			#if the file exists
			for nb in range(100):
				#for python 2
				try:
					strNb = unicode(nb)
				#for python 3
				except NameError:
					strNb = str(nb)
				if u'%s_%s' %(nameOfFile, strNb) == utilsString.toUtf8(splittedFileName[0]) or u'%s_%s' %(noTroublesomeName(nameOfFile), strNb) == utilsString.toUtf8(splittedFileName[0]):
					return True
		#if the file never appeared
		return False
	#exclusive extension
	else:
		return os.path.isfile(u'%s%s.%s' %(directoryOrWholeFilePath, nameOfFile, fileExtension))


def readAllLinesFromFile(pathToFile, noNewLineChar=False, asStringNotUnicode=False):
	'''
	Returns a list containing all the lines in the file
	'''
	#as unicode
	if asStringNotUnicode == False:
		with codecs.open(pathToFile, 'r', encoding='utf8') as openedFile:
			linesList = openedFile.readlines()
		if noNewLineChar == True:
			linesList = [(e.replace(u'\n', u'').replace(u'\r', u'')) for e in linesList]
	#as simple string
	else: 
		with open(pathToFile, 'r') as openedFile:
			linesList = openedFile.readlines()
		if noNewLineChar == True:
			linesList = [(e.replace('\n', '').replace('\r', '')) for e in linesList]
	#if linesList is None we return and empty list
	if linesList == None:
		linesList = []
	return linesList


def readGzipFile(pathToGzipFile):
	''''''
	with gzip.open(pathToGzipFile, u'rb') as openedFile:
		return openedFile.readlines()


def openJsonFileAsDict(pathToFile):
	'''	loads a json file and returns a dict '''
	import json
	with codecs.open(pathToFile, u'r', encoding=u'utf8') as openedFile:
		return json.load(openedFile)


def convertJsonLineToDict(jsonFileStringLine):
	'''
	Given a line (string) from a json file as argument,
	we try to return a dict corresponding to said line,
	otherwise, we return None.
	Useful if the json file has one json dict per line
	and we must read line by lane and transform each one
	'''
	try:
		jsonLine = json.loads(jsonFileStringLine)
		#we dump each job title
		return jsonLine
	except ValueError:
		return None


def dumpRawLines(listOfRawLines, filePath, addNewline=True, rewrite=True): 
	'''
	Dumps a list of raw lines in a a file 
	so the Benchmark script can analyse the results
	'''
	folderPath = u'/'.join((filePath.split(u'/'))[:-1]+[''])
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)
	#we dump an empty string to make sure the file is empty
	if rewrite == True:
		openedFile = codecs.open(filePath, 'w', encoding='utf8')
		openedFile.write('')
		openedFile.close()
	openedFile = codecs.open(filePath, 'a', encoding='utf8')
	#we dump every line of the list
	for line in listOfRawLines:
		if addNewline == True:
			openedFile.write(u'%s\n' %(line))
		else:
			openedFile.write(u'%s' %(line))
	openedFile.close()
	return


def dumpDictToJsonFile(aDict, pathOutputFile='./dump.json', overwrite=False):
	'''
	save dict content in json file
	'''
	import json
	if overwrite == False:
		#to avoid overwriting the name may change
		pathOutputFile = safeFilePath(pathOutputFile)
	#dumping
	with codecs.open(pathOutputFile, u'wb', encoding=u'utf8') as dictFile:
		dictFile.write('')
		json.dump(aDict, dictFile)
	return 


def deleteAFile(filePath):
	""" given a path to a file simply deletes it if it exists """
	if theFileExists(filePath):
		os.remove(filePath)
		return True
	return False


def deleteTheFile(directoryPath, nameOfFile, fileExtension):
	'''
	Removes all files corresponding to the given name and the specified file(s) extension(s).
	'''	
	import utilsString
	#if the path is correctly written at the end
	if directoryPath[-1] !=u'/':
		directoryPath = u'%s/' %(directoryPath)
	#preparing to dump into file
	for char in [u' ', u'_', u'/', u'\\', u':', u'…', u'。', u';', u',', u'.', u'>', u'<', u'?', u'!', u'*', u'+', u'(', u')', u'[', u']', u'{', u'}', u'"', u"'", u'=']:
		nameOfFile = nameOfFile.replace(char, u'_')
	#we change the iri code if there is one
	if u'%' in nameOfFile or '%' in nameOfFile:
		nameOfFile = iriToUri(nameOfFile)
	#we make a list of all the possible names of the files to be deleted
	fileNamesToBeDeleted = []
	namePlusExt = u'%s.%s' %(nameOfFile, fileExtension)
	fileNamesToBeDeleted.append(namePlusExt)
	fileNamesToBeDeleted.append(noTroublesomeName(namePlusExt))
	for nb in range(10):
		#for python 2
		try:
			strNb = unicode(nb)
		#for python 3
		except NameError:
			strNb = str(nb)
		fileNamesToBeDeleted.append(u'%s_%s.%s' %(nameOfFile, strNb, fileExtension))
		fileNamesToBeDeleted.append(u'%s_%s.%s' %(noTroublesomeName(nameOfFile), strNb, fileExtension))
	#we make a list of all extension-like 
	try:
		#we catch all corresponding names
		if type(fileExtension) is str:
			filelist = [utilsString.toUtf8(file) for file in os.listdir(directoryPath) if file.endswith(".%s" %(fileExtension)) ]
		elif type(fileExtension) or unicode:	
			filelist = [utilsString.toUtf8(file) for file in os.listdir(directoryPath) if file.endswith(".%s" %(fileExtension.encode('utf8'))) ]		
	except OSError:
		filelist = []
	#we make a list of the intersection between the 2 lists
	intersection = list(set(fileNamesToBeDeleted) & set(filelist))
	#we delete the files
	for file in intersection:
		os.remove(directoryPath + file)
	return


def deleteFileContent(pathToFile, openAnAppendFile=False):
	'''
	Deletes a file's content without deleting the file by 
	writing an empty string into it.
	It returns the object corresponding to the file.
	If the openAnAppendFile is not False, it will return the
	object corresponding to an openend and append file
	'''
	openedFile = codecs.open(pathToFile, 'w', encoding='utf8')
	openedFile.write('')
	openedFile.close()
	if openAnAppendFile != False:
		openedFile = codecs.open(pathToFile, 'a', encoding='utf8')
	return openedFile


def appendLineToFile(stringLine, filePath, addNewLine=True):
	if theFileExists(filePath) != True:
		with open(filePath, 'w') as emptyFile:
			emptyFile.write(u'')
	if addNewLine == True:
		stringLine = u'{0}\n'.format(stringLine)
	with open(filePath, 'a') as file:
		file.write(stringLine)


def countLines(openedFile):
	for i, l in enumerate(openedFile):
		pass
	return i + 1


##################################################################################
#NAMES AND PATHS
##################################################################################

def noTroublesomeName(string):
	'''
	Transforms the name into a non-troublesome name
	'''
	for char in [u' ', u' ', u'_', u'/', u'\\', u':', u';', u',', u'.', u'>', u'<', u'?', u'!', u'*', u'+', u'(', u')', u'[', u']', u'{', u'}', u'"', u"'", u'=']:
		string = string.replace(char, u'_')
	#we change the iri code if there is one
	if u'%' in string:
		string = iriToUri(string)
	return string
	

def noTroublesomeNameAndNoDoubleUnderscore(string):
	'''
	Transforms the name into a non-troublesome name
	'''
	for char in [u' ', u' ', u'_', u'/', u'\\', u':', u';', u',', u'.', u'>', u'<', u'?', u'!', u'*', u'+', u'(', u')', u'[', u']', u'{', u'}', u'"', u"'", u'=']:
		string = string.replace(char, u'_')

	#we change the iri code if there is one
	if u'%' in string:
		string = iriToUri(string)
		#if there is still a '%' char we replace it
		if u'%' in string:
			string = string.replace(u'%', u'_') 

	if len(string) > 0:
		#we replace all double underscore by a single underscore
		if u'__' in string:
			string.replace(u'__', u'_')
		#if there is an underscore at the begining and at the end of the name, we delete it
		if string[0] == u'_':
			string = string[1:]
		if len(string) > 0 and string[-1] == u'_':
			string = string[:-1]
	return string


def safeFilePath(outputFilePath):
	fileName = outputFilePath.split(u'/')[-1]
	folderPath = outputFilePath.replace(fileName, u'')
	if u'.' not in fileName:
		fileExtension = None
	else:
		fileExtension = fileName.split(u'.')[-1]
		fileName = fileName.replace(u'.%s' %(fileExtension), u'')
	nb = 1
	if theFileExists(folderPath, fileName, fileExtension) == True:
		fileName = u'%s_%s' %(fileName, nb)
		while theFileExists(folderPath, fileName, fileExtension) == True:
			fileName = fileName.replace(u'_%s' %(str(nb)), u'_%s' %(str(nb+1)))
			nb += 1
	return u'%s%s.%s' %(folderPath, fileName, fileExtension)


##################################################################################
#TIME COUNTING
##################################################################################

def countTime(startingTime=None):
	if startingTime == None:
		return time.time()
	return time.time() - startingTime


##################################################################################
#USER INTERACTION VIA THE TERMINAL
##################################################################################

def moveUpAndLeftNLines(n, slowly=True):
	'''
	Moves up N lines in the terminal 
	at the starting point of the line
	so text can be rewritten over (dynamically)
	(use of carriage return \r and ansi code for up \u001b[#intNumber#A )
	'''
	sys.stdout.write("\r") #move to the beguinning of the line	
	sys.stdout.write(" "*100) #writes a blank string
	sys.stdout.write("\r") #move to the beguinning of the line	
	for e in range(n):
		sys.stdout.write(u"\u001b[" + str(1) + "A") # Move up n lines
		sys.stdout.write(" "*100) #writes a blank string
		sys.stdout.write("\r") #move to the beguinning of the line
	sys.stdout.flush()
	if slowly == True:
		import time
		time.sleep(0.4)


##################################################################################
#DATAFRAME FUNCTIONS
##################################################################################

def getDataFrameFromArgs(df1arg, df2arg=None, header=True):
	'''
	we chech if 'df1arg' and 'df2arg' are string paths or pandas dataframes
	'''
	#df1
	if type(df1arg) != str: # or type(df1arg) != unicode:
		df1 = df1arg
	else:
		#with header as df.columns
		if header == True:
			df1 = pd.read_csv(df1arg, sep=u'\t')
		#without header (useful for series instead of df)
		else:
			df1 = pd.read_csv(df1arg, sep=u'\t', header=None)
	#df2
	if df2arg is None:
		return df1
	elif type(df2arg) != str: # or type(df2arg) != unicode:
		df2 = df2arg
	else:
		#with header as df.columns
		if header == True:
			df2 = pd.read_csv(df2arg, sep=u'\t')
		#without header (useful for series instead of df)
		else:			
			df2 = pd.read_csv(df2arg, sep=u'\t', header=None)
	return df1, df2 


def dumpDataFrame(df, dfPath):
	'''  '''
	df.to_csv(dfPath, sep='\t', index=False)