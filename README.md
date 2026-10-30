# 设备售后运维助手（FieldOps Copilot）

一个面向工业设备售后场景的 **LangChain + RAG + Tool Calling + MCP** 简历项目。

> 用户报修后，助手查设备档案、检索维修手册、读取实时工况、判断保修/备件，最后生成一份**待人工确认**的工单草稿。

![status](https://img.shields.io/badge/status-v0.1%20UI%20demo-orange)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 当前状态

**v0.1：可运行的界面演示版（Mock 数据）。**

已经实现：

- Streamlit 对话界面
- E-204 高温故障的完整演示流程
- 工单草稿、人工确认、模拟建单
- “技术栈”页面：说明每项技术解决的实际问题

规划中（按 Roadmap 逐步接入）：

- LangChain Agent
- Chroma RAG + 页码引用
- 3 个 Native Tools（遥测/保修/备件）
- 1 个 `cmms-mcp` Server
- 50 条评测集

> 仓库不会把“规划中”写成“已完成”。当前版本就是 UI 原型，方便先看交互和业务闭环。

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
| **RAG** | 手册长、版本多，模型直接答会编造故障码 | 按标题切分 + 型号/版本/页码元数据 + Chroma 检索 + 引用 |
| **Tool Calling** | 设备当前温度、转速、保修、库存不在文档里 | `get_telemetry` / `check_warranty` / `check_parts` |
| **MCP** | CMMS 是外部系统，建单要认证、审计、复用 | `cmms-mcp` 暴露 `create_work_order` / `get_work_order` |
| **HITL** | 建单、订备件有真实成本，误操作代价高 | Agent 只出 draft，工程师批准后才写 CMMS |

一句话：

> LangChain 管“流程怎么编排”，RAG 管“知识从哪来”，Tool Calling 管“实时数据怎么查”，MCP 管“外部系统怎么接”，HITL 管“写操作怎么不闯祸”。

---

## 本地运行

### 方式一：直接运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

打开 <http://127.0.0.1:8501>。

### 方式二：Windows 一键脚本

```powershell
.\run.ps1
```

脚本会创建 `.venv`、安装依赖并启动 Streamlit。

### 演示步骤

1. 打开页面，确认标题为 **设备售后运维助手**
2. 在对话框输入：

```text
X100 报 E-204，出水温度高，客户已停机。
```

3. 查看诊断、实时工况、手册引用、备件和保修
4. 打开左侧 **工单草稿**，勾选确认，点击 **批准并创建工单**
5. 打开左侧 **技术栈**，查看“技术 → 实际问题 → 实现”的对应关系

---

## 项目结构

```text
fieldops-copilot/
├─ app.py              # Streamlit 演示界面（当前版本）
├─ requirements.txt    # 运行依赖
├─ run.ps1             # Windows 启动脚本
├─ .gitignore
├─ LICENSE
└─ README.md
```

后续接入后端后，计划扩展为：

```text
app/
├─ main.py             # FastAPI：/chat、/work-order/approve
├─ agent.py            # LangChain create_agent
├─ rag.py              # Chroma 检索 + 引用
├─ tools.py            # 3 个原生工具
├─ mcp_client.py       # langchain-mcp-adapters
└─ schemas.py          # Pydantic

mcp_server/
└─ cmms_server.py      # FastMCP：create/get work order
```

---

## Roadmap

- [x] v0.1：Streamlit 界面 + Mock 业务流程
- [ ] v0.2：Chroma 知识库 + 20–30 份手册 + 页码引用
- [ ] v0.3：3 个 Native Tools + mock API
- [ ] v0.4：LangChain `create_agent` 串联 RAG + Tools
- [ ] v0.5：`cmms-mcp` + `langchain-mcp-adapters`
- [ ] v0.6：50 条评测集 + 指标报告
- [ ] v1.0：3 分钟端到端 Demo + 部署说明

---

## 简历写法

**设备售后运维助手｜LangChain + RAG + Tool Calling + MCP｜个人项目**

- 基于 LangChain 1.x 构建设备售后诊断 Agent，将 RAG 检索、3 个业务工具和 1 个 MCP Server 统一为工具调用，完成从故障描述到工单草稿的闭环。
- 设计面向设备手册/服务公告的 RAG 链路，按标题切分并保留型号、版本、页码元数据，在 50 条评测集上 Recall@5 达 __%，引用准确率 __%。
- 将 CMMS 封装为 MCP Server，通过 `langchain-mcp-adapters` 暴露建单/查单能力；写操作经 Streamlit 人工确认后执行，避免误建单。
- 使用 Streamlit 实现纯 Python 演示界面，支持对话诊断、工单预览与审批，3 分钟完成端到端演示。

> 指标请填你实测的数字；没有实测就写“搭建了 50 条评测集”，不要编。

---

## 数据说明

当前所有设备、故障码、工单、库存均为**虚构演示数据**，不对应任何真实厂商或客户。

---

## License

MIT
