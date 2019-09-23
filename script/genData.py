from __future__ import division, print_function
import numpy as np
import random
import sys

vowels = list("aeiou")
consonants = list("pbtdkgmnszrlhwy")

def genWord():
    syllables = min(5, np.random.geometric(.5))
    word = []
    for si in range(syllables):
        ci = np.random.choice(consonants)
        vi = np.random.choice(vowels)
        word += [ci, vi]

    return "".join(word)

def insertGlide(phon):
    highV = {"i" : "y", "u" : "w"}
    vowels = "aeiou"
    newPhon = []
    high = None

    for ci in "".join(phon):
        if ci in highV:
            if high: #sequence of two high vs in a row
                newPhon.append(highV[high])

            high = ci
        else:
            if high:
                if ci in vowels:
                    newPhon.append(highV[high])
                else:
                    newPhon.append(high)
                high = None

            newPhon.append(ci)

    if high:
        newPhon.append(high)

    return newPhon

def twoVowels(phon):
    vowels = "aeiou"
    newPhon = []
    prev = None

    for ci in "".join(phon):
        if ci in vowels:
            if prev and prev not in vowels:
                newPhon.append(prev)
        elif prev is not None:
            newPhon.append(prev)

        prev = ci

    newPhon.append(prev)
    return newPhon

def fusedSystem(m1s, m3s):
    m1s = dict(m1s)
    m3s = dict(m3s)

    fusedM3s = {}
    for m1 in m1s:
        for m3 in m3s:
            ln = np.random.randint(1, 3)

            value = ""
            for ii in range(ln):
                ci = np.random.choice(consonants)
                vi = np.random.choice(vowels)
                value += ci + vi

            fusedM3s[m1, m3] = value

    for m1 in sorted(m1s):
        for m3 in sorted(m3s):
            print("%s %s -> %s" % (m1, m3, fusedM3s[m1, m3]))

    def fuse(phon):
        newPhon = []

        for msp in phon:
            if msp in m1s:
                newPhon.append(m1s[msp])
                m1 = msp

            elif msp in m3s:
                newPhon.append(fusedM3s[m1, msp])

            else:
                newPhon.append(msp)

        #print(newPhon)

        return newPhon

    return fuse

def reduceVowels(stress, prob=1):
    assert(stress in ["penult", "final", "initial"])

    def process(phon):
        print("reducing", phon)

        newPhon = []
        sylls = 0

        if stress != "initial":
            pseq = reversed("".join(phon))
        else:
            pseq = "".join(phon)

        for pi in pseq:
            if pi in vowels:
                if ((stress == "penult" and sylls % 2 == 1) or
                    (stress in ["final", "initial"] and sylls % 2 == 0)):
                    newPhon.append(pi)
                else:
                    rr = random.random()
                    if rr < (1 - prob):
                        newPhon.append(pi)

                sylls += 1
            else:
                newPhon.append(pi)

        if stress != "initial":
            newPhon.reverse()

        print("returning", newPhon)
        return newPhon

    return process

def voicingAssimilation(direction):
    assert(direction in ["regressive", "progressive"])
    if direction == "progressive":
        dx = -1
    else:
        dx = 1

    voicelessToVoiced = {
        "p" : "b",
        "t" : "d",
        "k" : "g",
        "s" : "z",
    }

    voicedToVoiceless = dict([(vv, kk) 
                              for (kk, vv) in voicelessToVoiced.items()])

    #some sounds are triggers but do not themselves have substitutes
    voicelessToVoiced["h"] = None
    for vi in "rlmn":
        voicedToVoiceless[vi] = None

    def process(phon):
        newPhon = []

        print("voice assimilating", phon)

        for ind, pi in enumerate(phon):
            print("\t", ind, pi)
            if 0 <= ind + dx < len(phon):
                print("next sound", phon[ind + dx], "is a trigger?")
                if phon[ind + dx] in voicelessToVoiced:
                    newCh = voicedToVoiceless.get(pi, pi)
                elif phon[ind + dx] in voicedToVoiceless:
                    newCh = voicelessToVoiced.get(pi, pi)
                else:
                    newCh = pi

                if newCh == None:
                    newCh = pi

                print("\t->", newCh)

                newPhon.append(newCh)
            else:
                newPhon.append(pi)

        print("produced", newPhon)

        return newPhon

    return process

def choose(morph):
    if len(morph[0]) == 3:
        probs = [xx[2] for xx in morph]
        vals = [xx[:2] for xx in morph]

        sample = np.where(np.random.multinomial(1, probs))[0][0]
        return vals[sample]
    else:
        return random.choice(morph)

def genLanguage(name, morphs, phonology, nStems=200, nGen=1000):
    assert("stem" in morphs)

    stems = set()
    while len(stems) < nStems:
        stems.add(genWord())

    stems = [("STEM=%d" % ind, stem) for ind, stem in enumerate(stems)]

    stemFile = file("data/stems-%s.txt" % name, "w")
    for stemInd, stem in stems:
        stemFile.write("%s %s\n" % (stemInd, stem))

    instances = set()
    for inst in range(nGen):
        word = []

        for morph in morphs:
            if morph is "stem":
                word.append(random.choice(stems))
            else:
                mi = choose(morph)
                word.append(mi)

        feats = [f0 for (f0, f1) in word]
        phon = [f1 for (f0, f1) in word]

        for fn in phonology:
            phon = fn(phon)

        phon = "".join(phon)

        #print(feats, "=>", phon)
        instances.add((tuple(feats), phon))

    of = open("data/instances-%s.train" % name, "w")
    for (feats, phon) in instances:
        of.write(" ".join(['"%s"' % fi for fi in feats]) + "\n")
        of.write(" ".join(['"%s"' % ci for ci in phon]) + "\n")

def setPr(morphs, rate):
    assert(len(morphs) == 2)
    newMorphs = []
    prs = [rate, 1 - rate]
    for mi, pi in zip(morphs, prs):
        newMorphs.append( mi + (pi,) )
    return newMorphs

if __name__ == "__main__":
    m1s = [("M1=I", "ta"), 
           ("M1=II", "mu"), 
           ("M1=III", "ko"), 
           ("M1=IV", "he"), 
           ("M1=V", "gu"), 
           ("M1=VI", "si"), 
           ]

    m2s = [("M2=I", "sa"), 
           ("M2=II", ""), 
           ]

    m3s = [("M3=I", "i"), 
           ("M3=II", "a"), 
           ("M3=III", "de"), 
           ("M3=IV", "no"), 
           ]

    m1sFused = []
    for msp, morph in m1s:
        m1sFused.append((msp, msp))
    m3sFused = []
    for msp, morph in m3s:
        m3sFused.append((msp, msp))

    m2bs = [("M2B=I", "be"), 
             ("M2B=II", ""), 
         ]

    languages = [
        ["A", [m1s, m3s, "stem"], []],
        ["B", [m1sFused, m3sFused, "stem"], [fusedSystem(m1s, m3s)]],
        ["C", [m1s, m3s, "stem"], [insertGlide, twoVowels]]]

    for rate in [0, .25, .5, .75, 1]:
        m2Pr = setPr(m2s, rate)
        languages.append(
            ["D%d" % int(100 * rate),
             [m1s, m2Pr, m3s, "stem"], [insertGlide, twoVowels]])

    for rate in [0, .25, .5, .75, 1]:
        m2Pr = setPr(m2s, rate)
        m2bPr = setPr(m2bs, rate)
        languages.append(
            ["E%d" % int(100 * rate),
             [m1s, m2Pr, m2bPr, m3s, "stem"], [insertGlide, twoVowels]])

    m3CVs = [("M3=I", "pi"), 
           ("M3=II", "ka"), 
           ("M3=III", "de"), 
           ("M3=IV", "no"), 
           ]
    
    languages += [
        ["F", ["stem", m1s, m3CVs], []],
        ["G", ["stem", m1s, m3CVs], [reduceVowels(stress="final")]],
        ]

    for rate in [0, .25, .5, .75, 1]:
        languages.append(
            ["H%d" % int(100 * rate),
             ["stem", m1s, m3CVs], 
             [reduceVowels(stress="final", prob=rate),
              voicingAssimilation(direction="progressive")]])

    for rate in [0, .25, .5, .75, 1]:
        languages.append(
            ["I%d" % int(100 * rate),
             ["stem", m1s, m3CVs], 
             [reduceVowels(stress="initial", prob=rate),
              voicingAssimilation(direction="progressive")]])

    genLang = sys.argv[1]
    language = None
    for li in languages:
        if li[0] == genLang:
            language = li
            break

    assert(language)

    genLanguage(*language)

