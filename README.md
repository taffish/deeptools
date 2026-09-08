# deepTools

`deeptools` packages upstream **deepTools 4.0.0** for TAFFISH, version `4.0.0-r1`.
The command is `taf-deeptools`; packaging is Apache-2.0 and upstream is MIT.

## What This App Packages

The official Linux CPython 3.12 wheels, including the Rust implementations of
`bamCoverage`, `bamCompare`, `computeMatrix`, `alignmentSieve` and `multiBamSummary`,
are installed without algorithm patches. All 27 official console commands are retained,
including the five transitional `_old` Python implementations. Python 3.12, NumPy,
SciPy, Matplotlib/Agg and fonts, pysam, pyBigWig, py2bit, deeptoolsintervals and
upstream-declared maturin are included. Exact versions/artifact hashes are in
`docker/requirements.lock` and `docker/dependency-artifacts.json`.

The thin entry calls `deeptools` and retains automatic command mode. Runtime arguments
only implement same-UID output and explicit resource binds. `deeptools-resources` is
a separate reference installer, not a replacement analysis entrypoint.

## Scope and Migration from 3.5.6

Use for BAM/bigWig processing, normalization, filtering, region matrices, QC and
headless PNG/PDF/SVG plots. This is a **major upstream update**, not a promise of
3.x numerical or CLI equivalence. See the [official 4.0.0 release](https://github.com/deeptools/deepTools/releases/tag/4.0.0).

- Five core names now use Rust. Their `_old` counterparts remain available for
  transition, but are not a complete frozen 3.5.6 environment. Keep the old
  `taf-deeptools-v3.5.6-r1` wrapper for exact historical runs.
- `bamCoverage`/`bamCompare` remove `--exactScaling` (exact scaling is now the only
  method) and `--ignoreDuplicates`. Mark duplicates separately and use
  `--samFlagExclude 1024` when appropriate; marked-duplicate exclusion is not the
  same operation as the former coordinate-based duplicate detection.
- Plotly/interactive HTML output is removed upstream. Use static plots; several
  plotting commands offer `--ggplot`. This app does not reintroduce Plotly.
- PCA scaling/orientation and related options are fixed upstream. Region/blacklist
  handling, BED block starts, missing-data treatment and f32 arithmetic also change.
  Reassess scientific thresholds rather than asserting old/new output identity.
- Gzipped BED/GTF and blacklists are supported by the relevant new Rust commands.
  Chromosome names and assembly still must match every BAM, bigWig and interval input.
- The new Rust BED parser accepts exactly BED3/6/12; a four-column named BED accepted
  by the old command now fails with `Invalid BED format`. Supply a complete BED6
  (including scientifically appropriate score/strand) or use `computeMatrix_old`.
  Packaging does not silently rewrite intervals. The smoke fixture uses explicit BED6.

Official **Galaxy integration** is a separate deployment: the upstream `galaxy/`
Tool Shed wrappers require an existing Galaxy server, administrator access and its
storage/authentication lifecycle. Python extras contain docs/actions, not a local
desktop GUI. This app preserves the CLI surface; it does not install Galaxy/noVNC,
open ports or manage a web service. Use the upstream-linked
[European Galaxy service](https://usegalaxy.eu/) or separately administered Galaxy
for that interface. No claim of Galaxy version parity or private-data suitability is made.

## Installation and Usage

Install TAFFISH and a usable Docker, Podman or native Linux Apptainer backend first.
After this immutable release is published and appears in the Hub Index:

```sh
taf install deeptools 4.0.0-r1
taf-deeptools-v4.0.0-r1 --version
```

Examples use the unversioned alias `taf-deeptools`; use the fixed wrapper above in
reproducible records. App installation and reference installation are separate.

```sh
taf-deeptools -- --help
taf-deeptools bamCoverage --help
taf-deeptools bamCoverage -b sample.bam -o sample.bw --binSize 50 --normalizeUsing CPM -p 4
taf-deeptools multiBamSummary bins -b a.bam b.bam -o counts.npz --binSize 1000 -p 4
taf-deeptools plotCorrelation -in counts.npz --corMethod pearson --whatToPlot heatmap -o correlation.png
taf-deeptools computeMatrix scale-regions -S sample.bw -R genes.bed -o matrix.gz -p 4
taf-deeptools plotHeatmap -m matrix.gz -out heatmap.pdf
```

Put inputs and outputs under the current working directory (automatically bound by
TAFFISH), or provide an explicit site-specific bind. Keep BAM indices alongside
coordinate-sorted BAMs. Never use a wrapper argument named `bins` or `scale-regions`
as the first command: use the full executable name before its subcommand.
`-- --help` forwards option-leading default-command help; `--` does not disable
automatic command-mode interpretation of bare subcommands.

## Inputs and Outputs

| Input | Meaning and boundary |
| --- | --- |
| BAM + BAI | Coordinate-sorted reads, index and consistent reference names |
| bigWig | Coverage tracks; check normalization/assembly before comparison |
| BED/GTF/blacklist | Explicit project intervals; not downloaded or chosen automatically |
| genome `.2bit` | GC routines; exact assembly/chromosomes matching the BAM |
| effective genome size | User-chosen scientific parameter, not guessed by the installer |

Outputs include bigWig/bedGraph tracks, NPZ summaries, gzipped region matrices,
filtered/corrected BAMs, GC frequency tables and static plots. Choose explicit output
names in writable directories. Resource verification proves file identity and 2bit
readability, not assembly compatibility, scientific correctness or analysis quality.

## Resources, Databases, and Platform

No model or database is fetched on startup or during local-file analysis. Remote
BAM/bigWig URLs are still an upstream opt-in and require network access. The smallest
reusable reference member is one assembly-specific `.2bit`, not the entire genome catalog.
An explicit catalog is provided for two fixed snapshots; it is **not an exhaustive
list of supported organisms**. Other authorized references use `local-*` import.

| Resource ID | Assembly | Bytes | SHA256 |
| --- | --- | ---: | --- |
| `ucsc-sacCer3-b061b22f` | UCSC sacCer3 | 3039745 | `b061b22fdce3cb82c24d85101bc6eae98d23ea7194c1888c966b5446dd7909ab` |
| `ucsc-hg38-1f67aaa1` | UCSC initial GRCh38, not a later patch release | 835393456 | `1f67aaa17a77b327738fe750ab37430a85dddf73c7d9189385ad1839259acec0` |

Sources are UCSC `goldenPath/<assembly>/bigZips/<assembly>.2bit`. The installer
pins complete-file SHA256 and bytes; `resource.json` records source, assembly,
chromosome inventory, timestamp and installing UID. `SHA256SUMS`/`READY` cover the
complete installed unit; incomplete, altered or extra members fail verification.
Automatic mounting checks the same four regular members, checksum inventory and
the selected ID before launching the upstream command. A root-directory symlink
is resolved to its physical directory; symlinks inside the unit are rejected.
ID-based discovery must match `resource.json.resource`, including fixed catalog
payload hashes. Explicit `RESOURCE_PATH` still overrides an ID selection.
For manual verification with an expected identity, use
`deeptools-resources verify ROOT --expected-resource ID`. Prepared units are
installer-produced, immutable local resources, not an authentication boundary
against an administrator able to replace both data and all receipts.

Choose a reference **only after confirming its scientific suitability**. Personal installation:

```sh
base="${TAFFISH_USER_HOME:-$HOME/.local/share/taffish}/resources/deeptools"
mkdir -p "$base"
TAFFISH_CONTAINER_BACKEND=docker TAFFISH_DEEPTOOLS_RESOURCE_INSTALL_ROOT="$base" \
  taf-deeptools deeptools-resources install --resource ucsc-sacCer3-b061b22f --resource-root /resource-install
export TAFFISH_DEEPTOOLS_RESOURCE_ID=ucsc-sacCer3-b061b22f
taf-deeptools deeptools-resources verify /deeptools-resource
```

Replace `docker` with `podman` or `apptainer` for the same installed-wrapper command.
Only installation receives a writable `/resource-install`; selection receives a
read-only `/deeptools-resource`. No whole-family download or implicit assembly choice.

An administrator installs once; ordinary users reuse the resource read-only.
For **administrator-once sharing**, an administrator may create
`/usr/local/share/taffish/resources/deeptools` with traversable 0755 parents, then
run the same explicit installer with `TAFFISH_DEEPTOOLS_RESOURCE_INSTALL_ROOT` set
to that parent using an already working backend. No automatic sudo or permission
changes are performed. Installed member directories are 0755, files 0644. Ordinary
users reuse the shared reference read-only: select the ID and read
`/deeptools-resource/genome.2bit`; no repeated download.
This workflow must respect the administrator's backend/root policy.

Selection precedence: explicit `TAFFISH_DEEPTOOLS_RESOURCE_PATH` (one installed unit),
otherwise `TAFFISH_DEEPTOOLS_RESOURCE_ID` searches
`${TAFFISH_USER_HOME:-$HOME/.local/share/taffish}/resources/deeptools/<ID>`,
`/usr/local/share/taffish/resources/deeptools/<ID>`, then
`/opt/taffish/resources/deeptools/<ID>`. Set `TAFFISH_DEEPTOOLS_RESOURCE_AUTO_MOUNT=0`
to disable selection; an explicit install root is a separate higher-priority mode.
Auto-bind paths require a physical path containing only letters, digits, `_ . / + -`.
Use a safe path or a manually configured backend bind when this restriction matters.

For other authorized 2bit references, bind or place the source under the current
directory, then use a **new** `local-*` ID and recorded license/assembly:

```sh
TAFFISH_DEEPTOOLS_RESOURCE_INSTALL_ROOT="$base" taf-deeptools deeptools-resources install \
  --resource local-myassembly-sha8 --resource-root /resource-install --source reference.2bit \
  --sha256 YOUR_64_HEX_SHA256 --assembly MY_ASSEMBLY --license-note '"Authorized source and sharing terms"'
```

Do not treat the license note as a license grant. Fixed genomes follow
[UCSC data-use terms](https://genome.ucsc.edu/license/) and underlying assembly
rights, **not** this app's Apache/MIT licenses. No liftOver chains or restricted
browser/BLAT software are included. Attribute UCSC and original assembly contributors.

Installation checks free space (2× source bytes + 64 MiB), uses a private lock/stage,
resumes HTTPS downloads, verifies before atomic promotion and never overwrites an
existing unit. Reinstallation verifies the full identity and exits without writes.
`--dry-run` shows requirements without creating directories or contacting a server.
Failed `.downloads/<SHA256>.part` files are retained for diagnosis; handled failures
release this process's own lock. A pre-existing lock is never removed automatically:
inspect its owner before recovery, never remove another active lock.
After successful verification an administrator may remove only the matching cached
download to reclaim space; installed `genome.2bit` is independent of that cache.

## Backend Usage and Capability Matrix

Native platforms are `linux/amd64` and `linux/arm64`. CPU-only plotting needs no GPU,
display, X11, noVNC or port forwarding. macOS uses a Linux Docker/Podman VM;
Apptainer requires Linux, including Linux arm64 (not native macOS).

| Capability | Docker | Podman | Apptainer |
| --- | --- | --- | --- |
| Explicit selection | `TAFFISH_CONTAINER_BACKEND=docker taf-deeptools bamCoverage --help` | `TAFFISH_CONTAINER_BACKEND=podman taf-deeptools bamCoverage --help` | `TAFFISH_CONTAINER_BACKEND=apptainer taf-deeptools bamCoverage --help` |
| Fixed resource install | Same installer above with `docker` | Same installer with `podman` | Same installer with `apptainer` and actual writable bind |
| Resource analysis | Automatic readonly `/deeptools-resource` | Automatic readonly `/deeptools-resource` | Automatic readonly `/deeptools-resource`; SIF stays readonly |
| Desktop/Galaxy service | Not packaged; use separate Galaxy | Not packaged; use separate Galaxy | Not packaged; use separate Galaxy |

Manual resource fallback (set `root` to a verified installed unit):

```sh
export TAFFISH_DEEPTOOLS_RESOURCE_AUTO_MOUNT=0
TAFFISH_CONTAINER_BACKEND=docker TAFFISH_DOCKER_RUN_ARGS="-v $root:/deeptools-resource:ro" taf-deeptools deeptools-resources verify /deeptools-resource
TAFFISH_CONTAINER_BACKEND=podman TAFFISH_PODMAN_RUN_ARGS="-v $root:/deeptools-resource:ro" taf-deeptools deeptools-resources verify /deeptools-resource
TAFFISH_CONTAINER_BACKEND=apptainer TAFFISH_APPTAINER_RUN_ARGS="--bind $root:/deeptools-resource:ro" taf-deeptools deeptools-resources verify /deeptools-resource
```

Temporary files go to writable `/tmp`/`TMPDIR`, explicit outputs to the work directory,
and persistent references only to actual binds. Matplotlib uses Agg; if its normal
user cache is unwritable it creates a temporary cache. To persist a cache, explicitly
run `taf-deeptools env MPLCONFIGDIR=/path/to/writable/bound/cache plotHeatmap ...`.
No runtime chmod/chown of image contents, fake mount markers or Docker VOLUME dependency.

## Troubleshooting and Boundaries

- Missing chromosome/empty matrix: compare assembly, naming, intervals and coverage;
  a correctly downloaded reference may still be the wrong reference for your BAM.
- Removed 3.x flags/HTML: use the migration notes and each current command's help.
- `correctGCBias` retains an upstream shell `cp` path in its single-chunk output
  branch; use paths **without whitespace/shell metacharacters** for this command.
  Other commands still need TAFFISH shell quoting, e.g. `'"output with spaces.bw"'`.
- Readonly error: choose writable output/scratch and a real install bind; do not
  chmod the SIF or modify `/opt`. Resolve corrupt selected resources before analysis.
- Resources and tests do not supply scientific parameter defaults, validation on
  real studies, full organism databases, Galaxy deployment or performance guarantees.

## Testing

The Dockerfile uses only version/dependency identity and a tiny BAM→BigWig check.
The independent offline manifest tests cover all command help, five Rust and five
legacy entrypoints, gzip regions, summaries, PNG/PDF/SVG/PCA, GC routines and resource
integrity/idempotence. Synthetic and tiny upstream fixtures are retained read-only.
Full renders are runtime tests, not QEMU-sensitive build-time assertions.

Final candidate validation: native arm64 Docker/Podman and native amd64 Docker/
Podman/Apptainer all pass their complete fresh, offline manifest tests; Docker/Podman
also pass the read-only-root proxy (369/369 exact checks across nine groups).
Apptainer uses a real read-only SIF made from
the same amd64 OCI candidate, not an emulation or proxy claim. Full wrapper tests
pass 188/188 checks, including actual writable installation binds, read-only
reference reuse and plots. Regressions reject selected-ID mismatches, symlinked,
missing or extra members, malformed/traversing checksum inventories and false
catalog payloads before launching the upstream command. Correct explicit overrides
and physical root-directory symlinks remain usable.
Both complete catalog genomes were imported and verified through all three backends;
the HTTPS installer also passed a resumed sacCer3 download and offline reinstall.

Earlier interrupted Docker and failed preflight diagnostics remain historical
evidence, not accepted checks; the repaired candidate was rebuilt and retested.
No host service was restarted. Linux arm64 Apptainer was not separately tested.
Both native-platform and supported-backend evidence dimensions
are closed, without an architecture-specific resource/GPU/GUI coupling; this is
not a claim of a fully tested platform × backend Cartesian product.

Docker image sizes are 456912861 bytes (arm64) and 423509949 bytes (amd64).
Podman reports 465388087 bytes for the same arm64 image ID because of engine size
accounting; these are not different candidates. Build-stage
compilers/caches and unused NumPy/SciPy test trees are excluded; runtime modules,
fonts, Python licenses and 165 fixed Rust crate notice sets are retained. The
upstream-declared maturin dependency remains installed rather than breaking its
metadata contract. No large genome reference is baked into either image.

See `release.md` for evidence and release boundaries. Tiny tests do not replace
scientific validation on real experiments. Administrator-once sharing was exercised
through ordinary-user private site copies with 0755/0644 permissions and read-only
binds, not by modifying a real system directory or switching to root.

## License and Citation

Packaging: Apache-2.0 (`LICENSE`). deepTools: MIT; upstream notices, Cargo.lock and
dependency freezes are under `/opt/deeptools/share/doc/deeptools/`. Debian copyright
files and Python distribution/bundled-library license files are retained.

Ramírez et al. (2016), *deepTools2: a next generation web server for deep-sequencing
data analysis*. [doi:10.1093/nar/gkw257](https://doi.org/10.1093/nar/gkw257).
