# SCIL 2019 "Stop the morphological cycle, I want to get off"

This repository contains the code and data for replicating our
study. It depends on [Carmel](github.com/isi-nlp/carmel). You should
look over the Carmel docs for information on debugging, formatting and
visualizing FSTs.

## Generating data

The data format for the files describes each form using two lines: one
lists all the morphosyntactic properties and values, the other gives
the surface string.

```
MSP=value MSP=value ...
char char char char char ...
```

The MSP for the stem property is named STEM. The MSPs should follow a
consistent morphological template.

To generate the data, run `genData.py [languagename]`. See the code
for a list of language names you can use. Note that some simulations
don't have the same name they had in the paper (since we ran some
other simulations we did not report).

Output goes to the `data` directory (hardcoded).

## Creating FSTs

Run `fstFusion.py data/instances-[language].train`. FSTs will be
created in the `scratch` directory (hardcoded). You get a whole bunch
of them, including several phonological processes.

You also get a *dot* and an *undot*. These add and remove an
end-of-sequence marker from the surface string; some phonological
process implementations require them to be used in the cascade but
they don't have learnable parameters. The processes used in the paper
all remove the dot for themselves, so you won't need undot.

Although all the FSTs created for a particular language are tagged
with that language name, most of them aren't language-specific;
they're the same every time.

## Running the program

Run `runAndReport.py data/instances-[language].train [fst1] [fst2] ... [fstN] --name [name] --priors [alpha1 alpha2 ... alphaN]`

Reports will be generated in `scratch`.

For the simulations in section 4, your cascade will be:

- Features
- Lexicon
- Dot
- Glide-insert

For the simulations in section 5, use:

- Features
- Lexicon
- Dot
- Reduce Vowel
- Voicing assimilation

## Reporting results

The report program tries to give useful results, but in the paper, we
used the longer reports from `posteriorIndexOfFusion.py [original
FEATURES fst] [output directory]` and `posteriorReduction.py [output
directory]`.

You can also use `dumpFeatures.py` and `dumpLexicon.py` to see what
the model has learned about the individual morphemes.

```
python script/dumpLexicon.py scratch/report-A/scratch-lexicon-A-fst.txt-trained-0
Symbol "M1=I" ->
	 ta 0.981008305060401
	 t 0.0146266772945044
	  0.000144518903795198
	 tu 7.26618994934006e-05
Symbol "M1=II" ->
	 mu 0.968109347395744
	 muak 0.0183001554885103
	 m 0.00699348535334923
	  0.000137494654895279
...
```

## Our actual results

See the `data` directory for input files and the `doc` directory for
raw outputs.
