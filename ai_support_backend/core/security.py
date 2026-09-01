import os
from fastapi import Header, HTTPException, status

# کلید مخفی که فقط اپ موبایل (که بعداً کدش رو اضافه می‌کنید) باید بفرسته.
# مقدارش رو در فایل .env تنظیم کنید: MOBILE_APP_API_KEY=یک-رشته-طولانی-و-تصادفی
MOBILE_APP_API_KEY = os.getenv("MOBILE_APP_API_KEY", "")


async def verify_mobile_api_key(x_app_key: str = Header(default=None)):
    """
    Dependency برای محافظت از /chat/mobile.

    نکته امنیتی مهم: چون این کلید داخل اپ اندروید (APK) قرار می‌گیره، قابل استخراجه.
    این لایه فقط جلوی ربات‌ها و درخواست‌های ساده‌ی مستقیم به سرور رو می‌گیره،
    نه یک راهکار امنیتی کامل. برای امنیت بیشتر در آینده می‌تونید:
      - از Firebase App Check استفاده کنید (تایید می‌کنه درخواست واقعاً از اپ رسمی میاد)
      - یا هر نصب اپ یک device-token موقع اولین اجرا از سرور بگیره
    """
    if not MOBILE_APP_API_KEY:
        # اگر در .env مقداری تنظیم نشده (مثلاً محیط توسعه محلی)، بررسی رو رد می‌کنیم
        # تا توسعه‌دهنده قفل نشه. حتماً قبل از انتشار عمومی این مقدار رو ست کنید.
        return

    if x_app_key != MOBILE_APP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
