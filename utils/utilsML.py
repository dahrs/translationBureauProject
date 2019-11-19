#!/usr/bin/python
#-*- coding:utf-8 -*- 

import pickle
import fastText
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

import utilsOs, utilsString


##################################################################################
# MODEL HANDLING
##################################################################################

def dumpModel(model, modelFilePath):
	'''
	Using pickle.
	:param model: sklearn machine learning model
	:param modelFilePath: path to the output file
	:return: dumped model
	'''
	with open(modelFilePath, u'wb') as modelFile:
		pickle.dump(model, modelFile)


def loadModel(modelFilePath):
	'''
	Using pickle.
	:param modelFilePath: path to the input file
	:return: load model
	'''
	with open(modelFilePath, u'rb') as modelFile:
		pickleModel = pickle.load(modelFile)
	return pickleModel


##################################################################################
# MAKE AND MANUPULATE CONFUSION MATRICES
##################################################################################


def transformScoreToBool(sc):
	# if the pred and real scores are not boolean transform into boolean
	if type(sc) in [int, np.int64]:
		if sc in [0, 1]:
			sc = True if sc == 1 else False
		else:
			raise TypeError("the scores must be binary. only 0 and 1 are accepted")
	elif type(sc) is float:
		sc = True if sc == 1.0 else False
	else:
		raise TypeError("the type is neither a bool, int or float")
	return sc


def populateBinaryConfMatrix(pred, real, confMatrix=None):
	if confMatrix is None:
		confMatrix = []
	# when the matrix is empty
	if len(confMatrix) == 0:
		content = np.zeros(shape=(2, 2))
		confMatrix = pd.DataFrame(content, index=[u'pred pos', u'pred neg'], columns=[u'real pos', u'real neg'])
	# if the pred and real scores are not boolean transform into boolean
	pred = transformScoreToBool(pred)
	# compare and populate
	if pred == real:
		if pred == False:
			# true negative
			confMatrix[u'real neg'][u'pred neg'] += 1
		else:
			# true positive
			confMatrix[u'real pos'][u'pred pos'] += 1
	else:
		if pred == False:
			# false negative
			confMatrix[u'real pos'][u'pred neg'] += 1
		else:
			# false positive
			confMatrix[u'real neg'][u'pred pos'] += 1
	return confMatrix


##################################################################################
# MAKE NUMPY OBJECTS
##################################################################################

def fromTsvToMatrix(path, justTheNFirstColumns='all'):
	""" given the path to a tsv file of scores (with no header), transforms them into a numpy array """
	listOfLists = []
	with open(path) as heurFile:
		# get line
		ln = heurFile.readline()
		while ln:
			lnList = ln.replace(u'\n', u'').replace(u'na', u'-1.0').split(u'\t')
			if lnList != '':
				# take all the columns
				if justTheNFirstColumns == u'all':
					listOfLists.append([float(sc) for sc in lnList])
				else:
					listOfLists.append([float(sc) for sc in lnList[:justTheNFirstColumns]])
				# take only the n first columns
			# next line
			ln = heurFile.readline()
	return np.asarray(listOfLists)


##################################################################################
# DIVISION IN TEST, TRAIN AND VALIDATION SETS
##################################################################################

def makeTrainTestValidSetsFromTsv(origDf, ratioSizes=None, outputFolderPath=None):
	""" given the dataframe with the whole original input, returns 2 or 3 distinct
	dataframes containing a randomly selected elements corresponding to the given 
	ratio sizes. The ratioSizes order must be: TRAIN - TEST - VALIDATION"""
	if outputFolderPath != None:
		outputFolderPath = u'{0}/'.format(outputFolderPath) if outputFolderPath[-1] != u'/' else outputFolderPath
	if ratioSizes is None:
		ratioSizes = [0.5, 0.3, 0.2]
	#get the data frame
	origDf = utilsOs.getDataFrameFromArgs(origDf)
	#get the actual sizes from the ratios
	nSizes = [ int(r*len(origDf)) for r in ratioSizes ] #we avoid using the argument "frac" from "pd.sample" function
	#train-test set
	trainDf = origDf.sample(n=nSizes[0], replace=False) #train set
	remainingDf = origDf.iloc[~origDf.index.isin(trainDf.index)]
	testDf = remainingDf.sample(n=nSizes[1], replace=False) #test set
	#determine if it must return a train-test set or a train-validation-test set
	if len(nSizes) == 2:
		#dumping
		if outputFolderPath != None:
			trainDf.to_csv(u'{0}train.tsv'.format(outputFolderPath), sep='\t', index=False)
			testDf.to_csv(u'{0}test.tsv'.format(outputFolderPath), sep='\t', index=False)
		return trainDf, testDf
	#train-validation-test set
	elif len(nSizes) == 3: 
		remainingDf = remainingDf.iloc[~remainingDf.index.isin(testDf.index)]
		validDf = remainingDf.sample(frac=nSizes[2], replace=False)
		#dumping
		if outputFolderPath != None:
			trainDf.to_csv(u'{0}train.tsv'.format(outputFolderPath), sep='\t', index=False)
			testDf.to_csv(u'{0}test.tsv'.format(outputFolderPath), sep='\t', index=False)
			validDf.to_csv(u'{0}validation.tsv'.format(outputFolderPath), sep='\t', index=False)
		return trainDf, testDf, validDf
	raise IndexError('The number of ratio sizes is neither 2 nor 3. We require 2 ratio sizes to return a train and test set and 3 to return a train, test and validation sets.')


def makeSetsForCrossVal(origDf, nbSegmentations=10, randomize=True, outputFolderPath=None):
	''' given a dataframe, returns subsets of said dataframe in order to 
	be used for cross-validation '''
	listOfDfs = []
	outputFolderPath = u'{0}/'.format(outputFolderPath) if outputFolderPath[-1] != u'/' else outputFolderPath
	#get the data frame
	origDf = utilsOs.getDataFrameFromArgs(origDf)
	#if the nb of segmentation is a ratio (e.g., 0.25 for 25%), we transform it into an int nb of segmentations
	if type(nbSegmentations) is float and str(nbSegmentations)[0] == '0':
		nbSegmentations = int(1/nbSegmentations)
	#get the size of each segment
	segmSize = float(len(origDf))/float(nbSegmentations)
	#shuffle randomly the dataframe
	if randomize == True:
		origDf = origDf.sample(frac=1.0, replace=False)
	#populate the list with the segmented dataframes
	for n in range(1, nbSegmentations):
		listOfDfs.append( origDf.iloc[ int(segmSize*(n-1)):int(segmSize*n) ] )
	#append the last segment, containing the remaining elements of the df, this number 
	#might slightly vary from the expected and uniform size of the other segments
	listOfDfs.append( origDf.iloc[ int(segmSize*(n)): ] )
	#dump the dataframes
	if outputFolderPath != None:
		utilsOs.emptyTheFolder(outputFolderPath, fileExtensionOrListOfExtensions=u'tsv')
		for n, df in enumerate(listOfDfs):
			df.to_csv(u'{0}crossValidation{1}.tsv'.format(outputFolderPath, n), sep='\t', index=False)
	return listOfDfs


def unifyListOfTestSetsIntoOne(listOfTestFiles, outputUnifiedFilePath=None):
	''' given a list of paths to files, unites them into a single one '''
	dataframes = []
	#open the dataframes and append them to the list
	dataframes = [ getDataFrameFromArgs(dfPath, header=False) for dfPath in listOfTestFiles ]
	#concatenate them
	unifiedDf = pd.concat(dataframes, ignore_index=True, sort=False)
	#dump the result
	if outputUnifiedFilePath != None:
		dumpDataFrame(unifiedDf, outputUnifiedFilePath, header=False)
	#return the unified dataframe
	return unifiedDf


##################################################################################
# TOKEN DATASETS FOR MACHINE LEARNING MODELS
##################################################################################

def makeSimpleTokenDatasetFromTsv(tsvInputFilePath, originalStringColumnName, correctStringColumnName, outputFilePath,
								  outputOriginalColumnName=u'input', outputCorrectColumnName=u'output',
								  caseSensitive=True):
	''' takes a tsv file, naively space-char tokenizes the content in the original 
	and correct columns, makes correspond the original and correct tokens and dumps 
	each token in a row of an output tsv file '''
	total = 0
	nonErrors = 0
	#create empty output file
	outputFile = utilsOs.createEmptyFile(outputFilePath, u'{0}\t{1}\n'.format(outputOriginalColumnName, outputCorrectColumnName))
	#browse the input file line by line
	with open(tsvInputFilePath, u'r', encoding=u'utf8') as inputFile:
		#header line
		headerList = (inputFile.readline().replace(u'\n', u'')).split(u'\t')
		#find the column indexes corresponding to the column names 
		originalIndex = headerList.index(originalStringColumnName) if originalStringColumnName in headerList else 0
		correctIndex = headerList.index(correctStringColumnName) if correctStringColumnName in headerList else 1
		#first line
		line = inputFile.readline()
		while line:
			#case sensibility
			if caseSensitive != True:
				line = line.lower()
			#get the list of elements in the line
			lineList = (line.replace(u'\n', u'')).split(u'\t')
			#get the tokens in the original string (in this case: tokens = space char separated elements)
			originalTokens = lineList[originalIndex].split(u' ')
			#get the erratic correspondences between the original string and the correct string
			errorTokens = utilsString.getcorrespondingTokensAndEditDist(lineList[originalIndex], lineList[correctIndex], caseSensitive)
			for origToken in originalTokens:
				#write the non problematic tokens
				if origToken not in [tupl[0] for tupl in errorTokens]:
					outputFile.write( u'{0}\t{1}\n'.format(origToken, origToken) )
					nonErrors += 1
				#write the problematic ones
				for tupl in errorTokens:
					outputFile.write( u'{0}\t{1}\n'.format(tupl[0], tupl[1]) )
				total +=1 
			line = inputFile.readline()
	print(nonErrors, total, nonErrors/total)
	return nonErrors, total


##################################################################################
# EMBEDDING NEAREST NEIGHBOURS
##################################################################################

class ftTools:
	''' fastText aid tools '''
	def __init__(self):
		return None

	def getFtMatrix(self, ft_model, ft_matrix):
		''' gets a fasttext matrix containing the vectors of the words in the model '''
		if ft_matrix is None:
			words = ft_model.get_words()
		#open the path to the json list of the most popular n words and use them to populate the ft_matrix
		elif type(ft_matrix) is str:
			import json
			#open the list of popular words
			with open(ft_matrix, u'r') as openedFile:
				words = json.load(openedFile)
		#make the fasttext matrix
		ft_matrix = np.empty((len(words), ft_model.get_dimension()))
		for i, word in enumerate(words):
			ft_matrix[i,:] = ft_model.get_word_vector(word)
		return ft_matrix


class FastTextNN:
	''' based on one comment in https://github.com/facebookresearch/fastText/issues/384 
	model = fastText.load_model(u'/data/rali5/Tmp/alfonsda/fasttextVectorModels/wiki.fr.bin')
	n = FastTextNN()
	n.nearest_words('toil') '''
	
	def __init__(self, ft_model=None, ft_matrix=None):
		if ft_model == None:
			ft_model = fastText.load_model(u'/data/rali5/Tmp/alfonsda/fasttextVectorModels/wiki.fr.bin')
		self.ft_model = ft_model
		self.ft_words = ft_model.get_words()
		self.word_frequencies = dict(zip(*ft_model.get_words(include_freq=True)))
		self.ft_matrix = ftTools().getFtMatrix(ft_model, ft_matrix)

	'''ftClass = FastTextNN(ft_matrix=u'./utilsString/tokDict/listOfMostCommon10000tok.json')
	liste = ftClass.nearestWords(u'toiletdte', n=10, word_freq=None)
	print(liste)'''
	
	def findNearestNeighbor(self, query, vectors, n=10,  cossims=None):
		"""
		based on one comment in https://github.com/facebookresearch/fastText/issues/384 
		query is a 1d numpy array corresponding to the vector to which you want to
		find the closest vector
		vectors is a 2d numpy array corresponding to the vectors you want to consider

		cossims is a 1d numpy array of size len(vectors), which can be passed for efficiency
		returns the index of the closest n matches to query within vectors and the cosine similarity (cosine the angle between the vectors)
		"""
		if cossims is None:
			cossims = np.matmul(vectors, query, out=cossims)

		norms = np.sqrt((query**2).sum() * (vectors**2).sum(axis=1))
		cossims = cossims/norms
		result_i = np.argpartition(-cossims, range(n+1))[1:n+1]
		return list(zip(result_i, cossims[result_i]))


	def nearestWords(self, word, n=10, word_freq=None):
		'''based on one comment in https://github.com/facebookresearch/fastText/issues/384 '''
		result = self.findNearestNeighbor(self.ft_model.get_word_vector(word), self.ft_matrix, n=n)
		if word_freq:
			return [(self.ft_words[r[0]], r[1]) for r in result if self.word_frequencies[self.ft_words[r[0]]] >= word_freq]
		else:
			return [(self.ft_words[r[0]], r[1]) for r in result]


##################################################################################
# FEED FORWARD NEURAL NETWORK
##################################################################################

class FeedforwardNeuralNetModel(nn.Module):
	""" from  www.deeplearningwizard.com/deep_learning/practical_pytorch/pytorch_feedforward_neuralnetwork/ """
	def __init__(self, input_dim, hidden_dim, output_dim):
		super(FeedforwardNeuralNetModel, self).__init__()
		# Linear function
		self.fc1 = nn.Linear(input_dim, hidden_dim)
		# Non-linearity
		self.sigmoid = nn.Sigmoid()
		# Linear function (readout)
		self.fc2 = nn.Linear(hidden_dim, output_dim)

	def forward(self, x):
		# Linear function  # LINEAR
		out = self.fc1(x)
		# Non-linearity  # NON-LINEAR
		out = self.sigmoid(out)
		# Linear function (readout)  # LINEAR
		out = self.fc2(out)
		return out


