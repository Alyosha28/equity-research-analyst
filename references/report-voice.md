# Report Voice & Register (read before writing any report)

The single most common failure of this skill is writing **"an AI answering the
person who asked"** instead of **a research report published for investors**. This
file defines the register that prevents that. It governs every Mode A report and
Mode B memo.

## The one rule everything follows
**The reader is an anonymous investor who never saw the conversation.** Write so a
stranger can read the document and act on it. Nothing may depend on chat context,
and nothing may address the commissioner.

## Voice
- **Restrained authorial / institutional.** Use Damodaran's "I" (the analyst
  publishing to the public), or "this report" / "本报告" / "笔者". Pick one and
  hold it.
- **No second person to the reader.** "you" / "你" / "你的" addressing the reader is
  banned in the body. (It is fine only inside a directly quoted market view.)
- **The requester's thesis is a market hypothesis, not the audience.** Attribute it
  impersonally and evaluate it: "bulls argue…", "a popular framing holds…",
  "看多者认为…", "市场流行的一种类比是…". Never "your thesis" / "回到你的命题" /
  "I'll back you up on this".

## Form
- **Long-form prose.** Develop arguments in paragraphs; weave numbers into
  sentences ("revenue compounded to $2.4bn by 2005", not a lone table cell).
- **Exhibits are sparse and purposeful.** A valuation summary, a SOTP bridge, a
  sensitivity table, a scenario range — a handful, not a wall. The body carries the
  argument; exhibits support it.
- **No AI-answer tells.** Banned: bullet-fragment dumps, bold-keyword stuffing,
  emoji, decorative section emojis, "校准命题①"-style callout boxes, "Here's…"
  openers, restating the question back.
- **Lead with a stance.** A header with rating + target/value + current price, then
  a thesis paragraph. End sections with judgments, not lists.
- **Length follows the benchmark.** A full report is ~3,500–5,000 words of prose
  (the scale of Damodaran's NVIDIA piece), not a one-screen summary.

## Structure (Mode A)
Title + rating box → opening (the core thesis/hook, impersonal) → industry →
company → theme/driver → story-to-numbers (DCF) → SOTP (if a holding-co) → what the
market is pricing (reverse/stub) → scenarios → evaluation of the prevailing market
narratives → conclusion & rating rationale → report limitations / what could prove
it wrong → key risks → disclaimer.

## Intellectual honesty (Damodaran register)
State a clear view, then attack it: name the assumptions that carry the result, the
ways the analysis could be wrong, biases, and data dates. Confidence and humility in
the same document — never false precision, never hedging into mush.

## Anti-examples → fixes

| ❌ AI-answer register | ✅ Investor-facing register |
|---|---|
| "回到你的四个命题……" | "市场上流行着四种叙事，本报告逐一检验。" |
| "我愿意替你背书这笔交易。" | "综合证据，本报告给予增持评级。" |
| "**核心结论**：…（表格+加粗+emoji）" | 一段陈述结论的散文 + 一个估值汇总 exhibit |
| "你需要判断的是……" | "投资者面对的真正问题是……" |
| 满屏 bullet 碎片 | 成段论述，数字写进句子 |

## Number sourcing & the numbers ledger (数字溯源)
The deadliest failure of an LLM-written report is not thin prose — it is a
**confidently invented number**. Every specific figure must be traceable, and the
reader must be able to tell a fact from a judgment.

- **Tag every material number with its data tier** (same tiers as the Guardrails):
  audited / management-guidance / sell-side-consensus / third-party-aggregator /
  own-estimate. Weave the tag into the sentence or a footnote — never a separate
  apparatus that breaks the prose.
- **Append a numbers ledger** to close the report: a compact table of the
  load-bearing figures → source → as-of date. This is the one permitted "wall of
  data"; it is what lets a stranger audit the call.
- **Never state a number you cannot source.** If it is an estimate, say so and give
  the basis — an honest "own estimate" beats a fake precision or a fabricated cite.
- **Mechanical gate:** `scripts/report_lint.py` flags numeric mentions with no
  adjacent source marker and a missing ledger. Run it before publishing; under
  `--strict` these become blocking.

## Quick self-check before delivering
- [ ] `grep` the body for second-person "你"/"you" → only inside quoted market views.
- [ ] A stranger with no chat context could read it and act.
- [ ] Prose-dominant; exhibits are few and earn their place.
- [ ] Leads with rating + target + thesis; ends with a judgment.
- [ ] States what could prove the thesis wrong (not just why it's right).
- [ ] Every material number is tier-tagged; a **numbers ledger** closes the report.
- [ ] A **margin-of-safety buy-band** is stated (intrinsic × (1 − MoS); `monte_carlo.py` emits it).
- [ ] Carries a not-advice disclaimer and data dates.
- [ ] **`python scripts/report_lint.py <report>` passes** (use `--strict` for a fresh report).

## Integration
- Templates: [`output-templates.md`](output-templates.md)
- Method: [`methodology-damodaran.md`](methodology-damodaran.md)
- Worked example in this register: [`../templates/report.example.md`](../templates/report.example.md)
