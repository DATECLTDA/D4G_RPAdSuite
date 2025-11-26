import json
import os
import requests
import logging
# from utilities.image_storage import download_pdf_to_tempfile # Comentado
# from utilities.general import ( # Comentado
#     get_transcript_document_cloud_vision,
#     get_openai_answer,
#     get_clean_json
# )
# from prompts import get_invoice_validator_prompt # Comentado

logger = logging.getLogger(__name__)

# URL de tu iFlow en BTP
BTP_ENDPOINT = "https://c93fd89ctrial.it-cpitrial05-rt.cfapps.us10-001.hana.ondemand.com/http/factura_mcp"

# ----------------------------------------------------------------------
# FUNCIONES AUXILIARES (YA EXISTENTES)
# ----------------------------------------------------------------------

def preparar_factura_sap(rutas_bucket: list[str]) -> dict:
    """ [CÓDIGO SIMULADO DE OCR, LLM Y PREPARACIÓN DE PAYLOAD] """
    try:
        if not rutas_bucket:
            return {"status": "error", "mensaje": "Sin rutas de imagen"}
            
        ruta_gcs = rutas_bucket[0]
        logger.info(f"📄 [SIMULACIÓN] Procesando: {ruta_gcs}")
        
        # SIMULACIÓN DE EXTRACCIÓN LLM
        datos = {
            "factura_valida": True,
            "monto_total": "1250.50",
            "fecha_emision": "2025-11-25",
            "purchase_order": "4500012345",
            "purchase_order_item": "00010"
        }
        
        # Construcción Payload SAP (Simulado)
        monto = str(datos.get("monto_total", "0.00"))
        
        sap_payload = {
            "d": {
                "CompanyCode": "1000",
                "DocumentDate": f"{datos.get('fecha_emision')}T00:00:00",
                "InvoiceGrossAmount": monto,
                "DocumentCurrency": "BOB",
                "InvoicingParty": "10000000",
                # ... (resto de campos SAP)
            }
        }
        
        return {"status": "success", "sap_payload": sap_payload}

    except Exception as e:
        logger.error(f"Excepción en preparar_factura_sap: {e}")
        return {"status": "error", "mensaje": str(e)}


def enviar_factura_sap(resultado_preparacion: dict, correo: str) -> dict:
    """ [CÓDIGO SIMULADO DE ENVÍO A SAP] """
    sap_payload = resultado_preparacion.get("sap_payload")
    if not sap_payload:
        return {"status": "error", "message": "No hay payload SAP"}

    logger.info("⚡ [SIMULACIÓN] Iniciando intento de envío a SAP BTP.")
    # Código de requests.get/post a BTP comentado para evitar fallos de credenciales/red
    
    return {"status": "success", "message": "Simulación: Factura enviada correctamente a SAP BTP."}

# ----------------------------------------------------------------------
# FUNCIÓN DE ORQUESTACIÓN PRINCIPAL (Llamada desde server.py)
# ----------------------------------------------------------------------

def preparar_y_enviar_factura_sap_tool(rutas_bucket: list[str], correo_remitente: str) -> dict:
    """
    Función principal que ejecuta toda la cadena de valor: Preparación y Envío.
    """
    logger.info(f"*** INICIANDO PROCESO DE FACTURA desde {correo_remitente} ***")
    
    # 1. Preparar Payload 
    resultado_preparacion = preparar_factura_sap(rutas_bucket)
    
    if resultado_preparacion.get("status") == "error":
        logger.error(f"Fallo en preparación de payload: {resultado_preparacion.get('mensaje')}")
        return {"status": "error", "message": f"Fallo en preparación: {resultado_preparacion.get('mensaje')}"}
        
    # 2. Enviar a SAP BTP
    resultado_envio = enviar_factura_sap(resultado_preparacion, correo_remitente)
    
    if resultado_envio.get("status") == "error":
        logger.error(f"Fallo en envío a SAP: {resultado_envio.get('message')}")
        return {"status": "error", "message": f"Fallo en envío a SAP: {resultado_envio.get('message')}"}
        
    # 3. Éxito
    logger.info("*** PROCESO COMPLETO Y EXITOSO ***")
    return {"status": "success", "message": resultado_envio.get("message")}