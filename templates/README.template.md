# {{Title}}

{{One-line description.}}

{{One paragraph: why this question is interesting, and to whom.}}

> **Status:** {{PASSED / FAILED — from VERIFY.md. If FAILED, state the error here.}}
> **Deck:** [slides](https://mlodian.github.io/agent-factory/projects/{{SLUG}}/deck/dist/deck.html) · [PDF](https://github.com/mlodian/agent-factory/releases/download/deck-{{SLUG}}/deck.pdf) · [PPTX](https://github.com/mlodian/agent-factory/releases/download/deck-{{SLUG}}/deck.pptx) · **Demo script:** [DEMO.md](DEMO.md)

## Quickstart

```bash
{{commands copied verbatim from verify.sh}}
```

## What it found

{{The results. Every number here appears in VERIFY.md — no exceptions.}}

## Data

| | |
|---|---|
| Source | [{{name}}]({{url}}) |
| Licence | {{licence}} |
| Records | {{n}} |
| Retrieved | {{date}} |
| Re-fetch | `python3 data/fetch_data.py` |

{{Attribution line, if the licence requires one.}}
Full provenance, including the SHA256 checksum, is in [data/SOURCE.md](data/SOURCE.md).

## How it works

{{Three or four sentences.}} See [ARCHITECTURE.md](ARCHITECTURE.md) for the design.

## Limitations

- {{Specific. "Could be improved" doesn't count.}}
- {{…}}

---

*Built by [agent-factory](../../README.md) on {{date}}. Reviewed by a human before merge.*
