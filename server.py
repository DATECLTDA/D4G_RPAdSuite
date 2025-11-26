import asyncio
import logging
import os
import requests
from fastmcp import FastMCP
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
import uvicorn

# Importar tus tools existentes
from tool import validar_factura_tool, enviar_factura_a_sheets_tool
from utilities.image_storage import upload_image_to_gcs

# Configuración de logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s]: %(message)s", 
    level=logging.INFO,
    force=True
)

# Crear servidor MCP
mcp = FastMCP("MCP Server on Cloud Run")

# Crear app FastAPI
app = FastAPI(title="MCP Server")

# Configuración
AUTH_SECRET = os.getenv("AUTH_SECRET", "MiClaveUltraSecreta_MCP_2025_#f6d9kP!")

# ------------------------------
# Endpoints SIMPLES Y DIRECTOS
# ------------------------------

@app.get("/")
async def root():
    """Endpoint raíz - para verificar que el servidor funciona"""
    return {
        "status": "active", 
        "service": "MCP Server",
        "timestamp": datetime.now().isoformat(),
        "message": "Servidor MCP funcionando correctamente"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/")
async def handle_post(request: Request):
    """Endpoint principal POST"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token requerido")
        
        token = auth_header.replace("Bearer ", "").strip()
        if token != AUTH_SECRET:
            raise HTTPException(status_code=401, detail="Token inválido")

        data = await request.json()
        logger.info(f"📥 Datos recibidos: {data}")
        
        # Procesar según el contenido
        action = data.get("action", "hola_mundo")
        
        if action == "hola_mundo":
            return await hola_mundo_handler(data.get("parameters", {}))
        else:
            return {"status": "error", "message": f"Acción no soportada: {action}"}
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/webhook/factura")
async def webhook_factura(request: Request):
    """Webhook para facturas"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"status": "error", "message": "Token requerido"}
        
        token = auth_header.replace("Bearer ", "").strip()
        if token != AUTH_SECRET:
            return {"status": "error", "message": "Token inválido"}

        data = await request.json()
        logger.info(f"📥 Webhook recibido: {data}")
        
        # Procesar la factura
        ruta_gcs = data.get("ruta_gcs") or data.get("gcs_path")
        correo = data.get("correo_remitente") or data.get("email")
        
        if not ruta_gcs:
            return {"status": "error", "message": "No se proporcionó ruta GCS"}
        
        return await hola_mundo_handler({
            "ruta_gcs": ruta_gcs,
            "correo_remitente": correo,
            "asunto": data.get("asunto", ""),
            "nombre_archivo": data.get("nombre_archivo", ""),
            "content_type": data.get("content_type", "")
        })
        
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return {"status": "error", "message": str(e)}

# ------------------------------
# Handlers
# ------------------------------

async def hola_mundo_handler(parameters: dict):
    """Manejador para Hola Mundo"""
    try:
        ruta_gcs = parameters.get("ruta_gcs", "")
        correo_remitente = parameters.get("correo_remitente", "")
        asunto = parameters.get("asunto", "")
        nombre_archivo = parameters.get("nombre_archivo", "")
        
        # Log detallado
        logger.info("🎉 ¡HOLA MUNDO! Factura recibida:")
        logger.info(f"   📧 De: {correo_remitente}")
        logger.info(f"   📝 Asunto: {asunto}")
        logger.info(f"   📁 Archivo: {nombre_archivo}")
        logger.info(f"   📍 Ruta GCS: {ruta_gcs}")
        logger.info(f"   ⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response_data = {
            "status": "success",
            "message": "¡Hola Mundo! Factura recibida correctamente",
            "data": {
                "correo": correo_remitente,
                "archivo": nombre_archivo,
                "ruta_gcs": ruta_gcs,
                "asunto": asunto,
                "timestamp": datetime.now().isoformat(),
                "servidor": "MCP Server - Cloud Run"
            }
        }
        
        logger.info(f"✅ Respuesta: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error en hola_mundo_handler: {e}")
        return {"status": "error", "message": f"Error en handler: {str(e)}"}

# ------------------------------
# Tools MCP (para compatibilidad)
# ------------------------------

@mcp.tool()
def validar_factura(rutas_bucket: list[str]) -> dict:
    """Valida facturas desde Google Cloud Storage."""
    logger.info(f">>> 🛠️ Tool: 'validar_factura' called")
    resultado = validar_factura_tool(rutas_bucket)
    logger.info(f">>> 🛠️ Resultado: {resultado}")
    return resultado

@mcp.tool()
def enviar_factura_a_sheets(factura: dict, correo_remitente: str) -> dict:
    """Envía datos de factura a Google Sheets."""
    logger.info(f">>> 🧾 Tool: 'enviar_factura_a_sheets'")
    
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
    logger.info(f">>> 🛠️ Tool: 'enviar_factura'")
    resultado = enviar_factura_a_sheets_tool(factura, correo)
    logger.info(f">>> 🛠️ Resultado: {resultado}")
    return resultado

# ------------------------------
# Servidor Principal
# ------------------------------

async def run_mcp_server():
    """Ejecuta el servidor MCP en segundo plano"""
    try:
        port = int(os.getenv("MCP_PORT", 7000))
        logger.info(f"🚀 MCP server starting on port {port}")
        await mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )
    except Exception as e:
        logger.error(f"❌ Error starting MCP server: {e}")

@app.on_event("startup")
async def startup_event():
    """Inicia el servidor MCP en segundo plano"""
    logger.info("🔧 Starting up MCP Server...")
    # Ejecutar MCP en segundo plano
    asyncio.create_task(run_mcp_server())

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7000))  # PUERTO 7000
    logger.info(f"🚀 Starting FastAPI Server on port {port}")
    logger.info(f"🔑 Auth Secret: {'Configured' if AUTH_SECRET else 'Not configured'}")
    
    # Iniciar servidor FastAPI
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        access_log=True
    )