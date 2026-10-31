# 星环产品选型助手（Transwarp Product Advisor）

一个面向星环科技产品售前场景的 **LangChain + RAG + Tool Calling + MCP** 简历项目。

> 客户想买数据平台，但星环产品线多：ArgoDB、TDH、TDC、Sophon、StellarDB、KunDB……  
> 助手根据行业、数据量、业务负载和国产化要求，查产品资料、做对比、找案例，最后生成一条**待人工确认**的售前线索。

> 说明：这是一个基于**公开产品资料**的演示项目，不代表星环科技真实内部系统、真实客户或真实报价。产品定位以星环科技官网为准。

---

## 当前状态

**v1.0：可本地运行的端到端 Demo。**

已实现：

- **RAG**：12 份知识文档（10 份 Markdown + 2 份 PDF），Chroma 检索 + 关键词/产品重排 + 页码引用
- **Tool Calling**：6 个 LangChain 原生工具
  - `search_knowledge`
  - `list_products`
  - `compare_products`
  - `search_cases`
  - `check_compatibility`
  - `draft_lead`
- **LangChain Agent**：`create_agent` 统一调度 RAG、产品工具和 MCP 工具
- **MCP**：`crm-mcp` 暴露 `create_lead` / `get_lead`，Streamable HTTP 接入
- **HITL**：Agent 只生成线索草稿；售前确认后才写入 CRM
- **FastAPI**：`/chat`、`/leads`、`/leads/{id}/approve`、`/audit`、`/health`
- **API Key 鉴权**：配置 `FIELDOPS_API_KEY` 后保护业务接口
- **审计日志**：记录 request_id、actor、action、resource、detail
- **适配层**：CRM 支持 `mcp / http / local`，产品目录支持 `json / http`
- **Streamlit**：选型咨询、引用来源、工具轨迹、线索草稿、技术栈说明
- **测试**：15 个 pytest 用例通过
- **评测**：
  - RAG：16 条问题，Recall@4 = 16/16
  - 端到端：20 条问题，citation/answer/lead 均 20/20，p50 = 29ms

> 没有模型 API Key 时，项目使用 `ProductAdvisorModel` 做确定性工具调用，**仍然走 LangChain `create_agent`**，所以离线可运行、可测试。配置 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY` 后自动切换真实模型。
>
> 真实模型路径已实现，但当前开发环境没有 API Key，未做真实模型端到端验证；评测数字来自离线 mock 路径。

---

## 这个项目解决什么问题

星环产品线覆盖数据库、大数据平台、数据云、AI 平台、图数据库和交易数据库。售前常见问题是：

1. **产品多，客户不知道选哪个**：ArgoDB 还是 TDH？TDC 和 TDH 有什么区别？
2. **资料散**：产品页、白皮书、案例、兼容性说明分散，查起来慢。
3. **线索容易丢**：客户表达试用/报价意向后，没有及时转成 CRM 线索。
4. **不能乱承诺**：价格、版本、兼容性必须谨慎，不能让模型直接编。

对应到技术栈：

| 技术 | 解决的实际问题 | 项目里的实现 |
|---|---|---|
| **LangChain** | 选型咨询是多步流程：问需求 → 查资料 → 对比 → 找案例 → 留资 | `create_agent` 统一调度工具 |
| **RAG** | 产品资料、案例、兼容性散落，模型容易记错 | Chroma 检索 + 产品/章节/页码引用 |
| **Tool Calling** | 产品对比、案例、兼容性不能靠模型记忆 | 6 个原生工具 |
| **MCP** | CRM 是外部系统，留资要认证、审计、复用 | `crm-mcp` 暴露建线索/查线索 |
| **HITL** | 线索写错会影响销售跟进 | Agent 只出 draft，售前确认后才写 CRM |
| **审计** | 出问题要能追溯谁让 Agent 做了什么 | request_id + actor + action + resource + detail |

一句话：

> LangChain 管“流程怎么编排”，RAG 管“产品资料从哪来”，Tool Calling 管“对比/案例/兼容性怎么查”，MCP 管“CRM 怎么接”，HITL 管“线索怎么写才不闯祸”。

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
│ Streamlit UI                       │
│ 选型咨询 / 引用 / 工具轨迹 / 线索     │
└───────────────┬────────────────────┘
                │ HTTP + X-API-Key
┌───────────────▼────────────────────┐
│ FastAPI                            │
│ auth / request_id / audit          │
│ /chat /leads /audit /health        │
└───────────────┬────────────────────┘
                │
┌───────────────▼────────────────────┐
│ LangChain create_agent             │
│ ProductAdvisorModel / DeepSeek     │
└───┬──────────────┬─────────────┬───┘
    │              │             │
┌───▼────┐   ┌─────▼──────┐  ┌───▼─────────────┐
│ Chroma │   │ Catalog    │  │ CRMAdapter      │
│ RAG    │   │ json/http  │  │ mcp/http/local  │
└────────┘   └─────┬──────┘  └───┬─────────────┘
                   │             │
             ┌─────▼─────┐  ┌────▼──────────┐
             │ products  │  │ crm-mcp       │
             │ cases     │  │ create/get    │
             │ compat    │  └────┬──────────┘
             └───────────┘       │
                            ┌────▼──────┐
                            │ SQLite    │
                            │ leads +   │
                            │ audit     │
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

启动 CRM MCP Server：

```powershell
$env:MCP_TRANSPORT = "streamable-http"
python -m mcp_server.crm_server
```

启动 FastAPI：

```bash
uvicorn fieldops.main:app --host 127.0.0.1 --port 8000
```

启动 UI：

```bash
streamlit run app.py
```

打开 <http://127.0.0.1:8501>。

或者 Windows 一键：

```powershell
.\run.ps1
```

### 演示步骤

输入：

```text
我们是城商行，TB 级数据，主要做报表和风控分析，ArgoDB 和 TDH 怎么选？
```

然后：

1. 查看选型建议、产品对比、金融案例和引用
2. 左侧切到 **线索草稿**
3. 核对客户、行业、需求和推荐产品
4. 点击 **批准并写入 CRM**
5. 通过 `crm-mcp.create_lead` 写入 SQLite，返回 `CRM-...`

---

## 配置

| 环境变量 | 默认值 | 作用 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 空 | 使用 DeepSeek 真实模型 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名 |
| `OPENAI_API_KEY` | 空 | 使用 OpenAI 真实模型 |
| `FIELDOPS_API_KEY` | 空 | 设置后启用 API Key 鉴权 |
| `CRM_MCP_URL` | `http://127.0.0.1:8765/mcp` | MCP 地址 |
| `CRM_ADAPTER` | `mcp` | `mcp` / `http` / `local` |
| `CRM_HTTP_URL` | `http://127.0.0.1:9000` | 真实 CRM REST 地址 |
| `CATALOG_ADAPTER` | `json` | `json` / `http` |
| `CATALOG_HTTP_URL` | `http://127.0.0.1:9100` | 真实产品目录地址 |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8765` | MCP 监听地址 |

真实模型：

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
uvicorn fieldops.main:app --port 8000
```

---

## API 与鉴权

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/health` | 模式、MCP 工具、鉴权状态 |
| `POST` | `/chat` | 选型咨询，返回 answer / citations / tool_trace / lead |
| `GET` | `/leads` | 最近的线索草稿 |
| `GET` | `/leads/{lead_id}` | 查询线索草稿 |
| `POST` | `/leads/{lead_id}/approve` | 人工确认后通过 CRM 适配器写线索 |
| `GET` | `/audit` | 最近审计日志 |

启用鉴权后，除 `/health`、`/docs`、`/openapi.json` 外都需要：

```http
X-API-Key: change-me
```

或：

```http
Authorization: Bearer change-me
```

示例：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: change-me" \
  -d '{"message":"ArgoDB 和 TDH 怎么选？","company":"某城商行","industry":"金融"}'
```

---

## 评测与测试

### RAG 检索

```bash
python eval/run_eval.py
```

当前：

```text
Recall@4 (doc)  = 16/16 = 100.00%
Page hit@4      = 16/16 = 100.00%
```

### 端到端

```bash
python eval/run_e2e.py
```

当前：

```text
citation_hit@4  = 20/20 = 100.00%
answer_keyword  = 20/20 = 100.00%
lead_expect     = 20/20 = 100.00%
p50 latency     = 29 ms
p95 latency     = 61 ms
```

**说明**：这是 12 篇文档、20 条问题的**小型合成评测**，100% 只能证明链路可用，不能说明真实售前场景的泛化能力。面试时要主动说明语料规模和 mock 模型限制。

### 测试

```bash
pytest -q
```

当前：`15 passed`（启动 CRM MCP 时）；未启动 CRM MCP 时为 `14 passed, 1 skipped`。

---

## 项目结构

```text
fieldops-copilot/
├─ app.py                       # Streamlit UI（HTTP 调后端）
├─ fieldops/
│  ├─ main.py                   # FastAPI + auth middleware
│  ├─ agent.py                  # create_agent + 模型选择
│  ├─ mock_llm.py               # 无 API Key 时的确定性产品顾问模型
│  ├─ rag.py                    # Chroma + 哈希 embedding + 产品文档引用
│  ├─ ingest.py                 # 语料统计与索引重建
│  ├─ tools.py                  # 6 个产品选型工具
│  ├─ mcp_client.py             # langchain-mcp-adapters
│  ├─ service.py                # 对话编排 / 线索审批 / 审计
│  ├─ audit.py                  # request_id + audit log
│  ├─ db.py                     # SQLite：leads + audit_log
│  ├─ integrations/
│  │  ├─ crm.py                 # mcp / http / local CRM 适配器
│  │  └─ catalog.py             # json / http 产品目录适配器
│  ├─ data.py                   # 产品/案例/兼容性/知识库读取
│  └─ schemas.py                # Pydantic
├─ mcp_server/
│  └─ crm_server.py             # FastMCP：create/get lead
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
│  ├─ e2e_questions.jsonl
│  ├─ run_eval.py
│  └─ run_e2e.py
├─ tests/                       # 15 个用例
├─ requirements.txt
├─ run.ps1
├─ pytest.ini
└─ README.md
```

---

## 安全与边界

- 默认 `FIELDOPS_API_KEY` 为空时鉴权关闭，仅适合本地开发。
- 产品资料来自公开页面并做了摘要，具体版本、价格、兼容性以星环科技官方资料为准。
- 演示数据中的客户名称均为匿名化/虚构，不代表真实客户。
- 审计日志会记录消息前 160 字；生产环境应做 PII 脱敏。
- `HttpCRMAdapter` / `HttpCatalogAdapter` 是适配器骨架，未对接真实 CRM/产品目录。
- 真实模型路径未验证；离线 mock 模型只覆盖预设场景。

---

## 简历写法

**星环产品选型助手｜LangChain + RAG + Tool Calling + MCP｜个人项目**

- 基于 LangChain 1.x `create_agent` 构建星环产品选型 Agent，统一调度 Chroma RAG、6 个产品工具和 1 个 CRM MCP Server，完成“需求澄清 → 产品对比 → 案例/兼容性 → 线索草稿”的闭环。
- 设计产品资料 RAG 链路，按章节切分并保留产品、版本、页码元数据；16 条检索评测 Recall@4 为 16/16，20 条端到端评测 citation/answer/lead 均 20/20。
- 将 CRM 封装为 MCP Server，通过 `langchain-mcp-adapters` 以 Streamable HTTP 暴露建线索/查线索；抽象 `mcp/http/local` 三种 CRM 适配器，写操作经人工确认后执行。
- 使用 FastAPI + Streamlit 实现前后端分离 Demo，加入 API Key 鉴权、request_id 审计日志；15 个 pytest 用例覆盖 RAG、工具、MCP、鉴权、审计与适配器。

> 指标请写你实测的数字；当前评测是小样本合成集，面试时主动说明语料规模和 mock 模型限制。

---

## Roadmap

- [x] v0.1：Streamlit UI + Mock 流程
- [x] v0.2：Chroma RAG + 产品工具 + LangChain Agent + CRM MCP
- [x] v1.0：PDF 入库 + 20 条端到端评测 + 鉴权/审计 + 适配层
- [ ] v1.1：真实模型端到端评测
- [ ] v1.2：接入真实产品目录/CRM API
- [ ] v1.3：多语言、权限分级、可观测性

---

## 数据说明

产品资料来自星环科技公开页面，经过摘要和改写用于演示；客户、案例、兼容性均为匿名化/演示数据，不代表真实合同、报价或承诺。

---

## License

MIT
