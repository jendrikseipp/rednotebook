from __future__ import with_statement

from rednotebook.util import filesystem
from rednotebook.util import utils

class Config(dict):
	
	def __init__(self):
		dict.__init__(self)
		
		keyValuePairs = []
		
		with open(filesystem.configFile, 'r') as configFile:
			keyValuePairs = configFile.readlines()
			
		if keyValuePairs:
			'something could be read'
			
			'delete whitespace'
			keyValuePairs = map(lambda line: line.strip(), keyValuePairs)
			
			'delete empty lines'
			keyValuePairs = filter(lambda line: len(line) > 0, keyValuePairs)
			
			'read keys and values'
			for keyValuePair in keyValuePairs:
				if '=' in keyValuePair:
					try:
						key, value = keyValuePair.split('=')
						
						try:
							'Save value as int if possible'
							valueInt = int(value)
							self[key] = valueInt
						except ValueError:
							self[key] = value
							
					except Exception:
						utils.printError('The line "' + keyValuePair + \
										'" in the config file contains errors')
						
	def read(self, key, default):
		if self.has_key(key):
			return self.get(key)
		else:
			return default
						
	def saveToDisk(self):
		with open(filesystem.configFile, 'w') as configFile:
			for key, value in self.iteritems():
				configFile.write(key + '=' + str(value) + '\n')
			print 'Configuration has been saved'
        

