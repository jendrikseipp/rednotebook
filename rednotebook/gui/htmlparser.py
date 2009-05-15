from HTMLParser import HTMLParser

html = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>TestPage</title>
</head><body>Normal <u>Text</u><br/>
<b><div style="text-align: left"><tt>Bold Text<br/>
</tt></div></b><div style="text-align: left"><tt><i>Italic<br/>
</i><br/>
<br/>
</tt></div><br/>
<img src="080205.jpg" width="200" height="200" /><br/>

 <ul><li>Liste</li>
<li>zweites <span style="font-size: 10pt">Element</span></li>

<li style="list-style-type: none"><ul><li><span style="font-size: 10pt">eingerueckt</span></li>

</ul>
</li>
</ul>

<ul>
<li>Liste</li>
<li>Second Item</li>
  
  <ul>
  <li>Eingerueckt
  </li>
  
</ul>
</li>
</ul>

 <br/>
<a href="www.heise.de">Heise<br/>
</a><hr/><br/>
</body></html>
'''

class Tag(object):
    def __init__(self, name):
        pass

class MyHTMLParser(HTMLParser):
    
    def __init__(self, *args, **kargs):
        HTMLParser.__init__(self, *args, **kargs)
    
        self.markup = ''
    
        self.tag_stack = []
    
        self.state = None
        
        self.symmetric_tags = {	'b': '**',
        						'u': '__',
        						'i': '//',
        						's': '--',
        						}
        
        self.starttags = {	'p': '\n\n',
        					'li': '- ',
        					}
        
    def append(self, text):
    	self.markup += text

    def handle_starttag(self, tag, attrs):
        print "Beginning of a %s tag," % tag,
        print #attrs
        
        if tag in self.symmetric_tags:
            self.append(self.symmetric_tags.get(tag))
        elif tag in self.starttags:
            self.append(self.starttags.get(tag))
        
        self.tag_stack.insert(-1, tag)

    def handle_endtag(self, tag):
        print "End of a %s tag" % tag
        #closed_tag = self.tag_stack.pop()
        print 'STACK', self.tag_stack
        
    def handle_startendtag(self, tag, attrs):
    	if tag in self.startendtags:
    		self.append('STARTENDTAG')
        
    def handle_data(self, data):
        #data = data.strip()
        if data:
            print "Data: %s" % data
            self.append(data)
            return
            current_tag = self.tag_stack[-1]
            if current_tag == 'title':
            	self.markup += data + '\n'
            elif current_tag == 'h2':
            	self.markup += data + '\n'
            elif current_tag == 'h3':
            	self.markup += '### ' + data + ' ###\n'
            elif current_tag == 'h3':
            	self.markup += data + '\n'

parser = MyHTMLParser()

parser.feed(html)

print
print parser.markup
