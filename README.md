# 设备售后运维助手（FieldOps Copilot）

一个面向工业设备售后场景的 **LangChain + RAG + Tool Calling + MCP** 简历项目。

> 用户报修后，助手检索维修手册、读取实时工况、判断保修/备件，生成一份**待人工确认**的工单草稿；工程师批准后，通过 `cmms-mcp` 写入 CMMS。

![status](https://img.shields.io/badge/status-v0.2%20working%20demo-brightgreen)
![python](https://img.shields.io/badge/python-3.12-blue)
![langchain](https://img.shields.io/badge/langchain-1.4-1c3d5a)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 当前状态

**v0.2：可本地运行的端到端 Demo。**

已经实现：

- **RAG**：6 份示例手册/公告/SOP/历史工单，Chroma 向量检索 + 关键词重排 + 页码引用
- **Tool Calling**：5 个原生 LangChain tools
  - `search_knowledge`
  - `get_telemetry`
  - `check_warranty`
  - `check_parts`
  - `draft_work_order`
- **LangChain Agent**：`create_agent` 统一调度 RAG、原生工具和 MCP 工具
- **MCP**：`cmms-mcp` 暴露 `create_work_order` / `get_work_order`，通过 Streamable HTTP 接入
- **HITL**：Agent 只生成 draft；工程师在 Streamlit 里批准后才写 CMMS
- **FastAPI**：`/chat`、`/work-orders`、`/work-orders/{id}/approve`、`/health`
- **Streamlit**：对话诊断、引用来源、工具轨迹、工单草稿、技术栈说明
- **测试**：9 个 pytest 用例通过
- **评测**：15 条手册检索问题，Recall@4 = 15/15（仅 6 篇文档，小样本，见下方说明）

> 没有模型 API Key 时，项目使用 `MockToolCallingModel` 做确定性工具调用，**仍然走 LangChain `create_agent`**，所以离线可运行、可测试。配置 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY` 后自动切换真实模型。
>
> 真实模型路径已实现，但当前开发环境没有 API Key，未做真实模型端到端验证；下面的测试与指标均来自离线 mock 路径。

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

一句话：

> LangChain 管“流程怎么编排”，RAG 管“知识从哪来”，Tool Calling 管“实时数据怎么查”，MCP 管“外部系统怎么接”，HITL 管“写操作怎么不闯祸”。

---

## 架构

```text
┌──────────────────────────────┐
│ Streamlit UI                 │
│ 对话 / 引用 / 工具轨迹 / 审批 │
└──────────────┬───────────────┘
               │ HTTP
┌──────────────▼───────────────┐
│ FastAPI                      │
│ /chat /work-orders /approve  │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│ LangChain create_agent       │
│  MockToolCallingModel        │
│  或 DeepSeek / OpenAI        │
└───┬──────────┬──────────┬────┘
    │          │          │
┌───▼────┐ ┌───▼─────┐ ┌──▼─────────────┐
│ Chroma │ │ Native  │ │ MCP Client     │
│ RAG    │ │ Tools   │ │ Streamable HTTP│
└────────┘ └─────────┘ └──┬─────────────┘
                          │
                   ┌──────▼──────┐
                   │ cmms-mcp    │
                   │ create/get  │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ SQLite      │
                   │ work_orders │
                   └─────────────┘
```

---

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 2. 启动 MCP Server

```powershell
$env:MCP_TRANSPORT = "streamable-http"
python -m mcp_server.cmms_server
```

启动后监听 `http://127.0.0.1:8765/mcp`。

### 3. 启动 FastAPI

另开一个终端：

```bash
uvicorn fieldops.main:app --host 127.0.0.1 --port 8000
```

### 4. 启动 Streamlit

再开一个终端：

```bash
streamlit run app.py
```

打开 <http://127.0.0.1:8501>。

### 或者：Windows 一键启动

```powershell
.\run.ps1
```

脚本会创建 `.venv`（如果不存在）、启动 MCP、启动 API、再启动 Streamlit。

### 5. 演示步骤

1. 在对话框输入：

```text
X100 报 E-204，出水温度高，客户已停机。
```

2. 查看诊断、实时工况、保修、备件和 4 条引用来源
3. 打开左侧 **工单草稿**，核对后点击 **批准并创建工单**
4. 工单通过 `cmms-mcp.create_work_order` 写入 SQLite，返回 `WO-...`
5. 打开左侧 **技术栈**，查看每项技术解决的实际问题

---

## API

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/health` | 模式、MCP 工具、服务状态 |
| `POST` | `/chat` | 诊断对话，返回 answer / citations / tool_trace / draft |
| `GET` | `/work-orders` | 最近的工单草稿 |
| `GET` | `/work-orders/{draft_id}` | 查询工单草稿 |
| `POST` | `/work-orders/{draft_id}/approve` | 人工批准后通过 MCP 建单 |

示例：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"X100 报 E-204，出水温度高","serial":"8F2-1042"}'
```

---

## 项目结构

```text
fieldops-copilot/
├─ app.py                    # Streamlit UI（HTTP 调后端）
├─ fieldops/
│  ├─ main.py                # FastAPI 入口
│  ├─ agent.py               # create_agent + 模型选择
│  ├─ mock_llm.py            # 无 API Key 时的确定性工具调用模型
│  ├─ rag.py                 # Chroma + HashingEmbeddings + 引用
│  ├─ tools.py               # 5 个原生工具
│  ├─ mcp_client.py          # langchain-mcp-adapters
│  ├─ service.py             # 对话编排 / 审批
│  ├─ db.py                  # SQLite
│  ├─ data.py                # JSON 数据访问
│  └─ schemas.py             # Pydantic
├─ mcp_server/
│  └─ cmms_server.py         # FastMCP：create/get work order
├─ data/
│  ├─ manuals/               # 6 份示例手册
│  ├─ devices.json
│  ├─ parts.json
│  └─ telemetry.json
├─ eval/
│  ├─ questions.jsonl
│  └─ run_eval.py
├─ tests/
│  ├─ test_rag.py
│  ├─ test_tools.py
│  ├─ test_service.py
│  └─ test_api.py
├─ requirements.txt
├─ run.ps1
├─ pytest.ini
└─ README.md
```

---

## 评测与测试

### RAG 检索

```bash
python eval/run_eval.py
```

当前结果：

```text
Recall@4 (doc)  = 15/15 = 100.00%
Page hit@4      = 15/15 = 100.00%
```

**说明**：语料只有 6 篇文档、15 条问题，这个 100% 只能证明链路可用，不能说明泛化能力。下一阶段应扩充到 50+ 篇文档、50+ 条问题，并加入 hard negatives。

### 测试

```bash
pytest -q
```

当前：`9 passed`。

---

## 模型配置

默认离线模式，无需 API Key：

```text
MockToolCallingModel -> 规则化选择工具 -> 仍由 LangChain create_agent 执行
```

使用真实模型：

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
# 可选
$env:DEEPSEEK_MODEL = "deepseek-chat"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"
```

或：

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_MODEL = "gpt-4o-mini"
```

重启 API 后生效。

---

## 简历写法

**设备售后运维助手｜LangChain + RAG + Tool Calling + MCP｜个人项目**

- 基于 LangChain 1.x `create_agent` 构建设备售后诊断 Agent，统一调度 Chroma RAG、5 个业务工具和 1 个 MCP Server，完成从故障描述到工单草稿的闭环。
- 设计面向设备手册/服务公告的 RAG 链路，按标题切分并保留型号、版本、页码元数据，在 15 条小样本评测集上 Recall@4 为 15/15，回答附带可追溯引用。
- 将 CMMS 封装为 MCP Server，通过 `langchain-mcp-adapters` 以 Streamable HTTP 暴露建单/查单能力；写操作经 Streamlit 人工确认后执行，避免误建单。
- 使用 FastAPI + Streamlit 实现前后端分离 Demo，支持对话诊断、引用来源、工具调用轨迹和工单审批，9 个 pytest 用例覆盖 RAG、工具、服务、MCP 与 API。

> 指标请写你实测的数字；当前 15/15 是小样本，面试时主动说明语料规模，避免被追问时显得夸大。

---

## Roadmap

- [x] v0.1：Streamlit 界面 + Mock 业务流程
- [x] v0.2：Chroma RAG + 5 个 tools + LangChain Agent + `cmms-mcp` + FastAPI + Streamlit
- [ ] v0.3：接入真实模型，补 50 条端到端评测
- [ ] v0.4：PDF/OCR 解析，扩充到 50+ 份手册
- [ ] v0.5：Docker Compose、鉴权、审计日志
- [ ] v1.0：真实 CMMS / ERP 适配

---

## 数据说明

所有设备、故障码、工单、库存均为**虚构演示数据**，不对应任何真实厂商或客户。

---

## License

MIT
