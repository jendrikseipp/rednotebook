import os
#import zipfile

from rednotebook.util import unicode, filesystem
from rednotebook import info



baseDir = os.path.dirname(__file__)   
      
        
def getFile(relativeFileName):
    return os.path.join(baseDir, relativeFileName)


def getFilesInDir(relativeDirName):
    foundFiles = []
    for root, dirs, files in os.walk(os.path.join(baseDir, relativeDirName)):
        if include(root):
            for file in files:            
                if include(file):
                    
                    #print 'ja'#, os.path.join(root, file)
                    foundFiles.append(os.path.join(root, file))
                #else:
                    #print 'ne'#, os.path.join(root, file)
    return foundFiles


def include(file):
    excludeList = ['.svn', '.pyc', '.zip']
    for excludeString in excludeList:
        if unicode.contains(file, excludeString):
            return False
    return True
      
        
def collectFiles():
    sourceDirs = ['rednotebook/', 'dev']
    sourceFiles = ['README.txt', 'setup.py', 'ez_setup.py', 'CHANGELOG.txt']
    
    releaseFiles = []
    for dir in sourceDirs:
        releaseFiles.extend(getFilesInDir(dir))
    
    for file in sourceFiles:
        releaseFiles.append(getFile(file))
    
    for file in releaseFiles:
        print 'adding', file
    return releaseFiles
       
        
def makeRelease():
    filesystem.writeArchive(getFile('dist/rednotebook-'+info.version+'.zip'), collectFiles(), baseDir, 'RedNotebook')
    
    
makeRelease()