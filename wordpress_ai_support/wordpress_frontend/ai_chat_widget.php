add_action( 'wp_footer', 'add_custom_ai_chat_widget' );
function add_custom_ai_chat_widget() {
    ?>
    <style>
      /* Main widget container */
      #ai-chat-widget {
        position: fixed;
        bottom: 25px;
        right: 25px;
        z-index: 999999;
        font-family: 'IRANYekan', 'Yekan', 'B Yekan', Tahoma, sans-serif;
        direction: rtl;
      }
      
      /* Floating action button with pulse animation */
      #ai-chat-button {
        width: 65px;
        height: 65px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
      }
      
      #ai-chat-button:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 12px 25px rgba(124, 58, 237, 0.5);
      }

      /* Chat window styling with slide-in animation */
      #ai-chat-window {
        display: none;
        opacity: 0;
        width: 380px;
        height: 550px;
        background: #ffffff;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        flex-direction: column;
        overflow: hidden;
        margin-bottom: 20px;
        border: 1px solid #f3f4f6;
        transform: translateY(20px);
        transition: opacity 0.3s ease, transform 0.3s ease;
      }

      /* When chat is active */
      #ai-chat-window.show {
        display: flex;
        opacity: 1;
        transform: translateY(0);
      }

      /* Header styling */
      #ai-chat-header {
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        padding: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      }

      .header-info {
        display: flex;
        flex-direction: column;
      }

      .header-title {
        font-weight: 700;
        font-size: 16px;
      }

      .header-status {
        font-size: 12px;
        color: #e5e7eb;
        display: flex;
        align-items: center;
        gap: 5px;
        margin-top: 4px;
      }

      .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
      }

      #ai-chat-close {
        cursor: pointer;
        font-size: 20px;
        opacity: 0.8;
        transition: opacity 0.2s;
        background: rgba(255,255,255,0.2);
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
      }
      
      #ai-chat-close:hover {
        opacity: 1;
        background: rgba(255,255,255,0.3);
      }

      /* Chat messages area */
      #ai-chat-messages {
        flex: 1;
        padding: 20px;
        overflow-y: auto;
        background: #f8fafc;
        display: flex;
        flex-direction: column;
        gap: 15px;
      }

      /* Custom Scrollbar for webkit */
      #ai-chat-messages::-webkit-scrollbar {
        width: 6px;
      }
      #ai-chat-messages::-webkit-scrollbar-track {
        background: transparent;
      }
      #ai-chat-messages::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 10px;
      }

      /* Base message bubble */
      .chat-msg-wrapper {
        display: flex;
        flex-direction: column;
        max-width: 85%;
      }

      .chat-msg {
        padding: 12px 16px;
        font-size: 14px;
        line-height: 1.6;
        word-wrap: break-word;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
      }

      /* User message styling */
      .msg-user-wrapper {
        align-self: flex-start;
      }
      
      .msg-user {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
        color: white;
        border-radius: 18px 18px 4px 18px;
      }

      /* Bot message styling */
      .msg-bot-wrapper {
        align-self: flex-end;
        display: flex;
        gap: 8px;
        max-width: 90%;
      }
      
      .bot-avatar {
        width: 28px;
        height: 28px;
        background: #7c3aed;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        flex-shrink: 0;
        margin-top: auto;
      }

      .msg-bot {
        background: #ffffff;
        color: #334155;
        border: 1px solid #e2e8f0;
        border-radius: 18px 18px 18px 4px;
      }

      /* Input area styling */
      #ai-chat-input-area {
        display: flex;
        padding: 15px;
        background: white;
        border-top: 1px solid #f1f5f9;
        gap: 10px;
      }

      #ai-chat-input {
        flex: 1;
        padding: 10px 15px;
        border: 1px solid #e2e8f0;
        border-radius: 25px;
        outline: none;
        font-family: inherit;
        font-size: 14px;
        background: #f8fafc;
        transition: all 0.2s;
      }

      #ai-chat-input:focus {
        border-color: #7c3aed;
        background: white;
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
      }

      #ai-chat-send {
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        border: none;
        width: 45px;
        height: 45px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s;
      }

      #ai-chat-send:hover {
        transform: scale(1.1);
      }

      #ai-chat-send svg {
        width: 30px !important;
        height: 30px !important;
        fill: currentColor;
        transform: rotate(180deg); /* Adjust for RTL */
      }

      /* Mobile Responsiveness */
      @media (max-width: 480px) {
        #ai-chat-window {
          width: calc(100vw - 40px);
          height: calc(100vh - 120px);
          bottom: 90px;
          right: 20px;
          position: fixed;
        }
      }
    </style>

    <div id="ai-chat-widget">
      <div id="ai-chat-window">
        <div id="ai-chat-header">
          <div class="header-info">
            <span class="header-title">پشتیبانی هوشمند</span>
            <span class="header-status"><span class="status-dot"></span> Online</span>
          </div>
          <div id="ai-chat-close">✕</div>
        </div>
        
        <div id="ai-chat-messages">
          <div class="msg-bot-wrapper">
            <div class="bot-avatar">AI</div>
            <div class="chat-msg msg-bot">سلام! من دستیار هوشمند سایت هستم. چطور می‌توانم به شما کمک کنم؟</div>
          </div>
        </div>
        
        <div id="ai-chat-input-area">
          <input type="text" id="ai-chat-input" placeholder="پیام خود را بنویسید..." autocomplete="off" />
          <button id="ai-chat-send">
            <svg width="30" height="30" viewBox="0 0 24 24" style="fill: white; transform: rotate(180deg);">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
            </svg>
          </button>
        </div>
      </div>
      
      <button id="ai-chat-button">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>
    </div>

    <script>
      document.addEventListener("DOMContentLoaded", function() {
        const chatBtn = document.getElementById('ai-chat-button');
        const chatWindow = document.getElementById('ai-chat-window');
        const closeBtn = document.getElementById('ai-chat-close');
        const sendBtn = document.getElementById('ai-chat-send');
        const inputField = document.getElementById('ai-chat-input');
        const messagesBox = document.getElementById('ai-chat-messages');

        // Toggle chat visibility with animation class
        chatBtn.addEventListener('click', () => {
          if(chatWindow.classList.contains('show')) {
            chatWindow.classList.remove('show');
            setTimeout(() => { chatWindow.style.display = 'none'; }, 300);
          } else {
            chatWindow.style.display = 'flex';
            // Slight delay to allow display:flex to apply before adding opacity class
            setTimeout(() => { chatWindow.classList.add('show'); }, 10);
          }
        });

        // Close chat
        closeBtn.addEventListener('click', () => {
          chatWindow.classList.remove('show');
          setTimeout(() => { chatWindow.style.display = 'none'; }, 300);
        });

        // Function to append messages to the chat DOM
        function appendMessage(text, sender) {
          const wrapper = document.createElement('div');
          
          if (sender === 'user') {
            wrapper.className = 'chat-msg-wrapper msg-user-wrapper';
            wrapper.innerHTML = `<div class="chat-msg msg-user">${text}</div>`;
          } else {
            wrapper.className = 'msg-bot-wrapper';
            wrapper.innerHTML = `
              <div class="bot-avatar">AI</div>
              <div class="chat-msg msg-bot">${text}</div>
            `;
          }
          
          const msgId = 'msg-' + Date.now();
          wrapper.id = msgId;
          messagesBox.appendChild(wrapper);
          
          // Auto-scroll to the bottom
          messagesBox.scrollTop = messagesBox.scrollHeight;
          return msgId;
        }

        // Handle the API request
        async function sendMessage() {
          const text = inputField.value.trim();
          if (!text) return;

          // Render user message and clear input
          appendMessage(text, 'user');
          inputField.value = '';

          // Show typing indicator
          const loadingId = appendMessage('در حال تایپ...', 'bot');

          try {
            // NOTE: Update this URL to your VPS IP once it is ready!
            const response = await fetch('http://127.0.0.1:8000/chat', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            // Remove typing indicator
            document.getElementById(loadingId).remove();

            // Render AI response
            if(data.reply) {
               appendMessage(data.reply, 'bot');
            } else {
               appendMessage('پاسخ معتبری دریافت نشد.', 'bot');
            }

          } catch (error) {
            console.error("API Connection Error:", error);
            document.getElementById(loadingId).remove();
            appendMessage('ارتباط با سرور هوش مصنوعی برقرار نشد!', 'bot');
          }
        }

        // Event listeners for sending message
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