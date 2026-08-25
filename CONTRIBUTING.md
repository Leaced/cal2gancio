<!--
SPDX-FileCopyrightText: 2026 cal2gancio contributors
SPDX-License-Identifier: EUPL-1.2
-->

# Contributing

## Branch model

| Branch    | Purpose |
| --------- | ------- |
| `main`    | Stable releases only. Never commit here directly. |
| `develop` | Integration branch. All contributions target this branch. |

`develop` is merged into `main` when a release is warranted. A release is only created when the accumulated changes justify a new version — not on every merge.

## How to contribute

1. Fork the repository.
2. Create a feature branch from `develop`.
3. Open a pull request **against `develop`**.

CI runs on every PR: REUSE licence compliance and a Trivy vulnerability scan of the built image.

## Commit messages

Every significant change requires a [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/) message.
`feat:` and `fix:` commits trigger a release; a `BREAKING CHANGE` footer or `!` suffix triggers a major release.

## REUSE compliance

Every new file must carry an SPDX licence header:

```python
# SPDX-FileCopyrightText: <year> <name>
# SPDX-License-Identifier: EUPL-1.2
```

Use the appropriate comment syntax for the file type. The CI will fail if the header is missing.
