# Archetype playbook — Financials (banks, insurers, lenders)

How to value a business whose **balance sheet is the product**. The FCFF engine is
not just imprecise here — it is *wrong* — so this archetype has its own engine,
`scripts/financial_valuation.py`. Embeds the one school that genuinely owns this
ground: **Buffett/Graham on banks and insurance float**.

> Uniform skeleton (shared by every archetype playbook): identify → why the default
> frame breaks → the right drivers → engine mapping → input-estimation deltas → bear
> checklist → master lens → self-check → traps. Method-first; numbers date, structure doesn't.

## 1. Identify (and the mis-classification trap)
Use this archetype when **regulatory capital is the binding constraint and the
balance sheet generates the earnings**: deposit banks, insurers (P&C, life,
reinsurance), specialty lenders, BDCs, mortgage REITs, broker-dealers running a book.

**The trap that wrecks valuations:** not everything in the "financial sector" is a
balance-sheet business. An **exchange, a card network, a rating agency, an asset
manager, a pure-fee fintech** earns operating margins on services and is valued with
the *normal* FCFF engine — capital-light, high-ROIC operating companies. Test:
*does the firm earn primarily a spread/underwriting result on its own balance sheet
(→ this playbook), or a fee/take-rate on others' money/flow (→ default FCFF)?* Visa
is not a bank; a regional lender is.

## 2. Why the default four-driver FCFF frame breaks
- **There is no "revenue × operating margin."** A bank's "revenue" (net interest +
  fee income) and its costs (funding, credit losses) do not separate into the
  EBIT-margin the engine assumes.
- **Debt is raw material, not financing.** Deposits/policy reserves *are* the
  product. You cannot net them out to an enterprise value; EV/EBITDA, EV/Sales and
  "sales-to-capital reinvestment" are meaningless.
- **Reinvestment runs through regulatory capital**, not `Δrevenue / sales_to_capital`.
  Growth consumes CET1 / risk-weighted assets, and the regulator sets the floor.

So value the **equity directly**: residual income (excess return on equity) as the
spine, with a Dividend Discount Model as the consistency check.

## 3. The right drivers
| Driver | What it is | Decomposes into |
|---|---|---|
| **ROE (through-cycle)** | the engine of value | NIM × leverage + fee income − efficiency ratio − **normalized credit cost** |
| **Cost of equity (Ke)** | the hurdle | riskfree + β·ERP; banks carry higher β and tail risk |
| **ROE − Ke spread** | *the whole story* | a bank that only earns Ke is worth book; the premium is PV(spread) |
| **CAP (advantage period)** | how long the spread lasts | deposit franchise, switching costs, underwriting discipline |
| **Book-value growth** | compounding base | retention = ROE × (1 − payout); capped by capital rules |
| **Payout** | dividends + buybacks | the rest of earnings; high when growth is scarce |
| **Regulatory capital (CET1)** | the binding constraint | headroom over the requirement gates growth *and* payout |

The value above book is **PV of the ROE−Ke spread over the CAP** — make that sentence
the thesis, not a P/E.

## 4. Engine mapping → `financial_valuation.py`
Residual income: `EquityValue = BV0 + Σ PV((ROE_t − Ke_t)·BV_{t-1}) + PV(terminal RI)`,
with clean-surplus book growth `BV_t = BV_{t-1} + NI_t·(1 − payout)`. The script also
prints a **two-stage DDM cross-check on the same path** — under clean surplus the two
must agree, so a gap is an input/coding error, not a view.

```bash
cd scripts
python financial_valuation.py ../templates/financials.example.json          # value/share, implied P/B, terminal share
python financial_valuation.py ../templates/financials.example.json --json    # for charts.py / programmatic use
```
Key inputs (see `templates/financials.example.json`): `book_value_equity` (use
**tangible** common equity), `base_roe`/`target_roe` (**through-cycle**, not peak),
`payout_ratio`, `cost_of_equity_*` glide, `terminal_roe` vs `cost_of_equity_terminal`
(the perpetual spread), and an optional `failure_probability` for crisis impairment.
Worked anchor: the illustrative large-bank inputs reproduce **≈ $231/share
going-concern, implied P/B ≈ 1.88×** at a 15% normalized ROE over a ~9–10% Ke.

## 5. Input-estimation deltas (the accounting that matters)
- **Normalize ROE across the credit cycle.** The single biggest error is valuing a
  bank on a benign-year ROE. Use a through-the-cycle credit cost (average provisions
  across a full cycle, not the current trough). Peak-cycle ROE × a high multiple is
  how banks get bought at the top.
- **Tangible book, not stated book.** Strip goodwill and intangibles from
  acquisitive banks; a premium to *stated* book can be a discount to *tangible* book.
- **Reserve adequacy.** Are loan-loss reserves keeping pace with the book, or is the
  bank releasing reserves to flatter EPS? (See the incentive flag below.)
- **Insurers — value the float.** Underwriting at a combined ratio < 100 means you
  are **paid to hold** policyholders' money: negative-cost leverage. Treat float as
  low-cost funding and the **underwriting result as the cost of that float**; value
  the investment income earned on it. Embedded value for life insurers.
- **AOCI / mark-to-market.** Held-to-maturity bond losses (the 2023 regional-bank
  break) sit outside stated capital — pull them into a stressed tangible book.

## 6. Bear checklist + leading indicators (Munger: invert; watch incentives)
Each vector paired with the metric that **cracks first**:
1. **Credit cycle turn** → NPL formation rate & coverage ratio (leads the loss).
2. **Funding / deposit flight** → deposit beta and the cost of funding; *for a bank,
   funding is what breaks before the loan book does* — it is the gross-margin
   equivalent here.
3. **NIM compression** → the rate cycle and asset/liability repricing gap.
4. **Capital inadequacy** → CET1 headroom vs requirement; a buyback cut is the tell.
5. **Reserve under-provisioning (incentive flag, Munger)** → management is *rewarded*
   on ROE/EPS, which is maximised by under-reserving and levering up. Reserve
   releases funding "beats" are the classic incentive-caused misjudgment — invert and
   ask what the numbers look like if provisions normalise.
6. **Opacity → outside circle of competence.** A derivative book or a loan portfolio
   you cannot decompose is a reason to pass, not to assume.

## 7. Master lens — Buffett / Graham (operational moves, not quotes)
- **ROE − Ke is the test.** "A bank earns its cost of capital plus a spread, or it is
  worth book at best." Only pay a premium to tangible book for a **durable** spread,
  and underwrite the CAP explicitly.
- **Insurance float = negative-cost leverage.** The prize is a long-tail, low-cost
  float compounded at a spread; the discipline is underwriting that does not chase
  premium by mispricing risk. State the **cost of float** (combined ratio) as a number.
- **Owner earnings vs reported.** Strip reserve releases, securities gains, and
  one-offs to a normalized earnings power; banks' GAAP earnings are unusually
  smoothable.
- **Margin of safety, financials-style.** Demand a discount to a **conservatively
  re-stated tangible book under stressed losses** — not just to value. Pair the
  engine's MoS buy-band (`monte_carlo` is for the FCFF archetypes; for financials,
  build the band by stressing ROE and credit cost) with the tangible-book floor.

## 8. Self-check gate (before publishing a financials report)
- [ ] ROE is **through-cycle**, with a normalized (not trough) credit cost stated.
- [ ] Book value is **tangible**; goodwill and AOCI marks handled.
- [ ] The **ROE − Ke spread and its CAP** are stated explicitly — the premium to book
      is derived from them, not asserted via a multiple.
- [ ] **CET1 headroom** checked; payout/growth are consistent with capital rules.
- [ ] Insurers: **cost of float / combined ratio** stated; float valued.
- [ ] RIM and the DDM cross-check **agree** (engine prints both).
- [ ] A margin-of-safety floor vs **stressed tangible book** is given.

## 9. Common traps
- Valuing on **peak-cycle ROE** or a benign-year credit cost.
- Trusting **stated book** through a credit cycle (reserves lag; AOCI hides).
- Putting a P/E on a lender **without checking capital adequacy** — earnings you
  cannot pay out (because the regulator won't let you) are worth less.
- **Double-counting** growth and payout (retention funds growth; you cannot spend it twice).
- Applying EV/EBITDA or sales-to-capital — **enterprise-value lenses to an equity story.**

## 10. Stress Testing and Margin of Safety

The standard Monte Carlo (`monte_carlo.py`) samples value drivers as if they
were independent — fine for an industrial company's revenue growth, margins, and
sales-to-capital. For financials that assumption is **wrong**. A bank's drivers
are **regime-dependent**: the same macro environment cannot simultaneously
produce strongly rising NIM **and** severely spiking credit losses.

### Why random sampling breaks for financials

- **NIM and credit losses are inversely coupled.** NIM widens when the central
  bank hikes rates (asset repricing > deposit cost); credit losses peak when
  the central bank is already cutting (recession response). Both spiking
  simultaneously requires contradictory macro regimes — a Monte Carlo that
  draws them independently will generate economically impossible outcomes.
- **Cost of equity moves with stress, not orthogonally.** Equity risk premia
  rise alongside credit losses in a recession; a draw of "low credit cost +
  high CoE" makes no regime sense.
- **Payout ratios are not free parameters.** Regulators constrain dividends
  and buybacks in stress; a draw of "high credit losses + high payout" is a
  capital-rule violation.

### Grid-based scenario analysis (replaces random-sampling Monte Carlo)

Instead of tens of thousands of independent draws, define a **small set of
internally-consistent scenarios** that span the economically-meaningful outcome
space. Each scenario is a coherent macro regime — rates, credit, and risk premia
move together in the direction that regime implies.

Engine: `scripts/financial_stress.py`

```bash
cd scripts
python financial_stress.py ../templates/financials.example.json
python financial_stress.py ../templates/financials.example.json --output stress.json
```

The script defines five scenarios (hardcoded in `SCENARIO_SPECS`; tune for the
specific company):

| Scenario | Probability | NIM | Credit loss | CoE | Payout |
|---|---|---|---|---|---|
| **Base** | 50% | through-cycle | through-cycle | base | base |
| **Optimistic** | 15% | wider (steep curve) | below-trend | lower | higher |
| **Pessimistic** | 15% | compressed (flat/inverted) | above-trend | higher | lower |
| **Credit Crunch** | 10% | compressed (Fed cutting) | severe | spiking | slashed |
| **Rate Shock** | 10% | wider (hiking cycle) | modestly elevated | higher | constrained |

Key design principle: **Credit Crunch has NIM compressing because the Fed cuts
in a crisis. Rate Shock has NIM widening because the Fed hikes. Neither
scenario has high NIM + high credit losses simultaneously** — the script
filters that combination with an explicit implausibility guard.

### Key stress dimensions

Each scenario adjusts these five dimensions (all flowing through to ROE, CoE,
and terminal assumptions in the residual-income engine):

| Dimension | What it captures | How it flows to the engine |
|---|---|---|
| **NIM** | asset/liability repricing gap, yield-curve shape | `base_roe`, `target_roe` |
| **Fee income growth** | capital-markets activity, wealth management, deal flow | `base_roe`, `target_roe` |
| **Credit loss rate** | NPL formation, reserve build/release, coverage ratio | `base_roe`, `target_roe` (drag) |
| **Cost/income ratio** | operating leverage, branch efficiency, tech spend | `base_roe`, `target_roe` (drag) |
| **Cost of equity** | risk-free rate, equity risk premium, bank-sector beta | `cost_of_equity_initial`, `cost_of_equity_terminal` |
| **Regulatory capital** | CET1 headroom, payout constraints | `payout_ratio`, `failure_probability`, convergence horizon |

The script maps each dimension delta to the `FinancialInputs` dataclass fields,
runs `financial_valuation.value()` for each scenario, and collects the results.

### Implausibility guard

Two thresholds are checked before each scenario runs (defined as constants at
the top of the script):

- `IMPLAUSIBLE_NIM_THRESHOLD = 0.010` (NIM contribution to ROE > +100 bp)
- `IMPLAUSIBLE_CREDIT_THRESHOLD = 0.020` (credit-loss drag > +200 bp)

If both are exceeded in the same scenario, it is flagged as implausible and
excluded from the weighted distribution. The warning reads:

> IMPLAUSIBLE: NIM delta +X% and credit-loss delta +Y% cannot coexist — rising
> rates (high NIM) and severe credit losses imply contradictory macro regimes.

### Computing the scenario-weighted MoS band

1. Run all non-implausible scenarios through the residual-income engine.
2. Compute the **weighted-mean** value-per-share: `sum(p_i × v_i) / sum(p_i)`.
3. Sort scenarios by value; build a discrete cumulative-probability
   distribution to extract percentiles (5th, 10th, 25th, 50th, 75th, 90th, 95th).
4. Compute dispersion: `(max - min) / median`.
5. MoS = `clamp(K × dispersion, 10%, 50%)` with `K = 0.35` (narrower than the
   Monte Carlo `K = 0.5` because a small scenario set overstates true spread).
6. Output the **buy-below / fair / rich-above** band, compatible with
   `charts.py` (`scenarios` and `football` chart kinds).

### Combining with the tangible-book floor

The scenario-weighted MoS band answers "what do I think it is worth across
regimes." The tangible-book floor (section 6, item 5; section 7, item 4) answers
"what is the hard asset value if everything goes wrong." Use both together:

- **Accumulate below:** the lower of (scenario MoS buy-below, 1.0× stressed
  tangible book).
- **Rich above:** scenario MoS rich-above.
- The gap between stressed tangible book and the pessimistic/credit-crunch
  scenario values tells you whether the market is pricing in tail risk or
  ignoring it.

### Self-check gate (additions for the stress-test section)

- [ ] The five scenarios are coherent regimes — no scenario has high NIM
      and high credit losses simultaneously (implausibility guard is clean).
- [ ] The scenario-weighted MoS band is stated alongside the tangible-book
      floor, not instead of it.
- [ ] Each scenario's DDM cross-check is within 5% of the RIM value (the
      engine prints both; a gap > 5% signals an input/derivation error).
- [ ] The probability weights sum to 100% (Base 50% + Optimistic 15% +
      Pessimistic 15% + Credit Crunch 10% + Rate Shock 10%).

> Worked template: `templates/financials.example.json` → `financial_valuation.py`.
> Stress engine: `scripts/financial_stress.py` → `financial_valuation.py` (per scenario).
> Classifier & other archetypes: `SKILL.md` (Mode A step 2). Voice & numbers ledger:
> `references/report-voice.md`.
