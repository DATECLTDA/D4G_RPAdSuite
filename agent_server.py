# agent.py (Servicio B: Servidor Agente Flask)

# Usamos os.getenv para las claves secretas (DEBES CONFIGURARLAS EN CLOUD RUN)
# -----------------------------------------------------------------------------------
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") 
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY") # Langsmith opcional
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
API_ACCESS_TOKEN = os.getenv("EASYCONTACT_API_TOKEN")

# URL del Servidor de Tools (Servicio A)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://TU-URL-DEL-SERVICIO-A.run.app") 
# -----------------------------------------------------------------------------------

# ... (Imports)

async def init_agent():
    mcp_client = MultiServerMCPClient({
        "datec_tools": {
            "transport": "streamable_http",
            # APUNTAMOS A LA URL DEL SERVICIO A (FastMCP)
            "url": f"{MCP_SERVER_URL}/sse", 
        },
    })

    tools = await mcp_client.get_tools()
    print(f"✅ {len(tools)} herramientas MCP cargadas: {', '.join([t.name for t in tools])}")

    # Asegúrate de que system_prompt esté alineado con los nombres de tus tools (subir_pdf_easycontact, validar_factura, enviar_factura_a_sheets)
    system_prompt = """ 
    Contexto: Eres Sergio un asistente virtual que responde correos electrónicos de facturación en nombre de la empresa Datec. Tu tarea es usar las tools disponibles, para comprobar la validez de sus facturas y luego subirlas a sheets
    Instrucciones:
    1. Si recibes un enlace de adjunto (archivo de easycontact: [URL]), primero usa la tool **subir_pdf_easycontact** para guardar el archivo en GCS.
    2. Luego, usa la tool **validar_factura** con la ruta GCS.
    3. Si la factura es válida, usa **enviar_factura_a_sheets**.
    4. Responde al usuario de forma clara con el resultado de las acciones.
    """
    
    agent = create_react_agent(model, tools, checkpointer=memory, system_prompt=system_prompt)
    return agent

# ... (El resto del código del Agente Flask, funciones process_message_with_langchain, handle_webhook, etc. se mantiene igual)

if __name__ == '__main__':
    # Usamos el puerto estándar de Cloud Run
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))