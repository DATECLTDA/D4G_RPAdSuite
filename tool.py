# tool.py (Lógica de Tools)

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# URL de tu iFlow en BTP (usada por enviar_factura_sap)
BTP_ENDPOINT = "https://c93fd89ctrial.it-cpitrial05-rt.cfapps.us10-001.hana.ondemand.com/http/factura_mcp"

# Datos simulados de la Orden de Compra (OC)
SIMULATED_PO = {
    "PurchaseOrder": "4500000004",
    "PurchaseOrderItem": "00020"
}

def preparar_factura_sap(rutas_bucket: list[str]) -> dict:
    """ 
    [SIMULACIÓN] 
    1. Simula la extracción de datos de la factura (usando la ruta GCS).
    2. Construye el payload SAP en el formato exacto requerido.
    """
    try:
        if not rutas_bucket:
            return {"status": "error", "message": "Sin rutas de imagen para validar."}
            
        ruta_gcs = rutas_bucket[0]
        logger.info(f"📄 [SIMULACIÓN OCR] Procesando: {ruta_gcs}")
        
        # 1. SIMULACIÓN DE EXTRACCIÓN (Datos de una factura genérica)
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        datos_extraidos = {
            "factura_valida": True,
            "monto_total": "2900.00",
            "fecha_documento": fecha_actual,
            "proveedor_nombre": "HIPERMAXI S.A.",
        }
        
        # 2. CONSTRUCCIÓN DEL PAYLOAD SAP (Formato exacto solicitado)
        payload_sap = {
            "d": {
                "CompanyCode": "1000",
                "DocumentDate": f"{datos_extraidos['fecha_documento']}T00:00:00",
                "PostingDate": f"{datos_extraidos['fecha_documento']}T00:00:00",
                "SupplierInvoiceIDByInvcgParty": datos_extraidos['proveedor_nombre'],
                "InvoicingParty": "10000000", # Asumiendo un código de proveedor simulado
                "DocumentCurrency": "BOB",
                "InvoiceGrossAmount": datos_extraidos['monto_total'],
                "DueCalculationBaseDate": f"{datos_extraidos['fecha_documento']}T00:00:00",
                "TaxIsCalculatedAutomatically": True,
                "TaxDeterminationDate": f"{datos_extraidos['fecha_documento']}T00:00:00",
                "SupplierInvoiceStatus": "A",
                "to_SuplrInvcItemPurOrdRef": {
                    "results": [
                        {
                            "SupplierInvoiceItem": "00001",
                            "PurchaseOrder": SIMULATED_PO['PurchaseOrder'], 
                            "PurchaseOrderItem": SIMULATED_PO['PurchaseOrderItem'],
                            "DocumentCurrency": "BOB",
                            "QuantityInPurchaseOrderUnit": "500.000",
                            "PurchaseOrderQuantityUnit": "EA",
                            "SupplierInvoiceItemAmount": datos_extraidos['monto_total'],
                            "TaxCode": "V0"
                        }
                    ]
                }
            }
        }
        
        return {
            "status": "success", 
            "message": "Factura validada y payload SAP preparado.", 
            "sap_payload": payload_sap,
            "factura_valida": datos_extraidos['factura_valida']
        }

    except Exception as e:
        logger.error(f"Excepción en preparar_factura_sap: {e}")
        return {"status": "error", "message": f"Error al validar/preparar: {str(e)}"}


def enviar_factura_sap(resultado_preparacion: dict, correo: str) -> dict:
    """ 
    [SIMULACIÓN] 
    Envía el payload SAP a la Integration Suite (BTP).
    """
    sap_payload = resultado_preparacion.get("sap_payload")
    if not sap_payload or not resultado_preparacion.get("factura_valida"):
        return {"status": "error", "message": "Factura no válida o payload ausente."}

    logger.info("⚡ [SIMULACIÓN ENVÍO] Intentando POST a SAP BTP...")
    
    # Aquí iría el código real de requests.post al BTP_ENDPOINT
    # usando las credenciales BTP_USER_CLIENT/SECRET
    
    # Simulamos éxito:
    simulated_doc_id = "5100000001"
    
    return {
        "status": "success", 
        "message": f"Factura enviada a SAP. ID de documento: {simulated_doc_id}",
        "sap_document_id": simulated_doc_id
    }