#!/usr/bin/env python3
"""
Batch Ingestion Script - Text-based PDFs Only
Automates ingestion of the 7 PDFs that work without OCR
"""

from llm_meta_v2 import LLMMetaEngine
from pathlib import Path

# Initialize the oracle
print("Initializing LLM Meta Oracle...")
oracle = LLMMetaEngine()

# Define the 7 text-based PDFs (no OCR needed)
# Resolve FUEL directory relative to this script so the bundle is portable
FUEL_DIR = (Path(__file__).resolve().parent / "FUEL")

text_books = [
    {
        "filename": "Manufacturing Consent [The Political Economy Of The Mass Media].pdf",
        "title": "Manufacturing Consent",
        "author": "Chomsky & Herman",
        "category": "media theory"
    },
    {
        "filename": "philip_e._tetlock_-_superforecasting_the_art_and_science_of_prediction.pdf",
        "title": "Superforecasting",
        "author": "Tetlock",
        "category": "forecasting"
    },
    {
        "filename": "The Grand Chessboard - Zbigniew Brzezinski.pdf",
        "title": "The Grand Chessboard",
        "author": "Brzezinski",
        "category": "geopolitics"
    },
    {
        "filename": "The structure of scentific revolutions.pdf",
        "title": "The Structure of Scientific Revolutions",
        "author": "Kuhn",
        "category": "philosophy of science"
    },
    {
        "filename": "the-tragedy-of-great-power-politics-0393020258-2001030915_compress.pdf",
        "title": "The Tragedy of Great Power Politics",
        "author": "Mearsheimer",
        "category": "international relations"
    },
    {
        "filename": "Why-Nations-Fail_-The-Origins-o-Daron-Acemoglu.pdf",
        "title": "Why Nations Fail",
        "author": "Acemoglu & Robinson",
        "category": "political economy"
    },
    {
        "filename": "yuval_noah_harari-sapiens_a_brief_histor.pdf",
        "title": "Sapiens",
        "author": "Harari",
        "category": "history"
    }
]

print("\n" + "="*70)
print("BATCH INGESTION - Text-based PDFs")
print("="*70)
print(f"\nBooks to ingest: {len(text_books)}")
print("Estimated time: ~60 minutes total")
print("\nNote: You can stop anytime with Ctrl+C and resume later.")
print("="*70)

# Ask for confirmation
response = input("\nStart batch ingestion? (y/n): ").strip().lower()
if response != 'y':
    print("Cancelled.")
    exit()

# Track progress
total_mechanisms = 0
successful = []
failed = []

for i, book_data in enumerate(text_books, 1):
    print(f"\n{'='*70}")
    print(f"[{i}/{len(text_books)}] Processing: {book_data['title']}")
    print(f"{'='*70}")
    
    file_path = FUEL_DIR / book_data['filename']
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        failed.append(book_data['title'])
        continue
    
    try:
        book_info = {
            "title": book_data['title'],
            "author": book_data['author'],
            "category": book_data['category']
        }
        
        # Count mechanisms before
        before_count = oracle.collection.count()
        
        # Ingest
        oracle.ingest_book(str(file_path), book_info)
        
        # Count mechanisms after
        after_count = oracle.collection.count()
        mechanisms_added = after_count - before_count
        
        total_mechanisms += mechanisms_added
        successful.append(book_data['title'])
        
        print(f"\n✅ Successfully ingested: {book_data['title']}")
        print(f"   Mechanisms added: {mechanisms_added}")
        print(f"   Total in database: {after_count}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        break
    except Exception as e:
        print(f"\n❌ Error ingesting {book_data['title']}: {e}")
        failed.append(book_data['title'])

# Final report
print("\n" + "="*70)
print("BATCH INGESTION COMPLETE")
print("="*70)
print(f"\n✅ Successful: {len(successful)}/{len(text_books)}")
for title in successful:
    print(f"   • {title}")

if failed:
    print(f"\n❌ Failed: {len(failed)}")
    for title in failed:
        print(f"   • {title}")

print(f"\n📊 Total mechanisms extracted: {total_mechanisms}")
print(f"   Database now contains: {oracle.collection.count()} mechanisms")

print("\n" + "="*70)
print("Next steps:")
print("  1. Run: python llm-meta-v2.py")
print("  2. Type: stats")
print("  3. Type: query")
print("  4. Ask strategic questions!")
print("="*70)
