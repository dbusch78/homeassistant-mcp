# Contributing

Thanks for your interest in contributing to this fork of
[maximeallanic/homeassistant-mcp](https://github.com/maximeallanic/homeassistant-mcp).

## Development setup

```bash
git clone https://github.com/dbusch78/homeassistant-mcp.git
cd homeassistant-mcp
./setup.sh                     # creates venv/ and installs requirements.txt
cp .env.example .env           # then add your HA_URL and HA_TOKEN
```

Always work inside the `venv/` virtual environment — never system Python. The
code is fully async; do not introduce blocking I/O.

## Branching strategy

- `main` — stable, production-ready. Never commit directly.
- `develop` — integration branch; all work merges here first.
- `feature/*`, `fix/*`, `security/*`, `docs/*` — topic branches.

Always branch from `develop`, and open your PR against `develop`. A `develop → main`
merge represents a tagged release.

## Commit standards

Use [Conventional Commits](https://www.conventionalcommits.org/), one logical
change per commit:

```
feat: add streamable HTTP transport
fix: remove duplicate restart_homeassistant tool
security: enforce per-call rate limiting
docs: document the HTTP transport
test: cover call_service input validation
chore: pin dependency versions
```

Keep commits atomic, present-tense, lowercase, no trailing period. Explain **why**,
not just what. Separate a longer body with a blank line.

## Pull requests

Every PR to `develop` must describe what changed and why, how to test it, and any
breaking changes. **Both** of these must be updated in the same PR:

- **CHANGELOG.md** — add an entry under `[Unreleased]` (newest first).
- **README.md** — keep it current. A change to available tools, transports/config,
  the security model, environment variables, or setup steps is not complete until
  the README reflects it. CHANGELOG records history; README reflects present state.

## Adding a new tool

1. Declare it in `handle_list_tools()` with a JSON input schema.
2. Implement it in `handle_call_tool()`.
3. Add **type hints** and a **docstring** stating what it does, its parameters,
   and its return value.
4. If it takes a service-call / path-interpolating argument, add it to the input
   validation spec so its identifiers are path-checked before reaching HA.
5. Add a test under `tests/`.

Do not add tools that allow arbitrary code execution on the Home Assistant host,
add cloud-dependent fallbacks, or weaken existing security controls.

## Testing

Tests are plain scripts runnable without a live Home Assistant where possible:

```bash
python tests/test_security.py
python tests/test_http_transport.py
# ...run the relevant suites before marking a branch ready
```

## Versioning

[Semantic Versioning](https://semver.org/): MAJOR for breaking tool-API/transport
changes, MINOR for new tools/features/transports, PATCH for fixes and security
patches. Flag any MAJOR-bumping change before implementing it.

## Security

Never log token values or PII. Report vulnerabilities privately — see
[SECURITY.md](SECURITY.md).

## Local Claude Code setup (optional)

If you use Claude Code with this repo, copy `CLAUDE.example.md` to `CLAUDE.md` and
fill in your local deployment details. `CLAUDE.md` is gitignored and never
committed — it holds your personal infrastructure context for Claude Code sessions.
