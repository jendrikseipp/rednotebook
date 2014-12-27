# -*- coding: utf-8 -*-

import tempfile

from rednotebook import configuration


def test_io():
    with tempfile.NamedTemporaryFile() as f:
        c1 = configuration.Config(f.name)
        c1['a'] = 1
        c1.write_list('b', ['foo', u'bär'])
        c1.save_to_disk()
        c2 = configuration.Config(f.name)
        assert c1 == c2
        assert c2.read_list('b', []) == ['foo', u'bär']


def test_changed():
    with tempfile.NamedTemporaryFile() as f:
        c = configuration.Config(f.name)
        assert not c.changed()
        c['a'] = 1
        assert c.changed()
        c.save_to_disk()
        assert not c.changed()
        c.read('a', 'foo')
        assert not c.changed()
        c.read_list('a', 'foo')
        assert not c.changed()
        c.read('b', 'bar')
        assert c.changed()
        c.save_to_disk()
        assert not c.changed()
        c.read_list('c', 'baz')
        assert c.changed()
