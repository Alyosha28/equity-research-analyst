# Segment-Level SOTP (Operating-Segment Sum-of-the-Parts)

> **适用场景**: 软硬一体的运营公司 (XPEV/NVDA/TSLA/BYD)——非 holding-co，无投资组合
> haircut，无 holding_company_discount。各分部独立估值后加总。
> **不适用**: 控股型公司 (Tencent/SoftBank/Berkshire)——参见 `holding-company-sotp.md`。
>
> **关联失败**: F4 (分部 SOTP 真空)——既有 `holding-company-sotp.md` 仅覆盖控股型，
> 本文档填补 operating-segment SOTP 真空。

---

## §1 何时用 operating-segment SOTP

### 触发信号 (满足任一即触发，**不设上限**)

1. **公司同时披露 Auto revenue + Software & Services revenue**，且软件收入 material
   (>5%，**无上限**)。示例: XPEV (FY2025 软件 ~5%, FY2026E ~8-10%)、TSLA (FSD + 服务)
2. **公司披露多个分部且各分部经济特性显著不同**——资本密集度差异 >2x、利润率差异 >5pp
   (如重资产 Auto margin 5% vs 轻资产 Software margin 60%)
3. **分析师判断单一 DCF 无法反映业务组合价值**——需在 narrative 说明原因

### 不设上限的理由

软件收入占比 40% 的公司同样适用——只要分部经济特性不同 (资本密集度、利润率、增长曲线)，
就应分别估值。硬编码 "5%-30% 触发上限" 会让 35% 软件收入的公司漏掉 SOTP，错失价值披露。

### 何时不适用

- 纯软件公司 (MSFT/CRM/ADBE): 单一 DCF 已足够，软件内部业务线 (Productivity vs Cloud)
  经济特性相近，无需 SOTP
- 纯硬件公司 (INTC 制造业务): 单一 DCF 已足够
- 业务分部经济特性相近 (BYD 的电池 vs 整车): 单一 DCF 可反映——除非披露的财务数据
  显示利润率差异 >5pp 且资本密集度差异 >2x，否则不必 SOTP

### 反例: 不要因为软件业务就归入 Holding-co

软硬一体公司 (XPEV/NVDA/TSLA) 的 archetype 仍归 Default/Young/Cyclical (按生命周期)，
但通过 `classify-archetype` 输出 `multi_segment: true` flag 触发 segment-level SOTP。
**不要因为公司有软件业务就归入 Holding-co**——Holding-co 的本质是"运营业务 + 投资组合"，
而软硬一体是"运营业务 A + 运营业务 B"。

---

## §2 与 holding-company SOTP 的区别

| 维度 | Holding-co SOTP | Operating-segment SOTP |
|------|----------------|------------------------|
| **公司类型** | 控股型 (Tencent/SoftBank) | 软硬一体运营型 (XPEV/NVDA) |
| **必填字段** | `core_assumptions_path` 或 `core_operating_value` | `operating_segments` (tuple) |
| **互斥** | 与 `operating_segments` 互斥 | 与 `core_*` 互斥 |
| **portfolio** | 有 (`listed_investments` / `unlisted_investments` + haircuts) | 无 (`portfolio_value = 0`) |
| **holding_company_discount** | 有 (applied to post-haircut portfolio) | 无 |
| **算法** | core (DCF) + portfolio (with haircuts) + net_cash - minority | Σ segment_value + net_cash - minority |
| **stub 交叉校验** | 有意义 (剥离 portfolio 看市场给 core 的 P/E) | 意义不大 (无 portfolio 可剥离) |
| **触发条件** | archetype == "holding-co" | `multi_segment: true` flag (A5) |
| **参考文档** | `holding-company-sotp.md` | `segment-level-sotp.md` (本文档) |

**核心区别**: holding-co SOTP 关注 "core vs portfolio" 的价值分离；operating-segment SOTP
关注 "segment A vs segment B" 的价值分离。前者剥离投资组合看运营业务隐含 P/E；后者
加总不同经济特性的分部得出整体公允价值。

---

## §3 段间去重 (避免重复计算)

**风险**: 若 Auto 段的 DCF 已包含软件收入 (如车机软件订阅随车销售)，再单独估值 Software
段会导致同一笔收入被计算两次。

### 去重规则

1. **明确分部边界**——Auto 段只含硬件 + 随车软件 (无法独立计费的部分)；Software 段只含
   独立计费的软件/服务 (TSLA FSD 一次性付费、VW 技术授权、XPEV XNGP 订阅)
2. **检查分部收入总和 vs 公司总营收**——若 Σ segment_revenue > total_revenue，必有重叠
3. **narrative 必须说明分部划分依据**——"Auto 段包含 X/Y/Z 收入，Software 段包含 A/B/C
   收入，二者互斥，加总 = 公司总营收"

### XPEV 示例

- Auto 段: 整车销售收入 + 随车配件 + 维修服务 (约 95% 营收)
- Software 段: 大众技术授权费 + XNGP 订阅 (约 5% 营收，FY2026E 8-10%)
- 互斥校验: Auto 95% + Software 5% = 100%，无重叠

---

## §4 估值方法选择 (per segment)

### 决策树

```
段是否产生正自由现金流且已盈利？
├─ 是 → DCF (适用于成熟重资产段，如 XPEV Auto、TSLA Auto)
└─ 否 → 段是否高速增长且 EV/EBITDA 不可用？
        ├─ 是 → EV/Sales (适用于早期高增长软件段，如 XPEV Software、TSLA FSD)
        │       **必须填 `_comps_source` 字段** (F4 framework)
        └─ 否 → EV/EBITDA (适用于中期段，EBITDA 已转正但 FCF 仍负)
```

### 各方法详解

#### DCF (适用于成熟重资产段)
- **何时用**: 段已盈利、产生正 FCF、可预测 10 年 FCFF 路径
- **字段**: `assumptions_path` 指向独立 DCF JSON (使用 `ValuationInputs` 完整字段)
- **段 JSON 结构**: 与公司级 `assumptions.json` 相同 (但只含本段收入/margin/capital)
- **路径解析**: `load_sotp()` 自动解析 `assumptions_path` 为绝对路径 (相对于 sotp JSON 所在目录)

#### EV/Sales (适用于早期高增长软件段)
- **何时用**: 段高速增长但尚未盈利；EV/EBITDA 不可用 (EBITDA 为负)
- **字段**: `revenue` (¥M) + `ev_sales_multiple` + `_comps_source` (必填)
- **`_comps_source` 结构** (F4 framework 强制):
  ```json
  {
    "_comps_source": {
      "peer_set": ["TSLA FSD", "MBLY", "APTV", "STM ADAS"],
      "peer_ev_sales_multiples": [12.5, 9.8, 7.2, 6.5],
      "peer_median": 8.5,
      "peer_range_low": 6.5,
      "peer_range_high": 12.5,
      "selected_multiple": 8.0,
      "selection_rationale": "取 peer 中位 8.5x 的 94%，反映小鹏软件业务规模较小、商业化早期、需付大众技术授权费的折扣",
      "comps_fetched_at": "2026-06-30",
      "comps_source": "CapIQ / Bloomberg peer comp set"
    }
  }
  ```
- **缺失 `_comps_source`** → `warnings.warn` "倍数不可追溯"——框架化要求，不阻断

#### EV/EBITDA (适用于中期段)
- **何时用**: EBITDA 已转正但 FCF 仍负 (高资本支出期)
- **字段**: `ebitda` (¥M) + `ev_ebitda_multiple`
- **建议**: 也填 `_comps_source` (与 EV/Sales 同样规则)；framework 暂不强制 (后续可加)

### 多方法混合示例

XPEV:
- Auto 段: DCF (成熟重资产，FY2025 已盈利)
- Software 段: EV/Sales (高增长早期，EBITDA 仍负)

NVDA:
- Data Center / AI 段: DCF (成熟，FCF 强劲)
- Gaming 段: EV/EBITDA (中期，EBITDA 稳定但 FCF 受制程迭代影响)
- Automotive 段: EV/Sales (早期，EBITDA 负)

---

## §5 Worked example 框架

### XPEV (软硬一体)

```
sotp.json (路径: data/xpev/xpev_sotp.json)
{
  "_about": "XPeng Inc. operating-segment SOTP — June 2026",
  "company": "XPeng Inc.",
  "valuation_currency": "RMB", "report_currency": "USD",
  "fx_report_per_valuation": 0.138,
  "shares_outstanding": 1904.0,
  "market_price_report_ccy": 13.30,
  "operating_segments": [
    {"name": "Auto", "assumptions_path": "xpev_auto_assumptions.json", "valuation_method": "dcf"},
    {"name": "Software & Services", "assumptions_path": "xpev_software_assumptions.json", "valuation_method": "ev_sales"}
  ],
  "net_cash": 27090.0,
  "minority_interests": 800.0
}

Auto 段 (xpev_auto_assumptions.json): 完整 ValuationInputs，sales_to_capital 0.90, target_margin 6%
Software 段 (xpev_software_assumptions.json): {"revenue": 12000, "ev_sales_multiple": 8.0, "_comps_source": {...}}

预期输出:
- Auto DCF value: ~¥280,000M
- Software EV/Sales: 12000 * 8.0 = ¥96,000M
- Total segment value: ~¥376,000M
- + net_cash: ¥27,090M
- - minority_interests: ¥800M
- = SOTP equity: ~¥402,290M
- per_share_val: ~¥211M / 1904 shares = ~¥211/股
- per_share_report (USD): 211 * 0.138 = ~$29.1/ADS (待 B1-B3 精算)
```

### BYD (单一 DCF 即可，反例)

BYD 虽有电池 + 整车 + 电子三业务，但:
- 电池 90% 内部供应 (随车销售，无法独立计费)
- 电子业务规模小 (<5%) 且利润率与整车相近

→ 不触发 `multi_segment: true`，单一 DCF 即可反映组合价值。

### NVDA (多方法混合)

```
operating_segments: [
  {"name": "Data Center / AI", "assumptions_path": "nvda_dc.json", "valuation_method": "dcf"},
  {"name": "Gaming", "ebitda": 8000, "ev_ebitda_multiple": 15.0, "valuation_method": "ev_ebitda"},
  {"name": "Automotive", "revenue": 1500, "ev_sales_multiple": 12.0, "_comps_source": {...}, "valuation_method": "ev_sales"}
]
```

---

## §6 反例与禁忌

### ❌ 硬编码 EV/Sales 倍数
```json
{"name": "Software", "revenue": 5000, "ev_sales_multiple": 8.0, "valuation_method": "ev_sales"}
```
**问题**: 8.0x 凭感觉填，无 peer 来源。
**正确**: 必须填 `_comps_source` 字段 (peer_set / peer_median / selected_multiple / selection_rationale)。

### ❌ 分部收入重叠
```json
"Auto": {"revenue": 40000}, "Software": {"revenue": 8000}  // 公司总营收 42000
```
**问题**: 8000 中可能已含在 Auto 的随车软件收入 (40000) 中——重复计算。
**正确**: 明确分部边界 (Auto 含随车软件 39500 + Software 独立 8000，总营收 47500；
或 Auto 仅硬件 40000 + Software 仅独立 8000，总营收 48000；二选一)。

### ❌ 用 holding-co SOTP 处理软硬一体公司
```json
{"core_assumptions_path": "xpev_auto.json", "listed_investments": 0, "holding_company_discount": 0}
```
**问题**: 把 Software 段强行塞进 core (单一 DCF) 或视为 portfolio (不合理)。
**正确**: 用 `operating_segments` 字段，分别估值。

### ❌ 触发条件硬编码
```python
if software_revenue_pct > 0.05 and software_revenue_pct < 0.30:
    trigger_sotp()
```
**问题**: 35% 软件收入的公司漏掉 SOTP。
**正确**: 不设上限——只要分部经济特性不同，触发 SOTP。
