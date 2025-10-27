import asyncio
import logging
import os

from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("MCP Server on Cloud Run")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Suma dos números enteros y devuelve el resultado."""
    logger.info(f">>> 🛠️ Tool: 'add' called with {a} and {b}")
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Resta el segundo número del primero y devuelve el resultado."""
    logger.info(f">>> 🛠️ Tool: 'subtract' called with {a} and {b}")
    return a - b

@mcp.tool()
def weighted_average(values: list[float], weights: list[float]) -> float:
    """
    Calcula el promedio ponderado de una lista de valores.

    Parámetros:
    - values: lista de números (valores a promediar)
    - weights: lista de números (pesos asociados a cada valor)

    Devuelve:
    - El promedio ponderado como un número decimal.

    Ejemplo:
    weighted_average([10, 20, 30], [1, 2, 3]) = 23.33

    Esta herramienta es útil cuando los valores tienen diferente importancia
    y se necesita un resultado más representativo que un promedio simple.
    """
    if len(values) != len(weights):
        raise ValueError("Las listas 'values' y 'weights' deben tener la misma longitud.")
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("La suma de los pesos no puede ser cero.")
    result = sum(v * w for v, w in zip(values, weights)) / total_weight
    logger.info(f">>> 🧮 Tool: 'weighted_average' called with values={values} weights={weights} result={result}")
    return result

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

