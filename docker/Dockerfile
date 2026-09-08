ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
FROM ${PYTHON_IMAGE} AS builder
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=120 PYTHONDONTWRITEBYTECODE=1
RUN apt-get -o Acquire::Retries=3 update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates libbz2-dev libcurl4-openssl-dev liblzma-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.lock docker/build-requirements.lock /tmp/locks/
RUN python -m venv /opt/deeptools && \
    /opt/deeptools/bin/pip install --require-hashes -r /tmp/locks/build-requirements.lock && \
    /opt/deeptools/bin/pip install --require-hashes --no-build-isolation --only-binary=deeptools \
      -r /tmp/locks/requirements.lock && /opt/deeptools/bin/pip check && \
    mkdir -p /opt/deeptools/share/doc/deeptools && \
    /opt/deeptools/bin/pip freeze --all > /opt/deeptools/share/doc/deeptools/requirements.freeze.txt
COPY docker/make_testdata.py /tmp/make_testdata.py
RUN /opt/deeptools/bin/python /tmp/make_testdata.py && \
    find /opt/deeptools -type d -name __pycache__ -prune -exec rm -rf {} + && \
    find /opt/deeptools/lib/python3.12/site-packages/numpy /opt/deeptools/lib/python3.12/site-packages/scipy \
      -type d -name tests -prune -exec rm -rf {} + && \
    rm -rf /opt/deeptools/include

FROM ${PYTHON_IMAGE}
ENV DEBIAN_FRONTEND=noninteractive PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
    PATH=/opt/deeptools/bin:$PATH TAFFISH_ENV=TAFFISH TAFFISH_NAME=deeptools
RUN apt-get -o Acquire::Retries=3 update && apt-get install -y --no-install-recommends \
    bash ca-certificates curl fontconfig fonts-dejavu-core libbz2-1.0 libcurl4 \
    libgomp1 liblzma5 libstdc++6 zlib1g && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /deeptools-resource /resource-install /work
COPY --from=builder /opt/deeptools /opt/deeptools
COPY docker/requirements.lock docker/build-requirements.lock docker/dependency-artifacts.json /opt/deeptools/share/doc/deeptools/
COPY docker/upstream-notices/ /opt/deeptools/share/doc/deeptools/upstream/
COPY docker/gc-testdata/ /opt/deeptools/share/testdata/gc/
COPY --chmod=755 docker/deeptools-smoke.py /usr/local/bin/deeptools-smoke
COPY --chmod=755 docker/deeptools-resources.py /usr/local/bin/deeptools-resources
# 构建期只用稳定 identity 和 tiny BAM→BigWig；完整绘图与旧/新命令在运行期离线测试。
RUN deeptools-smoke buildtime
WORKDIR /work
CMD ["deeptools"]
