add_action( 'wp_footer', 'add_custom_ai_chat_widget' );
function add_custom_ai_chat_widget() {
    ?>
    <style>
      /* Chat Widget Container */
      #ai-chat-widget {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999999;
        font-family: Tahoma, Arial, sans-serif;
        direction: rtl;
      }
      
      /* Floating Bubble Button */
      #ai-chat-button {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: #2563eb;
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        font-size: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s;
      }
      #ai-chat-button:hover {
        transform: scale(1.05);
      }

      /* Chat Window Box */
      #ai-chat-window {
        display: none;
        width: 350px;
        height: 500px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        flex-direction: column;
        overflow: hidden;
        margin-bottom: 15px;
        border: 1px solid #e5e7eb;
      }

      /* Chat Header */
      #ai-chat-header {
        background: #2563eb;
        color: white;
        padding: 15px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      #ai-chat-close {
        cursor: pointer;
        font-size: 18px;
      }

      /* Messages Area */
      #ai-chat-messages {
        flex: 1;
        padding: 15px;
        overflow-y: auto;
        background: #f9fafb;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      /* Message Bubbles */
      .chat-msg {
        max-width: 80%;
        padding: 10px 14px;
        border-radius: 10px;
        font-size: 14px;
        line-height: 1.6;
        word-wrap: break-word;
      }
      .msg-user {
        background: #2563eb;
        color: white;
        align-self: flex-start; 
        border-bottom-right-radius: 2px;
      }
      .msg-bot {
        background: #e5e7eb;
        color: #1f2937;
        align-self: flex-end; 
        border-bottom-left-radius: 2px;
      }

      /* Input Area */
      #ai-chat-input-area {
        display: flex;
        padding: 10px;
        border-top: 1px solid #e5e7eb;
        background: white;
      }
      #ai-chat-input {
        flex: 1;
        padding: 10px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        outline: none;
        font-family: inherit;
        font-size: 14px;
      }
      #ai-chat-input:focus {
        border-color: #2563eb;
      }
      #ai-chat-send {
        background: #2563eb;
        color: white;
        border: none;
        padding: 0 15px;
        margin-right: 8px;
        border-radius: 6px;
        cursor: pointer;
        font-family: inherit;
      }
    </style>

    <div id="ai-chat-widget">
      <div id="ai-chat-window">
        <div id="ai-chat-header">
          <span>پشتیبانی هوشمند</span>
          <span id="ai-chat-close">✖</span>
        </div>
        <div id="ai-chat-messages">
          <div class="chat-msg msg-bot">سلام! من دستیار هوشمند سایت هستم. چطور می‌توانم کمکتان کنم؟</div>
        </div>
        <div id="ai-chat-input-area">
          <input type="text" id="ai-chat-input" placeholder="پیام خود را بنویسید..." autocomplete="off" />
          <button id="ai-chat-send">ارسال</button>
        </div>
      </div>
      <button id="ai-chat-button">💬</button>
    </div>

    <script>
      document.addEventListener("DOMContentLoaded", function() {
        const chatBtn = document.getElementById('ai-chat-button');
        const chatWindow = document.getElementById('ai-chat-window');
        const closeBtn = document.getElementById('ai-chat-close');
        const sendBtn = document.getElementById('ai-chat-send');
        const inputField = document.getElementById('ai-chat-input');
        const messagesBox = document.getElementById('ai-chat-messages');

        // Toggle chat visibility
        chatBtn.addEventListener('click', () => {
          chatWindow.style.display = chatWindow.style.display === 'flex' ? 'none' : 'flex';
        });

        // Close chat
        closeBtn.addEventListener('click', () => {
          chatWindow.style.display = 'none';
        });

        // Handle sending message to Python API
        async function sendMessage() {
          const text = inputField.value.trim();
          if (!text) return;

          // Display user message
          addMessage(text, 'msg-user');
          inputField.value = '';

          // Display loading indicator
          const loadingId = addMessage('در حال تایپ...', 'msg-bot');

          try {
            // Fetch request to local FastAPI server
            const response = await fetch('http://127.0.0.1:8000/chat', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            // Remove loading indicator
            document.getElementById(loadingId).remove();

            // Display bot response
            if(data.reply) {
               addMessage(data.reply, 'msg-bot');
            } else {
               addMessage('پاسخ معتبری دریافت نشد.', 'msg-bot');
            }

          } catch (error) {
            console.error("API Error:", error);
            document.getElementById(loadingId).remove();
            addMessage('ارتباط با سرور هوش مصنوعی برقرار نشد!', 'msg-bot');
          }
        }

        // Helper function to append message to chat box
        function addMessage(text, className) {
          const msgDiv = document.createElement('div');
          msgDiv.className = 'chat-msg ' + className;
          msgDiv.innerText = text;
          
          const msgId = 'msg-' + Date.now();
          msgDiv.id = msgId;
          
          messagesBox.appendChild(msgDiv);
          messagesBox.scrollTop = messagesBox.scrollHeight;
          return msgId;
        }

        // Allow pressing Enter to send
        inputField.addEventListener('keypress', function (e) {
          if (e.key === 'Enter') {
            sendMessage();
          }
        });

        sendBtn.addEventListener('click', sendMessage);
      });
    </script>
    <?php
}