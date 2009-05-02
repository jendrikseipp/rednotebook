

# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk, gobject, pango
from gtk import gdk



#=============================================================================
# tags and tag table


class RichTextBaseTagTable (gtk.TextTagTable):
    """A tag table for a RichTextBuffer"""

    # Class Tags:
    # Class tags cannot overlap any other tag of the same class.
    # example: a piece of text cannot have two colors, two families,
    # two sizes, or two justifications.

    
    def __init__(self):
        gtk.TextTagTable.__init__(self)

        self._tag_classes = {}
        self._tag2class = {}        


    def new_tag_class(self, class_name, class_type, exclusive=True):
        """Create a new RichTextTag class for RichTextBaseTagTable"""
        c = RichTextTagClass(class_name, class_type, exclusive)
        self._tag_classes[class_name] = c
        return c

    def get_tag_class(self, class_name):
        """Return the set of tags for a class"""
        return self._tag_classes[class_name]

    def get_tag_class_type(self, class_name):
        """Return the RichTextTag type for a class"""
        return self._tag_classes[class_name].class_type

    def tag_class_add(self, class_name, tag):
        """Add a tag to a tag class"""
        c = self._tag_classes[class_name]
        c.tags.add(tag)
        self.add(tag)
        self._tag2class[tag] = c
        return tag
        

    def get_class_of_tag(self, tag):
        """Returns the exclusive class of tag,
           or None if not an exclusive tag"""
        return self._tag2class.get(tag, None)
    

    def lookup(self, name):
        """Lookup any tag, create it if needed"""

        # test to see if name is directly in table
        #  modifications and justifications are directly stored
        tag = gtk.TextTagTable.lookup(self, name)        
        if tag:
            return tag

        # make tag from scratch
        for tag_class in self._tag_classes.itervalues():
            if tag_class.class_type.is_name(name):
                tag = tag_class.class_type.make_from_name(name)
                self.tag_class_add(tag_class.name, tag)
                return tag
        
        
        raise Exception("unknown tag '%s'" % name)



class RichTextTagClass (object):
    """
    A class of tags that specify the same attribute


    Class tags cannot overlap any other tag of the same class.
    example: a piece of text cannot have two colors, two families,
    two sizes, or two justifications.

    """

    def __init__(self, name, class_type, exclusive=True):
        """
        name:        name of the class of tags (i.e. "family", "fg_color")
        class_type:  RichTextTag class for all tags in class
        exclusive:   bool for whether tags in class should be mutually exclusive
        """
        
        self.name = name
        self.tags = set()
        self.class_type = class_type
        self.exclusive = exclusive



class RichTextTag (gtk.TextTag):
    """A TextTag in a RichTextBuffer"""
    def __init__(self, name, **kargs):
        gtk.TextTag.__init__(self, name)

        for key, val in kargs.iteritems():
            self.set_property(key.replace("_", "-"), val)

    def can_be_current(self):
        return True

    def can_be_copied(self):
        return True

    def is_par_related(self):
        return False

    @classmethod
    def tag_name(cls):
        # NOT implemented
        raise Exception("Not implemented")

    @classmethod
    def get_value(cls, tag_name):
        # NOT implemented
        raise Exception("Not implemented")

    @classmethod
    def is_name(cls, tag_name):
        return False

    @classmethod
    def make_from_name(cls, tag_name):        
        return cls(cls.get_value(tag_name))
