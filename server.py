import asyncio
import logging
import os

from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("MCP Server on Cloud Run")

@mcp.tool()
def add(a: int, b: int) -> int:
    logger.info(f">>> 🛠️ Tool: 'add' called with {a} and {b}")
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    logger.info(f">>> 🛠️ Tool: 'subtract' called with {a} and {b}")
    return a - b

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7000))
    logger.info(f"🚀 MCP server started on port {port}")
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )
    )
