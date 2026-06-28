[English](./README.md) | **简体中文**

<p align="center">
  <h1 align="center">AnalystCollective</h1>
  <p align="center"><em>叙事 → 数字 → 价值 &nbsp;·&nbsp; 用 Damodaran 的方法论，做可复现的基本面估值</em></p>
</p>

---

**AnalystCollective** 不是一个黑箱荐股工具。它是一套**透明的、由 AI Agent 协作驱动的估值引擎**——
你看到的不只是一家公司"值多少钱"，而是这个故事在每一个假设下如何展开，以及价格与价值的差距到底意味着什么。

它把 Aswath Damodaran 的六层估值框架变成了可运行的 Python 代码，用 **17 个独立的 AI 子 Agent**
组成一条自迭代估值产线，每一步都经对抗性审查。每个数字都可审计，每份报告都可复现。

---

## 为什么是 AnalystCollective？

大多数投资研究工具落在两个极端上：

- **券商/卖方报告**：结论先定，数据后凑。不可复现，不可审计。
- **量化回测框架**：纯数学，没有故事。把公司当成一串时间序列。

AnalystCollective 走第三条路——**一人成队**：17 个 Agent 并行工作，彼此交叉验证，每一步都经对抗性审查，最终产出的不是"买/卖"两个字，而是一份完整的、带安全边际区间的、可复现的投资备忘录。

---

## 更新内容（2026 年 6 月）

`generate-pdf` 子技能经过在中国公司中文报告、Windows 环境（含中文路径如 `D:\研报生成`）下的真实测试，完成了一次稳健性重构：

| 功能 | 重构前 | 重构后 |
|------|--------|--------|
| **公司 Logo** | CSS `position: fixed`（每页与标题文字重叠） | 引擎原生机制：headerTemplate（Chromium）/ `position: running()`（WeasyPrint）。上边距随 logo 高度自动增长——永不复现重叠。 |
| **图片路径** | `file://` / 相对路径（在非 ASCII 目录下静默空白） | 所有图片 base64 嵌入为 `data:` URI —— 与路径无关，引擎通用。 |
| **图表尺寸** | 无高度上限（9×5.2 英寸图表占据全页） | `max-height: 8.5cm; object-fit: contain` 上限约束所有图表。 |
| **视觉自检** | 仅靠文件大小检查（排版 bug 完全不可见） | `render_pdf_previews()` 将 PDF 渲染回 PNG 供实际查看。`--verify-visual` 标志。 |
| **引擎检测** | Windows 上 WeasyPrint 抛出 `OSError`（缺失 Pango）时崩溃 | 捕获宽泛 `Exception` → 优雅降级到 Playwright。 |
| **Logo 尺寸** | 硬编码 0.95cm | 可配置 `--logo-height`（cm）。上边距自动计算：`max(2.5, height + 1.4)`。 |

详见 [`skills/generate-pdf/PDF_FIXES.md`](skills/generate-pdf/PDF_FIXES.md)（完整事后分析）和 [`skills/generate-pdf/SKILL.md`](skills/generate-pdf/SKILL.md)（更新后的规格文档）。

## 目录

| 模块 | 说明 |
|------|------|
| **估值引擎**（`scripts/`）| 13 个 Python 程序 —— DCF、蒙特卡洛、逆向 DCF、盈亏平衡、分部估值、可比分析、金融股估值、金融压力测试、图表、报告质检、数据获取、裁决工件管理、CJK 字体检测 |
| **方法论**（`references/`）| Damodaran 六层框架 + 5 类公司操作手册 + 跨模型裁决指南 + 七视角交叉验证 |
| **公司类型手册** | 6 类公司各有专属 playbook — 默认（含护城河）、银行/保险、周期/大宗商品、亏损/成长期、成熟/衰退型、控股公司 |
| **模板**（`templates/`）| 已跑通的完整案例 —— NVIDIA（2023.6）、美光 MU（2026.6）、腾讯 SOTP、Freeport-McMoRan |
| **测试**（`tests/`）| 44 项 pytest 测试 + 10 fixtures，覆盖 PDF 渲染、图表生成、主题解析 |
| **写作规范** | 投资者报告写作纪律 —— 禁止第二人称、禁止 emoji、强制安全边际区间、强制数字台账、强制图表引用检查 |

## 架构：Agent 团队 + 对抗性审查

AnalystCollective 由 **17 个子 Agent** 组成，通过一条 10-Wave 自迭代管线编排。
设计上有两个核心机制：

### 机制一：默认并行（Agent 团队）

子 Agent 之间凡是独立的任务，编排器**自动并行派发**，无需人工指定。大幅缩短端到端时间：

```
第一波（并行）→ /analyze-industry  ∥  /analyze-theme
第二波         → /analyze-company
第三波         → /build-assumptions
第四波         → /run-valuation
第五波（并行）→ /durability-check   ∥  /triangulate
第五点五波     → /generate-charts      （12 种专业级图表）
第六波         → /write-report
第七波         → /self-audit
第八波         → /generate-pdf         （含图表嵌入 + CJK 排版）
```

### 机制二：每一步都经对抗性审查

**每个**子 Agent 完成后，立刻有一个审查 Agent 对其输出进行批判性审查。
审查立场不是友好的，而是怀疑的——必须至少找到一个薄弱点，或者证明输出真正经得起推敲。
每个子 Agent 有 1–2 轮修改机会：

```
子Agent → 输出 → 对抗性审查 → 需要修改？
  ↑                              │
  └── 修正 + 重新提交（第2轮）───┘
                                       ↓
                                  还要再改？
                                       │
                          ┌────────────┴────────────┐
                          ↓                         ↓
                        通过                     升级标记
                    （进入下一步）          （继续，但带风险标注）
```

### 全部子 Agent

| 子 Agent | 职责 | 关键审查项 |
|----------|------|-----------|
| `/classify-archetype` | 判定公司类型 → 选择引擎和操作手册 | 是否误判为金融股？边界情况是否考虑？ |
| `/analyze-industry` | 行业生命周期、利润周期、龙头轮动 | 是否有 10 年以上数据？龙头轮动表是否真实？ |
| `/analyze-company` | 商业模式、护城河、十年轨迹、回撤 | 护城河是否分解？回撤是否记录？股权激励是否量化？ |
| `/analyze-theme` | 主题驱动力、TAM×份额、竞争格局 | 是否有两条收入路径？TAM 来源？是否存在"大市场幻觉"？ |
| `/build-assumptions` | 叙事→数字，会计调整，输出 .json | 会计科目是否计算？每项假设是否有依据？ |
| `/run-valuation` | 执行 DCF / 蒙特卡洛 / 盈亏平衡 / 逆向 | 所有脚本是否跑通？终值占比是否注明？安全边际区间是否给出？ |
| `/durability-check` | ROIC-WACC 差、竞争优势期、RONIC 衰减 | ROIC 是否调整？每项护城河是否有威胁？CAP 是否有理有据？ |
| `/triangulate` | 七视角交叉验证 | 是否避免了简单平均？分歧点是否具体？变体是否可证伪？ |
| `/write-report` | 撰写投资者报告 | 六大深度要素是否齐全？数字台账是否完整？ |
| `/self-audit` | 报告质检 + 自我批评 | Lint 是否通过？严重问题是否被回避？分数是否诚实？ |
| `/generate-charts` | 渲染 12 种专业级金融图表 | CJK 字体是否渲染？色板是否统一？图表标题是否陈述结论？ |
| `/generate-pdf` | 生成排版级 PDF（含图表嵌入） | 图表是否嵌入？Logo 是否在页边距内（不压标题）？所有图片是否 base64 嵌入？中文字体是否渲染？评级框是否醒目？视觉预览是否验证？ |
| `/critique-report` | 模式 B：审计外部研究报告 | 是否有证据支撑？关键计算是否可复现？结论是否与证据一致？ |
| `/refresh-valuation` | 模式 C：追踪更新估值 | 日期是否覆盖更新？假设变动是否明确？逆向是否重新检验？ |
| `/fetch-data` | 共享：数据骨架 | 数据来源是否标注？置信度分级是否正确？警告是否完整？ |
| `/fetch-damodaran-data` | 共享：从 NYU Stern 拉取 ERP/CRP/Beta/CoC | 数据是否最新？日期是否标注？适用范围是否正确？ |

每个子 Agent 均可独立调用和优化——改一个 Agent 的审查标准、优化一段 prompt，整条产线直接受益。

## 哲学

> **"估值是一个被数字约束的故事。没有数字的故事是童话，没有故事的数字是没人信的电子表格。"**
> —— Aswath Damodaran

每份估值都追溯到一个叙事，每个叙事都用分布而不是点估计做压力测试。引擎强制执行几条不妥协的纪律：

- **叙事 → 数字 → 价值。** 永远不要给出没有叙事的电子表格，永远不要给出没有数字的叙事。
- **量化不确定性，而不是躲在其后。** 对关键驱动因子跑蒙特卡洛，输出一个分布。
- **稳健性优于精度。** 如果一个结论因为 2% 的参数微调就反转，那它不算结论。
- **投资与交易分开。** 价值收敛填补价格-价值缺口；动量是另一个游戏。
- **诚实面对偏见。** 披露先验、数据日期和数字台账。

## 快速开始

```bash
# 克隆项目
git clone https://github.com/Alyosha28/equity-research-analyst.git
cd equity-research-analyst

# 复现 NVIDIA 估值（Damodaran，2023年6月）
cd scripts
python dcf_valuation.py ../templates/assumptions.example.json
# → 内在价值 ≈ $236/股

# 蒙特卡洛模拟
python monte_carlo.py ../templates/assumptions.example.json --price 409 --trials 20000
# → 市价位于价值分布 ~94 分位，P(低估) ≈ 5%

# 市价已经隐含了什么？
python reverse_dcf.py ../templates/assumptions.example.json --price 409 --solve-for terminal_revenue
# → $409 的股价隐含着第 10 年营收 ~$4890 亿（比基准高 83%）

# 生成图表
python monte_carlo.py ../templates/assumptions.example.json --price 409 --json > mc.json
python charts.py --kind montecarlo --in mc.json --out figs/

# 构建专业 PDF（自动检测引擎，图片 base64 嵌入）
cd ../skills/generate-pdf/scripts
python render_pdf.py ../../templates/report.example.md --out report.pdf \
    --cjk --lang zh --chart-index ../../figs/chart-index.json

# 附加公司 Logo（自动适配尺寸，永不压文字）
python render_pdf.py ../../report.md --out report.pdf \
    --logo company_logo.jpg --logo-height 1.4 --verify-visual

# 估值你自己的公司
cp ../templates/assumptions.example.json ../my_company.json
# 编辑 my_company.json，填入你的假设
python dcf_valuation.py ../my_company.json
```

核心引擎零依赖，Python 3.10+ 即可运行。图表生成可选安装 `matplotlib`。

---

## 引擎一览

所有脚本以 JSON 假设表为统一输入。金额单位为**百万美元**，利率为**小数**（0.40 = 40%），
股数以**百万股**计。每个估值脚本均支持 `--json` 输出机器可读格式，直接对接 `charts.py`。

| 脚本 | 视角 | 输出 |
|------|------|------|
| `dcf_valuation.py` | 内在价值 DCF | 每股价值、FCFF 时间表、终值占比 |
| `monte_carlo.py` | 不确定性 | 价值分布、分位数、**安全边际买入区间**、市价分位 |
| `breakeven.py` | "什么条件必须成立" | 双变量敏感性表（营收 × 利润率） |
| `reverse_dcf.py` | 预期投资 | 当前市价隐含的增长/利润率/资本成本 |
| `sotp.py` | 分布估值 | 核心 DCF + 投资组合市值 + 净现金 → 每股价值 |
| `comps.py` | 相对估值 | 同业中位数倍数 → 隐含价值 |
| `financial_valuation.py` | 银行与保险 | 超额回报模型 `(ROE − Ke) × BV` + DDM 交叉验证 |
| `financial_stress.py` | 金融压力测试 | 5 情景网格分析 → scenario-weighted MoS band（替代 MC） |
| `charts.py` | 可视化 | 5 种专业级金融图表 → PNG/SVG（矢量，CJK 字体） |
| `render_pdf.py` | PDF 渲染 | MD+图表+CSS → 专业排版 PDF。自动检测引擎（WeasyPrint/Playwright）。Logo 通过 headerTemplate/running element。Base64 图片嵌入。视觉预览。 |
| `report_lint.py` | 质检关卡 | 检测第二人称/emoji/缺失安全边际/台账/免责声明/**未引用图表** |
| `verdict.py` | 裁决管理 | 跨模型/同模型裁决工件保存、加载、同族安全验证 |
| `fetch_financials.py` | 数据预填 | yfinance/EDGAR → 假设骨架（*第三方数据，使用前请核实*） |
| `cjk_font_detection.py` | CJK 检测 | 三级回退（matplotlib → fc-list → 文件系统扫描） |
| `build_manifest.py` | 清单组装 | 自动发现引擎 JSON → 生成 output-manifest.json |

### 四大价值驱动因子

所有估值最终归结为四个输入——它们全部来自叙事，而非拍脑袋：

1. **营收增长** —— 分业务线 TAM × 市场份额，逐步收敛至无风险利率水平
2. **目标营业利润率** —— 研发调整后，附收敛路径
3. **再投资效率** —— 销售/资本比（每一美元投资产生的营收）
4. **资本成本** —— 始于行业水平，逐步滑向成熟市场水平

---

## 公司类型

大多数公司适用默认的 FCFF 框架。另有五类公司**不适用**——各有自己的引擎和操作手册：

| 类型 | 引擎 | 核心思路 | 示例 |
|------|------|----------|------|
| **默认（有护城河）** | `dcf_valuation.py` | FCFF，四大驱动因子，terminal_ROC > CoC | NVIDIA，多数实业公司 |
| **金融股**（银行、保险）| `financial_valuation.py` | 超额权益回报 `(ROE − Ke) × BV` | 大型银行、产险公司 |
| **周期/大宗商品** | `dcf_valuation.py` | 基于**标准化**周期中值的 FCFF + 商品价格中枢 | Freeport-McMoRan、美光 MU |
| **亏损/成长期** | `dcf_valuation.py` | FCFF + **失败分支** + 利润率路径 | 生物医药、早期 SaaS |
| **成熟/衰退型** | `dcf_valuation.py` | FCFF，低/负增长，近期现金流占主导 | 烟草、传统媒体 |
| **控股公司** | `sotp.py` | 核心 DCF + 投资组合按市价重估 + 净现金 | 腾讯、软银、综合企业 |

---

## 完整案例 —— NVIDIA（2023年6月）

忠实复现 Damodaran 对 NVDA 的公开估值（当时市价 ~$409/股）：

```
内在价值 ≈ $236–240/股
市价位于价值分布 ~94 分位
P(被低估) ≈ 5%
评级：减持（REDUCE）
```

引擎完整复现了数字、分布和决策。完整研究报告见 `templates/report.example.md`。

---

## 交叉验证 —— 七个视角

单视角不可靠。框架用七个视角交叉验证，并明确要求：**告诉我它们在何处一致、何处分歧——
分歧所在，正是尽调的战场。**

| 视角 | 回答什么 | 引擎脚本 |
|------|----------|----------|
| 1. 内在 DCF | 这家公司值多少钱？ | `dcf_valuation.py` |
| 2. 蒙特卡洛 | 不确定性有多大？ | `monte_carlo.py` |
| 3. 盈亏平衡 | 当前市价需要什么条件才成立？ | `breakeven.py` |
| 4. 逆向 DCF | 市价已经隐含了多少？ | `reverse_dcf.py` |
| 5. 可比分析 | 同行暗示什么估值？ | `comps.py` |
| 6. 分部估值 | 拆开来分别值多少？ | `sotp.py` |
| 7. 熊/怀疑视角 | 怎么才能亏钱？ | *结构化核查清单* |

---

## 报告质检

每份报告在发布前必须通过自家工具审计：

```bash
python report_lint.py ../path/report.md          # 快速检查
python report_lint.py ../path/report.md --strict  # 新报告 —— 零容忍
```

质检工具检查：第二人称（"你"）、emoji、被禁用的话术模式、
缺失安全边际区间、缺失数字台账、缺失免责声明、AI 写作痕迹。
另外，用 `references/report-critique-rubric.md` 中的七维审查标准自我对标。

---

## 项目结构

```
equity-research-analyst/
├── SKILL.md              # 主编排器（路由 A/B/C 三种模式）
├── skills/               # 14 个子 Agent（估值产线）
│   ├── classify-archetype/SKILL.md
│   ├── analyze-industry/SKILL.md
│   ├── analyze-company/SKILL.md
│   ├── analyze-theme/SKILL.md
│   ├── build-assumptions/SKILL.md
│   ├── run-valuation/SKILL.md
│   ├── durability-check/SKILL.md
│   ├── triangulate/SKILL.md
│   ├── write-report/SKILL.md
│   ├── self-audit/SKILL.md
│   ├── generate-pdf/SKILL.md
│   ├── critique-report/SKILL.md
│   ├── refresh-valuation/SKILL.md
│   └── fetch-data/SKILL.md
├── scripts/              # Python 估值引擎（11 个程序）
│   ├── dcf_valuation.py
│   ├── monte_carlo.py
│   ├── breakeven.py
│   ├── reverse_dcf.py
│   ├── sotp.py
│   ├── comps.py
│   ├── financial_valuation.py
│   ├── charts.py
│   ├── render_pdf.py       # MD→PDF，含 logo、base64、视觉自检
│   ├── report_lint.py
│   ├── fetch_financials.py
│   └── valuation_inputs.py
├── references/           # 方法论 & 操作手册
│   ├── methodology-damodaran.md
│   ├── input-estimation.md
│   ├── valuation-lenses.md
│   ├── analyst-playbook.md
│   ├── playbook-financials.md
│   ├── playbook-cyclical.md
│   ├── playbook-young.md
│   ├── playbook-mature.md
│   ├── holding-company-sotp.md
│   ├── report-critique-rubric.md
│   ├── report-voice.md
│   ├── self-audit-gate.md
│   ├── live-tracking.md
│   └── output-templates.md
├── templates/            # 跑通案例 & 假设模板
│   ├── assumptions.example.json      （NVIDIA，2023.6）
│   ├── report.example.md             （完整 NVIDIA 研报）
│   ├── tencent.assumptions.json      （腾讯核心 DCF）
│   ├── tencent.sotp.json             （腾讯 SOTP 桥梁）
│   ├── financials.example.json       （大型银行）
│   ├── cyclical.freeport.json        （Freeport-McMoRan）
│   ├── young.example.json            （亏损/成长型）
│   ├── mature.example.json           （成熟/衰退型）
│   ├── comps.example.json
│   └── freeport.figs/                （示例图表输出）
├── tests/                # 单元测试 & 可复现性守卫
├── evals/                # 评估配置
├── docs/                 # 开发 & 优化文档
├── SKILL.md              # 完整 Skill 定义（Claude Code）
├── LICENSE               # MIT
└── README.md
```

---

## 纪律

- 这是**分析，不是个人投资建议。**始终附上免责声明。
- 假设必须**以假设的口吻陈述**，附依据和低/基准/高区间。
- 始终报告**终值占估值总额的百分比**，以及**市价在价值分布中的位置**。
- 给出**安全边际买入区间**（买入以下 / 合理区间 / 高估以上），而非单一目标价。
- **熊案必须和牛案一样严谨。**
- **自我证伪。**明确指出哪一项假设撑着整个结论，以及它在什么临界值上会让论点反转。
- 标注数据日期。陈旧数据是好方法产出坏结论的第一原因。
- **数据置信度分级。**区分经审计财务数据、管理层指引、卖方一致性预期、第三方聚合数据、自有估算。

---

## 致谢

本项目建立在纽约大学 Stern 商学院 **Aswath Damodaran** 教授的公开估值方法论之上。
他的博客 *Musings on Markets* 和开源的电子表格教会了一代人如何给公司估值。
AnalystCollective 将他的六层框架变成了可复现、可脚本化的引擎。

同时融合了以下思想资源：

- **Mauboussin & Rappaport** —— *Expectations Investing*（逆向 DCF、隐含预测期）
- **SemiAnalysis** —— 自下而上的供应链建模（产能上限 → 出货量 × 均价）
- **卖方一致性方法** —— 分业务线建模 → EPS → 估值倍数分解
- **Buffett / Munger** —— 所有者盈余、安全边际、护城河韧性
- **Dalio** —— 周期定位（周期股/大宗商品）

---

## License

MIT —— 见 [LICENSE](LICENSE)。自由使用、Fork、部署到生产环境。署名致谢。

---

<p align="center">
  <sub>非投资建议。所有估值对假设高度敏感——首当其冲是资本成本。</sub>
  <br>
  <sub><a href="README.md">English README</a> · <a href="https://github.com/Alyosha28/equity-research-analyst">GitHub</a></sub>
</p>
