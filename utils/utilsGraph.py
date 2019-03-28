#!/usr/bin/python
#-*- coding:utf-8 -*-

import json, codecs, random, shutil, os
from tqdm import tqdm
import pandas as pd
import numpy as np
import networkx as nx

import utilsOs, utilsString


##################################################################################
#TOOL FUNCTIONS
##################################################################################


def getDataFrameFromArgs(df1arg, df2arg=None):
	'''
	we chech if 'df1arg' and 'df2arg' are string paths or pandas dataframes
	'''
	#df1
	if type(df1arg) != str: # or type(df1arg) != unicode:
		df1 = df1arg
	else:
		df1 = pd.read_csv(df1arg, sep=u'\t')
	#df2
	if df2arg is None:
		return df1
	elif type(df2arg) != str: # or type(df2arg) != unicode:
		df2 = df2arg
	else:
		df2 = pd.read_csv(df2arg, sep=u'\t')
	return df1, df2


##################################################################################
#GRAPH FILES MAKER (EDGE_LIST and NODE_LIST) in O(n^2) where n is the nb of skills
##################################################################################


def edgeListTemp(pathInput, pathTempFile, pathOutput, lowercaseItAll=False):
	'''
	takes the linkedin data and makes a temporary file that is an edge list of (columns):
		- jobNode(source)
		- skillNode(target)
	It's only a temporary file because we still need to erase doubles, 
	to make the weight (count coreference of skills) 

	also count all coreferences and dump the resulting dict in a json file so the info 
	can be accessed later
	'''
	#open a temp file
	outputTempFile = utilsOs.createEmptyFile(pathTempFile) #don't specify that the headerLine is 'Source \t Target'
	#make and dump a json dict that keeps track of all types of coreferences (edge coref, node coref, skill, jobtitle, profile, etc.)
	corefDict = {u'edge':{}, 
				u'node':{
					u'jobtitle':{}, 
					u'skill':{}}}

	with open(pathInput) as jsonFile:
		#we read the original json file line by line
		for jsonData in tqdm(jsonFile, total=utilsOs.countLines(jsonFile)) :
			jsonDict = json.loads(jsonData)
			#if there are experiences
			if u'experiences' in jsonDict:
				#reliable job-skill correspondence if we only have one job title
				if len(jsonDict[u'experiences']) == 1:
					if u'function' in jsonDict[u'experiences'][0]:
						jobTitle = jsonDict[u'experiences'][0][u'function']
						if lowercaseItAll != False:
							jobtitle = jobTitle.lower()
						if u'skills' in jsonDict:
							for skillDict in jsonDict[u'skills']:
								skill = skillDict[u'name']
								if lowercaseItAll != False:
									skill = skill.lower()
								outputTempFile.write(u'{0}\t{1}\n'.format(jobTitle, skill))
								#count skill coreference
								corefDict[u'node'][u'skill'][u'{0}__t'.format(skill)] = corefDict[u'node'][u'skill'].get(u'{0}__t'.format(skill), 0) + 1
								#count edge coreference
								edge = u'{0}__s\t{1}__t'.format(jobtitle, skill)
								corefDict[u'edge'][edge] = corefDict[u'edge'].get(edge, 0) + 1
						#count jobtitle coreference
						corefDict[u'node'][u'jobtitle'][u'{0}__s'.format(jobtitle)] = corefDict[u'node'][u'jobtitle'].get(u'{0}__s'.format(jobtitle), 0) + 1
	#closing the file	
	outputTempFile.close()
	#dumping the coreference dictionnary
	pathCorefDict = u'/'.join(pathOutput.split(u'/')[:-1]+[u'corefDict.json'])
	utilsOs.dumpDictToJsonFile(corefDict, pathOutputFile=pathCorefDict, overwrite=True)
	return pathCorefDict


def edgeListDump(pathTempFile, pathOutput, pathCorefDict):
	'''
	opens the temp file containing the extracted linkedin data and makes an edge list of (columns):
		- jobNode(source)
		- skillNode(target)	
		- weight(skill coreference)
	
	[in a further function we might want to add keywords (non stop-words most common tokens for each jobtitle)]
	'''
	skillCorefDict = {}

	jobTitleCorefDict = {}
	lastJobTitle = None

	lineSet = set()

	#open the output file
	outputTxt = utilsOs.createEmptyFile(pathOutput, headerLine=u'Source\tTarget\tWeight\tWeight1')
	#we browse the data once to get the weight and nbOfTimesJobTitleAppeared data

	with codecs.open(pathTempFile, u'r', encoding=u'utf8') as tempData:
		for dataLine in tqdm(tempData, total=utilsOs.countLines(tempData)) :
			dataList = dataLine.replace(u'\n', u'').split(u'\t')
			if len(dataList) > 1:
				#get the skills coref
				corefDict = utilsOs.openJsonFileAsDict(pathCorefDict)
				skillCoref = corefDict[u'node'][u'skill'][u'{0}__t'.format(dataList[1])]
				#write the edge list with weight (skill weight)
				outputTxt.write(u'{0}__s\t{1}__t\t{2}\n'.format(dataList[0], dataList[1], skillCoref))
	#closing the file	
	outputTxt.close()


def nodeListIdType(pathEdgeListFile, pathNodeFileOutput):
	'''
	opens the edge file containing the extracted linkedin data and makes a node list of (columns):
		- id(same as label)
		- label(jobTitle / skill node)	
		- type(source or target; 2 for source 1 for target) #the job title is always the source, the skill is always the target
	'''
	jobTitleSet = set()
	skillSet = set()

	#open the output file
	outputTxt = utilsOs.createEmptyFile(pathNodeFileOutput, headerLine=u'Id\tLabel\tNodeType')

	with codecs.open(pathEdgeListFile, u'r', encoding=u'utf8') as edgeData:
		for dataLine in tqdm(edgeData, total=utilsOs.countLines(edgeData)) :
			dataList = dataLine.replace(u'\n', u'').split(u'\t')
			if len(dataList) > 1:
				#add to the jobTitle (source) set
				jobTitleSet.add(dataList[0])
				#add to the skill (target) set
				skillSet.add(dataList[1])
	#browse the data sets to dump them
	for jobTitle in jobTitleSet:
		outputTxt.write(u'{0}\t{1}\t{2}\n'.format(jobTitle, jobTitle.replace(u'__s', u''), 2)) #id's '_s' means 'source', 2 means 'source'
	for skill in skillSet:
		outputTxt.write(u'{0}\t{1}\t{2}\n'.format(skill, skill.replace(u'__t', u''), 1)) #id's '_t' means 'target', 1 means 'target'
	outputTxt.close()


##################################################################################
#GET ADJACENCY
##################################################################################


def getNodeAdjacency(nodeName, edgeList, bothWays=True): ###########################################################
	'''
	given a node, searchs for the adjacent nodes to it
	'''
	adjacencyList = []
	#add all nodes adjacent to the source nodes
	for edge in edgeList:
		if edge[0] == nodeName:
			adjacencyList.append(edge[1])
	#if the nodeName is not a source node, browse all the target nodes and append the source nodes to the adjacency list
	#or if bothways is true, it means the graph is not directed so there is no difference between source and target nodes
	if len(adjacencyList) == 0 or bothways == True:
		for edge in edgeList:
			if edge[1] == nodeName:
				adjacencyList.append(edge[0])
	return adjacencyList


##################################################################################
#RANDOM WALK
##################################################################################

def randomWalk(edgeDf, nodeDf):
	'''
	takes 2 pandas dataframes as main arguments:
	an edgeList and nodeList with the following columns:
	- edge list:
		- Source, Target, Weight, etc.
	- node list:
		- Id, Label, etc.
	'''
	#get a random node where to begin the random walk
	#get the adjacency list of the randomly chosen node
	#randomly choose if we want to move or not
		#randomly choose where we want to move, if we want to move
	return


##################################################################################
#MODULARITY
##################################################################################

def nodeDfCleaner(nodeDf):
	''' cleans all the node dataframe from NaN values in the modularity class '''
	#return nodeDf.loc[nodeDf[u'modularity_class'] != float(u'nan')]
	return nodeDf.dropna()


def formatModularityValue(dendroPartitionDict, nodeDf, nameOfModularityColumn, nameOfPreviousModCol):
	'''
	modifies the values of the modularity dict so it has the wanted 
	string format for the modularity column
	'''
	if nameOfPreviousModCol not in nodeDf.columns:
		for key, val in dendroPartitionDict.items():
			dendroPartitionDict[key] = str(val)
	else:
		column = nodeDf[u'Id'].map(dendroPartitionDict)
		for key, val in list(dendroPartitionDict.items()):
			#get index of previous (more general) modularity community number
			try:
				previousIndex = column[nodeDf[u'Id']==key].index.tolist()[0]
				#apply changes
				dendroPartitionDict[key] = u'{0}.{1}'.format(nodeDf[nameOfPreviousModCol][previousIndex], str(val))
			#if the previous column is empty (it doesn<t exist)
			except IndexError:
				del dendroPartitionDict[key]
				#dendroPartitionDict[key] = str(val)			
	return dendroPartitionDict


def modularize(edgeGraph, nodeDf):
	'''
	uses the original code of the louvain algorithm to give modularity to a graph
	'''
	import community #downloaded and installed from https://github.com/taynaud/python-louvain
	#compute the best partition
	dendrogram = community.generate_dendrogram(edgeGraph, weight='weight')
	for indexPartition in list(reversed(range(len(dendrogram)))):
		dendroPartitionDict = community.partition_at_level(dendrogram, indexPartition) #dendroPartitionDict = community.best_partition(graph)
		nameOfModularityColumn = u'Community_Lvl_{0}'.format(str(len(dendrogram)-indexPartition-1))
		#name a possible previous modularity column (needed to format the column values)
		nameOfPreviousModCol = u'Community_Lvl_{0}'.format(str(len(dendrogram)-indexPartition-2))
		#add a column to the node data frame so we can add the community values
		if nameOfModularityColumn not in nodeDf.columns:
			nodeDf[nameOfModularityColumn] = np.nan	
		#apply the wanted format to the content of the dict
		dendroPartitionDict = formatModularityValue(dendroPartitionDict, nodeDf, nameOfModularityColumn, nameOfPreviousModCol)
		#add the community values to the node data frame
		nodeDf[nameOfModularityColumn] = nodeDf[u'Id'].map(dendroPartitionDict)
	#making sure all 'modularity_class' NaN were deleted 
	return nodeDfCleaner(nodeDf), dendrogram


def modularizeLouvain(edgeFilePath, nodeFilePath, outputFilePath=None):
	'''
	uses the original code of the louvain algorithm to give modularity to a graph on multiple levels
	downloaded from https://github.com/taynaud/python-louvain
	documentation at: http://python-louvain.readthedocs.io/en/latest/api.html
	official website: https://perso.uclouvain.be/vincent.blondel/research/louvain.html
	'''
	#open the edge list as a networkx graph
	edgeGraph = nx.read_weighted_edgelist(edgeFilePath, delimiter='\t')
	#open the node list as a data frame	
	nodeDf = pd.read_csv(nodeFilePath, sep=u'\t')
	#get the louvain modularity algorithm result in the form of a completed node data frame
	nodeDf, dendrogram = modularize(edgeGraph, nodeDf)
	#dumps the dataframe with the modularization data
	if outputFilePath != None:
		nodeDf.to_csv(outputFilePath, sep='\t', index=False)
	return nodeDf, dendrogram


def modularizeSubCommunities(edgeFilePath, nodeFilePath, outputFilePath):
	'''
	reapplies a second time the louvain algorithm to each individual 
	sub-community obtained from the louvain algorithm
	'''
	#open the edge list as a data frame	
	edgeDf = pd.read_csv(edgeFilePath, sep=u'\t')
	#open the node list as a data frame	
	nodeDf = pd.read_csv(nodeFilePath, sep=u'\t')
	#modularize
	nodeDf, dendrogram = modularizeFurther(edgeDf, nodeDf, nameOfCommunityColumn=u'Community_Lvl_0', nameOfNewCommunityColumn=u'Community_Lvl_1', outputFilePath=outputFilePath)
	return nodeDf, dendrogram


def modularizeFurther(edgeDf, nodeDf, nameOfCommunityColumn, nameOfNewCommunityColumn, outputFilePath=None):
	'''
	recalculates the modularity for each community already in existence (adds one level of modularization)
	returns a node data frame with 
	'''
	#get the list of community ids
	communityList = list(set(nodeDf[nameOfCommunityColumn].tolist()))
	#for each community reapply the louvain algorithm
	for community in communityList:
		communityNodeDf = nodeDf.loc[nodeDf[nameOfCommunityColumn] == community]
		#select all the edges that have a community node as a source (we leave behind all the community nodes that are 'targets')
		selectiveEdgeDf = edgeDf.loc[edgeDf[u'Source'].isin(communityNodeDf[u'Id'].tolist())]
		#use the reduced edge list to make the graph
		communityGraph = nx.from_pandas_edgelist(selectiveEdgeDf, u'Source', u'Target', edge_attr=u'Weight')
		#further modularization
		subCommunityDf, dendrogram = modularize(communityGraph, communityNodeDf, nameOfModularityColumn=nameOfNewCommunityColumn)
		if nameOfNewCommunityColumn not in nodeDf.columns:
			nodeDf[nameOfNewCommunityColumn] = np.nan
		#add the Community_Lvl_1 value to the whole node data frame in the form : community_lvl_0 . community_lvl_1 (i.e., 1245.00015)
		for index in subCommunityDf.index:
			nodeDf.loc[index, nameOfNewCommunityColumn] = nodeDf.loc[index, nameOfCommunityColumn] + (subCommunityDf.loc[index, nameOfNewCommunityColumn] / 10000)
	#dumps the dataframe with the modularization data
	if outputFilePath != None:
		nodeDf.to_csv(outputFilePath, sep='\t', index=False)
	return nodeDf, dendrogram


def getModularityPercentage(nodeFilePathWithModularity, communityColumnHeader=u'Community_Lvl_0'):
	'''
	opens the node list tsv file and calculates the percentage of communities
	'''
	communityDict = {}
	resultDict = {}
	nodeDf = getDataFrameFromArgs(nodeFilePathWithModularity)

	#remaking a community dict
	for nodeIndex, nodeRow in nodeDf.iterrows():
		modCommunity = nodeRow[communityColumnHeader]
		if modCommunity in communityDict:
			communityDict[modCommunity].append(nodeRow[u'Label'])
		else:
			communityDict[modCommunity] = [nodeRow[u'Label']]
	#calculation
	for idKey, communityValue in communityDict.items():
		resultDict[idKey] = (float(len(communityValue)) / float(len(nodeDf)))
	#printing in order
	for v,k in (sorted( ((v,k) for k,v in resultDict.items()), reverse=True)):
		print('community {0} normalized score: {1}'.format(k, v))
		#if v > 0.01:
		#	print(55555555555, communityDict[k])
	return resultDict


##################################################################################
#MODULARITY DOMAIN NAME GUESSING USING BAG OF WORDS
##################################################################################


def fillBagOfWords(bowSet, jobTitleList, occupationsDf):
	'''
	Takes an empty of full set and fills it with the job title and description bag of words
	'''
	#adding the job titles to the bag of words
	for jobTitle in jobTitleList:
		bowSet = bowSet.union(set(utilsString.tokenizeAndExtractSpecificPos(jobTitle, [u'n', u'np', u'j'], caseSensitive=False, eliminateEnStopwords=True)))
	#adding the description(s) to the bag of words
	selectiveEscoDf = occupationsDf.loc[occupationsDf['preferredLabel'].isin(jobTitleList)]
	if selectiveEscoDf.empty:
		return bowSet
	for rowIndex, row in selectiveEscoDf.iterrows():
		#adding the alternative label(s) to the bag of words
		try:
			bowSet = bowSet.union(set(utilsString.tokenizeAndExtractSpecificPos(row['altLabels'].replace(u'\n', u' '), [u'n', u'np', u'j'], caseSensitive=False, eliminateEnStopwords=True)))
		#if the row value is an int or float
		except AttributeError:
			pass
		#adding the description(s) to the bag of words
		bowSet = bowSet.union(set(utilsString.tokenizeAndExtractSpecificPos(row['description'], [u'n', u'np', u'j'], caseSensitive=False, eliminateEnStopwords=True)))
	return bowSet


def getJobOfferDescriptionDict(listOfPathToJobOfferFiles=[
		u'/u/alfonsda/Documents/DOCTORAT_TAL/004projetOntologie/002data/jobsoffers/jobs_indeed-2016-06-17-noDup.json', 
		u'/u/alfonsda/Documents/DOCTORAT_TAL/004projetOntologie/002data/jobsoffers/jobs_indeed-2016-02-25-noDup.json']):
	'''
	extracts the jobOffer name and description and returns a dictionary
	'''
	jobOfferDict = {}
	#for each 'jobOffer source path' open json as dict
	for jobOfferFilePath in listOfPathToJobOfferFiles:
		jobOfferDictTemp = {}
		with open(jobOfferFilePath) as jobOfferFile:
			jsonData = jobOfferFile.readline()
			while jsonData:
				jsonDict = json.loads(jsonData)
				#get the title and description alone
				jobOfferDictTemp[jsonDict[u'title']] = u'{0} {1}'.format(jobOfferDictTemp.get(jsonDict[u'title'], u''), jsonDict[u'description'].replace(u'\n', u' '))
				#get next line
				jsonData = jobOfferFile.readline()
		jobOfferDict.update(jobOfferDictTemp)
	return jobOfferDict


def addJobOfferDescriptionToBow(jobTitle, jobOfferDict, bowDict={}):
	'''
	returns a dict of matching the job title and a description taken from a job offer
	'''	
	#best match job offer name and length of stems in common with job title
	bestMatch = [None, 0, None]
	jobTitleStems = utilsString.naiveStemmer(jobTitle, caseSensitive=False, eliminateEnStopwords=True, language=u'english')
	#search for a match between the job title and the job offer posts
	for jobOffer in jobOfferDict.keys():
		jobOfferStems = utilsString.naiveStemmer(jobOffer, caseSensitive=False, eliminateEnStopwords=True, language=u'english')
		stemIntersection = set(jobTitleStems).intersection(set(jobOfferStems))
		#if we have more than 2/3 match between job title and job offer post and if we have a better match than bestMatch, we update bestMatch
		if len(stemIntersection) > round(len(jobTitleStems)*0.66) and len(stemIntersection) > round(len(jobOfferStems)*0.66) and len(stemIntersection) > bestMatch[1]:
			bestMatch[0] = jobOffer
			bestMatch[1] = len(stemIntersection)
			bestMatch[2] = stemIntersection
	#extract the description and make a bow
	if bestMatch[0] != None:
		description = jobOfferDict[bestMatch[0]]
	return None


def getEscoBowByLevel(escoTree):
	'''
	starting at level 0 : the most abstract job title domain,
	we make a bag of words of the job titles and added descriptions 
	contained in the domain
	e.g., 	0: 		a0 : bow of a1+a2
					b0: bow of b1+b2
				1: 		a1: bow of a1 ...
						a2: bow of a2 ...
						b1: bow of b1 ...
						b2: bow of b2 ...
	'''
	from nltk.corpus import stopwords
	bowsDict = {0:{}, 1:{}, 2:{}, 3:{}}
	#open a dataframe of all occupation data, ready to extract the description
	occupationsUkDf = pd.read_csv(u'./001ontologies/ESCO/v1.0.2/occupations_en.csv')
	occupationsUsDf = pd.read_csv(u'./001ontologies/ESCO/v1.0.2/occupations_en-us.csv')
	#browsing the esco tree by hand to add the bow in the 4 levels	
	with codecs.open(u'./001ontologies/ESCO/v1.0.2/occupations_en.csv', u'r', encoding=u'utf8') as escoFileForDescription:
		#level 0
		for domain1digit, value1digit in escoTree.items():
			bow0 = set()
			#level 1
			for domain2digit, value2digit in value1digit.items():
				bow1 = set()
				#level 2
				for domain3digit, value3digit in value2digit.items():
					bow2 = set()
					#when the job titles are at level 3
					if type(value3digit) is list:
						bow2 = fillBagOfWords(bow2, value3digit, occupationsUkDf)
						bow2 = fillBagOfWords(bow2, value3digit, occupationsUsDf)
					else:
						#level 3
						for domain4digit, value4digit in value3digit.items():
							bow3 = set()
							#when the job titles are at level 4
							bow3 = fillBagOfWords(bow3, value4digit, occupationsUkDf)	
							bow3 = fillBagOfWords(bow3, value4digit, occupationsUsDf)						
							#saving in the bow dict
							bowsDict[3][domain4digit] = bow3
							bow2 = bow2.union(bow3)
					#saving in the bow dict
					bowsDict[2][domain3digit] = bow2
					bow1 = bow1.union(bow2)
				#saving in the bow dict
				bowsDict[1][domain2digit] = bow1
				bow0 = bow0.union(bow1)
			#saving in the bow dict
			bowsDict[0][domain1digit] = bow0
	return bowsDict


def addPitchToBow(jobTitle, bowDict={}, jobPitchDict=None):
	'''
	add pitch tokens to bow if there is a pitch and if the job title has a pitch
	'''
	if jobTitle in jobPitchDict:
		#pitch
		if len(jobPitchDict[jobTitle][u'pitch']) != 0:
			for pitch in jobPitchDict[jobTitle][u'pitch']:
				for pitchToken in utilsString.naiveRegexTokenizer(pitch, caseSensitive=False, eliminateEnStopwords=True):
					bowDict[pitchToken] = bowDict.get(pitchToken, 0) + 1
		#missions
		if len(jobPitchDict[jobTitle][u'mission']) != 0:
			for mission in jobPitchDict[jobTitle][u'mission']:
				for missionToken in utilsString.naiveRegexTokenizer(mission, caseSensitive=False, eliminateEnStopwords=True):
					bowDict[missionToken] = bowDict.get(missionToken, 0) + 1
	return bowDict


def getOntologyBowByCommunity(nodeDf, columnToInferFrom):
	'''
	makes a bag of words composed of the job title names
	for each community in the ontology
	'''
	communityBagOfWords = {}
	communitiesSet = set(nodeDf[columnToInferFrom].tolist())

	#get the dict containing all jobtitles and pitches
	jobPitchDict = utilsOs.openJsonFileAsDict(u'/u/alfonsda/Documents/DOCTORAT_TAL/004projetOntologie/002data/candidats/2016-09-15/fr/anglophone/jobAndPitch.json')

	for community in communitiesSet:
		bowDict = {}
		#get a reduced df where the community column corresponds to the community value
		communityDf = nodeDf.loc[nodeDf[columnToInferFrom] == community]
		#make the bag of words set
		jobTitleList = communityDf['Label'].tolist()
		for jobTitle in jobTitleList:
			#save te coreference of each token in the community as a proxy of the relevance weight of each token for that specific community
			for jobToken in utilsString.naiveRegexTokenizer(jobTitle, caseSensitive=False, eliminateEnStopwords=True):
				bowDict[jobToken] = bowDict.get(jobToken, 0) + 1
			#add the linkedIn profiles pitch to the bow
			bowDict = addPitchToBow(jobTitle, bowDict, jobPitchDict)
			
		#save the bag of words to the dict
		communityBagOfWords[community] = bowDict
	return communityBagOfWords


def getCommunityNameInferences(nodeFileInput, outputFilePath):
	''' 
	using a bag of words on jobtitles of the same community and on
	job titles and descriptions from existing ontologies (ESCO)
	estimate what is the name of the community domain
	'''
	inferencesDict = {}
	#we chech if 'edgeFileInput' and 'nodeFileInput' are string paths or pandas dataframes
	nodeDf = getDataFrameFromArgs(nodeFileInput)
	#bag of words of the esco ontology
	escoTree = utilsOs.openJsonFileAsDict(u'./jsonJobTaxonomies/escoTree.json')
	escoTreeBagOfWords = getEscoBowByLevel(escoTree)
	#infer a name for each existing level of communities
	communityLevel = 0
	subClasses = set()	
	while u'Community_Lvl_{0}'.format(str(communityLevel)) in nodeDf.columns:
		columnToInferFrom = u'Community_Lvl_{0}'.format(str(communityLevel))
		communityLevel += 1
		#bag of words of the communities in our ontology
		communityBagOfWords = getOntologyBowByCommunity(nodeDf, columnToInferFrom)
		#add an empty column
		inferenceColumnName = u'Infered_Community_Name_Lvl_{0}'.format(columnToInferFrom.split(u'_')[-1])
		nodeDf[inferenceColumnName] = np.nan
		#comparing intersection between esco bow and the communities bow
		for community, communityBowDict in communityBagOfWords.items():
			#reset values of best intersection
			bestIntersection = {u'result': 0.0, u'set': None, u'name': u'00000000___'}
			for nb in reversed(range(1, 4)):
				for escoDomain, escoBow in escoTreeBagOfWords[nb].items():
					bowIntersectionScore = 0
					#we intersect the 2 bag of words
					bowIntersection = set(communityBowDict.keys()).intersection(escoBow)
					for token in bowIntersection:
						bowIntersectionScore += communityBowDict[token]
					#we evaluate if we are at the same level in the esco taxonomy. If we are still on the same level the score 
					#needed to replace the best intersection is simply the one > than the precedent, 
					#if we are one level upper, then the needed score is multiplied by a variable (to priorize staying in a 
					#lower, more specialized, ESCO level)
					if len(bestIntersection[u'name'].split(u'___')[0]) == len(escoDomain.split(u'___')[0]):
						multiplier = 1.0
					else:
						#multiplier = (4.6 - (nb * 1.2))
						multiplier = 1.5
					#if the score is greater, we replace the previous best intersection with the new intersection
					if bowIntersectionScore > bestIntersection['result']*multiplier or bestIntersection['result'] == 0.0:
						bestIntersection[u'result'] = bowIntersectionScore
						bestIntersection[u'set'] = bowIntersection
						bestIntersection[u'dict'] = communityBowDict
						bestIntersection[u'name'] = escoDomain
			#saving the information
			inferencesDict[community] = bestIntersection
			nodeDf[inferenceColumnName].loc[nodeDf[columnToInferFrom] == community] = str(bestIntersection['name'])
	#dump to file
	nodeDf.to_csv(outputFilePath, sep='\t', index=False)
	return inferencesDict


##################################################################################
#MODULARITY DOMAIN NAME GUESSING USING WORD EMBEDDINGS
##################################################################################


def avg_sentence_vector(sentence, modelFastText):
	#make an empty vector
	num_features = model.get_dimension()
	featureVec = np.zeros(num_features, dtype="float32")
	#tokenization
	words = word_tokenize(sentence)
	for word in words:
		#sum of the vector's values
		featureVec = np.add(featureVec, model.get_word_vector(word))
	featureVec = np.divide(featureVec, float(max(len(words),1)))
	return featureVec


def cosine_similarity(vec1, vec2):
	return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def getWordEmbeddingInference(semanticClassCluster):
	'''
	Follows the Patel and Ravichandran algorithm for automatically
	labelling semantic classes and returns a ranked list of semantic
	classes names
	'''
	#pathToModel = u'/data/rali5/Tmp/alfonsda/DOCTORAT_TAL/004projetOntologie/fastTextModel/crawl-300d-2M.vec'
	pathToModel = u'/data/rali5/Tmp/alfonsda/DOCTORAT_TAL/004projetOntologie/fastTextModel/wiki-news-300d-1M.vec'
	model = FastText()
	model.load_model(pathToModel)
	###################################################################
	###################################################################


##################################################################################
#ONTOLOGY CLEANING AND TRIMMING
##################################################################################

def wasteNodeElimination(edgeFileInput, nodeFileInput):
	'''
	Checks if every node in the node file appear in the edge file
	otherwise it eliminates it
	Checks if the nodes of every edge is in the node file
	otherwise the edge gets eliminated
	'''
	edgesToEliminate = []
	nodesToEliminate = []
	edgeDf, nodeDf = getDataFrameFromArgs(edgeFileInput, nodeFileInput)
	#browse edges if its nodes are not in the nodes list, prepare the lists of elements to drop
	edgesToEliminate = edgeDf.loc[ ~edgeDf[u'Source'].isin(nodeDf[u'Id']) | ~edgeDf[u'Target'].isin(nodeDf[u'Id'])]
	#drop the edges
	edgeDf = edgeDf.drop(edgesToEliminate.index)
	#browse nodes if not in edges, prepare the lists of elements to drop	
	nodesToEliminate = nodeDf.loc[ ~nodeDf[u'Id'].isin(edgeDf[u'Source']) & ~nodeDf[u'Id'].isin(edgeDf[u'Target'])]
	#drop the nodes
	nodeDf = nodeDf.drop(nodesToEliminate.index)
	#dumping the data frames to the same file where we opened them
	if type(edgeFileInput) == str and type(nodeFileInput) == str:
		edgeDf.to_csv(edgeFileInput, sep='\t', index=False)
		nodeDf.to_csv(nodeFileInput, sep='\t', index=False)	
	return edgeDf, nodeDf


def ontologyContentCleaning(languageOfOntology, edgeFilePathInput, nodeFilePathInput, edgeFilePathOutput=None, nodeFilePathOutput=None):
	'''
	NOTE: this function only cleans interlanguage intrusion between FRENCH and ENGLISH
	given an ontology (edge list and node list), removes:
		- all nodes detected to be in a different language that the language of the ontology
		- all over-specific nodes (having more than 5 tokens) 
		- all 2in1 nodes (all nodes having '/', '\', ',', ':', ';', ' - ' and '&' between words)
		- all nodes containing giberish : 
				- repetition of the 3 same characters or more (e.g., 'aaa', 'xxxxxx')
				- a great number of non alphanumerical symbols (e.g., '!#&*&^%$#', 'adr--+)
	'''
	import langdetect
	theRightNodes = set()
	edgeDf = pd.read_csv(edgeFilePathInput, sep=u'\t')
	nodeDf = pd.read_csv(nodeFilePathInput, sep=u'\t')

	for nodeIndex, nodeRow in nodeDf.iterrows():
		label = nodeRow['Label']
		#detecting if the label is in english or french
		if utilsString.englishOrFrench(label) == languageOfOntology:
			#if the node is not over-specific
			if len(utilsString.naiveRegexTokenizer(label, eliminateEnStopwords=True)) <= 5:
				#if we detect no 2in1 jobTitles/skills
				if utilsString.indicator2in1(label) == False:
					#if we don't detect gibberish in a row
					if utilsString.isItGibberish(label, gibberishTreshold=0.49, exoticCharSensitive=False) == False:
						#add the node id to the list of correct nodes
						theRightNodes.add(nodeRow['Id'])
	#get the dataframes containing the right nodes
	cleanedEdgeDf = edgeDf.loc[edgeDf[u'Source'].isin(theRightNodes) & edgeDf[u'Target'].isin(theRightNodes)]
	cleanedNodeDf = nodeDf.loc[nodeDf[u'Id'].isin(theRightNodes)]
	#dumping the data frames
	if edgeFilePathOutput != None:
		cleanedEdgeDf.to_csv(edgeFilePathOutput, sep='\t', index=False)
		cleanedEdgeDf.to_csv(u'{0}NoHeader.tsv'.format(edgeFilePathOutput.split(u'.tsv')[0]), sep='\t', index=False, header=None)
	if nodeFilePathOutput != None:
		cleanedNodeDf.to_csv(nodeFilePathOutput, sep='\t', index=False)
	return cleanedEdgeDf, cleanedNodeDf



def remove1DegreeNodes(dictA, dictB, aOldSize=0, bOldSize=0):
	'''
	recursive function to remove all the less core-connected 
	nodes from the dicts representing the graph
	'''
	aOriginalSize = len(dictA)
	bOriginalSize = len(dictB)
	#remove job titles of degree 1 (with only one skill)
	for aKey, aList in dict(dictA).items():
		#if there is one (or less) skill for that job title
		if len(aList) <= 1:
			#to maintain consistency, delete the job title from the skill to jobs dict
			for bElem in list(aList):
				#delete the job title from the skill to jobs dict
				dictB[bElem].remove(aKey)
				#remove the keys in the dict with an empty list as value
				if len(dictB[bElem]) == 0:
					del dictB[bElem]
			#delete the dict entry from the job to skills dict
			del dictA[aKey]
	if len(dictA) != aOriginalSize and aOriginalSize != aOldSize and len(dictB) != bOriginalSize and bOriginalSize != bOldSize:
		dictB, dictA = remove1DegreeNodes(dictB, dictA, bOriginalSize, aOriginalSize)
	return dictA, dictB


def dropNodesAppearingNOrLessTimes(edgeDf, nodeDf, n, corefDictPath):
	'''
	drop all nodes appearing n times or less than n times in the ontology
	using the coreference dict of the whole ontology
	'''
	nLessAppearingJobTitlesNodes = set()	
	nLessAppearingSkillNodes = set()

	corefDict = utilsOs.openJsonFileAsDict(corefDictPath)
	#get jobTitle set of n appearing nodes
	for jobTitle, jobTitleCoref in corefDict[u'node'][u'jobtitle'].items():
		if jobTitleCoref <= n:
			nLessAppearingJobTitlesNodes.add(jobTitle)
	#get skill set of n appearing nodes
	for skill, skillCoref in corefDict[u'node'][u'skill'].items():
		if skillCoref <= n:
			nLessAppearingSkillNodes.add(skill)
	#get df of nodes appearing more than n times
	nodeDf = nodeDf.loc[~nodeDf[u'Id'].isin( list(nLessAppearingJobTitlesNodes) + list(nLessAppearingSkillNodes) )]
	#drop nodes that are not present in the ontology at all	
	nodeDf = nodeDf.loc[nodeDf[u'Id'].isin(list(corefDict[u'node'][u'jobtitle'].keys()) + list(corefDict[u'node'][u'skill'].keys()) )]
	#get df of edges whose nodes appear more than n times
	edgeDf = edgeDf.loc[~edgeDf[u'Source'].isin(nLessAppearingJobTitlesNodes) ]
	edgeDf = edgeDf.loc[~edgeDf[u'Target'].isin(nLessAppearingSkillNodes) ]
	#drop edges of nodes that are not present in the ontology at all	
	edgeDf = edgeDf.loc[edgeDf[u'Target'].isin(corefDict[u'node'][u'skill'].keys())]
	edgeDf = edgeDf.loc[edgeDf[u'Source'].isin(corefDict[u'node'][u'jobtitle'].keys())]
	return edgeDf, nodeDf 


def dropNodesOnlyConnectedToNodesAppearingNOrLessTimes(edgeDf, nodeDf, n, corefDictPath):
	'''
	drop all nodes appearing n times or less than n times in the ontology
	using the coreference dict of the whole ontology
	'''
	nLessAppearingJobTitlesNodes = set()	
	nLessAppearingSkillNodes = set()
	nodesToDrop = set()

	corefDict = utilsOs.openJsonFileAsDict(corefDictPath)
	#get jobTitle set of n (or less) appearing nodes
	for jobTitle, jobTitleCoref in corefDict[u'node'][u'jobtitle'].items():
		if jobTitleCoref <= n:
			nLessAppearingJobTitlesNodes.add(jobTitle)
	#get skill set of n (or less) appearing nodes
	for skill, skillCoref in corefDict[u'node'][u'skill'].items():
		if skillCoref <= n:
			nLessAppearingSkillNodes.add(skill)
	#look for all jobtitles appearing n or less times if ALL their skills also appear n or less times, then we drop them
	for jobTitle in nLessAppearingJobTitlesNodes: 
		#we look at the edges of the candidate jobtitle to be dropped
		candidateEdgeDf = edgeDf.loc[ edgeDf[u'Source'] == jobTitle ] ##########################3
		candidateSkills = set(candidateEdgeDf[u'Target'].tolist())
		#if all the skills of the candidate jobtitle appear n times or less, then we drop the jobtitle and the skills
		if len(candidateSkills) != 0 and len(candidateSkills.intersection(nLessAppearingSkillNodes)) == len(candidateSkills):
			edgeDf = edgeDf.drop(candidateEdgeDf.index)
	#drop nodes of already dropped edges	
	edgeDf, nodeDf = wasteNodeElimination(edgeDf, nodeDf)
	return edgeDf, nodeDf


def ontologyStructureCleaning(edgeFileInput, nodeFileInput, corefDictPath, edgeFilePathOutput=None, nodeFilePathOutput=None):
	'''
	given an ontology (edge list and node list), removes:
		- all communities corresponding to less than 1% of the node
		- all independent and isolated skills and job titles:
			- all skills connected to only 1 job title
			- all job titles with only one skill
			- all job titles (and skills) whose skills are not connected to any other job titles
			- all job titles and skills appearing n times or less in the whole ontology
	'edgeFileInput' and 'nodeFileInput' can either be a string/unicode path to a tsv file or a pandas dataframe
	'''
	#get dataframes
	edgeDf, nodeDf = getDataFrameFromArgs(edgeFileInput, nodeFileInput)
	#remove communities corresponding to less than 1% of the node
	communitiesSet = set(nodeDf['Community_Lvl_0'].tolist())
	copyCommunitiesSet = list(communitiesSet)
	for communityId in copyCommunitiesSet:
		#get a reduced df where the community column corresponds to the community id value
		communityDf = nodeDf.loc[nodeDf[u'Community_Lvl_0'] == communityId]
		if len(communityDf)/len(nodeDf) < 0.01:
			communitiesSet.remove(communityId)
	#save the trimmed df as the new node df
	nodeDf = nodeDf.loc[nodeDf[u'Community_Lvl_0'].isin(list(communitiesSet))]
	#make a dict of jobtitle to skills and a dict of skill to jobtitles
	jToSkillsDict = {}
	sToJobsDict = {}
	emptyList = []
	for edgeIndex, edgeRow in edgeDf.iterrows():
		jToSkillsDict[edgeRow[u'Source']] = list(set(jToSkillsDict.get(edgeRow[u'Source'], list(emptyList)) + [edgeRow[u'Target']]))
		sToJobsDict[edgeRow[u'Target']] = list(set(sToJobsDict.get(edgeRow[u'Target'], list(emptyList)) + [edgeRow[u'Source']]))
	#drop the rows whose nodes appear n times or less in the whole ontology
	edgeDf, nodeDf = dropNodesOnlyConnectedToNodesAppearingNOrLessTimes(edgeDf, nodeDf, 1, corefDictPath)
	#remove independent and isolated skills and job titles
	jToSkillsDict, sToJobsDict = remove1DegreeNodes(jToSkillsDict, sToJobsDict)
	#save the trimmed data frames as the new data frames
	nodeDf = nodeDf.loc[nodeDf[u'Id'].isin( list(jToSkillsDict.keys())+list(sToJobsDict.keys()) )]
	edgeDf = edgeDf.loc[edgeDf[u'Source'].isin(list(jToSkillsDict.keys())) & edgeDf[u'Target'].isin(list(sToJobsDict.keys()))]
	#dumping the data frames
	if edgeFilePathOutput != None:
		edgeDf.to_csv(edgeFilePathOutput, sep='\t', index=False)
	if nodeFilePathOutput != None:
		nodeDf.to_csv(nodeFilePathOutput, sep='\t', index=False)
	#we make sure there are no unconnected nodes
	wasteNodeElimination(edgeFilePathOutput, nodeFilePathOutput)
	return edgeDf, nodeDf


##################################################################################
#ONTOLOGY AUTOMATIC EVALUATION METRICS
##################################################################################

def ontoQA(edgeFilePath, nodeFilePath, verbose=True):
	'''
	given an ontology (edge list and node list) it calculates the ontoQA score
	the lists must contain certain column names:
	 - edge list: Source, Target
	 - node list: Id, Community_Lvl_0
	'''
	emptyDict = {}
	dataDict = {}
	metricsDict = {}
	#open the edge list as a data frame	
	edgeDf = pd.read_csv(edgeFilePath, sep=u'\t')
	#open the node list as a data frame	
	nodeDf = pd.read_csv(nodeFilePath, sep=u'\t')
	#make a dict for the class related data
	classes = set(nodeDf['Community_Lvl_0'].tolist())
	classDataDict = {k:dict(emptyDict) for k in classes}
	#count the number of subClasses (not counting the main, upper level, classes)
	nb = 1
	subClasses = set()
	while 'Community_Lvl_{0}'.format(str(nb)) in nodeDf.columns:
		subClasses = subClasses.union(set( nodeDf[ 'Community_Lvl_{0}'.format(str(nb)) ].tolist() ))
		nb += 1

	#get C, number of classes
	dataDict['C'] = len(classes)
	#get P', non-inheritance relationships (relation types) deducing the inexisting schema
	if 'esco' in edgeFilePath.lower():
		escoRelationships = ['hasSkill', 'conceptType', 'conceptUri', 'broaderUri', 'iscoGroup', 'preferredLabel', 'alternativeLabel', 'description', 'occupationUri', 'relationType', 'skillType', 'skillUri', 'reuseLevel']
		dataDict['P'] = len(escoRelationships) #has 13 relationships
	else:
		ourRelationships = ['hasSkill', 'conceptType', 'conceptUri', 'broaderUri', 'communityGroupId', 'preferredLabel', 'occupationUri', 'relationType', 'skillUri', 'reuseLevel']
		dataDict['P'] = len(ourRelationships) #in an edge and node List it's 2!!!: hasSkill, hasSubclass #BUT can be grown to 10 if put in a formal ontology form: 
	#get P' (P prime), non-inheritance relations (instances)
	dataDict["P'"] = len(edgeDf)
	#get H, inheritance relationships
	dataDict['H'] = 1	 #isSubclassOf or broaderUri(in ESCO)
	#get Hs, number of subclasses
	dataDict['Hs'] = len(subClasses)	
	#get att, number of attributes
	dataDict['att'] = len(edgeDf) + len(nodeDf)
	#get CI, total number of instances
	dataDict['CI'] = len(nodeDf) + len(classes)
	#get class (C_i) dependent data (inst)
	for classId in classes:
		classDataDict[classId]['inst_nbClassInstances'] = len(nodeDf.loc[nodeDf['Community_Lvl_0'] == classId])
		#add a NIREL value of 0 in case there is an 'na' in the classes
		classDataDict[classId]['NIREL_nbRelOtherClass'] = 0
	#get class (C_i) dependent data (NIREL)
	for edgeIndex, edgeRow in edgeDf.iterrows():
		sourceClass = nodeDf.loc[nodeDf['Id'] == edgeRow['Source']]['Community_Lvl_0'].values
		targetClass = nodeDf.loc[nodeDf['Id'] == edgeRow['Target']]['Community_Lvl_0'].values
		try:
			if sourceClass != targetClass:
				#get NIREL(Cj), number of relationships instances of the class have with instances of other classes
				classDataDict[sourceClass[0]]['NIREL_nbRelOtherClass'] = classDataDict[sourceClass[0]].get('NIREL_nbRelOtherClass', 0) + 1 
			else:
				classDataDict[sourceClass[0]]['nbRelSameClass'] = classDataDict[sourceClass[0]].get('nbRelSameClass', 0) + 1 
		except IndexError:
			pass
	#open the edge list as a networkx graph to get the nb of connected components
	edgeGraph = nx.from_pandas_edgelist(edgeDf, u'Source', u'Target', edge_attr=u'Weight')
	#get CC, number of connected components
	dataDict['CC'] = nx.number_connected_components(edgeGraph)

	#calculating the ONTOQA METRICS:
	#RR - relationship richness
	metricsDict['RR'] = float(dataDict['P']) / float(dataDict['H']+dataDict['P'])
	#IR - inheritance richness
	metricsDict['IR'] = float(dataDict['Hs']) / float(dataDict['C'])
	#AR - attribute richness
	metricsDict['AR'] = float(dataDict['att']) / float(dataDict['C'])
	#CR - class richness
	##################unable to actually calculate it without having a preconceived schema of the ontology
	#Conn(C_i) - class connectivity 
	metricsDict['Conn'] = {}
	for classId, classData in classDataDict.items():
		try:
			metricsDict['Conn'][u'CLASS {0}'.format(classId)] = classData['NIREL_nbRelOtherClass']
		except KeyError:
			#print(classId, classData)
			pass
	#Imp(C_i) - class importance
	metricsDict['Imp'] = {}
	for classId, classData in classDataDict.items():
		metricsDict['Imp'][u'CLASS {0}'.format(classId)] = float(classData['inst_nbClassInstances']) / float(dataDict['CI'])
	#Coh - cohesion
	metricsDict[u'Coh'] = dataDict[u'CC']
	#RR(C_i) - relationship richness per class
	##################unable to actually calculate it without having a preconceived schema of the ontology
	if verbose == True:
		print(metricsDict)
	return metricsDict


##################################################################################
#TOOLS FOR HUMAN ONTOLOGY ANALYSIS AND EVALUATION
##################################################################################

def printCommunityInferenceHeaders(nodeFileInput):
	'''
	pretty prints an ASCII table containing the communities 
	header selection of a particular level of the ontology
	'''
	from prettytable import PrettyTable
	dataDict = {}
	#get the node dataframe
	nodeDf = getDataFrameFromArgs(nodeFileInput)
	#get the data from the node dataframe
	communityLevel = 0
	while u'Community_Lvl_{0}'.format(str(communityLevel)) in nodeDf.columns:
		nameOfCommunityColumn = u'Community_Lvl_{0}'.format(str(communityLevel))
		#empty dict
		dataDict[communityLevel] = {}
		#get the list of community ids for a specific level
		communityIdsList = list(set(nodeDf[nameOfCommunityColumn].tolist()))
		#save the data for each community
		for communityId in communityIdsList:
			communityNodeDf = nodeDf.loc[nodeDf[nameOfCommunityColumn] == communityId]
			#transform the ratio into string beacause prettytable has trouble with exponential numbers
			ratio = str(len(communityNodeDf)/len(nodeDf))
			if 'e-' in ratio:
				ratio = ratio.split('e-')
				ratio1 = '0' * (int(ratio[1])-1)
				ratio2 = ratio[0].replace('.', '')
				ratio = '0.{0}{1}'.format(ratio1, ratio2)
			#fill data dict with the data
			dataDict[communityLevel][communityId] = {
			'communityName': (communityNodeDf.head(1)['Infered_Community_Name_Lvl_{0}'.format(communityLevel)]).values[0] , 
			'ratioOfNodeInWholeDf': ratio, 
			'nbOfNodes': len(communityNodeDf), 
			'sample': communityNodeDf.head(10)['Label'].tolist()}
		communityLevel += 1
	#print one table per level
	for levelNb in sorted(dataDict.keys()):
		levelDataDict = dataDict[levelNb]
		#use prettytable to show the data in a human readable way
		table = PrettyTable()
		table.title = "LEVEL {0}".format(str(levelNb))
		table.field_names = ['Ratio', 'Infered Name', 'Sample']
		#insert the data as rows
		for communityId, data in levelDataDict.items():
			#cut the community name if it's too long
			if len(data['communityName']) > 20:
				segmentedCommunityName = []
				lastSeg = 0
				for nbSeg in range((len(data['communityName']) % 20)+2)[1:]:
					if nbSeg * 20 < len(data['communityName']):
						seg = nbSeg*20
					else:
						seg = len(data['communityName'])
					segmentedCommunityName.append(data['communityName'][lastSeg:seg])
					#hold place of last segmentation
					lastSeg = seg
				communityName = '\n'.join(segmentedCommunityName)
			else:
				communityName = data['communityName']
			#add the row data to the table
			table.add_row([data['ratioOfNodeInWholeDf'], communityName, '\n'.join(data['sample'] + [''])])
		#sort
		table.sortby = "Ratio"
		table.reversesort = True
		#printing
		print("LEVEL {0}".format(str(levelNb)))
		print(table)


def getSampleForHumanEvaluation(edgeFileInput, nodeFileInput, lengthOfSample=1000, outputEdgeFilePath=None, outputNodeFilePath=None):
	'''
	given a finished ontology in the form of an edge list and a node list
	return and dump a randomly chosen sample
	'''
	setOfIndexes = set()
	#get dataframes
	edgeDf, nodeDf = getDataFrameFromArgs(edgeFileInput, nodeFileInput)
	#get a random list of indexes
	while len(setOfIndexes) < lengthOfSample:
		setOfIndexes.add(random.randint(0, len(edgeDf)))
	#get a reduced randomly chosen edge dataframe
	sampleEdgeDf = edgeDf.iloc[list(setOfIndexes)]
	#get the reduced node dataframe corresponding to the randomly chosen edge dataframe
	sampleNodeDf = nodeDf.loc[nodeDf[u'Id'].isin(sampleEdgeDf[u'Source'].tolist() + sampleEdgeDf[u'Target'].tolist())]
	#dumps the dataframes
	if outputEdgeFilePath != None:
		sampleEdgeDf.to_csv(outputEdgeFilePath, sep='\t', index=False)
	if outputNodeFilePath != None:
		(sampleNodeDf.sort_values(by=['Community_Lvl_1'])).to_csv(outputNodeFilePath, sep='\t', index=False)
	return sampleEdgeDf, sampleNodeDf.sort_values(by=['Community_Lvl_1'])


def getPrintableStringOfGoodNodes(sourceOrTargetNodes, sampleNodeDf, nodeRow, corefDict, typeOfNode, communityColumnName=u'Community_Lvl_0'):
	'''
	transforms the node data frame onto a printable version 
	of limited number, ordered by score and with the analyzed 
	node in the middle and in red
	'''
	listOfNodesOrderedByValue = []
	#transform the dataframe into a list of the elements we care about
	listOfNodes = (sourceOrTargetNodes.loc[sampleNodeDf[communityColumnName] == nodeRow[communityColumnName]])[u'Id'].tolist()
	#drop the analyzed node and get only the nlargest with greater weight
	orderedByValue = sorted(corefDict[u'node'][typeOfNode].items(), key=lambda kv: kv[1], reverse=True)
	for node in orderedByValue:
		if node[0] in listOfNodes:
			listOfNodesOrderedByValue.append(node[0])
	#remove the node we are interested in analyzing because we want to add it later in the middle of the list, in red
	try:
		listOfNodesOrderedByValue.remove(nodeRow[u'Id'])
	except ValueError:
		pass
	#if the list is too long, we only take the 5 best scored nodes
	if len(listOfNodesOrderedByValue) > 5:
		listOfNodesOrderedByValue = listOfNodesOrderedByValue[:5]
	#add the node we are analyzing in the middle of the list
	listOfNodesOrderedByValue = listOfNodesOrderedByValue[:int(len(listOfNodesOrderedByValue)/2.0)] + [nodeRow[u'Id']] + listOfNodesOrderedByValue[int(len(listOfNodesOrderedByValue)/2.0):]
		
	#transform the list into a string
	stringOfNodes = u''
	for indexNode, node in enumerate(listOfNodesOrderedByValue):
		#one string per line
		stringOfNodes = u'{0}\t{1}\n'.format(stringOfNodes, str(node)) if (indexNode+1) != len(listOfNodes) else u'{0}\t{1}'.format(stringOfNodes, str(node))
	#coloration
	stringOfNodes = stringOfNodes.replace(nodeRow[u'Id'], u'\033[1;31m{0}\033[0m'.format(nodeRow[u'Id']))
	return stringOfNodes


def getPrintableStringOfGoodInferenceNodes(nodeRow, escoNodeDf, inferedDomain):
	'''
	transforms the node data frame onto a printable version 
	of limited number, ordered by score and with the analyzed 
	node in the middle and in red
	'''
	#transform the ESCO dataframe into a list of the nodes belonging to the infered domain
	for nb in reversed(range(4)):
		if len( (escoNodeDf[u'Community_Lvl_{0}'.format(nb)])[0] ) == len(str(inferedDomain)):
			break
	#get the ESCO nodes belonging to the infered domain
	listOfNodesInEsco = (escoNodeDf.loc[escoNodeDf[u'Community_Lvl_{0}'.format(nb)] == str(inferedDomain)])[u'Label'].tolist()
	#remove the node we are interested in analyzing because we want to add it later in the middle of the list, in red
	try:
		listOfNodesInEsco.remove(nodeRow[u'Label'].lower())
	except ValueError:
		pass
	#if the list is too long, we only take the 5 best scored nodes
	if len(listOfNodesInEsco) > 5:
		listOfNodesInEsco = listOfNodesInEsco[:5]
	#add the node we are analyzing in the middle of the list
	listOfNodesInEsco = listOfNodesInEsco[:int(len(listOfNodesInEsco)/2.0)] + [nodeRow[u'Id']] + listOfNodesInEsco[int(len(listOfNodesInEsco)/2.0):]
		
	#transform the list into a string
	stringOfNodes = u''
	for indexNode, node in enumerate(listOfNodesInEsco):
		#one string per line
		stringOfNodes = u'{0}\t{1}\n'.format(stringOfNodes, str(node)) if (indexNode+1) != len(listOfNodesInEsco) else u'{0}\t{1}'.format(stringOfNodes, str(node))
	#coloration
	stringOfNodes = stringOfNodes.replace(nodeRow[u'Id'], u'\033[1;31m{0}\033[0m'.format(nodeRow[u'Id']))
	return stringOfNodes


def savingAnnotatorInput(sampleDf, nodeColumnName, objIndex, nbOfLines, listOfAnswers=[0,1,2]):
	'''
	waits for the annotation and adds it to the data frame
	'''
	#avoid the SettingWithCopy Warning in pandas (https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas) 
	pd.options.mode.chained_assignment = None
	#wait for annotator input
	annotatorInput = input(u'Annotation: ')
	#if we wish to stop and return the data frame to be dumpted (even if incomplete)
	if annotatorInput in [u'stop', u'Stop', u'STOP', u'-s']:
		return sampleDf, True
	#make sure the annotation is right
	while True:
		try:
			if int(annotatorInput) in listOfAnswers:
				break
			else:
				utilsOs.moveUpAndLeftNLines(1, slowly=False)
				annotatorInput = input(u'Repeat annotation: ')
				#if we wish to stop and return the data frame to be dumpted (even if incomplete)
				if annotatorInput in [u'stop', u'Stop', u'STOP', u'-s']:
					return sampleDf, True
		except ValueError:
			utilsOs.moveUpAndLeftNLines(1, slowly=False)
			annotatorInput = input(u'Repeat annotation: ')
			#if we wish to stop and return the data frame to be dumpted (even if incomplete)
			if annotatorInput in [u'stop', u'Stop', u'STOP', u'-s']:
				return sampleDf, True
	#save the annotation as int if we only have 3 possibilities: -1, 0, 1
	if len(listOfAnswers) == 3:
		sampleDf[nodeColumnName][objIndex] = int(annotatorInput) - 1
	#save as a float if we have more than 3 options
	else:		
		sampleDf[nodeColumnName][objIndex] = (float(annotatorInput)/10.0) - 1
	#clear the terminal before the next row
	utilsOs.moveUpAndLeftNLines(nbOfLines, slowly=False)
	return sampleDf, False


def getPrintableStringOfGoodEdges(sampleEdgeDf, edgeRow, corefDict):
	'''
	transforms the edge data frame into a printable version 
	of limited number, ordered by score and with the analyzed 
	edge in the middle and in red
	'''
	sameSourceEdgesDict = {}
	#reduce the dataframe into a list containing all edges with the same source as the analyzed edge row
	for edgeKey, edgeVal in corefDict[u'edge'].items():
		#only take the edges having the same source as the edge row but not exactly identical to the edge row
		if edgeKey.split(u'\t')[0] == edgeRow[u'Source'].lower() and edgeKey.split(u'\t')[1] != edgeRow[u'Target'].lower():
			#asign the coreference value + the inverse length of the edge target
			#so when we sort it, the first elements of the list will be the more referenced and the shortest edges (we postulate that the shortest target required less processing/thought from the profile user and could be more pertinents)
			sameSourceEdgesDict[edgeKey.replace(u'\n', u'').replace(u'\t', u' >>>>> ')] = edgeVal + 1.0-float(len(edgeKey.split(u'\t')[1])/float(1000))
	
	#sort the edges by coreference and length of the target
	listOfEdgesOrderedByValue = sorted(sameSourceEdgesDict.keys(), reverse=True, key=lambda k : sameSourceEdgesDict[k])
	#if the list is too long, we only take the 5 best scored edges
	if len(listOfEdgesOrderedByValue) > 4:
		listOfEdgesOrderedByValue = listOfEdgesOrderedByValue[:4]
	#add the edge we are analyzing in the middle of the list 
	currentEdge = u'{0} >>>>> {1}'.format(edgeRow[u'Source'].lower(), edgeRow[u'Target'].lower())
	listOfEdgesOrderedByValue = listOfEdgesOrderedByValue[:int(len(listOfEdgesOrderedByValue)/2.0)] + [currentEdge] + listOfEdgesOrderedByValue[int(len(listOfEdgesOrderedByValue)/2.0):]
		
	#transform the list into a string
	stringOfEdges = u''
	for indexEdge, edge in enumerate(listOfEdgesOrderedByValue):
		#one string per line
		stringOfEdges = u'{0}\t{1}\n'.format(stringOfEdges, str(edge)) if (indexEdge+1) != len(listOfEdgesOrderedByValue) else u'{0}\t{1}'.format(stringOfEdges, str(edge))
	#coloration
	stringOfEdges = stringOfEdges.replace(currentEdge, u'\033[1;31m{0}\033[0m'.format(currentEdge))
	return stringOfEdges


def edgeUsefulnessEval(sampleEdgeDf, corefDict):
	'''
	makes an evaluation of the edge usefulness by asking
	the evaluator if the red edge on the list seems useful
	for the occupation (at least as much as the other edges)

	(Used to be named relevance evaluation)
	'''
	#add the columns preparing for the data
	sampleEdgeDf[u'edgeUsefulnessAnnotation'] = np.nan
	for edgeIndex, edgeRow in sampleEdgeDf.iterrows():
		print('-----edge Nb {0}/{1}'.format(edgeIndex, len(sampleEdgeDf)))
		#print the edge
		stringOfEdges = getPrintableStringOfGoodEdges(sampleEdgeDf, edgeRow, corefDict)
		print(stringOfEdges)
		#get annotator input
		sampleEdgeDf, stop = savingAnnotatorInput(sampleEdgeDf, u'edgeUsefulnessAnnotation', edgeIndex, nbOfLines=len(stringOfEdges.split(u'\n'))+2, listOfAnswers=[0,1,2])
		#if the user asks to stop, then we stop where we were and we dumpt the data frame
		if stop == True:
			break
	return sampleEdgeDf
	

def filterEval(sampleNodeDf, corefDict):
	'''
	makes an evaluation of the quality of the filter by
	asking the annotator to specify if there is an error
	in the node and what kind of error it is
	'''
	#add the columns preparing for the data
	sampleNodeDf[u'nodeAnnotationFilter'] = np.nan	
	for nodeIndex, nodeRow in sampleNodeDf.iterrows():		
		print('-----node Nb {0}/{1}'.format(nodeIndex, len(sampleNodeDf)))
		#print the node
		print(nodeRow[u'Label'])
		#get and save the annotator input
		sampleNodeDf, stop = savingAnnotatorInput(sampleNodeDf, u'nodeAnnotationFilter', nodeIndex, nbOfLines=3, listOfAnswers=[0,1,2,3,4,5,6])
		#if the user asks to stop, then we stop where we were and we dumpt the data frame
		if stop == True:
			break
	return sampleNodeDf


def taxonomyEval(sampleNodeDf, corefDict):
	'''
	makes a taxonomy evaluation by asking the evaluator if
	the red element of the list seems to belong to the same
	domain as the others
	'''
	#avoid the SettingWithCopy Warning in pandas (https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas) 
	pd.options.mode.chained_assignment = None
	#add the columns preparing for the data
	sampleNodeDf[u'nodeAnnotationTaxo0'] = np.nan	
	sampleNodeDf[u'nodeAnnotationTaxo1'] = np.nan	
	for nodeIndex, nodeRow in sampleNodeDf.iterrows():
		print('-----node Nb {0}/{1}'.format(nodeIndex, len(sampleNodeDf)))
		#look what substring does the row label contains,  __s or __t (source or target)
		if nodeRow.str.contains(u'__s', regex=False)[u'Id'] == True:
			substring = u'__s'
			typeOfNode = u'jobtitle'
		else: 
			substring = u'__t'
			typeOfNode = u'skill'
		#get only rows of the same kind of substring 
		sourceOrTargetNodes = sampleNodeDf[sampleNodeDf[u'Id'].str.contains(substring, regex=False) == True]

		#print the name of the infered community level 0
		print(u'Infered name of the community Lvl-0: {0}'.format(nodeRow[u'Infered_Community_Name_Lvl_0']))
		print(u'---------------------------------------------------------------------------------')
		#level 0 taxonomy
		stringOfNodes = getPrintableStringOfGoodNodes(sourceOrTargetNodes, sampleNodeDf, nodeRow, corefDict, typeOfNode, communityColumnName=u'Community_Lvl_0')
		#print the node and its group	
		print(stringOfNodes)
		#get annotator input
		sampleNodeDf, stop = savingAnnotatorInput(sampleNodeDf, u'nodeAnnotationTaxo0', nodeIndex, nbOfLines=len(stringOfNodes.split(u'\n'))+3) 
		#if the user asks to stop, then we stop where we were and we dumpt the data frame
		if stop == True:
			break

		#print the name of the infered community level 1
		print(u'Infered name of the community Lvl-1: {0}'.format(nodeRow[u'Infered_Community_Name_Lvl_1']))
		print(u'---------------------------------------------------------------------------------')
		#level 1 taxonomy
		stringOfNodes = getPrintableStringOfGoodNodes(sourceOrTargetNodes, sampleNodeDf, nodeRow, corefDict, typeOfNode, communityColumnName=u'Community_Lvl_1')
		#reorder the nodes in case the level1 sleection is exactly like the one from level 0
		listOfNodes = stringOfNodes.split(u'\n')
		listOfNodes.remove(u'')
		stringOfNodes = u'\n'.join(list(set(listOfNodes))+[u''])
		#print the node and its group	
		print(stringOfNodes)
		#get annotator input
		sampleNodeDf, stop = savingAnnotatorInput(sampleNodeDf, u'nodeAnnotationTaxo1', nodeIndex, nbOfLines=len(stringOfNodes.split(u'\n'))+4, listOfAnswers=[0,1,2]) 
		#if the user asks to stop, then we stop where we were and we dumpt the data frame
		if stop == True:
			break
	return sampleNodeDf


def inferenceEval(sampleNodeDf, corefDict):
	'''
	makes an evaluation of the infered name for the domain in
	each taxonomy level by comparing a given node with a sample
	of the ESCO nodes contained in the ESCO domain infered
	e.g, 
	- given node: Quantitative Analyst Intern__s
	- ESCO domain infered for given node: 311___Physical and engineering science technicians
	- sample of ESCO nodes: 
		metallurgical technician, 
		resilient floor layer,
		foreign exchange trader,
		marine engineering technician,
		domestic energy assessor.
	'''
	#avoid the SettingWithCopy Warning in pandas (https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas) 
	pd.options.mode.chained_assignment = None
	#add the columns preparing for the data
	sampleNodeDf[u'nodeAnnotationInfer0'] = np.nan	
	sampleNodeDf[u'nodeAnnotationInfer1'] = np.nan	
	#ESCO paths
	edgeFilePath = u'/u/alfonsda/Documents/DOCTORAT_TAL/004projetOntologie/001ontologies/ESCO/v1.0.2/edgeAndNodeList/ESCOedgeList.tsv'
	nodeFilePath = u'/u/alfonsda/Documents/DOCTORAT_TAL/004projetOntologie/001ontologies/ESCO/v1.0.2/edgeAndNodeList/ESCOnodeList.tsv'
	#open the ESCO edge list as a data frame	
	escoEdgeDf = pd.read_csv(edgeFilePath, sep=u'\t')
	#open the ESCO node list as a data frame	
	escoNodeDf = pd.read_csv(nodeFilePath, sep=u'\t')
	#lowercase the label column data
	sampleNodeDf['Label'] = sampleNodeDf['Label'].str.lower()
	#limit the node dataframe to the nodes that we can find in the ESCO ontology
	mergedNodeDf = pd.merge(sampleNodeDf, escoNodeDf, how=u'inner', on=[u'Label'])
	sampleNodeDf = sampleNodeDf.loc[sampleNodeDf[u'Id'].isin(mergedNodeDf[u'Id_x'])]
	#use only the rows with source nodes (__s), since target nodes do not have a domain code
	sourceNodes = sampleNodeDf[sampleNodeDf[u'Id'].str.contains(u'__s', regex=False) == True]

	for indexSourceNode, (nodeIndex, nodeRow) in enumerate(sourceNodes.iterrows()):
		print('-----node Nb {0}/{1}  (index of node: {2})'.format(indexSourceNode, len(sourceNodes), nodeIndex))
		#get the esco domain number that was infered for this particular row
		inferedDomain = int(nodeRow[u'Infered_Community_Name_Lvl_0'].split(u'___')[0])

		#print the name of the infered community level 0
		print(u'Infered name of the community Lvl-0: {0}'.format(nodeRow[u'Infered_Community_Name_Lvl_0']))
		print(u'---------------------------------------------------------------------------------')
		#level 0 taxonomy
		stringOfNodes = getPrintableStringOfGoodInferenceNodes(nodeRow, escoNodeDf, inferedDomain)
		#print the node and its group	
		print(stringOfNodes)
		#get annotator input
		sampleNodeDf, stop = savingAnnotatorInput(sampleNodeDf, u'nodeAnnotationInfer0', nodeIndex, nbOfLines=len(stringOfNodes.split(u'\n'))+3) 
		#if the user asks to stop, then we stop where we were and we dumpt the data frame
		if stop == True:
			break

		#print the name of the infered community level 1
		print(u'Infered name of the community Lvl-1: {0}'.format(nodeRow[u'Infered_Community_Name_Lvl_1']))
		print(u'---------------------------------------------------------------------------------')
		#level 1 taxonomy
		stringOfNodes = getPrintableStringOfGoodInferenceNodes(nodeRow, escoNodeDf, inferedDomain)
		#reorder the nodes in case the level1 sleection is exactly like the one from level 0
		listOfNodes = stringOfNodes.split(u'\n')
		stringOfNodes = u'\n'.join(list(set(listOfNodes)))
		#print the node and its group	
		print(stringOfNodes)
		#get annotator input
		sampleNodeDf, stop = savingAnnotatorInput(sampleNodeDf, u'nodeAnnotationInfer1', nodeIndex, nbOfLines=len(stringOfNodes.split(u'\n'))+4, listOfAnswers=[0,1,2]) 
		#if the user asks to stop, then we stop where we were and we dumpt the data frame
		if stop == True:
			break
	return sampleNodeDf


def humanAnnotatorInterface(sampleEdgeFileInput, sampleNodeFileInput, corefDictPath, nameOfEvaluator='David', listOfEvaluationsToBeLaunched=[0,1,2,3]):
	'''
	terminal interface for human annotation
	3 types of annotation:
	 - edge relevance (is the skill relevant for that job title?)
	 - filter evaluation (is the node in the right language? is the node well written? must not show a named entity. must be coherent.)
	 - community/taxonomy evaluation (Sesame Street test: is this thing just like the others?)
	3 types of annotation:
	 - 0 : negative evaluation (plus other possible answers)
	 - 1 : positive evaluation
	 - 2 : neutral/doubtful evaluation
	'''
	import datetime
	#get coreference dictionary
	corefDict = utilsOs.openJsonFileAsDict(corefDictPath)
	#get dataframe
	sampleEdgeDf, sampleNodeDf = getDataFrameFromArgs(sampleEdgeFileInput, sampleNodeFileInput)

	#edge annotation relevance evaluation 
	if 0 in listOfEvaluationsToBeLaunched:
		#print instructions
		print(u'3 types of annotation: 0 = negative eval, 1 = doubtful eval, 2 = positive eval\n')
		#print instructions
		print(u'The colored edge must be useful. The non-colored edges are meant as an indication of what relevant nodes (most probably) look like.\n')
		#launching the annotation interface (in terminal)
		print(u'EDGE USEFULNESS EVALUATION:\n')
		sampleEdgeDf = edgeUsefulnessEval(sampleEdgeDf, corefDict)
		#clear the instructions in the terminal before the next kind of annotation
		utilsOs.moveUpAndLeftNLines(7, slowly=False)

		#dump the edge dataframe
		sampleEdgeDf.to_csv(u'{0}{1}{2}.tsv'.format(sampleEdgeFileInput.split(u'.tsv')[0], str(datetime.datetime.now()).replace(u' ', u'+'), nameOfEvaluator), sep='\t', index=False)
		
	#node annotation filter evaluation 
	if 1 in listOfEvaluationsToBeLaunched:
		#print instructions
		print(u'7 types of annotation: \n0 = general/other negative eval, \n1 = doubtful eval, \n2 = positive eval, \n3 = negative eval - in a foreign language, \n4 = negative eval - incoherent/non-understandable, \n5 = negative eval - has a named entity, \n6 = negative eval - erreurs orth/gramm\n')
		#print(u'must be: the right language... coherent... not having a named entity... well written.\n')
		#launching the annotation interface (in terminal)
		print(u'NODE FILTER EVALUATION):\n')
		sampleNodeDf = filterEval(sampleNodeDf, corefDict)
		#clear the instructions in the terminal
		utilsOs.moveUpAndLeftNLines(12, slowly=False)
		
		#dump the node dataframe
		sampleNodeDf.to_csv(u'{0}{1}{2}.tsv'.format(sampleNodeFileInput.split(u'.tsv')[0], str(datetime.datetime.now()).replace(u' ', u'+'), nameOfEvaluator), sep='\t', index=False)
	
	#node annotation taxonomy evaluation
	if 2 in listOfEvaluationsToBeLaunched:
		#print instructions
		print(u'3 types of annotation: 0 = negative eval, 1 = doubtful eval, 2 = positive eval\n')
		#print instructions
		print(u'The colored node must have an evident connexion with the others.\n')
		#launching the annotation interface (in terminal)
		print(u'NODE TAXONOMY EVALUATION:\n')
		sampleNodeDf = taxonomyEval(sampleNodeDf, corefDict)
		#clear the instructions in the terminal before the next kind of annotation
		utilsOs.moveUpAndLeftNLines(7, slowly=False)

		#dump the node dataframe
		sampleNodeDf.to_csv(u'{0}{1}{2}.tsv'.format(sampleNodeFileInput.split(u'.tsv')[0], str(datetime.datetime.now()).replace(u' ', u'+'), nameOfEvaluator), sep='\t', index=False)

	#node annotation taxonomic name-inference evaluation
	if 3 in listOfEvaluationsToBeLaunched:
		#print instructions
		print(u'3 types of annotation: 0 = negative eval, 1 = doubtful eval, 2 = positive eval\n')
		#print instructions
		print(u'The colored node must belong to the same domain as the non-colored nodes.\n')
		#launching the annotation interface (in terminal)
		print(u'NODE TAXONOMIC INFERENCE EVALUATION:\n')
		sampleNodeDf = inferenceEval(sampleNodeDf, corefDict)
		#clear the instructions in the terminal before the next kind of annotation
		utilsOs.moveUpAndLeftNLines(7, slowly=False)
	
		#dump the node dataframe
		sampleNodeDf.to_csv(u'{0}{1}{2}.tsv'.format(sampleNodeFileInput.split(u'.tsv')[0], str(datetime.datetime.now()).replace(u' ', u'+'), nameOfEvaluator), sep='\t', index=False)


##################################################################################
#CALIBRATION OF THE SIGMA.JS EXPORTATION OF THE GRAPH
##################################################################################

def modifyConfigAndIndexFiles(pathToTheExportationEnvironment):
	'''
	given the path to the sigma.js exportation environment (ending in 
	the folder "network/"), it changes the config.json file and the index.html
	file so they show the graph the way intended
	'''
	from shutil import copyfile

	if pathToTheExportationEnvironment[-1] != u'/':
		pathToTheExportationEnvironment = u'{0}/'.format(pathToTheExportationEnvironment)
	#copying config.json file
	configContent = {"type": "network","version": "1.0","data": "data.json","logo": {"file": "","link": "","text": ""},"text": {"more": "","intro": "","title": ""},"legend": {"edgeLabel": "","colorLabel": "","nodeLabel": ""},"features": {"search": True,"groupSelectorAttribute": True,"hoverBehavior": "default"},"informationPanel": {"groupByEdgeDirection": True,"imageAttribute": False},"sigma": {"drawingProperties": {"defaultEdgeType": "curve","defaultHoverLabelBGColor": "#002147","defaultLabelBGColor": "#ddd","activeFontStyle": "bold","defaultLabelColor": "#000","labelThreshold": 999,"defaultLabelHoverColor": "#fff","fontStyle": "bold","hoverFontStyle": "bold","defaultLabelSize": 14},"graphProperties": {"maxEdgeSize": 2,"minEdgeSize": 2,"minNodeSize": 0.25,"maxNodeSize": 2.5},"mouseProperties": {"maxRatio": 20,"minRatio": 0.75}}}
	pathConfigJson = u'{0}config.json'.format(pathToTheExportationEnvironment)
	if utilsOs.theFileExists(pathConfigJson) == True:
		os.remove(pathConfigJson)
	utilsOs.dumpDictToJsonFile(configContent, pathConfigJson) 
	#copying the logo images
	srcRali = u'./testsGephi/gephiExportSigma0/rali.png'
	dstRali = u'{0}images/rali.png'.format(pathToTheExportationEnvironment)
	srcUdem = u'./testsGephi/gephiExportSigma0/udem.png'
	dstUdem = u'{0}images/udem.png'.format(pathToTheExportationEnvironment)
	copyfile(srcRali, dstRali)
	copyfile(srcUdem, dstUdem)
	#getting the color information from the data file
	colorCommunityDict = {}
	dataDict = utilsOs.openJsonFileAsDict(u'{0}data.json'.format(pathToTheExportationEnvironment))
	for nodeDict in dataDict[u'nodes']:
		try:
			if nodeDict[u'attributes'][u'community_lvl_0'] not in colorCommunityDict:
				colorCommunityDict[nodeDict[u'attributes'][u'community_lvl_0']] = u'\t\t\t<div style="color: {0};">● {1}</div>\n'.format(nodeDict[u'color'], nodeDict[u'attributes'][u'infered_community_name_lvl_0'])
			'''
			#####################################################
			#before I changed the names of the columns
			if nodeDict[u'attributes'][u'community'] not in colorCommunityDict:
				colorCommunityDict[nodeDict[u'attributes'][u'community']] = u'\t\t\t<div style="color: {0};">● {1}</div>\n'.format(nodeDict[u'color'], nodeDict[u'attributes'][u'infered_community_name'])
			'''
		except KeyError:
			pass
	#modifying the index.html file
	with open(u'{0}index.html'.format(pathToTheExportationEnvironment)) as indexFile:
		fileLines = indexFile.readlines()
		#to add the colors
		for index, line in enumerate(fileLines):
			if line == u'\t\t<dt class="colours"></dt>\n':
				indexDivisorCol = index + 1
				break
		fileLines = fileLines[:indexDivisorCol] + [u'\t\t<dd>\n'] + list(colorCommunityDict.values()) + [u'\t\t</dd>\n'] + fileLines[indexDivisorCol+1:]
		#to change the images and urls to rali and udem
		for index, line in enumerate(fileLines):
			if line == u'\t<a href="http://www.oii.ox.ac.uk" title="Oxford Internet Institute"><div id="oii"><span>OII</span></div></a>\n':
				indexDivisorImg = index + 1
				break
		fileLines = fileLines[:indexDivisorImg-1] + [u'\t<a href="http://rali.iro.umontreal.ca/rali/en" title="RALI laboratories"><div id="RALI"><span>RALI</span></div></a>\n', 
		u'\t<a href="http://www.umontreal.ca/en/" title="UdeM"><div id="UdeM"><span>UdeM</span></div></a>\n']  + fileLines[indexDivisorImg+2:]
	utilsOs.dumpRawLines(fileLines, u'{0}index.html'.format(pathToTheExportationEnvironment), addNewline=False, rewrite=True)
	#modifying the style.css file to point to the images
	with open(u'{0}css/style.css'.format(pathToTheExportationEnvironment)) as styleFile:
		fileLines = styleFile.readlines()
		fileLines = fileLines + [u'''#UdeM {\nwidth: 198px;\nheight: 81px;\nbackground-image: url('../images/udem.png');\nbackground-repeat: no-repeat;\ndisplay:inline-block;\n}\n\n#UdeM span {\n\tdisplay:none;\n}\n\n#RALI {\nwidth: 318px;\nheight: 75px;\nbackground-image: url('../images/rali.png');\nbackground-repeat: no-repeat;\ndisplay:inline-block;\nmargin-right:10px;\n\n}\n\n#RALI span {\n\tdisplay:none;\n}\n''']
	utilsOs.dumpRawLines(fileLines, u'{0}css/style.css'.format(pathToTheExportationEnvironment), addNewline=False, rewrite=True)



