# Changelog

All notable changes to this project (a fork of
[maximeallanic/homeassistant-mcp](https://github.com/maximeallanic/homeassistant-mcp))
are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This fork starts fresh at **v1.0.0** — a significant divergence from upstream, not a
patch release. Changes relative to the upstream baseline are recorded under the
`[1.0.0]` heading below.

## [Unreleased]

### Added
- `CHANGELOG.md` following Keep a Changelog, tracking this fork's divergence from
  upstream.

### Changed
- `.gitignore` now excludes `CLAUDE.md` so machine/network-specific deployment
  context (VLAN topology, Home Assistant host IP) is never committed to the public
  fork.

## [1.0.0] — Fork baseline

Initial fork of `maximeallanic/homeassistant-mcp`. Subsequent fixes, security work,
and features are recorded under `[Unreleased]` until the next tagged release.
