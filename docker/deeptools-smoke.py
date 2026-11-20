#!/usr/bin/env python3
"""Independent offline checks using tiny synthetic inputs; no scientific validation."""
import argparse
import gzip
import hashlib
import importlib.metadata as md
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

DATA = Path('/opt/deeptools/share/testdata')
COMMANDS = sorted(e.name for e in md.distribution('deeptools').entry_points if e.group == 'console_scripts')

def run(*args, marker=None, fail=False):
    args = [str(a) for a in args]
    print('stage: ' + shlex.join(args), flush=True)
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=180)
    if (result.returncode == 0) == fail or (marker and marker.lower() not in result.stdout.lower()):
        print(result.stdout[-16000:], flush=True)
        raise RuntimeError(f'exit={result.returncode}; expected={"nonzero" if fail else "zero"}; marker={marker}')
    return result.stdout

def version_gate(text, code):
    if code != 0 or text.strip().lower() != 'deeptools 4.1.0':
        raise ValueError(f'incorrect deepTools identity: exit={code}, output={text!r}')

def identity():
    assert md.version('deeptools') == '4.1.0'
    assert len(COMMANDS) == 20, COMMANDS
    for line in Path('/opt/deeptools/share/doc/deeptools/requirements.lock').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.split()[0].split('==')
            assert md.version(name) == version, (name, md.version(name), version)
    import deeptools.hp, deeptoolsintervals, matplotlib, numpy, pyBigWig, pysam, scipy
    version_gate(run('deeptools', '--version'), 0)
    for value, code in [('deeptools 4.1.0', 1), ('deeptools 4.1.0-old', 0), ('deeptools 4.0.0', 0)]:
        try:
            version_gate(value, code)
        except ValueError:
            pass
        else:
            raise AssertionError('version gate accepted incorrect identity')
    run('python', '-m', 'pip', 'check', marker='No broken requirements')
    for removed in ['computeGCBias', 'correctGCBias', 'bamCoverage_old', 'bamCompare_old',
                    'alignmentSieve_old', 'computeMatrix_old', 'multiBamSummary_old', 'deeptools-resources']:
        assert shutil.which(removed) is None, removed
    root = Path('/opt/deeptools/share/doc/deeptools/upstream/rust-notices')
    inventory = json.loads((root / 'inventory.json').read_text())
    for crate in inventory:
        assert crate['files'], crate['crate']
        for member in crate['files']:
            assert hashlib.sha256((root / member['path']).read_bytes()).hexdigest() == member['sha256']
    sbom = json.loads(next(Path('/opt/deeptools/lib/python3.12/site-packages').glob('deeptools-*.dist-info/sboms/*.json')).read_text())
    covered = {c['crate'] for c in inventory}
    assert all(c['name'] + '-' + c['version'] in covered for c in sbom['components'])

def coverage():
    run('bamCoverage', '-b', DATA / 'sample1.bam', '-o', 'one.bw', '--binSize', '10', '-p', '1')
    import pyBigWig
    with pyBigWig.open('one.bw') as bw:
        assert bw.chroms() == {'chr1': 1000}
        assert bw.stats('chr1', 100, 200, type='max')[0] > 0

def core():
    import numpy as np
    import pysam
    import pyBigWig
    coverage()
    run('bamCompare', '-b1', DATA / 'sample1.bam', '-b2', DATA / 'sample2.bam',
        '-o', 'compare.bw', '--binSize', '10', '-p', '1')
    run('multiBamSummary', 'bins', '-b', DATA / 'sample1.bam', DATA / 'sample2.bam', DATA / 'sample3.bam',
        '-o', 'summary.npz', '--binSize', '100', '-p', '1')
    matrix = np.load('summary.npz')['matrix']
    assert matrix.shape == (10, 3) and np.isfinite(matrix).all() and matrix.sum() > 0
    for extra, name in [([], 'filtered'), (['--shift', '0', '0', '--keepTags', 'NM', 'RG'], 'tagged')]:
        run('alignmentSieve', '-b', DATA / 'sample1.bam', '-o', name + '.bam',
            '--minMappingQuality', '10', '-p', '1', *extra)
        with pysam.AlignmentFile(name + '.bam') as bam:
            reads = list(bam.fetch(until_eof=True))
            assert len(reads) == 8
            if name == 'tagged':
                assert all(r.get_tag('NM') == 1 and r.get_tag('RG') == 'synthetic' for r in reads)
    for bed, out in [('regions.bed', 'matrix.gz'), ('regions.bed.gz', 'matrix-gzip.gz')]:
        run('computeMatrix', 'scale-regions', '-S', 'one.bw', '-R', DATA / bed,
            '-o', out, '--regionBodyLength', '100', '-p', '1')
    with gzip.open('matrix.gz', 'rb') as a, gzip.open('matrix-gzip.gz', 'rb') as b:
        rows = a.read().splitlines()
        assert rows[0].startswith(b'@') and len(rows) == 4
        assert rows[1:] == b.read().splitlines()[1:]
    # Explicit scaling isolates the documented "first" operand from normalization.
    run('bamCompare', '-b1', DATA / 'sample1.bam', '-b2', DATA / 'sample2.bam',
        '-o', 'first.bw', '--binSize', '10', '--operation', 'first',
        '--scaleFactorsMethod', 'None', '--scaleFactors', '1:1', '-p', '1')
    with pyBigWig.open('one.bw') as x, pyBigWig.open('first.bw') as y:
        np.testing.assert_allclose(x.values('chr1', 0, 1000), y.values('chr1', 0, 1000))

def plot_inputs():
    import numpy as np
    import pyBigWig
    for sample in range(3):
        with pyBigWig.open(f'signal{sample}.bw', 'w') as bw:
            bw.addHeader([('chr1', 1000)])
            bw.addEntries(['chr1'] * 10, list(range(0, 1000, 100)),
                          ends=list(range(100, 1100, 100)),
                          values=[float((i * (sample + 2) + sample) % 11 + 1) for i in range(10)])
    np.savez_compressed('summary.npz',
        matrix=np.array([[((i * (s + 2) + s) % 11) + 1.0 for s in range(3)] for i in range(10)]),
        labels=np.array(['sample A', 'sample B', 'sample C']))
    run('computeMatrix', 'scale-regions', '-S', 'signal0.bw', 'signal1.bw',
        '-R', DATA / 'regions.bed', '-o', 'matrix.gz', '--regionBodyLength', '100', '-p', '1')

def image_check(*names):
    from PIL import Image
    for name in names:
        path = Path(name)
        assert path.stat().st_size > 100, name
        if name.endswith('.png'):
            with Image.open(path) as im:
                assert min(im.size) > 100 and len(im.convert('RGB').getcolors(1000000) or []) > 10
        elif name.endswith('.pdf'):
            assert path.read_bytes().startswith(b'%PDF')
        elif name.endswith('.svg'):
            assert '<svg' in path.read_text()

def plots():
    plot_inputs()
    run('multiBigwigSummary', 'bins', '-b', 'signal0.bw', 'signal1.bw', '-o', 'bigwig.npz', '--binSize', '100', '-p', '1')
    run('bigwigAverage', '-b', 'signal0.bw', 'signal1.bw', '-o', 'average.bw', '-p', '1')
    run('bigwigCompare', '-b1', 'signal0.bw', '-b2', 'signal1.bw', '-o', 'ratio.bw', '-p', '1')
    run('computeMatrixOperations', 'info', '-m', 'matrix.gz', marker='Samples')
    run('plotHeatmap', '-m', 'matrix.gz', '-out', 'heatmap.png', '--colors', '#147d92', '#bb5f23', '-p', '2')
    run('plotProfile', '-m', 'matrix.gz', '-out', 'profile.pdf', '-p', '2')
    run('plotCorrelation', '-in', 'summary.npz', '--corMethod', 'pearson', '--whatToPlot', 'heatmap', '-o', 'correlation.svg')
    run('plotPCA', '-in', 'summary.npz', '-o', 'pca.png', '--outFileNameData', 'pca.tsv', '--ggplot')
    assert all(x in Path('pca.tsv').read_text() for x in ['sample A', 'sample B', 'sample C'])
    image_check('heatmap.png', 'profile.pdf', 'correlation.svg', 'pca.png')

def qc():
    bams = [DATA / f'sample{i}.bam' for i in (1, 2)]
    run('plotCoverage', '-b', *bams, '-o', 'coverage.png', '--numberOfSamples', '100', '-p', '1')
    run('plotFingerprint', '-b', *bams, '-o', 'fingerprint.png', '--numberOfSamples', '100',
        '--binSize', '10', '--extendReads', '150', '-p', '1', '--outRawCounts', 'fingerprint.tsv')
    run('plotEnrichment', '-b', *bams, '--BED', DATA / 'regions.bed', '-o', 'enrichment.png',
        '--outRawCounts', 'enrichment.tsv', '-p', '1')
    run('bamPEFragmentSize', '-b', *bams, '-hist', 'fragment.png', '--samplesLabel', 'A', 'B', '-p', '1')
    run('estimateReadFiltering', '-b', bams[0], '--minMappingQuality', '10')
    run('estimateScaleFactor', '-b', *bams, '-p', '1')
    image_check('coverage.png', 'fingerprint.png', 'enrichment.png', 'fragment.png')
    assert Path('enrichment.tsv').stat().st_size > 20

def validation():
    run('bamCoverage', '-b', 'missing input.bam', '-o', 'missing.bw', fail=True)
    assert not Path('missing.bw').exists()
    run('bamCompare', '-b1', DATA / 'sample1.bam', '-b2', DATA / 'sample2.bam',
        '-o', 'invalid.bw', '--normalizeUsing', 'RPGC', fail=True, marker='RPGC')
    run('alignmentSieve', '-b', DATA / 'sample1.bam', '-o', 'bad.bam', '--keepTags', 'NM',
        fail=True, marker='--keepTags')
    run('plotCoverage', '-b', DATA / 'sample1.bam', DATA / 'sample2.bam',
        '-o', 'bad-label.png', '--labels', 'one', fail=True, marker='labels')
    plot_inputs()
    run('plotPCA', '-in', 'summary.npz', '-o', 'old.png', '--transpose', fail=True, marker='unrecognized')
    Path('bad.bed').write_text('chr1\t200\t100\tbad\t0\t+\nchr1\t80\t230\tgood\t0\t+\n')
    run('computeMatrix', 'scale-regions', '-S', 'signal0.bw', '-R', 'bad.bed',
        '-o', 'bad-matrix.gz', marker='Skipping.')
    # Upstream deliberately warns and skips invalid intervals, not a fatal exit.
    with gzip.open('bad-matrix.gz', 'rt') as stream:
        rows = stream.read().splitlines()
        assert len(rows) == 2 and rows[1].split('\t')[3] == 'good', rows
    for cmd in ['computeGCBias', 'correctGCBias', 'bamCoverage_old']:
        assert shutil.which(cmd) is None

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['buildtime', 'identity', 'help', 'core', 'plots', 'qc', 'validation'])
    p.add_argument('--outdir', type=Path, help='new output directory for inspection; default unique /tmp')
    a = p.parse_args()
    owner = tempfile.TemporaryDirectory(prefix='taf-deeptools-', dir='/tmp') if a.outdir is None else None
    work = Path(owner.name) if owner else a.outdir.resolve()
    if not owner:
        work.mkdir(parents=True, exist_ok=False)
    old = Path.cwd()
    try:
        os.chdir(work)
        os.environ.update(TMPDIR=str(work), MPLCONFIGDIR=str(work / 'mpl'), XDG_CACHE_HOME=str(work / 'cache'))
        if a.mode == 'buildtime':
            identity()
            coverage()
        elif a.mode == 'help':
            for command in COMMANDS:
                run(command, '--help', marker='usage:')
        else:
            globals()[a.mode]()
        print('PASS ' + a.mode, flush=True)
    finally:
        os.chdir(old)
        if owner:
            owner.cleanup()

if __name__ == '__main__':
    main()
