# equity-research-analyst 优化路线图 — 设计文档

- **日期**: 2026-06-27
- **对象 skill**: `C:\Users\Administrator\.claude\skills\equity-research-analyst`
- **状态**: 已通过 brainstorming 评审,待 user 复核 → 进入 writing-plans
- **方法**: 先 grill-me 收敛主轴,再 brainstorming 拓宽全景,按 ROI 排成分阶路线

---

## 1. 背景与问题

现 skill 是一套成熟的、以 Damodaran "story → numbers → value" 为脊柱的基本面估值 skill,已内置 7 个分析 lens、可运行的 Python 引擎(DCF/Monte Carlo/breakeven/reverse-DCF/comps/SOTP)、严格的 report-voice 与 depth 标准。

user 在评审中确认的三个真实痛点(按其原话):

1. **公司类型覆盖太窄** — 仅成长股(NVDA)+ 控股公司(腾讯)样例;遇到银行/周期/未盈利/高股息无现成抓手。
2. **判断维度不够** — 觉得方法论缺某些视角(这是"加大师"真正想解决的)。
3. **输出质量不稳** — 有时跑出"AI 摘要"而非 Damodaran 级深度;voice/depth 时好时坏。

brainstorming 进一步揭示两条 grill 阶段未充分探索、但 ROI/effort 很高的轴:**可视化** 与 **数字溯源**;并确认引擎已算出可视化所需全部数字(纯增量画图)。

### 设计判断:三个痛点的根因
- 痛点 1 与 2 同根:**不同公司 archetype 需要不同 driver**。当前只有一种隐含框架(成长-tech)。→ 解法是 **archetype-specific 估值 playbook**。
- 痛点 3 部分是痛点 1/2 的下游(无框架 → 输出薄),部分独立(已覆盖公司也会忽略 depth 标准)。→ 解法是 **可执行的质量门(不是更多描述性标准)**。

---

## 2. 目标 / 非目标

### 目标
- 让 skill 覆盖 Damodaran 估值分类的全部主干 archetype,每类有正确 driver、引擎适配、样例。
- 把投资大师知识以**操作化、点对点、嵌入式**方式注入(非语录专栏)。
- 用**可视化 + 数字溯源 + 可执行质量门**把输出从"像 AI 摘要"稳定提升到"像专业研报"。
- 降低输入数据准备摩擦(数据自动抓取)。

### 非目标(YAGNI,明确砍掉)
- skill 拆分(produce/critique/refresh 三模式当前内聚,不拆)。
- real-options / 生物科技期权估值、FX 大改。
- 独立 PDF/HTML 渲染管线(待 charts 落地后另议)。
- 实时行情/技术面/情绪信号(归 `stock_analyzer`,本 skill 只做基本面)。

---

## 3. 决策账本(grill-me + brainstorming 已锁定)

| # | 决策 | 结论 |
|---|------|------|
| 1 | 主轴 | 按公司类型分档的 **archetype 估值 playbook**(非"大师语录注入") |
| 2 | archetype 集 | 新增 **金融、周期/大宗、未盈利/年轻、成熟/衰退**;复用现有 成长-tech + 控股-SOTP |
| 3 | 引擎 | 新建 `financial_valuation.py`;其余 3 档复用现有 FCFF 引擎 |
| 4 | 金融主方法 | **超额收益 `(ROE−Ke)×BV`** 为主,FCFE / DDM 为备 |
| 5 | 大师注入 | **嵌入式、点对点、不立专栏**。Buffett→金融 + 通用 MoS 买入带;Dalio→周期;Munger→折入 bear 清单 |
| 6 | 范文 | **周期=完整 gold-standard 范文(Freeport-McMoRan)**;金融=模板+数值复现锚;未盈利/成熟=各一份输入模板 |
| 7 | 质量轨 | **重量、全局**:自审门(Mode B rubric 转向内用)+ `report_lint.py`,改到通过 |
| 8 | 可视化 | matplotlib PNG/SVG;**复用** ChartForge / python-advanced-visual 的渲染与嵌入,**移植** auto_dcf / daloopa 的金融图样式 |
| 9 | 数据抓取 | `fetch_financials.py` 并入 Phase 1(原 Phase 3 上提) |
| 10 | 排期 | **三阶**(grill 原定"先 spine 后 enforcement",brainstorming 在前插入便宜高冲击的 Phase 0):Phase 0 quick-wins → Phase 1 spine(含数据抓取)→ Phase 2 enforcement |

---

## 4. 架构:新增件如何接入现有引擎

所有新脚本沿用现有约定:输入 JSON assumptions(金额 $M、利率小数、股数 M、`_` 前缀为注释)。

```
scripts/
  valuation_inputs.py      (现有, 共享输入模型)
  dcf_valuation.py         (现有 FCFF; 周期/未盈利/成熟复用)
  monte_carlo.py           (现有; + MoS 买入带输出)
  breakeven.py reverse_dcf.py comps.py sotp.py  (现有)
  financial_valuation.py   (新: 超额收益/FCFE/DDM, 金融专用)
  charts.py                (新: 消费各脚本 --json → PNG/SVG)
  report_lint.py           (新: 机检 markdown 报告, 质量门)
  fetch_financials.py      (新: 预填 assumptions 骨架)
references/
  playbook-financials.md playbook-cyclical.md playbook-young.md playbook-mature.md  (新)
  self-audit-gate.md       (新, Phase 2)
  (现有 references 增补: report-voice.md 加源台账纪律; report-critique-rubric.md 注明可转向内用)
templates/
  freeport.cyclical.* (新, 含范文) ; financials/young/mature assumptions 模板 (新)
evals/evals.json           (Phase 2 增 archetype 用例)
SKILL.md                   (加 archetype 分类器 + MoS + 新脚本 + description 触发词)
```

每个新单元的单一职责 / 接口 / 依赖:
- **financial_valuation.py** — 做什么:对金融机构按超额收益模型出 value/share。接口:`python financial_valuation.py inputs.json [--json]`。依赖:valuation_inputs(扩展)。
- **charts.py** — 做什么:把引擎 JSON 转成研报图。接口:`python charts.py --kind football|montecarlo|breakeven|tornado|terminal --in x.json --out dir/`。依赖:matplotlib;各引擎脚本的 `--json`。
- **report_lint.py** — 做什么:对 markdown 报告做确定性合规检查,FAIL 退非零。接口:`python report_lint.py report.md`。依赖:无(纯文本规则)。
- **fetch_financials.py** — 做什么:抓 10 年财务/股本/现价 → 预填 assumptions 骨架(标记数据 tier)。接口:`python fetch_financials.py TICKER --out skel.json`。依赖:yfinance / SEC EDGAR;**产出永远标为第三方 tier,需人工确认,绝不自动发布**。

---

## 5. 路线图(ROI 排序)

### Phase 0 — Quick wins(最便宜、最提"专业度+可信度";是 Phase 1 范文的素材)
1. **`charts.py`** — Monte Carlo 直方图(含价格分位标记)、breakeven 热力图、football field(内在DCF vs 反向DCF隐含 vs comps)、敏感性 tornado、终值占比。复用/移植见 §6。
2. **`report_lint.py` v1** — 确定性机检:第二人称(你/您/you/your)、emoji、表格/散文比、必备段落(评级/value-target/现价/MoS/terminal%/价格分位/valid-as-of/disclaimer)、`校准命题①`式 callout、**无来源数字旗标**。
3. **源台账纪律** — `report-voice.md`/depth 标准/Guardrails 增"每个数字带 source-tag + 附录 numbers ledger"(现有 data-tiering 延伸)。
4. **MoS 买入带** — `monte_carlo.py` 输出 `intrinsic_median×(1−MoS)`,MoS 随分布离散度 `(P90−P10)/median` 放大并 clamp 到 [0.15, 0.50];报告呈"低于 X 增持 / X–Z 合理 / 高于 Z 偏贵"。写入 Guardrails。

### Phase 1 — Spine:archetype 覆盖 + 数据抓取
5. **`financial_valuation.py`**(超额收益主 / FCFE / DDM 备)+ 数值复现锚。设计见 §7。
6. **4 份 playbook**(统一骨架见 §8),大师嵌入:financials(Buffett:浮存/owner-earnings/ROE−Ke)、cyclical(Dalio:周期定位→正常化点+price deck)、young(failure 分支)、mature(runoff/派息);Munger 折入各 bear 清单。
7. **archetype 分类器/路由** 写入 SKILL.md Mode A step 2(决策表见 §8)。
8. **4 份 assumptions 输入模板** + **Freeport 周期 gold-standard 范文**(嵌 Phase-0 图)。
9. **`fetch_financials.py`** — 预填假设骨架,降低输入摩擦。
10. **description 触发词更新**(银行/保险/周期/大宗/未盈利/安全边际/owner earnings/价值投资·巴菲特·达利欧;仍标"基本面估值,非荐股")。

### Phase 2 — Enforcement + 度量(承诺项)
11. **自审门**(`self-audit-gate.md`)— 发布前把 Mode B rubric 转向内用(语义自评)+ 调 `report_lint.py`(机检),revise-until-pass。
12. **`evals/evals.json` 每档新增 eval 用例** — 用 skill-creator 跑评测,量化 rich vs thin。
13. **全局 depth/voice 强制** 接到发布门(Mode A/C 输出前必过门)。

---

## 6. 可视化复用决策(GitHub 调研结论)

- **无 finance 专用 charting skill** 可直接安装。
- **复用渲染/导出/美学层**:`SJAD-67/ChartForge-skill`(出版级 PNG/SVG/PDF、配色)、`ohyesiamy/python-advanced-visual`(matplotlib→markdown/PDF 嵌入、BytesIO、dpi/figsize 校准)。Tufte/HBR 风格参考:`vikast908/data-visualization-skill`、`kgraph57/hbr-style-visualization`。
- **移植 finance 图样式**:`akshatg10104/auto_dcf`(football field + 双敏感性)、`daloopa/investing`→`chart_generator.py`("Valuation Football Field")、`skumyol/ubs`→`sensitivity.py`(tornado)。
- **边界**:我们写 finance 逻辑(消费本引擎 JSON),不重造图表管线与美学。**移植任何代码前先核对其 license**。

---

## 7. `financial_valuation.py` 设计(金融档引擎)

**为何不能用 FCFF 引擎**:银行无"营收×营业利润率",其再投资经由监管资本/风险加权资产,非 sales-to-capital。强套 FCFF 算出的是错值。

**主模型 — 超额收益(Excess Return on Equity)**
- `Equity = BV0 + Σ PV(ExcessReturn_t)`,其中 `ExcessReturn_t = (ROE_t − Ke_t) × BV_{t-1}`,以 `Ke` 折现。
- 账面价值滚动:`BV_t = BV_{t-1} × (1 + ROE_t × (1 − payout_t))`。
- 终值:稳定 ROE/g 下的超额收益永续。
- 输入:`bv0`、ROE 路径(base→target 渐变,类比 margin glide)、Ke 路径(CAPM)、payout/retention、terminal ROE、terminal growth、shares。
- 输出:value/share、隐含 P/B、超额收益时间表、终值占比。

**备用 lens**:FCFE 折现、DDM —— 作为交叉校验输出,不作主值。

**保险特例**:浮存(float)作为低/负成本资金,以 owner-earnings 口径在 playbook 中说明;核心仍走超额收益。

**数值复现锚**:选一家财报干净的银行,固定一组 inputs → `≈$Y/share`,写入模板与 reproducibility check(类比 NVDA `≈$236`)。

---

## 8. archetype 分类器 + playbook 统一骨架

**分类器(SKILL.md Mode A step 2,按序判定)**
1. 金融中介(银行/保险/放贷),资本即原料? → financials + `financial_valuation.py`
2. 盈利由不可控的大宗/周期价格主导? → cyclical(Dalio 叠加;正常化 + price deck;现有引擎)
3. 当前亏损/未达规模,价值系于生存 + 通向 margin? → young(failure 分支;现有引擎)
4. 营收持平/下滑、资本在返还而非再投? → mature/declining(现有引擎)
5. 经营主体 + 大额投资组合(控股)? → SOTP(现有)
6. 否则 → 成长-tech 默认(现有)

**playbook 统一骨架(对齐现有 "Method/Borrow/Blind-spot" 房风)**
1. 识别(分类测试 + 误判陷阱)
2. 为何默认四驱动 FCFF 框架在此失效
3. 正确 driver(表)
4. 引擎映射(用哪个脚本 + 如何设输入)
5. 输入估计 / 会计调整 deltas
6. archetype bear 清单 + 领先指标(Munger 逆向/激励折入此处)
7. 大师操作(Buffett/Dalio,若适用)
8. 自检门(发布前须确认项)
9. 常见陷阱 + 模板指针

---

## 9. 测试 / 验证

- **financial_valuation.py**:数值复现锚(固定 inputs → 期望 value/share);单元测试覆盖超额收益滚动与终值。
- **charts.py**:smoke test,对样例 JSON 渲染不报错,产出非空 PNG/SVG。
- **report_lint.py**:`templates/report.example.md` 必须 PASS;一份故意写坏的样例(含"你"、emoji、缺 MoS)必须 FAIL。
- **evals**:每 archetype 新增 eval 用例,度量 rich vs thin(skill-creator 可跑)。
- **自审门**:Mode A 范文(Freeport)过门通过即闭环验证 Phase 2。

---

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 数据抓取源(yfinance/EDGAR)质量/限流 | 产出标第三方 tier,人工确认,绝不自动发布 |
| 复用 charting 代码 license | 移植前逐一核对 license;仅借模式不照搬受限代码 |
| scope 蔓延 | 严格分阶;Phase 2 为承诺项但排在 spine 之后 |
| 新引擎/脚本回归 | 每个引擎都配 reproducibility 锚 + 单测 |
| 大师注入退化成"语录" | 强制嵌入式、点对点;不设独立大师专栏 |

---

## 11. 开放问题

- 金融数值复现锚选哪家银行(需财报干净、公开可得)— 实现期定;不阻塞设计。
- `fetch_financials.py` 数据源优先级(yfinance vs EDGAR vs stooq)— 实现期定。

> 免责:本 skill 产出为基本面分析,非个性化投资建议。
