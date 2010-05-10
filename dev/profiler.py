import sys

sys.path.insert(0, '../rednotebook')

def main():
	import redNotebook
	rn = redNotebook.main()

import cProfile
import pstats
cProfile.run('main()', 'Profile.prof')
s = pstats.Stats("Profile.prof")
# time or cumulative
s.sort_stats("cumulative").print_stats('.*rednotebook.*\d(?!\(<module>\))')
#s.strip_dirs().sort_stats("time").print_stats()
