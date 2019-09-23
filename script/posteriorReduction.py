from __future__ import division, print_function
import sys
import os
import re
import numpy as np

if __name__ == "__main__":
    dirName = sys.argv[1]

    totalReducing = 0
    totalNonReducing = 0

    for fst in os.listdir(dirName):
        if "reduce-v" in fst or "reduce-init" in fst:
            fullName = dirName + "/" + fst

            if "reduce-v" in fst:
                keyState = 3
            else:
                keyState = 5

            with open(fullName) as fh:
                reducing = 0
                nonReducing = 0

                prs = {}

                for line in fh:
                    if line.startswith("(%d " % keyState):
                        evts = re.findall("\(\d+ [^()]+\)", line)
                        #print("evts",evts)
                        for evt in evts:
                            evt = evt.replace("(", "").replace(")", "")
                            flds = evt.split()

                            if int(flds[0]) != keyState:
                                pr = float(flds.pop(-1))
                                prs[int(flds[0])] = pr

                    for state in prs:
                        if line.startswith("(%d " % state):
                            if "*e*" in line:
                                reducing = prs[state]
                            else:
                                nonReducing = prs[state]

                norm = (reducing + nonReducing)
                if norm == 0:
                    norm += 1

                print("R: %.3g -R: %.3g" % (
                    reducing / norm,
                    nonReducing / norm))

                totalReducing += reducing
                totalNonReducing += nonReducing

    print("-------Total--------")
    norm = (totalReducing + totalNonReducing)
    if norm == 0:
        norm += 1
    print("R: %.3g -R: %.3g" % (
        totalReducing / norm,
        totalNonReducing / norm))
