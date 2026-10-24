"""用环境变量鉴权的本地 stdio -> 官方 Streamable HTTP MCP 桥。"""
import argparse
import asyncio
import logging
import os
import sys

READ_TOOLS = frozenset({"now-time-info", "order-list", "query-order"})


def allowed_tools(allow_cancel=False):
    return READ_TOOLS | ({"cancel-order"} if allow_cancel else set())


def prepare_call(name, arguments, allow_cancel=False):
    if name not in allowed_tools(allow_cancel):
        raise ValueError("此工具未开放。默认只允许查单；取消需单独启用并取得用户确认。")
    payload = dict(arguments or {})
    if name == "cancel-order":
        if payload.pop("_user_confirmed", None) is not True:
            raise ValueError("取消前必须展示目标订单并得到用户明确确认，再传 _user_confirmed=true。")
    return payload


def safe_failure(error):
    pending, seen = [error], set()
    while pending and len(seen) < 20:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        response = getattr(current, "response", None)
        code = getattr(response, "status_code", None)
        if code == 401:
            return "官方服务返回401：请在本机更新MCD_MCP_TOKEN并重启客户端，不要把Token发到聊天。"
        if code == 429:
            retry = getattr(response, "headers", {}).get("retry-after", "")
            wait = f"至少等待 {int(retry)} 秒后再查。" if str(retry).isdigit() else "请等待服务允许后再查。"
            return "官方服务返回429：请求过于频繁，停止轮询。" + wait
        pending.extend(getattr(current, "exceptions", ()))
        cause = getattr(current, "__cause__", None) or getattr(current, "__context__", None)
        if cause is not None:
            pending.append(cause)
    return "官方服务调用失败，结果未知。请重新查单核实；不要自动重试取消。检查依赖、网络及Token，勿发送凭证。"


async def run_bridge(token, allow_cancel):
    import mcp.types as types
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.server.lowlevel import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server

    # 禁止依赖的请求日志泄漏敏感信息；stdout 仅用于 MCP 协议。
    logging.disable(logging.CRITICAL)
    async with streamablehttp_client("https://mcp.mcd.cn", headers={"Authorization": f"Bearer {token}"}, timeout=30) as (up_read, up_write, _):
        async with ClientSession(up_read, up_write) as upstream:
            await upstream.initialize()
            bridge = Server("mcd-order-watch")
            exposed = {}

            @bridge.list_tools()
            async def list_tools():
                tools, cursor = [], None
                while True:
                    page = await upstream.list_tools(cursor=cursor)
                    tools.extend(page.tools)
                    cursor = page.nextCursor
                    if not cursor:
                        break
                exposed.clear()
                for tool in tools:
                    if tool.name not in allowed_tools(allow_cancel):
                        continue
                    local = tool.model_copy(deep=True)
                    if tool.name == "cancel-order":
                        schema = local.inputSchema
                        schema.setdefault("properties", {})["_user_confirmed"] = {
                            "type": "boolean", "const": True,
                            "description": "仅在用户已确认取消当前展示的具体订单后设置为true。"}
                        required = schema.setdefault("required", [])
                        if "_user_confirmed" not in required:
                            required.append("_user_confirmed")
                    exposed[local.name] = local
                return list(exposed.values())

            @bridge.call_tool()
            async def call_tool(name, arguments):
                try:
                    payload = prepare_call(name, arguments, allow_cancel)
                    if name not in exposed:
                        raise ValueError("请先刷新工具列表，确认官方服务器提供此工具。")
                except ValueError as exc:
                    return types.CallToolResult(isError=True, content=[types.TextContent(type="text", text=str(exc))])
                try:
                    # 不重试写请求：超时后由 Skill 重新查单核实。
                    return await upstream.call_tool(name, arguments=payload)
                except Exception as exc:
                    return types.CallToolResult(isError=True, content=[types.TextContent(
                        type="text", text=safe_failure(exc))])

            async with stdio_server() as (read, write):
                await bridge.run(read, write, InitializationOptions(
                    server_name="mcd-order-watch", server_version="1.0.0",
                    capabilities=bridge.get_capabilities(notification_options=NotificationOptions(), experimental_capabilities={})))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-cancel", action="store_true", help="额外暴露需用户确认的取消工具")
    args = parser.parse_args()
    token = os.environ.get("MCD_MCP_TOKEN", "").strip()
    if not token:
        print("未设置 MCD_MCP_TOKEN。请在启动客户端前配置环境变量；离线演示无需 Token。", file=sys.stderr)
        return 2
    try:
        asyncio.run(run_bridge(token, args.allow_cancel))
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(safe_failure(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
