# Swiss Website Design Skill

An Agent Skill for Codex and Claude Code that designs, builds, revises, and audits polished React/Vite websites through Josef Müller-Brockmann’s Swiss International Typographic Style.

The skill treats the grid as a governing communication system. It requires explicit columns, gutters, margins, baseline rhythm, component spans, and responsive transformations rather than applying a superficial minimalist aesthetic.

## What it enforces

- React with Vite for new website projects
- mathematically defined desktop, tablet, and mobile grids
- semantic typography roles and restrained sans-serif hierarchy
- asymmetric, content-led composition with functional color and imagery
- subtle fade-in reveals during normal scrolling
- progressive enhancement and `prefers-reduced-motion` support
- first-class mobile layouts tested from 320 CSS px upward
- distinct tablet compositions tested at representative iPad-class widths
- accessible touch, keyboard, chart, map, and navigation behavior
- maintainable tokens and consolidated responsive CSS
- licensed fonts, documented assets, and production-path verification
- successful builds and live deployment checks when publishing is in scope

## Install

Clone the repository and run the setup script:

```bash
git clone git@github.com:p3jitnath/website-design-skill.git
cd website-design-skill
./setup.sh
```

The installer copies the skill to:

```text
${CODEX_HOME:-$HOME/.codex}/skills/swiss-website-design
```

Codex is the default harness. To install for Claude Code instead, run:

```bash
./setup.sh --harness claude
```

The Claude installation uses `${CLAUDE_HOME:-$HOME/.claude}/skills/swiss-website-design`. Restart the selected harness if the skill does not appear in the current session.

## Use

Open the selected harness in a website project and invoke `$swiss-website-design` in Codex or `/swiss-website-design` in Claude Code.

```text
$swiss-website-design
/swiss-website-design
```

Example request:

```text
Use $swiss-website-design to build a responsive editorial website in React and Vite. Define and document the grid before implementation, use subtle fade-in reveals, and verify every route across the required mobile viewport matrix.
/swiss-website-design build a responsive editorial website in React and Vite. Define and document the grid before implementation, use subtle fade-in reveals, and verify every route across the required mobile viewport matrix.
```

## Structure

```text
website-design-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── data-visualization.md
│   ├── production-identity.md
│   ├── react-vite-implementation.md
│   ├── review-checklist.md
│   └── swiss-design-system.md
└── setup.sh
```

`SKILL.md` contains the core requirements and workflow. The references provide focused guidance for the Swiss design system, React/Vite implementation, mobile acceptance, charts and cartography, fonts and social previews, deployment, and final review.

## Validate changes

Run the Codex skill validator when available:

```bash
python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" .
bash -n setup.sh
```

Then install into a temporary or local Codex home and confirm that the installed files match the repository source.

## Design basis

The guidance is grounded in descriptions and collections from the Swiss National Library, Museum für Gestaltung Zürich, the Swiss Federal Department of Foreign Affairs, and Cooper Hewitt. Research links are maintained in `references/swiss-design-system.md`.
