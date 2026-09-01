"""
اسکریپت کمکی برای بازسازی دیتابیس برداری FAISS.

اجرا از ریشه پروژه:
    python3 scripts/build_vector_db.py

هر بار که محتوای data/bluewave_knowledge_base_V6.txt تغییر کرد، این اسکریپت رو
دوباره اجرا کنید تا vector_store به‌روز بشه.
"""
import sys
import os

# اضافه کردن ریشه پروژه به sys.path تا import کردن core کار کنه
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag_core import initialize_vector_db

if __name__ == "__main__":
    initialize_vector_db()
