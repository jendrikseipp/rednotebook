import sys
import signal
import random
import operator

def printError(message):
	print '\nERROR:', message

def floatDiv(a, b):
	return float(float(a)/float(b))

#-----------DICTIONARY-----------------------------

class ZeroBasedDict(dict):
	def __getitem__(self, key):
		if key in self:
			return dict.__getitem__(self, key)
		else:
			return 0

def getSortedDictByKeys(adict):
	'''Returns a sorted list of (key, value) pairs, sorted by key'''
	items = adict.items()
	items.sort()
	return items
   
def sortDictByKeys(adict):
	'''Returns a sorted list of values, sorted by key'''
	keys = adict.keys()
	keys.sort()
	return map(adict.get, keys)

def sortDictByValues(adict):
	'''
	Returns a sorted list of (key, value) pairs, sorted by value
	'''
	
	'''items returns a list of (key, value) pairs'''
	items = adict.items()
	items.sort(lambda (key1, value1), (key2, value2): cmp(value1, value2))
	return items


def restrain(valueToRestrain, range):
	rangeStart, rangeEnd = range
	if valueToRestrain < rangeStart:
		valueToRestrain = rangeStart
	if valueToRestrain > rangeEnd:
		entryNumber = rangeEnd
	return valueToRestrain


def getHtmlDocFromWordCountDict(wordCountDict, type):
	sortedDict = sortDictByValues(wordCountDict)
	
	if type == 'word':
		'filter short words'
		sortedDict = filter(lambda x: len(x[0]) > 4, sortedDict)
	
	oftenUsedWords = []
	numberOfWords = 42
	
	'''
	only take the longest words. If there are less words than n, 
	len(longWords) words are returned
	'''
	tagCloudWords = sortedDict[-numberOfWords:]
	if len(tagCloudWords) < 1:
		return '<html></html>'
	minCount = tagCloudWords[0][1]
	maxCount = tagCloudWords[-1][1]
	
	deltaCount = maxCount - minCount
	if deltaCount == 0:
		deltaCount = 1
	
	minFontSize = 10
	maxFontSize = 50
	
	fontDelta = maxFontSize - minFontSize
	
	htmlElements = []
	
	htmlHead = '<html><body TEXT="#000000" BGCOLOR="#FFFFFF" LINK="#000000" VLINK="#000000" ALINK="#000000">\n<center>'
	htmlTail = '</center></body></html>'
	for word, count in tagCloudWords:
		fontFactor = floatDiv((count - minCount), (deltaCount))
		fontSize = int(minFontSize + fontFactor * fontDelta)
		
		htmlElements.append('<a href="search/' + word + '">' + \
								'<span style="font-size:' + str(int(fontSize)) + 'px;">' + \
									word + \
								'</span>' + \
							'</a>' + \
							'&nbsp;'*random.randint(1,4) + '\n')
		
	random.shuffle(htmlElements)
	
	htmlDoc = htmlHead 
	htmlDoc += reduce(operator.add, htmlElements, '')
	htmlDoc += htmlTail
	
	print htmlDoc#.encode("utf-8")
	return htmlDoc


def setup_signal_handlers(redNotebook):
	'''
	Catch abnormal exits of the program and save content to disk
	Look in signal man page for signal names
	
	SIGKILL cannot be caught
	SIGINT is caught again by KeyboardInterrupt
	'''
	
	signals = [	signal.SIGHUP,  #Terminal closed, Parent process dead
				signal.SIGINT,  #Interrupt from keyboard (CTRL-C)
				signal.SIGQUIT, #Quit from keyboard
				signal.SIGABRT, #Abort signal from abort(3)
				signal.SIGTERM, #Termination signal
				#signal.SIGSTOP, #Stop process
				signal.SIGTSTP, #Stop typed at tty
				]
	
	
	def signal_handler(signum, frame):
		redNotebook.saveToDisk()
		sys.exit()


	for signalNumber in signals:
		if signalNumber != signal.SIGKILL:
			try:
				signal.signal(signalNumber, signal_handler)
			except RuntimeError:
				print 'False Signal Number:', signalNumber