# 设备售后运维助手（FieldOps Copilot）

一个面向工业设备售后场景的 **LangChain + RAG + Tool Calling + MCP** 简历项目。

> 用户报修后，助手检索维修手册、读取实时工况、判断保修/备件，生成一份**待人工确认**的工单草稿；工程师批准后，通过 `cmms-mcp` 写入 CMMS。

![status](https://img.shields.io/badge/status-v1.0-brightgreen)
![python](https://img.shields.io/badge/python-3.12-blue)
![langchain](https://img.shields.io/badge/langchain-1.4-1c3d5a)
![license](https://img.shields.io/badge/license-MIT-green)

---

## v1.0 状态

**v1.0 是一个功能完整的本地 Demo，不是生产认证版本。**

已实现：

- **RAG**：9 份知识文档（6 Markdown + 3 PDF），Chroma 检索 + 关键词重排 + 页码引用
- **Tool Calling**：5 个 LangChain 原生工具
- **LangChain Agent**：`create_agent` 统一调度 RAG、原生工具、MCP 工具
- **MCP**：`cmms-mcp` 暴露 `create_work_order` / `get_work_order`，Streamable HTTP 接入
- **HITL**：Agent 只生成 draft；工程师批准后才写 CMMS
- **FastAPI**：`/chat`、`/work-orders`、`/work-orders/{id}/approve`、`/audit`、`/health`
- **API Key 鉴权**：配置 `FIELDOPS_API_KEY` 后保护业务接口
- **审计日志**：每次对话、审批都会记录 request_id、actor、action、resource、detail
- **适配层**：CMMS 支持 `mcp / http / local`，ERP 支持 `json / http`
- **Streamlit**：对话诊断、引用来源、工具轨迹、工单审批、技术栈说明
- **本地一键启动**：`run.ps1` 拉起 MCP、API、UI 三个进程
- **测试**：15 个 pytest 用例通过
- **评测**：
  - RAG 检索：15 条问题，Recall@4 = 15/15
  - 端到端：20 条问题，citation/answer/draft 均 20/20，p50 = 35ms

> 没有模型 API Key 时，项目使用 `MockToolCallingModel` 做确定性工具调用，**仍然走 LangChain `create_agent`**，所以离线可运行、可测试。配置 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY` 后自动切换真实模型。
>
> 真实模型路径已实现，但当前开发环境没有 API Key，未做真实模型端到端验证；评测数字来自离线 mock 路径。

---

## 这个项目解决什么问题

工业设备售后有三个典型问题：

1. **知识散**：维修手册、SOP、服务公告、历史工单分散，工程师查资料慢。
2. **数据散**：设备实时工况在 IoT 平台，保修在 ERP，备件在另一个系统。
3. **写操作有风险**：建单、订备件、派工都有真实成本，不能让模型直接执行。

对应到技术栈：

| 技术 | 解决的实际问题 | 项目里的实现 |
|---|---|---|
| **LangChain** | 故障处理是多步流程，if/else 会越写越乱 | `create_agent` 统一调度 RAG、业务工具、MCP 工具 |
| **RAG** | 手册长、版本多，模型直接答会编造故障码 | Chroma 检索 + 型号/版本/页码元数据 + 引用 |
| **Tool Calling** | 设备当前温度、转速、保修、库存不在文档里 | 3 个查询工具 + 1 个草稿工具 + 1 个知识检索工具 |
| **MCP** | CMMS 是外部系统，建单要认证、审计、复用 | `cmms-mcp` 暴露建单/查单；Streamable HTTP 接入 |
| **HITL** | 建单、订备件有真实成本，误操作代价高 | Agent 只出 draft，工程师批准后才写 CMMS |
| **审计** | 出问题要能追溯“谁在什么时候让 Agent 做了什么” | request_id + actor + action + resource + detail |

一句话：

> LangChain 管“流程怎么编排”，RAG 管“知识从哪来”，Tool Calling 管“实时数据怎么查”，MCP 管“外部系统怎么接”，HITL 管“写操作怎么不闯祸”。

---

## 架构

```text
┌────────────────────────────────────┐
│ Streamlit UI                       │
│ 对话 / 引用 / 工具轨迹 / 工单审批    │
└───────────────┬────────────────────┘
                │ HTTP + X-API-Key
┌───────────────▼────────────────────┐
│ FastAPI                            │
│ auth middleware / request_id       │
│ /chat /work-orders /audit /health  │
└───────────────┬────────────────────┘
                │
┌───────────────▼────────────────────┐
│ LangChain create_agent             │
│ MockToolCallingModel / DeepSeek    │
└───┬──────────────┬─────────────┬───┘
    │              │             │
┌───▼────┐   ┌─────▼──────┐  ┌───▼─────────────┐
│ Chroma │   │ ERPAdapter │  │ CMMSAdapter     │
│ RAG    │   │ json/http  │  │ mcp/http/local  │
└────────┘   └─────┬──────┘  └───┬─────────────┘
                   │             │
             ┌─────▼─────┐  ┌────▼──────────┐
             │ devices   │  │ cmms-mcp      │
             │ parts     │  │ create/get    │
             │ telemetry │  └────┬──────────┘
             └───────────┘       │
                            ┌────▼──────┐
                            │ SQLite    │
                            │ audit +   │
                            │ workorders│
                            └───────────┘
```

---

## 快速开始

### 方式一：本地运行

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

启动 MCP Server：

```powershell
$env:MCP_TRANSPORT = "streamable-http"
python -m mcp_server.cmms_server
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
X100 报 E-204，出水温度高，客户已停机。
```

然后：

1. 查看诊断、工况、保修、备件和引用
2. 左侧切到 **工单草稿**
3. 审核后点击 **批准并创建工单**
4. 工单通过 `cmms-mcp.create_work_order` 写入 SQLite，返回 `WO-...`
5. 左侧 **技术栈** 查看每项技术解决的实际问题

---

## 配置

| 环境变量 | 默认值 | 作用 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 空 | 使用 DeepSeek 真实模型 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名 |
| `OPENAI_API_KEY` | 空 | 使用 OpenAI 真实模型 |
| `FIELDOPS_API_KEY` | 空 | 设置后启用 API Key 鉴权 |
| `CMMS_MCP_URL` | `http://127.0.0.1:8765/mcp` | MCP 地址 |
| `CMMS_ADAPTER` | `mcp` | `mcp` / `http` / `local` |
| `CMMS_HTTP_URL` | `http://127.0.0.1:9000` | 真实 CMMS REST 地址 |
| `ERP_ADAPTER` | `json` | `json` / `http` |
| `ERP_HTTP_URL` | `http://127.0.0.1:9100` | 真实 ERP/IoT 地址 |
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
| `POST` | `/chat` | 诊断对话，返回 answer / citations / tool_trace / draft |
| `GET` | `/work-orders` | 最近的工单草稿 |
| `GET` | `/work-orders/{draft_id}` | 查询工单草稿 |
| `POST` | `/work-orders/{draft_id}/approve` | 人工批准后通过 CMMS 适配器建单 |
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
  -d '{"message":"X100 报 E-204，出水温度高","serial":"8F2-1042"}'
```

---

## 评测与测试

### RAG 检索

```bash
python eval/run_eval.py
```

当前：

```text
Recall@4 (doc)  = 15/15 = 100.00%
Page hit@4      = 15/15 = 100.00%
```

### 端到端

```bash
python eval/run_e2e.py
```

当前：

```text
citation_hit@4  = 20/20 = 100.00%
answer_keyword  = 20/20 = 100.00%
draft_expect    = 20/20 = 100.00%
p50 latency     = 35 ms
p95 latency     = 90 ms
```

**说明**：这是 9 篇文档、20 条问题的**小型合成评测**，100% 只能证明链路可用，不能说明真实场景的泛化能力。面试时要主动说明语料规模和 mock 模型限制。

### 测试

```bash
pytest -q
```

当前：`15 passed`。

---

## 项目结构

```text
fieldops-copilot/
├─ app.py                       # Streamlit UI（HTTP 调后端）
├─ fieldops/
│  ├─ main.py                   # FastAPI + auth middleware
│  ├─ agent.py                  # create_agent + 模型选择
│  ├─ mock_llm.py               # 无 API Key 时的确定性工具调用
│  ├─ rag.py                    # Chroma + 哈希 embedding + PDF/Markdown 索引
│  ├─ ingest.py                 # 预留的批量入库入口
│  ├─ tools.py                  # 5 个原生工具
│  ├─ mcp_client.py             # langchain-mcp-adapters
│  ├─ service.py                # 对话编排 / 审批 / 审计
│  ├─ audit.py                  # request_id + audit log
│  ├─ db.py                     # SQLite：work_orders + audit_log
│  ├─ integrations/
│  │  ├─ cmms.py                # mcp / http / local 适配器
│  │  └─ erp.py                 # json / http 适配器
│  ├─ data.py                   # Markdown + PDF 数据访问
│  └─ schemas.py                # Pydantic
├─ mcp_server/
│  └─ cmms_server.py            # FastMCP：create/get work order
├─ data/
│  ├─ manuals/                  # 6 份 Markdown
│  ├─ manuals/pdf/              # 3 份 PDF
│  ├─ devices.json
│  ├─ parts.json
│  └─ telemetry.json
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
- 生产环境应把 API Key 放在 Secret Manager，不要提交到 Git。
- 审计日志会记录消息前 160 字；生产环境应做 PII 脱敏。
- `HttpCMMSAdapter` / `HttpERPAdapter` 是适配器骨架，未对接真实 CMMS/ERP。
- 当前 PDF 为 ASCII 示例，中文扫描件需要 OCR（PaddleOCR/Tesseract）。
- 真实模型路径未验证；离线 mock 模型只覆盖预设场景。

---

## 简历写法

**设备售后运维助手｜LangChain + RAG + Tool Calling + MCP｜个人项目**

- 基于 LangChain 1.x `create_agent` 构建设备售后诊断 Agent，统一调度 Chroma RAG、5 个业务工具和 1 个 MCP Server，完成从故障描述到工单草稿的闭环。
- 设计 Markdown/PDF 混合知识入库链路，按标题切分并保留型号、版本、页码元数据；15 条检索评测 Recall@4 为 15/15，20 条端到端评测 citation/answer/draft 均 20/20。
- 将 CMMS 封装为 MCP Server，通过 `langchain-mcp-adapters` 以 Streamable HTTP 暴露建单/查单；抽象 `mcp/http/local` 三种 CMMS 适配器，写操作经人工确认后执行。
- 使用 FastAPI + Streamlit 实现前后端分离 Demo，加入 API Key 鉴权、request_id 审计日志；15 个 pytest 用例覆盖 RAG、工具、MCP、鉴权、审计与适配器。

> 指标请写你实测的数字；当前评测是小样本合成集，面试时主动说明语料规模和 mock 模型限制。

---

## Roadmap

- [x] v0.1：Streamlit UI + Mock 业务流程
- [x] v0.2：Chroma RAG + 5 个 tools + LangChain Agent + `cmms-mcp` + FastAPI
- [x] v1.0：PDF 入库 + 20 条端到端评测 + 鉴权/审计 + 适配层
- [ ] v1.1：真实模型端到端评测
- [ ] v1.2：中文 PDF/OCR + 50+ 份真实风格手册
- [ ] v1.3：真实 CMMS/ERP 对接、SSO、可观测性

---

## 数据说明

所有设备、故障码、工单、库存均为**虚构演示数据**，不对应任何真实厂商或客户。PDF 为脚本生成的 ASCII 示例，仅用于验证入库链路。

---

## License

MIT
