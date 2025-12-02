# server.py - Servicio A: Servidor de Tools/MCP

import asyncio
import logging
import os
from fastmcp import FastMCP
from tool import validar_factura_tool, enviar_factura_a_sap_tool
from utilities.image_storage import upload_image_to_gcs

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Crear servidor MCP
mcp = FastMCP("MCP Server S4HANA Tools")

# ------------------------------
# 1. TOOL: Subir PDF desde EasyContact a GCS
# ------------------------------
@mcp.tool()
def subir_pdf_easycontact(user_email: str, image_url: str) -> str:
    """
    Sube la factura desde el link de EasyContact a Google Cloud Storage (GCS).
    
    Parámetros:
        user_email: email del usuario que envía el mensaje
        image_url: url del archivo adjunto en EasyContact (pdf, imagen, doc, etc.)
    
    Devuelve:
        Confirmación de subida de archivo y la ruta GCS
    """
    url = upload_image_to_gcs(user_email, image_url)
    if url:
        return f"Archivo subido correctamente a GCS: {url}"
    else:
        return "Error al subir el archivo."


# ------------------------------
# 2. TOOL: Validar Factura
# ------------------------------
@mcp.tool()
def validar_factura(rutas_bucket: list[str]) -> dict:
    """
    Valida facturas desde Google Cloud Storage (GCS). 
    Devuelve un dict con el resultado de la validación y los datos de la factura si es válida.
    """
    logger.info(f"Tool: 'validar_factura' called with rutas_bucket={rutas_bucket}")
    resultado = validar_factura_tool(rutas_bucket)
    logger.info(f"Resultado: {resultado}")
    return resultado


# ------------------------------
# 3. TOOL: Enviar Factura a SAP S/4HANA
# ------------------------------
@mcp.tool()
def enviar_factura_a_sap(datos_factura: dict, correo_remitente: str) -> dict:
    """
    Envía los datos validados de la factura al sistema SAP S/4HANA.
    
    Parámetros:
        datos_factura: dict con los datos validados (proveedor, monto, etc.)
        correo_remitente: correo que realizó la consulta

    Devuelve:
        dict con el resultado de la operación (ej. ID de documento SAP)
    """
    logger.info(f"Tool: 'enviar_factura_a_sap' llamada para el correo={correo_remitente}")
    resultado_sap = enviar_factura_a_sap_tool(datos_factura, correo_remitente)
    return resultado_sap


# ------------------------------
# Ejecución (Protocolo MCP para el Agente)
# ------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"MCP server started on port {port}")
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )
    )