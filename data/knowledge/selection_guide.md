---
doc_id: tw-selection-guide
title: 星环产品选型指南
product: all
doc_type: selection_guide
version: demo-1.0
section: 需求到产品的映射
page: 1
source_url: https://www.transwarp.cn/
---

## 先问四个问题

1. 业务以什么为主：报表分析、在线交易、数据湖、AI 建模、图关系？
2. 数据规模：GB、TB 还是 PB？
3. 部署要求：私有云、混合云、信创环境、多租户运营？
4. 客户最在意什么：性能、国产化、成本、实时性、平台完整性？

## 需求到产品的映射

| 客户需求 | 优先推荐 | 说明 |
|---|---|---|
| 企业级数据仓库、BI 报表、实时分析、HTAP | ArgoDB | 分析型数据库，替代 Hadoop+MPP 混合架构 |
| 数据湖、多模数据、实时流、平台级大数据底座 | TDH | 一站式平台，组件齐全 |
| 多租户数据云、平台运营、云原生数据服务 | TDC | 数据 PaaS + 分析 PaaS + 应用 PaaS |
| 机器学习、知识图谱、边缘智能、隐私计算 | Sophon | AI 分析平台，含 4 个子产品 |
| 反欺诈、资金流向、多层关系、图算法 | StellarDB | 分布式图数据库 |
| 高并发 OLTP、核心交易、业务库国产化 | KunDB | 分布式交易型数据库 |

## 常见组合

- **ArgoDB + TDH**：TDH 做数据湖和多模加工，ArgoDB 做高性能分析
- **TDH + StellarDB + Sophon**：平台 + 图谱 + AI 建模
- **TDC + ArgoDB**：多租户数据云 + 分析型数据库服务
- **KunDB + ArgoDB**：交易与分析分离，HTAP/混合负载

## 回答原则

- 先澄清业务负载，不要一上来就报产品名
- 不要只推最贵的产品，要说明“为什么不是另一个”
- 涉及具体版本、兼容性、报价时，明确说“需以官方兼容性列表和售前确认为准”
