import asyncio
import logging
import os
from fastmcp import FastMCP
from tool import preparar_y_enviar_factura_sap_tool 

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# --- CONFIGURACIÓN DE SEGURIDAD Y ENTORNO ---
AUTH_SECRET = os.getenv("APPS_SCRIPT_AUTH_SECRET", "default_secret_if_missing") 

# Crear servidor MCP
mcp = FastMCP("MCP Server on Cloud Run")

# --------------------------------------------------------
# 🚨 TOOL PRINCIPAL: procesar_factura_sap (El nuevo ENDPOINT)
# --------------------------------------------------------

@mcp.tool()
def procesar_factura_sap(rutas_bucket: list[str], correo_remitente: str) -> dict:
    """
    Tool principal llamada por Apps Script para orquestar la validación LLM y el envío a SAP.
    """
    logger.info(f">>> 🛠️ Tool: 'procesar_factura_sap' called by {correo_remitente}")
    
    # Esta función llama a la lógica real en tool.py
    resultado_final = preparar_y_enviar_factura_sap_tool(rutas_bucket, correo_remitente)
    
    # FastMCP espera que la tool devuelva un dict, no raise HTTPException
    if resultado_final.get("status") == "success":
        logger.info(f"✅ Tool procesada. Mensaje: {resultado_final.get('message')}")
        return resultado_final
    else:
        logger.error(f"❌ Tool fallida. Mensaje: {resultado_final.get('message')}")
        return resultado_final # Devuelve el dict con status="error"

# ------------------------------
# Tools Antiguas (COMENTADAS/ELIMINADAS)
# ------------------------------
# ... (Aquí irían tus tools antiguas si quieres mantener las líneas comentadas) ...

# -----------------------------
# Run server MCP (Configuración de ejecución que nos permite usar FastMCP)
# -----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7000)) 
    logger.info(f"🚀 MCP server starting on port {port}")
    
    # Uso de mcp.run_async para entornos Serverless (sin Uvicorn)
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )
    )