# Roadmap

Ideas raised in the 1.0 design review that were deliberately left for later (see `docs/design/reviews/consolidated_review_report.md`).

- **Ingest model for readers:** reader subagents only write input files; one `tracker.py ingest` call processes them all under the lock.
- **External-edit audit:** record in the event log when a CSV was changed outside the tools.
- **Repeated eval runs as a release gate:** each injection and consent scenario run five times per supported agent, with pass rates published.
- **Per-agent tool allow-lists** in subagent frontmatter, once every supported agent accepts the same format.
- **Codex:** an end-to-end tested install.
