from __future__ import division, print_function
import re
import os
import subprocess

class FST:
    def __init__(self, symbols, directory, startState="start", endState="sink",
                 osymbols=None):
        self.symbols = symbols
        if osymbols != None:
            self.osymbols = osymbols
        else:
            self.osymbols = self.symbols
        self.directory = directory
        self.arcs = {}
        self.states = { startState : 0 }
        self.sink = endState
        self.startState = startState
        self.binary = None
        self.sortedFST = {}
        self.symTab = None
        self.textFST = None

    def arc(self, s1, s2, chIn, chOut, weight=1):
        self.addState(s1)
        self.addState(s2)
        assert(chIn in self.symbols and chOut in self.osymbols),\
            "Bad symbol %s/%s" % (chIn, chOut)
        if (s1, s2) not in self.arcs:
            self.arcs[(s1, s2)] = {}
        self.arcs[(s1, s2)][chIn, chOut] = weight

    def end(self, si):
        assert(si in self.states)
        self.arc(si, self.sink, "*e*", "*e*", weight=1)
        
    def addState(self, st):
        if st not in self.states:
            self.states[st] = len(self.states)
        
    def writeSymbols(self):
        self.symtab = self.directory + "/symtab.txt"
        with open(self.symtab, "w") as fh:
            for ch, num in sorted(self.symbols.items(),
                                  key=lambda xx: xx[1]):
                fh.write("%s\t%d\n" % (ch, num))

        if self.osymbols is not self.symbols:
            self.osymtab = self.directory + "/osymtab.txt"
            with open(self.osymtab, "w") as fh:
                for ch, num in sorted(self.osymbols.items(),
                                      key=lambda xx: xx[1]):
                    fh.write("%s\t%d\n" % (ch, num))
        else:
            self.osymtab = self.symtab
                    
    def writeArcs(self):
        self.textFST = self.directory + "/fst.txt"
        with open(self.textFST, "w") as fh:
            fh.write("%s\n" % self.sink)

            for (s1, s2), trans in sorted(
                    self.arcs.items(),
                    key=lambda xx: self.states[xx[0][0]]):

                for (chIn, chOut), wt in trans.items():
                    if chIn != "*e*":
                        chIn = '"%s"' % chIn
                    if chOut != "*e*":
                        chOut = '"%s"' % chOut

                    fh.write("(%s (%s %s %s %s))\n" % (s1,
                                                          s2,
                                                          chIn,
                                                          chOut,
                                                          str(wt)))

    def write(self):
        self.writeSymbols()
        self.writeArcs()

    def compile(self):
        self.write()
        self.binary = self.directory + "/binary.fst"
        rval = os.system("fstcompile --isymbols=%s --osymbols=%s --keep_state_numbering=true %s %s" %
                         (self.symtab, self.osymtab, self.textFST, self.binary))
        if rval != 0:
            raise OSError()

    def sort(self, direction):
        if direction == "output":
            stype = "olabel"
        elif direction == "input":
            stype = "ilabel"
        else:
            assert(0)

        oname = self.directory + ("/sort-%s.fst" % stype)
            
        rval = os.system("fstarcsort --sort_type=%s %s %s" % (
            stype, self.binary, oname))

        if rval != 0:
            raise OSError()

        self.sortedFST[direction] = oname

        return oname
        
def sigmaStar(charset, directory):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    fst = FST(charset, directory)
    for ch in charset:
        if ch != "<eps>":
            fst.arc("start", "start", ch, ch)
    fst.end("start")
    fst.compile()

    return fst

def acceptor(string, charset, directory):
    try:
        os.mkdir(directory)
    except OSError:
        pass

    fst = FST(charset, directory)
    prevS = "start"
    for ind, ci in enumerate(string):
        dest = "st-%d-%s" % (ind, ci)
        fst.arc(prevS, dest, ci, ci)
        prevS = dest 
    fst.end(dest)
    fst.write()

    return fst
    
def compose(fst1, fst2, fname):
    try:
        os.mkdir(fname)
    except OSError:
        pass

    name1 = fst1.sort("output")
    name2 = fst2.sort("input")
    rval = os.system("fstcompose %s %s %s/binary.fst" % (name1, name2, fname))
    if rval != 0:
        raise OSError()

    fst = FST(None, fname)
    fst.binary = "%s/binary.fst" % fname
    return fst

def decompose(fsts):
    def findBin(fst):
        for dr in ["output", "input"]:
            if dr in fst.sortedFST:
                return fst.sortedFST[dr]
        return fst.binary

    #print("cmd", "src/decompose %s" % " ".join([fst.binary for fst in fsts]))
    lines = subprocess.check_output(["src/decompose"] +
                                    [findBin(fst) for fst in fsts],
                                    stderr=subprocess.STDOUT)
    # print("LINES", lines)
    res = [None for xx in fsts]

    for line in lines.split("\n"):
        #print(line)
        mtch = re.search("INFO: Fst (\d+) best state sequence : (.*)", line)
        if mtch:
            fstN, states = mtch.groups()
            print("FST:", fstN, "states", states)
            fstN = int(fstN) - 1
            states = [int(xx) for xx in states.split()]
            fst = fsts[fstN]
            fst.rState = dict([(vv, kk) for (kk, vv) in fst.states.items()])
            states = [fst.rState[xx] for xx in states]
            print(states)
            res[fstN] = states

    return res
