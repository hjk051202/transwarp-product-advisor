---
doc_id: tw-argodb
title: Transwarp ArgoDB 产品概览
product: ArgoDB
doc_type: product
version: public-2026
section: 产品定位与适用场景
page: 1
source_url: https://www.transwarp.cn/product/argodb
---

## ArgoDB 是什么

Transwarp ArgoDB 是星环科技自主研发的分布式数据库，定位为面向海量数据分析的一体化数据平台，支持多模型、湖仓集一体和 HTAP 混合负载。

## 适合什么场景

- 企业级数据仓库、数据集市、报表分析
- 实时报表、实时大屏、实时风控
- 高并发点查与复杂分析并存的 HTAP 场景
- 同城/异地容灾、多租户数据平台
- 国产化替换：兼容标准 SQL，兼容 MySQL、Oracle 等方言

## 关键能力

- 批流融合分析，入库即分析
- 向量化引擎，高并发复杂分析
- 弹性扩缩容，多租户资源隔离
- 支持 x86、ARM 混合部署
- 基于 Raft 的存储引擎，自动故障迁移

## 什么时候优先推荐

客户需求以“报表、数仓、实时分析、湖仓、HTAP”为主，且希望用一套分布式数据库替代 Hadoop+MPP 混合架构时，优先推荐 ArgoDB。

如果客户的核心是高频 OLTP 交易，应评估 KunDB；如果需要平台级多模数据湖和大量组件，应评估 TDH。
