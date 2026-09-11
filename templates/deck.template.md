---
marp: true
theme: factory
paginate: true
footer: "agent-factory · {{DATE}}"
---

<!-- _class: title -->
<!-- _paginate: false -->

# {{TITLE}}

{{ONE-LINE PITCH}}

{{DATE}} · github.com/mlodian/agent-factory

<!--
Open with the question, not the tech. One sentence on why you picked it.
-->

---

## The problem

{{The real question someone actually has — one or two lines.}}

<!--
Make it concrete. Who asks this, and what do they do today without an answer?
-->

---

## Why it matters

- {{who is affected}}
- {{what it costs them}}
- {{why existing answers fall short}}

<!-- Keep to three bullets. The notes carry the detail. -->

---

## Architecture

![w:1000](architecture.svg)

<!--
architecture.svg is rendered by the workflow from deck/architecture.mmd.
Walk left to right: source → processing → output. Five or six boxes, no more.
-->

---

## How it works

{{The one genuinely interesting technical decision, and why.}}

<!-- One decision, explained well, beats a tour of every file. -->

---

<!-- _class: demo -->

## Demo

```bash
{{the exact command from DEMO.md}}
```

<!--
Switch to the terminal. Follow DEMO.md timings.
Point at: {{the one number to watch for}}.
-->

---

## Results

| Measure | Value |
|---|---|
| {{metric from VERIFY.md}} | {{value from VERIFY.md}} |
| {{metric from VERIFY.md}} | {{value from VERIFY.md}} |

<!--
Every number on this slide appears in VERIFY.md. Nothing estimated.
Say what the number means, then what it does NOT mean.
-->

---

## Limitations

- {{specific limitation}}
- {{specific limitation}}
- {{specific limitation}}

<!-- Own this slide. It's the one that makes the audience trust the rest. -->

---

## What's next

{{The honest next step — one or two items, not a roadmap.}}

<!-- What would you actually do with one more day on this? -->

---

<!-- _class: title -->

## Links & data

**Code:** github.com/mlodian/agent-factory/tree/main/projects/{{SLUG}}

**Data:** {{source name}} — {{licence}}
{{attribution line, required by the licence}}

<!-- Thank the audience. Invite the question you're best prepared for. -->
