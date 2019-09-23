from __future__ import division, print_function
import sys
import os
from fstCarmel import *
from collections import defaultdict
import numpy as np

# def readData(fh):
#     for line in fh:
#         print(line)
#         word, feats = line.strip().split("\t")
#         feats = [xx.split("=") for xx in feats.split(";")]
#         yield word, feats

def readData(fh):
    while True:
        try:
            #reps = next(fh)
            feats = next(fh)
            phon = next(fh)
            feats = feats.replace('"', "").strip().split()
            phon = phon.replace('"', "").strip().split()
            phon = "".join(phon)
            feats = [xx.split("=") for xx in feats]
            yield phon, feats
        except StopIteration:
            break

def partitions(items):
    if len(items) == 1:
        return [[ [items[0],] ]]
    else:
        xparts = partitions(items[1:])
        res = []
        for part in xparts:
            for gi in range(len(part)):
                newPart = [xx for xx in part]
                newPart[gi] = newPart[gi] + [items[0]]
                res.append(newPart)
            res.append(part + [[items[0]]])
        return res    

def linearPartitions(items):
    if len(items) == 0:
        return [[ ]]
    else:
        res = []
        for groupLength in range(1, len(items) + 1):
            currGroup = items[:groupLength]
            rest = items[groupLength:]
            moreParts = linearPartitions(rest)

            for more in moreParts:
                res.append([currGroup,] + more)

        return res

def orders(items):
    if len(items) == 1:
        yield [items[0]]
    else:
        for ii in range(len(items)):
            for order in orders(items[:ii] + items[ii + 1:]):
                yield [items[ii]] + order

def featurePowerset(data, directory):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    chars = { "*e*" : 0 }
    ochars = { "*e*" : 0 }
    canonOrder = [ftype for (ftype, fval) in data[0][1]]
    featureValues = defaultdict(set)
    for (word, feats) in data:
        for (ftype, fval) in feats:
            featureValues[ftype].add(fval)
            if (ftype, fval) not in chars:
                chars["%s=%s" % (ftype, fval)] = len(chars)

    print("feature types/vals", featureValues)

    featMachine = FST(chars, directory, osymbols=ochars)

    featureBags = [ [] ]
    for ind, ftype in enumerate(canonOrder):
        # print("Pathing on", ftype, featureBags)
        newBags = []
        for bag in featureBags:

            if bag == []:
                fromState = "start"
            else:
                fromState = ";".join(bag)

            # print("\tpaths from", fromState)

            for fval in featureValues[ftype]:
                newBags.append(bag + ["%s=%s" % (ftype, fval)])

                toState = ";".join(bag + ["%s=%s" % (ftype, fval)])

                # print("\t\tDest", toState)

                featMachine.arc(fromState,
                                toState,
                                "%s=%s" % (ftype, fval),
                                "*e*")

        featureBags = list(newBags)
        # print("current bags", featureBags)

    print("all bags", featureBags)
        
    for bag in featureBags:
        print("exiting", bag)
        bagState = ";".join(bag)
        # for partition in partitions(bag):
        #     print("\tpartition", partition)
        #     for order in orders(partition):
        #         print("\t\torder", order)
        for order in linearPartitions(bag):
            print("\tpartition", order)
            if True:
                fromState = bagState

                for sset in order:
                    print("\t\t\tgroup", sset)

                    if "|".join(sset) not in ochars:
                        ochars["|".join(sset)] = len(ochars)

                    toState = fromState + ">" + "|".join(sset)

                    featMachine.arc(fromState,
                                    toState,
                                    "*e*",
                                    "|".join(sset))

                    print("\t\t\tarc from", fromState, featMachine.states[fromState], "to", toState, featMachine.states[toState])

                    fromState = toState

                featMachine.end(toState)

    print("states of machine")
    for st, ind in featMachine.states.items():
        print(st, ind)

    return featMachine

def featureCompact(data, directory, fuseStem=True, fusePen=1):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    chars = { "*e*" : 0 }
    canonOrder = [ftype for (ftype, fval) in data[0][1]]
    featureValues = defaultdict(set)
    for (word, feats) in data:
        for (ftype, fval) in feats:
            featureValues[ftype].add(fval)
            if (ftype, fval) not in chars:
                chars["%s=%s" % (ftype, fval)] = len(chars)
    ochars = dict(chars.items())

    print("feature types/vals", featureValues)

    featMachine = FST(chars, directory, osymbols=ochars)
    fuseGroup = { None : 0}

    #backbone structure without fusion
    fromState = "start"
    for ind, ftype in enumerate(canonOrder):
        toState = "state-%s" % ftype
        fuseGroup[toState] = len(fuseGroup)
        fuseGrp = fuseGroup[toState]

        for fval in featureValues[ftype]:
            featMachine.arc(fromState,
                            toState,
                            "%s=%s" % (ftype, fval),
                            "%s=%s" % (ftype, fval),
                            #weight="%g!%d" % (10, fuseGrp))
                            weight="!1")
                            #weight=1)

        fromState = toState

    featMachine.end(fromState)

    #allow fusion... stop 2 before end because we can't fuse a single item
    for ind, startState in enumerate(["start"] + canonOrder[:-2]):
        #build a satellite state by accepting the next item
        ftype = canonOrder[ind]
        for fval in featureValues[ftype]:
            toState = "read-%s=%s" % (ftype, fval)
            if ftype not in fuseGroup:
                fuseGroup[ftype] = len(fuseGroup)
            fuseGrp = fuseGroup[ftype]

            featMachine.arc(startState,
                            toState,
                            "%s=%s" % (ftype, fval),
                            "*e*",
                            #weight="%g!%d" % (1, fuseGrp))
                            weight="!1")

            #accept at least one more item and output fused symbols
            intermeds = [( toState, [(ftype, fval)] ) ]
            for nxtState in canonOrder[ind + 1 :]:
                if not fuseStem and nxtState == "STEM":
                    break

                nextLayer = []

                for fval in featureValues[nxtState]:
                    for fromState, fromSyms in intermeds:
                        toState = ("read-" + "-".join([
                                   "%s=%s" % (tp, val) for (tp, val) in
                            fromSyms + [(nxtState, fval)]]))

                        tps = "-".join([tp for (tp, val) in
                                        fromSyms + [(nxtState, fval)]])
                        if tps not in fuseGroup:
                            fuseGroup[tps] = len(fuseGroup)
                        fuseGrp = fuseGroup[tps]
                        featMachine.arc(fromState,
                                        toState,
                                        "%s=%s" % (nxtState, fval),
                                        "*e*",
                                        #weight="%g!%d" % (1, fuseGrp))
                                        weight="!1")
                        nextLayer.append( 
                            (toState, fromSyms + [(nxtState, fval)]) )

                        spineState = "state-%s" % nxtState
                        fusedSym = "|".join(
                            ["%s=%s" % (tp, val) for (tp, val) in 
                             fromSyms + [(nxtState, fval)]])
                        if fusedSym not in ochars:
                            ochars[fusedSym] = len(ochars)

                        featMachine.arc(fromState,
                                        spineState,
                                        "%s=%s" % (nxtState, fval),
                                        fusedSym,
                                        #weight="1")
                                        weight="!1")

                intermeds = nextLayer

    return featMachine

def instantiationSets(features, values):
    prevSets = [ [] ]
    for feature in features:
        newSets = []
        for value in values[feature]:
            for prev in prevSets:
                newSet = prev + [ (feature, value) ]
                newSets.append(newSet)
                yield newSet

        prevSets = newSets

def linearFusion(features, featMachine, featureValues, start, end):
    ochars = featMachine.osymbols

    if not features:
        featMachine.arc(start, end, "*e*", "*e*")
        return

    for part in linearPartitions(features):
        print("\n\n")
        print("Fusion type", part)
        pName = "-".join(["|".join(xx) for xx in part])
        featMachine.arc(start, pName + "-0", "*e*", "*e*",
                        weight="1")

        for subInd, subset in enumerate(part):
            print("Generating", subset)

            for inst in instantiationSets(subset, featureValues):
                print("Instance", inst)

                if len(inst) == 1:
                    prevName = "%s-%d" % (pName, subInd)
                else:
                    prevName = "%s-%s" % (
                        pName, 
                        ("read-%s" % 
                         "-".join(["%s=%s" % (ft, fv)
                                   for (ft, fv) in inst[:-1]])))

                if len(inst) == len(subset):
                    oSym = "|".join(["%s=%s" % (ft, fv)
                                     for (ft, fv) in inst])
                    nxt = "%s-%d" % (pName, subInd + 1)
                else:
                    oSym = "*e*"
                    nxt = "%s-%s" % (
                        pName,
                        ("read-%s" % 
                         "-".join(["%s=%s" % (ft, fv)
                                   for (ft, fv) in inst])))

                if oSym not in ochars:
                    ochars[oSym] = len(ochars)

                featMachine.arc(prevName,
                                nxt,
                                "%s=%s" % inst[-1],
                                oSym,
                                weight="1")

                if len(inst) == len(subset) and subInd == len(part) - 1:
                    featMachine.arc(nxt,
                                    end,
                                    "*e*",
                                    "*e*",
                                    weight="1")

def featureFair(data, directory, stemName="STEM",
                fuseStem=True, fusePen=1):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    chars = { "*e*" : 0 }
    canonOrder = [ftype for (ftype, fval) in data[0][1]]
    featureValues = defaultdict(set)
    for (word, feats) in data:
        for (ftype, fval) in feats:
            featureValues[ftype].add(fval)
            if (ftype, fval) not in chars:
                chars["%s=%s" % (ftype, fval)] = len(chars)
    ochars = dict(chars.items())

    print("feature types/vals", featureValues)

    featMachine = FST(chars, directory, osymbols=ochars)

    stemInd = canonOrder.index(stemName)
    preStem = canonOrder[:stemInd]
    postStem = canonOrder[stemInd + 1:]

    linearFusion(preStem, featMachine, featureValues,
                 start="start", end="stem")

    for val in featureValues[stemName]:
        featMachine.arc("stem",
                        "postStem",
                        "%s=%s" % (stemName, val),
                        "%s=%s" % (stemName, val),
                        weight="1")

    linearFusion(postStem, featMachine, featureValues, 
                 start="postStem", end="sink")

    return featMachine

def lexicon(chars, featMachine, directory, wordLength):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    lexicon = FST(featMachine.osymbols, directory, osymbols=chars)

    for morphsyn in featMachine.osymbols:
        if "=" not in morphsyn:
            continue

        finish = morphsyn + ":end"
        lexicon.arc("start", morphsyn, morphsyn, "*e*")
        lexicon.arc(morphsyn, morphsyn + ":X", "*e*", "*e*", .1)
        lexicon.arc(morphsyn, finish, "*e*", "*e*", 10)

        prev = morphsyn + ":X"
        for ind in range(wordLength):
            state = morphsyn + ":%d" % ind
            for ch in chars:
                if ch != "*e*":
                    lexicon.arc(prev, state, "*e*", ch, weight=.1)
                elif ind > 0:
                    lexicon.arc(prev, finish, "*e*", "*e*", weight=.1)
            prev = state

        lexicon.arc(finish, "start", "*e*", "*e*")

    lexicon.end("start")

    return lexicon

def addDot(lexicon, directory):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    osyms = dict(lexicon.osymbols.items())
    osyms["."] = len(osyms)
    phon = FST(lexicon.osymbols, directory, 
               osymbols=osyms)

    for char in lexicon.osymbols:
        if char != "*e*":
            phon.arc("start", "start", char, char)

    phon.arc("start", "dot", "*e*", ".")
    phon.end("dot")

    return phon

def unDot(lexicon, directory):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    osyms = dict(lexicon.osymbols.items())
    phon = FST(lexicon.osymbols, directory)

    for char in lexicon.osymbols:
        if char != "*e*" and char != ".":
            phon.arc("start", "start", char, char)

    phon.arc("start", "dot", ".", "*e*")
    phon.end("dot")

    return phon

def bigramPhon(dot, directory, priorDel=1, priorNoDel=1):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    high = {"i" : "y", "u" : "w" }

    phon = FST(dot.osymbols, directory)
    vowels = ["a", "e", "i", "o", "u"]
    consonants = set(dot.osymbols).difference(vowels + ["*e*", "."])
    letters = set(dot.osymbols).difference(["*e*", "."])

    phon.arc("start", "yesRule", "*e*", "*e*", weight=priorDel)
    phon.arc("start", "noRule", "*e*", "*e*", weight=priorNoDel)

    for char in letters:
        phon.arc("noRule", "noRule", char, char)

    phon.arc("noRule", "end", ".", "*e*")
    phon.end("end")

    for c1 in letters:
        phon.arc("yesRule", "read-%s" % c1, c1, "*e*")
        phon.arc("yesRule", "end", ".", ".")
        phon.arc("read-%s" % c1, "end", ".", c1)

        for c2 in letters:
            if c1 in high and c2 in vowels:
                phon.arc("read-%s" % c1, "read-%s" % c2, c2, high[c1])
            elif c1 in vowels and c2 in vowels:
                #deletes arbitrarily long vowel seqs
                #phon.arc("read-%s" % c1, "read-%s" % c2, c2, "*e*")
                phon.arc("read-%s" % c1, "yesRule", c2, c2)
            else:
                phon.arc("read-%s" % c1, "read-%s" % c2, c2, c1)

    return phon

def reduceV(dot, directory, stress, priorDel=1, priorNoDel=1):
    assert(stress in ["final", "penult"])

    try:
        os.mkdir(directory)
    except OSError:
        pass

    phon = FST(dot.osymbols, directory)
    vowels = ["a", "e", "i", "o", "u"]
    consonants = set(dot.osymbols).difference(vowels + ["*e*", "."])
    letters = set(dot.osymbols).difference(["*e*", "."])

    phon.arc("start", "yesRule", "*e*", "*e*", weight=priorDel)
    phon.arc("start", "noRule", "*e*", "*e*", weight=priorNoDel)

    for char in letters:
        phon.arc("noRule", "noRule", char, char)

    phon.arc("noRule", "end", ".", ".")
    phon.end("end")

    phon.arc("yesRule", "even", "*e*", "*e*")
    phon.arc("yesRule", "odd", "*e*", "*e*")

    for c1 in consonants:
        phon.arc("even", "evenOns", c1, c1)
        phon.arc("odd", "oddOns", c1, c1)

    for v1 in vowels:
        if stress == "final":
            phon.arc("oddOns", "even", v1, v1)
            phon.arc("evenOns", "odd", v1, "*e*")
        else:
            phon.arc("oddOns", "even", v1, "*e*")
            phon.arc("evenOns", "odd", v1, v1)

    phon.arc("even", "end", ".", ".")

    return phon

def reduceVIndependent(dot, directory, stress, priorDel=1, priorNoDel=1):
    assert(stress in ["final", "penult", "initial"])

    try:
        os.mkdir(directory)
    except OSError:
        pass

    phon = FST(dot.osymbols, directory)
    vowels = ["a", "e", "i", "o", "u"]
    consonants = set(dot.osymbols).difference(vowels + ["*e*", "."])
    letters = set(dot.osymbols).difference(["*e*", "."])

    if stress != "initial":
        phon.arc("start", "odd", "*e*", "*e*")

    phon.arc("start", "even", "*e*", "*e*")

    for c1 in consonants:
        phon.arc("even", "evenOns", c1, c1)
        phon.arc("evenOns", "evenOns", c1, c1)

        phon.arc("odd", "oddOns", c1, c1)
        phon.arc("oddOns", "oddOns", c1, c1)

    for v1 in vowels:
        if stress == "final":
            phon.arc("oddOns", "even", v1, v1)

            phon.arc("evenOns", "copy", "*e*", "*e*", weight=priorNoDel)
            phon.arc("evenOns", "del", "*e*", "*e*", weight=priorDel)

            phon.arc("copy", "odd", v1, v1)
            phon.arc("del", "odd", v1, "*e*")
        else:
            phon.arc("evenOns", "odd", v1, v1)

            phon.arc("oddOns", "copy", "*e*", "*e*", weight=priorNoDel)
            phon.arc("oddOns", "del", "*e*", "*e*", weight=priorDel)

            phon.arc("copy", "even", v1, v1)
            phon.arc("del", "even", v1, "*e*")

    phon.arc("even", "end", ".", ".")
    if stress == "initial":
        phon.arc("odd", "end", ".", ".")
    phon.end("end")

    return phon

def voiceAssim(dot, directory, direction, priorDel=1, priorNoDel=1):
    assert(direction in ["progressive", "regressive"])
    try:
        os.mkdir(directory)
    except OSError:
        pass

    voicelessToVoiced = {
        "p" : "b",
        "t" : "d",
        "k" : "g",
        "s" : "z",
    }

    voicedToVoiceless = dict([(vv, kk) 
                              for (kk, vv) in voicelessToVoiced.items()])

    #some sounds are triggers but do not themselves have substitutes
    voicelessToVoiced["h"] = "h"
    for vi in "rlmn":
        voicedToVoiceless[vi] = vi

    phon = FST(dot.osymbols, directory)
    vowels = ["a", "e", "i", "o", "u"]
    consonants = set(dot.osymbols).difference(vowels + ["*e*", "."])
    letters = set(dot.osymbols).difference(["*e*", "."])

    phon.arc("start", "yesRule", "*e*", "*e*", weight=priorDel)
    phon.arc("start", "noRule", "*e*", "*e*", weight=priorNoDel)

    for char in letters:
        phon.arc("noRule", "noRule", char, char)

    phon.arc("noRule", "end", ".", "*e*")
    phon.end("end")

    for c1 in letters:
        phon.arc("yesRule", "read-%s" % c1, c1, "*e*")
        phon.arc("yesRule", "end", ".", ".")
        phon.arc("read-%s" % c1, "end", ".", c1)

        for c2 in letters:
            if direction == "regressive":
                if c2 in voicedToVoiceless and c1 in voicelessToVoiced:
                    phon.arc("read-%s" % c1, "read-%s" % c2, c2, 
                             voicelessToVoiced[c1])
                elif c1 in voicedToVoiceless and c2 in voicelessToVoiced:
                    phon.arc("read-%s" % c1, "read-%s" % c2, c2, 
                             voicedToVoiceless[c1])
                else:
                    phon.arc("read-%s" % c1, "read-%s" % c2, c2, c1)
            else:
                if c2 in voicedToVoiceless and c1 in voicelessToVoiced:
                    phon.arc("read-%s" % c1, 
                             "read-%s" % voicedToVoiceless[c2],
                             c2, c1)
                elif c1 in voicedToVoiceless and c2 in voicelessToVoiced:
                    phon.arc("read-%s" % c1,
                             "read-%s" % voicelessToVoiced[c2],
                             c2, c1)
                else:
                    phon.arc("read-%s" % c1, "read-%s" % c2, c2, c1)

    return phon

if __name__ == "__main__":
    fname = sys.argv[1]
    name = os.path.basename(fname).replace(
        ".train", "").replace("instances-", "")
    data = list(readData(open(fname)))

    print("read data")

    chars = { "*e*" : 0 }
    for (word, feats) in data:
        for ci in word:
            if ci not in chars:
                chars[ci] = len(chars)

    # print(linearPartitions([1,]))

    # print("---------")

    # print(linearPartitions([1, 2, 3]))

    # for order in orders("abcd"):
    #     print(order)
    # print("---------")
    
    # for part in partitions("dcba"):
    #     print(part)
    #     for order in orders(part):
    #         print("\t", order)

    featMachine = featureFair(data, "scratch/features-%s" % name,
                              fuseStem=False,
                              fusePen=1)
    featMachine.write()

    lexicon = lexicon(chars, featMachine, "scratch/lexicon-%s" % name, 15)
    lexicon.write()

    dot = addDot(lexicon, "scratch/dot")
    dot.write()

    undot = unDot(dot, "scratch/undot")
    undot.write()

    phon = bigramPhon(dot, "scratch/glide-insert-%s-%g" % 
                      (name, 100),
                      priorDel=1, priorNoDel=100)
    phon.write()

    phon = reduceVIndependent(dot, "scratch/reduce-vindep-%s-%g" % 
                   (name, 100),
                   stress="final",
                   priorDel=1, priorNoDel=100)
    phon.write()

    phon = reduceVIndependent(dot, "scratch/reduce-init-%s-%g" % 
                   (name, 100),
                   stress="initial",
                   priorDel=1, priorNoDel=100)
    phon.write()

    phon = voiceAssim(dot, "scratch/assimilate-voice-%s-%g" % 
                      (name, 100),
                      direction="progressive",
                      priorDel=1, priorNoDel=100)
    phon.write()
