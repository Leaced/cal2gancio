# cal2gancio – Multi-stage OCI Container Image
#
# Stage 0 (python-stripped): strips pip and setuptools via uninstall.
#   COPY --from reads the *merged* filesystem of the source stage, so whiteouts
#   are resolved before the copy — the bytes never land in any runtime layer.
# Stage 1 (builder):         installs Python dependencies into an isolated prefix
# Stage 2 (runtime):         FROM scratch + full rootfs from python-stripped;
#                             no pip, no setuptools, no CVE bytes in any layer,
#                             no apk packages to maintain independently
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
FROM scratch

LABEL org.opencontainers.image.title="cal2gancio" \
      org.opencontainers.image.description="Sync iCal feeds to a Gancio instance" \
      org.opencontainers.image.source="https://github.com/Leaced/cal2gancio" \
      org.opencontainers.image.licenses="EUPL-1.2"

# Copy the full Alpine rootfs from python-stripped.
# FROM scratch contributes no layers; this COPY layer reflects the merged
# filesystem — system libraries, Python runtime, everything python-stripped
# ships — minus pip and setuptools (resolved out by the whiteouts above).
COPY --from=python-stripped / /

# Non-root user (BusyBox sh is available after the COPY above)
RUN adduser -S -H -s /sbin/nologin -u 1312 cal2gancio

WORKDIR /app

# Copy pre-built dependencies from builder stage (no pip in final image)
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
