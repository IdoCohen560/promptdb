"""P2.5 verification: connect to the PromptDB MCP server over stdio and round-trip its tools.

Proves both sides of MCP — the server is authored, and this client consumes it.
Run: python scripts/mcp_client_demo.py
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _text(result) -> str:
    return " ".join(getattr(c, "text", str(c)) for c in result.content)


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "promptdb.mcp_server.server"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            r1 = await session.call_tool("list_tables", {})
            print("list_tables ->", _text(r1)[:200])

            r2 = await session.call_tool("run_sql", {"sql": "SELECT Name FROM Artist LIMIT 3"})
            print("run_sql(SELECT) ->", _text(r2)[:300])

            r3 = await session.call_tool("run_sql", {"sql": "DELETE FROM Artist"})
            print("run_sql(DELETE) ->", _text(r3)[:200])


if __name__ == "__main__":
    asyncio.run(main())
