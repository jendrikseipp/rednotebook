# -*- coding: utf-8 -*-
import htmlentitydefs

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
   
def make_transdict():
	'''
	returns a dict that maps unicode chars to corresponding 
	chars without tildes etc.
	'''
	cp2n = htmlentitydefs.codepoint2name
	#suffixes = 'acute crave circ uml slash tilde cedil'.split()
	suffixes = htmlentitydefs.name2codepoint.keys()
	td = {}
	for x in range(128, 256):
		if x not in cp2n: continue
		n = cp2n[x]
		for s in suffixes:
			if n.endswith(s):
				td[x] = unicode(n[-len(s)])
				break
	return td

def coll(us, td=make_transdict()):
	'''
	Unicode sort function
	
	Usage:
	unicodeStrings = [u'\xe9cole', u'ecole', u'las', u'laß', u'lax', \
						u'ueber', u'über', u'zer']
	unicodeStrings.sort(key=coll)
	'''
	if type(us) is not unicode:
		us = unicode(us, errors='replace')
	return us.translate(td)

def replace_html_encoding(text):
	dict = {'%20': ' '}
	result = text
	for htmlText, normalText in dict.iteritems():
		result = result.replace(htmlText, normalText)
	return result

