#!/usr/bin/env python3
"""显式、固定成员的 2bit 参考安装；不在分析阶段联网或选择 assembly。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

SCHEMA = 'taffish.deeptools.resource.v1'
CATALOG = {
    'ucsc-sacCer3-b061b22f': dict(assembly='sacCer3', bytes=3039745,
        sha256='b061b22fdce3cb82c24d85101bc6eae98d23ea7194c1888c966b5446dd7909ab',
        url='https://hgdownload.soe.ucsc.edu/goldenPath/sacCer3/bigZips/sacCer3.2bit'),
    'ucsc-hg38-1f67aaa1': dict(assembly='hg38-initial-GRCh38', bytes=835393456,
        sha256='1f67aaa17a77b327738fe750ab37430a85dddf73c7d9189385ad1839259acec0',
        url='https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.2bit'),
}
for item in CATALOG.values():
    item.update(kind='genome-2bit', license='UCSC downloadable genome data; underlying assembly rights apply',
                license_url='https://genome.ucsc.edu/license/', attribution='UCSC Genome Browser and original genome assembly contributors')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def chromosomes(path):
    import py2bit
    with path.open('rb') as f:
        if f.read(4) not in (bytes.fromhex('1a412743'), bytes.fromhex('4327411a')):
            raise ValueError('source is not a UCSC 2bit file')
    with py2bit.open(str(path)) as reference:
        result = reference.chroms()
        if not result or any(n <= 0 for n in result.values()):
            raise ValueError('empty or invalid chromosome inventory')
        for name, size in result.items():
            if len(reference.sequence(name, 0, min(size, 32))) != min(size, 32):
                raise ValueError('unreadable reference member')
    return result

def verify(root, expected_resource=None):
    if root.is_symlink() or not root.is_dir():
        raise ValueError('resource root must be a physical directory')
    expected = {'genome.2bit','resource.json','SHA256SUMS','READY'}
    if {p.name for p in root.iterdir()} != expected or any(p.is_symlink() or not p.is_file() for p in root.iterdir()):
        raise ValueError('missing/extra resource member or symlink')
    if digest(root/'SHA256SUMS') != (root/'READY').read_text().strip():
        raise ValueError('invalid READY/SHA256SUMS')
    rows = {}
    for line in (root/'SHA256SUMS').read_text().splitlines():
        checksum, name = line.split('  ',1)
        if name not in {'genome.2bit','resource.json'} or name in rows or not re.fullmatch('[a-f0-9]{64}', checksum):
            raise ValueError('invalid checksum inventory')
        if digest(root/name) != checksum:
            raise ValueError('checksum mismatch: '+name)
        rows[name] = checksum
    if set(rows) != {'genome.2bit','resource.json'}:
        raise ValueError('incomplete checksum inventory')
    receipt = json.loads((root/'resource.json').read_text())
    if receipt['schema'] != SCHEMA or receipt['source']['sha256'] != rows['genome.2bit']:
        raise ValueError('invalid resource identity')
    identity = receipt['resource']
    if not isinstance(identity, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*', identity):
        raise ValueError('invalid resource ID')
    if expected_resource is not None and identity != expected_resource:
        raise ValueError(f'resource identity mismatch: requested={expected_resource} actual={identity}')
    if identity not in CATALOG and not re.fullmatch('local-[A-Za-z0-9_.-]+', identity):
        raise ValueError('unknown resource ID; non-catalog references require local-*')
    if receipt['source']['bytes'] != (root/'genome.2bit').stat().st_size:
        raise ValueError('resource size mismatch')
    if receipt['resource'] in CATALOG and receipt['source'] != CATALOG[receipt['resource']]:
        raise ValueError('receipt differs from fixed catalog')
    if receipt['chromosomes'] != chromosomes(root/'genome.2bit'):
        raise ValueError('chromosome inventory mismatch')
    print('verified resource='+receipt['resource'], flush=True)
    return receipt

def install(args):
    identity = args.resource
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*', identity):
        raise ValueError('choose an explicit safe resource ID')
    source = Path(args.source).resolve() if args.source else None
    item = CATALOG.get(identity)
    if item is None:
        if not identity.startswith('local-') or source is None or not args.assembly or not args.license_note or not re.fullmatch('[a-f0-9]{64}', args.sha256 or ''):
            raise ValueError('local-* requires --source, --sha256, --assembly and --license-note recording authorized use/sharing')
        item = dict(kind='genome-2bit', assembly=args.assembly, sha256=args.sha256,
                    bytes=source.stat().st_size, license=args.license_note, origin=source.name)
    root = Path(args.resource_root).resolve()
    target = root/identity
    required = 2*item['bytes']+67108864
    if args.dry_run:
        print(json.dumps(dict(resource=identity,source=item,target=str(target),required_free_bytes=required),indent=2))
        return
    if target.exists() or target.is_symlink():
        old = verify(target, identity)
        if old['resource'] != identity or old['source'] != item:
            raise ValueError('existing identity differs; choose a new immutable ID/root')
        print('already installed; no writes or download')
        return
    root.mkdir(parents=True,exist_ok=True)
    lock = root/('.'+identity+'.lock')
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError:
        raise ValueError(f'lock exists: {lock}; inspect owner before any recovery') from None
    stage = None
    try:
        (lock/'owner.json').write_text(json.dumps(dict(uid=os.getuid(),pid=os.getpid(),time=time.time())))
        if shutil.disk_usage(root).free < required:
            raise ValueError(f'insufficient free space; require {required} bytes')
        if source is None:
            cache = root/'.downloads'
            cache.mkdir(mode=0o700,exist_ok=True)
            source = cache/(item['sha256']+'.part')
            if source.is_symlink():
                raise ValueError('download cache cannot be a symlink')
            if not source.exists() or source.stat().st_size < item['bytes']:
                print('downloading '+identity+' (resume supported)',flush=True)
                subprocess.run(['curl','--fail','--location','--proto','=https','--proto-redir','=https',
                    '--retry','3','--retry-all-errors','--connect-timeout','30','--max-time','1800',
                    '--continue-at','-','--output',str(source),item['url']],check=True)
        if source.stat().st_size != item['bytes'] or digest(source) != item['sha256']:
            raise ValueError('source checksum/size mismatch; nothing promoted, retain cache for diagnosis')
        inventory = chromosomes(source)
        stage = Path(tempfile.mkdtemp(prefix='.'+identity+'.stage-',dir=root))
        shutil.copyfile(source,stage/'genome.2bit')
        receipt = dict(schema=SCHEMA,resource=identity,source=item,chromosomes=inventory,
                       created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),uid=os.getuid())
        (stage/'resource.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
        (stage/'SHA256SUMS').write_text(''.join(digest(stage/name)+'  '+name+'\n' for name in ['genome.2bit','resource.json']))
        (stage/'READY').write_text(digest(stage/'SHA256SUMS')+'\n')
        for p in stage.iterdir(): p.chmod(0o644)
        stage.chmod(0o755)
        verify(stage)
        if target.exists(): raise ValueError('target appeared; refusing overwrite')
        stage.rename(target)
        stage = None
        print('installed resource='+identity+' root='+str(target))
    finally:
        if stage is not None: shutil.rmtree(stage)
        (lock/'owner.json').unlink(missing_ok=True)
        lock.rmdir()

def main():
    p = argparse.ArgumentParser(description='Explicit immutable 2bit reference members; analysis never downloads resources.')
    sub = p.add_subparsers(dest='command',required=True)
    sub.add_parser('list',help='show fixed members; no default genome and no download')
    v = sub.add_parser('verify',help='offline full inventory/2bit check; no writes'); v.add_argument('root')
    v.add_argument('--expected-resource',help='also require this exact resource ID')
    i = sub.add_parser('install',help='atomic download/local import into an explicitly writable parent')
    i.add_argument('--resource',required=True); i.add_argument('--resource-root',required=True)
    i.add_argument('--source'); i.add_argument('--sha256'); i.add_argument('--assembly'); i.add_argument('--license-note')
    i.add_argument('--dry-run',action='store_true')
    a = p.parse_args(); os.umask(0o022)
    if a.command == 'list': print(json.dumps(CATALOG,indent=2))
    elif a.command == 'verify': verify(Path(a.root), a.expected_resource)
    else: install(a)

if __name__ == '__main__':
    try: main()
    except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as e:
        print('deeptools-resources: '+str(e),file=sys.stderr); sys.exit(1)
