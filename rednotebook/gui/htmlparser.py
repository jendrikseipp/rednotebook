from HTMLParser import HTMLParser
import re

html = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head><body>Normal <u>underlined</u><br/>
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
<h1>Title</h1>
</body></html>
'''

class Tag(object):
    def __init__(self, name, type, attrs=None):
        self.name = name
        self.type = type
        if attrs:
            self.attrs = dict(attrs)
        else:
            self.attrs = attrs

class DataElement(object):
    def __init__(self, data):
        self.data = data


class T2THtmlParser(HTMLParser):

    def __init__(self, *args, **kargs):
        HTMLParser.__init__(self, *args, **kargs)

        self.markup = ''

        self.stack = []

        self.state = None
        self.parsing_link = False
        self.linkname = ''

        self.symmetric_tags = { 'b': '**',
                                'u': '__',
                                'i': '//',
                                's': '--',
                                'h1': '=',
                                'h2': '==',
                                'h3': '===',
                                }

        self.starttags = {  'p': '\n\n',
                            'li': '- ',
                            }

        self.endtags = {    'li': '\n',}

        self.startendtags = {
                                'br': '\n',
                                'hr': '='*20,
                            }

    def append(self, text):
        self.markup += text

    def handle_starttag(self, tag, attrs):
        print "Beginning of a %s tag," % tag,
        print #attrs

        if tag == 'a':
            self.parsing_link = True

        if tag in self.symmetric_tags:
            self.append(self.symmetric_tags.get(tag))
        elif tag in self.starttags:
            self.append(self.starttags.get(tag))



        self.stack.append(Tag(tag, 'start', attrs))

    def handle_endtag(self, tag):
        print "End of a %s tag" % tag
        #closed_tag = self.stack.pop()
        #print 'STACK', self.stack
        if tag in self.symmetric_tags:
            self.append(self.symmetric_tags.get(tag))
        if tag in self.endtags:
            self.append(self.endtags.get(tag))
        elif tag == 'a':


            last_a_tag = self._get_last_occurence_of_tag('a')
            href = last_a_tag.attrs.get('href')
            #data = self._get_all_data_before_last_occurence('a')

            self.linkname = self.linkname.replace('\n', '')
            self.append('[""%s"" %s]' % (self.linkname, href))

            self.parsing_link = False
            self.linkname = ''

        # cleanup
        beautifiers = 'b i u s'.split()
        if tag in beautifiers:

            area_start = self.markup.rfind(self.symmetric_tags[tag],
                                        0, len(self.markup) - 2)

            left_markup = self.markup[:area_start]
            right_markup = self.markup[area_start:]

            print 'area_start', area_start, right_markup

            # preserve newlines by placing them behind the beautifier area
            contains_newline = '\n' in right_markup


            # No linebreaks allowed inside beautifiers
            right_markup = right_markup.replace('\n', '')

            if contains_newline:
                right_markup += '\n'

            #no_glue = re.compile(r'')

            # No spaces around beautifiers (No ** bold**)
            tags = map(lambda tag: self.symmetric_tags[tag], beautifiers)
            for tag in tags:
                right_markup = right_markup.replace(tag + ' ', tag)
                right_markup = right_markup.replace(' ' + tag, tag)

            self.markup = left_markup + right_markup


        self.stack.append(Tag(tag, 'end'))

    def handle_startendtag(self, tag, attrs):
        # Convert pairs into attribute dict
        attrs = dict(attrs)

        if tag == 'hr' and not self.markup.endswith('\n'):
            self.markup += '\n'
        if tag in self.startendtags:
            self.append(self.startendtags.get(tag))
        elif tag == 'img':
            filename = attrs.get('src')
            self.append('[""%s""]' % filename)

        self.stack.append(Tag(tag, 'startend', attrs))


    def handle_data(self, data):
        #self.stack.append(data)

        #any_char = re.compile(pattern, flags)

        # Only remove newlines between tags, not from the end of data
        stripped_data = data.strip()
        if not stripped_data:
            return
            #data = stripped_data

        if data:
            print "Data: %s" % data
            #last_tag = self._get_last_tag().name
            #assert last_tag is not None
            if self.parsing_link:
                self.linkname += data
            else:
                self.append(data)
            #return
            #current_tag = self.stack[-1]

        self.stack.append(DataElement(data))

    def _get_all_data_before_last_occurence(self, tag):
        '''
        Returns all data that occured before the last
        occurence of tag.
        '''
        all_data = ''
        for element in reversed(self.stack):
            if type(element) == Tag and element.name == tag:
                break
            if type(element) == DataElement:
                all_data = element.data + all_data
        return all_data

    def _get_last_occurence_of_tag(self, tag):
        for element in reversed(self.stack):
            if type(element) == Tag and element.name == tag:
                return element

    def _get_last_tag(self):
        for element in reversed(self.stack):
            if type(element) == Tag:
                return element


if __name__ == '__main__':
    parser = T2THtmlParser()

    parser.feed(html)

    print
    text = parser.markup

    print text

    import sys, os
    dir = os.path.join(os.path.dirname(__file__), '../../')
    sys.path.insert(0, dir)
    from rednotebook.util import markup

    print markup.convert(text, 'xhtml')
