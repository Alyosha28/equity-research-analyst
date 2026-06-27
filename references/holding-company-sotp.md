# Holding-Company / Conglomerate Valuation (Sum-of-the-Parts)

When a company is an **operating business + a large investment portfolio**
(Tencent, SoftBank, Naspers/Prosus, Berkshire-likes, many Asian conglomerates), a
single whole-company DCF or P/E is the wrong tool — it blends businesses with
different economics and double-counts or hides the portfolio. Use **sum-of-the-
parts (SOTP)**. Engine: `scripts/sotp.py`.

## The structure
```
SOTP equity = core operating value            (intrinsic DCF of the OPERATING business only)
            + investment portfolio             (listed at market; unlisted at carrying)
              ... each with a haircut, then a holding-company discount
            + net cash
            - minority interests
per share = SOTP equity / shares  (then × FX to the listing currency)
```

## Rules that keep it honest
1. **Value the core on operating cash flows ONLY.** Strip out share of associates'
   profits and investment gains from the DCF — those live in the portfolio leg, or
   you double-count. (In `sotp.py`, run the core DCF with cash=debt=0 and use
   `operating_asset_value`; add net cash + investments separately.)
2. **Listed stakes at market**, optionally less a **tax-on-disposal haircut**
   (10–20%) if gains would be taxed on sale.
3. **Unlisted stakes at carrying value**, usually less an illiquidity markdown
   (10–30%) — or marked up if you have evidence (a hot private holding).
4. **Holding-company discount (10–40%)** on the portfolio for: lack of control,
   capital-allocation distrust, and the risk cash never reaches minority holders.
   Always show the result *across* a range of discounts — if the answer barely
   moves, the discount isn't the crux (it usually isn't).
5. **Don't double-count cash.** Net cash is added once, in the bridge — not also
   inside the core DCF.

## The stub / implied-core cross-check (the heart of a "hidden value" thesis)
Back the portfolio + net cash out of the **market cap** to reveal the multiple the
market is paying for the **core alone**:
```
implied core value = market cap − portfolio(after haircuts) − net cash
implied core P/E   = implied core value / core earnings
```
If the implied core multiple is far below what the core's growth/margins/FCF
deserve (and below peers), the "value gap / 价值洼地" is real — *quantified*, not
asserted. (Tencent June 2026: market paid ~11.8x for the core while a 9%-CoC DCF
valued it at ~21x.)

## The trap: a cheap stub can be a value trap, not an opportunity
A low implied-core multiple has two readings, and you must decide which:
- **Opportunity**: the market's extra discount is excessive fear → mean-reversion.
- **Trap**: the extra discount is a *rational* price for unmodelable risk
  (regulation, geopolitics, VIE/legal structure, capital controls, poor capital
  allocation) → it can stay cheap for years.

Make this explicit by solving for the **breakeven cost of capital** — the discount
rate at which your SOTP equals the current price. Then ask: *is that rate fair?*
For China/EM holding-cos the gap between a CAPM-fair rate and the market-implied
rate often **is** the whole thesis (Tencent: CAPM ~9% vs market-implied ~13.4% →
the ~4.4pp is the "China risk" you're really debating). Buybacks at a depressed
stub multiple are the mechanism that converts the discount into per-share value —
weigh capital-allocation discipline heavily.

## Don't force a Gaussian on a regime risk
For names whose dominant risk is a structural break (regulatory crackdown,
delisting, sanction), prefer **discrete scenarios** (bull/base/bear, each a full
driver set) over a Monte Carlo that imposes a smooth distribution — the real
distribution is often bimodal (re-rate vs break), and a symmetric simulation
understates the tails. See `valuation-lenses.md` (scenario lens).
