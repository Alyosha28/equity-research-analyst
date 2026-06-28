# Analyst Playbook: how top-tier research operationalizes each lens

Distilled from a focused study of high-quality NVDA research. The goal is the
*reusable, company-agnostic technique* behind each style — not the (quickly stale)
numbers. Use this to enrich the four lenses in `valuation-lenses.md` with the
specific moves practitioners actually make.

> **Source-quality caveat.** NVDA is the most hype-saturated stock in the market;
> much online "research" is reverse-engineered narrative. Primary/named sources
> (Damodaran's blog, SemiAnalysis, Mauboussin/Rappaport, company guidance) are
> weighted highest; secondary aggregators are flagged. **All dollar figures are
> illustrative of method and date quickly — the durable asset is the structure.**

## Contents
1. Sell-side consensus (segment → EPS → multiple)
2. SemiAnalysis bottoms-up supply build (capacity ceiling → units × ASP)
3. Capex demand bridge (customer budgets → share-of-wallet)
4. Intrinsic DCF (Damodaran story → numbers) — the anchor
5. Reverse DCF / expectations investing (Mauboussin & Rappaport)
6. Bear / skeptic case (structured risk + leading indicators)
7. Quality-compounder / moat-durability (ROIC–WACC, CAP, RONIC fade)
8. Synthesis: comparison table, triangulation rules, company-agnostic checklist
9. Sources

---

## 1. Sell-side consensus — segment → EPS → target multiple
*(Morgan Stanley, Goldman Sachs; secondary reporting of paywalled notes.)*

**Method:** build revenue **by reported segment** (for NVDA, Data Center ≈ 90% dominates)
→ gross margin & opex → tax → **forward EPS** (CY26/27) → apply a **target multiple**.
The two banks expose the *two knobs* cleanly: Morgan Stanley = *low multiple × high
EPS* (~22× on an above-consensus Data Center build); Goldman = *high multiple ×
normalized EPS* (~30×, thesis in re-rating catalysts). MS also validates demand from
**NVDA's own balance sheet** (~$95B purchase commitments + ~$21B inventory ⇒ revenue
support) and a simple perpetuity sanity-check.

**Borrow:** (a) the **segment-build → EPS → multiple** scaffold; (b) **two-knob
discipline** — state your EPS estimate and your multiple *separately* so any target
decomposes; (c) the **balance-sheet cross-check** (purchase commitments / inventory /
backlog as an independent validator of the revenue story); (d) always output a
**bull/base/bear price triplet**, never a point. *Blind spot:* herds on
consensus/guidance; the whole answer pivots on one subjective multiple.

## 2. SemiAnalysis bottoms-up — capacity ceiling → units × ASP
*(SemiAnalysis / Dylan Patel; public previews give method + anchors, full model paywalled.)*

**Method:** (1) find the **binding supply constraint** — not the chip but the
bottleneck *around* it (CoWoS advanced packaging → HBM → datacenter power); solving
one exposes the next. (2) Convert the constraint into a **physical unit ceiling**
(e.g. CoWoS wafers/mo + HBM stacks → max buildable GPUs). (3) **Units × ASP →
revenue**, margin inferred from "selling bottlenecked productivity". (4) Decide the
regime: **supply-gated** (forecast supply) vs **demand-gated** (forecast utilization).
Yield is "the only metric that matters for profitability"; channel checks are
cross-referenced *against* management guidance, not trusting it.

**Borrow:** (a) a **supply/capacity ceiling cross-check** on any demand forecast —
"is this physically buildable?"; (b) **constraint-chain mapping** (find the binding
input, then the next); (c) **units × ASP** as an independent revenue path vs top-down
%-growth; (d) **primary-source channel checks**; (e) the **supply-gated vs
demand-gated** question *before* forecasting. *Blind spot:* supply ≠ sell-through
(can't see double-ordering); needs deep domain access.

## 3. Capex demand bridge — customer budgets → contestable pool → capture
*(CNBC, Tom's Hardware, CreditSights; company guidance + aggregators.)*

**Method:** sum **hyperscaler capex guidance** → apply **AI share %** → strip non-chip
items (real estate, **power**, cooling, networking) to get the **directly contestable
accelerator pool** → apply NVDA **capture rate** (+ networking recapture + sovereign/
enterprise add-on). The key sensitivity is **share-of-wallet compression** from custom
silicon and memory-cost inflation — which is why a stock can fall on *record* capex.

**Borrow:** the **customer-budget bridge** is the most transferable demand technique —
for any supplier, build revenue from *customers' disclosed spending* × your
contestable-pool share, and model **share-of-wallet compression** as the key
sensitivity. **Separate absolute-pool growth from your share of the marginal dollar**
— they can diverge. *Blind spot:* capex-as-proxy is breaking down; concentration risk.

## 4. Intrinsic DCF (Damodaran) — the anchor
*(Primary: Damodaran's blog (June 2023 NVDA), 2024-2026 data updates, The Corporate Life Cycle book (Aug 2024), 17th annual ERP study (March 2026).)*

The skill's spine; see `methodology-damodaran.md` and `input-estimation.md` for full
detail. Four drivers: revenue (**TAM × share**, ~$267B by 2033), R&D-adjusted **margin
~40%**, **sales-to-capital ~1.15**, **cost of capital 12.21% → 8.85%** → ~$240 (Jun
2023). Note how the *story* moved the number over time: ~$87 (Sep 2024) as share/margin
assumptions re-rated; ~$78 (Feb 2025) after DeepSeek "changed the story". Uncertainty
via **Monte Carlo** on all four drivers + a **breakeven grid**.

**Borrow:** TAM×share build; four-driver spine; **Monte Carlo over point estimates**;
**breakeven / "what has to be true"**; the **3P discipline** (possible / plausible /
**probable**); and the **aggregate-TAM "Big Market Delusion" cross-check** (below).
*Blind spot:* terminal value/CAP dominate; lags fast technical shifts.

## 5. Reverse DCF / expectations investing — the highest-leverage cross-check
*(Mauboussin & Rappaport, *Expectations Investing*; framework primary.)*

**Method:** take current EV and WACC as given; **solve for the cash flows the price
implies** (price-implied expectations). Express as **implied revenue growth, operating
margin, investment rate, and implied forecast period** (years of excess return the
price requires; market avg > 10). Then **test realism** vs history & peers. Edge =
**variant perception**: where your *well-founded* view differs from the implied bar.

**Borrow:** **always run a reverse DCF alongside the forward DCF** — "what does today's
price imply, and is that plausible?" Encode the **implied-forecast-period** and the
**variant-perception** statement (the one thing you must out-predict the market on) as
standard outputs. Engine: `reverse_dcf.py`. *Blind spot:* still needs a defensible
WACC/structure; sensitive to terminal assumptions.

## 6. Bear / skeptic case — structured risk + monitorable signals
*(CNBC, Tom's Hardware, Motley Fool; primary reporting + analyst blogs.)*

**Method:** enumerate the vectors that break the bull math, each with a mechanism and a
**leading indicator**: (1) **customer concentration** (DC ≈ 90% of revenue; the buyers
*are* the competitors); (2) **custom-ASIC substitution** (Google TPU, AWS Trainium,
Broadcom — often growing faster than GPU, esp. inference; *adoption %s from secondary
reporting, directional*); (3) **gross-margin sustainability** (~75% is the keystone —
**margin cracks before revenue does**, so GM is the leading indicator of share loss);
(4) **cyclicality / double-ordering / vendor-financing** (inventory + commitments +
circular demand); (5) **China / export-control** TAM caps. Disciplined bears note the
case "has repeatedly failed to play out" — counter-tells include rising GPU *rental*
prices and pie growth swamping per-customer defection.

**Borrow:** a **structured bear checklist** for any moat stock — concentration,
substitution (are customers the substituters?), **the one financial metric that cracks
first** (usually gross margin), cyclicality/channel-inventory/vendor-financing, and
regulatory/geographic caps — each paired with a **named leading indicator to monitor**.
*Blind spot:* chronically early; can mistake *share* erosion for *absolute* decline.

## 7. Quality-compounder / moat-durability — ROIC–WACC, CAP, RONIC fade
*(GuruFocus, moat analyses; framework = standard quality-investing canon.)*

**Method:** (1) establish the **ROIC–WACC spread** (confirms value creation exists);
(2) assess the **Competitive Advantage Period (CAP)** — how many years the spread
persists — by decomposing the moat into *named components* (CUDA network effects, full
software stack, TSMC relationship, installed-base switching costs); (3) model **RONIC
(return on *new* capital) fading** toward (but above) WACC over time; (4) tie FCF →
buybacks/reinvestment as the compounding engine.

**Borrow:** make **ROIC–WACC spread + explicit CAP + RONIC-fade** a required block of
any long-horizon valuation — it *is* what the terminal value rests on (the engine's
`terminal_roc` encodes a perpetual excess return; set it deliberately). Decompose the
moat into **independently-testable components**. *Blind spot:* CAP is unobservable and
easy to over-assume; current ROIC can be cyclically inflated.

---

## 8. Synthesis

### Comparison table

| Lens | Models | Anchor | Horizon | Strength | Blind spot |
|---|---|---|---|---|---|
| 1 Sell-side | segment → EPS → multiple | guidance, balance-sheet commitments | 1–3 yr | tied to near-term financials | herds; multiple subjective |
| 2 Supply build | capacity ceiling → units×ASP | CoWoS/HBM/power, yield | 0–2 yr | catches physical ceilings early | supply ≠ sell-through |
| 3 Capex bridge | customer capex → capture | hyperscaler capex, ASP | 1–2 yr | grounds revenue in real budgets | proxy breaking down; concentration |
| 4 Intrinsic DCF | TAM×share, margin, reinvest, risk | TAM, margins, WACC | 10 yr + terminal | explicit, simulated odds | terminal/CAP dominate |
| 5 Reverse DCF | price → implied expectations | EV, WACC | implied (>10 yr) | quantifies "priced for perfection" | terminal-sensitive |
| 6 Bear | risk vectors + signals | concentration, GM, inventory | 1–5 yr | falsification; monitorable | chronically early |
| 7 Compounder | ROIC–WACC, CAP, RONIC fade | ROIC, WACC, moat parts | 10 yr+ | addresses durability | CAP unobservable |

### Triangulation rules
1. **Forward DCF (4) vs Reverse DCF (5)** is the master cross-check: if value << price,
   lens 5 names the *specific* implied assumption you'd have to beat.
2. **Demand bridge (3) vs Supply build (2):** forecast the *minimum* of buildable-supply
   and fundable-demand; the divergence reveals the binding regime and the opportunity.
3. **Sell-side EPS (1)** is the near-term bridge, but discipline it: if consensus
   revenue exceeds what customers' capex can fund (3) *or* what the chain can build (2),
   consensus is too high regardless of the multiple debate.
4. **Compounder/CAP (7) anchors the terminal value** that lenses 4/5 are most sensitive
   to; the **bear case (6) is the input that shortens CAP** — resolve 6 and 7 together.
5. **Where the lenses agree vs disagree is the signal.** For NVDA, bottoms-up (1,2,3)
   agree on huge *near-term* revenue; intrinsic/reverse/bear/compounder (4,5,6,7) locate
   the dispute in *durability — terminal margin & share*. "Everyone agrees on year 1; the
   fight is about years 5–10" means the stock is a **bet on CAP length and terminal
   margin** — so concentrate diligence there and widen Monte Carlo variance there.

### Company-agnostic checklist (run in roughly this order)
1. **Story first, then numbers** → force into 4 drivers (growth, margin, reinvestment, risk).
2. **Build revenue two independent ways and reconcile:** *top-down* TAM × share (TAM =
   customer-capex bridge where customers are concentrated; watch share-of-wallet) and
   *bottom-up* units × ASP **capped by a supply/capacity ceiling**. Take the binding one;
   the gap is information.
3. **Forward DCF with Monte Carlo**, not a point — report the value *distribution* and
   where price sits in it. (`dcf_valuation.py`, `monte_carlo.py`)
4. **Reverse DCF always** — implied growth/margin/**forecast period**; test vs history &
   peers; state the **variant perception**. (`reverse_dcf.py`)
5. **Durability block** — ROIC–WACC spread, explicit **CAP**, **RONIC fade**; decompose
   the moat into named, testable parts. This underwrites terminal value.
6. **Structured bear checklist with leading indicators** — concentration, substitution,
   the metric that cracks first (usually gross margin), cyclicality/inventory/financing,
   regulatory & geographic caps.
7. **Multiple discipline** — if using a target multiple, keep it separate from the EPS
   estimate and justify it against the durability block (CAP), not by analogy.
8. **Aggregate "Big Market Delusion" check** — sum the implied breakeven revenues/share
   of *all* credible players in the TAM; if the total exceeds a plausible market, the
   individual stories are collectively delusional.
9. **3P gate** (possible / plausible / **probable**) + a plain-language **"what has to be
   true"** breakeven statement with the odds. (`breakeven.py`)
10. **Triangulation output** — state where lenses agree vs disagree; the dispute locus
    (near-term vs terminal) defines where the real bet, and the diligence, should concentrate.

---

## 9. Sources
Primary / named (weighted highest): Damodaran *Musings on Markets* (Jun 2023 NVDA
valuation + 2024–25 updates); SemiAnalysis newsletters (CoWoS/HBM constraints,
silicon shortage, Blackwell rework); Mauboussin & Rappaport, *Expectations
Investing* (Columbia UP) + expectationsinvesting.com; NVDA company guidance.
Secondary (directional, flagged): TheStreet (MS/GS note summaries); CNBC & Tom's
Hardware (custom-ASIC, hyperscaler capex); Motley Fool / Daloopa (concentration);
GuruFocus (ROIC, gross margin); Chipstrat (AMD vs CUDA moat); antoinebuteau.com
("Lessons from Dylan Patel" — *AI-paraphrase caution, method-framing only*).

**Reliability flags:** sell-side figures and bear-case adoption %s are secondary
reporting of primary notes — directionally sound, exact numbers unverified.
SemiAnalysis's full unit→revenue arithmetic is paywalled (public previews give method
+ anchors). All dollar figures illustrate method and will date quickly.
