# Sources

Create one directory per source:

```text
sources/<YYYY-MM-DD>-<slug>-<short-id>/
├── original.<ext>
└── source.md
```

`original.<ext>` preserves the captured bytes when licensing and policy permit
storage. `source.md` records provenance, a SHA-256 hash, evidence limits, and a
summary. For URL-only captures, omit the original and state
`capture_kind: link_and_summary`.

Do not edit an approved original. Add a new source version when the upstream
artifact changes.
