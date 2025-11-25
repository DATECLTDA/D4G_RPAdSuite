import asyncio
import logging
import os
# import requests # <- Comentado
# from datetime import datetime # <- Comentado
from fastmcp import FastMCP
from fastapi import Request, HTTPException, status
import json

# Importar solo la función de orquestación que usaremos
from tool import preparar_y_enviar_factura_sap_tool 

# # Importar tus tools antiguas (COMENTADAS)
# from tool import validar_factura_tool, enviar_factura_a_sheets_tool
# from utilities.image_storage import upload_image_to_gcs

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# --- CONFIGURACIÓN DE SEGURIDAD Y ENTORNO ---
# Cargar secreto de entorno (de las variables que ya tienes en Cloud Run)
AUTH_SECRET = os.getenv("APPS_SCRIPT_AUTH_SECRET", "default_secret_if_missing") 

# Crear servidor MCP
mcp = FastMCP("MCP Server on Cloud Run")

# ------------------------------
# 🚨 ENDPOINT PRINCIPAL: WEBHOOK DE APPS SCRIPT
# ------------------------------
@mcp.api_route("/webhook/invoice", methods=["POST"])
async def handle_invoice_webhook(request: Request):
    """
    Recibe el webhook de Apps Script, valida la autenticación y llama a la lógica principal.
    """
    logger.info("📡 Webhook /webhook/invoice recibido.")
    
    try:
        data = await request.json()
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON received.")
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    # 1. Autenticación del Webhook
    received_secret = data.get("auth_secret")
    if received_secret != AUTH_SECRET:
        logger.warning(f"❌ AUTH FAILED: Secret mismatch. Received: {received_secret}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization secret")

    gcs_path = data.get("gcs_path")
    correo_remitente = data.get("remitente_correo")

    if not gcs_path or not correo_remitente:
        logger.error("❌ Missing gcs_path or remitente_correo in payload.")
        raise HTTPException(status_code=400, detail="Missing GCS path or sender email")

    # 2. Llamada a la lógica principal en tool.py
    logger.info(f"➡️ Llamando a tool.py con Path: {gcs_path} y Correo: {correo_remitente}")
    
    # La lista de rutas es requerida por la tool.
    rutas_bucket = [gcs_path] 
    
    # Ejecutamos la función principal
    resultado_final = preparar_y_enviar_factura_sap_tool(rutas_bucket, correo_remitente)
    
    # 3. Respuesta al Webhook
    if resultado_final.get("status") == "success":
        logger.info(f"✅ Webhook procesado. Mensaje: {resultado_final.get('message')}")
        return {"status": "success", "message": resultado_final.get("message")}
    else:
        logger.error(f"❌ Webhook fallido. Mensaje: {resultado_final.get('message')}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=resultado_final.get("message"))


# ------------------------------
# Tools Antiguas (COMENTADAS)
# ------------------------------

# @mcp.tool()
# def validar_factura(rutas_bucket: list[str]) -> dict:
#     # ... Código de validación antiguo ...
#     return {"status": "commented"}

# @mcp.tool()
# def enviar_factura_a_sheets(factura: dict, correo_remitente: str) -> dict:
#     # ... Código de sheets antiguo ...
#     return {"status": "commented"}

# @mcp.tool()
# def subir_pdf_easycontact(user_email: str, image_url: str) -> str:
#     # ... Código de subida easycontact antiguo ...
#     return {"status": "commented"}

# @mcp.tool()
# def enviar_factura(factura: dict, correo: str) -> dict:
#     # ... Código de envío antiguo ...
#     return {"status": "commented"}


# ------------------------------
# Run server MCP
# ------------------------------
if __name__ == "__main__":
    # Importamos Uvicorn aquí para el launch local
    import uvicorn
    port = int(os.getenv("PORT", 8080)) # Usar 8080 por convención de Cloud Run
    logger.info(f"🚀 MCP server starting on port {port}")
    
    # Usamos la app de FastAPI que FastMCP genera internamente
    app = mcp.get_app() 
    
    uvicorn.run(app, host="0.0.0.0", port=port)
    # Nota: El uso de mcp.run_async() fue reemplazado por uvicorn.run() para una ejecución estándar.