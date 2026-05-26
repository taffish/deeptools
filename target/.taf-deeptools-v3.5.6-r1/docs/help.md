taf-deeptools 3.5.6-r1

TAFFISH wrapper for deepTools 3.5.6, a command-line suite for BAM and
bigWig processing, sequencing QC, matrix generation, and NGS visualization.

Usage:
  taf-deeptools --help
  taf-deeptools --version
  taf-deeptools -- --help
  taf-deeptools -- --version
  taf-deeptools <deepTools-command> [arguments...]
  taf-deeptools --compile [arguments...]

Wrapper options:
  --help       Show this TAFFISH help text.
  --version    Show the TAFFISH package version.
  --compile    Print the generated shell instead of running it.
  --           Stop wrapper option parsing and pass following arguments to
               the default upstream command.

Default upstream command:
  deeptools

  taf-deeptools -- --help
  taf-deeptools -- --version

Command mode:
  deepTools installs many public console scripts. Use TAFFISH command mode to
  run them directly in the same reproducible container environment:

  taf-deeptools bamCoverage -b sample.bam -o sample.bw
  taf-deeptools bamCompare -b1 treatment.bam -b2 control.bam -o log2ratio.bw
  taf-deeptools computeMatrix scale-regions -S signal.bw -R genes.bed -o matrix.gz
  taf-deeptools plotHeatmap -m matrix.gz -out heatmap.png

Packaged commands:
  deeptools
  bamCoverage
  bamCompare
  bigwigCompare
  bigwigAverage
  multiBamSummary
  multiBigwigSummary
  alignmentSieve
  plotCoverage
  plotFingerprint
  plotCorrelation
  plotPCA
  bamPEFragmentSize
  estimateReadFiltering
  computeGCBias
  correctGCBias
  computeMatrix
  computeMatrixOperations
  plotHeatmap
  plotProfile
  plotEnrichment
  estimateScaleFactor

Common workflows:
  BAM to bigWig:
    taf-deeptools bamCoverage \
      -b sample.sorted.bam \
      -o sample.coverage.bw \
      --binSize 10 \
      --normalizeUsing CPM \
      --numberOfProcessors 4

  BAM comparison:
    taf-deeptools bamCompare \
      -b1 treatment.sorted.bam \
      -b2 control.sorted.bam \
      -o treatment_vs_control.log2ratio.bw \
      --operation log2 \
      --numberOfProcessors 4

  Multi-sample BAM summary:
    taf-deeptools multiBamSummary bins \
      --bamfiles sample1.bam sample2.bam sample3.bam \
      -out read_counts.npz \
      --binSize 10000 \
      --numberOfProcessors 4

    taf-deeptools plotCorrelation \
      -in read_counts.npz \
      --corMethod pearson \
      --whatToPlot heatmap \
      -o read_count_correlation.png

  Heatmap/profile from bigWig tracks:
    taf-deeptools computeMatrix scale-regions \
      -S sample1.bw sample2.bw \
      -R genes.bed \
      -o matrix.gz \
      --regionBodyLength 3000 \
      --beforeRegionStartLength 1000 \
      --afterRegionStartLength 1000 \
      --numberOfProcessors 4

    taf-deeptools plotHeatmap -m matrix.gz -out heatmap.png
    taf-deeptools plotProfile -m matrix.gz -out profile.png

Inputs:
  Common inputs are coordinate-sorted and indexed BAM files, bigWig files,
  BED/GTF region files, and user-provided genome resources for GC-bias tools.

Outputs:
  Outputs depend on the selected subcommand and may include bigWig tracks,
  bedGraph-style coverage outputs, npz summary matrices, computeMatrix gz
  matrices, filtered BAM files, PNG/PDF/SVG plots, and tabular QC summaries.

Platform:
  Native container builds are declared for linux/amd64 and linux/arm64.
  Plotting uses a headless matplotlib backend. Runtime does not require
  network access or database downloads.

Boundaries:
  This app exposes the upstream deepTools console-script suite. It does not
  sort/index BAM files, generate alignments, call peaks, download genomes,
  create 2bit genome files, or choose analysis-specific normalization
  parameters. Upstream auxiliary files under scripts/ are not installed as
  public console scripts by the Python package and are not supported as the
  TAFFISH command surface for this app.
