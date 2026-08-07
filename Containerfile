# cal2gancio – Multi-stage OCI Container Image
#
# Stage 0 (python-stripped): strips pip and setuptools from the Alpine Python image.
#   COPY --from reads the *merged* filesystem of the source stage, so whiteouts
#   are resolved before the copy — the bytes never land in any runtime layer.
# Stage 1 (builder):        installs Python dependencies into an isolated prefix
# Stage 2 (runtime):        Alpine base + Python from python-stripped + deps from builder;
#                            no pip, no setuptools, no CVE bytes anywhere in the image
#
# Build:  buildah build -t cal2gancio .

# ── Stage 0: strip pip and setuptools from Python ────────────────────────────
FROM docker.io/python:3.14.7-alpine3.24 AS python-stripped
RUN pip uninstall -y setuptools pip

# ── Stage 1: dependency installation ────────────────────────────────────────
FROM docker.io/python:3.14.7-slim AS builder

WORKDIR /install

COPY requirements.txt .

# Install into a self-contained prefix so we can copy it cleanly
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt --root-user-action=ignore

# ── Stage 2: minimal runtime image ──────────────────────────────────────────
FROM alpine:3.24

LABEL org.opencontainers.image.title="cal2gancio" \
      org.opencontainers.image.description="Sync iCal feeds to a Gancio instance" \
      org.opencontainers.image.source="https://github.com/Leaced/cal2gancio" \
      org.opencontainers.image.licenses="EUPL-1.2"

# System libraries Python 3.14.7 links against, plus CA certs and timezone data
RUN apk add --no-cache \
      ca-certificates \
      libffi \
      openssl \
      tzdata \
      libyaml \
      bzip2 \
      xz-libs \
      expat \
    && adduser -S -H -s /sbin/nologin -u 1312 cal2gancio

# Python runtime from python-stripped: merged FS has no pip and no setuptools —
# those bytes are absent from this COPY layer, not merely hidden by a whiteout.
COPY --from=python-stripped /usr/local /usr/local

WORKDIR /app

# App dependencies from builder (no pip, no setuptools in requirements.txt)
COPY --from=builder /install/deps /usr/local

# Copy application source
COPY cal2gancio/ ./cal2gancio/

# Config mount point with correct ownership
RUN mkdir -p /opt/cal2gancio \
      && chown cal2gancio /opt/cal2gancio

USER cal2gancio

# Mount: /opt/cal2gancio/config.yml + password_file path from config
VOLUME ["/opt/cal2gancio"]

ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "cal2gancio"]
