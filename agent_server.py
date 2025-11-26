import asyncio
import logging
import os
import requests
from fastapi import FastAPI, HTTPException, Request, Depends
import uvicorn
from typing import Optional
from datetime import datetime

# Configuración de logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s]: %(message)s", 
    level=logging.INFO,
    force=True
)

# Crear app FastAPI
app = FastAPI(
    title="MCP Agent Server", 
    description="Servidor con agente MCP para procesamiento de facturas",
    version="1.0.0"
)

# Configuración
AUTH_SECRET = os.getenv("AUTH_SECRET", "MiClaveUltraSecreta_MCP_2025_#f6d9kP!")
BUCKET_NAME = os.getenv("BUCKET_NAME", "rpa_facturacion")

# Importar utilities después de configurar logging
from tool import validar_factura_tool, enviar_factura_a_sheets_tool
from utilities.image_storage import upload_image_to_gcs, download_pdf_to_tempfile

# ------------------------------
# Agente MCP Simplificado
# ------------------------------

class MCPFacturaAgent:
    def __init__(self):
        self.system_prompt = """
        Eres un asistente especializado en procesamiento de facturas. Tu tarea es:
        1. Recibir facturas desde correos electrónicos
        2. Validar su autenticidad y extraer datos
        3. Procesar la información para almacenamiento
        4. Confirmar el resultado al usuario

        Responde de manera profesional y concisa.
        """
        logger.info("🤖 Agente MCP de Facturas inicializado")

    async def procesar_factura_desde_gcs(self, ruta_gcs: str, correo_remitente: str, asunto: str = "") -> dict:
        """
        Procesa una factura desde Google Cloud Storage
        """
        try:
            logger.info(f"🔍 Iniciando procesamiento de factura: {ruta_gcs}")
            
            # Paso 1: Validar factura
            logger.info("📋 Validando factura...")
            resultado_validacion = await self.validar_factura([ruta_gcs])
            
            if resultado_validacion["status"] != "success":
                return resultado_validacion

            datos_factura = resultado_validacion["datos"]
            
            # Paso 2: Si es válida, enviar a sheets
            if datos_factura.get("factura_valida", False):
                logger.info("📊 Enviando factura a sheets...")
                resultado_envio = await self.enviar_a_sheets(datos_factura, correo_remitente)
                
                return {
                    "status": "success",
                    "message": "Factura procesada y validada correctamente",
                    "validacion": resultado_validacion,
                    "envio_sheets": resultado_envio,
                    "procesado_por": "MCP Agent"
                }
            else:
                return {
                    "status": "success",
                    "message": "Factura procesada pero no es válida",
                    "validacion": resultado_validacion,
                    "envio_sheets": {"status": "skipped", "reason": "Factura no válida"},
                    "procesado_por": "MCP Agent"
                }

        except Exception as e:
            logger.error(f"❌ Error en procesamiento: {e}")
            return {"status": "error", "message": f"Error en procesamiento: {str(e)}"}

    async def validar_factura(self, rutas_bucket: list[str]) -> dict:
        """Valida facturas usando la tool existente"""
        try:
            return validar_factura_tool(rutas_bucket)
        except Exception as e:
            logger.error(f"❌ Error validando factura: {e}")
            return {"status": "error", "message": str(e)}

    async def enviar_a_sheets(self, factura: dict, correo: str) -> dict:
        """Envía factura a sheets usando la tool existente"""
        try:
            return enviar_factura_a_sheets_tool(factura, correo)
        except Exception as e:
            logger.error(f"❌ Error enviando a sheets: {e}")
            return {"status": "error", "message": str(e)}

    async def hola_mundo(self, parametros: dict) -> dict:
        """Función de prueba 'Hola Mundo'"""
        logger.info("🎉 Ejecutando Hola Mundo desde el agente")
        
        return {
            "status": "success",
            "message": "¡Hola Mundo desde el Agente MCP!",
            "agente": "MCP Factura Agent",
            "timestamp": datetime.now().isoformat(),
            "parametros_recibidos": parametros
        }

# Inicializar el agente
agent = MCPFacturaAgent()

# ------------------------------
# Autenticación
# ------------------------------

def verificar_autenticacion(request: Request):
    authorization = request.headers.get("Authorization")
    
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("❌ Intento de acceso sin token")
        raise HTTPException(status_code=401, detail="Token requerido")
    
    token = authorization.replace("Bearer ", "").strip()
    if token != AUTH_SECRET:
        logger.warning("❌ Token inválido")
        raise HTTPException(status_code=401, detail="Token inválido")
    
    return True

# ------------------------------
# Endpoints
# ------------------------------

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "status": "active",
        "service": "MCP Agent Server - Factura Processing",
        "timestamp": datetime.now().isoformat(),
        "agente": "MCP Factura Agent",
        "endpoints": [
            "GET /",
            "GET /health", 
            "POST /",
            "POST /procesar-factura",
            "POST /webhook/factura"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "MCP Agent Server",
        "timestamp": datetime.now().isoformat(),
        "agente": "Activo"
    }

@app.post("/")
async def root_endpoint(request: Request, auth: bool = Depends(verificar_autenticacion)):
    """Endpoint principal para App Script"""
    try:
        data = await request.json()
        action = data.get("action", "hola_mundo")
        parameters = data.get("parameters", {})
        
        logger.info(f"📥 Llamada recibida - Action: {action}")
        
        if action == "hola_mundo":
            return await agent.hola_mundo(parameters)
        elif action == "procesar_factura":
            ruta_gcs = parameters.get("ruta_gcs")
            correo = parameters.get("correo_remitente")
            if not ruta_gcs:
                return {"status": "error", "message": "Se requiere ruta_gcs"}
            return await agent.procesar_factura_desde_gcs(ruta_gcs, correo)
        elif action == "validar_factura":
            rutas = parameters.get("rutas_bucket", [])
            return await agent.validar_factura(rutas)
        else:
            return {
                "status": "error", 
                "message": f"Acción no reconocida: {action}",
                "actions_available": ["hola_mundo", "procesar_factura", "validar_factura"]
            }
            
    except Exception as e:
        logger.error(f"❌ Error en endpoint principal: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/procesar-factura")
async def procesar_factura_directo(request: Request, auth: bool = Depends(verificar_autenticacion)):
    """Endpoint directo para procesar facturas"""
    try:
        data = await request.json()
        ruta_gcs = data.get("ruta_gcs")
        correo_remitente = data.get("correo_remitente")
        
        if not ruta_gcs:
            return {"status": "error", "message": "Se requiere ruta_gcs"}
            
        return await agent.procesar_factura_desde_gcs(ruta_gcs, correo_remitente)
        
    except Exception as e:
        logger.error(f"❌ Error procesando factura: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/webhook/factura")
async def webhook_factura(request: Request, auth: bool = Depends(verificar_autenticacion)):
    """Webhook para recibir facturas desde múltiples fuentes"""
    try:
        data = await request.json()
        
        # Soporte para diferentes formatos de webhook
        ruta_gcs = data.get("ruta_gcs") or data.get("gcs_path") or data.get("file_path")
        correo_remitente = data.get("correo_remitente") or data.get("email") or data.get("from")
        asunto = data.get("asunto") or data.get("subject", "")
        
        logger.info(f"🌐 Webhook recibido - Correo: {correo_remitente}")
        
        if not ruta_gcs:
            return {"status": "error", "message": "No se proporcionó ruta GCS"}
            
        resultado = await agent.procesar_factura_desde_gcs(ruta_gcs, correo_remitente, asunto)
        
        # Log del resultado
        logger.info(f"✅ Webhook procesado - Resultado: {resultado.get('status', 'unknown')}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return {"status": "error", "message": str(e)}

# ------------------------------
# Tools MCP (para compatibilidad)
# ------------------------------

@app.post("/tools/validar-factura")
async def tool_validar_factura(request: Request, auth: bool = Depends(verificar_autenticacion)):
    """Tool para validar facturas (compatibilidad con MCP)"""
    try:
        data = await request.json()
        rutas_bucket = data.get("rutas_bucket", [])
        return await agent.validar_factura(rutas_bucket)
    except Exception as e:
        logger.error(f"❌ Error en tool validar-factura: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/tools/enviar-sheets")
async def tool_enviar_sheets(request: Request, auth: bool = Depends(verificar_autenticacion)):
    """Tool para enviar a sheets (compatibilidad con MCP)"""
    try:
        data = await request.json()
        factura = data.get("factura", {})
        correo = data.get("correo_remitente", "")
        return await agent.enviar_a_sheets(factura, correo)
    except Exception as e:
        logger.error(f"❌ Error en tool enviar-sheets: {e}")
        return {"status": "error", "message": str(e)}

# ------------------------------
# Servidor Principal
# ------------------------------

@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    logger.info("🚀 MCP Agent Server starting...")
    logger.info(f"🔑 Authentication: {'Enabled' if AUTH_SECRET else 'Disabled'}")
    logger.info(f"📦 Bucket: {BUCKET_NAME}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🌐 Starting MCP Agent Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")