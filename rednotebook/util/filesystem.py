import os

appDir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
imageDir = os.path.join(appDir, 'images/')
userHomedir = os.path.expanduser('~')
redNotebookUserDir = os.path.join(userHomedir, ".rednotebook/")
dataDir = os.path.join(redNotebookUserDir, "data/")
fileNameExtension = '.txt'

def makeDirectory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
        
def makeDirectories(dirs):
    for dir in dirs:
        makeDirectory(dir)
        
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