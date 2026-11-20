# deepTools

`deeptools` packages **deepTools 4.1.0** for TAFFISH as **4.1.0-r1**.

Package: `deeptools` · command: `taf-deeptools` · kind: tool.
Packaging is Apache-2.0; upstream is MIT.
[Upstream release](https://github.com/deeptools/deepTools/releases/tag/4.1.0).

## What This App Packages

The unmodified official Linux CPython 3.12 amd64/arm64 wheels, including the Rust
core, and all **20 official console commands**. The thin entry runs `deeptools`
and enables ordinary TAFFISH command mode. No scientific algorithm patch is applied.
The wrapper adds same-UID output handling on Docker/Podman, not a separate analysis workflow.

## Scope and Migration

This app supports indexed BAM/bigWig processing, filtering, region matrices, QC
and headless PNG/PDF/SVG plots. Reassess analytical parameters when migrating;
packaging checks do not assert scientific equivalence between releases.

- **4.1.0 removes** `computeGCBias`, `correctGCBias` and all five transitional
  `*_old` commands. Use the separately retained `taf-deeptools-v4.0.0-r1`
  environment if an existing workflow needs them. This release does not alias or
  resurrect those implementations.
- The former `deeptools-resources` 2bit helper and `TAFFISH_DEEPTOOLS_RESOURCE_*`
  automatic binds are retired with those GC commands. Previously installed
  references and older wrappers are **not deleted or modified**.
- `plotPCA` now uses scores by default; `--transpose` and `--centerRows`
  are removed. `bamCompare --normalizeUsing RPGC` is not supported.
- `alignmentSieve --keepTags` explicitly retains selected SAM tags with
  `--shift`/`--ATACshift` and BAM output; it is not a standalone filter. Selected
  tags are copied, not recalculated for the shifted coordinates.
- `plotHeatmap --colors` colors summary profiles; `plotHeatmap` and
  `plotProfile -p` support parallel matrix parsing.
- Since 4.0, Plotly/interactive HTML is removed. Rust-backed commands also remove
  `--exactScaling` and `--ignoreDuplicates`. Duplicate marking and
  `--samFlagExclude 1024` are not equivalent to the old coordinate deduplication.
- Use valid BED3/6/12, not incomplete BED4. Chromosome names, coordinates, assembly,
  normalization and effective genome size must be appropriate for your experiment.

## Container Contents

`deeptools`, `bamCoverage`, `bamCompare`, `alignmentSieve`, `multiBamSummary`,
`multiBigwigSummary`, `bigwigAverage`, `bigwigCompare`, `computeMatrix`,
`computeMatrixOperations`, `plotHeatmap`, `plotProfile`, `plotCorrelation`,
`plotPCA`, `plotCoverage`, `plotFingerprint`, `plotEnrichment`, `bamPEFragmentSize`,
`estimateReadFiltering` and `estimateScaleFactor` are available.

Python 3.12, NumPy, SciPy, Matplotlib/Agg, fonts, pysam, pyBigWig,
deeptoolsintervals and upstream-declared maturin are included.
Exact Python pins and accepted artifact hashes are in `docker/requirements.lock`
and `docker/dependency-artifacts.json`. Rust licenses and Cargo.lock are bundled
under `/opt/deeptools/share/doc/deeptools/upstream`; wheel SBOMs remain installed.

## Installation and Usage

Install TAFFISH and a working Docker, Podman or native Linux Apptainer backend.
After this version is published and indexed:

```sh
taf install deeptools 4.1.0-r1
taf-deeptools-v4.1.0-r1 --help
taf-deeptools -- --help
taf-deeptools -- --version
taf-deeptools bamCoverage --help
```

Keep a writable project directory; place inputs and outputs underneath it:

```sh
cd "/path/to/my project"
taf-deeptools bamCoverage -b "'input/sample A.bam'" -o "'coverage A.bw'" --binSize 10 -p 4
taf-deeptools computeMatrix scale-regions -S "'coverage A.bw'" -R input/regions.bed \
  -o matrix.gz --regionBodyLength 1000 -p 4
taf-deeptools plotHeatmap -m matrix.gz -out heatmap.png -p 4
taf-deeptools plotProfile -m matrix.gz -out profile.pdf -p 4
```

These examples show invocation syntax, not recommended biological parameters.
The same commands apply to Docker, Podman and Apptainer; select the engine using
`TAFFISH_CONTAINER_BACKEND=docker`, `podman` or `apptainer`.

## Command Mode and Paths

A non-option-leading word selects that packaged executable, e.g.
`taf-deeptools bamCoverage ...`. `--help`, `--version` and
`--compile` belong to the wrapper; `-- --help` and `-- --version`
reach the default upstream executable.

TAFFISH 0.12 command mode joins forwarded arguments as shell text; ordinary shell
quotes alone do not preserve a spaced filename. For simple paths containing
spaces, keep the inner quote characters literally, as in
`-b "'sample A.bam'" -o "'coverage A.bw'"`. This form was verified through the real
wrapper on all three backends. The outer double quotes are consumed by the host
shell; the inner single quotes reach the generated command. Quote `cd` normally.
Prefer simple filenames; names containing quote characters or shell metacharacters
are not covered by this workaround. Do not pass untrusted text as shell arguments.

Current-directory files are visible through the wrapper's normal work bind. A
host absolute path outside that bind is not automatically a container path. For
a site-managed shared input directory, mount it read-only to the same fixed
container destination:

```sh
# Run from the writable project directory; /srv/shared/deeptools-inputs must exist.
TAFFISH_CONTAINER_BACKEND=docker \
  TAFFISH_DOCKER_RUN_ARGS='--volume=/srv/shared/deeptools-inputs:/reference:ro' \
  taf-deeptools bamCoverage -b /reference/sample.bam -o coverage.bw -p 4
TAFFISH_CONTAINER_BACKEND=podman \
  TAFFISH_PODMAN_RUN_ARGS='--volume=/srv/shared/deeptools-inputs:/reference:ro' \
  taf-deeptools bamCoverage -b /reference/sample.bam -o coverage.bw -p 4
TAFFISH_CONTAINER_BACKEND=apptainer \
  TAFFISH_APPTAINER_RUN_ARGS='--bind=/srv/shared/deeptools-inputs:/reference:ro' \
  taf-deeptools bamCoverage -b /reference/sample.bam -o coverage.bw -p 4
```

Use a host mount path without spaces or runtime-argument metacharacters in these
extra-argument forms; quoting file arguments is a separate issue. Administrators
prepare complete readable inputs and BAM indexes once, including traversal
permissions on all parent directories. Ordinary users need no write permission
on shared inputs. Do not chmod shared directories globally to fix one task.

## Inputs and Outputs

| Input | Requirements |
| --- | --- |
| BAM and index | Coordinate-sorted, indexed; pair flags/assembly must match the task |
| bigWig | Correct chromosome names and coordinate space |
| BED/GTF/blacklist | Appropriate intervals; new Rust BED parser accepts BED3/6/12 |
| Matrix/NPZ | Produced by the corresponding deepTools command, not arbitrary gzip/ZIP |

Outputs are explicit bigWig/BAM, compressed matrices, NPZ, tabular counts or plots
in the work directory. Names may be overwritten by upstream; use new output names
and keep input backups. Plot files can be opened with an external image/PDF/SVG
viewer. No browser service or port is needed. Cache/temp writes use the runtime
temporary directory; Matplotlib uses Agg.

## Resources, Databases, and Platform

The installed 4.1.0 command suite has no model/reference-database installer.
BAM, bigWig and interval files are explicit project inputs; local workflows do not
download missing inputs automatically. Remote bigWig URLs, where supported by
pyBigWig/upstream, explicitly opt into network access and external availability.

`--effectiveGenomeSize` is a numeric analysis parameter, not a downloadable
resource selection. Consult the
[upstream effective genome size documentation](https://deeptools.readthedocs.io/en/latest/content/feature/effectiveGenomeSize.html).
The source repository's `scripts/ess.py` regenerates documentation tables,
downloads multiple genomes and uses separate Kent/khmer tools; it is not a wheel
entrypoint and is not included as a supported end-user pipeline here. Its outputs
are not silently used to choose a scientific parameter.

Linux amd64 and arm64 are supported using official architecture-specific wheels.
Base image identity and Python artifacts are pinned, but Debian repositories and
external package hosting can change or remove historical files. Dockerfile comments
identify this rebuild boundary; locks do not promise indefinite upstream retention.

## GUI and Other Boundaries

PNG/PDF/SVG are static native Matplotlib outputs. No HTML, interactive plotting
service, noVNC or display server is added. Galaxy is an independent server deployment
requiring its own administrator, storage and authentication; it is not called by
the CLI and is outside this app. See the [official Galaxy service](https://usegalaxy.eu/)
or deploy Galaxy separately under your site's data policies.

## Troubleshooting

- Missing files: check the current-directory bind and explicit mounts; host paths
  outside mounts are not visible. Keep a BAM index next to its BAM.
- Invalid BED or labels: correct intervals/column count and provide one label per
  input. This app does not silently repair analytical inputs.
  Upstream can warn and skip reversed/empty BED intervals while exiting zero;
  inspect warnings and matrix row counts, not only the exit status.
- Removed command/argument: follow the migration section or select an older
  versioned wrapper; `*_old` and GC commands are not in 4.1.0.
- Permission failure: use a writable work directory and readable shared inputs.
  Do not run the whole analysis as root to bypass permissions.
- Blank/uninformative plot: inspect actual counts/matrix and input assembly; a
  successful plot command is not proof of meaningful scientific data.

## Testing

The 4.1.0-r1 candidate was built and tested natively on 2026-11-19: ARM64 with
Docker/Podman, and Linux amd64 with Docker/Podman/Apptainer. The final generated
wrapper passed help/version/compile, the actual BAM-to-bigWig-to-matrix workflow,
paths containing spaces using the literal-quote form above, read-only shared
inputs, output ownership, error status
and temporary-file cleanup. Actual ATAC shifts retain only requested tags;
injected command failures expose their stage, exit status and diagnostic tail.

All 26 manifest existence checks and six smoke commands were executed independently
in fresh offline containers, plus the combined existence gate. Docker/Podman also
passed the same commands with a read-only root and an ordinary user. The amd64 SIF
was converted from the tested OCI image and run as an ordinary user.
Static PNG/PDF/SVG outputs were inspected; no HTML service is claimed.

Build-time checks remain limited to identity and tiny non-rendering coverage;
full plotting and negative checks run after the build, not as architecture-sensitive
build gates. Final Docker image sizes were 457,226,590 bytes (arm64) and
423,894,941 bytes (amd64), approximately 0.07% and 0.09% above the preceding
4.0.0-r1 measurements. These tests verify packaging, not scientific accuracy on
production data. Local acceptance is not publication or public CI/Index acceptance.

## License and Citation

TAFFISH packaging: Apache-2.0. deepTools: MIT; third-party libraries retain their
licenses and installed notices. No external user data license is granted.
The wheel source is the official tag 4.1.0,
commit `c678938e18dfaa801484a78b8328da7e6a4b3006`.
Cite Deboutte et al. (2026), deepTools4 (bioRxiv preprint), DOI
[10.64898/2026.11.11.765524](https://doi.org/10.64898/2026.11.11.765524),
and Ramirez et al. (2016), deepTools2, DOI
[10.1093/nar/gkw257](https://doi.org/10.1093/nar/gkw257), and follow current upstream
citation guidance for the methods used.
