# 🤖 BlueWave AI Support — Backend

این مخزن، بک‌اند مرکزی دستیار هوشمند BlueWave Robotics هست که بر پایه معماری RAG (Retrieval-Augmented
Generation) و FastAPI ساخته شده. این بک‌اند از **چند کلاینت هم‌زمان** پشتیبانی می‌کنه:

- ✅ ویجت وردپرس (فعال، در `clients/wordpress/`)
- 🔜 اپ اندروید (در آینده، جای رزرو شده در `clients/android/`)

نکته مهم معماری: **تمام پردازش (RAG، جستجوی دانش‌نامه، فراخوانی Gemini/Groq) فقط و فقط سمت سرور انجام
می‌شه.** هیچ کلاینتی (نه وردپرس، نه اپ موبایل) مستقیم به Groq یا Gemini وصل نمی‌شه — همه از طریق این
سرور رد می‌شن. دلیلش امنیت کلید API، کنترل هزینه، و امکان مدیریت متمرکز نرخ درخواسته.

## 🏗 ساختار پروژه

```
ai_support_backend/
├── main.py                      # اپلیکیشن FastAPI — دو endpoint: /chat و /chat/mobile
├── core/
│   ├── rag_core.py               # موتور RAG (بدون تغییر منطق، فقط خروجی ساخت‌یافته)
│   ├── response_utils.py         # فرمت‌دهی خروجی (HTML برای وب / JSON برای موبایل)
│   └── security.py               # بررسی API Key برای endpoint موبایل
├── data/
│   └── bluewave_knowledge_base_V6.txt   # دانش‌نامه محصولات
├── scripts/
│   └── build_vector_db.py        # اسکریپت بازسازی دیتابیس FAISS
├── clients/
│   ├── wordpress/
│   │   └── ai_chat_widget.php    # ویجت فعلی وردپرس (بدون تغییر)
│   └── android/
│       └── README.md             # مستندات اتصال برای اپ اندروید (کد بعداً اینجا اضافه می‌شه)
├── API_CONTRACT.md               # قرارداد دقیق API برای توسعه‌ی سمت اندروید
├── requirements.txt
├── .env.example
└── .gitignore
```

## 🔌 دو Endpoint سرور

| Endpoint | مصرف‌کننده | فرمت خروجی | نیاز به API Key |
|---|---|---|---|
| `POST /chat` | ویجت وردپرس فعلی | HTML (دکمه‌های لینک تعبیه‌شده) | خیر (بدون تغییر نسبت به قبل) |
| `POST /chat/mobile` | اپ اندروید (در آینده) | JSON ساخت‌یافته (`reply_markdown` + `links[]`) | بله، هدر `X-App-Key` |

هر دو از همون موتور `rag_core.py` و همون دانش‌نامه استفاده می‌کنن — فقط شکل خروجی فرق داره.

## 🚀 راه‌اندازی اولیه

```bash
git clone <این-مخزن>
cd ai_support_backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# سپس مقادیر GOOGLE_API_KEY / GROQ_API_KEY / MOBILE_APP_API_KEY رو در .env پر کنید
```

ساخت دیتابیس برداری (اولین بار، یا هر بار که دانش‌نامه تغییر کرد):

```bash
python3 scripts/build_vector_db.py
```

اجرای سرور (development):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

اجرای سرور در production با چند worker (برای مقیاس‌پذیری با رشد تعداد کاربر، بدون نیاز به تغییر معماری):

```bash
nohup gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 127.0.0.1:8000 > output.log 2>&1 &
```

## 🔁 به‌روزرسانی روی سرور (Deployment)

```bash
cd /opt/ai_support_backend
git fetch origin
git reset --hard origin/main
git pull origin main

pkill -f gunicorn   # یا pkill -f uvicorn اگر بدون gunicorn اجرا می‌کنید

source venv/bin/activate
pip install -r requirements.txt

# فقط اگر محتوای دانش‌نامه تغییر کرده:
python3 scripts/build_vector_db.py

nohup gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 127.0.0.1:8000 > output.log 2>&1 &
```

## 📱 اضافه کردن کلاینت اندروید (مرحله بعدی)

سرور همین الان برای این کار آماده‌ست. کافیه:

1. فایل [`API_CONTRACT.md`](./API_CONTRACT.md) رو بخونید — قرارداد کامل درخواست/پاسخ + نمونه کد Kotlin توش هست.
2. در پروژه اندروید فعلی‌تون، یک صفحه/فیلد چت اضافه کنید که به `POST /chat/mobile` وصل بشه.
3. مقدار `MOBILE_APP_API_KEY` که در `.env` سرور گذاشتید رو به‌عنوان هدر `X-App-Key` از اپ بفرستید.

هیچ تغییری در `rag_core.py` یا دانش‌نامه لازم نیست — همون منطقی که برای وردپرس کار می‌کنه، عیناً برای
موبایل هم استفاده می‌شه.

## 🔒 امنیت

- Rate limiting (پیش‌فرض ۱۵ درخواست در دقیقه به ازای هر IP، قابل تنظیم با `RATE_LIMIT_PER_MINUTE` در `.env`).
- Endpoint موبایل با هدر `X-App-Key` محافظت می‌شه (نگاه کنید به `core/security.py`).
- کلیدهای Gemini/Groq فقط سمت سرور نگه‌داری می‌شن و هیچ‌وقت به هیچ کلاینتی ارسال نمی‌شن.

## 👨‍💻 توسعه‌دهنده

توسعه‌یافته توسط **Mohammad Rahimi** برای شرکت توسعه فناوری سیستم‌های رباتیک پارسیان (BlueWave Robotics).
