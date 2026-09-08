#!/usr/bin/env python3
"""独立离线 smoke：每次调用只在唯一临时目录写入；失败保留精确命令和日志尾部。"""
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
    print('stage: '+shlex.join(args),flush=True)
    r = subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
    if (r.returncode == 0) == fail or (marker and marker.lower() not in r.stdout.lower()):
        print('\n'.join(r.stdout.splitlines()[-80:]),flush=True)
        raise RuntimeError(f'exit={r.returncode}; expected={"nonzero" if fail else "zero"}; marker={marker}')
    return r.stdout

def nonempty(*names):
    for name in names:
        assert Path(name).is_file() and Path(name).stat().st_size > 0, name

def identity():
    assert md.version('deeptools') == '4.0.0'
    assert md.version('deeptoolsintervals') == '0.1.9'
    for line in Path('/opt/deeptools/share/doc/deeptools/requirements.lock').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.split()[0].split('==')
            assert md.version(name) == version, (name,md.version(name),version)
    import deeptools.hp, deeptoolsintervals, matplotlib, numpy, py2bit, pyBigWig, pysam, scipy
    assert len(COMMANDS) == 27, COMMANDS
    run('deeptools','--version',marker='deeptools 4.0.0')
    run('python','-m','pip','check',marker='No broken requirements')
    root = Path('/opt/deeptools/share/doc/deeptools/upstream/rust-notices')
    inventory = json.loads((root/'inventory.json').read_text())
    for crate in inventory:
        assert crate['files'], crate['crate']
        for member in crate['files']:
            assert hashlib.sha256((root/member['path']).read_bytes()).hexdigest() == member['sha256'], member['path']
    sbom = json.loads(next(Path('/opt/deeptools/lib/python3.12/site-packages').glob('deeptools-*.dist-info/sboms/*.json')).read_text())
    covered = {c['crate'] for c in inventory} | {'deeptools-4.0.0'}
    assert all(c['name']+'-'+c['version'] in covered for c in sbom['components'])

def coverage(command='bamCoverage', sample=1, out='one.bw'):
    run(command,'-b',DATA/f'sample{sample}.bam','-o',out,'--binSize','10','--numberOfProcessors','1')
    import pyBigWig
    with pyBigWig.open(out) as bw:
        assert bw.chroms() == {'chr1':1000}
        assert bw.stats('chr1',100,200,type='max')[0] > 0

def core(suffix=''):
    import numpy as np
    import pysam
    coverage('bamCoverage'+suffix)
    run('bamCompare'+suffix,'-b1',DATA/'sample1.bam','-b2',DATA/'sample2.bam',
        '-o','compare.bw','--binSize','10','-p','1')
    run('multiBamSummary'+suffix,'bins','-b',DATA/'sample1.bam',DATA/'sample2.bam',DATA/'sample3.bam',
        '-o','summary.npz','--binSize','100','-p','1')
    matrix = np.load('summary.npz')['matrix']
    assert matrix.shape[1] == 3 and matrix.sum() > 0, matrix
    run('alignmentSieve'+suffix,'-b',DATA/'sample1.bam','-o','filtered.bam','--minMappingQuality','10','-p','1')
    with pysam.AlignmentFile('filtered.bam') as bam:
        assert sum(1 for _ in bam.fetch(until_eof=True)) == 8
    run('computeMatrix'+suffix,'scale-regions','-S','one.bw','-R',DATA/'regions.bed',
        '-o','matrix.gz','--regionBodyLength','100','-p','1')
    with gzip.open('matrix.gz','rt') as f:
        assert f.readline().startswith('@') and len(f.readlines()) == 3
    if not suffix:
        run('computeMatrix','scale-regions','-S','one.bw','-R',DATA/'regions.bed.gz',
            '-o','matrix-gzip.gz','--regionBodyLength','100','-p','1')
        with gzip.open('matrix.gz','rb') as a, gzip.open('matrix-gzip.gz','rb') as b:
            # 头部可能记录输入名称；只比较实际 matrix 行。
            assert a.read().splitlines()[1:] == b.read().splitlines()[1:]
    nonempty('compare.bw','summary.npz','matrix.gz')

def plots():
    core()
    coverage(sample=2,out='two.bw')
    run('multiBigwigSummary','bins','-b','one.bw','two.bw','-o','bigwig.npz','--binSize','100','-p','1')
    run('bigwigAverage','-b','one.bw','two.bw','-o','average.bw','-p','1')
    run('bigwigCompare','-b1','one.bw','-b2','two.bw','-o','ratio.bw','-p','1')
    run('computeMatrixOperations','info','-m','matrix.gz',marker='Samples')
    run('plotHeatmap','-m','matrix.gz','-out','heatmap.png')
    run('plotProfile','-m','matrix.gz','-out','profile.pdf')
    run('plotCorrelation','-in','summary.npz','--corMethod','pearson','--whatToPlot','heatmap','-o','correlation.svg')
    run('plotPCA','-in','summary.npz','-o','pca.png','--outFileNameData','pca.tsv','--ggplot')
    nonempty('heatmap.png','profile.pdf','correlation.svg','pca.png','pca.tsv')
    from PIL import Image
    for name in ['heatmap.png','pca.png']:
        with Image.open(name) as im:
            assert min(im.size) > 100 and len(im.convert('RGB').getcolors(1000000) or []) > 10
    assert Path('profile.pdf').read_bytes().startswith(b'%PDF')
    assert '<svg' in Path('correlation.svg').read_text()

def gc():
    import numpy as np
    import pysam
    d = DATA/'gc'
    run('computeGCBias','-b',d/'paired_chr2L.bam','-g',d/'sequence.2bit',
        '--effectiveGenomeSize','10050','--sampleSize','1000','-l','150','-freq','frequency.tsv','-p','1')
    assert np.isfinite(np.loadtxt('frequency.tsv')).all()
    run('correctGCBias','-b',d/'paired_chr2L.bam','-g',d/'sequence.2bit',
        '--effectiveGenomeSize','10050','--GCbiasFrequenciesFile',d/'computeGCBias_result1.tabular',
        '-o','corrected.bam','-p','1')
    with pysam.AlignmentFile('corrected.bam') as f:
        assert sum(1 for _ in f.fetch(until_eof=True)) > 0
    run('estimateReadFiltering','-b',DATA/'sample1.bam','--minMappingQuality','10')
    run('estimateScaleFactor','-b',DATA/'sample1.bam',DATA/'sample2.bam','-p','1')

def resources():
    import hashlib
    source = DATA/'gc/sequence.2bit'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    args = ['deeptools-resources','install','--resource','local-test','--resource-root',str(Path.cwd()/'resources'),
            '--source',str(source),'--sha256',checksum,'--assembly','tiny-chr2L','--license-note','upstream MIT test fixture']
    run('deeptools-resources','list',marker='ucsc-hg38')
    run(*args,'--dry-run',marker='required_free_bytes')
    assert not Path('resources').exists()
    run(*args,marker='installed resource=')
    run(*args,marker='already installed')
    run('deeptools-resources','verify','resources/local-test',marker='verified resource=')
    run('deeptools-resources','verify','resources/local-test','--expected-resource','local-test',marker='verified resource=')
    run('deeptools-resources','verify','resources/local-test','--expected-resource','local-other',fail=True,marker='identity mismatch')
    for member in ['genome.2bit','resource.json','SHA256SUMS','READY']:
        damaged = Path('symlink-'+member)
        shutil.copytree('resources/local-test', damaged)
        (damaged/member).unlink()
        (damaged/member).symlink_to((Path('resources/local-test')/member).resolve())
        run('deeptools-resources','verify',damaged,fail=True,marker='member or symlink')
    for label in ['missing','extra','hidden-extra']:
        damaged = Path(label)
        shutil.copytree('resources/local-test',damaged)
        if label == 'missing': (damaged/'genome.2bit').unlink()
        else: (damaged/('.unexpected' if label=='hidden-extra' else 'unexpected')).touch()
        run('deeptools-resources','verify',damaged,fail=True,marker='member or symlink')
    Path('resources/.local-locked.lock').mkdir()
    locked = args.copy(); locked[locked.index('local-test')] = 'local-locked'
    run(*locked,fail=True,marker='lock exists')
    assert not Path('resources/local-locked').exists()
    with Path('resources/local-test/genome.2bit').open('ab') as f: f.write(b'bad')
    run('deeptools-resources','verify','resources/local-test',fail=True,marker='checksum mismatch')
    run(*args,fail=True,marker='checksum mismatch')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['buildtime','identity','help','core','legacy','plots','gc','resources'])
    p.add_argument('--outdir',type=Path,help='new empty output directory for visual review; default unique /tmp')
    a = p.parse_args()
    owner = tempfile.TemporaryDirectory(prefix='taf-deeptools-',dir='/tmp') if a.outdir is None else None
    work = Path(owner.name) if owner else a.outdir.resolve()
    if not owner: work.mkdir(parents=True,exist_ok=False)
    old = Path.cwd()
    try:
        os.chdir(work)
        os.environ.update(TMPDIR=str(work),MPLCONFIGDIR=str(work/'mpl'),XDG_CACHE_HOME=str(work/'cache'))
        if a.mode == 'buildtime': identity(); coverage()
        elif a.mode == 'identity': identity()
        elif a.mode == 'help':
            for command in COMMANDS: run(command,'--help',marker='usage:')
            run('deeptools-resources','--help',marker='usage:')
        elif a.mode == 'core': core()
        elif a.mode == 'legacy': core('_old')
        else: globals()[a.mode]()
        print('PASS '+a.mode,flush=True)
    finally:
        os.chdir(old)
        if owner: owner.cleanup()

if __name__ == '__main__': main()
