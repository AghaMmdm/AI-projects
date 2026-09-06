# API contract — for the Kotlin/Android app

## Endpoint

```
POST https://your-server-domain/chat
```

## Headers

| Header | Value | Required? |
|---|---|---|
| `Content-Type` | `application/json` | Yes |
| `X-App-Key` | The value of `MOBILE_APP_API_KEY` from the server's `.env` | Yes (if set on the server) |

## Request body

```json
{
  "message": "کد بده تا با I2C2 به OLED وصل بشم"
}
```

## Response body (200 OK)

```json
{
  "reply_markdown": "برای اتصال به نمایشگر OLED از طریق I2C2...\n\n```python\nfrom machine import I2C, Pin\ni2c = I2C(2, scl=Pin('Y9'), sda=Pin('Y10'))\n```",
  "links": [],
  "model_used": "gemini",
  "is_fast_answer": false
}
```

### Field notes

- **`reply_markdown`**: raw Markdown, may include fenced ```python code blocks. Render with a Markdown
  library (e.g. [Markwon](https://github.com/noties/Markwon)) so code blocks and formatting display correctly —
  do not show this as plain text.
- **`links`**: usually empty for this project (the datasheet knowledge base has no URLs). Will start
  containing entries once `data/company_info.md` includes links (store, contact page, etc.).
- **`model_used`**: one of `local_faq` / `gemini` / `groq` / `error`. Useful for debugging/analytics, not
  meant to be shown to the end user.
- **`is_fast_answer`**: `true` if the reply came from the local greeting shortcut rather than the RAG+LLM pipeline.

## Errors

| Status | Reason | Suggested app behavior |
|---|---|---|
| `400` | Empty `message` field | Prevent sending empty messages from the UI |
| `401` | Missing/invalid `X-App-Key` | Configuration bug in the app, not a user-facing error |
| `429` | Rate limit exceeded | Show "please wait a moment" |
| `500` | Internal server error (e.g. all LLM providers down) | Show the fallback message from the response, or a generic retry prompt |
| Network error (timeout / no connection) | — | Show "check your internet connection" + a retry button |

## Kotlin (Retrofit) example

```kotlin
data class ChatRequest(val message: String)
data class LinkItem(val title: String, val url: String)
data class ChatResponse(
    val reply_markdown: String,
    val links: List<LinkItem> = emptyList(),
    val model_used: String,
    val is_fast_answer: Boolean
)

interface AssistantApi {
    @POST("chat")
    suspend fun sendMessage(@Body request: ChatRequest): ChatResponse
}

object RetrofitInstance {
    val api: AssistantApi by lazy {
        Retrofit.Builder()
            .baseUrl("https://your-server-domain/")
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
            .create(AssistantApi::class.java)
    }
}
```

> Security note: `APP_API_KEY` still ends up inside the compiled APK and can be extracted by decompiling it.
> Keeping it in `BuildConfig` (not hardcoded inline) mainly helps avoid accidentally committing it to git —
> it is not a substitute for real security if that becomes a concern later.

## Quick test with curl (before writing any Kotlin code)

```bash
curl -X POST https://your-server-domain/chat \
  -H "Content-Type: application/json" \
  -H "X-App-Key: YOUR_MOBILE_APP_API_KEY" \
  -d '{"message": "پین‌های I2C کدومن؟"}'
```

Interactive Swagger docs are also available (for testing only, not for public production use) at:

```
https://your-server-domain/docs
```
