#!/usr/bin/env python3
from pathlib import Path
import gzip

import pysam


OUTDIR = Path("/opt/deeptools/share/testdata")
OUTDIR.mkdir(parents=True, exist_ok=True)

HEADER = {
    "HD": {"VN": "1.6", "SO": "coordinate"},
    "SQ": [{"SN": "chr1", "LN": 1000}],
}


def make_segment(qname, flag, start, mate_start, template_length):
    read = pysam.AlignedSegment()
    read.query_name = qname
    read.query_sequence = "A" * 50
    read.flag = flag
    read.reference_id = 0
    read.reference_start = start
    read.mapping_quality = 60
    read.cigar = [(0, 50)]
    read.next_reference_id = 0
    read.next_reference_start = mate_start
    read.template_length = template_length
    read.query_qualities = pysam.qualitystring_to_array("F" * 50)
    return read


def write_paired_bam(path, fragment_starts):
    reads = []
    for i, start in enumerate(fragment_starts, 1):
        mate_start = start + 100
        qname = f"{path.stem}_{i}"
        reads.append(make_segment(qname, 99, start, mate_start, 150))
        reads.append(make_segment(qname, 147, mate_start, start, -150))
    reads.sort(key=lambda read: read.reference_start)
    with pysam.AlignmentFile(path, "wb", header=HEADER) as bam:
        for read in reads:
            bam.write(read)
    pysam.index(str(path))


write_paired_bam(OUTDIR / "sample1.bam", [100, 240, 500, 720])
write_paired_bam(OUTDIR / "sample2.bam", [120, 280, 560, 800])
write_paired_bam(OUTDIR / "sample3.bam", [100, 140, 180, 450, 480, 760])

(OUTDIR / "regions.bed").write_text(
    "chr1\t80\t230\tregion_a\t0\t+\n"
    "chr1\t450\t620\tregion_b\t0\t+\n"
    "chr1\t700\t920\tregion_c\t0\t+\n"
)
(OUTDIR / "genome.sizes").write_text("chr1\t1000\n")
with gzip.GzipFile(str(OUTDIR / 'regions.bed.gz'), 'wb', mtime=0) as stream:
    stream.write((OUTDIR / 'regions.bed').read_bytes())
(OUTDIR / "README.txt").write_text(
    "TAFFISH deepTools 极小合成 paired-end BAM：chr1/1000bp，3 个样本，\n"
    "用于结构、命令和运行时回归，不代表科学正确性或真实测序性能。\n"
)
