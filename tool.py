import json
import os
import requests
import logging
# from utilities.image_storage import download_pdf_to_tempfile # <- Descomentar cuando exista
# from utilities.general import ( # <- Descomentar cuando exista
#     get_transcript_document_cloud_vision,
#     get_openai_answer,
#     get_clean_json
# )
# from prompts import get_invoice_validator_prompt # <- Descomentar cuando exista

logger = logging.getLogger(__name__)

# URL de tu iFlow en BTP
BTP_ENDPOINT = "https://c93fd89ctrial.it-cpitrial05-rt.cfapps.us10-001.hana.ondemand.com/http/factura_mcp"

# ----------------------------------------------------------------------
# FUNCIONES AUXILIARES (YA EXISTENTES)
# ----------------------------------------------------------------------

def preparar_factura_sap(rutas_bucket: list[str]) -> dict:
    """
    Descarga el archivo, realiza OCR y extracción LLM. Devuelve el payload SAP.
    """
    try:
        if not rutas_bucket:
            return {"status": "error", "mensaje": "Sin rutas de imagen"}
            
        # Procesar la primera imagen
        ruta_gcs = rutas_bucket[0]
        logger.info(f"📄 Procesando: {ruta_gcs}")
        
        # 1. Descarga y OCR
        # ruta_temp = download_pdf_to_tempfile(ruta_gcs) # <- Comentado
        # text_factura = get_transcript_document_cloud_vision(ruta_temp) # <- Comentado
        text_factura = "PO: 4500012345, Monto: 1250.50" # <- SIMULACIÓN DE OCR
        logger.info("Simulación de OCR/Descarga exitosa.")

        # 2. Extracción LLM
        # system_prompt, user_prompt = get_invoice_validator_prompt(text_factura) # <- Comentado
        # raw_result = get_openai_answer(system_prompt, user_prompt) # <- Comentado
        # datos = json.loads(get_clean_json(raw_result)) # <- Comentado
        
        # SIMULACIÓN DE EXTRACCIÓN LLM
        datos = {
            "factura_valida": True,
            "monto_total": "1250.50",
            "fecha_emision": "2025-11-25",
            "purchase_order": "4500012345",
            "purchase_order_item": "00010"
        }
        
        # 3. Validación y Mapeo
        if not datos.get("factura_valida"):
            return {"status": "error", "mensaje": "Factura inválida según IA", "datos": datos}

        # Construcción Payload SAP
        monto = str(datos.get("monto_total", "0.00"))
        
        sap_payload = {
            "d": {
                "CompanyCode": "1000",
                "DocumentDate": f"{datos.get('fecha_emision')}T00:00:00",
                "PostingDate": f"{datos.get('fecha_emision')}T00:00:00",
                "InvoiceGrossAmount": monto,
                "DocumentCurrency": "BOB",
                "InvoicingParty": "10000000",
                "to_SuplrInvcItemPurOrdRef": {
                    "results": [{
                        "SupplierInvoiceItem": "00001",
                        "PurchaseOrder": datos.get("purchase_order"),
                        "PurchaseOrderItem": datos.get("purchase_order_item", "00010"),
                        "DocumentCurrency": "BOB",
                        "SupplierInvoiceItemAmount": monto,
                        "TaxCode": "V0"
                    }]
                }
            }
        }
        
        return {"status": "success", "sap_payload": sap_payload}

    except Exception as e:
        logger.error(f"Excepción en preparar_factura_sap: {e}")
        return {"status": "error", "mensaje": str(e)}


def enviar_factura_sap(resultado_preparacion: dict, correo: str) -> dict:
    """
    Intenta obtener el token CSRF y enviar la factura a SAP BTP.
    """
    CLIENT_ID = os.getenv("BTP_CLIENT_ID")
    CLIENT_SECRET = os.getenv("BTP_CLIENT_SECRET")
    
    sap_payload = resultado_preparacion.get("sap_payload")
    if not sap_payload:
        return {"status": "error", "message": "No hay payload SAP"}

    logger.info("Simulación: Iniciando intento de conexión a SAP BTP.")

    # # 1. GET Token (COMENTADO)
    # try:
    #     token_res = requests.get(
    #         BTP_ENDPOINT, 
    #         auth=(CLIENT_ID, CLIENT_SECRET), 
    #         headers={'X-CSRF-Token': 'Fetch'},
    #         timeout=10
    #     )
    #     csrf_token = token_res.headers.get('X-CSRF-Token')
    #     cookies = token_res.cookies
    # except Exception as e:
    #     return {"status": "error", "message": f"Fallo Token: {e}"}

    # # 2. POST Factura (COMENTADO)
    # try:
    #     post_res = requests.post(
    #         BTP_ENDPOINT,
    #         auth=(CLIENT_ID, CLIENT_SECRET),
    #         json=sap_payload,
    #         headers={'X-CSRF-Token': csrf_token, 'Content-Type': 'application/json'},
    #         cookies=cookies,
    #         timeout=20
    #     )
        
    #     if post_res.status_code in [200, 201]:
    #         return {"status": "success", "message": post_res.text}
    #     else:
    #         return {"status": "error", "message": f"HTTP {post_res.status_code}: {post_res.text}"}
            
    # except Exception as e:
    #     return {"status": "error", "message": f"Fallo POST: {e}"}
    
    # SIMULACIÓN DE ÉXITO DE SAP
    return {"status": "success", "message": "Simulación: Factura enviada correctamente a SAP BTP."}

# ----------------------------------------------------------------------
# FUNCIÓN DE ORQUESTACIÓN PRINCIPAL (Llamada desde server.py)
# ----------------------------------------------------------------------

def preparar_y_enviar_factura_sap_tool(rutas_bucket: list[str], correo_remitente: str) -> dict:
    """
    Función principal que ejecuta toda la cadena de valor para un Webhook:
    1. Prepara el payload SAP (Descarga, OCR, IA, Mapeo).
    2. Envía la factura a SAP BTP.
    """
    logger.info(f"*** INICIANDO PROCESO DE FACTURA desde {correo_remitente} ***")
    
    # 1. Preparar Payload (Llamada a preparar_factura_sap)
    resultado_preparacion = preparar_factura_sap(rutas_bucket)
    
    if resultado_preparacion.get("status") == "error":
        logger.error(f"Fallo en preparación de payload: {resultado_preparacion.get('mensaje')}")
        return {"status": "error", "message": f"Fallo en preparación: {resultado_preparacion.get('mensaje')}"}
        
    # 2. Enviar a SAP BTP (Llamada a enviar_factura_sap)
    resultado_envio = enviar_factura_sap(resultado_preparacion, correo_remitente)
    
    if resultado_envio.get("status") == "error":
        logger.error(f"Fallo en envío a SAP: {resultado_envio.get('message')}")
        return {"status": "error", "message": f"Fallo en envío a SAP: {resultado_envio.get('message')}"}
        
    # 3. Éxito
    logger.info("*** PROCESO COMPLETO Y EXITOSO ***")
    return {"status": "success", "message": resultado_envio.get("message")}