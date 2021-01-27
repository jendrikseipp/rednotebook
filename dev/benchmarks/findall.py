#!/usr/bin/env python

import os.path
import sys
import timeit

DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(DIR))

sys.path.insert(0, REPO)

N = 2500
TEXTS = ["aa " * N, "\\\\ " * N, "\\  " * N, "== " * N, "$$ " * N, "$= " * N]
ITERATIONS = 10 ** 0

for text in TEXTS:
    timer = timeit.Timer(
        "HASHTAG.findall(text)",
        setup='from rednotebook.data import HASHTAG; text = "{text}"'.format(
            **locals()
        ),
    )
    print(text[:10], timer.timeit(ITERATIONS))
