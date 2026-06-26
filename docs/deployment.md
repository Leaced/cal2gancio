# Deployment

## Container image

Images are published to the GitHub Container Registry for amd64 and arm64:

```bash
podman pull ghcr.io/leaced/cal2gancio:latest
```

### Verifying image signatures

All images pushed to `main` are signed with [Cosign](https://github.com/sigstore/cosign) using keyless signing via GitHub Actions OIDC. No key management is required to verify.

```bash
cosign verify \
  --certificate-identity-regexp "https://github.com/Leaced/cal2gancio/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/leaced/cal2gancio:latest
```

The signature is recorded in the [Sigstore transparency log](https://rekor.sigstore.dev) and can be inspected independently of GitHub.

## Password setup

The password is read from a file whose path is set by `password_file` in `config.yml`.

**Recommended: podman secret**

```bash
echo -n "your-gancio-password" | podman secret create gancio_password -
```

This mounts the secret at `/run/secrets/gancio_password` inside the container — the default path.

**Alternative: plain file**

```bash
echo -n "your-gancio-password" > /etc/cal2gancio/password
chmod 600 /etc/cal2gancio/password
```

Set `password_file: /run/secrets/gancio_password` in `config.yml` and mount the file at the same path.

## Quick run

With a podman secret:

```bash
podman run --rm \
  -v /opt/cal2gancio:/opt/cal2gancio:ro,Z \
  --secret gancio_password \
  ghcr.io/leaced/cal2gancio:latest
```

With a password file mounted directly:

```bash
podman run --rm \
  -v /opt/cal2gancio:/opt/cal2gancio:ro,Z \
  -v /etc/cal2gancio/password:/run/secrets/gancio_password:ro,Z \
  ghcr.io/leaced/cal2gancio:latest
```

## Running on a schedule (systemd + Quadlet)

[Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html) lets systemd manage the container declaratively.

```ini
# /etc/containers/systemd/cal2gancio.container
[Unit]
Description=cal2gancio iCal → Gancio sync

[Container]
Image=ghcr.io/leaced/cal2gancio:latest
Volume=/opt/cal2gancio:/opt/cal2gancio:ro,Z
Secret=gancio_password

[Service]
Type=oneshot
```

```ini
# /etc/systemd/system/cal2gancio.timer
[Unit]
Description=cal2gancio sync timer

[Timer]
OnCalendar=*:0/30
Persistent=true
Unit=cal2gancio.service

[Install]
WantedBy=timers.target
```

```bash
systemctl daemon-reload        # triggers the Quadlet generator
systemctl enable --now cal2gancio.timer
```
