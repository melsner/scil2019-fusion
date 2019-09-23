from __future__ import division, print_function
import argparse
import sys
import os
from subprocess import *
import tempfile
import shutil

def run(invocation, data, fsts, runDir, index):
    #with tempfile.TemporaryDirectory() as tempD: #newer than module version

    tempD = tempfile.mkdtemp()

    if tempD:

        print("Temporary files in", tempD)

        newFsts = []
        for fst in fsts:
            newFst = tempD + "/" + fst.replace("/", "-")
            shutil.copyfile(fst, newFst)
            newFsts.append(newFst)

        fsts = newFsts

        cmd = invocation + [data,] + fsts

        print("Iteration", index, "running", cmd)
        print(" ".join(cmd))

        check_call(cmd)# stdout=None, stderr=None)

        machines = []
        for fst in fsts:
            trained = fst + ".trained"
            #newName = runDir + "/" + trained.replace("/", "-") + "-%d" % index
            newName = runDir + "/" + os.path.basename(trained) + "-%d" % index
            print("Copying", trained, "to", newName)
            shutil.move(trained, newName)
            machines.append(newName)

        for fst in fsts: #ensure tempdir is now empty, then destroy it
            os.unlink(fst)
        os.rmdir(tempD)

        return machines

    assert(0)

def indexOfFusion(featureMachine, fsets):
    total = 0
    fsets = [list(fsets)[0]]
    for fset in fsets:
        tmpf = open("scratch/fset.txt", "w")
        tmpf.write("sink\n")
        for ind, feat in enumerate(fset):
            tmpf.write("(%d (%d *e* %s))\n" % (ind, ind + 1, feat))
        tmpf.write("(%d (sink *e* *e*))\n" % (ind + 1))
        tmpf.close()

        out = check_output(["carmel/build/carmel", "-k", "5", "-OE", 
                            "scratch/fset.txt", featureMachine], stderr=PIPE)
        o1 = out.split("\n")[0]
        flds = o1.split()
        pr = float(flds[-1])
        analysis = flds[:-2] #discard stem
        nMSPs = (len(fset) - 1) #no stem
        nExponents = len(analysis)
        fusion = 1 - ((nExponents - 1) / (nMSPs - 1))
        print("Features", fset)
        print("Output", out)
        print("Analysis", analysis, "index", fusion)
        total += fusion

    return total / len(fsets)

if __name__ == "__main__":
    # invocation = ["carmel/build/carmel",
    #               "-1", #random start
    #               #"-?", #memorize derivations
    #               "-+a", "0", "-U", #digamma
    #               #"-f", "0",  #standard
    #               #"--digamma=0,0,0",
    #               "--train-cascade",
    #               "-M", "1",
    #               "-X", "0.9999",
    #               "-e", "1e-10",
    #               ]

    parser = argparse.ArgumentParser()
    parser.add_argument("data", action="store")
    parser.add_argument("fsts", action="store", nargs="*")
    parser.add_argument("--name", action="store", default=None)
    parser.add_argument("--priors", action="store", default=None)
    parser.add_argument("--resume", action="store_true")

    args = parser.parse_args()

    data = args.data
    fsts = args.fsts
    priors = args.priors
    resume = args.resume
    if priors is None:
        priors = ",".join(["0.01" for mi in fsts])

    invocation = ["carmel/build/carmel",
                  "--random-start", #random start
                  "--crp",
                  "--priors=" + priors,
                  "--high-temp=4",
                  "--final-counts",
                  "-M", "200",
                  ]

    if args.name is None:
        name = os.path.basename(data).replace(
            ".train", "").replace("instances-", "")
    else:
        name = args.name

    print("Run name:", name)

    missing = list(range(20))

    try:
        os.mkdir("scratch/report-%s" % name)
    except OSError:
        print("Reports dir", name, "already exists.")

        if not resume:
            sys.exit(1)
        else:
            dname = "scratch/report-%s" % name
            for fi in os.listdir(dname):
                digits = int(fi.split("-")[-1])
                if digits in missing:
                    missing.remove(digits)

            print("Resuming, with missing items", missing)

    dfile = open(data)

    lines = dfile.readlines()

    fsets = set()
    for ind, line in enumerate(lines):
        if ind % 2 == 0:
            fsets.add(tuple(line.strip().split()[:-1]) + 
                      ("\"STEM=0\"",)) #no stem

    indexes = []
    for it in missing:
        machines = run(invocation, data, fsts, "scratch/report-%s" % name, it)
        featMachine = machines[0]
        #featMachine = "scratch/report/scratch-features-fst.txt.trained-0"
        index = indexOfFusion(featMachine, fsets)
        print("Index of fusion:", index)

        indexes.append(index)

    print(indexes)
