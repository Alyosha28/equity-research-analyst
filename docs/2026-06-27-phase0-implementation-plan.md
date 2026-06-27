# Phase 0 实施计划 — equity-research-analyst 优化

- **日期**: 2026-06-27
- **依据 spec**: `docs/2026-06-27-optimization-roadmap-design.md`
- **范围**: Phase 0 quick-wins(最便宜、最提专业度/可信度;是 Phase 1 范文素材)
- **不在本计划**: Phase 1 spine / Phase 2 enforcement(末尾仅大纲)

## Phase 0 目标 & 验收

交付四件:`charts.py`、`report_lint.py`、源台账纪律(文档)、MoS 买入带。验收 = 下列每条通过:
- `charts.py` 能用 NVDA 模板 JSON 产出 5 类图(非空 PNG+SVG),不报错。
- `report_lint.py` 对 `templates/report.example.md` 判 PASS;对一份故意写坏样例判 FAIL(退非零)。
- `monte_carlo.py --json` 输出含百分位 + MoS 买入带;`report()` 文本含买入带行。
- `report-voice.md` / SKILL.md Guardrails 含源台账(per-number source-tag + numbers ledger)与 MoS 说明。

---

## Workstream D — MoS 买入带(先做,charts/lint 都依赖其 JSON 与必备段落)

**改 `scripts/monte_carlo.py`**
1. 新增 `mos_band(values, dispersion_k=0.5, lo=0.15, hi=0.50)`:
   - `median = P50`;`dispersion = (P90 − P10) / median`;
   - `mos = clamp(dispersion * dispersion_k, lo, hi)`(默认 k=0.5;**阈值/系数实现期可校准**,写成命名常量)。
   - 返回 `{median, mos, buy_below: median*(1-mos), rich_above: median*(1+mos)}`。
2. `report()` 末尾加三行:`低于 X 增持 / X–Z 合理 / 高于 Z 偏贵`(X=buy_below, Z=rich_above)。
3. 新增 `--json` flag:输出 `{trials, mean, percentiles:{5,10,25,50,75,90,95,99}, price, price_percentile, p_value_ge_price, mos_band:{...}, values:[...]}`(values 供直方图;其余供报告/football field)。

**改 `SKILL.md` Guardrails**:加一条 "MoS 买入带:报告须给出 intrinsic×(1−MoS) 的增持线,MoS 随分布离散度放大"。

**测试**:`python monte_carlo.py ../templates/assumptions.example.json --price 409 --json` → 校验 JSON schema 完整、buy_below < median < rich_above、mos ∈ [0.15,0.50]。

---

## Workstream A — `charts.py`(消费引擎 JSON → 研报图)

**前置:补齐 JSON 出口**(charts.py 只读 JSON,不重算)
- `monte_carlo.py --json`(见 D)。
- 核对并按需为 `breakeven.py` / `reverse_dcf.py` / `comps.py` / `dcf_valuation.py` 增/确认 `--json`(dcf 已有)。每个缺的补一个最小 `--json`。

**新建 `scripts/charts.py`**,函数(各产 PNG+SVG 到 `--out` 目录):
| 函数 | 输入 JSON | 图 |
|------|----------|----|
| `monte_carlo_hist` | monte_carlo --json | 直方图 + 价格分位竖线 + MoS 买入带阴影 |
| `football_field` | dcf + reverse_dcf + comps（+ 现价） | 横向区间条:各 lens 的低/基/高 |
| `breakeven_heatmap` | breakeven --json | 2 变量(年10营收×margin)热力图 |
| `sensitivity_tornado` | 由 charts 调引擎做 ±1SD 单变量摆动 或读预算 JSON | tornado |
| `terminal_share` | dcf --json | 终值占比(显式FCFF vs PV-TV) |

**CLI**:`python charts.py --kind football|montecarlo|breakeven|tornado|terminal --in x.json [--price P] --out dir/`。

**复用/移植(先核 license)**:渲染/导出/配色与 markdown 嵌入 → `SJAD-67/ChartForge-skill`、`ohyesiamy/python-advanced-visual`;finance 图样式 → `akshatg10104/auto_dcf`、`daloopa/investing` chart_generator、`skumyol/ubs` sensitivity。统一一个 `_style()` 设 figsize/dpi/调色板/字体。

**测试**:对 NVDA 模板跑全部 5 类,断言输出文件存在且字节数>0;无显示后端(`matplotlib.use("Agg")`)。

---

## Workstream B — `report_lint.py`(确定性质量门)

**新建 `scripts/report_lint.py`**:输入一个 markdown 报告,逐规则 PASS/FAIL + 行号,任一 FAIL 退非零。

规则集(确定性):
1. **第二人称**:命中 `你/您/your/you`(词界)→ FAIL(report 正文禁第二人称)。
2. **emoji**:命中 emoji Unicode 区段 → FAIL。
3. **表格/散文比**:表格行数 / 正文段数 超阈值 → FAIL(防"表格墙")。**阈值实现期校准**,命名常量。
4. **必备段落**:缺 评级 / value-or-target / 现价 / MoS 买入带 / terminal% / 价格分位 / valid-as-of / 免责 → 每缺一项 FAIL。
5. **banned callout**:`校准命题[①-⑨]`、`回到你的命题` 等 → FAIL。
6. **无来源数字旗标**(源台账种子):正文中"裸数字"(无邻近 source-tag/脚注/引用)→ WARN(可配置升 FAIL)。

输出:汇总 + 每条 (规则, 行号, 摘录)。`--strict` 把 WARN 升 FAIL。

**测试**:
- `report_lint.py templates/report.example.md` → PASS(若现范文不达标,记录差距,作为修范文/调阈值依据,不擅改范文语义)。
- 新建 `tests/bad_report.sample.md`(含"你"、emoji、缺 MoS)→ FAIL 且列出违规。

---

## Workstream C — 源台账纪律(文档,无代码)

- **`references/report-voice.md`**:加一节"数字溯源":正文每个具体数字带 source-tag(audited/guidance/consensus/aggregator/own-estimate 之一),报告末附 **numbers ledger**(数字→来源→日期)。给正/反例。
- **`SKILL.md` Guardrails**:把现有 data-tiering 扩成 per-number sourcing;指向 report-voice 新节与 `report_lint.py` 规则 6。

---

## 顺序与依赖
```
D(MoS+monte_carlo --json) ──┬─→ A(charts: 依赖各 --json)
                            └─→ B(report_lint: 必备段落含 MoS)
C(文档) 可并行;B 规则6 与 C 源台账同义,一起定稿
```
建议序:**D → (A ∥ B) → C 收口**。

## 全局测试
- 现有 NVDA 复现锚不回归:`dcf_valuation.py ../templates/assumptions.example.json` 仍 ≈$236。
- 新增脚本均 `matplotlib.use("Agg")` / 无交互,可在 CI 无头跑。
- 给 `report_lint.py` 与 `monte_carlo.mos_band` 写 pytest 单测。

## 风险
- 复用图代码 license:移植前逐一核对,仅借模式。
- 阈值(表格比、MoS 系数)首版凭经验,标注"实现期校准"为命名常量,便于调。
- 改 `monte_carlo.py` 勿破坏现有文本 `report()` 与 NVDA 数值。

---

## Phase 1 / 2 大纲(后续各自成计划)
- **Phase 1 spine**:`financial_valuation.py`(超额收益)+ 4 playbook(大师嵌入)+ 分类器入 SKILL.md + 4 模板 + Freeport 范文(嵌图)+ `fetch_financials.py` + description 触发词。
- **Phase 2 enforcement**:`self-audit-gate.md`(Mode B rubric 转向内用)+ 每档 eval 用例 + 全局发布门。
