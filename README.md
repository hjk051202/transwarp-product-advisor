# 星环产品选型助手（Transwarp Product Advisor）

一个面向星环科技产品售前场景的 **LangChain + RAG + Tool Calling + MCP** 简历项目。

> 场景设定：星环科技（南京）产品售前演示，非官方项目。

> 客户想买数据平台，但星环产品线多：ArgoDB、TDH、TDC、Sophon、StellarDB、KunDB……  
> 助手根据行业、数据量、业务负载和国产化要求，查产品资料、做对比、找案例，并把每次问答保存成**历史会话**。

---

## 当前状态

**v1.0：可本地运行的 Streamlit 单进程 Demo。**

已实现：

- **RAG**：12 份知识文档（10 份 Markdown + 2 份 PDF），Chroma + BM25 混合检索 + RRF 融合 + 可选 cross-encoder 重排 + 页码引用；Embedding 默认离线 Hashing，可切 BGE-M3/OpenAI 兼容接口
- **Tool Calling**：5 个 LangChain 原生工具
  - `search_knowledge`
  - `list_products`
  - `compare_products`
  - `search_cases`
  - `check_compatibility`
- **LangChain Agent**：`create_agent` 统一调度 RAG 和产品工具
- **MCP**：`history-mcp` 暴露 `save_conversation` / `get_conversation` / `list_conversations`，Streamable HTTP 接入
- **历史会话**：每次问答自动保存到 SQLite；Streamlit 有「历史会话」页面
- **多轮上下文**：当前会话最近 8 条消息会传给 Agent，支持“我给了你了呀”这类追问；刷新页面不自动恢复上下文
- **Streamlit 直连**：UI 直接调用 `fieldops.service`，没有 FastAPI、没有 HTTP API、没有 API Key
- **审计日志**：内部记录 request_id、actor、action、resource、detail（当前没有单独的审计页面）
- **适配层**：历史会话支持 `mcp / http / local`，产品目录支持 `json / http`
- **测试**：15 个 pytest 用例通过
- **评测**：
  - RAG：26 条问题，纯向量 Recall@4 = 20/26，混合检索 Recall@4 = 25/26
  - 端到端：20 条问题，citation/answer/history 均 20/20

> 没有模型 API Key 时，项目使用 `ProductAdvisorModel` 做确定性工具调用，**仍然走 LangChain `create_agent`**，所以离线可运行、可测试。配置 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY` 后自动切换真实模型。
>
> 真实模型路径已实现，但当前开发环境没有 API Key，未做真实模型端到端验证；评测数字来自离线 mock 路径。

---

## 这个项目解决什么问题

星环产品线覆盖数据库、大数据平台、数据云、AI 平台、图数据库和交易数据库。售前常见问题是：

1. **产品多，客户不知道选哪个**：ArgoDB 还是 TDH？TDC 和 TDH 有什么区别？
2. **资料散**：产品页、白皮书、案例、兼容性说明分散，查起来慢。
3. **历史咨询留不下来**：客户上次问过什么、助手给过什么建议，关掉页面就没了。
4. **不能乱承诺**：价格、版本、兼容性必须谨慎，不能让模型直接编。

对应到技术栈：

| 技术 | 解决的实际问题 | 项目里的实现 |
|---|---|---|
| **LangChain** | 选型咨询是多步流程：问需求 → 查资料 → 对比 → 找案例 | `create_agent` 统一调度工具 |
| **RAG** | 产品资料、案例、兼容性散落，模型容易记错 | Chroma 检索 + 产品/章节/页码引用 |
| **Tool Calling** | 产品对比、案例、兼容性不能靠模型记忆 | 5 个原生工具 |
| **MCP** | 历史会话要跨进程持久化、可复用 | `history-mcp` 暴露保存/查询会话 |
| **历史会话** | 用户关闭页面后还能回看之前问过什么 | `conversations` 表 + 历史会话页面 |

一句话：

> LangChain 管“流程怎么编排”，RAG 管“产品资料从哪来”，Tool Calling 管“对比/案例/兼容性怎么查”，MCP 管“历史会话怎么存”，SQLite 管“聊过什么”。

---

## 产品范围

| 产品 | 定位 | 典型场景 |
|---|---|---|
| **ArgoDB** | 分布式分析型数据库 / 湖仓集一体 | 数据仓库、BI 报表、实时分析、HTAP |
| **TDH** | 一站式大数据基础平台 | 数据湖、多模分析、实时流、平台级数据底座 |
| **TDC** | 云原生数据云平台 | 多租户数据云、数据 PaaS、平台运营 |
| **Sophon** | 智能分析 / 数据科学平台 | 机器学习、知识图谱、边缘智能、隐私计算 |
| **StellarDB** | 分布式图数据库 | 反欺诈、资金流向、集团派系、知识图谱 |
| **KunDB** | 分布式交易型数据库 | 高并发 OLTP、核心交易、业务库国产化 |

公开资料参考：

- [ArgoDB 产品页](https://www.transwarp.cn/product/argodb)
- [TDH 产品页](https://www.transwarp.cn/product/tdh)
- [Sophon 产品页](https://www.transwarp.cn/product/sophon)
- [StellarDB 产品页](https://www.transwarp.cn/product/stellardb)

---

## 架构

```text
┌────────────────────────────────────┐
│ Streamlit UI (app.py)              │
│ 选型咨询 / 引用 / 工具轨迹 / 历史     │
└───────────────┬────────────────────┘
                │ 直接 Python 调用
┌───────────────▼────────────────────┐
│ fieldops.service.chat              │
└───────────────┬────────────────────┘
                │
┌───────────────▼────────────────────┐
│ LangChain create_agent             │
│ ProductAdvisorModel / DeepSeek     │
└───┬──────────────┬─────────────┬───┘
    │              │             │
┌───▼────┐   ┌─────▼──────┐  ┌───▼─────────────┐
│ Chroma │   │ Catalog    │  │ HistoryAdapter  │
│ RAG    │   │ json/http  │  │ mcp/http/local  │
└────────┘   └─────┬──────┘  └───┬─────────────┘
                   │             │
             ┌─────▼─────┐  ┌────▼──────────┐
             │ products  │  │ history-mcp   │
             │ cases     │  │ save/get/list │
             │ compat    │  └────┬──────────┘
             └───────────┘       │
                            ┌────▼──────┐
                            │ SQLite    │
                            │ history   │
                            └───────────┘
```

---

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

启动 history MCP Server：

```powershell
$env:MCP_TRANSPORT = "streamable-http"
python -m mcp_server.history_server
```

另开一个终端，启动 UI：

```bash
streamlit run app.py
```

打开 <http://127.0.0.1:8501>。

或者 Windows 一键：

```powershell
.\run.ps1
```

`run.ps1` 只启动 **history-mcp + Streamlit**，不再启动 FastAPI。

### 演示步骤

输入：

```text
我们是城商行，TB 级数据，主要做报表和风控分析，ArgoDB 和 TDH 怎么选？
```

然后：

1. 查看选型建议、产品对比、金融案例和引用
2. 每次问答会自动保存一条历史会话
3. 左侧切到 **历史会话**
4. 点开之前的问答，回看用户问题、助手回答和引用

如果只输入：

```text
我选择什么产品比较好？
```

助手不会乱推产品，也不会贴 FAQ，而是先问：

- 主要负载是什么？
- 数据量多大？
- 是否有国产化/部署要求？

然后给一个初步方向。

---

## 配置

| 环境变量 | 默认值 | 作用 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 空 | 使用 DeepSeek 真实模型 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名 |
| `OPENAI_API_KEY` | 空 | 使用 OpenAI 真实模型 |
| `HISTORY_MCP_URL` | `http://127.0.0.1:8765/mcp` | MCP 地址 |
| `HISTORY_ADAPTER` | `mcp` | `mcp` / `http` / `local` |
| `HISTORY_HTTP_URL` | `http://127.0.0.1:9000` | 真实历史服务地址 |
| `CATALOG_ADAPTER` | `json` | `json` / `http` |
| `CATALOG_HTTP_URL` | `http://127.0.0.1:9100` | 真实产品目录地址 |
| `RAG_SCORE_THRESHOLD` | `0.30` | 向量相关性拒答阈值 |
| `EMBEDDING_PROVIDER` | `auto` | `auto` / `hashing` / `openai` / `openai-compatible` |
| `EMBEDDING_MODEL` | 按 provider 决定 | `auto` 默认 `BAAI/bge-m3`；`openai` 默认 `text-embedding-3-small` |
| `EMBEDDING_BASE_URL` | 按 provider 决定 | `auto` 默认 SiliconFlow；`openai` 默认 OpenAI |
| `EMBEDDING_API_KEY` | 空 | Embedding API Key；`openai` 模式可回退 `OPENAI_API_KEY` |
| `EMBEDDING_DIMENSIONS` | 空 | 可选，指定向量维度 |
| `RERANK_ENABLED` | `0` | 是否启用 cross-encoder 重排 |
| `RERANK_MODEL` | `BAAI/bge-reranker-v2-m3` | 重排模型 |
| `RERANK_BASE_URL` | `https://api.siliconflow.cn/v1` | 重排接口 |
| `RERANK_API_KEY` | 空 | 重排 API Key |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8765` | MCP 监听地址 |

真实模型：

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
streamlit run app.py
```

---

## 评测与测试

### RAG 检索

```bash
python eval/run_eval.py
python eval/compare_retrieval.py
python eval/compare_retrieval.py --questions eval/holdout_questions.jsonl
```

当前：

```text
Recall@4 (doc)  = 25/26 = 96.15%
Page hit@4      = 25/26 = 96.15%

vector Recall@4 = 20/26 = 76.92%
hybrid Recall@4 = 25/26 = 96.15%

holdout（14 条改写问题）:
vector Recall@4 = 14/14 = 100.00%
hybrid Recall@4 = 14/14 = 100.00%
```

> 26 条里 `q23`（“只有 GB 级数据，还需要上 TDH 吗？”）未命中：Top-4 被 TDH 产品文档占据，选型指南没有进前四。没有为了凑 100% 调整期望。

RAG 优化点：

1. **BM25 + 向量混合召回**：向量负责语义相近，BM25 负责产品名、数字、专有名词的精确匹配。
2. **RRF 融合**：只融合两路排名，不直接相加余弦分和 BM25 分，避免量纲不一致。
3. **产品/选型指南加权**：问题里出现产品名时给对应产品文档小加权；问“组合/定位”时给选型指南加权。
4. **可选 cross-encoder 重排**：配置 `RERANK_ENABLED=1` 后调用 `bge-reranker-v2-m3`，未配置或接口失败时回退 RRF 顺序。
5. **拒答**：问题不在星环产品域，或向量相关性低于 `RAG_SCORE_THRESHOLD` 时，返回“知识库未命中”，不硬编答案。

### Embedding 配置

默认 `EMBEDDING_PROVIDER=auto`：

- 配置了 `EMBEDDING_API_KEY` → 使用 OpenAI 兼容接口（默认 SiliconFlow `BAAI/bge-m3`）
- 没有 Key → 自动回退 `HashingEmbeddings`，保证离线可跑

切换到外部 Embedding：

```powershell
$env:EMBEDDING_PROVIDER = "openai"
$env:EMBEDDING_MODEL = "BAAI/bge-m3"
$env:EMBEDDING_BASE_URL = "https://api.siliconflow.cn/v1"
$env:EMBEDDING_API_KEY = "sk-..."
# 可选：$env:EMBEDDING_DIMENSIONS = "1024"
```

强制离线：

```powershell
$env:EMBEDDING_PROVIDER = "hashing"
```

说明：

- 切换 Embedding 后，`.chroma` 会因 manifest 签名变化自动重建索引。
- 当前仓库的 25/26 指标是 **HashingEmbeddings** 下测得的；外部 BGE-M3 未在本环境实际调用验证。
- 配置后可先验证：

```bash
python scripts/check_embedding.py
```

### 端到端

```bash
python eval/run_e2e.py
```

当前：

```text
citation_hit@4  = 20/20 = 100.00%
answer_keyword  = 20/20 = 100.00%
history_saved   = 20/20 = 100.00%
```

**说明**：这是 12 篇文档、20 条问题的**小型合成评测**，100% 只能证明链路可用，不能说明真实售前场景的泛化能力。面试时要主动说明语料规模和 mock 模型限制。

### 测试

```bash
pytest -q
```

当前：`15 passed`（启动 history MCP 时）；MCP 未启动时 `14 passed, 1 skipped`。

---

## 项目结构

```text
fieldops-copilot/
├─ app.py                       # Streamlit UI，直接调用 service
├─ fieldops/
│  ├─ agent.py                  # create_agent + 模型选择
│  ├─ mock_llm.py               # 无 API Key 时的确定性产品顾问模型
│  ├─ rag.py                    # Chroma + 混合检索 + Embedding 选择 + 引用
│  ├─ retrieval.py              # BM25 + RRF 融合
│  ├─ reranker.py               # 可选 cross-encoder 重排
│  ├─ ingest.py                 # 语料统计与索引重建
│  ├─ tools.py                  # 5 个产品选型工具
│  ├─ history_client.py         # langchain-mcp-adapters（history）
│  ├─ service.py                # 对话编排 / 历史会话保存 / 审计
│  ├─ audit.py                  # request_id + audit log
│  ├─ db.py                     # SQLite：conversations + audit_log
│  ├─ integrations/
│  │  ├─ history.py             # mcp / http / local 历史适配器
│  │  └─ catalog.py             # json / http 产品目录适配器
│  ├─ data.py                   # 产品/案例/兼容性/知识库读取
│  └─ schemas.py                # Pydantic
├─ mcp_server/
│  └─ history_server.py         # FastMCP：save/get/list conversation
├─ data/
│  ├─ knowledge/                # 10 份产品/选型/案例 Markdown
│  ├─ knowledge/pdf/            # 2 份 PDF
│  ├─ products.json
│  ├─ cases.json
│  └─ compatibility.json
├─ scripts/
│  └─ generate_pdfs.py          # 生成演示 PDF
├─ eval/
│  ├─ questions.jsonl
│  ├─ holdout_questions.jsonl  # 14 条改写问题，验证不退化
│  ├─ e2e_questions.jsonl
│  ├─ run_eval.py
│  ├─ compare_retrieval.py      # 纯向量 vs 混合检索
│  └─ run_e2e.py
├─ tests/                       # 15 个用例
├─ requirements.txt
├─ run.ps1
├─ pytest.ini
└─ README.md
```

---

## 安全与边界

- 没有登录、没有 API Key：这是本地单机 Demo，默认所有历史会话共用同一个 SQLite。
- 如果部署到多人环境，需要自己加用户 ID / 登录 / 权限。
- 产品资料来自公开页面并做了摘要，具体版本、价格、兼容性以星环科技官方资料为准。
- 演示数据中的客户名称均为匿名化/虚构，不代表真实客户。
- `HttpHistoryAdapter` / `HttpCatalogAdapter` 是适配器骨架，未对接真实历史服务/产品目录。
- 真实模型路径未验证；离线 mock 模型只覆盖预设场景。

---

## 简历写法

**星环产品选型助手｜LangChain + RAG + Tool Calling + MCP｜个人项目**

- 基于 LangChain 1.x `create_agent` 构建星环产品选型 Agent，统一调度 RAG 和 5 个产品工具，完成“需求澄清 → 产品对比 → 案例/兼容性”的闭环。
- 将 RAG 从纯向量升级为 **BM25 + 向量混合检索**，用 **RRF** 融合两路排名，并加入产品词/选型指南加权、领域拒答和可选 cross-encoder 重排；自建对比评测中 Recall@4 从 20/26 提升到 25/26。
- 设计产品资料 RAG 链路，按章节切分并保留产品、版本、页码元数据；20 条端到端评测 citation/answer/history 均 20/20。
- 将历史会话封装为 MCP Server，通过 `langchain-mcp-adapters` 以 Streamable HTTP 暴露保存/查询会话；抽象 `mcp/http/local` 三种历史适配器。
- 使用 Streamlit 实现单进程本地 Demo，支持产品选型、引用来源、工具调用轨迹、当前会话多轮上下文和历史会话回看；15 个 pytest 用例覆盖 RAG、工具、MCP 与适配器。

> 指标请写你实测的数字；当前评测是小样本合成集，面试时主动说明语料规模和 mock 模型限制。

---

## Roadmap

- [x] v0.1：Streamlit UI + Mock 流程
- [x] v0.2：Chroma RAG + 产品工具 + LangChain Agent
- [x] v1.0：PDF 入库 + 历史会话 + MCP
- [x] v1.1：BM25 + RRF 混合检索 + 可选重排 + 拒答
- [ ] v1.2：真实模型端到端评测
- [ ] v1.3：接入真实产品目录/历史服务 API
- [ ] v1.4：多用户历史隔离、权限分级

---

## 数据说明

产品资料来自星环科技公开页面，经过摘要和改写用于演示；客户、案例、兼容性均为匿名化/演示数据，不代表真实合同、报价或承诺。

---

## License

MIT
