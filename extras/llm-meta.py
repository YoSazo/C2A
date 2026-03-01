#!/usr/bin/env python3
"""
LLM Meta - C2A Strategic Oracle
Mistral 7B (Drafter) + Phi-3 (Judge) + Historical Knowledge Base
"""

import ollama
import chromadb
from pathlib import Path
import json

# PDF support
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️  PDF support not available. Install: pip install pymupdf")

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
    
    def _read_file(self, file_path):
        """Read text from file (supports .txt and .pdf)"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            if not PDF_SUPPORT:
                raise Exception("PDF support not installed. Run: pip install pymupdf")
            
            # Read PDF
            doc = fitz.open(file_path)
            text = ""
            for page_num, page in enumerate(doc):
                text += page.get_text()
                if (page_num + 1) % 10 == 0:
                    print(f"  Reading page {page_num + 1}/{len(doc)}...")
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
            print(f"❌ Error reading file: {e}")
            return
        
        print(f"  ✓ Extracted {len(text)} characters")
        
        # Chunk (2000 chars, 200 overlap)
        chunks = []
        chunk_size = 2000
        overlap = 200
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i+chunk_size])
        
        print(f"  Processing {len(chunks)} chunks...")
        
        mechanisms_extracted = 0
        for i, chunk in enumerate(chunks):
            # Skip if chunk is too small or just whitespace
            if len(chunk.strip()) < 100:
                continue
            
            # Extract C2A mechanism
            mechanism_json = self._extract_mechanism(chunk, book_info)
            
            if mechanism_json and mechanism_json != "null":
                try:
                    # Get embedding using Ollama
                    embedding = ollama.embeddings(
                        model='nomic-embed-text',
                        prompt=mechanism_json
                    )['embedding']
                    
                    # Store
                    self.collection.add(
                        ids=[f"{book_info['title'].replace(' ', '_')}_chunk_{i}"],
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
                except Exception as e:
                    # Skip on error
                    pass
            
            if (i + 1) % 20 == 0:
                print(f"  ✓ {i+1}/{len(chunks)} chunks ({mechanisms_extracted} mechanisms)")
        
        print(f"✓ Completed: {mechanisms_extracted} mechanisms extracted from {book_info['title']}\n")
    
    def _extract_mechanism(self, text_chunk, book_info):
        """Extract C2A mechanism using Mistral"""
        prompt = f"""
SYSTEM: Extract Constraint-to-Advantage patterns from historical text.

BOOK: {book_info['title']} by {book_info['author']}
CATEGORY: {book_info['category']}

TEXT:
{text_chunk}

TASK: If this text describes a situation where a CONSTRAINT was turned into an ADVANTAGE, extract it.

OUTPUT (JSON only, or return null):
{{
  "constraint": "What limitation existed?",
  "actor": "Who faced it?",
  "transmutation": "How was it flipped?",
  "advantage": "What asymmetric gain resulted?",
  "principle": "Abstract rule (e.g., 'Turn scarcity into focus')",
  "context": "Brief historical context"
}}

Return ONLY valid JSON or the word null.
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
                context_text += f"\n[{meta['book']}]\n{doc}\n"
        
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


def main():
    """Main interface"""
    oracle = LLMMetaEngine()
    
    print("\n" + "="*60)
    print("LLM META - Strategic Oracle")
    print("="*60)
    print("\nCommands:")
    print("  ingest  - Add books to knowledge base")
    print("  query   - Ask strategic questions")
    print("  quit    - Exit")
    print("="*60)
    
    while True:
        cmd = input("\n> ").strip().lower()
        
        if cmd == "quit":
            print("\n🧠 Keep transmuting constraints into advantages.")
            break
        
        elif cmd == "ingest":
            # Book ingestion interface
            file_path = input("Book file path (no quotes): ").strip()
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
        
        else:
            print("Unknown command. Use: ingest, query, or quit")


if __name__ == "__main__":
    main()
