# deeptools

TAFFISH wrapper for [deepTools](https://github.com/deeptools/deepTools) 3.5.6, a command-line suite for processing BAM and bigWig files, computing sequencing quality summaries, preparing signal matrices, and generating heatmaps, profiles, correlations, PCA plots, and other NGS visualizations.

Package identity:

- App: `deeptools`
- Command: `taf-deeptools`
- Kind: `tool`
- TAFFISH release: `3.5.6-r1`
- Container image: `ghcr.io/taffish/deeptools:3.5.6-r1`
- Upstream: `deeptools/deepTools` tag `3.5.6`
- Runtime version banner: `deeptools 3.5.6`
- Native platforms: `linux/amd64`, `linux/arm64`

## Usage

Show TAFFISH wrapper help:

```sh
taf-deeptools --help
```

Show the upstream deepTools tool list:

```sh
taf-deeptools -- --help
taf-deeptools -- --version
```

Create a normalized bigWig coverage track from a BAM file:

```sh
taf-deeptools bamCoverage \
  -b sample.sorted.bam \
  -o sample.coverage.bw \
  --binSize 10 \
  --normalizeUsing CPM \
  --numberOfProcessors 4
```

Compare two BAM files:

```sh
taf-deeptools bamCompare \
  -b1 treatment.sorted.bam \
  -b2 control.sorted.bam \
  -o treatment_vs_control.log2ratio.bw \
  --operation log2 \
  --binSize 25 \
  --numberOfProcessors 4
```

Summarize multiple BAM files and plot correlations:

```sh
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
```

Prepare a signal matrix and plot heatmaps/profiles:

```sh
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
```

Filter alignments:

```sh
taf-deeptools alignmentSieve \
  -b sample.sorted.bam \
  -o sample.filtered.bam \
  --minMappingQuality 30 \
  --numberOfProcessors 4
```

## Packaged Commands

The image installs deepTools from PyPI and exposes the upstream console scripts:

- BAM / bigWig processing: `bamCoverage`, `bamCompare`, `bigwigCompare`, `bigwigAverage`, `multiBamSummary`, `multiBigwigSummary`, `alignmentSieve`
- QC: `plotCoverage`, `plotFingerprint`, `plotCorrelation`, `plotPCA`, `bamPEFragmentSize`, `estimateReadFiltering`, `computeGCBias`, `correctGCBias`
- Matrix and plots: `computeMatrix`, `computeMatrixOperations`, `plotHeatmap`, `plotProfile`, `plotEnrichment`
- Utility entry points: `deeptools`, `estimateScaleFactor`

TAFFISH command mode is enabled. Use `taf-deeptools bamCoverage ...`, `taf-deeptools computeMatrix ...`, and similar forms for the individual tools. The default command is the upstream `deeptools` tool-list command, so `taf-deeptools -- --help` shows the upstream overview rather than a specific subtool.

## Inputs and Outputs

Common inputs include coordinate-sorted and indexed BAM files, bigWig files, BED/GTF region files, and, for GC-bias workflows, user-supplied genome resources such as 2bit genome files and mappability tracks.

Common outputs include bigWig tracks, bedGraph-like coverage outputs, `.npz` summary matrices, `computeMatrix` `.gz` matrices, filtered BAM files, PNG/PDF/SVG plots, and tabular QC summaries depending on the selected subcommand.

The image includes a tiny synthetic paired-end fixture under:

```text
/opt/deeptools/share/testdata/
```

This fixture is for packaging smoke tests only and is not a scientific reference dataset.

## Dependencies

The package uses a Python 3.11 virtual environment with deepTools 3.5.6 and pins `deeptoolsintervals` to 0.1.9 because that dependency is built from source during the image build. Core Python runtime dependencies include NumPy, SciPy, matplotlib, pysam, pyBigWig, py2bit, plotly, numpydoc, and deeptoolsintervals.

The runtime sets `MPLBACKEND=Agg` for headless plotting and limits OpenBLAS/OpenMP thread defaults to avoid surprising CPU oversubscription. No network access, genome database download, or external service is required at runtime.

## Platform

This app declares native `linux/amd64` and `linux/arm64` container builds. The Dockerfile builds the small compiled dependency `deeptoolsintervals` in a build stage, then copies the prepared virtual environment into a runtime image with only runtime libraries and fonts needed for plotting.

## Boundaries

This is a tool app, not a TAFFISH flow. It does not sort or index BAM files, generate alignments, call peaks, download genomes, build 2bit files, or choose biological normalization parameters for the user. Those inputs and choices remain explicit user responsibilities or should be handled by upstream/downstream flow apps.

The upstream repository also has a `scripts/` directory with auxiliary scripts. They are not installed as public console scripts by the upstream Python package and are not treated as supported TAFFISH command surface in this app. The supported surface is the deepTools console-script suite listed above.

Smoke tests validate package metadata, imports, help surfaces, BAM to bigWig coverage generation, BAM summaries, correlation plotting, bigWig summaries, matrix generation, heatmap/profile plotting, bigWig arithmetic, alignment filtering, and read-filtering estimation using tiny synthetic fixtures. They do not validate every command option or the scientific suitability of any normalization/plotting strategy for a particular experiment.

## Metadata

- Upstream repository: <https://github.com/deeptools/deepTools>
- Upstream documentation: <https://deeptools.readthedocs.io/>
- Upstream release: <https://github.com/deeptools/deepTools/releases/tag/3.5.6>
- PyPI package: <https://pypi.org/project/deepTools/3.5.6/>
- Upstream license: MIT, with `deeptools/cm.py` under a BSD license notice
- Citation: Ramírez F, Ryan DP, Grüning B, Bhardwaj V, Kilpert F, Richter AS, Heyne S, Dündar F, Manke T. 2016. `deepTools2: a next generation web server for deep-sequencing data analysis.`
- DOI: `10.1093/nar/gkw257`
- PMID: `27079975`
