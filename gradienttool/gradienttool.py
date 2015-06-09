from __future__ import absolute_import, division, print_function

import sys
import csv

import numpy as np
import scipy as sp

numreps = 4

inp = csv.reader(sys.stdin)

hdr = next(inp)
names = hdr[1:]
rows = []
data = []

print(names)

for l in inp:
    rows.append(l[0])
    data.append(l[1:])

data = np.asarray(data, dtype=np.float64)
data.shape = (data.shape[0],numreps,data.shape[1]//numreps)

print(data)

time = np.tile(np.linspace(0, 1, numtimepoints),numreps)
