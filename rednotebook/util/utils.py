import sys
import signal

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
				signal.SIGSTOP, #Stop process
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