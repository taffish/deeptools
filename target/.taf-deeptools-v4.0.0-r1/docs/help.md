deeptools 4.0.0-r1

Purpose:
  Process BAM/bigWig coverage, compare samples and plot region profiles/QC.

Usage:
  taf-deeptools -- --help
  taf-deeptools bamCoverage --help
  taf-deeptools computeMatrix scale-regions --help
  Always name the executable before a subcommand (not just "bins").

Common tasks:
  taf-deeptools bamCoverage -b sample.bam -o sample.bw --binSize 50 --normalizeUsing CPM -p 4
  taf-deeptools multiBamSummary bins -b a.bam b.bam -o counts.npz --binSize 1000 -p 4
  taf-deeptools plotCorrelation -in counts.npz --corMethod pearson --whatToPlot heatmap -o correlation.png
  taf-deeptools computeMatrix scale-regions -S sample.bw -R genes.bed -o matrix.gz -p 4
  taf-deeptools plotHeatmap -m matrix.gz -out heatmap.pdf
  taf-deeptools plotProfile -m matrix.gz -out profile.png
  taf-deeptools plotPCA -in counts.npz -o pca.png --ggplot

Required inputs:
  Coordinate-sorted BAM + BAI; bigWig tracks; BED3/6/12 or GTF regions.
  Rust computeMatrix rejects BED4/5: supply BED6 (name, score, strand) or use *_old.
  Keep files under the current directory or an explicit bind; outputs must be writable.
  Match assembly/chromosome names across reads, tracks, regions and 2bit references.

Common options:
  -p N / --numberOfProcessors N    CPU threads; choose a sensible limit.
  --binSize N                     Coverage/summary bin size (command-specific).
  --normalizeUsing CPM/RPKM/BPM/RPGC   Check command help and effective genome size.

Key outputs:
  .bw / bedGraph tracks, .npz summaries, matrix.gz, filtered BAM and static plots.
  Do not compare tracks without checking normalization and assembly.

Backend-specific use (CPU CLI and headless plots):
  Docker:    TAFFISH_CONTAINER_BACKEND=docker taf-deeptools bamCoverage -b sample.bam -o sample.bw
  Podman:    TAFFISH_CONTAINER_BACKEND=podman taf-deeptools bamCoverage -b sample.bam -o sample.bw
  Apptainer: TAFFISH_CONTAINER_BACKEND=apptainer taf-deeptools bamCoverage -b sample.bam -o sample.bw
  Apptainer requires native Linux; on macOS use Docker/Podman's Linux VM.
  No GPU/display/port needed. Galaxy UI is not included; use a separate Galaxy server.

2bit reference installation (only for GC routines; explicitly choose a matching genome):
  taf-deeptools deeptools-resources list
  base="${TAFFISH_USER_HOME:-$HOME/.local/share/taffish}/resources/deeptools"
  mkdir -p "$base"
  Docker:    TAFFISH_CONTAINER_BACKEND=docker TAFFISH_DEEPTOOLS_RESOURCE_INSTALL_ROOT="$base" taf-deeptools deeptools-resources install --resource ucsc-sacCer3-b061b22f --resource-root /resource-install
  Podman:    TAFFISH_CONTAINER_BACKEND=podman TAFFISH_DEEPTOOLS_RESOURCE_INSTALL_ROOT="$base" taf-deeptools deeptools-resources install --resource ucsc-sacCer3-b061b22f --resource-root /resource-install
  Apptainer: TAFFISH_CONTAINER_BACKEND=apptainer TAFFISH_DEEPTOOLS_RESOURCE_INSTALL_ROOT="$base" taf-deeptools deeptools-resources install --resource ucsc-sacCer3-b061b22f --resource-root /resource-install
  Run only the line for your backend. Add --dry-run for space/source preview.
  sacCer3 is yeast, NOT a human reference. Other genomes: list or local-* import.

Reuse a personal or administrator-installed reference (same on all three backends):
  export TAFFISH_DEEPTOOLS_RESOURCE_ID=ucsc-sacCer3-b061b22f
  taf-deeptools deeptools-resources verify /deeptools-resource
  taf-deeptools computeGCBias -b sample.bam -g /deeptools-resource/genome.2bit --effectiveGenomeSize EFFECTIVE_SIZE -freq gc.tsv
  taf-deeptools correctGCBias -b sample.bam -g /deeptools-resource/genome.2bit --effectiveGenomeSize EFFECTIVE_SIZE --GCbiasFrequenciesFile gc.tsv -o corrected.bam
  Replace EFFECTIVE_SIZE using your assembly/read assumptions, not the file size.
  Searches personal resources then /usr/local/share/taffish/resources/deeptools/ID
  and /opt/taffish/resources/deeptools/ID. Installed references are mounted read-only.
  Override one installed unit: TAFFISH_DEEPTOOLS_RESOURCE_PATH=/safe/path/to/ID
  Wrong ID, missing/extra members or member symlinks are rejected; do not rename units.
  Disable discovery: TAFFISH_DEEPTOOLS_RESOURCE_AUTO_MOUNT=0
  For administrator-once setup, permissions, local import or manual binds: see README.

Immediate notes:
  4.0 changes five commands to Rust; corresponding *_old commands remain available.
  --exactScaling and --ignoreDuplicates are removed from new coverage/compare.
  For marked duplicates use --samFlagExclude 1024 if scientifically appropriate.
  Interactive Plotly/HTML output is removed; use PNG/PDF/SVG.
  Use paths without whitespace/metacharacters for correctGCBias (upstream cp boundary).
  For other tools, preserve shell quoting: -o '"output with spaces.bw"'.
  Readonly failure: choose writable scratch/output or an actual install bind; do not chmod SIF.

More help:
  taf-deeptools deeptools-resources install --help
  https://github.com/taffish/deeptools

Wrapper options:
  taf-deeptools --help       This task-oriented TAFFISH help.
  taf-deeptools --version    Wrapper identity, not upstream runtime version.
  taf-deeptools --compile    Print generated shell without analysis.
  taf-deeptools -- --help    Default upstream help.
