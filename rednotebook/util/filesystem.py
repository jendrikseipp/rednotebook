from __future__ import with_statement
import os
import zipfile



#from http://www.py2exe.org/index.cgi/HowToDetermineIfRunningFromExe
import imp, os, sys

def main_is_frozen():
   return (hasattr(sys, "frozen") or # new py2exe
		   hasattr(sys, "importers") # old py2exe
		   or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
   if main_is_frozen():
	   return os.path.dirname(sys.executable)
   return os.path.dirname(sys.argv[0])
#--------------------------------------------------------------------------------------------------------


if not main_is_frozen():
	appDir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
else:
	appDir = get_main_dir()
	


imageDir = os.path.join(appDir, 'images/')
frameIconDir = os.path.join(imageDir, 'redNotebookIcon/')
userHomedir = os.path.expanduser('~')
redNotebookUserDir = os.path.join(userHomedir, ".rednotebook/")
dataDir = os.path.join(redNotebookUserDir, "data/")
templateDir = os.path.join(redNotebookUserDir, "templates/")
configFile = os.path.join(redNotebookUserDir, 'configuration.cfg')
filesDir = os.path.join(appDir, 'files/')
fileNameExtension = '.txt'



def makeDirectory(dir):
	if not os.path.exists(dir):
		os.makedirs(dir)
		
def makeDirectories(dirs):
	for dir in dirs:
		makeDirectory(dir)
		
def makeFile(file, content=''):
	if not os.path.exists(file):
		with open(file, 'w') as f:
			f.write(content)
			
def makeFiles(fileContentPairs):
	for file, content in fileContentPairs:
		if len(content) > 0:
			makeFile(file, content)
		else:
			makeFile(file)
		
def getAbsPathFromAbsFileAndRelFile(absFilePath, relFilePath):
	absDir = os.path.abspath(os.path.dirname(absFilePath))
	absPath = os.path.join(absDir, relFilePath)
	return os.path.abspath(absPath)

def getAbsPathFromDirAndFilename(dir, fileName):
	return os.path.abspath(os.path.join(dir, fileName))

def dirExistsOrCanBeCreated(dir):
	if os.path.exists(dir):
		return os.path.isdir(dir)
	elif dir.endswith(os.sep) and os.path.exists(dir[:-1]):
		return False
	else:
		return True
	
def writeArchive(archiveFileName, files, baseDir='', arcBaseDir=''):
	"""
	use baseDir for relative filenames, in case you don't 
	want your archive to contain '/home/...'
	"""
	archive = zipfile.ZipFile(archiveFileName, "w")
	for file in files:
		archive.write(file, os.path.join(arcBaseDir, file[len(baseDir):]))
	archive.close()
	
def getTemplateFile(dayNumber):
	assert dayNumber in range(1,8)
	return os.path.join(templateDir, str(dayNumber) + fileNameExtension)