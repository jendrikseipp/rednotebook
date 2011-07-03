#!/usr/bin/env python

"""
Needs the python-profiler package.
"""

import sys
import cProfile

import pstats
import gtk

sys.path.insert(0, '../rednotebook')

def main():
    import journal
    journal.Journal()

cProfile.run('main()', 'Profile.prof')
#s = pstats.Stats("Profile.prof")

# time or cumulative
#s.sort_stats("cumulative").print_stats('.*rednotebook.*\d(?!\(<module>\))')
##s.strip_dirs().sort_stats("time").print_stats()
