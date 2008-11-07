def floatDiv(a, b):
    return float(float(a)/float(b))

#-----------DICTIONARY-----------------------------

class ZeroBasedDict(dict):
    def __getitem__(self, key):
        if key in self:
            return dict.__getitem__(self, key)
        else:
            return 0

def getSortedDict(adict):
    items = adict.items()
    items.sort()
    return items

def _dictValuesSortFunction(x,y):
    return cmp(x[1], y[1])

def getSortedDictByValues(adict):
    items = adict.items()
    items.sort(_dictValuesSortFunction)
    return items