# 本地验证记录

验证日期：2026-10-24。环境：Windows、Python 3.11.15；真实桥接的隔离测试环境使用 `mcp==1.30.0`。

## 已执行

- `python -m unittest discover -s tests -v`：安装固定版本 SDK 的环境中，14 项全部通过，无跳过。
- `python -m pip check`：No broken requirements found。
- Skill Creator 的 `quick_validate.py`（启用 Python UTF-8 模式）：Skill is valid。
- `git hash-object CONTEST_DECLARATION.md`：`136e76f3160317049f19f5ba03f4d0fedd70fc3c`，与官方固定版本 Git blob 完全一致。
- 运行外送、自取待取、超时、未知状态、多单选择/最近一单及模拟取消的 CLI 示例；拒绝缺少确认和订单号不匹配的模拟取消。

## 测试覆盖

12 项逻辑检查覆盖服务器时间计算、超过预计时间、日期/时区缺失、自取制作中与待取、完成终态、未知状态/方式、多单歧义、目标一致的模拟取消、完成后拒绝取消、桥接只读白名单、取消标记转发前移除，以及401/429脱敏分类。

2 项协议检查通过真正的 SDK 通信链路：测试 MCP 客户端 → stdio 桥 → 127.0.0.1 上的假 Streamable HTTP MCP 服务器。验证握手、动态保留非预设参数名 `receipt_key`、查询转发、默认隐藏取消与点餐工具、拒绝缺确认取消，以及显式启用后的模拟取消。测试进程强制将目标重定向到本机，不访问 `mcp.mcd.cn`。

独立静态场景检查覆盖多单、备注中伪指令、延迟但无骑手信息、用户改选订单后旧确认失效，以及预约日期/时区缺失。

## 已完成的真实调用

2026-10-24 已使用真实 Token 连接 `https://mcp.mcd.cn`，完成 MCP 初始化、服务器校时与账号历史订单列表查询，两项业务响应均为 200；随后在 Codex 原生 MCP 会话中再次完成校时和历史列表查询。详情见 [LIVE_VERIFICATION.md](LIVE_VERIFICATION.md)。

## 尚未验证

尚未对具体订单调用 `query-order`，未验证进行中订单的状态变化、实际取消资格或退款，也未验证客户端的技能自动选择或 WorkBuddy 导入。未生成 WorkBuddy 开发对话记录。真实历史订单列表查询成功不能代替上述验证。
