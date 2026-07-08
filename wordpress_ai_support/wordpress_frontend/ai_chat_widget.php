add_action( 'wp_footer', 'add_custom_ai_chat_widget' );
function add_custom_ai_chat_widget() {
    // آدرس لوگوی سایت شما
    $site_logo_url = 'https://bluewaverobotics.ir/wp-content/uploads/2026/07/IMG_1903.png';
    $send_icon_url = 'https://bluewaverobotics.ir/wp-content/uploads/2026/07/paper-plane-solid-full.svg';
    ?>
    <style>
      /* Main widget container */
      #ai-chat-widget {
        position: fixed;
        bottom: 25px;
        right: 25px;
        z-index: 2147483647 !important;
        font-family: 'IRANYekan', 'Yekan', 'B Yekan', Tahoma, sans-serif;
        direction: rtl;
      }
      
      /* Floating action button */
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
        z-index: 2147483647 !important;
      }
      
      #ai-chat-button:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 12px 25px rgba(124, 58, 237, 0.5);
      }

      /* Chat window styling */
      #ai-chat-window {
        display: none;
        opacity: 0;
        width: 400px;
        height: 600px;
        background: #ffffff;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        flex-direction: column;
        overflow: hidden;
        margin-bottom: 20px;
        border: 1px solid #f3f4f6;
        transform: translateY(20px);
        transition: opacity 0.3s ease, transform 0.3s ease, height 0.3s ease, bottom 0.3s ease;
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
        padding: 22px 20px;
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
        font-size: 18px;
      }

      .header-status {
        font-size: 14px;
        color: #e5e7eb;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 5px;
      }

      .status-dot {
        width: 9px;
        height: 9px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        transition: background-color 0.3s;
      }
      
      .status-typing .status-dot {
        background-color: #f59e0b;
        animation: pulse-dot 1s infinite alternate;
      }
      
      @keyframes pulse-dot {
        from { opacity: 0.4; }
        to { opacity: 1; }
      }

      #ai-chat-close {
        cursor: pointer;
        font-size: 22px;
        opacity: 0.8;
        transition: opacity 0.2s;
        background: rgba(255,255,255,0.2);
        width: 34px;
        height: 34px;
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

      #ai-chat-messages::-webkit-scrollbar { width: 6px; }
      #ai-chat-messages::-webkit-scrollbar-track { background: transparent; }
      #ai-chat-messages::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }

      .chat-msg-wrapper {
        display: flex;
        flex-direction: column;
        max-width: 85%;
      }

      .chat-msg {
        padding: 14px 18px;
        font-size: 16px;
        line-height: 1.7;
        word-wrap: break-word;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
      }

      .msg-user-wrapper {
        align-self: flex-start;
      }
      
      .msg-user {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
        color: white;
        border-radius: 18px 18px 4px 18px;
      }

      .msg-bot-wrapper {
        align-self: flex-end;
        display: flex;
        gap: 10px;
        max-width: 90%;
      }
      
      .bot-avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: auto;
        overflow: hidden;
        background: #ffffff;
        border: 1px solid #e2e8f0;
      }

      .bot-avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
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
        align-items: center;
      }

      #ai-chat-input {
        flex: 1;
        padding: 12px 18px;
        border: 1px solid #e2e8f0;
        border-radius: 25px;
        outline: none;
        font-family: inherit;
        font-size: 15px;
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
        width: 48px;
        height: 48px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s;
        flex-shrink: 0;
        padding: 15px;
      }

      #ai-chat-send:hover {
        transform: scale(1.05);
      }

      #ai-chat-send img {
        width: 36px !important;
        height: 36px !important;
        object-fit: contain;
        /* اگر عکس شما تیره است و میخواهید سفید شود (اختیاری): */
        /* filter: brightness(0) invert(1); */
      }

      /* استایل‌های موبایل */
      @media (max-width: 480px) {
        #ai-chat-widget {
          position: fixed;
          bottom: 0;
          right: 0;
          z-index: 2147483647 !important;
        }
        
        #ai-chat-window {
          width: calc(100vw - 40px);
          height: 75vh !important; 
          max-height: 700px;
          bottom: 150px !important; 
          right: 20px;
          left: auto;
          margin-bottom: 0;
          border-radius: 20px;
          position: fixed !important;
          z-index: 2147483647 !important;
          border: 1px solid #f3f4f6;
          transform: translateY(20px);
        }
        
        #ai-chat-window.show {
          transform: translateY(0);
        }
        
        #ai-chat-window.keyboard-active {
          height: 40vh !important; 
          bottom: 80px !important; 
        }
        
        #ai-chat-header {
          padding: 15px;
        }
        
        .chat-msg {
          font-size: 15px;
          padding: 12px 15px;
        }
        
        #ai-chat-button {
          position: fixed !important;
          bottom: 70px !important; 
          right: 20px !important;
          z-index: 2147483647 !important;
        }
        
        #ai-chat-input-area {
          padding: 12px 10px;
        }
      }
    </style>

    <div id="ai-chat-widget">
      <div id="ai-chat-window">
        <div id="ai-chat-header">
          <div class="header-info">
            <span class="header-title">پشتیبانی هوشمند</span>
            <span class="header-status" id="chat-status-text"><span class="status-dot"></span> Online</span>
          </div>
          <div id="ai-chat-close">✕</div>
        </div>
        
        <div id="ai-chat-messages">
          <div class="msg-bot-wrapper">
            <div class="bot-avatar"><img src="<?php echo esc_url($site_logo_url); ?>" alt="Bot Logo"></div>
            <div class="chat-msg msg-bot">سلام! من دستیار هوشمند سایت هستم. چطور می‌توانم به شما کمک کنم؟</div>
          </div>
        </div>
        
        <div id="ai-chat-input-area">
          <input type="text" id="ai-chat-input" placeholder="پیام خود را بنویسید..." autocomplete="off" />
          <button id="ai-chat-send">
            <img src="<?php echo esc_url($send_icon_url); ?>" alt="Send Button">
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
        // Variables Definition
        const chatWidget = document.getElementById('ai-chat-widget');
        const chatWindow = document.getElementById('ai-chat-window');
        const chatBtn = document.getElementById('ai-chat-button');
        const closeBtn = document.getElementById('ai-chat-close');
        const sendBtn = document.getElementById('ai-chat-send');
        const inputField = document.getElementById('ai-chat-input');
        const messagesBox = document.getElementById('ai-chat-messages');
        const statusText = document.getElementById('chat-status-text');
        
        const logoUrl = "<?php echo esc_js($site_logo_url); ?>";

        // Close Chat Function
        function closeChat() {
            chatWindow.classList.remove('show');
            setTimeout(() => chatWindow.style.display = 'none', 300);
        }

        // Toggle Chat Window
        chatBtn.addEventListener('click', (e) => {
              e.stopPropagation(); 
              
              if (chatWindow.style.display === 'flex') {
                  closeChat();
              } else {
                  chatWindow.style.display = 'flex';
                  setTimeout(() => chatWindow.classList.add('show'), 10);
              }
        });

        // Close button click
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeChat();
        });

        // Outside click to close
        document.addEventListener('click', function(event) {
            if (event.target.closest('#ai-chat-button')) return;

            const isClickInside = chatWidget.contains(event.target);
            if (!isClickInside && chatWindow.classList.contains('show')) {
                closeChat();
            }
        });

        // Prevent closing when clicking inside the window
        chatWindow.addEventListener('click', function(e) {
            e.stopPropagation();
        });

        // Function to append messages with correct structure
        function appendMessage(message, sender) {
            const wrapper = document.createElement('div');
            wrapper.className = sender === 'bot' ? 'chat-msg-wrapper msg-bot-wrapper' : 'chat-msg-wrapper msg-user-wrapper';
            
            if (sender === 'bot') {
                const avatar = document.createElement('div');
                avatar.className = 'bot-avatar';
                avatar.innerHTML = `<img src="${logoUrl}" alt="Bot">`;
                wrapper.appendChild(avatar);
            }

            const msgDiv = document.createElement('div');
            msgDiv.className = sender === 'bot' ? 'chat-msg msg-bot' : 'chat-msg msg-user';
            
            // Using innerHTML to render HTML buttons from server
            msgDiv.innerHTML = message;
            
            wrapper.appendChild(msgDiv);
            messagesBox.appendChild(wrapper);
            messagesBox.scrollTop = messagesBox.scrollHeight;
        }

        // Send Message Function
        async function sendMessage() {
            const text = inputField.value.trim();
            if (!text) return;

            appendMessage(text, 'user');
            inputField.value = '';

            statusText.innerHTML = '<span class="status-dot"></span> Typing...';
            statusText.classList.add('status-typing');

            try {
                const response = await fetch('https://chat.bluewaverobotics.ir/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });

                statusText.innerHTML = '<span class="status-dot"></span> Online';
                statusText.classList.remove('status-typing');

                // حالت اول: سرور ارور داده (مثل تمام شدن توکن یا خطای 500 در پایتون)
                if (!response.ok) {
                    appendMessage('متاسفانه در حال حاضر سرویس هوش مصنوعی به دلیل ترافیک بالا یا محدودیت سرور در دسترس نیست. لطفاً دقایقی دیگر مجدداً تلاش کنید.', 'bot');
                    return; // توقف اجرای بقیه کد
                }

                const data = await response.json();

                // حالت دوم: سرور وصل شده ولی پاسخ خالی یا نامعتبر داده است
                if(data.reply) {
                   appendMessage(data.reply, 'bot');
                } else {
                   appendMessage('متاسفانه در پردازش درخواست شما خطایی رخ داد. لطفاً سوال خود را با جمله‌بندی دیگری مطرح کنید.', 'bot');
                }

            } catch (error) {
                // حالت سوم: کلا اینترنت کاربر قطع است یا سرور خاموش شده (ارور شبکه)
                console.error("API Error:", error);
                statusText.innerHTML = '<span class="status-dot"></span> Online';
                statusText.classList.remove('status-typing');
                appendMessage('ارتباط با سرور پشتیبانی قطع شده است. لطفاً وضعیت اینترنت خود را بررسی کرده و لحظاتی بعد دوباره تلاش کنید.', 'bot');
            }
        }

        // Event Listeners for sending
        sendBtn.addEventListener('click', sendMessage);
        inputField.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
      });
    </script>
    <?php
}