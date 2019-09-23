from __future__ import division, print_function
import sys
import os
import re
import numpy as np

if __name__ == "__main__":
    origFile = sys.argv[1]

    fusionNames = []
    fusionNamesPost = []
    for line in open(origFile):
        if "start" in line:
            name = re.match("\(start \((\S+) ", line)
            fusionNames.append(name.group(1))

        if "postStem" in line:
            name = re.match("^\(postStem \((\S+) ", line)
            if name:
                fusionNamesPost.append(name.group(1))

    dirName = sys.argv[2]

    nameCts = {}
    for name in fusionNames:
        nameCts[name] = []

    nameCtsPost = {}
    for name in fusionNamesPost:
        nameCtsPost[name] = []

    # print("FUSE NAMES", fusionNames)
    # print("POST", fusionNamesPost)

    for fst in os.listdir(dirName):
        if "features" in fst:
            fullName = dirName + "/" + fst

            with open(fullName) as fh:
                sink = next(fh)
                fusions = next(fh)

                evts = re.findall("\(\d+ [^()]+\)", fusions)
                for evt in evts:
                    evt = evt.replace("(", "").replace(")", "")
                    fuseTp, pr = evt.split()
                    fuseTp = fusionNames[int(fuseTp) - 1]
                    pr = float(pr)

                    nameCts[fuseTp].append(pr)

                if len(fusionNames) > 1:
                    for fuseTp in sorted(nameCts.keys()):
                        print("%s: %.3g" % 
                              (fuseTp, nameCts[fuseTp][-1]), end="\t")
                    print()

                stems = ""
                while "STEM" not in stems:
                    stems = next(fh)

                fusions = next(fh)

                evts = re.findall("\(\d+ [^()]+\)", fusions)
                tp0 = None
                for evt in evts:
                    evt = evt.replace("(", "").replace(")", "")
                    fuseTp, pr = evt.split()
                    if tp0 is None:
                        tp0 = int(fuseTp)
                    fuseTp = fusionNamesPost[int(fuseTp) - tp0]
                    pr = float(pr)

                    nameCtsPost[fuseTp].append(pr)

                if len(fusionNamesPost) > 1:
                    for fuseTp in sorted(nameCtsPost.keys()):
                        print("Suffix: %s: %.3g" % 
                              (fuseTp, nameCtsPost[fuseTp][-1]), end="\t")
                    print()

    if len(fusionNames) > 1:
        print("%d files" % len(list(nameCts.values())[0]))
        print("--------Total----------")

        for fuseTp in sorted(nameCts.keys()):
            print("%s: %.3g" % (fuseTp, np.mean(nameCts[fuseTp])))


    if len(fusionNamesPost) > 1:
        print("%d files" % len(list(nameCtsPost.values())[0]))
        print("--------Total (suffixes)----------")

        for fuseTp in sorted(nameCtsPost.keys()):
            print("%s: %.3g" % (fuseTp, np.mean(nameCtsPost[fuseTp])))
