import re
import markdown

# regex برای پیدا کردن URLهای خام داخل متن (که قبلاً داخل تگ href قرار نگرفته باشن)
URL_PATTERN = r'(?<!href=")(?<!\()(https?://[^\s<>"]+)'

WEB_BUTTON_TEMPLATE = (
    r'<br><a href="\1" target="_blank" '
    r'style="display:inline-block; margin:10px 0; padding:10px 15px; '
    r'background-color:#0073aa; color:#ffffff; border-radius:5px; '
    r'text-decoration:none; font-weight:bold;">مشاهده اطلاعات بیشتر</a><br>'
)

DEFAULT_LINK_TITLE = "مشاهده اطلاعات بیشتر"


def markdown_to_html_with_buttons(text: str) -> str:
    """
    خروجی مخصوص کلاینت وب (وردپرس): Markdown رو به HTML تبدیل می‌کنه و
    لینک‌های خام رو به دکمه‌های HTML قابل کلیک تبدیل می‌کنه.
    این دقیقاً همون منطق process_response نسخه قبلی main.py هست.
    """
    html_text = markdown.markdown(text, extensions=["tables"])
    return re.sub(URL_PATTERN, WEB_BUTTON_TEMPLATE, html_text)


def extract_links(text: str) -> list[dict]:
    """
    خروجی مخصوص کلاینت موبایل: به‌جای ساختن HTML، فقط URLها رو استخراج می‌کنه
    تا اپ اندروید بتونه با UI نیتیو خودش (دکمه، کارت و ...) نمایششون بده.
    """
    urls = re.findall(r"https?://[^\s<>\"]+", text)
    # حذف تکراری‌ها با حفظ ترتیب
    seen = set()
    links = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            links.append({"title": DEFAULT_LINK_TITLE, "url": url})
    return links


def strip_raw_urls(text: str) -> str:
    """
    اختیاری: برای کلاینت موبایل، چون لینک‌ها جدا در فیلد links برگردونده می‌شن،
    می‌تونید URL خام رو از متن اصلی حذف کنید تا در UI نیتیو تکراری نمایش داده نشه.
    فعلاً استفاده نمی‌شه؛ در صورت نیاز در main.py صداش بزنید.
    """
    return re.sub(r"https?://[^\s<>\"]+", "", text).strip()
