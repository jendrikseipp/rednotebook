def printUnicode(unicodeString):
    print unicodeString.encode("latin-1")
    
def substring(s, start=0, end=None):
    if end == None:
        end = len(s)  
    if start < 0:
        start = 0
    if end > len(s):
        end = len(s)
    return s[start:end]

def contains(string, substring):
    return string.find(substring) > -1