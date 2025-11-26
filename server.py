import asyncio
import logging
import os
import requests
from fastmcp import FastMCP
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
import uvicorn

# Importar tu tool de facturas
from tool import validar_factura_tool, enviar_factura_a_sheets_tool
from utilities.image_storage import upload_image_to_gcs

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Crear servidor MCP
mcp = FastMCP("MCP Server on Cloud Run")

# Crear app FastAPI para endpoints HTTP
app = FastAPI(title="MCP Server")

# ------------------------------
# Endpoint para pruebas "Hola Mundo"
# ------------------------------

@app.post("/")
async def root_endpoint(request: Request):
    """
    Endpoint principal para recibir llamadas del App Script
    """
    try:
        data = await request.json()
        action = data.get("action")
        parameters = data.get("parameters", {})
        
        logger.info(f"📥 Llamada recibida - Action: {action}, Parameters: {parameters}")
        
        if action == "hola_mundo":
            return await hola_mundo_handler(parameters)
        elif action == "validar_factura":
            return await validar_factura_handler(parameters)
        else:
            return {"status": "error", "message": f"Acción no reconocida: {action}"}
            
    except Exception as e:
        logger.error(f"❌ Error en endpoint principal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def hola_mundo_handler(parameters: dict):
    """Manejador para la acción hola_mundo"""
    ruta_gcs = parameters.get("ruta_gcs", "")
    correo_remitente = parameters.get("correo_remitente", "")
    asunto = parameters.get("asunto", "")
    
    logger.info(f"🎉 ¡HOLA MUNDO! Factura recibida:")
    logger.info(f"   📧 De: {correo_remitente}")
    logger.info(f"   📝 Asunto: {asunto}")
    logger.info(f"   📁 Archivo: {ruta_gcs}")
    logger.info(f"   ⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Aquí puedes agregar más lógica posteriormente
    return {
        "status": "success",
        "message": "¡Hola Mundo! Factura recibida correctamente",
        "data": {
            "correo": correo_remitente,
            "archivo": ruta_gcs,
            "asunto": asunto,
            "timestamp": datetime.now().isoformat()
        }
    }

async def validar_factura_handler(parameters: dict):
    """Manejador para validar facturas"""
    rutas_bucket = parameters.get("rutas_bucket", [])
    if not rutas_bucket:
        return {"status": "error", "message": "No se proporcionaron rutas de archivos"}
    
    try:
        resultado = validar_factura_tool(rutas_bucket)
        return {"status": "success", "data": resultado}
    except Exception as e:
        logger.error(f"❌ Error validando factura: {e}")
        return {"status": "error", "message": str(e)}

# ------------------------------
# Tools MCP existentes (mantener igual)
# ------------------------------

@mcp.tool()
def validar_factura(rutas_bucket: list[str]) -> dict:
    """Valida facturas desde Google Cloud Storage."""
    logger.info(f">>> 🛠️ Tool: 'validar_factura' called with rutas_bucket={rutas_bucket}")
    resultado = validar_factura_tool(rutas_bucket)
    logger.info(f">>> 🛠️ Resultado: {resultado}")
    return resultado

@mcp.tool()
def enviar_factura_a_sheets(factura: dict, correo_remitente: str) -> dict:
    """Envía datos de factura a Google Sheets."""
    logger.info(f">>> 🧾 Tool: 'enviar_factura_a_sheets' llamada con correo={correo_remitente}")
    
    SCRIPT_URL = os.getenv("APPS_SCRIPT_URL", "YOUR_APPS_SCRIPT_URL")
    factura["correo_remitente"] = correo_remitente
    factura["fecha_hora_consulta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        response = requests.post(SCRIPT_URL, json=factura, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Datos enviados correctamente a Google Sheets.")
            return {"success": True, "status": 200, "response": response.text}
        else:
            logger.error(f"❌ Error al enviar a Sheets: {response.text}")
            return {"success": False, "status": response.status_code, "error": response.text}
    except Exception as e:
        logger.error(f"⚠️ Excepción al enviar factura: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def subir_pdf_easycontact(user_email: str, image_url: str) -> str:
    """Sube factura a Google Cloud Storage."""
    url = upload_image_to_gcs(user_email, image_url)
    if url:
        return f"Archivo subido correctamente a GCS: {url}"
    else:
        return "Error al subir el archivo."

@mcp.tool()
def enviar_factura(factura: dict, correo: str) -> dict:
    """Envía factura a sheets para ser registrada."""
    logger.info(f">>> 🛠️ Tool: 'enviar_factura' called with factura={factura} correo={correo}")
    resultado = enviar_factura_a_sheets_tool(factura, correo)
    logger.info(f">>> 🛠️ Resultado: {resultado}")
    return resultado

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7000))
    logger.info(f"🚀 Starting MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)