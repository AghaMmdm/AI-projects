# قرارداد API — برای استفاده در اپ موبایل (Android)

این سند برای زمانیه که می‌خواید فیلد/صفحه چت رو به اپ اندروید فعلی‌تون اضافه کنید.
سمت سرور همین الان آماده و در دسترسه؛ فقط کافیه از اپ به این endpoint وصل بشید.

## Endpoint

```
POST https://chat.bluewaverobotics.ir/chat/mobile
```

## Headers

| هدر | مقدار | اجباری؟ |
|---|---|---|
| `Content-Type` | `application/json` | بله |
| `X-App-Key` | مقدار `MOBILE_APP_API_KEY` که در `.env` سرور تنظیم کردید | بله (اگر در سرور مقداردهی شده باشه) |

## Request Body

```json
{
  "message": "تفاوت BlueMind و BlueLab چیه؟"
}
```

## Response Body (موفق — 200)

```json
{
  "reply_markdown": "بر اساس اطلاعات موجود، BlueMind ... در مقابل BlueLab ...",
  "links": [
    { "title": "مشاهده اطلاعات بیشتر", "url": "https://bluewaverobotics.ir/shop" }
  ],
  "model_used": "gemini",
  "is_fast_answer": false
}
```

### توضیح فیلدها

- **`reply_markdown`**: متن پاسخ به فرمت Markdown خام (نه HTML). در اپ اندروید با یک کتابخانه‌ی رندر Markdown
  (مثل [Markwon](https://github.com/noties/Markwon)) نمایشش بدید تا بولد، لیست، و جدول درست دیده بشن.
- **`links`**: لیست جدای لینک‌هایی که در پاسخ اومده. به‌جای parse کردن HTML، این‌ها رو مستقیم به شکل
  دکمه‌ی نیتیو (`Button` + `Intent(ACTION_VIEW)`) نمایش بدید.
- **`model_used`**: یکی از مقادیر `local_faq` / `gemini` / `groq` / `error`. می‌تونید برای دیباگ یا آمار داخلی نگهش دارید؛
  لازم نیست به کاربر نهایی نمایش داده بشه.
- **`is_fast_answer`**: اگه `true` باشه یعنی پاسخ از پیش‌فیلتر محلی (سوالات پرتکرار) اومده، نه از LLM.

## خطاها

| کد وضعیت | دلیل | پیشنهاد رفتار در اپ |
|---|---|---|
| `400` | فیلد `message` خالیه | جلوی ارسال پیام خالی رو تو UI بگیرید |
| `401` | هدر `X-App-Key` غلط یا خالیه | این یعنی مشکل تنظیمات اپه، نه کاربر نهایی |
| `429` | Rate limit — کاربر خیلی سریع پیام فرستاده | پیام «کمی صبر کنید» نشون بدید |
| `500` | خطای داخلی سرور (مثلاً LLM در دسترس نیست) | همون پیام fallback که در نمونه کد پایین هست رو نشون بدید |
| خطای شبکه (timeout/no internet) | ارتباط برقرار نشد | پیام «اتصال اینترنت را بررسی کنید» + دکمه تلاش مجدد |

## نمونه کد Kotlin (Retrofit)

```kotlin
data class ChatRequest(val message: String)
data class LinkItem(val title: String, val url: String)
data class ChatResponse(
    val reply_markdown: String,
    val links: List<LinkItem> = emptyList(),
    val model_used: String,
    val is_fast_answer: Boolean
)

interface SupportApi {
    @POST("chat/mobile")
    suspend fun sendMessage(@Body request: ChatRequest): ChatResponse
}

object RetrofitInstance {
    val api: SupportApi by lazy {
        Retrofit.Builder()
            .baseUrl("https://chat.bluewaverobotics.ir/")
            .addConverterFactory(MoshiConverterFactory.create())
            .client(
                OkHttpClient.Builder()
                    .addInterceptor { chain ->
                        val req = chain.request().newBuilder()
                            .addHeader("X-App-Key", BuildConfig.APP_API_KEY)
                            .build()
                        chain.proceed(req)
                    }
                    .build()
            )
            .build()
            .create(SupportApi::class.java)
    }
}
```

> نکته امنیتی: `APP_API_KEY` رو در `BuildConfig` یا `local.properties` بذارید، نه هاردکد داخل کد —
> این کار جلوگیری از commit کردن اشتباهی کلید به گیت‌هاب رو راحت‌تر می‌کنه (هرچند در نهایت چون داخل
> APK کامپایل می‌شه باز هم قابل استخراجه؛ این کلید فقط لایه اول دفاعیه، نه امنیت کامل).

## تست سریع با curl (قبل از نوشتن کد اندروید)

```bash
curl -X POST https://chat.bluewaverobotics.ir/chat/mobile \
  -H "Content-Type: application/json" \
  -H "X-App-Key: YOUR_MOBILE_APP_API_KEY" \
  -d '{"message": "سلام"}'
```

مستندات تعاملی و خودکار (Swagger UI) هم روی آدرس زیر در دسترسه (فقط برای تست، نه برای production عمومی):

```
https://chat.bluewaverobotics.ir/docs
```
