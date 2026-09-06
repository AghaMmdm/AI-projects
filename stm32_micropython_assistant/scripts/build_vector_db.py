"""
Helper script to (re)build the FAISS vector database.

Run from the project root:
    python3 scripts/build_vector_db.py

Re-run this any time a file in data/ changes (e.g. after filling in
data/company_info.md, or updating the datasheet).
"""
import sys
import os

# Add the project root to sys.path so `from core...` imports work when this
# script is run directly (e.g. `python3 scripts/build_vector_db.py`).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag_core import initialize_vector_db

if __name__ == "__main__":
    initialize_vector_db()
