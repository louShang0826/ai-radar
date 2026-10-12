---
title: "端到端工作流 / AI Agent 平台行业调研（第 1 步）"
subtitle: "面向内部类 Grok Bot 平台的定位与技术选型准备"
date: "2026-10-01"
---

# 0. 摘要（TL;DR）

- **形态在收敛**：2025 年下半年到 2026 年，各家头部厂商都在往同一种产品形态靠：**云端持久运行的 Agent，带独立电脑/沙箱，连接企业应用，能定时或由事件触发，有记忆和技能，后台异步执行，并且要人审批**。例子有 OpenAI 的 Codex Cloud、workspace agents 和 Agents API，Anthropic 的 Cowork、Claude Code Routines 和 Managed Agents，Microsoft Copilot Cowork，Google Gemini Enterprise Agent Platform，Manus 2.0，以及字节扣子（2.0/2.5/3.0，2026-08 起并入豆包，对外品牌为豆包工作）。这和 Grok Bot 的产品形态高度一致。
- **协议层基本定型**：MCP（工具/数据连接）、A2A（Agent 间通信）、AGENTS.md（项目指令）都已归入 Linux 基金会的 Agentic AI Foundation（AAIF）。Agent Skills（SKILL.md）也已成为跨厂商的开放格式。
- **"确定性工作流"和"自主 Agent"在融合**：工作流厂商（Zapier、n8n、UiPath、Workato）把 Agent 做成流程里的一个节点。Agent 厂商则反过来补调度、触发器、审批和审计。主流架构变成 **"可治理的确定性骨架 + 局部 LLM 自主"**。
- **钱和人流向基础设施层**：Temporal 2026 年 9 月以 125.5 亿美元估值融资 5.5 亿美元；n8n 估值 52 亿美元（SAP 战略投资）；还有一批沙箱和浏览器基础设施公司拿到融资（E2B、Daytona、Browserbase）。
- **安全和成本是主要瓶颈**：OpenClaw 爆火，随后出现 ClawHub 恶意技能供应链事件；Gartner 预测 40%+ 的 Agentic AI 项目会在 2027 年底前被取消；按用量计费（credits）成了主流，于是预算控制成了企业的刚需。

> 说明：本文信息截至 2026-10-01，主要来自厂商官方博客/文档和主流媒体（Reuters、Bloomberg、TechCrunch、The Verge 等）。标注 **[待核实]** 的条目是二手来源，或者没能找到一手来源的信息。

---

# 1. 竞品与生态全景（按类别）

## 1.1 类别地图

| 层级 | 类别 | 代表产品（2026 年在售/在维护） |
|---|---|---|
| 终端产品 | (a) 自带电脑/沙箱的通用自主 Agent | OpenAI Codex / ChatGPT workspace agents / ChatGPT Work；Anthropic Claude Cowork / Claude Code / Claude in Chrome；Microsoft Copilot Cowork；Google Gemini Agent（原 Project Mariner）；Manus 2.0；Genspark（Claw / AI Workspace）；Perplexity Comet；OpenClaw（开源） |
| 流程层 | (b) 加入 AI Agent 的工作流自动化平台 | Zapier（AI by Zapier）、n8n、Make、Workato（Genies / Agent Studio）、UiPath（Agent Builder + Maestro）、Microsoft Power Automate / Copilot Studio |
| 构建层 | (c) Agent 构建 / LLM 应用平台 | Dify、扣子 Coze（2026-08 起并入豆包，成为豆包工作的能力层；开源 Coze Studio 仍独立）、FastGPT、Langflow（IBM）、Flowise（Workday）、OpenAI AgentKit / Agent Builder、Google Gemini Enterprise（含原 Agentspace）、AWS Bedrock AgentCore、Salesforce Agentforce、Lindy、Relevance AI、Glean、阿里云百炼 Agent Studio、腾讯元器 / 腾讯云智能体开发平台 |
| 开发与基础设施层 | (d) 框架、运行时、沙箱、协议 | LangGraph / LangChain、CrewAI、Microsoft Agent Framework（AutoGen + Semantic Kernel 的继任者）、OpenAI Agents SDK / Agents API、Google ADK、Claude Agent SDK / Managed Agents、Temporal、E2B、Daytona、Modal、Browserbase；协议：MCP、A2A、AGENTS.md、Agent Skills |
| 区域 | (e) 中国玩家与"龙虾"生态 | 字节豆包 / 豆包工作（2026-08 起整合扣子、TRAE、飞书产品团队；扣子作为能力层）/ 火山引擎 ArkClaw；阿里百炼、CoPaw、HiClaw、无影 JVS；腾讯 WorkBuddy、QClaw、元器、企业微信接入；智谱 AutoGLM / Open-AutoGLM；百度千帆；小米 miclaw；Manus（总部已迁到新加坡） |

## 1.2 (a) 自带电脑/沙箱的通用自主 Agent

**OpenAI**
- **ChatGPT agent**：2025 年 7 月推出，把 Operator（网页操作）和 deep research 合并，提供虚拟浏览器、终端和连接器。Operator 网站随后下线。OpenAI 帮助中心现在写着"ChatGPT agent is no longer available"，长任务改用 **ChatGPT Work**，浏览器任务改用 cloud browser。[来源](https://help.openai.com/en/articles/11752874-chatgpt-agent)、[发布](http://openai.com/index/introducing-chatgpt-agent)
- **Atlas 浏览器**：已宣布废弃，2026-08-09 停止工作。浏览器 Agent 能力转入 ChatGPT 桌面端和 Codex。[来源](https://help.openai.com/en/articles/20001371-evolving-atlas-into-chatgpt-for-browser-based-agentic-work)。可以看出，独立"AI 浏览器"这条路线在 OpenAI 内部被收编进了主应用。
- **Workspace agents**：GPTs 的演进版，由 Codex 驱动，在云端运行，可以定时执行或在 Slack 中调用，在组织内共享，带记忆。2026-05-06 起改为按 credit 计费。[来源](https://openai.com/index/introducing-workspace-agents-in-chatgpt/)
- **Codex Cloud（新版）**：可复用的持久云环境，笔记本合上后任务继续跑，桌面、网页、手机之间可以接力；支持子 Agent 并行。[帮助](https://help.openai.com/en/articles/20001545-using-codex-cloud)、[Subagents](https://developers.openai.com/codex/concepts/subagents.md)

**Anthropic**
- **Claude Code**：2024 年 11 月推出 CLI，之后陆续推出 Web 版和 Slack 集成。[TechCrunch](https://techcrunch.com/2026/01/12/anthropics-new-cowork-tool-offers-claude-code-without-the-code/)
- **Claude Code Routines**（研究预览）：在 Anthropic 云端运行的定时、API 或 GitHub 事件触发自动化，电脑关机也能执行。[来源](https://claude.com/blog/introducing-routines-in-claude-code)
- **Claude Cowork**：2026-01-12 以研究预览形式发布，是"给非程序员用的 Claude Code"。之后扩展到 Pro/Max/Team，支持云端继续执行和手机端；2026-08-26 加入内置浏览器。[产品页](https://claude.com/product/cowork)、[The Verge](https://www.theverge.com/ai-artificial-intelligence/860730/anthropic-cowork-feature-ai-agents-claude-code)
- **Claude in Chrome**：已 GA。浏览器里的定时任务在本地执行，需要电脑开着。[来源](https://claude.com/blog/claude-in-chrome-generally-available)
- **Claude Managed Agents**：2026-04-08 公测，是托管的长时 Agent 服务，提供沙箱、持久会话、权限、定时和 tracing。[来源](https://claude.com/blog/claude-managed-agents)

**Microsoft**
- **Copilot Cowork**：2026-06-16 GA。云端托管，笔记本关机也能继续跑；接 Work IQ 企业上下文；多模型，GA 时用的是 Anthropic Opus 4.8 / Sonnet 4.6，自研 Cowork 1 即将推出。按 Copilot Credits 计费，PayGo 价格为 0.01 美元/credit；带租户、组、用户三级预算上限；Edge 浏览器操作在 Frontier 计划中提供。微软称预览期已有超过一半的财富 500 强在用。[来源](https://www.microsoft.com/en-us/microsoft-365/blog/2026/06/16/copilot-cowork-is-now-generally-available/)
- **Agent 365**：企业 Agent 控制平面（观测、治理、安全），15 美元/用户/月，或包含在 M365 E7 中。[来源](https://www.microsoft.com/en-us/microsoft-agent-365) **[价格以二手摘要为准]**

**Google**
- **Gemini Agent / Chrome Auto Browse**：Project Mariner 已不再作为独立产品，技术并入 Gemini Agent 和 Chrome Auto Browse，需要 Google AI Pro/Ultra 订阅。[来源](https://futuretweets.com/comet-vs-edge-copilot-vs-chrome-auto-browse-2026/) **[二手来源，待核实]**
- **Gemini Spark**（消费级 24/7 个人 Agent，更新于 2026-10）：2026-05-19 在 I/O 发布，基于 Gemini 3.5 和 Antigravity harness，云端持续运行，深度接入 Gmail/Docs 等，支持定时与触发、技能、MCP 连接；高风险动作先问人；先向 Ultra 用户开放，7 月扩大到美国 AI Pro。[Google](https://blog.google/innovation-and-ai/products/gemini-app/next-evolution-gemini-app/)
- **Gemini agent**（企业版"通用工作 Agent"）：2026-10-08 在 Gemini at Work 发布。[Google](https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/gemini-at-work/)
- 企业侧见 1.4 的 Gemini Enterprise。

**Manus（Butterfly Effect，现总部在新加坡）**
- 2025 年 5 月获 Benchmark 领投的 7500 万美元融资，7 月关闭中国办公室并迁往新加坡。[Reuters](https://www.reuters.com/world/asia-pacific/china-blocks-foreign-acquisition-ai-startup-manus-2026-04-27/)
- 2025-12-29，Meta 宣布收购，估值 20–30 亿美元。[Meta](https://www.facebook.com/business/news/manus-joins-meta-accelerating-ai-innovation-for-businesses)、[Reuters](https://www.reuters.com/world/china/meta-acquire-chinese-startup-manus-boost-advanced-ai-features-2025-12-29/)
- 2026-04-27，中国发改委外商投资安全审查办公室要求撤销这笔交易。2026 年 8 月，Manus 宣布恢复独立运营，并需删除部分 Meta 期间的用户数据。[Computerworld](https://www.computerworld.com/article/4209728/meta-gives-up-control-of-chinese-ai-startup-manus-after-eight-months.html)
- **2026-10-08**：宣布完成超 5 亿美元融资（博裕、IDG 领投，腾讯、红杉中国 HSG、真格跟投），未披露估值（此前传言 40 亿美元）；据报道考虑在香港上市【二手】。[TechCrunch](https://techcrunch.com/2026/10/08/chinas-manus-raises-over-500m-in-first-funding-round-since-split-with-meta/)
- **Manus 2.0**（2026 年 9 月）包括：重构的 Cascade 引擎；本地文件工作区 Studio；Cloud Computer（独立付费的持久云电脑，每月 10/30/50 美元三档）；Remote Control / Computer Use；事件触发的 Automations；以及 **Cue**，这是一个"个人 Agent 团队"应用，每个 Agent 有自己的邮箱、电话、钱包和电脑。[来源](https://help.manus.im/en/articles/17190150-what-is-new-in-manus-2-0)、[计费](https://help.manus.im/en/articles/15392078-understanding-cloud-computer-plans-and-billing)。Cue 和"多 bot 队友"的概念非常接近。

**Genspark**
- 2026 年 3 月发布 Genspark Claw（"AI 员工"）和 AI Workspace 3.0，当时宣称年化收入超过 2 亿美元。[BusinessWire](https://www.businesswire.com/news/home/20260312641003/en/)
- 2026 年 6 月 B 轮扩至 4.85 亿美元，投后估值 26 亿美元。[BusinessWire](https://www.businesswire.com/news/home/20260617758937/en/)

**Perplexity Comet**
- AI 浏览器，免费使用；Comet Plus 每月 5 美元。企业版捆绑在 Perplexity Enterprise 中（每席位每月 40/325 美元），带 MDM、审计日志和 Agent 控制。[来源](https://www.perplexity.ai/hub/blog/comet-is-now-available-to-everyone-worldwide)、[Enterprise](https://www.perplexity.ai/enterprise/comet)

**OpenClaw（开源、自托管个人 Agent）**
- 前身为 Clawdbot / Moltbot，2026 年初爆红。创始人 Peter Steinberger 2026 年 2 月加入 OpenAI，项目转入独立基金会，继续开源。[The Verge](https://www.theverge.com/ai-artificial-intelligence/879623/openclaw-founder-peter-steinberger-joins-openai)
- 到 2026 年 8 月，GitHub 约 38.8 万 star。[GitHub Blog](https://github.blog/open-source/maintainers/openclaw-went-viral-meet-the-maintainers-building-and-securing-it/)
- 安全模型是"每个网关一个可信操作者"，不支持敌对多租户。[文档](https://docs.openclaw.ai/security)
- 技能市场 ClawHub 多次出现恶意技能（最初发现 341 个，后来超过 1100 个）。[CSA 研究报告](https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/07/CSA%5Fresearch%5Fnote%5Fopenclaw%5Fclawhub%5Fsupply%5Fchain%5Frisk%5F20260707-csa-styled.pdf) **[具体数字来自二手摘要]**

## 1.3 (b) 加入 AI Agent 的工作流自动化平台

- **Zapier**：独立的 Agents 产品（agents.zapier.com）正在迁移进 **AI by Zapier**。Agent 现在是 Zap 里的一个步骤，可以和确定性步骤混排。迁移后的能力包括：逐工具开启"运行前审批"、结构化输出、单次运行 task 上限（默认 75，最高 500）、管理员可按模型禁用、发布前审批；按 task 计费。[来源](https://help.zapier.com/hc/en-us/articles/47402591569805-Migrating-from-Agents-to-AI-by-Zapier)。值得注意的是，**连 Zapier 都放弃了"独立 Agent 产品"，转向"Agent 嵌入工作流"**。
- **n8n**：
  - 2025 年 10 月 C 轮融资 1.8 亿美元，估值 25 亿美元。[n8n](https://blog.n8n.io/series-c/)
  - 2026 年 5 月 SAP 战略投资，估值 52 亿美元，n8n 将嵌入 SAP Joule Studio。[n8n](https://blog.n8n.io/n8n-sap/)、[Bloomberg](https://www.bloomberg.com/news/articles/2026-05-12/sap-invests-in-ai-automation-startup-n8n-at-5-2-billion-value)
  - 采用 Sustainable Use License（fair-code）：可以内部自托管，但不能拿来转售托管服务；按执行次数计费。[许可证](https://docs.n8n.io/privacy-and-security/sustainable-use-license)
- **UiPath**：Agent Builder 加 **Maestro**。Maestro Flow / Orchestrate 把 Agent、RPA 机器人、API 和人工步骤编排在一起，支持 BPMN 和长时流程，可暂停、恢复、重试，带审计。[来源](https://www.uipath.com/product/maestro/flow)
- **Workato**：Genies / Agent Studio，无代码 Agent，带知识库、MCP、recipes 和审批。[对比](https://www.itechguides.com/compare/microsoft-power-automate-vs-workato-agent-studio/) **[二手来源]**
- **Make、Power Automate / Copilot Studio**：都提供 AI 步骤和 Agent。Power Automate 适合以微软生态为主的企业，长处是审批流和桌面 RPA。**[本次未逐项核实最新版本]**

## 1.4 (c) Agent 构建 / LLM 应用平台

- **OpenAI AgentKit**：2025-10-06 发布，包括 Agent Builder（可视化多 Agent 画布，beta）、ChatKit、Evals 和 Connector Registry。[来源](https://openai.com/index/introducing-agentkit/)。2026 年又推出 **Agents API**（公测），把 Codex 的 harness 和托管沙箱开放给开发者，计算环境可以选 OpenAI 托管、自有基础设施或合作伙伴沙箱。[来源](https://openai.com/index/introducing-the-agents-api/)
- **Google Gemini Enterprise**：Agentspace 已并入 Gemini Enterprise。2026-04-22，Vertex AI 演进为 **Gemini Enterprise Agent Platform**，包括 Agent Studio（低代码）、ADK、Agent Runtime（支持连续运行数天）、Memory Bank、Agent Sandbox、Agent Identity / Registry / Gateway、Simulation / Evaluation / Observability。[来源](https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform)。定价：Business 每用户每月 21 美元，Standard 30 美元。[来源](https://cloud.google.com/gemini-enterprise/business)
- **AWS Bedrock AgentCore**：已 GA。Runtime（microVM）、Memory、Gateway、Identity 等组件分别按量计费，例如 Gateway 每 1000 次调用 0.005 美元；新版 Runtime 于 2026 年 9 月发布。[定价](https://aws.amazon.com/bedrock/agentcore/pricing/)、[公告](https://aws.amazon.com/about-aws/whats-new/2026/09/new-agentcore-runtime-generally-available/)
- **Salesforce Agentforce**：Flex Credits 为 500 美元/10 万 credits，每个标准动作消耗 20 credits，约合 0.10 美元/动作。[定价](https://www.salesforce.com/agentforce/pricing/)。Agentforce ARR 超过 15 亿美元，但口径已扩大，把 Slackbot 等也算了进去。[来源](https://www.insidermonkey.com/news/wells-fargo-raises-salesforces-price-target-can-1-5-billion-agentforce-arr-reaccelerate-growth-1842360/) **[口径注意]**
- **Dify**：开源 LLM 应用和工作流平台。2026 年 3 月 Pre-A 轮融资 3000 万美元，估值 1.8 亿美元。[来源](https://dify.ai/blog/dify-raises-30m-tomorrow-s-organizations-will-be-built-by-people-and-agents)
- **扣子 Coze → 豆包工作**：2026 年 1 月升级为"扣子 2.0"，推出 Agent Skills、Agent Plan（长期目标拆解，持续执行并汇报）、Agent Office 和 Agent Coding。[新浪](https://finance.sina.com.cn/tech/it/2026-01-19/doc-inhhvwpt6817994.shtml)。开源的 **Coze Studio**（可视化 Agent 构建）和 **Coze Loop**（评测与观测）采用 Apache-2.0 许可证。[GitHub](https://github.com/coze-dev/coze-studio)
  - **后续（更新于 2026-10）**：
    - 2026-04 推出 2.5（Agent World：独立邮箱身份、云电脑/云手机）。
    - 2026-06-01 推出 **扣子 3.0**（"人 + 多 Agent"协作，可接入 Claude Code、Codex CLI、OpenClaw 等本地 Agent）。[IT之家](https://www.ithome.com/0/958/277.htm)
    - 2026-07-30 飞书与豆包产品团队整合。
    - 2026-08-24 扣子、TRAE 团队并入豆包。[新浪财经](https://finance.sina.com.cn/stock/t/2026-08-24/doc-inipmnpq6049441.shtml)
    - 2026-08-25 发布「豆包工作」。[飞书](https://www.feishu.cn/content/article/7677519271848610746)
    - 现在对外的主品牌是豆包 / 豆包工作，扣子退为智能体、技能和工作流的能力层。详见深度报告 §1.9。
- **Langflow**：DataStax 于 2024 年收购，IBM 随后于 2025 年宣布收购 DataStax。[IBM](https://www.ibm.com/new/announcements/ibm-to-acquire-datastax-helping-clients-bring-the-power-of-unstructured-data-to-enterprise-ai-applications)
- **Flowise**：2025 年 8 月被 Workday 收购。[Workday](https://investor.workday.com/news-and-events/press-releases/news-details/2025/Workday-Acquires-Flowise-Bringing-Powerful-AI-Agent-Builder-Capabilities-to-the-Workday-Platform-08-14-2025/default.aspx)
- **FastGPT**：国内开源知识库和工作流平台。**[本次未核实最新动态]**
- **Glean**：企业搜索加 Agent。F 轮融资 1.5 亿美元，估值 72 亿美元。[来源](https://www.glean.com/blog/glean-series-f-announcement)
- **Lindy / Relevance AI**：面向业务用户的"AI 员工"构建平台，按 credit 或用量计费。融资数据来源不一致。**[待核实]**
- **阿里云百炼 Agent Studio**：覆盖 Agent 开发、托管运行、知识库/记忆、MCP/Skill/Connector、沙箱、评测和安全治理。[阿里云](https://developer.aliyun.com/article/1763850)
- **腾讯元器 / 腾讯云智能体开发平台**：偏重微信和企业微信生态的低代码应用与连接器；提供 OpenClaw 一键部署。[36氪](https://www.36kr.com/p/3715653109200263)

## 1.5 (d) 开发框架与基础设施

- **LangChain / LangGraph**：2025 年 10 月同时发布 1.0；B 轮融资 1.25 亿美元，估值 12.5 亿美元。LangGraph 定位为"持久化 Agent 运行时"。[来源](https://www.langchain.com/blog/langchain-langgraph-1dot0)、[TechCrunch](https://techcrunch.com/2025/10/21/open-source-agentic-startup-langchain-hits-1-25b-valuation/)
- **Microsoft Agent Framework**：AutoGen 和 Semantic Kernel 的统一继任者，2026-04-03 发布 1.0 GA（.NET/Python），带图式工作流。之后又发布 Harness，提供规划、记忆、工具、审批和遥测。[1.0](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)、[Harness](https://devblogs.microsoft.com/agent-framework/the-microsoft-agent-framework-harness-is-now-released/)
- **CrewAI**：2026 年 4 月 B 轮融资 2000 万美元。[PitchBook](https://pitchbook.com/profiles/company/590845-78) **[二手来源]**
- **OpenAI Agents SDK / Agents API；Google ADK；Claude Agent SDK / Managed Agents**：三家模型厂商都同时提供"开源 harness 加托管运行时"。
- **Temporal**（持久化执行）：
  - 2026 年 2 月 D 轮融资 3 亿美元，估值 50 亿美元。
  - 2026-09-14 E 轮融资 5.5 亿美元，估值 125.5 亿美元，明确押注长时 AI Agent。[Temporal](https://temporal.io/blog/temporal-raises-usd550m-series-e-at-usd12-55b-valuation-ai)、[Reuters](https://www.reuters.com/business/temporals-valuation-spikes-126-billion-lightspeed-led-funding-round-2026-09-14/)
- **沙箱**：
  - E2B：Firecracker microVM，2025 年 7 月 A 轮 2100 万美元。[E2B](https://e2b.dev/resources/series-a)
  - Daytona：有状态沙箱，可 fork、暂停、快照，2026 年 A 轮 2400 万美元。[PR](https://www.prnewswire.com/news-releases/daytona-raises-24m-series-a-to-give-every-agent-a-computer-302680740.html)
  - Modal：Serverless GPU/CPU 容器。**[本次未核实最新融资]**
- **浏览器基础设施**：Browserbase，2025 年 6 月 B 轮 4000 万美元。[LinkedIn](https://linkedin.com/company/browserbasehq) **[二手来源]**
- **协议**：见第 2.2 节。

## 1.6 (e) 中国玩家与"养龙虾"潮

- 2026 年 1–3 月，OpenClaw 在国内引发"养龙虾"热潮。据智东西统计，到 3 月 9 日，13 家以上大厂已上线一键部署或类 OpenClaw 产品。[36氪](https://www.36kr.com/p/3715653109200263)、[钛媒体](https://www.tmtpost.com/7907922.html)
  - **腾讯**：WorkBuddy（兼容 OpenClaw，可切换混元、DeepSeek、GLM、Kimi 等模型）；QClaw（本地一键部署，可直连微信；**2026-09-24 宣布停运，12-24 停止服务，团队并入 WorkBuddy**，[澎湃](https://www.thepaper.cn/newsDetail_forward_34140067)）；企业微信和 QQ 开放平台接入；Lighthouse 云端"养虾"用户超过 10 万；电脑管家 AI 安全沙箱。
  - **字节**：火山引擎 ArkClaw（云上 SaaS 版 OpenClaw，适配飞书）、扣子 InStreet（中文版 Moltbook 社区）；飞书把免费 API 额度提升到每月 100 万次。
  - **阿里**：CoPaw（个人 Agent 工作台，可本地或云端运行，支持定时任务）；开源 HiClaw（团队版，带 Manager Agent）；无影 JVS（多 Agent 协作云电脑）。
  - **其他**：百度千帆和红手指云手机 Operator；小米 miclaw（手机系统级 Agent）；支付宝百宝箱；美团 LongCat 免费 API。
- **智谱 AutoGLM**：手机、电脑、网页三端 Agent。AutoGLM 2.0 支持云手机/云电脑异步执行；开源 Open-AutoGLM（Apache-2.0，含 AutoGLM-Phone-9B）。[GitHub](https://github.com/zai-org/Open-AutoGLM)
- **豆包工作（含原扣子）、百炼、元器**：见 1.4。
- **Manus**：中国团队背景，已迁往新加坡，产品不在中国大陆提供；Meta 收购被叫停，是中美监管博弈的典型案例。

---

# 2. 行业动态

## 2.1 融资与并购（已核实部分）

| 时间 | 事件 | 来源 |
|---|---|---|
| 2024-04 / 2025 | DataStax 收购 Langflow；IBM 宣布收购 DataStax | [IBM](https://www.ibm.com/new/announcements/ibm-to-acquire-datastax-helping-clients-bring-the-power-of-unstructured-data-to-enterprise-ai-applications) |
| 2025-05 | Manus 获 7500 万美元融资（Benchmark 领投） | [Reuters](https://www.reuters.com/world/asia-pacific/china-blocks-foreign-acquisition-ai-startup-manus-2026-04-27/) |
| 2025-07 | E2B A 轮 2100 万美元 | [E2B](https://e2b.dev/resources/series-a) |
| 2025-08 | Workday 收购 Flowise | [Workday](https://investor.workday.com/news-and-events/press-releases/news-details/2025/Workday-Acquires-Flowise-Bringing-Powerful-AI-Agent-Builder-Capabilities-to-the-Workday-Platform-08-14-2025/default.aspx) |
| 2025-10 | n8n C 轮 1.8 亿美元，估值 25 亿美元；LangChain 估值 12.5 亿美元 | [n8n](https://blog.n8n.io/series-c/)、[TechCrunch](https://techcrunch.com/2025/10/21/open-source-agentic-startup-langchain-hits-1-25b-valuation/) |
| 2025-12 | Meta 宣布收购 Manus（20–30 亿美元） | [Reuters](https://www.reuters.com/world/china/meta-acquire-chinese-startup-manus-boost-advanced-ai-features-2025-12-29/) |
| 2026-02 | OpenClaw 创始人加入 OpenAI；Temporal D 轮 3 亿美元（估值 50 亿美元）；Daytona A 轮 2400 万美元 | [The Verge](https://www.theverge.com/ai-artificial-intelligence/879623/openclaw-founder-peter-steinberger-joins-openai)、[Temporal](https://temporal.io/blog/temporal-raises-usd300m-series-d-at-a-usd5b-valuation) |
| 2026-03 | Dify 3000 万美元（估值 1.8 亿美元）；Genspark 宣称 ARR 超过 2 亿美元 | [Dify](https://dify.ai/blog/dify-raises-30m-tomorrow-s-organizations-will-be-built-by-people-and-agents)、[BusinessWire](https://www.businesswire.com/news/home/20260312641003/en/) |
| 2026-04 | 中国叫停 Meta 收购 Manus | [Reuters](https://www.reuters.com/world/asia-pacific/china-blocks-foreign-acquisition-ai-startup-manus-2026-04-27/) |
| 2026-05 | SAP 投资 n8n，估值 52 亿美元 | [Bloomberg](https://www.bloomberg.com/news/articles/2026-05-12/sap-invests-in-ai-automation-startup-n8n-at-5-2-billion-value) |
| 2026-06 | Genspark 估值 26 亿美元（B 轮累计 4.85 亿美元） | [BusinessWire](https://www.businesswire.com/news/home/20260617758937/en/) |
| 2026-09 | Temporal E 轮 5.5 亿美元，估值 125.5 亿美元；Instinct C 轮 10 亿美元（估值 100 亿美元） | [Reuters](https://www.reuters.com/business/temporals-valuation-spikes-126-billion-lightspeed-led-funding-round-2026-09-14/)、[SiliconANGLE](https://siliconangle.com/2026/09/28/everyday-personal-ai-assistant-startup-instinct-raises-1b-at-10b-valuation/) |
| 2026-10 | Manus（蝴蝶效应）融资超 5 亿美元（博裕、IDG 领投，腾讯等跟投），是 Meta 交易撤销后首轮；Nous Research（Hermes Agent）B 轮 9000 万美元，估值 15 亿美元 | [TechCrunch](https://techcrunch.com/2026/10/08/chinas-manus-raises-over-500m-in-first-funding-round-since-split-with-meta/)、[SiliconANGLE](https://siliconangle.com/2026/10/07/nvidia-samsung-back-90m-round-for-ai-agent-startup-nous-research/) |

从这些事件看出三个规律：
- 低代码构建器多被**大型 SaaS 或基础软件厂商并购**（Workday、IBM、SAP 投资）。
- **基础设施层**（持久化执行、沙箱）估值涨得最快。
- 跨境并购受地缘监管的约束越来越强。

## 2.2 协议标准化

- **MCP**：
  - 2025-12-09，Anthropic 把 MCP 捐给 Linux 基金会新成立的 **Agentic AI Foundation（AAIF）**。AAIF 由 Anthropic、Block、OpenAI 联合创立，Google、Microsoft、AWS、Cloudflare、Bloomberg 支持。同时入驻的还有 Block 的 goose 和 OpenAI 的 AGENTS.md（后者已被 6 万多个项目采用）。[LF](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)、[Anthropic](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)
  - 规范演进：2025-11-25 版引入实验性的 **Tasks**（异步/持久任务）和 OAuth 2.1 授权。2026-07-28 版把核心改为无状态，Tasks 改成扩展，并用 Client ID Metadata Documents 取代动态客户端注册。另有官方 MCP Registry。[Tasks](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks)、[2026-07-28](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
  - **MCP Apps**：OpenAI 和 Anthropic 联合，基于 MCP-UI 把交互式 UI 扩展到 MCP。[OpenAI](https://openai.com/index/agentic-ai-foundation/)
- **A2A**：Google 于 2025 年 4 月发布，6 月捐给 Linux 基金会；8 月 IBM 的 ACP 并入 A2A；2026-08-17 正式成为 AAIF 托管项目。不过，有评论认为 A2A 的实际生产使用量明显少于 MCP。[AAIF](https://aaif.io/blog/a2a-joins-aaif)、[Devlery](https://devlery.com/en/blog/a2a-joins-aaif-mcp-governance)
- **Agent Skills（SKILL.md）**：Anthropic 于 2025 年 10 月推出，后来作为开放规范发布在 agentskills.io。格式是目录加 SKILL.md（YAML frontmatter 写 name/description），按"渐进式披露"加载。扣子（2.0 起，现豆包工作可把流程沉淀为 Skill）、OpenClaw、各家"龙虾"产品都采用了技能机制。[规范](https://agentskills.io/specification)
- **其他**：Google 的 AP2（Agent 支付协议）出现在 Gemini Enterprise 的客户案例中。[Google](https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform)

## 2.3 从对话走向后台/异步 Agent

- 几乎所有头部产品都强调同一件事："电脑合上也能继续"，以及从手机远程监看和纠偏。例如 Codex Cloud、Cowork、Copilot Cowork、Claude Code Routines 和 Manus Cloud Computer。
- 触发方式从"聊天触发"扩展到 **定时、Webhook、GitHub 事件、Pub/Sub、邮件**。Zapier 迁移文档里提到，聊天触发型 Agent 反而暂时没有直接对应的触发器。
- 出现了"Agent 身份化"：Manus Cue 给每个 Agent 分配邮箱、电话和钱包；Google 给每个 Agent 一个加密身份。

## 2.4 Computer use 与浏览器 Agent

- 有两条路线并存：
  - **云端虚拟浏览器/桌面**：ChatGPT cloud browser、Cowork 内置浏览器、Manus Cloud Computer、Browserbase。
  - **用户本地浏览器扩展**：Claude in Chrome、Manus Browser Operator、Copilot Cowork 的 Edge 浏览。本地路线可以复用用户已有的登录态，但需要电脑开机，风险也更高。
- 独立 AI 浏览器的结局分化：OpenAI Atlas 已废弃；Perplexity Comet 转为免费并做企业版。

## 2.5 企业治理与安全

- **控制平面成为独立品类**：Microsoft Agent 365；Google Agent Identity / Registry / Gateway + Model Armor；AWS AgentCore Identity / Gateway。
- **凭证隔离是共识**：Anthropic 在 Managed Agents 中把"大脑"（harness）和"手"（沙箱）解耦，凭证放在沙箱外的 vault 里，通过 MCP 代理注入，"让沙箱里运行的生成代码永远拿不到 token"。[Anthropic Engineering](https://www.anthropic.com/engineering/managed-agents)
- **提示注入**：ChatGPT agent 的应对方式包括高影响操作前要求确认、注入监控、敏感站点"watch mode"、登录时用户接管。[OpenAI](https://help.openai.com/en/articles/11752874-chatgpt-agent)
- **典型事件**：
  - OpenClaw ClawHub 恶意技能，属于供应链风险。
  - 据报道，Meta 安全研究员的 OpenClaw "失控删除了全部邮件"。[36氪](https://www.36kr.com/p/3715653109200263)
  - 微软、Meta 高管警告不要在普通工作站上运行 OpenClaw。
- **合规接入**：Copilot Cowork 接入审计、DSPM、eDiscovery 等 M365 合规栈，DLP 即将支持。

## 2.6 定价模式

| 模式 | 例子 |
|---|---|
| 席位订阅 + 额度 | Claude Pro/Max/Team、ChatGPT 各计划；Gemini Enterprise（21/30 美元/用户/月） |
| 席位 + 按用量的 credits | Copilot Cowork（需要 Copilot USL，0.01 美元/credit）；ChatGPT workspace agents（credits） |
| 按动作/调用 | Agentforce（约 0.10 美元/动作）；Zapier（按 task 计，MCP 每次调用计 2 个 task） |
| 按执行次数 | n8n |
| 按基础设施资源 | AgentCore（vCPU-小时、GB-小时、调用次数）；E2B / Daytona；Manus Cloud Computer 月费 |
| 开源免费 + 企业版 | Dify、Coze Studio、n8n 社区版、OpenClaw |

整体趋势是从固定席位转向**混合用量计费**，同时都配了**预算上限和单次运行防失控上限**（Copilot Cowork 三级预算，Zapier 单次运行 task 上限）。

## 2.7 失败与反思

- Gartner 2025 年 6 月预测：**超过 40% 的 Agentic AI 项目会在 2027 年底前被取消**，原因是成本、价值不清和风控不足。它还指出存在大量"agent washing"，在数千家自称做 Agentic AI 的厂商中，真正的约只有 130 家。[Gartner](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)
- 被收编或下线的产品：
  - OpenAI Operator 并入 ChatGPT agent，ChatGPT agent 又被 ChatGPT Work 取代；Atlas 下线。
  - Zapier 独立的 Agents 并回 Zap。
  - Project Mariner 并入 Gemini Agent。
  - 这说明**独立的单点 Agent 产品难以存活，会被吸收回主平台或工作流**。
- 平台方封禁：据报道，Google 2026 年 2 月曾大面积封禁通过 OpenClaw 接入的 Google AI 服务，3 月转向发布 Workspace CLI。[36氪](https://www.36kr.com/p/3715653109200263)

---

# 3. 技术原理

## 3.1 编排模型

1. **DAG / 可视化工作流**（n8n、Zapier、Make、Dify、Coze Studio、Agent Builder、UiPath Maestro）
   - 节点和边是确定的，LLM 只是其中的节点。
   - 优点：可预测、可审计、好调试，业务人员也能维护。
   - 缺点：分支爆炸，适应开放任务的能力差。
2. **LLM 驱动的 Agent 循环**（Claude Code / Cowork、Codex、Manus、OpenClaw）
   - 核心是"模型 → 工具调用 → 观察 → 再推理"的 ReAct 式循环，加上上下文工程（压缩、记忆文件、子 Agent），由 harness 管理。
   - 优点：通用性强，能处理长尾任务。
   - 缺点：成本和行为方差大，需要护栏。
3. **混合**（目前的主流）
   - 确定性的骨架（触发器、审批、结构化 I/O）中嵌入 Agent 步骤，比如 AI by Zapier、UiPath "Agents in Flow"。
   - 或者在 Agent 里调用确定性的工作流或技能，比如 Agent Skills、Coze Agent Plan。
   - Google 明确提出要在同一平台同时支持 "generative and deterministic orchestration patterns"。
4. **Harness 与基础设施分离**
   - Anthropic Managed Agents 把 Agent 拆成三个接口：**session**（只追加的事件日志，持久保存）、**harness**（无状态循环，崩溃后用 `wake(sessionId)` 恢复）、**sandbox**（可按需 `provision`、可随时替换的"牲口"）。
   - 这种设计让 TTFT 的 p50 降低约 60%，p95 降低超过 90%。
   - OpenAI Agents API 同样是"OpenAI 托管 harness，计算环境自选"。

## 3.2 执行环境

- **沙箱 VM/容器**：Firecracker microVM（E2B、AgentCore Runtime）、gVisor 或容器、有状态快照与 fork（Daytona）。设计重点是冷启动速度、持久化、按需 provision、网络出口控制。
- **持久"个人电脑"**：每个 bot 或用户一台长期存在的 Linux 机器，带桌面和浏览器，例如 Grok Bot、Manus Cloud Computer、腾讯云桌面 OpenClaw 镜像、无影 JVS。好处是环境、登录态和文件可以复用；代价是成本，以及"宠物式"运维的问题。
- **浏览器自动化**：有基于截图的视觉 computer use（ChatGPT agent 用虚拟浏览器截图来"看"），也有 DOM/CDP 方式（Playwright/Puppeteer，例如微博插件用 Puppeteer）；还有云浏览器（Browserbase）。登录时由用户接管，过程中不截图。
- **本地执行**：桌面应用加用户授权的文件夹（Cowork、Manus Studio）、浏览器扩展、手机端 ADB（Open-AutoGLM）。

## 3.3 工具集成

- MCP 已成为事实标准，ChatGPT connectors、Cowork、Copilot、Gemini、百炼、扣子都支持。认证采用 OAuth 2.1，令牌放在 vault 中，通过代理调用。
- 另外两种接入方式：
  - **SaaS 原生连接器库**：Zapier 声称 9000 多个集成 [Automation Atlas](https://automationatlas.io/tools/zapier/) **[二手]**，n8n 和 Workato 也有大量 recipes。
  - **CLI/API 直调**：Google Workspace CLI 和 GitHub CLI 等 CLI 加技能的方式在编码型 Agent 中很流行。
- 治理层面：企业通过工具注册表和网关（Connector Registry、Agent Registry/Gateway、AgentCore Gateway）集中审批工具。

## 3.4 记忆

- **短期**：会话事件日志，加上压缩和裁剪。
- **长期**：
  - 文件型记忆（memory 文件、AGENTS.md、CLAUDE.md）。
  - 托管记忆服务：Google Memory Bank/Profiles，AWS AgentCore Memory（按事件、记录、检索计费）。
  - 知识库 RAG（Dify、Glean、百炼）。
- **程序性记忆**：技能（SKILL.md）把成功的做法固化下来，实现跨任务复用。

## 3.5 触发与调度

- Cron 定时、Webhook、SaaS 事件（新邮件、GitHub PR、X 新帖）、消息平台（Slack、飞书、企业微信、QQ）、API 调用。
- 云端执行和本地执行的差别很关键：Claude in Chrome 的定时任务需要电脑开机，Routines 和 Cowork 云端版则不需要。

## 3.6 持久化执行

- 长时任务（数小时到数天）需要：检查点、崩溃恢复、重试、超时、幂等、人工等待（可以挂起数天）。
- 实现路线有：
  - Temporal（workflow 加 activity 的事件溯源，估值飙升正是因为 Agent 需求）。
  - LangGraph checkpointer。
  - MCP Tasks。
  - 托管 runtime（Gemini Agent Runtime 支持多日运行，AgentCore）。
  - 自研的 session 日志加无状态 harness（Anthropic）。

## 3.7 多 Agent

- **主 Agent 加并行子 Agent**（Codex subagents、Claude Code subagents、Grok Bot executor），用来扩展上下文和并行探索，代价是 token 成本更高。Codex 文档明确说"只有明确要求时才派生"。
- **团队/角色制**：Manus Cue、阿里 HiClaw Manager Agent、CrewAI、Microsoft Agent Framework 图式工作流。
- **跨组织 Agent 通信**：A2A。

## 3.8 人在回路（HITL）

- 有这几种模式：
  - 高影响操作前确认：ChatGPT agent，Zapier 逐工具 "Require approval"。
  - 发布前审批：Zapier 管理员发布审批。
  - 登录或敏感输入时用户接管。
  - 运行中纠偏：Remote Control、手机端 steer。
  - 超预算时暂停：Zapier 默认 75 task 上限，Copilot 用户发起 credit 申请。
- UiPath Maestro 和 BPMN 把人工任务当作流程里的一等节点。

## 3.9 评测与可观测性

- 运行轨迹（trace）：Zap history 记录每次工具调用、数据、模型和 task 消耗；Managed Agents 提供 tracing；LangSmith；Coze Loop。
- 离线和在线评测：OpenAI Evals、Google Agent Simulation / Evaluation / Optimizer（会自动聚类失败案例并建议修改提示词）。
- 成本观测：每个任务的 credit 明细，以及按用户、组聚合的报表。

## 3.10 安全

- 威胁模型：提示注入（网页、邮件、附件）、凭证外泄、技能/插件供应链、越权操作、数据泄露、失控循环。
- 防护手段：
  - 沙箱隔离，凭证不进沙箱。
  - 最小权限加工具白名单。
  - 网络出口和站点黑名单。
  - 异常检测（Google Agent Anomaly/Threat Detection）。
  - Agent 身份与审计。
  - 对技能市场做签名和审核。
  - 自动安全审查器（类似 Grok Bot 的 Auto-review）。
- OpenClaw 文档的立场有参考价值：它是"单一可信操作者"模型，并不提供多租户隔离。企业平台必须自己补上这一层。

---

# 4. 产品定位差异

| 维度 | 光谱 | 代表 |
|---|---|---|
| 目标用户 | 开发者 ←→ 业务用户 ←→ 消费者 ←→ 企业 IT | 开发者：LangGraph、Agents SDK、E2B、Temporal；业务用户：Zapier、n8n、扣子、Lindy；消费者：Manus、Genspark、Comet、OpenClaw；企业 IT：Agent 365、Gemini Enterprise、AgentCore、UiPath |
| 确定性程度 | 确定性流程 ←→ 混合 ←→ 完全自主 | n8n、UiPath 偏确定；AI by Zapier、Coze 混合；Manus、Cowork、Codex 偏自主 |
| 水平/垂直 | 通用 ←→ 领域 | 通用：Manus、Cowork；垂直：Agentforce（CRM）、Workday + Flowise（HR/财务）、Glean（知识） |
| 部署 | SaaS ←→ 私有云 ←→ 开源自托管 | SaaS：大多数；VPC：Managed Agents、Agents API 自选计算；开源：Dify、Coze Studio、n8n（fair-code）、OpenClaw、Open-AutoGLM |
| 生态锚点 | 以办公套件/数据为中心 | Microsoft（M365 Work IQ）、Google（Workspace/BigQuery）、Salesforce（CRM）、字节（飞书）、腾讯（微信/企微）、阿里（钉钉） |
| 计费 | 席位 ←→ 用量 | 见 2.6 |

可以观察到三点：
- 平台型大厂的护城河是**企业上下文和合规边界**（Work IQ、M365 合规栈）。
- 创业公司的护城河在于**体验与速度**（Manus、Genspark）或者**开源社区**（n8n、Dify、OpenClaw）。
- 中国大厂的主要抓手是**IM 入口**（微信、QQ、飞书、钉钉）加**云资源售卖**。

---

# 5. 关键产品对比表

| # | 产品 | 类别 | 目标用户 | 编排方式 | 执行环境 | 集成方式 | 开源 | 计费模式 |
|---|---|---|---|---|---|---|---|---|
| 1 | OpenAI Codex Cloud / workspace agents | (a) | 开发者 / 企业团队 | LLM 循环 + 子 Agent；定时/Slack 触发 | OpenAI 托管持久云环境 | 连接器（MCP）、Slack、GitHub | Codex harness 开源 | 订阅 + credits |
| 2 | Anthropic Claude Cowork / Code / Routines | (a) | 知识工作者 / 开发者 | LLM 循环（Claude Code harness）+ Skills | 本地文件夹 + 云端 + 内置浏览器 | MCP 连接器、Chrome | Agent SDK 开源；产品闭源 | Pro/Max/Team 订阅 |
| 3 | Microsoft Copilot Cowork + Agent 365 | (a)/(c) | 企业员工 / IT | LLM 循环，多模型 | 云托管，Edge 本地浏览 | Work IQ、M365、插件 | 否 | Copilot USL + 用量 credits（0.01 美元/credit） |
| 4 | Google Gemini Enterprise + Agent Platform | (c) | 企业 IT / 开发者 | 生成式 + 确定性编排；ADK 图式 | Agent Runtime（多日）、Agent Sandbox | MCP、原生集成、A2A、AP2 | ADK 开源 | 21–30 美元/用户/月 + 云用量 |
| 5 | Manus 2.0（含 Cue） | (a) | 消费者 / 小团队 | LLM 循环（Cascade），多 Agent 团队 | 云 VM、Cloud Computer、本地 Computer Use | 连接器、浏览器扩展 | 否 | credits + Cloud Computer 月费 |
| 6 | Genspark Claw / AI Workspace | (a) | 业务用户 | LLM 多 Agent | 云端 | 多工具 | 否 | 订阅（详情待核实） |
| 7 | Perplexity Comet | (a) | 消费者 / 企业 | 浏览器内 Agent | 本地 AI 浏览器 | Web | 否 | 免费 + Pro/Max/Enterprise |
| 8 | OpenClaw | (a)/(e) | 极客 / 个人 | LLM 循环 + 技能 + IM 网关 | 自托管（本地/VPS） | IM、浏览器、技能（ClawHub） | 是 | 免费（自付模型费用） |
| 9 | Zapier（AI by Zapier） | (b) | 业务用户 | DAG + Agent 步骤（混合） | Zapier 云 | 9000+ 应用、MCP | 否 | 按 task |
| 10 | n8n | (b) | 技术型业务 / 开发者 | DAG + AI Agent 节点 | 云或自托管 | 节点库、MCP | fair-code | 按执行次数；社区版免费 |
| 11 | UiPath Agent Builder + Maestro | (b) | 企业自动化中心 | BPMN / 流程 + Agent + RPA | 云 / 本地机器人 | RPA、API、MCP | 否 | 企业许可 |
| 12 | OpenAI AgentKit / Agents API | (c)/(d) | 开发者 | 可视化画布 / 托管 harness | OpenAI 沙箱或自有 | Connector Registry、MCP | SDK 开源 | API 用量 |
| 13 | AWS Bedrock AgentCore | (c)/(d) | 企业开发者 | 框架无关运行时 | microVM Runtime | Gateway（MCP）、Identity | 否 | 按资源/调用 |
| 14 | Salesforce Agentforce | (c) 垂直 | CRM 企业 | 主题/动作 + LLM | Salesforce 云 | Salesforce 数据、MCP | 否 | Flex Credits（约 0.10 美元/动作） |
| 15 | Dify | (c) | 开发者 / 业务 | 可视化工作流 + Agent | 云或自托管 | 插件、MCP | 是（开源许可附条件） | 开源 + SaaS / 企业版 |
| 16 | 豆包工作（原扣子 Coze 2.0→3.0，2026-08 并入豆包）/ Coze Studio | (c)/(e) | 业务用户 / 开发者 | 工作流 + Agent Plan + Skills | 字节云；开源可自托管 | 插件、飞书、MCP | Studio/Loop 采用 Apache-2.0 | 订阅 + 开源 |
| 17 | 阿里云百炼 Agent Studio | (c)/(e) | 企业开发者 | 规划-执行-反思 Agent + 工作流 | 阿里云沙箱 | MCP、Skill、Connector、钉钉 | 否 | 云用量 |
| 18 | 腾讯 WorkBuddy / 元器 | (a)/(c)/(e) | 个人 / 企业微信用户 | OpenClaw 兼容 Agent / 低代码 | 本地 + 腾讯云 | 微信、企微、QQ、飞书 | 部分 | credits / 云资源 |
| 19 | LangGraph | (d) | 开发者 | 图（状态机）+ 持久化 checkpoint | 自部署 / LangGraph Platform | 任意 | 是（MIT） | 开源 + 平台/LangSmith 订阅 |
| 20 | Temporal | (d) | 平台工程 | 代码即工作流（事件溯源） | 自托管 / Cloud | SDK | 是（MIT） | 开源 + Cloud 用量 |
| 21 | E2B / Daytona | (d) | 开发者 | — | microVM / 有状态沙箱 | SDK | 部分开源 | 按沙箱时长 |

> 注：Dify 的许可证是在 Apache-2.0 基础上附加条件，用于多租户 SaaS 或去品牌化需要另行授权。这一点基于训练知识，**[请以仓库 LICENSE 为准]**。Genspark 的具体价格未核实。

---

# 6. 给内部团队的观察（供第 2、3 步参考，不作结论）

**定位相关**

1. **"每个 bot 一台持久电脑 + 连接器 + 后台/定时 + 技能 + 审批"已经是外部头部产品的标配**（Cowork、Copilot Cowork、Codex Cloud、Manus 2.0、豆包工作 / 扣子）。内部平台的差异化不太可能来自这些能力本身，更可能来自：**企业内部系统和数据的深度接入、身份/权限/审计和公司 IAM 打通、合规数据边界、成本可控**。
2. 头部厂商在不断把独立 Agent 产品**收编**（Operator、Atlas、Zapier Agents、Mariner）。这意味着内部平台最好挂在员工已有的入口上，比如 IM（飞书、企微、Slack）、桌面端、现有工作流系统，而不是再做一个孤立入口。
3. 用户群体需要分层，至少有三类：**开发者**（要 API/SDK、CLI 和代码 harness）、**业务用户**（要模板、技能和可视化的混合流程）、**IT/安全**（要控制平面）。外部厂商一般用两到三个产品分别覆盖这三类。

**技术相关**

4. **混合编排是共识**。需要一个确定性的"骨架层"（触发器、审批、结构化 I/O、预算上限），再加一个 LLM Agent 循环层。两者之间用技能（SKILL.md）和工作流节点互相调用。
5. 架构上值得参考 **Anthropic 的 session / harness / sandbox 三分离**和"凭证不进沙箱"（vault 加 MCP 代理）。持久化执行可以评估 Temporal、LangGraph checkpoint 或自研事件日志。
6. **开放标准优先**：MCP（对齐 2026-07-28 版规范和 OAuth）、Agent Skills、AGENTS.md，A2A 可以作为可选项。这能降低锁定风险，也能复用外部生态的连接器和技能。
7. **自建、托管还是开源**的取舍，可以参考这些成熟组件：托管 runtime（AgentCore、Gemini Agent Runtime、Claude Managed Agents、OpenAI Agents API）、开源平台（Dify、Coze Studio、n8n，需注意 fair-code 限制）、沙箱（E2B、Daytona）。
8. **安全是一等需求**。OpenClaw 的教训是：技能和插件供应链、单租户安全模型、本地执行误删数据，都是真实发生过的事故。审批、审计、注入防护和自动安全审查需要在第一版就设计进去。
9. **成本模型**：外部全面转向按用量计费，并配了预算、上限和单任务成本可见性。内部平台同样需要做租户、团队、用户三级预算，以及任务级成本观测。
10. 中国区可用性和合规（数据出境、模型备案）会影响模型和供应商选择。Manus 交易被叫停说明，跨境依赖存在政策风险。国内大厂的"龙虾"产品和百炼、豆包工作（含扣子）可以作为国内对标和备选。

---

# 附：主要来源清单

- OpenAI：[ChatGPT agent](https://help.openai.com/en/articles/11752874-chatgpt-agent)｜[Atlas 废弃](https://help.openai.com/en/articles/20001371-evolving-atlas-into-chatgpt-for-browser-based-agentic-work)｜[Workspace agents](https://openai.com/index/introducing-workspace-agents-in-chatgpt/)｜[Agents API](https://openai.com/index/introducing-the-agents-api/)｜[AgentKit](https://openai.com/index/introducing-agentkit/)｜[Codex Cloud](https://help.openai.com/en/articles/20001545-using-codex-cloud)
- Anthropic：[Cowork](https://claude.com/product/cowork)｜[Managed Agents 工程博客](https://www.anthropic.com/engineering/managed-agents)｜[Routines](https://claude.com/blog/introducing-routines-in-claude-code)｜[Claude in Chrome GA](https://claude.com/blog/claude-in-chrome-generally-available)｜[MCP 捐赠](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)
- Microsoft：[Copilot Cowork GA](https://www.microsoft.com/en-us/microsoft-365/blog/2026/06/16/copilot-cowork-is-now-generally-available/)｜[Agent 365](https://www.microsoft.com/en-us/microsoft-agent-365)｜[Agent Framework 1.0](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)
- Google：[Gemini Enterprise Agent Platform](https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform)｜[定价](https://cloud.google.com/gemini-enterprise/business)
- AWS：[AgentCore 定价](https://aws.amazon.com/bedrock/agentcore/pricing/)
- 协议：[AAIF 成立](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)｜[A2A 加入 AAIF](https://aaif.io/blog/a2a-joins-aaif)｜[MCP 2026-07-28](https://blog.modelcontextprotocol.io/posts/2026-07-28/)｜[Agent Skills](https://agentskills.io/specification)
- 工作流：[Zapier 迁移](https://help.zapier.com/hc/en-us/articles/47402591569805-Migrating-from-Agents-to-AI-by-Zapier)｜[n8n C 轮](https://blog.n8n.io/series-c/)｜[n8n x SAP](https://blog.n8n.io/n8n-sap/)｜[UiPath Maestro](https://www.uipath.com/product/maestro/flow)
- 初创与中国：[Manus 2.0](https://help.manus.im/en/articles/17190150-what-is-new-in-manus-2-0)｜[Reuters：叫停 Manus 收购](https://www.reuters.com/world/asia-pacific/china-blocks-foreign-acquisition-ai-startup-manus-2026-04-27/)｜[Genspark](https://www.businesswire.com/news/home/20260617758937/en/)｜[36氪：大厂养龙虾](https://www.36kr.com/p/3715653109200263)｜[扣子 2.0](https://finance.sina.com.cn/tech/it/2026-01-19/doc-inhhvwpt6817994.shtml)｜[扣子 3.0](https://www.ithome.com/0/958/277.htm)｜[扣子/TRAE 并入豆包](https://finance.sina.com.cn/stock/t/2026-08-24/doc-inipmnpq6049441.shtml)｜[豆包工作](https://www.feishu.cn/content/article/7677519271848610746)｜[Coze Studio](https://github.com/coze-dev/coze-studio)｜[Open-AutoGLM](https://github.com/zai-org/Open-AutoGLM)｜[百炼 Agent Studio](https://developer.aliyun.com/article/1763850)｜[Dify 融资](https://dify.ai/blog/dify-raises-30m-tomorrow-s-organizations-will-be-built-by-people-and-agents)
- 基础设施：[Temporal E 轮](https://temporal.io/blog/temporal-raises-usd550m-series-e-at-usd12-55b-valuation-ai)｜[LangChain 1.0](https://www.langchain.com/blog/langchain-langgraph-1dot0)｜[Daytona](https://www.prnewswire.com/news-releases/daytona-raises-24m-series-a-to-give-every-agent-a-computer-302680740.html)｜[E2B](https://e2b.dev/resources/series-a)
- 行业：[Gartner 40% 预测](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)｜[OpenClaw 安全](https://docs.openclaw.ai/security)｜[GitHub Blog：OpenClaw](https://github.blog/open-source/maintainers/openclaw-went-viral-meet-the-maintainers-building-and-securing-it/)
