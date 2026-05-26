ARG DEEPTOOLS_VERSION=3.5.6
ARG DEEPTOOLS_INTERVALS_VERSION=0.1.9
ARG DEBIAN_MIRROR=http://deb.debian.org/debian
ARG DEBIAN_SECURITY_MIRROR=http://deb.debian.org/debian-security

FROM python:3.11-slim-bookworm AS builder

ARG DEEPTOOLS_VERSION
ARG DEEPTOOLS_INTERVALS_VERSION
ARG DEBIAN_MIRROR
ARG DEBIAN_SECURITY_MIRROR

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DEFAULT_TIMEOUT=120
ENV PIP_RETRIES=5
ENV PYTHONNOUSERSITE=1
ENV MPLBACKEND=Agg

RUN set -eux; \
    sed -i \
      -e "s|http://deb.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
      -e "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g" \
      /etc/apt/sources.list.d/debian.sources; \
    for attempt in 1 2 3; do \
      if apt-get -o Acquire::Retries=3 update \
       && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
            build-essential \
            ca-certificates \
            libbz2-dev \
            libcurl4-openssl-dev \
            liblzma-dev \
            zlib1g-dev; then \
        break; \
      fi; \
      if [ "$attempt" = "3" ]; then exit 1; fi; \
      apt-get clean; \
      rm -rf /var/lib/apt/lists/*; \
      sleep 5; \
    done; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    python -m venv /opt/deeptools; \
    /opt/deeptools/bin/python -m pip install --upgrade pip setuptools wheel; \
    /opt/deeptools/bin/python -m pip install \
      "deeptoolsintervals==${DEEPTOOLS_INTERVALS_VERSION}" \
      "deepTools==${DEEPTOOLS_VERSION}"; \
    /opt/deeptools/bin/python -m pip check; \
    /opt/deeptools/bin/python -m pip freeze --all > /opt/deeptools/requirements.freeze.txt

COPY docker/make_testdata.py /tmp/make_testdata.py

RUN set -eux; \
    /opt/deeptools/bin/python /tmp/make_testdata.py; \
    rm -f /tmp/make_testdata.py; \
    mkdir -p /opt/deeptools/share/doc/deeptools; \
    mv /opt/deeptools/requirements.freeze.txt /opt/deeptools/share/doc/deeptools/requirements.freeze.txt; \
    printf "%s\n" "${DEEPTOOLS_VERSION}" > /opt/deeptools/share/doc/deeptools/VERSION

RUN set -eux; \
    export PATH="/opt/deeptools/bin:${PATH}"; \
    deeptools --version | grep -Fx "deeptools ${DEEPTOOLS_VERSION}" >/dev/null; \
    deeptools --help | grep -F "bamCoverage" >/dev/null; \
    bamCoverage --help 2>&1 | grep -F "usage: bamCoverage" >/dev/null; \
    computeMatrix --help 2>&1 | grep -F "usage: computeMatrix" >/dev/null; \
    plotHeatmap --help 2>&1 | grep -F "usage: plotHeatmap" >/dev/null; \
    /opt/deeptools/bin/python -c 'import deeptools, deeptoolsintervals, matplotlib, numpy, plotly, py2bit, pyBigWig, pysam, scipy'

RUN set -eux; \
    export PATH="/opt/deeptools/bin:${PATH}"; \
    data=/opt/deeptools/share/testdata; \
    tmp=/tmp/taf-deeptools-runtime-check; \
    rm -rf "$tmp"; \
    mkdir -p "$tmp"; \
    cd "$tmp"; \
    bamCoverage -b "$data/sample1.bam" -o sample1.bw --binSize 10 --numberOfProcessors 1; \
    bamCoverage -b "$data/sample2.bam" -o sample2.bw --binSize 10 --numberOfProcessors 1; \
    test -s sample1.bw; \
    test -s sample2.bw; \
    multiBamSummary bins --bamfiles "$data/sample1.bam" "$data/sample2.bam" -out bam_summary.npz --binSize 100 --numberOfProcessors 1; \
    test -s bam_summary.npz; \
    plotCorrelation -in bam_summary.npz --corMethod pearson --whatToPlot heatmap -o correlation.png; \
    test -s correlation.png; \
    multiBigwigSummary bins -b sample1.bw sample2.bw -out bigwig_summary.npz --binSize 100 --numberOfProcessors 1; \
    test -s bigwig_summary.npz; \
    computeMatrix scale-regions -S sample1.bw sample2.bw -R "$data/regions.bed" -o matrix.gz --regionBodyLength 100 --beforeRegionStartLength 0 --afterRegionStartLength 0 --numberOfProcessors 1; \
    test -s matrix.gz; \
    plotHeatmap -m matrix.gz -out heatmap.png; \
    plotProfile -m matrix.gz -out profile.png; \
    test -s heatmap.png; \
    test -s profile.png; \
    bigwigAverage -b sample1.bw sample2.bw -o average.bw; \
    bigwigCompare -b1 sample1.bw -b2 sample2.bw -o compare.bw; \
    test -s average.bw; \
    test -s compare.bw; \
    alignmentSieve -b "$data/sample1.bam" -o filtered.bam --minMappingQuality 10 --numberOfProcessors 1; \
    test -s filtered.bam; \
    estimateReadFiltering -b "$data/sample1.bam" --minMappingQuality 10 > filtering.tsv; \
    test -s filtering.tsv; \
    rm -rf "$tmp"

FROM python:3.11-slim-bookworm

ARG DEBIAN_MIRROR
ARG DEBIAN_SECURITY_MIRROR

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONNOUSERSITE=1
ENV MPLBACKEND=Agg
ENV OPENBLAS_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV PATH=/opt/deeptools/bin:${PATH}
ENV DEEPTOOLS_HOME=/opt/deeptools
ENV DEEPTOOLS_TESTDATA=/opt/deeptools/share/testdata

RUN set -eux; \
    sed -i \
      -e "s|http://deb.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
      -e "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g" \
      /etc/apt/sources.list.d/debian.sources; \
    for attempt in 1 2 3; do \
      if apt-get -o Acquire::Retries=3 update \
       && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
            bash \
            ca-certificates \
            fontconfig \
            fonts-dejavu-core \
            libbz2-1.0 \
            libcurl4 \
            libgomp1 \
            liblzma5 \
            libstdc++6 \
            zlib1g; then \
        break; \
      fi; \
      if [ "$attempt" = "3" ]; then exit 1; fi; \
      apt-get clean; \
      rm -rf /var/lib/apt/lists/*; \
      sleep 5; \
    done; \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/deeptools /opt/deeptools

RUN set -eux; \
    deeptools --version | grep -Fx "deeptools 3.5.6" >/dev/null; \
    deeptools --help | grep -F "bamCoverage" >/dev/null; \
    bamCoverage --help 2>&1 | grep -F "usage: bamCoverage" >/dev/null; \
    computeMatrix --help 2>&1 | grep -F "usage: computeMatrix" >/dev/null; \
    plotHeatmap --help 2>&1 | grep -F "usage: plotHeatmap" >/dev/null; \
    python -c 'import deeptools, deeptoolsintervals, matplotlib, numpy, plotly, py2bit, pyBigWig, pysam, scipy'

RUN set -eux; \
    data=/opt/deeptools/share/testdata; \
    tmp=/tmp/taf-deeptools-runtime-check; \
    rm -rf "$tmp"; \
    mkdir -p "$tmp"; \
    cd "$tmp"; \
    bamCoverage -b "$data/sample1.bam" -o sample1.bw --binSize 10 --numberOfProcessors 1; \
    test -s sample1.bw; \
    multiBamSummary bins --bamfiles "$data/sample1.bam" "$data/sample2.bam" -out bam_summary.npz --binSize 100 --numberOfProcessors 1; \
    test -s bam_summary.npz; \
    computeMatrix scale-regions -S sample1.bw -R "$data/regions.bed" -o matrix.gz --regionBodyLength 100 --beforeRegionStartLength 0 --afterRegionStartLength 0 --numberOfProcessors 1; \
    test -s matrix.gz; \
    plotHeatmap -m matrix.gz -out heatmap.png; \
    test -s heatmap.png; \
    rm -rf "$tmp"

WORKDIR /root

ENV TAFFISH_ENV=TAFFISH
ENV TAFFISH_NAME=deeptools
