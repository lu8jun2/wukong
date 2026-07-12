# 悟空多 Agent 调度使用说明

这份文档用于实际运行 `$multi-agent-wukong`。悟空只作为多 Agent 调度控制面，负责需求确认、任务拆分、任务板、派工、状态监控、冲突协调和结果汇总；所有实质工作由 Subagent 完成。

## 一句话启动

在任何需要多 Agent 协作的项目里，可以这样要求 Codex：

```text
使用 $multi-agent-wukong 调度这个任务。
先深入拆解目标、范围、交付物、限制条件、非目标和验收标准，再给出任务板草案并等待我用自然语言明确同意开始；不要求固定口令。
确认前不得派工或执行实质工作；确认后所有实质工作都交给任务相关 Subagent。
如果可以并行，按角色派工；如果不能并行，则派给 Subagent 串行执行。
实施完成后，另派一个未参与实施的 Subagent 独立验证。
最后汇总 Subagent 返回的验证证据和未解决风险。
```

## 核心模型

悟空是控制面，不是执行面。

```text
用户目标
  -> 悟空深入确认目标、范围、交付物、约束、非目标、验收标准
  -> 悟空选择编排模式
  -> 悟空给出任务板草案并等待用户用自然语言明确同意按所示范围开始
  -> 确认后悟空装配上下文包并派工
  -> 唐僧 / 猪八戒 / 白龙马 / 嫦娥 / 观音 / 太上老君 / 二郎神 / 沙僧 / 哪吒执行各自任务
  -> 独立于实施者的验证 Subagent 执行验证
  -> 如需写回，由获派 Subagent 执行
  -> 悟空收敛报告、协调冲突
  -> 悟空汇报证据和风险
```

## 什么时候使用

适合使用：

- 任务有多个独立分析面，例如架构、实现、测试、业务、文档。
- PR review 需要安全、质量、测试缺口、可维护性分开看。
- 多个失败测试可能有不同 root cause。
- 大型需求需要先拆任务，再由不同角色推进。
- 同一个项目会持续多轮工作，需要记住任务状态、决策和事实。
- 长研究、跨源调研、竞品/技术/市场扫描、流程化设计或自动化流程需要 DeerFlow 推演。

不要机械扩张角色：

- 任务很小时，只派一个任务相关 Subagent，不由悟空直接处理。
- 多个 Subagent 会改同一批文件时，改为串行派工或拆分所有权。
- 一个 Subagent 的输出决定另一个 Subagent 的输入时，使用顺序流水线。
- 没有明确验收标准、测试、人工确认或其他验证 oracle 时，先在确认门前澄清，不得开始执行。

## 角色分工

| 角色 | 主要职责 | 典型任务 | 不能做 |
|---|---|---|---|
| 悟空 - 总调度者 | 目标确认、任务拆分、上下文装配、派工、状态监控、冲突协调、结果汇总 | 建任务板、选编排模式、汇总报告、最终沟通 | 不执行调研、命令、文件读写、编码、测试、浏览器或验证，也不做失败回退执行 |
| 唐僧 - 系统架构师 | 架构方向、模块边界、接口不变量、长期结构 | 画模块边界、识别依赖、定义并行切片 | 不做大范围实现 |
| 猪八戒 - 核心开发者 | 核心逻辑、复杂实现、算法、成本和复杂度取舍 | 实现核心模块、修复杂 bug、补行为测试 | 不改产品范围，不越界改文件 |
| 白龙马 - 产品执行者 | 稳定执行、机械任务、脚手架、配置、简单页面 | 创建文件、跑命令、搭 demo、整理目录 | 不重新设计架构 |
| 嫦娥 - UI 交互与视觉总监 | 前端设计、UI交互、设计系统、动效渲染、视觉验收 | 设计页面、把控交互、维护 DESIGN.md/design.md、制作 Remotion/HyperFrames 动效、调用 Vibe Motion 子技能 | 不负责后端 API、数据库、云部署 |
| 观音 - 业务规划师 | 业务目标、协议语义、内容策略、验收标准、风险判断 | 梳理 MVP、需求矩阵、API 语义、文档口径 | 不写代码，不覆盖技术证据 |
| 太上老君 - 长研究与流程编排师 | 长研究、流程化、跨源调研、工作流设计、DeerFlow 推演 | 做深度研究、整理来源、设计 SOP、优化流程；仅在 `ALLOWED` 且 `Role` 明确授权子协调器时调用研究/流程外援 | 不替悟空总控，不替其他角色做最终业务/法务/架构/部署决策 |
| 二郎神 - 云平台与后端部署专家 | 云平台、API 调用、后台服务、数据库、CI/CD、运维验证 | 设计部署拓扑、API 合约、DB schema、迁移、健康检查、回滚 | 不负责 UI 视觉和前端交互 |
| 沙僧 - 全能兜底者 | 调试、恢复、验证、证据、交接记录 | 复现失败、定位 root cause、跑测试、整理日志 | 不成为默认实现者 |
| 哪吒 - 经营合规与组织事务官 | 财务、法务、行政、人事、采购、隐私和组织运营风险 | 做预算、审合同风险、列合规清单、写招聘/入离职/行政流程 | 不给正式法律/税务/会计/劳动争议结论，不做绑定审批 |

## 编排模式选择

| 模式 | 使用条件 | 示例 |
|---|---|---|
| 单 Subagent | 任务小、强耦合、共享同一写入面 | 派白龙马修改一个配置项，再派独立验证者检查 |
| 顺序流水线 | 每一步依赖上一步产物 | 观音需求 -> 唐僧架构 -> 猪八戒实现 -> 沙僧验证 |
| Fan-out / Fan-in | 多个独立任务可并行，最后合并 | 安全 review、测试缺口 review、可维护性 review |
| Supervisor Loop | 下一步取决于中间证据 | 沙僧复现失败后，悟空决定派八戒修还是唐僧重审边界 |
| Debate / 多视角评审 | 需要判断而不是并行改代码 | 唐僧和观音分别评估 API 设计，悟空裁决 |

默认原则：选择最简单、能保证上下文隔离和验证闭环的模式。

## 严格确认门

每个新的 user-facing 任务都先拆解目标、范围、交付物、限制条件、非目标和验收标准，并向用户提问确认。用户用自然语言明确同意执行即可打开执行门，不要求固定口令；“是的，确认”“确认”“按这个执行”“开始吧”等直接同意均有效。含糊回复、条件性回复、提问、沉默，或改变范围、成本、时限、风险的回复，需要先澄清并按变更后的任务重新确认。

确认前只允许：加载技能、纯需求澄清、起草任务板，以及最小化检查 Subagent 调度工具是否可调用。确认前禁止派发执行型 Subagent，也禁止调研、运行命令、读取仓库状态、权限、写入面、目标文件、业务上下文或其他任务文件，禁止编码、测试、浏览器操作和验证；这些 readiness/inspection 工作只能在确认后由 Subagent 执行。

确认后，悟空仍不得亲自执行实质任务。简单问答、单条命令、单文件小改也必须至少派一个任务相关 Subagent；“全量调用”只要求覆盖任务需要的角色，不要求机械调用所有角色。

Subagent 不可用、超时、失败或返回 `BLOCKED` 时，悟空必须报告阻塞并等待用户决定，禁止直接回退执行。实施结果必须交给未参与实施的另一个 Subagent 独立验证。

`NEEDS_CONTEXT` 只能在原任务包的范围、成本、风险和写入面内补充上下文并重派；任一边界变化都必须回到 user-facing confirmation gate，取得新的明确确认后再派发。

确认门只由 user-facing 悟空执行。每个执行任务包必须携带原始确认文本，并包含 `Authorization status: CONFIRMED_BY_USER`、`Authorization issuer: USER_FACING_WUKONG`、`Parent task ID:`、`Confirmation evidence:`、`Delegation permission:`。授权来源字段只是 coordination contract，不是 security boundary。worker 只接受 user-facing Wukong 发出的、来源和父任务一致的任务包；字段缺失或冲突时返回 `BLOCKED` 或 `NEEDS_CONTEXT`，不得自行声明或升级授权。收到有效已确认任务包的普通执行或验证 Subagent 继承父任务授权，直接执行获派角色，不得扮演悟空、重复拆解或再次索要确认。派发权限默认 `FORBIDDEN`；只有任务包明确写 `Delegation permission: ALLOWED`，且 `Role` 明确授权该 worker 为子协调器时才能继续派发。Agency Agents、外援、研究代理和 DeerFlow 子调用全部受这一双条件硬门约束。

## 标准运行流程

### 1. 确认门与 Post-Confirmation Harness Readiness Check

确认门前，悟空只能加载适用技能、澄清纯需求、起草任务板，并最小化确认 Subagent 调度工具是否可调用；不得填写需要读取仓库、权限、写入面、目标文件或业务上下文的 readiness 字段。用户确认后，悟空派 Subagent 完成：

```text
Objective:
Available delegation tools:
Callable agent types:
Risky operations needing confirmation:
Verification oracle:
Max useful concurrency:
Timeout/stop condition:
If delegation is unavailable: report BLOCKED and wait; no Wukong fallback
```

仓库状态、权限、写入面等需要读取或运行命令的信息，必须在用户明确同意开始后交给 Subagent 检查。如果缺少验证 oracle，先补验收标准，不要派工实现。

### 2. 建任务板

每个 workstream 必须有明确所有权：

```text
Task ID:
Role:
Authorization status: CONFIRMED_BY_USER
Authorization issuer: USER_FACING_WUKONG
Parent task ID:
Confirmation evidence: [用户原始确认文本]
Delegation permission: FORBIDDEN
Inputs:
Forbidden scope:
Independent verifier:
Mission:
Read scope:
Write scope:
Dependencies:
Expected output:
Verification:
Timeout/stop condition:
Fallback/escalation:
```

写代码时，两个 agent 不能拥有同一个文件、模块、文档段落或外部资源。

### 3. 装配 Context Packet

每个 agent 只拿自己需要的上下文：

```text
Task ID:
Role:
Authorization status: CONFIRMED_BY_USER
Authorization issuer: USER_FACING_WUKONG
Parent task ID:
Confirmation evidence: [用户原始确认文本]
Delegation permission: FORBIDDEN
Inputs:
Forbidden scope:
Independent verifier:
Mission:
Current state:
Relevant long-term memories:
Shared facts and evidence:
Relevant paths/resources:
Known facts:
User constraints:
Non-goals:
Allowed actions:
Forbidden actions:
Expected output schema:
Validation signal:
Timeout or stop condition:
Fallback/escalation path:
Writeback proposals allowed:
```

不要把完整父对话倾倒给每个 agent。上下文包越窄，结果越稳定。

### 4. 派工

Read-only 任务优先使用 explorer 类型 agent；实现任务使用 worker 类型 agent。

普通 worker 在任务包授权范围内直接执行，不运行确认门，也不继续派发。验证 Subagent 本身就是验证执行者，不依赖更下一级 Subagent；即使没有可调用的下级 Subagent，也必须执行获派验证，不得仅因此返回 `BLOCKED`。

代码派工必须包含：

```text
You are not alone in the codebase.
Do not revert changes made by others.
Work only inside your assigned ownership boundary.
If another change affects your task, adapt and report the dependency instead of overwriting it.
```

### 5. 收敛报告和协调冲突

悟空只根据角色返回报告协调：

- 是否报告越界修改。
- 是否附有证据。
- 是否和其他角色结论冲突。
- 独立验证者是否报告满足验收标准。
- 是否需要补派工。
- 是否有记忆或事实需要写回。

### 6. 独立验证和汇报

实施 Subagent 返回后，悟空必须另派一个未参与实施的 Subagent 执行测试、命令、文件检查、浏览器检查或其他任务相关验证。悟空不得亲自验证。

验证任务包同样必须携带 `Authorization status: CONFIRMED_BY_USER`、`Authorization issuer: USER_FACING_WUKONG`、`Parent task ID:`、原始 `Confirmation evidence:` 和 `Delegation permission:`。验证者直接运行任务相关验证，不重新询问用户或悟空确认。

最终汇报必须包含：

```text
Completed:
Not completed:
Role outputs integrated:
Key decisions:
Verification evidence:
Risks:
User decisions needed:
Recommended next step:
```

没有新鲜验证证据，不要说完成。

## C-lite Context Stack

C-lite 是本地可运行的上下文调度原型，后续可以替换成真实 LangGraph / mem0 / Graphiti 后端。

| 层 | 对应未来后端 | 当前文件 | 用途 |
|---|---|---|---|
| Current State | LangGraph | `state store` | 任务状态、依赖、写范围、验证路径 |
| Long-Term Memory | mem0 | `memory store` | 用户偏好、项目习惯、历史决策、经验教训 |
| Shared Facts | Graphiti | `facts store` | 有证据的实体关系、时间事实、置信度 |

### 初始化

用户确认后，派给上下文状态 worker 在项目根目录运行：

```powershell
python <skill-root>\scripts\wukong_context_orchestrator.py --root .wukong-context init
```

### 写入当前任务状态

```powershell
python <skill-root>\scripts\wukong_context_orchestrator.py --root .wukong-context task `
  --id T1 `
  --role 唐僧 `
  --mission "Map module boundaries for the payment refactor" `
  --status running `
  --write-scope "docs/architecture/payment-boundaries.md" `
  --validation "architecture checklist reviewed by independent verifier"
```

### 写入长期记忆

悟空只协调是否批准写入；获派的上下文状态 worker 执行命令：

```powershell
python <skill-root>\scripts\wukong_context_orchestrator.py --root .wukong-context memory `
  --scope project `
  --text "This repo requires npm test before reporting completion." `
  --actor context-state-worker `
  --evidence "package.json scripts and prior user instruction"
```

### 写入共享事实

事实必须有 subject、predicate、object、evidence、confidence：

```powershell
python <skill-root>\scripts\wukong_context_orchestrator.py --root .wukong-context fact `
  --subject payment-service `
  --predicate depends_on `
  --object auth-service `
  --actor context-state-worker `
  --evidence "src/payment/client.ts import graph" `
  --confidence 0.9
```

### 生成角色上下文包

```powershell
python <skill-root>\scripts\wukong_context_orchestrator.py --root .wukong-context packet `
  --task-id T1 `
  --role 唐僧 `
  --query "payment module boundaries"
```

上下文状态 worker 把输出返回给悟空；悟空将摘要放入派工 prompt，不把完整父对话倾倒给 Subagent。

## 写回规则

| 写回类型 | 谁能写 | 什么时候写 | 示例 |
|---|---|---|---|
| State | 获派的上下文状态 worker | 悟空协调批准后，任务状态、依赖、验证路径变化 | `T2 -> blocked` |
| Memory | 获派的上下文状态 worker | 用户明确允许且悟空协调批准后，跨任务仍有价值的经验或偏好 | `用户偏好先看计划再实现` |
| Fact | 获派的上下文状态 worker | 独立验证证据充分且悟空协调批准后 | `module-a depends_on module-b` |

角色可以提议写回；只有获派且获批的上下文状态 worker 可以实际写入：

```text
Writeback proposal:
- State update:
- Durable memory:
- Shared fact:
- Evidence:
```

悟空协调写回决定，worker 执行写回。不要保存未经独立验证的猜测。

## 外援库映射

Agency Agents 外援不是新的常驻角色，而是挂在现有 Wukong 角色下面的专项能力。映射源：

- 人读：`references/agency-agent-role-map.md`
- 机器校验：`references/agency-agent-role-map.json`
- 重新生成：`python -X utf8 <skill-root>\scripts\generate_agency_agent_role_map.py`

调用逻辑：

1. 悟空先判断任务类型和常驻主责角色。
2. 若需要外援，确认后派 Subagent 查 `agency-agent-role-map.json`，确认该 agent 的 primary role；这一步只读映射，不授予继续派发权。
3. 只有任务包同时写明 `Delegation permission: ALLOWED`，且 `Role` 明确授权该 worker 为子协调器时，primary role 才可调用 Agency Agents、外援、研究代理或 DeerFlow 子调用；缺一条件即按默认 `Delegation permission: FORBIDDEN` 执行，不得继续派发。
4. 获得双条件授权的 primary role 负责给外援装配窄 context packet、边界、输出格式和验证方式。
5. secondary roles 只检查交叉风险，例如合规、平台、体验或证据。
6. 悟空最终收敛外援结果，不能让外援直接变成总控。

## 常见场景

### 场景 A：并行 PR Review

```text
使用 $multi-agent-wukong review 当前分支。
并行派：
1. 唐僧：架构和边界风险
2. 沙僧：测试缺口和可复现问题
3. 观音：业务/协议语义风险
4. 猪八戒：复杂度和实现成本风险
5. 太上老君：长研究/流程化/自动化治理风险（当 PR 涉及研究流程、自动化流程或反复执行 SOP 时）
6. 哪吒：财务/法务/行政/人事/隐私风险（当 PR 涉及经营、合同、组织或数据处理时）
悟空等待全部结果，合并成按严重度排序的 finding。
```

### 场景 B：复杂功能实现

```text
使用 $multi-agent-wukong 实现这个功能。
先由观音定义验收标准，唐僧定义模块边界。
如果涉及前端设计和 UI 交互，嫦娥先定义 DESIGN.md/design.md、交互状态和视觉验收。
如果涉及云平台、API、后台服务或数据库，二郎神先定义部署/API/DB 边界和验证方式。
如果涉及长研究、流程化、跨源调研、自动化流程、周期性任务或 DeerFlow 推演，太上老君先定义研究计划、流程地图、证据路径和停止条件。
如果涉及预算、合同、采购、隐私、招聘、绩效、入离职或组织流程，哪吒先定义财务/法务/行政/人事风险边界和需要专业确认的事项。
只有边界和验收标准明确后，猪八戒实现核心逻辑，白龙马做机械接线，沙僧负责验证。
使用 C-lite context stack 记录状态和关键事实。
```

### 场景 B2：产品 UI 和交互动效

```text
使用 $multi-agent-wukong 处理这个前端体验任务。
嫦娥负责所有前端设计、UI交互、设计系统、动效和渲染验收。
她必须读取 DESIGN.md/design.md；如果不存在，先提出最小设计系统。
需要视频、动效、转场或演示时，使用 Remotion 或 HyperFrames，并提供 render/inspect/browser 证据。
如果需要专项动效，优先使用官方 `vibe-motion/skills`：pixel2motion、light-spotlight-render、threejs-earth-render、svg-assembly-animator、remotion-3d-ticker、wechat-2d-render 等。
悟空只负责派工并汇总独立验收报告，不让其他角色绕过嫦娥交付用户可见 UI。
```

### 场景 B2.1：Vibe Motion 子技能路由

```text
使用 $multi-agent-wukong 处理这个 motion 任务。
嫦娥先判断是否需要 Vibe Motion：
- 图片、截图、产品帧转动效：pixel2motion。
- 聚光、灯效、舞台感渲染：light-spotlight-render。
- 3D 地球、全球化、轨道视效：threejs-earth-render。
- SVG 组装、线条生长、结构拆装：svg-assembly-animator。
- Remotion 3D ticker 或唱片机风格：remotion-3d-ticker / remotion-vinyl-player。
- 聊天、微信、对话场景：wechat-2d-render。
嫦娥必须输出所选子技能、输入素材、生成路径、render/inspect/browser 证据和残余风险。
```

### 场景 B2.2：Chang'e Product Design 强制门

```text
任何 Role=嫦娥/Chang'e 的 design-start 任务，无论规模为 S、M、L 还是 XL，必须先设置 product_design_plugin_required=true，并在产生任何设计 artifact 前实际调用 Product Design plugin。
只记录 plugin metadata、capability evaluation 或 selection 不算 invocation；必须提供 invocation_evidence。
任务包和 handoff 必须携带 plugin id/version、tool-call id、timestamp、input digest、artifact paths/hashes、output validation、confirmation evidence、dependency status/evidence。
Product Design runtime unavailable、authentication failure 或 tool-call failure 时，立即返回 BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE；不得自动改用 Figma 或 Claude Design，除非用户明确确认替代方案。
```

### 场景 B3：云平台、API、后台和数据库

```text
使用 $multi-agent-wukong 处理这个部署/后端任务。
二郎神负责云平台部署、API 调用、后台服务、数据库、CI/CD、secrets、日志、监控和回滚。
他必须给出平台拓扑、API 合约、DB migration/rollback、环境变量清单和 health check。
涉及生产破坏性操作时，先请求悟空/用户确认。
最终必须有 live URL、API response、migration result、health check 或日志证据。
```

### 场景 B4：财务、法务、行政、人事

```text
使用 $multi-agent-wukong 处理这个经营合规/组织事务任务。
哪吒负责财务预算、合同初审、合规清单、行政流程、人事制度、招聘/入离职和采购/供应商风险。
需要专项外援时，只有任务包同时包含 `Delegation permission: ALLOWED` 且 `Role` 明确授权哪吒为子协调器，哪吒才可调用 Agency Agents：Chief Financial Officer、Financial Analyst、FP&A Analyst、Bookkeeper & Controller、Tax Strategist、Legal Compliance Checker、Legal Document Review、Data Privacy Officer、HR Onboarding、Recruitment Specialist。
哪吒必须标出假设、适用范围、证据路径、风险等级、用户决策点，以及需要律师/会计/税务/劳动法或隐私专业人士确认的事项。
哪吒不做绑定付款、合同审批、雇佣/解雇、薪酬发放或正式法律/税务/会计结论。
```

### 场景 B5：长研究、流程化和 DeerFlow

```text
使用 $multi-agent-wukong 处理这个长研究/流程化任务。
太上老君负责长研究、跨源调研、流程化、工作流设计、SOP、自动化流程和多步推演。
DeerFlow 是太上老君的核心技能：可在获派范围内直接使用技能或工具；任何 DeerFlow child-agent/harness 子调用都必须同时具备 `Delegation permission: ALLOWED` 和明确授权子协调器的 `Role`。
需要专项外援时，也只有满足同一双条件硬门，太上老君才可调用 Agency Agents：Trend Researcher、Investment Researcher、Search Query Analyst、AI Citation Strategist、Agents Orchestrator、Workflow Architect、Workflow Optimizer、Automation Governance Architect、Project Shepherd、Senior Project Manager、Business Strategist、Analytics Reporter、Data Engineer、Data Consolidation Agent、Document Generator、Threat Intelligence Analyst。
太上老君必须输出研究问题、来源路径、置信度、未决问题、DeerFlow 运行摘要、流程图/SOP、下一轮研究条件和停止条件。
太上老君不替悟空总控，不替观音做最终业务裁决，不替唐僧做架构裁决，不替二郎神做部署裁决，不替哪吒做法务/财务/人事合规裁决。
```

### 场景 C：多个测试失败

```text
使用 $multi-agent-wukong 诊断失败测试。
先由沙僧分类失败。
如果失败彼此独立，fan-out 给多个 worker。
如果同一 root cause，串行修复。
每个修复必须给出复现、root cause、验证命令。
```

### 场景 D：长期项目推进

场景 D 必须先完成确认门；确认前不得读取业务上下文，确认后才可由 Subagent 读取项目状态、长期记忆和共享事实。

```text
使用 $multi-agent-wukong 继续这个项目。
先完成确认门；确认后派 Subagent 读取 .wukong-context 当前状态、长期记忆和共享事实。
给我当前任务板、阻塞点、下一步建议。
只在状态不明确时问我。
```

## 冲突处理

| 冲突 | 悟空处理方式 |
|---|---|
| 两个 agent 要改同一文件 | 停止并行，拆分文件段落或串行 |
| 记忆和当前状态冲突 | 当前状态优先 |
| 共享事实互相矛盾 | 新鲜证据优先；保留旧事实但标记失效或风险 |
| UI 方案和技术实现冲突 | 嫦娥负责用户体验目标，唐僧/猪八戒评估技术边界，悟空裁决 |
| 长研究/流程化结论和业务/技术目标冲突 | 太上老君负责研究证据、流程地图和 DeerFlow 推演路径，观音/唐僧/二郎神评估业务、架构和平台约束，悟空裁决 |
| 部署方案和产品目标冲突 | 二郎神负责平台可行性，观音负责业务价值，悟空裁决 |
| 经营合规和产品/技术目标冲突 | 哪吒负责财务、法务、行政、人事风险边界，观音/唐僧/二郎神评估价值和技术可行性，悟空裁决 |
| agent 报告成功但无证据 | 派独立的沙僧或其他验证 Subagent 验证 |
| agent BLOCKED | 分类为缺上下文、权限问题、错误角色、无效拆分、验证失败或计划错误 |

## 验收清单

悟空汇报前检查：

- [ ] 任务目标、非目标和验收标准明确。
- [ ] 每个 workstream 有 owner、read scope、write scope、verification。
- [ ] 每个执行和验证任务包都携带 `CONFIRMED_BY_USER`、原始确认证据和派发权限；普通 worker 不重复确认。
- [ ] 并行任务没有共享写入面。
- [ ] 每个 role 输出包含 `Status`、`Evidence`、`Risks`。
- [ ] 前端设计、UI 交互、动效或渲染任务经过嫦娥验收。
- [ ] 长研究、跨源调研、流程化、自动化流程或 DeerFlow 任务经过太上老君验收，并保留来源路径、流程图/SOP 和停止条件。
- [ ] 云平台、API、后台服务或数据库任务经过二郎神验收。
- [ ] 财务、法务、行政、人事、采购、隐私或组织流程任务经过哪吒风险检查，并标出专业确认边界。
- [ ] 未参与实施的独立验证 Subagent 运行了相关验证。
- [ ] 需要写回的状态、记忆、事实已经过悟空批准。
- [ ] 最终报告包含未完成项和残余风险。

## 反模式

| 反模式 | 正确做法 |
|---|---|
| 给所有 agent 完整聊天历史 | 给每个 agent 一个窄 context packet |
| 多个 worker 同时改同一文件 | 拆分 ownership 或串行执行 |
| 把 agent 猜测写入 memory | 只写证据支持、悟空批准的长期记忆 |
| 把旧记忆当事实 | 以当前状态和证据事实为准 |
| 没有验证就宣布完成 | 跑测试、检查 diff、引用证据 |
| 为小任务启动一堆 agent 或由悟空直接处理 | 只派一个任务相关 Subagent 执行，并另派独立验证 Subagent |

## 后续升级到真实后端

当前 C-lite 只是本地原型。升级时保持接口不变：

| 当前类 | 替换方向 |
|---|---|
| `StateStore` | LangGraph state graph + checkpointer |
| `MemoryStore` | mem0 durable user/agent memory |
| `FactGraphStore` | Graphiti temporal context graph |
| `ContextBuilder` | 带 ranking/token budget 的上下文装配器 |
| `WritebackGuard` | 统一安全策略和写入审批层 |

升级原则不变：

```text
角色提出写回建议。
独立验证 Subagent 审查证据并返回报告。
WritebackGuard 执行策略。
Store 保存状态、记忆或事实。
```

## 最小推荐 Prompt

```text
使用 $multi-agent-wukong。
目标：[写清目标]
约束：[写清不能做什么]
验收：[写清测试/人工确认/交付物]

要求：
1. 确认前只最小检查 Subagent 调度工具是否可调用；确认后派 Subagent 做完整 harness readiness check。
2. 如果任务超过一轮或涉及多个角色，使用 .wukong-context。
3. 建任务板，明确 read scope / write scope / verification。
4. 每个任务包写明 Authorization status / Confirmation evidence / Delegation permission；默认 `FORBIDDEN`，只有 `ALLOWED` 且 `Role` 明确授权子协调器时才能继续派发。
5. 只并行独立任务。
6. 每个 agent 返回 Status / Evidence / Risks / Needs Wukong decision。
7. 悟空汇总结果；独立验证 Subagent 运行验证，获派 worker 执行经批准的状态/记忆/事实写回。
```

## Governance Addendum

- Before substantive project work, require the canonical `project-control/v1` document at `<project-root>/docs/wukong/PROJECT-CONTROL.md`; only `BOOTSTRAP_DOC` may create the first one.
- Every project-start and large task must use `Superpowers brainstorming` through `superpowers:brainstorming`, retain all `S/M/L/XL` lifecycle dimensions, and obtain explicit user confirmation before dispatch.
- External capability review must record candidate/evaluation/selection/skip reason before choosing skills, agents, plugins, or external specialists.
- The current governance migration keeps Goal status `NOT_CREATED_BY_USER_DIRECTION`; future project-specific Goals require explicit dialog confirmation after scope confirmation and the hard gates `COMPILE_ZERO_ERRORS`, `ALL_TESTS_PASS`, and `REVIEW_APPROVED`.
- Every implementation handoff goes to the historian and must include work summary, TDD status, issues, bug logs, hard constraints, evidence, and a no-recursion statement.
