deepTools 4.1.0-r1

Purpose:
  Process indexed BAM/bigWig files, build region matrices, run QC, and create
  static PNG/PDF/SVG plots with the official deepTools command suite.

Usage:
  taf-deeptools -- --help
  taf-deeptools -- --version
  taf-deeptools bamCoverage --help
  taf-deeptools <packaged-command> [options]

Common tasks:
  taf-deeptools bamCoverage -b "'sample A.bam'" -o "'coverage A.bw'" --binSize 10 -p 4
  taf-deeptools computeMatrix scale-regions -S "'coverage A.bw'" -R regions.bed -o matrix.gz --regionBodyLength 1000 -p 4
  taf-deeptools plotHeatmap -m matrix.gz -out heatmap.png -p 4
  taf-deeptools plotProfile -m matrix.gz -out profile.pdf -p 4

Required inputs:
  Coordinate-sorted BAM with a readable matching index, or bigWig signal files.
  Appropriate BED3/6/12 or GTF regions/blacklists; chromosome names must match.
  Work in a writable project directory and keep inputs under it or mount them.
  For spaces, preserve literal inner quotes: -b "'sample A.bam'". Ordinary shell
  quotes alone are insufficient in current TAFFISH command mode. Prefer simple
  names without quotes/metacharacters; do not pass untrusted shell text.
  External paths need explicit binds; see README for three-backend read-only forms.

Common options:
  -p N                         Worker count; choose for the available machine.
  --binSize N                  Coverage bin width (command-dependent).
  --normalizeUsing METHOD      Choose a scientifically appropriate normalization.
  --effectiveGenomeSize N      Numeric parameter where required, not a database.
  alignmentSieve --keepTags     Only with --shift/--ATACshift and BAM output.

Key outputs:
  Explicit bigWig/BAM, matrix.gz, NPZ and tabular files in your work directory.
  Native static PNG/PDF/SVG plots; open them with an external file viewer.
  Use new output names to avoid upstream overwriting previous results.

Immediate notes:
  4.1.0 removes computeGCBias, correctGCBias and all five *_old commands.
  The former deeptools-resources helper and RESOURCE_* automatic binds are gone;
  existing external reference files remain untouched. Use the old wrapper for GC.
  plotPCA removes --transpose/--centerRows; bamCompare cannot normalize with RPGC.
  Inputs must match the assembly and experimental design; examples are syntax only.
  Invalid BED intervals may be warned/skipped with exit zero; inspect matrix rows.
  No database download, HTML output, GUI service or port is required for local use.
  The same CLI works on Docker, Podman and Apptainer.

More help:
  taf-deeptools <packaged-command> --help
  https://github.com/taffish/deeptools
  https://deeptools.readthedocs.io/

Wrapper options:
  taf-deeptools --help       Show this TAFFISH help.
  taf-deeptools --version    Show TAFFISH wrapper version.
  taf-deeptools --compile    Print the generated shell.
  taf-deeptools -- --help    Show upstream default-command help.
