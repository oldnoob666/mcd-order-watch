"""可选协议检查：仅连接127.0.0.1假服务器，绝不访问麦当劳服务。"""
import asyncio
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


def fake_server(port):
    from mcp.server.fastmcp import FastMCP
    fake = FastMCP("fake-mcd-test-only", host="127.0.0.1", port=port, stateless_http=True)

    @fake.tool(name="now-time-info")
    def now_time_info() -> str:
        return "DEMO SERVER 2026-10-24T12:22:00+08:00"

    @fake.tool(name="order-list")
    def order_list() -> str:
        return "DEMO receipt_key TEST-1001"

    @fake.tool(name="query-order")
    def query_order(receipt_key: str) -> str:
        return json.dumps({"demo": True, "id": receipt_key, "status": "preparing"})

    @fake.tool(name="cancel-order")
    def cancel_order(receipt_key: str) -> str:
        return json.dumps({"demo": True, "id": receipt_key, "status": "cancelled"})

    @fake.tool(name="create-order")
    def create_order() -> str:
        return "THIS TOOL MUST NOT BE EXPOSED"

    fake.run(transport="streamable-http")


def bridge_child(port, allow_cancel):
    import mcp.client.streamable_http as transport
    original = transport.streamablehttp_client

    def local_only(url, **kwargs):
        # 测试进程强制重定向，生产代码不增加可配置服务器地址。
        assert url == "https://mcp.mcd.cn"
        assert kwargs["headers"]["Authorization"] == "Bearer DEMO-NOT-A-REAL-TOKEN"
        return original(f"http://127.0.0.1:{port}/mcp", **kwargs)

    transport.streamablehttp_client = local_only
    sys.path.insert(0, str(ROOT / "scripts"))
    import mcp_bridge
    asyncio.run(mcp_bridge.run_bridge("DEMO-NOT-A-REAL-TOKEN", allow_cancel))


try:
    HAS_SDK = importlib.metadata.version("mcp") == "1.30.0"
except importlib.metadata.PackageNotFoundError:
    HAS_SDK = False


@unittest.skipUnless(HAS_SDK, "Optional: install requirements.txt to test the pinned MCP SDK")
class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--fake-server", str(cls.port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", cls.port), timeout=0.1):
                    return
            except OSError:
                if cls.process.poll() is not None:
                    break
                time.sleep(0.1)
        cls.process.terminate()
        cls.process.wait(timeout=5)
        raise RuntimeError("本地假MCP服务器未成功启动")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)

    async def check_bridge(self, allow_cancel):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        args = [str(Path(__file__).resolve()), "--bridge-child", str(self.port)]
        if allow_cancel:
            args.append("--allow-cancel")
        params = StdioServerParameters(command=sys.executable, args=args,
                                       env={"PYTHONIOENCODING": "utf-8"})
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errors:
            async with stdio_client(params, errlog=errors) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    self.assertEqual(set(tools), {"now-time-info", "order-list", "query-order"} |
                                     ({"cancel-order"} if allow_cancel else set()))
                    self.assertIn("receipt_key", tools["query-order"].inputSchema["properties"])
                    clock = await client.call_tool("now-time-info", {})
                    self.assertFalse(clock.isError)
                    self.assertIn("DEMO SERVER", clock.content[0].text)
                    query = await client.call_tool("query-order", {"receipt_key": "TEST-1001"})
                    self.assertFalse(query.isError)
                    self.assertEqual(json.loads(query.content[0].text)["id"], "TEST-1001")
                    forbidden = await client.call_tool("create-order", {})
                    self.assertTrue(forbidden.isError)
                    refused = await client.call_tool("cancel-order", {"receipt_key": "TEST-1001"})
                    self.assertTrue(refused.isError)
                    if allow_cancel:
                        self.assertIn("_user_confirmed", tools["cancel-order"].inputSchema["required"])
                        result = await client.call_tool("cancel-order", {
                            "receipt_key": "TEST-1001", "_user_confirmed": True})
                        self.assertFalse(result.isError)
                        self.assertEqual(json.loads(result.content[0].text)["status"], "cancelled")

    def test_read_only_bridge_protocol(self):
        asyncio.run(asyncio.wait_for(self.check_bridge(False), timeout=25))

    def test_opt_in_cancel_bridge_protocol(self):
        asyncio.run(asyncio.wait_for(self.check_bridge(True), timeout=25))


if __name__ == "__main__":
    if "--fake-server" in sys.argv:
        fake_server(int(sys.argv[2]))
    elif "--bridge-child" in sys.argv:
        bridge_child(int(sys.argv[2]), "--allow-cancel" in sys.argv)
    else:
        unittest.main()
