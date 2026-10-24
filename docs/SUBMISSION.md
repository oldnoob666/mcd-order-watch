# 参赛前操作与官方来源

本文记录官方要求和报名步骤；实际提交及审核结果以官方仓库对应 Issue 为准。项目已完成真实校时和历史订单列表查询，脱敏结果见 [LIVE_VERIFICATION.md](LIVE_VERIFICATION.md)。

## 官方来源

2026-10-24 核对：

- [比赛仓库](https://github.com/M-China/mcd-developer-innovation-challenge)：README 要求 `README.md`、`CONTEST_DECLARATION.md`、`MCP_INTEGRATION.md` 及源代码/可运行内容。`SKILL.md` 是本项目技能入口。
- [固定版本比赛说明](https://github.com/M-China/mcd-developer-innovation-challenge/blob/905f29129305fa6ce4c65d0f517fcddb71fa7be9/README.md)：报名截止北京时间 2026-10-25 23:59，最终排行采集时间为 2026-10-26 00:00。
- [完整活动规则](https://github.com/M-China/mcd-developer-innovation-challenge/blob/905f29129305fa6ce4c65d0f517fcddb71fa7be9/activityGuidelines.md)：参赛者自行阅读和确认资格、声明及发布授权。
- 完整活动规则额外要求根目录提供 `mcp-config.example.json`，本仓库已补齐只含环境变量占位符的模板；该要求不能仅根据比赛首页的简表判断。
- [麦当劳 MCP 官方指南](https://github.com/M-China/mcd-mcp-server/blob/main/README.md)：本项目所用服务、鉴权与工具名称的来源。
- [MCP Python SDK 1.30.0](https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0)：本地桥接实现依赖，安装固定版本避免跨主版本接口差异。

## 声明原文校验

`CONTEST_DECLARATION.md` 从[官方固定版本文件](https://github.com/M-China/mcd-developer-innovation-challenge/blob/905f29129305fa6ce4c65d0f517fcddb71fa7be9/CONTEST_DECLARATION.md)取得，UTF-8、1522 字节。未添加署名、说明或改写；本说明单独存放。

```text
官方 Git blob SHA-1: 136e76f3160317049f19f5ba03f4d0fedd70fc3c
本地文件 SHA-256: cd28101bcb29cc8fb24b372fe91ce6b42c4a1487a54e01f7ade0c8c6a84241b7
```

可以在本地运行 `git hash-object CONTEST_DECLARATION.md` 核对 Git blob SHA-1；没有 Git 时用 `Get-FileHash -Algorithm SHA256 CONTEST_DECLARATION.md` 核对 SHA-256。本项目 `.gitattributes` 将该文件标为 `-text`，避免 Windows Git 自动转换换行。赛前如官方更新声明，应重新取得官方原文件并重新核对。

## 完成参赛

1. 运行离线演示和测试，检查自己理解项目行为。真实 Token 只保存在本机环境变量中。
2. 连接真实 MCP，调用服务器时间并查询历史订单列表。保留脱敏的日期、工具名、成功/失败结果；无需公开个人订单和完整响应。本项目已完成这两项真实调用，具体订单详情和取消仍须另行验证。
3. 自行阅读官方活动规则和原样声明，确认本人可以作出相关声明。
4. 将 `mcd-order-watch` **目录内的文件作为仓库根目录**上传到自己的公开 GitHub 仓库；必需文件不能藏在多一层压缩包/子目录内。发布前检查没有凭证、真实订单信息或本地配置。
5. 到官方比赛仓库，按当前 Issue 模板提交报名。标题可用「麦麦盯单：已有餐饮订单进度与行动建议」。正文示例中的仓库地址需要换成自己的真实公开地址：

```text
【参赛申请】
项目名称：麦麦盯单
项目地址：https://github.com/oldnoob666/mcd-order-watch
项目简介：基于麦当劳MCP查询已下单餐饮订单，使用服务器时间解释自取与外送进度，给出延迟和取餐行动建议，取消前确认；提供无Token离线演示。
```

官方提醒字段标签与内容放在同一行，项目地址用裸 URL，不要用 Markdown 链接。以当前官方模板为准。

6. 收到官方 Issue 的成功回复才算报名成功；失败则按其原因修复。Star 与排名以官方规则和采集为准，本项目不承诺获奖。

`workbuddy.md` 仅参加 WorkBuddy 专项奖励时要求。这里由 Codex 生成项目，没有实际 WorkBuddy 开发上下文，因此不生成该文件。若需要专项资格，请真实使用 WorkBuddy 调试并导出其对话，脱敏后再提交。
