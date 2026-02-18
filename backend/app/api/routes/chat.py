from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.services.adk_agent_service import ADKAgentService

router = APIRouter()
adk_service = ADKAgentService()

class ChatMessage(BaseModel):
    message: str

@router.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """Página HTML con interfaz de chat para el agente ADK"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ADK Agent Chat</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }

            .container {
                width: 100%;
                max-width: 700px;
                height: 600px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            }

            .header h1 {
                font-size: 24px;
                margin-bottom: 5px;
            }

            .header p {
                font-size: 12px;
                opacity: 0.9;
            }

            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
                background: #f8f9fa;
            }

            .message {
                display: flex;
                gap: 10px;
                animation: slideIn 0.3s ease-out;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .message.user {
                justify-content: flex-end;
            }

            .message-content {
                max-width: 500px;
                padding: 12px 16px;
                border-radius: 10px;
                word-wrap: break-word;
                font-size: 14px;
                line-height: 1.4;
            }

            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-bottom-right-radius: 2px;
            }

            .message.agent .message-content {
                background: white;
                color: #333;
                border: 1px solid #e0e0e0;
                border-bottom-left-radius: 2px;
            }

            .message.loading .message-content {
                background: #e8e8e8;
                color: #666;
                font-style: italic;
            }

            .input-area {
                padding: 20px;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 10px;
                background: white;
            }

            input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }

            input:focus {
                border-color: #667eea;
            }

            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
            }

            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            }

            button:active {
                transform: translateY(0);
            }

            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .typing-indicator {
                display: flex;
                gap: 5px;
                padding: 12px 16px;
            }

            .typing-indicator span {
                width: 8px;
                height: 8px;
                background: #999;
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }

            .typing-indicator span:nth-child(2) {
                animation-delay: 0.2s;
            }

            .typing-indicator span:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }

            .chat-messages::-webkit-scrollbar {
                width: 8px;
            }

            .chat-messages::-webkit-scrollbar-track {
                background: #f1f1f1;
            }

            .chat-messages::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }

            .chat-messages::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1> ADK Agent Chat</h1>
                <p>Conversa con el agente de diseño web IA</p>
            </div>

            <div class="chat-messages" id="messages">
                <div class="message agent">
                    <div class="message-content">
                        ¡Hola! Soy un asistente de diseño web impulsado por Google ADK. 
                        ¿En qué puedo ayudarte hoy? Puedo generar diseños para:
                        <br/>• E-commerce
                        <br/>• Portafolios
                        <br/>• Landing pages
                    </div>
                </div>
            </div>

            <div class="input-area">
                <input 
                    type="text" 
                    id="messageInput" 
                    placeholder="Escribe tu pregunta aquí..."
                    autocomplete="off"
                />
                <button id="sendBtn" onclick="sendMessage()">Enviar</button>
            </div>
        </div>

        <script>
            const messageInput = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const messagesDiv = document.getElementById('messages');

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;

                // Agregar mensaje del usuario
                addMessage(message, 'user');
                messageInput.value = '';
                sendBtn.disabled = true;

                // Mostrar indicador de tipeo
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message agent';
                loadingDiv.innerHTML = '<div class="message-content typing-indicator"><span></span><span></span><span></span></div>';
                messagesDiv.appendChild(loadingDiv);
                scrollToBottom();

                try {
                    const response = await fetch('/api/chat/message', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message })
                    });

                    loadingDiv.remove();

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    addMessage(data.response, 'agent');
                } catch (error) {
                    loadingDiv.remove();
                    addMessage(`Error: ${error.message}. Por favor intenta de nuevo.`, 'agent');
                } finally {
                    sendBtn.disabled = false;
                    messageInput.focus();
                }
            }

            function addMessage(text, sender) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                messageDiv.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
                messagesDiv.appendChild(messageDiv);
                scrollToBottom();
            }

            function scrollToBottom() {
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function escapeHtml(text) {
                const map = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#039;'
                };
                return text.replace(/[&<>"']/g, m => map[m]);
            }

            // Focus en input al cargar
            messageInput.focus();
        </script>
    </body>
    </html>
    """

@router.post("/api/chat/message")
async def chat_message(request: ChatMessage):
    """Endpoint para enviar mensajes al agente ADK"""
    user_message = request.message.strip()
    
    if not user_message:
        return {"response": "Por favor envía un mensaje."}
    
    try:
        response = await adk_service.chat(user_message)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error al procesar tu mensaje: {str(e)}"}
