# 麦麦盯单：不帮你点餐，只帮你把已下的单盯到吃上嘴

面向已经下单、想知道“还要等多久”“现在出门会不会空等”的麦当劳用户。把麦当劳 MCP 订单状态翻译成一句进度和一个下一步。非麦当劳官方产品。

> 说「看看我那单到哪了」，或给一个餐饮订单号。查状态 → 讲进度 → 给建议。取消前单独确认。

**真实接入已验证（2026-10-24）**：服务器校时与账号历史订单列表均返回业务码 200，并已在 Codex 原生 MCP 会话中查询历史订单。公开记录仅包含工具名称和结果，见 [真实接入验证](docs/LIVE_VERIFICATION.md)。具体订单详情与真实取消仍待单独验证。

## 用户怎么用

先把本项目作为 Skill 导入支持技能的 AI 客户端，并连接麦当劳 MCP。完成后在聊天里直接说：

| 你说 | Skill 会做什么 |
| --- | --- |
| 看看我那单到哪了 | 校准服务器时间，列近期订单供选择，再查详情 |
| 查我最近一单 | 根据真实下单时间选最新一笔，返回进度 |
| 查一下订单 你的订单号 | 直接查这单，不额外罗列其他订单 |
| 我自取，现在去会不会空等 | 看是否明确可取；还在制作就提醒可能空等 |
| 怎么还没送到 | 核对预计时间和配送阶段，达到阈值给延迟建议 |
| 帮我取消这单 | 先展示目标、状态和限制，等你明确确认后才尝试取消 |
| 再查一次 | 重新查询同一单，对比状态有没有变化 |

普通查询输出示意（**假数据**）：

```text
【离线演示】订单尾号 1001 · 外送 · 配送中
模拟巨无霸套餐，预计 12:35 送达，按模拟服务器时间还约 13 分钟。
你现在可以：保持电话畅通；没有返回骑手位置，无法推算精确到达时间。
最近查询：2026-10-24 12:22 +08:00。预计时间不是准时承诺。
```

## 先体验：无需 Token、无需第三方依赖

需要 Python 3.10 或更新版本。在解压后的项目根目录打开终端：

```powershell
python scripts/demo.py
python scripts/demo.py --scenario pickup
python scripts/demo.py --scenario overdue
python scripts/demo.py --scenario unknown
```

多笔订单与“最近一单”：

```powershell
python scripts/demo.py --scenario multiple --list
python scripts/demo.py --scenario multiple --order-id DEMO-5002
python scripts/demo.py --scenario multiple --latest
```

模拟取消：第一条会拒绝，第二条会模拟成功。样例文件不会被改写，每次运行重新开始。

```powershell
python scripts/demo.py --cancel DEMO-1001
python scripts/demo.py --cancel DEMO-1001 --confirm DEMO-1001
```

这是确定性的命令行演示，不是自然语言聊天程序。全部订单和服务器时间为固定假数据，不连网、不读取 Token、不代表真实退款或可取消能力。自然语言能力由加载 `SKILL.md` 的 AI 客户端提供。

## 连接真实麦当劳 MCP

真实服务器：`https://mcp.mcd.cn`，协议为 Streamable HTTP。先到 [麦当劳 MCP 开放平台](https://open.mcd.cn/mcp) 登录并申请 Token。不要把 Token 发到聊天或写进仓库。

本项目提供 `scripts/mcp_bridge.py`：客户端通过 stdio 连接本地脚本，脚本从环境变量读取 Token，再连接官方服务器，动态保留官方工具参数。

仓库根目录的 [mcp-config.example.json](mcp-config.example.json) 是官方远程 HTTP 连接形式的环境变量模板，仅适用于能展开 `${MCD_MCP_TOKEN}` 的客户端；它不是所有客户端都能直接导入的通用配置。不支持变量展开时使用下面的本地桥接方式，保留 Token 在本机环境变量中。远程模板本身不限制服务端工具列表；本项目默认只读工具白名单由本地桥接器提供。

### 1. 安装接入脚本依赖

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 在本机配置环境变量

Windows 打开「编辑账户的环境变量」，新增用户变量 `MCD_MCP_TOKEN`，值填自己的 Token。保存后**完全退出并重新启动 AI 客户端**，让本地子进程继承新环境。Token 只在本机配置；无需改任何项目文件。

不要把真实值写进命令行、截图、对话、`.env` 或 MCP 配置 JSON。本项目不假定 WorkBuddy 会自动替换 `${变量名}`，因此使用本地脚本读取环境变量。

### 3. 添加本地 MCP 连接

在客户端支持的本地 stdio MCP 配置入口填入下列结构，**把路径改为自己解压后的绝对路径**。这是本地桥接配置，不是官方远程 HTTP 配置。

```json
{
  "mcpServers": {
    "mcd-order-watch": {
      "command": "C:/你的路径/mcd-order-watch/.venv/Scripts/python.exe",
      "args": ["C:/你的路径/mcd-order-watch/scripts/mcp_bridge.py"]
    }
  }
}
```

启用连接后，检查工具列表出现 `now-time-info`、`order-list`、`query-order`，再在聊天里让 AI 获取服务器时间做只读连通性检查。工具存在且真实调用成功才算接入成功。

WorkBuddy 的连接器入口可参考 [官方连接器说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Connector)。不同版本入口和本地 MCP 支持可能不同：选择其实际支持的本地 stdio 方式；若只有远程 HTTP 或无法继承环境变量，请改用支持本地 MCP 的客户端。不要为了连接成功把 Token 填进公开文件。

默认连接**只提供查单工具**。确实希望使用取消能力时，在 `args` 最后加上 `"--allow-cancel"` 并重启连接；Skill 仍须对具体订单二次确认。`_user_confirmed` 是模型提交的本地标记，不能在程序层面证明用户已同意，最终确认依赖客户端和 Skill 遵守交互流程。脚本不会自动退款、付款或重下单。

### 4. 导入 Skill

将包含 `SKILL.md` 的整个 `mcd-order-watch` 文件夹导入客户端的技能目录/本地技能功能，保留 `scripts/`、`examples/` 和 `MCP_INTEGRATION.md` 的相对路径。具体导入入口以客户端版本为准。

客户端没有 Skill 功能时，可在新聊天中附上 `SKILL.md` 和 `MCP_INTEGRATION.md`，明确让助手按它们执行已下单订单查询；MCP 连接仍需另行完成。此方式属于手动加载说明。

然后说：「按麦麦盯单 Skill，看看我最近一单到哪了。」也可以先说「用假订单演示一下」。

## 判断规则

- 自取看“是否可取”，外送看“门店阶段 / 配送阶段”；不编造骑手位置或出餐时间。
- 服务器时间与 ETA 的日期、时区完整才计算差值；预约单先核对预约日期。
- 超过预计时间 **10 分钟**触发延迟提醒。这是项目阈值，不是官方服务承诺或赔付规则。
- 单独的抱怨不算取消授权。用户换单或撤回后，旧的确认作废；取消失败/超时先查状态，不自动重试。
- 本版支持单次查询和用户发起的复查。后台定时轮询需要客户端调度能力与用户指定的时长，本版脚本没有后台常驻盯单功能。

## 文件说明与验证

```text
mcd-order-watch/
├─ README.md                  使用说明、演示、安装和参赛提示
├─ SKILL.md                   技能触发、顺序、状态机与确认流程
├─ MCP_INTEGRATION.md         官方服务、真实工具和字段边界
├─ CONTEST_DECLARATION.md     固定版本官方声明，内容原样保留
├─ mcp-config.example.json   仅含环境变量占位符的远程配置模板
├─ LICENSE                   项目原创代码与文档的 MIT 许可
├─ requirements.txt          真实接入所需的 MCP Python SDK
├─ scripts/demo.py           标准库离线演示
├─ scripts/mcp_bridge.py     真实 MCP 接入桥，默认只读
├─ examples/orders.json      明确标注的假订单
├─ tests/                    订单逻辑与本地假服务器协议检查
└─ docs/                     提交步骤、官方来源与验证记录
```

```powershell
python -m unittest discover -s tests -v
```

不安装第三方依赖也可运行 12 项订单逻辑测试；2 项协议检查需 `requirements.txt` 中的固定版 SDK，否则会跳过。协议检查只启动本机假服务器，不使用真实 Token。交付时 14 项均已通过，详见 [验证记录](docs/VALIDATION.md)。

离线测试与本地模拟协议检查只能证明项目逻辑和接入机制，不证明真实账号鉴权成功、真实订单字段适配、取消可用或退款成功。公开资料仅定义工具用途，输入参数和状态码必须以真实会话 `tools/list` 及返回内容为准。

## 参加比赛

[官方比赛仓库](https://github.com/M-China/mcd-developer-innovation-challenge) 公布的报名截止时间为 **北京时间 2026 年 10 月 25 日 23:59**。具体提交步骤和待完成项见 [docs/SUBMISSION.md](docs/SUBMISSION.md)。

本项目已经使用真实麦当劳 MCP 完成校时和历史订单列表查询，脱敏结果见 [真实接入验证](docs/LIVE_VERIFICATION.md)。其他使用者仍需配置自己的 Token。项目发布为 Public、提交报名 Issue 与官方审核回复属于不同步骤，提交 Issue 不等于审核通过。

未附 `workbuddy.md`，因为本次没有真实 WorkBuddy 对话导出。普通参赛不强制该文件；若申请 WorkBuddy 专项奖励，请在 WorkBuddy 中真实开发/调试后导出，勿把示例对话冒充记录。

## 许可

本项目原创代码和文档采用 [MIT License](LICENSE)。官方参赛声明原样保留，麦当劳服务和第三方依赖受其各自条款约束；本项目不代表麦当劳官方，也不授予其商标使用权。
