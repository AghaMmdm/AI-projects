# Android client (placeholder)

This folder is a placeholder for the Kotlin/Android integration code.

The backend is ready and waiting at:

```
POST https://your-server-domain/chat
```

See [`API_CONTRACT.md`](../../API_CONTRACT.md) in the project root for the
full request/response contract, headers, error codes, and a ready-to-use
Kotlin/Retrofit example.

No RAG logic, LLM calls, or knowledge base handling should live in the app —
all of that stays server-side, per the architecture decision made for this
project. The app is only a thin HTTP client.
