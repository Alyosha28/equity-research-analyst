---
name: equity-research-analyst/research
description: >
  Shared research agent 鈥?the single point for all web research, data gathering,
  and fact-checking in the equity-research-analyst pipeline. Invoked by any sub-skill
  that needs sourced, dated information. Centralizes research methodology so analysis
  sub-skills focus on analysis, not data hunting.
license: MIT
---

# Research Agent (Shared Utility)

**Pipeline position:** Shared 鈥?invoked by any sub-skill that needs external data.
Centralizes all web research so analysis sub-skills stay focused on analysis.

## Why a dedicated research agent

Without this, every analysis sub-skill duplicates research instructions ("use
web search," "cite sources," "date every fact"). That leads to inconsistent
sourcing quality and makes it hard to upgrade research methodology.

This agent is the **single point** for:
- Web searching and fact-gathering
- Source annotation and tiering
- Data recency verification
- Cross-referencing claims against primary sources

## Input

The calling sub-skill provides a **research brief**:

```json
{
  "topic": "What to research (specific, not vague)",
  "depth": "quick" | "standard" | "deep",
  "time_range": "last 2 quarters" | "last 5 years" | "10+ years",
  "required_data_points": ["list", "of", "specific", "numbers", "needed"],
  "sources_preferred": ["filings", "industry reports", "news"],
  "calling_skill": "analyze-industry"
}
```

## Research modes

| Depth | When to use | Tools | Expected output |
|-------|------------|-------|----------------|
| **quick** | Single fact check, current price, latest quarter revenue | web search 脳 1-2 | 1-2 sourced data points |
| **standard** | Sub-skill research (industry data, company history, TAM) | web search 脳 3-5 + web fetch 脳 1-2 | Multiple sourced data points with cross-references |
| **deep** | Material facts for valuation drivers, contested claims | deep research workflow if available + web search verification | Comprehensive, multi-source, cross-verified |

## Research workflow

### 1. Parse the brief
- What exactly is being asked? (Not "NVIDIA" but "NVIDIA's Data Center segment revenue Q1 FY2025")
- What depth is required?
- What's the acceptable data vintage?

### 2. Execute the search

**Standard path (most sub-skill research):**
```
web search 脳 2-3 (different angles)
    鈫?
Identify primary sources (filings, earnings calls, industry reports)
    鈫?
web fetch primary sources for exact numbers
    鈫?
Cross-reference: do two independent sources agree on the key numbers?
    鈫?
If numbers diverge >10%: flag the divergence, use the more reliable source
```

**Deep path (valuation-critical facts):**
```
Invoke deep research workflow if available with the specific question
    鈫?
Extract the key data points + source list
    鈫?
web search to independently verify the 2-3 most critical numbers
    鈫?
Flag any deep research claims that can't be independently confirmed
```

### 3. Annotate every finding

Every data point returned MUST carry:
```json
{
  "value": 26914,
  "unit": "$ millions",
  "source": "NVIDIA 10-K FY2024",
  "source_url": "https://...",
  "tier": "audited",
  "as_of_date": "2024-01-28",
  "cross_referenced": true,
  "cross_reference_source": "Bloomberg terminal"
}
```

**Source tiers (mandatory 鈥?same as the main skill's data confidence system):**
- `audited` 鈥?From company filings (10-K, 20-F, annual report)
- `management-guidance` 鈥?Company's forward guidance (earnings call, investor day)
- `sell-side-consensus` 鈥?Consensus estimates (Visible Alpha, Bloomberg consensus)
- `third-party-aggregator` 鈥?yfinance, Wind, Capital IQ, Statista
- `industry-report` 鈥?Gartner, IDC, McKinsey, SemiAnalysis, etc.
- `news-reporting` 鈥?Reuters, Bloomberg, CNBC, Caixin, etc.
- `own-estimate` 鈥?Your inference/judgment (explicitly labeled)

### 4. Flag what's NOT found

Research that finds nothing useful is still useful 鈥?it tells the analyst the
data gap exists. Always report:
- What was searched for but NOT found
- What data exists but is stale (beyond acceptable vintage)
- What data is behind paywalls (exists but inaccessible)

## Output format

```markdown
## Research: [topic]
**Depth:** standard | **Date of search:** [today]

### Findings
| # | Data point | Value | Unit | Source | Tier | As-of date | Cross-ref |
|---|-----------|-------|------|--------|------|-----------|-----------|
| 1 | ... | ... | ... | ... | ... | ... | ... |

### Key narrative
[2-3 sentences synthesizing what the data says, with sources woven in]

### Data gaps
- [What was searched for but not found]
- [What exists but is stale]

### Source reliability note
[If any source has a reliability concern (biased, secondary reporting, paywalled preview), state it]

### For the calling sub-skill
[Specific implications: which numbers are solid enough for the valuation, which need
further confirmation, what low/base/high range is supported by the data]
```

## Which sub-skills invoke this

| Calling sub-skill | Typical research brief | Depth |
|-------------------|----------------------|-------|
| `/analyze-industry` | "Industry aggregate revenue 2015-2025, top-5 market shares each 5 years, historical EV/Revenue multiples" | deep |
| `/analyze-company` | "Company 10-year financials, historical stock price drawdowns, segment revenue breakdown, SBC dilution" | deep |
| `/analyze-theme` | "TAM estimates for [segment], competitor revenue and market share, hyperscaler capex guidance" | deep |
| `/build-assumptions` | "Current riskfree rate, industry beta, sector average cost of capital, peer margins" | standard |
| `/run-valuation` | "Current stock price, shares outstanding (latest filing), peer multiples for comps" | quick |
| `/refresh-valuation` | "Last 2 quarters: earnings, guidance changes, competitor moves, analyst revisions" | standard |
| `/critique-report` | "Verify key claims in the report being audited: are the TAM numbers real? Is the margin target plausible?" | standard |
| `/fetch-data` | "Company financials skeleton" | standard |

## Adversarial Review Gate

### Review criteria
- [ ] **Every data point annotated:** value, unit, source, tier, as-of date.
  Missing annotation 鈫?REVISE.
- [ ] **Cross-referencing attempted:** At least 2 independent sources for
  valuation-critical numbers (>5% of intrinsic value sensitivity). Single-source
  critical data 鈫?REVISE (flag as single-source risk).
- [ ] **Recency:** Data is within the acceptable vintage for the brief.
  Stale data 鈫?flag prominently, do not silently use.
- [ ] **Tier accuracy:** `audited` only for actual filing data. Aggregator data
  tagged as `audited` 鈫?REVISE.
- [ ] **Data gaps reported:** What was searched for but not found is stated.
  Silent omission 鈫?REVISE.
- [ ] **Source reliability:** Paywalled, biased, or secondary sources flagged.

### Common failure modes
- Numbers without sources (most common 鈥?"the AI market is $500B")
- Aggregator data passed off as audited
- Stale data used without flagging
- Single-source critical numbers without cross-reference
- Search too narrow (one angle, missing the obvious counter-source)

### Verdict thresholds
- **PASS:** All data annotated, cross-referenced for critical numbers, gaps reported.
- **REVISE:** Missing annotations, stale data, no cross-reference on critical data.
- **BLOCK:** Fabricated sources, completely wrong data, or search so shallow it
  missed publicly available filings.

## Self-check (run before submitting to review)
- [ ] Every data point has source + tier + date
- [ ] Critical numbers (>5% value sensitivity) cross-referenced with 2+ sources
- [ ] Data recency is within acceptable vintage
- [ ] Data gaps explicitly reported
- [ ] Source reliability concerns flagged
- [ ] Output explicitly states implications for the calling sub-skill
