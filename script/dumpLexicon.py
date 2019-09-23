from __future__ import division, print_function
import sys
import re 
from subprocess import check_output, STDOUT, PIPE

infile = open(sys.argv[1])

lines = infile.readlines()

isyms = set()
for line in lines:
    if " " not in line:
        continue
    firstSpace = line.index(" ")
    starting = line[:firstSpace]
    rest = line[firstSpace:]
    syms = re.findall("\(\S+ (\"\S+\") ", rest)
    isyms.update(syms)

#print("Known terms", isyms)

def sortStem(xx):
    xx = xx.replace('"', "")

    if xx.startswith("STEM"):
        return ("STEM", int(xx.split("=")[-1]))
    else:
        return xx.count("|"), xx.split("=")

for isym in sorted(isyms, key=sortStem):
    #print("EXEC", isym)
    tmpf = open("scratch/isym.txt", "w")
    tmpf.write("sink\n")
    tmpf.write("(0 (1 *e* %s))\n" % isym)
    tmpf.write("(1 (sink *e* *e*))\n")
    tmpf.close()

    out = check_output(["carmel/build/carmel", "-k", "4", "-OE", 
                        "scratch/isym.txt", sys.argv[1]], stderr=PIPE)

    options = out.split("\n")
    if options[0].split()[-1] == "1":
        chars = options[0].split()[:-1]
        chars = [ch.replace('"', "") for ch in chars]
        print("Symbol", isym, "->", "".join(chars))
    else:
        print("Symbol", isym, "->")
        for opt in options:
            if not opt.strip():
                continue
            chars = opt.split()
            try:
                pr = chars.pop(-1)
            except IndexError:
                pr = 0
            chars = [ch.replace('"', "") for ch in chars]
            print("\t", "".join(chars), pr)
