#!/usr/bin/python
#-*- coding:utf-8 -*-

import utilsOs
from utilsGraph import getDataFrameFromArgs
from nltk.metrics import distance
from tqdm import tqdm
import pandas as pd


##################################################################################
#RAW DATA
##################################################################################

def analyseNodeListStrDistance(nodeListPath, outputPath=None):
	'''
	analyses the nodes in the node list and returns the stats 
	concerning the similarities between node string labels
	'''
	import multiprocessing as mp

	pool = mp.Pool(processes=4) 
	nodeSimilarsDict = {1:{}, 2:{}, 3:{}}
	nodeSetJobTitles = set()
	nodeSetSkills = set()
	#put the node Labels in a set
	with open(nodeListPath) as nodeFile:
		nodeData = nodeFile.readline()
		while nodeData:
			#get the data for each row
			nodeDataList = nodeData.split(u'\t')
			#we make sure we are not in the header
			if nodeDataList[0] != u'Id':
				#save the node id/label in a set
				if u'__s' in nodeDataList[0]:
					nodeSetJobTitles.add(nodeDataList[1])
				elif u'__t' in nodeDataList[0]:
					nodeSetSkills.add(nodeDataList[1])
			#get next line
			nodeData = nodeFile.readline()

	#get the number and list of N-similar nodes for each Job title node
	jobtitleResults = [pool.apply_async(getElemSimilarByEditDistanceOfN, args=(original, nodeSetJobTitles, nodeSimilarsDict, True, u'{0}__s'.format(original))) for original in nodeSetJobTitles]
	#get the number and list of N-similar nodes for each skill node
	skillResults = [pool.apply_async(getElemSimilarByEditDistanceOfN, args=(original, nodeSetSkills, nodeSimilarsDict, True, u'{0}__t'.format(original))) for original in nodeSetSkills]
	
	#merge all the obtained dict together
	def merge_two_dicts(x, y):
		w = x.copy()
		for nb in range(1,4):
			z = w[nb].copy() # start with x's keys and values
			z.update(y[nb]) # modifies z with y's keys and values & returns None
			w[nb] = z
		return w
	#prepare the objects containing the results
	dictResults = {1:{}, 2:{}, 3:{}}
	for dictToBeAdded in tqdm(jobtitleResults+skillResults):
		dictResults = merge_two_dicts(dictResults, dictToBeAdded.get())

	#dump into a json file
	if outputPath != None:
		utilsOs.dumpDictToJsonFile(dictResults, outputPath, overwrite=True)
	#get the summary of the results
	countResultStrDistanceDict(dictResults)
	return dictResults


def countResultStrDistanceDict(dictResults):
	'''
	counts the results in the str distance dict
	'''
	if type(dictResults) is str:
		dictResults = utilsOs.openJsonFileAsDict(dictResults)
	for keyNb, neighDict in dictResults.items():
		print(u'Edition distance of {0}:'.format(keyNb))
		print(u'\tNb of nodes with neighbours of distance {0}: {1}'.format(keyNb, str(len(neighDict))) )
		totalNeigh = 0
		for nodeKey, neighboursList in neighDict.items():
			totalNeigh += len(neighboursList)
		print(u'\t\tMean nb of neighbours: {0}'.format(float(totalNeigh)/float(len(neighDict))))


##################################################################################
#STRING STATS
##################################################################################

def tokenDistribution(listOfStrings):
	import utilsString
	distribDict = {}
	base = [0, []]	
	for line in listOfStrings:
		line = line.lower()
		tokens = utilsString.naiveRegexTokenizer(line, caseSensitive=False, eliminateEnStopwords=True)
		value = distribDict.get(len(tokens), list(base))
		if line not in value[1]:
			value[0] += 1
			value[1].append(line)
			distribDict[len(tokens)] = value
	return distribDict


def getElemSimilarByEditDistanceOfN(original, similarCandidatesList, nodeSimilarsDict={1:{}, 2:{}, 3:{}}, lowerCase=True, dictKey=None):
	'''
	returns the list of elements having n or less distance score (excluding 0)
	the n max distance is given by the keys of the dict
	(the function is not N exclusive but n or less)
	Uses levenshtein distance (but could be augmented with other distances)
	'''
	dictKeys = sorted(nodeSimilarsDict.keys(), reverse=True)
	if dictKey == None:
		dictKey = original
	#we look at each candidate
	for candidate in tqdm(similarCandidatesList):
		#lowerCase the candidate and original
		if lowerCase == True:
			compareCandidate = str(candidate).lower()
			compareOriginal = str(original).lower()
		#if we maintain the uppercase
		else:
			compareCandidate = str(candidate)
		#if the distance is inferior to n and different from 0
		levenshteinDistance = distance.edit_distance(compareOriginal, compareCandidate)
		if levenshteinDistance <= dictKeys[0] and levenshteinDistance != 0:
			#add the candidate to all the corresponding sets
			for nMax in dictKeys:
				#add the candidate to each set where it's smaller than the nmax
				if levenshteinDistance <= nMax:
					#add the original jobtitle to the dict if it's not there
					try:
						#add the data to the dict
						nodeSimilarsDict[nMax][dictKey].append(candidate)
					except KeyError:
						#populate the slot with empty list
						nodeSimilarsDict[nMax][dictKey] = list()
						#add the data to the dict
						nodeSimilarsDict[nMax][dictKey].append(candidate)
	return nodeSimilarsDict


##################################################################################
#DATAFRAMES
##################################################################################

def dataframesIntersection(tsvFile1Path, tsvFile2Path, listOfIntersectingColumnNames, outputFilePath=None, lowerCase=True):
	'''
	returns the exact intersection between 2 dataframes and some statistical data
	in dict form: 
		- size of intersection
		- size of df1
		- ratio of intersection according to df1
		- size of df2
		- ratio of intersection according to df2
	'''
	import pandas as pd
	from utilsGraph import getDataFrameFromArgs
	#get the dataframes
	df1, df2 = getDataFrameFromArgs(tsvFile1Path, tsvFile2Path)
	#get their size
	sizeDf1 = len(df1)
	sizeDf2 = len(df2)
	#make sur the name of the column of columns to intersect are in a list
	if listOfIntersectingColumnNames is str:
		listOfIntersectingColumnNames = [listOfIntersectingColumnNames]
	#lowercase the values in the intersectable columns before the intersection
	for columnName in listOfIntersectingColumnNames:
		#lowercase strings
		try:
			df1[columnName] = df1[columnName].str.lower()
			df2[columnName] = df2[columnName].str.lower()
		#if it's not a string, then no need to lowercase
		except AttributeError:
			pass
	#drop the possible doubles we might have created after lowercasing
	for columnName in listOfIntersectingColumnNames:
		df1 = df1.drop_duplicates(subset=columnName)
		df2 = df2.drop_duplicates(subset=columnName)
	#make the intersection
	intersectDf = pd.merge(df1, df2, how='inner', on=listOfIntersectingColumnNames)
	#dump
	if outputFilePath != None:
		intersectDf.to_csv(outputFilePath, sep='\t', index=False)
	return intersectDf, {u'intersection size': len(intersectDf), u'df1 size': sizeDf1, u'intersect-df1 ratio': float(len(intersectDf))/float(sizeDf1), u'df2 size': sizeDf2, u'intersect-df2 ration': float(len(intersectDf))/float(sizeDf2)}


def diffBtw2Dataframes(df1, df2, caseSensitive=True):
	'''
	opens two dataframes and analyzes the difference and points in common
	from the headers to the content
	'''
	# if df1 and df2 are paths, returns the dataframes
	df1, df2 = getDataFrameFromArgs(df1, df2)
	#classify according to which df is larger, we place the larger df in the df2 variable and the smaller in df1
	df1, df2 = (df2, df1)if len(df1) > len(df2) else (df1, df2)
	#if case sensitive is false, lowercase it all
	if caseSensitive != True:
		df1.columns = map(str.lower, df1.columns)
		df1 = df1.apply(lambda x: x.astype(str).str.lower())
		df2.columns = map(str.lower, df2.columns)
		df2 = df2.apply(lambda x: x.astype(str).str.lower())
	#print header column names in common
	commonColumns = [c for c in list(df1) if c in list(df2)]
	print(u'0 - header column names in common: {0}'.format(commonColumns))
	#print header column names not in common
	divergentColumns = [c for c in list(df1) if c not in list(df2)] + [c for c in list(df2) if c not in list(df1)]
	print(u'1 - header column names NOT in common: {0}'.format(divergentColumns))
	#identical rows in both dfs (for common columns)
	commonDf = pd.merge(df1, df2, how='inner', on=commonColumns)
	commonDf.dropna(inplace=True) #drop empty rows
	print(u'2 - nb of rows with common values for both dataframes (in common columns): {0}/{1} (ratio: {2})'.format( len(commonDf), len(df2), (float(len(commonDf))/float(len(df2))) ))
	#identical values in both dfs (column by column)
	for indexColumn, columnName in enumerate(commonColumns):
		#it's easier to intersect pandas.series rather than dataframes (to avoid index mishaps)
		commonInterseption = list(map(lambda r: r in df1[columnName], df2[columnName]))
		print(u'\t2.{0} - nb of rows with common values on the column "{1}" (for both dataframes) : {2}/{3} (ratio: {4})'.format( indexColumn, columnName, len(commonInterseption), len(df2), (float(len(commonInterseption))/float(len(df2))) ))
	#divergent rows in both dfs (for common columns) #supposing there are 2 columns in common
	###divergentDf2 = df2.loc[~df2[commonColumns[0]].isin(commonDf[commonColumns[0]]) & ~df2[commonColumns[1]].isin(commonDf[commonColumns[1]])]
	###divergentDf2.to_csv(u'./divergent.tsv', sep='\t', index=False)
	###commonDf.to_csv(u'./common.tsv', sep='\t', index=False)


##################################################################################
#DIAGRAMS
##################################################################################

'''Plotting methods allow for a handful of plot styles other than the default Line plot. 
These methods can be provided as the kind keyword argument to plot(). These include:
‘bar’ or ‘barh’ for bar plots
‘hist’ for histogram
‘box’ for boxplot
‘kde’ or 'density' for density plots
‘area’ for area plots
‘scatter’ for scatter plots
‘hexbin’ for hexagonal bin plots
‘pie’ for pie plots'''


def plotDictAsBarChart(dictOfData, xLabel, yLabel, barWidth=0.85, rgbColor=[0.1,0.2,1.0,0.3,0.4,1.0,0.5,0.6,1.0,0.7,0.8,1.0,0.9,1.0], vertical=True, legend=False):
	'''
	When given a dict of data the function transforms it in a dataframe 
	and then plots it as a bar chart.
	key = any
	values = int/float or list of ints/floats
	MUST BE RUNNED WITH PYTHON 2
	'''
	import matplotlib.pyplot as plt
	
	#defining plot style
	plt.style.use('ggplot')
	#sorting the dict to get a list of keys in the intended order
	dictOfData = dict(dictOfData)
	#if one or all the values of the dict of data is a list, we sum it 
	try:
		for key, value in dictOfData.items():
			if type(value) is list:
				dictOfData[key] = sum(value)
	#if the elements in the value list are not summable, we pass
	except TypeError:
		pass
	#we use the list of keys of the dict ordered by values
	orderedKeys = sorted(dictOfData, key=dictOfData.__getitem__, reverse=False)
	for indexKey, dataKey in enumerate(orderedKeys):
		valueOfDict = dictOfData[dataKey]
		#defining the colors using the rgb colors (if there are more )
		redIndex = (indexKey*3)%len(rgbColor)
		greenIndex = (redIndex+1)%len(rgbColor)
		blueIndex = (greenIndex+1)%len(rgbColor)
		#launching one plot bar at a time
		#vertical bars
		if vertical == True:
			plt.bar(indexKey, valueOfDict, barWidth,
				label = u'%s. %s' %(str(indexKey), dataKey),
				color=(rgbColor[redIndex], rgbColor[greenIndex], rgbColor[blueIndex]),
				align='center')	
		#horizontal bars
		else:
			plt.barh(indexKey, valueOfDict, barWidth,
				label = u'%s. %s' %(str(indexKey), dataKey),
				color=(rgbColor[redIndex], rgbColor[greenIndex], rgbColor[blueIndex]),
				align='center')		
		#making a legend (parameters for legend to be outside of the chart)
		if legend == True:
			plt.xticks(range(len(dictOfData)))
			if len(dictOfData) <= 20:
				nbOfColumns = 1
			else:
				nbOfColumns = 2
			plt.legend(bbox_to_anchor=(0.70, 1), 	#place to be located (1.0 being the limit of the plot)
				loc=2,
				borderaxespad=0.0, 
				mode='expand',
				ncol=nbOfColumns)	#nb of columns of legend		
		#ennumerate the bars 
		plt.text(valueOfDict+1.0, indexKey+0.00, str(valueOfDict), color=(0, 0, 0))
	#applying labels to x and y
	plt.yticks(range(len(dictOfData)), orderedKeys, rotation=00)
	plt.ylabel(yLabel)
	plt.xlabel(xLabel)
	plt.tight_layout(pad=0.5, w_pad=0.0, h_pad=0.0)
	plt.show()
	return None


def plotDictAsBoxplot(dictOfData):
	'''
	When given a dict of data the function transforms it in a dataframe 
	and then plots it as a boxplot (boites a moustache).
	key = any
	values = list of ints/floats (or int/float)
	MUST BE RUNNED WITH PYTHON 2
	http://www.physics.csbsju.edu/stats/box2.html
	'''
	import matplotlib.pyplot as plt
	#defining plot style
	plt.style.use('ggplot')
	#sorting the dict to get a list of keys in the intended order
	newDict = {}
	for key in dictOfData:
		if type(dictOfData[key]) is list:
			newDict[key] = sum(dictOfData[key])
		else:
			newDict[key] = dictOfData[key]
	orderedKeys = (sorted(newDict, key=newDict.__getitem__, reverse=False))
	#we automatically calculate how many columns and rows we will need to fit all boxplots
	fig, axes = plt.subplots(nrows=((len(dictOfData)/5)+(1 if (len(dictOfData)%5) != 0 else 0)), ncols=(5 if len(dictOfData) >= 5 else len(dictOfData)))
	#we use the list of keys of the dict ordered by values
	for index, dataKey in enumerate(orderedKeys):
		if type(dictOfData[dataKey]) is list:
			valueOfDict = dictOfData[dataKey]
		else:
			valueOfDict = [dictOfData[dataKey]]

		#we keep the row index if there are multiple rows, otherwise we get an error
		if len(dictOfData) > 5:
			boxplot = axes[(index/5), (index%5)].boxplot(valueOfDict, 
			notch=True,  # notch shape
			vert=True,   # vertical box aligmnent
			showmeans=True,	#shows the means line
			meanline=True,	#the mean is shown with a interrupted line instead of an arrow
			patch_artist=True)	# fill with color 
			#we add the x labels
			axes[(index/5), (index%5)].set_xlabel(dataKey, fontsize=8)
			#we add the y labels if the plot is the first of the row
			if (index%5) == 0:
				axes[(index/5), (index%5)].set_ylabel('Nb of facts')
			#show median number in graph
			median = boxplot['medians'][0].get_ydata()[0]
			axes[(index/5), (index%5)].text(1.08, median+0.0, str("%.0f" %(median)), color=(1, 0, 0), weight=600, horizontalalignment='left', verticalalignment='center')
			#show means number in graph
			mean = boxplot['means'][0].get_ydata()[0]
			axes[(index/5), (index%5)].text(0.85, mean+0.0, str("%.2f" %(mean)), color=(0, 0, 0), weight=400, horizontalalignment='right', verticalalignment='center')
			#show whiskers number in graph
			whiskersTop = boxplot['whiskers'][1].get_ydata()
			whiskersBottom = boxplot['whiskers'][0].get_ydata()
			axes[(index/5), (index%5)].text(0.88, whiskersTop[0], str("%.0f" %(whiskersTop[0])), color=(0.3, 0, 1), weight=600, horizontalalignment='right', verticalalignment='bottom')
			axes[(index/5), (index%5)].text(1, whiskersTop[1]+0.01, str("%.0f" %(whiskersTop[1])), color=(0.3, 0, 1), weight=400, horizontalalignment='right', verticalalignment='bottom')
			axes[(index/5), (index%5)].text(0.9, whiskersBottom[0], str("%.0f" %(whiskersBottom[0])), color=(0, 0.3, 1), weight=600, horizontalalignment='right', verticalalignment='top')
			axes[(index/5), (index%5)].text(1, whiskersBottom[1]-0.01, str("%.0f" %(whiskersBottom[1])), color=(0, 0.3, 1), weight=400, horizontalalignment='right', verticalalignment='top')
		#we suppress the row index if there is only one row, otherwise we get an error
		else:
			boxplot = axes[(index%5)].boxplot(valueOfDict, 
			notch=True,  # notch shape
			vert=True,   # vertical box aligmnent
			showmeans=True,	#shows the means line
			meanline=True,	#the mean is shown with a interrupted line instead of an arrow
			patch_artist=True)	# fill with color

			#we add the x labels
			axes[(index%5)].set_xlabel(dataKey)
			#we add the y labels if the plot is the first of the row
			if (index%5) == 0:
				axes[(index/5)].set_ylabel('Nb of facts')
			#show median number in graph
			median = boxplot['medians'][0].get_ydata()[0]
			axes[(index%5)].text(1.08, median+0.0, str("%.0f" %(median)), color=(1, 0, 0), weight=600, horizontalalignment='left', verticalalignment='center')
			#show means number in graph
			mean = boxplot['means'][0].get_ydata()[0]
			axes[(index%5)].text(0.9, mean+0.0, str("%.2f" %(mean)), color=(0, 0, 0), weight=400, horizontalalignment='right', verticalalignment='center')
			#show whiskers number in graph
			whiskersTop = boxplot['whiskers'][1].get_ydata()
			whiskersBottom = boxplot['whiskers'][0].get_ydata()
			axes[(index%5)].text(0.88, whiskersTop[0], str("%.0f" %(whiskersTop[0])), color=(0.3, 0, 1), weight=600, horizontalalignment='right', verticalalignment='bottom')
			axes[(index%5)].text(1, whiskersTop[1]+0.01, str("%.0f" %(whiskersTop[1])), color=(0.3, 0, 1), weight=400, horizontalalignment='center', verticalalignment='bottom')
			axes[(index%5)].text(0.9, whiskersBottom[0], str("%.0f" %(whiskersBottom[0])), color=(0, 0.3, 1), weight=600, horizontalalignment='right', verticalalignment='top')
			axes[(index%5)].text(1, whiskersBottom[1]-0.01, str("%.0f" %(whiskersBottom[1])), color=(0, 0.3, 1), weight=400, horizontalalignment='center', verticalalignment='top')
	plt.tight_layout(pad=0.5, w_pad=0.0, h_pad=0.0)
	plt.show()
	return None


#######FIX THIS
def vennDiagram(listDataDict={'Set1': [], 'Set2': [], 'Set3': [], 'Se t1': [], 'Se t2': [] }):
	'''
	Makes a Venn diagrams between the lists in the dict
	https://pypi.python.org/pypi/matplotlib-venn
	'''
	import math, matplotlib_venn

	subplotsNbSolved = False
	dejaVus = []
	nbOfPlotCases = 0

	#we calculate the nb of subplots required
	for cutNb in range(len(listDataDict)):
		nbOfPlotCases += (((cutNb + 1) ** 2) / 2 ) - ((cutNb+1)/2)
	sqRoot = math.sqrt(nbOfPlotCases)
	#if we can du a 3 circles Venn diagram
	if nbOfPlotCases == 2:
		subplotsNbSolved = True
	#if we can du a 3 circles Venn diagram
	elif nbOfPlotCases == 3:
		subplotsNbSolved = True
	#if we can distribute equally the nb of subplots required on x and y
	elif sqRoot == int(sqRoot):
		#we specify the subplots
		figure, axes = plt.subplots(int(sqRoot), int(sqRoot))
	else:
		return None
	#if we can distribute the nb of subplots orderly on x and y without using unnecessary spaces
	for nbVal in reversed(range(int(sqRoot*2))):
		if nbVal not in [0, 1] and nbOfPlotCases%(nbVal) == 0:
			figure, axes = plt.subplots(nbOfPlotCases/nbVal, nbVal)
			subplotsNbSolved = True
			break
	#we try and distribute the nb of subplots the best we can on x and y without using the less unused spaces possible
	if subplotsNbSolved == False:
		xValue = 0
		yValue = 0
		nbAfterDecPoint = 0.0
		for nbVal in reversed(range(int(sqRoot*2))):
			#we separate the decimal value
			if nbVal not in [0, 1] and math.modf(float(nbOfPlotCases)/float(nbVal))[0] > nbAfterDecPoint:
				nbAfterDecPoint = math.modf(float(nbOfPlotCases)/float(nbVal))[0]
				xValue = int(nbOfPlotCases/nbVal)+1
				yValue = nbVal
		figure, axes = plt.subplots(xValue, yValue)

	#we make the venn diagrams
	plt.show()

	matplotlib_venn.venn3(subsets = {'001': 10, '100': 20, '010': 21, '110': 13, '011': 14, '101': 5, '111': 5}, set_labels = ('Set1', 'Set2', 'Set3'))
	matplotlib_venn.venn3(subsets = {'001': 10, '100': 20, '010': 21, '110': 13, '011': 14, '101': 5, '111': 5}, set_labels = ('Set1', 'Set2', 'Set3'))
	matplotlib_venn.venn3(subsets = {'001': 10, '100': 20, '010': 21, '110': 13, '011': 14, '101': 5, '111': 5}, set_labels = ('Set1', 'Set2', 'Set3'))
	matplotlib_venn.venn3(subsets = {'001': 10, '100': 20, '010': 21, '110': 13, '011': 14, '101': 5, '111': 5}, set_labels = ('Set1', 'Set2', 'Set3'))
	'''
	matplotlib_venn.venn2(subsets={'10': 1, '01': 1, '11': 1}, set_labels = ('A', 'B'), ax=axes[0][0])
	matplotlib_venn.venn2_circles((1, 2, 3), ax=axes[0][1])
	matplotlib_venn.venn3(subsets=(1, 1, 1, 1, 1, 1, 1), set_labels = ('A', 'B', 'C'), ax=axes[1][0])
	matplotlib_venn.venn3_circles({'001': 10, '100': 20, '010': 21, '110': 13, '011': 14}, ax=axes[1][1])
	'''
	plt.show()
	return None


'''
nodeListPath = u'/u/alfonsda/Documents/DOCTORAT_TAL/004projetOntologie/002data/candidats/2016-09-15/fr/anglophone/nodeListCleanedModularizedTrimmedInfered.tsv'
outputPath = u'/u/alfonsda/Documents/DOCTORAT_TAL/004projetOntologie/002data/candidats/2016-09-15/fr/anglophone/oldOnes/nSimilarDict.json'

analyseNodeListStrDistance(nodeListPath, outputPath)




listOfStrings = []
with open('/u/alfonsda/Documents/DOCTORAT_TAL/004projetOntologie/001ontologies/ESCO/v1.0.2/edgeAndNodeList/ESCOnodeList.tsv') as openfile:
	nodeData = openfile.readline()
	while nodeData:
		#get the data for each row
		nodeDataList = nodeData.split(u'\t')
		#we make sure we are not in the header
		if nodeDataList[0] != u'Id':
			#save the node id/label in a set
			listOfStrings.append(nodeDataList[1])
		#get next line
		nodeData = openfile.readline()
dicto = (tokenDistribution(listOfStrings))

print(11111111, len(listOfStrings))
for key, val in dicto.items():
	print(key, val[0], '%', float(val[0])/(float(len(listOfStrings))/100.0))


'''