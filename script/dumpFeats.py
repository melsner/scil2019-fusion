from __future__ import division, print_function
import sys
import re 
from subprocess import check_output, STDOUT, PIPE

dfile = open(sys.argv[1])

lines = dfile.readlines()

fsets = set()
for ind, line in enumerate(lines):
    if ind % 2 == 0:
        fsets.add(tuple(line.strip().split()))

#print("Known terms", fsets)

for fset in fsets:
    #print("EXEC", fset)
    tmpf = open("scratch/fset.txt", "w")
    tmpf.write("sink\n")
    for ind, feat in enumerate(fset):
        tmpf.write("(%d (%d *e* %s))\n" % (ind, ind + 1, feat))
    tmpf.write("(%d (sink *e* *e*))\n" % (ind + 1))
    tmpf.close()

    out = check_output(["carmel/build/carmel", "-k", "5", "-OE", 
                        "scratch/fset.txt", sys.argv[2]], stderr=PIPE)

    print("Features", fset, "->")
    print(out)

