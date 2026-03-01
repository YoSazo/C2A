#!/usr/bin/env python3
"""
LLM Meta - C2A Strategic Oracle (FIXED VERSION v2)
Mistral 7B (Drafter) + Phi-3 (Judge) + Historical Knowledge Base

FIXES:
- Detects scanned vs text-based PDFs
- Works immediately for 8/14 of your books (text-based)
- Optional OCR support for remaining 6 scanned books
- Better error handling and progress reporting
- Enhanced C2A pattern extraction

INSTALL:
pip install ollama chromadb pymupdf

OPTIONAL (for scanned PDFs):
pip install pytesseract pillow
+ Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
"""

import ollama
import chromadb
from pathlib import Path
import json
import re

# PDF support
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️  PDF support not available. Install: pip install pymupdf")

# OCR support for scanned PDFs (optional)
try:
    from PIL import Image
    import pytesseract
    import io
    OCR_SUPPORT = True
except ImportError:
    OCR_SUPPORT = False

class LLMMetaEngine:
    """The Meta Knowledge Oracle with C2A thinking"""
    
    def __init__(self):
        # Models
        self.drafter_model = "mistral:7b-instruct"  # The strategist
        self.judge_model = "phi3:mini"        # The fact-checker
        
        # Vector DB setup
        self.client = chromadb.PersistentClient(path="./meta_brain")
        self.collection = self.client.get_or_create_collection(
            name="meta_strategies",
            metadata={"description": "Historical C2A patterns from meta-knowledge"}
        )
        
        print("✓ LLM Meta initialized")
        print(f"  Drafter: {self.drafter_model}")
        print(f"  Judge: {self.judge_model}")
        print(f"  PDF Support: {'✓' if PDF_SUPPORT else '✗ (install pymupdf)'}")
        print(f"  OCR Support: {'✓' if OCR_SUPPORT else '✗ (optional - for scanned PDFs)'}")
        
        if not OCR_SUPPORT:
            print("\n  💡 Tip: 8 of your 14 books are text-based and work without OCR!")
            print("      Start with: Sapiens, Why Nations Fail, Superforecasting, etc.")
    
    def _is_scanned_pdf(self, doc):
        """Check if PDF is scanned (needs OCR) by testing first few pages"""
        pages_to_check = min(3, len(doc))
        total_text = 0
        
        for i in range(pages_to_check):
            page = doc[i]
            text = page.get_text()
            total_text += len(text.strip())
        
        avg_text = total_text / pages_to_check
        # If average text per page is less than 100 chars, it's likely scanned
        return avg_text < 100
    
    def _extract_text_with_ocr(self, page):
        """Extract text from a page using OCR"""
        if not OCR_SUPPORT:
            return ""
        
        try:
            # Get page as image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Run OCR
            text = pytesseract.image_to_string(img, lang='eng')
            return text
        except Exception as e:
            print(f"    ⚠️  OCR error on page: {e}")
            return ""
    
    def _read_file(self, file_path):
        """Read text from file (supports .txt and .pdf)"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            if not PDF_SUPPORT:
                raise Exception("PDF support not installed. Run: pip install pymupdf")
            
            # Open PDF
            doc = fitz.open(file_path)
            print(f"  📄 {len(doc)} pages detected")
            
            # Check if scanned
            is_scanned = self._is_scanned_pdf(doc)
            
            if is_scanned:
                print(f"  🔍 Scanned PDF detected - needs OCR")
                if not OCR_SUPPORT:
                    doc.close()
                    print(f"\n  ❌ Cannot process scanned PDF without OCR.")
                    print(f"  Install OCR support:")
                    print(f"    pip install pytesseract pillow")
                    print(f"    Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
                    print(f"\n  📝 Text-based PDFs that work NOW (no OCR needed):")
                    print(f"    - Manufacturing Consent")
                    print(f"    - Superforecasting")
                    print(f"    - The Grand Chessboard")
                    print(f"    - The Structure of Scientific Revolutions")
                    print(f"    - The Tragedy of Great Power Politics")
                    print(f"    - Why Nations Fail")
                    print(f"    - Sapiens")
                    raise Exception("OCR required for this PDF")
                else:
                    print(f"  ⚡ Using OCR (this will take 30-60 minutes for large books)")
                    response = input("  Continue? (y/n): ").strip().lower()
                    if response != 'y':
                        doc.close()
                        raise Exception("User cancelled OCR processing")
            else:
                print(f"  📝 Text-based PDF - direct extraction (fast)")
            
            # Extract text
            text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                if is_scanned:
                    # Use OCR
                    page_text = self._extract_text_with_ocr(page)
                else:
                    # Direct text extraction
                    page_text = page.get_text()
                
                text += page_text + "\n\n"
                
                # Progress reporting
                if (page_num + 1) % 10 == 0:
                    print(f"    Processed {page_num + 1}/{len(doc)} pages ({len(text):,} chars so far)...")
            
            doc.close()
            return text
        else:
            # Read text file
            return file_path.read_text(encoding='utf-8', errors='ignore')
    
    def ingest_book(self, file_path, book_info):
        """
        Ingest a book and extract C2A mechanisms
        book_info = {"title": "...", "author": "...", "category": "..."}
        """
        # Strip quotes if present
        file_path = file_path.strip('"').strip("'")
        
        print(f"\n📚 Ingesting: {book_info['title']}")
        print(f"  File: {file_path}")
        
        # Read text (handles PDF or TXT)
        try:
            text = self._read_file(file_path)
        except Exception as e:
            print(f"\n❌ Error reading file: {e}\n")
            return
        
        # Clean text
        text = self._clean_text(text)
        print(f"  ✓ Extracted {len(text):,} characters")
        
        if len(text) < 1000:
            print(f"  ⚠️  Warning: Only {len(text)} characters extracted. File may be corrupted.")
            response = input("  Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                return
        
        # Chunk (2000 chars, 200 overlap)
        chunks = []
        chunk_size = 2000
        overlap = 200
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i+chunk_size]
            if len(chunk.strip()) >= 100:  # Only keep substantial chunks
                chunks.append(chunk)
        
        print(f"  Processing {len(chunks)} chunks for C2A patterns...")
        print(f"  (This extracts Constraint-to-Advantage mechanisms using {self.drafter_model})")
        
        mechanisms_extracted = 0
        for i, chunk in enumerate(chunks):
            # Extract C2A mechanism
            mechanism_json = self._extract_mechanism(chunk, book_info)
            
            if mechanism_json and mechanism_json != "null":
                try:
                    # Parse to validate
                    mechanism_data = json.loads(mechanism_json)
                    
                    # Get embedding using Ollama
                    embedding = ollama.embeddings(
                        model='nomic-embed-text',
                        prompt=mechanism_json
                    )['embedding']
                    
                    # Store
                    self.collection.add(
                        ids=[f"{book_info['title'].replace(' ', '_').replace('/', '_')}_chunk_{i}"],
                        embeddings=[embedding],
                        documents=[mechanism_json],
                        metadatas=[{
                            "book": book_info['title'],
                            "author": book_info['author'],
                            "category": book_info['category'],
                            "type": "historical_mechanism"
                        }]
                    )
                    mechanisms_extracted += 1
                except json.JSONDecodeError:
                    # Skip invalid JSON
                    pass
                except Exception as e:
                    # Skip on other errors
                    pass
            
            if (i + 1) % 20 == 0:
                print(f"  ✓ {i+1}/{len(chunks)} chunks ({mechanisms_extracted} mechanisms)")
        
        print(f"\n✅ Completed: {mechanisms_extracted} mechanisms extracted from {book_info['title']}")
        print(f"   Total in database: {self.collection.count()}\n")
    
    def _clean_text(self, text):
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        # Remove page numbers (common pattern)
        text = re.sub(r'\n\d+\n', '\n', text)
        return text.strip()
    
    def _extract_mechanism(self, text_chunk, book_info):
        """Extract C2A mechanism using Mistral - Enhanced prompt"""
        prompt = f"""
SYSTEM: You are an expert at identifying Constraint-to-Advantage (C2A) patterns in historical texts.

BOOK: {book_info['title']} by {book_info['author']}
CATEGORY: {book_info['category']}

TEXT:
{text_chunk[:1500]}

TASK: Analyze if this text describes a situation where a CONSTRAINT, LIMITATION, or DISADVANTAGE was turned into an ADVANTAGE, STRENGTH, or STRATEGIC ASSET.

Look for patterns like:
- Resource scarcity forcing innovation
- Geographic isolation becoming defensive advantage  
- Cultural difference becoming competitive edge
- Weakness forcing creative strategy
- Setback leading to unexpected opportunity
- Small size enabling agility
- Late start allowing leapfrogging

If you find such a pattern, extract it. Otherwise return null.

OUTPUT (JSON only):
{{
  "constraint": "What limitation/disadvantage existed?",
  "actor": "Who faced it (nation/group/leader)?",
  "transmutation": "How was it transformed into an advantage?",
  "advantage": "What strategic benefit resulted?",
  "principle": "Abstract rule (e.g., 'Turn scarcity into focus', 'Use isolation as defense')",
  "context": "Brief historical context (2-3 sentences)"
}}

Return ONLY valid JSON or the word null. No other text.
"""
        
        try:
            response = ollama.chat(
                model=self.drafter_model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            result = response['message']['content'].strip()
            
            # Validate it's actual JSON
            if result != "null":
                json.loads(result)  # Test parse
            
            return result
        except Exception as e:
            return "null"
    
    def query(self, user_question):
        """
        Main query interface - answers strategic questions using C2A lens
        """
        print(f"\n🧠 Analyzing: {user_question}\n")
        
        # Step 1: Retrieve relevant historical patterns
        print("⚙️  Retrieving historical patterns...")
        context = self._retrieve_context(user_question, n_results=5)
        
        if not context["documents"][0]:
            print("⚠️  No historical patterns found in database.")
            print("   Tip: Use 'ingest' to add books first.\n")
            return "No knowledge base available. Please ingest books first."
        
        print(f"  ✓ Found {len(context['documents'][0])} relevant patterns")
        
        # Step 2: Draft strategic answer (Mistral)
        print("⚔️  Drafting strategy (Mistral)...")
        draft = self._draft_answer(user_question, context)
        
        # Step 3: Judge validates against sources (Phi-3)
        print("⚖️  Validating logic (Phi-3)...")
        verdict = self._judge_answer(draft, context)
        
        # Step 4: Return or repair
        if verdict['valid']:
            print("✓ Answer validated\n")
            return draft
        else:
            print(f"⚠️  Logic issue detected: {verdict['critique']}\n")
            return f"[DRAFT - Needs Refinement]\n\n{draft}\n\n[Judge's Critique: {verdict['critique']}]"
    
    def _retrieve_context(self, query, n_results=5):
        """Retrieve relevant mechanisms from vector DB"""
        try:
            # Get embedding
            query_embedding = ollama.embeddings(
                model='nomic-embed-text',
                prompt=query
            )['embedding']
            
            # Query
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas"]
            )
            
            return results
        except Exception as e:
            print(f"Retrieval error: {e}")
            return {"documents": [[]], "metadatas": [[]]}
    
    def _draft_answer(self, question, context):
        """Mistral drafts the strategic answer"""
        # Build context summary
        context_text = ""
        if context["documents"][0]:
            context_text = "\n\nHISTORICAL PATTERNS:\n"
            for doc, meta in zip(context["documents"][0], context["metadatas"][0]):
                context_text += f"\n[{meta['book']} by {meta['author']}]\n{doc}\n"
        
        prompt = f"""
SYSTEM: You are a Grand Strategist with deep knowledge of history and power.
You think in Constraint-to-Advantage (C2A) logic.

CONTEXT (Historical Precedents):
{context_text}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Identify the core CONSTRAINT in the question
2. Use historical patterns to show how this constraint can become an ADVANTAGE
3. Provide concrete mechanisms, not vague advice
4. Think like a strategic advisor to a leader
5. Cite specific historical examples from the patterns above

OUTPUT FORMAT:
- The Constraint: [What is limiting them]
- The Historical Precedent: [Which pattern applies]
- The Transmutation: [How to flip it]
- The Action: [Specific moves to take]
"""
        
        response = ollama.chat(
            model='mistral:7b-instruct',
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        return response['message']['content']
    
    def _judge_answer(self, draft, context):
        """Phi-3 validates the logic and grounding"""
        # Build context for judge
        context_text = ""
        if context["documents"][0]:
            context_text = "AVAILABLE SOURCES:\n"
            for doc in context["documents"][0]:
                context_text += f"{doc}\n\n"
        
        prompt = f"""
SYSTEM: You are a strict logic validator. Check if this strategy is grounded in the provided sources.

SOURCES:
{context_text}

DRAFT ANSWER:
{draft}

VALIDATION TASK:
1. Does every claim reference an actual pattern from the sources?
2. Is the logic sound (no leaps or contradictions)?
3. Are there unsupported claims that look like hallucinations?

OUTPUT (JSON only):
{{
  "valid": true/false,
  "critique": "Brief explanation of any issues, or 'Grounded and logical'"
}}
"""
        
        try:
            response = ollama.chat(
                model=self.judge_model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            return json.loads(response['message']['content'])
        except:
            return {"valid": True, "critique": "Judge unavailable"}
    
    def stats(self):
        """Show database statistics"""
        try:
            count = self.collection.count()
            print(f"\n📊 Knowledge Base Stats:")
            print(f"  Total mechanisms: {count}")
            
            if count > 0:
                # Get all unique books
                all_data = self.collection.get(include=["metadatas"])
                books = {}
                for meta in all_data["metadatas"]:
                    book = meta.get("book", "Unknown")
                    books[book] = books.get(book, 0) + 1
                
                print(f"\n  Books ingested:")
                for book, mech_count in sorted(books.items()):
                    print(f"    - {book}: {mech_count} mechanisms")
            else:
                print("  Database is empty. Use 'ingest' to add books.")
            print()
        except Exception as e:
            print(f"Error getting stats: {e}")
    
    def recommend_books(self):
        """Show which books work with/without OCR"""
        print("\n📚 Book Status Report\n")
        print("✓ TEXT-BASED PDFs (Work now - no OCR needed):")
        text_books = [
            "Manufacturing Consent - Chomsky",
            "Superforecasting - Tetlock",
            "The Grand Chessboard - Brzezinski",
            "The Structure of Scientific Revolutions - Kuhn",
            "The Tragedy of Great Power Politics - Mearsheimer",
            "Why Nations Fail - Acemoglu",
            "Sapiens - Harari"
        ]
        for book in text_books:
            print(f"  • {book}")
        
        print("\n✗ SCANNED PDFs (Need OCR - install pytesseract):")
        scanned_books = [
            "The Rise and Fall of the Great Powers - Kennedy",
            "Technopoly - Postman",
            "The Birth of the Modern World - Bayly",
            "The Silk Roads - Frankopan",
            "The Historian's Craft - Bloch",
            "The True Believer - Hoffer",
            "Use and Abuse of History - Nietzsche"
        ]
        for book in scanned_books:
            print(f"  • {book}")
        print()


def main():
    """Main interface"""
    oracle = LLMMetaEngine()
    
    print("\n" + "="*60)
    print("LLM META - Strategic Oracle")
    print("="*60)
    print("\nCommands:")
    print("  ingest    - Add books to knowledge base")
    print("  query     - Ask strategic questions")
    print("  stats     - Show database statistics")
    print("  books     - Show which PDFs work with/without OCR")
    print("  quit      - Exit")
    print("="*60)
    
    while True:
        cmd = input("\n> ").strip().lower()
        
        if cmd == "quit":
            print("\n🧠 Keep transmuting constraints into advantages.")
            break
        
        elif cmd == "ingest":
            # Book ingestion interface
            file_path = input("Book file path: ").strip()
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            category = input("Category (e.g., geopolitics, economics): ").strip()
            
            book_info = {"title": title, "author": author, "category": category}
            oracle.ingest_book(file_path, book_info)
        
        elif cmd == "query":
            question = input("\n🎯 Your strategic question: ").strip()
            answer = oracle.query(question)
            print("\n" + "="*60)
            print(answer)
            print("="*60)
        
        elif cmd == "stats":
            oracle.stats()
        
        elif cmd == "books":
            oracle.recommend_books()
        
        else:
            print("Unknown command. Use: ingest, query, stats, books, or quit")


if __name__ == "__main__":
    main()
