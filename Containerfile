# cal2gancio – Multi-stage OCI Container Image
#
# Stage 1 (builder): installs Python dependencies into an isolated prefix
# Stage 2 (runtime): copies only the installed packages, no pip, no cache
#
# Build:  buildah build -t cal2gancio .

# ── Stage 1: dependency installation ────────────────────────────────────────
FROM docker.io/python:3.14.6-slim AS builder

WORKDIR /install

COPY requirements.txt .

# Install into a self-contained prefix so we can copy it cleanly
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt --root-user-action=ignore


# ── Stage 2: minimal runtime image ──────────────────────────────────────────
FROM docker.io/python:3.14.6-alpine3.24

LABEL org.opencontainers.image.title="cal2gancio" \
      org.opencontainers.image.description="Sync iCal feeds to a Gancio instance" \
      org.opencontainers.image.source="https://github.com/Leaced/cal2gancio" \
      org.opencontainers.image.licenses="EUPL-1.2"

# Non-root user
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

CMD ["python3", "-m", "cal2gancio"]
