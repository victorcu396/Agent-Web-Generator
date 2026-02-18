from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.agents.web_builder_agent import WebBuilderAgent
from app.dto.prompt_dto import PromptDTO

router = APIRouter()

class ChatMessage(BaseModel):
    message: str

@router.get("/chat", response_class=HTMLResponse)
async def chat_page():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ADK Agent Chat</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }

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
                max-width: 900px;
                height: 700px;
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
            }

            .header h1 { font-size: 24px; margin-bottom: 5px; }
            .header p { font-size: 12px; opacity: 0.9; }

            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
                background: #f8f9fa;
            }

            .message { display: flex; gap: 10px; animation: slideIn 0.3s ease-out; }

            @keyframes slideIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .message.user { justify-content: flex-end; }

            .message-content {
                max-width: 600px;
                padding: 12px 16px;
                border-radius: 10px;
                font-size: 14px;
                line-height: 1.4;
                word-wrap: break-word;
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

            .message.agent iframe {
                width: 100%;
                min-width: 600px;
                height: 400px;
                border: none;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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

            input:focus { border-color: #667eea; }

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

            button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

            .typing-indicator { display: flex; gap: 5px; padding: 12px 16px; }
            .typing-indicator span {
                width: 8px; height: 8px;
                background: #999;
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }
            .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
            .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }

            .chat-messages::-webkit-scrollbar { width: 8px; }
            .chat-messages::-webkit-scrollbar-track { background: #f1f1f1; }
            .chat-messages::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Web Builder</h1>
                <p>Describe la página web que quieres y la generaré para ti</p>
            </div>

            <div class="chat-messages" id="messages">
                <div class="message agent">
                    <div class="message-content">
                        ¡Hola! Soy tu asistente de diseño web. Dime qué página quieres crear:<br/><br/>
                        • <b>Tienda online</b> → "quiero una tienda de ropa"<br/>
                        • <b>Portfolio</b> → "crea mi portfolio de diseñador"<br/>
                        • <b>Landing page</b> → "landing para mi startup de IA"
                    </div>
                </div>
            </div>

            <div class="input-area">
                <input 
                    type="text" 
                    id="messageInput" 
                    placeholder="Describe tu página web..."
                    autocomplete="off"
                />
                <button id="sendBtn" onclick="sendMessage()">Generar</button>
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

                addUserMessage(message);
                messageInput.value = '';
                sendBtn.disabled = true;

                // Indicador de carga
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message agent';
                loadingDiv.innerHTML = '<div class="message-content typing-indicator"><span></span><span></span><span></span></div>';
                messagesDiv.appendChild(loadingDiv);
                scrollToBottom();

                try {
                    const response = await fetch('/api/chat/message', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message })
                    });

                    loadingDiv.remove();

                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                    const data = await response.json();
                    addAgentMessage(data.response);

                } catch (error) {
                    loadingDiv.remove();
                    addTextMessage(`Error: ${error.message}. Por favor intenta de nuevo.`);
                } finally {
                    sendBtn.disabled = false;
                    messageInput.focus();
                }
            }

            function addUserMessage(text) {
                const div = document.createElement('div');
                div.className = 'message user';
                div.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
                messagesDiv.appendChild(div);
                scrollToBottom();
            }

            function addAgentMessage(html) {
                const div = document.createElement('div');
                div.className = 'message agent';

                // Si parece HTML generado, mostrarlo en iframe
                if (html.trim().startsWith('<!DOCTYPE') || html.trim().startsWith('<html')) {
                    const encoded = html.replace(/"/g, '&quot;');
                    div.innerHTML = `<iframe srcdoc="${encoded}"></iframe>`;
                } else {
                    // Si es texto normal, mostrarlo como mensaje
                    div.innerHTML = `<div class="message-content">${escapeHtml(html)}</div>`;
                }

                messagesDiv.appendChild(div);
                scrollToBottom();
            }

            function addTextMessage(text) {
                const div = document.createElement('div');
                div.className = 'message agent';
                div.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
                messagesDiv.appendChild(div);
                scrollToBottom();
            }

            function scrollToBottom() {
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function escapeHtml(text) {
                const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
                return text.replace(/[&<>"']/g, m => map[m]);
            }

            messageInput.focus();
        </script>
    </body>
    </html>
    """

@router.post("/api/chat/message")
async def chat_message(request: ChatMessage):
    user_message = request.message.strip()

    if not user_message:
        return {"response": "Por favor envía un mensaje."}

    try:
        agent = WebBuilderAgent()
        prompt_dto = PromptDTO(prompt=user_message)
        result = await agent.run(prompt_dto)
        return {"response": result.html}
    except Exception as e:
        return {"response": f"Error al procesar tu mensaje: {str(e)}"}