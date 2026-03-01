#!/usr/bin/env python3
"""
C2A-Cortex Integration System v2.0
- Added 90-second "High Velocity" constraint timer
- Live countdown UI
- Level penalties for slow transmutation
"""

import os
import sys
import json
import datetime
import time
import threading
import queue
from pathlib import Path
import textwrap
import shutil

# Import scenario database
try:
    from constraint_scenarios import get_scenario, validate_constraint_identification, score_transmutation, CONSTRAINT_ARCHETYPES
    SCENARIOS_AVAILABLE = True
except ImportError:
    SCENARIOS_AVAILABLE = False
    print("Warning: constraint_scenarios.py not found. Scenario mode disabled.")

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent / "C2A-AI"))
sys.path.append(str(Path(__file__).parent.parent / "cortex"))

# Import core dependencies
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    import ollama
except ImportError as e:
    print(f"Missing core dependency: {e}")
    print("Please install: pip install chromadb sentence-transformers ollama")
    sys.exit(1)

# Import optional dependencies
try:
    import requests
except ImportError:
    requests = None
try:
    import anthropic
except ImportError:
    anthropic = None
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class TimedInput:
    """Handle input with a live countdown timer that doesn't break input"""
    
    @staticmethod
    def get_input_with_timeout(prompt, timeout=90):
        print(f"\n{prompt}")
        print("-" * 60)
        
        # Shared state
        state = {
            'finished': False,
            'input_received': None
        }

        def timer_thread():
            start_time = time.time()
            while not state['finished']:
                elapsed = int(time.time() - start_time)
                remaining = timeout - elapsed
                
                # Move cursor UP 1 line, Print Timer, Move DOWN 1 line
                # \033[A moves up, \033[B moves down (ANSI codes)
                if remaining >= 0:
                    status = f"⏳ Time Remaining: {remaining}s   "
                else:
                    status = f"⚠️  OVERTIME: +{abs(remaining)}s   "
                
                # This sequence updates the line ABOVE the input cursor
                sys.stdout.write(f"\033[s\033[1A\r{status}\033[u")
                sys.stdout.flush()
                
                time.sleep(0.1)

        # 1. Print a placeholder for the timer
        print("⏳ Starting Timer...") 
        
        # 2. Start the timer thread
        t = threading.Thread(target=timer_thread)
        t.daemon = True
        t.start()
        
        # 3. Get input (Main thread blocks here, but timer updates above)
        start_time = time.time()
        try:
            response = input("> ")
        except EOFError:
            response = ""
            
        # 4. cleanup
        state['finished'] = True
        state['input_received'] = response
        duration = time.time() - start_time
        
        # Clear the timer line one last time to look clean
        print("") 
        
        return response, duration



class TerminalUI:
    """Enhanced terminal UI with ASCII art and chat-style input"""

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def get_terminal_width():
        return shutil.get_terminal_size().columns

    @staticmethod
    def display_ascii_art():
        """Display C2A ASCII art"""
        art = """
╔═══════════════════════════════════════════════════════════════╗
║   ██████╗██████╗ █████╗                                       ║
║  ██╔════╝╚════██╗██╔══██╗                                     ║
║  ██║     █████╔╝███████║                                      ║
║  ██║     ██╔═══╝ ██╔══██║                                     ║
║  ╚██████╗███████╗██║  ██║                                     ║
║   ╚═════╝╚══════╝╚═╝  ╚═╝                                     ║
║                                                               ║
║          Enhanced with Cortex Memory & Timer System           ║
╚═══════════════════════════════════════════════════════════════╝
"""
        print(art)

    @staticmethod
    def get_chat_input(prompt, multiline=True):
        """Get input with simple prompt"""
        print(f"\n{prompt}")
        response = input("> ")
        return response.strip()

    @staticmethod
    def display_info_box(title, content, width=None):
        """Display information in a bordered box"""
        terminal_width = TerminalUI.get_terminal_width()
        box_width = width or min(80, terminal_width - 4)
        
        # Wrap content to fit box
        wrapped_lines = []
        for line in content.split('\n'):
            wrapped_lines.extend(textwrap.wrap(line, box_width - 4) or [''])
            
        print(f"\n┌─ {title} " + "─" * (box_width - len(title) - 4) + "┐")
        for line in wrapped_lines:
            padding = box_width - len(line) - 4
            print(f"│ {line}" + " " * padding + " │")
        print("└" + "─" * (box_width - 2) + "┘")

class CortexMemoryEngine:
    """Cortex memory system for C2A integration with anti-plateau mechanisms"""
    
    def __init__(self, collection_name="c2a_memory", ollama_model="mistral:7b-instruct"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedder = None
        self.ollama_model = ollama_model
        self.llm_config = self.load_llm_config()
        
        # Anti-plateau tracking
        self.retrieval_frequency = {}  # Track how often each session is retrieved
        self.last_n_retrievals = []  # Track recent retrievals for diversity
        
        self.initialize_memory()

    def load_llm_config(self):
        """Load LLM configuration"""
        config_path = Path(__file__).parent.parent / "cortex" / "llm_config.json"
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "primary_provider": "ollama",
                "models": {
                    "ollama": {"model": "mistral", "url": "http://localhost:11434"}
                }
            }

    def initialize_memory(self):
        """Initialize ChromaDB and embeddings"""
        try:
            # Initialize ChromaDB
            data_dir = Path(__file__).parent / "memory_data"
            data_dir.mkdir(exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=str(data_dir))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "C2A constraint-to-advantage training sessions"}
            )
            
            # Initialize embedder
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            print("✓ Cortex memory system initialized")
            
        except Exception as e:
            print(f"Error initializing memory: {e}")
            raise

    def query_llm(self, prompt, provider=None):
        """Query configured LLM using Ollama"""
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            return f"LLM Error: {e}"

    def store_session(self, session_data):
        """Store C2A session in vector memory"""
        # Create rich text for embedding
        session_text = f"""
        C2A Training Session {session_data['session_id']}
        Challenge Description: {session_data['description']}
        Core Constraint: {session_data['problem']}
        Generated Alchemies: {session_data['solutions']}
        Selected Alchemy: {session_data['final_alchemy']}
        G-Score: {session_data['g_score']}
        Divergence Score: {session_data['divergence_score']}
        Meta-Cognitive Reflection: {session_data['meta_reflection']}
        Session Date: {session_data['timestamp']}
        """.strip()
        
        # Generate embedding
        embedding = self.embedder.encode(session_text).tolist()
        
        # Store in ChromaDB
        self.collection.add(
            embeddings=[embedding],
            documents=[session_text],
            metadatas=[{
                "session_id": session_data['session_id'],
                "g_score": session_data['g_score'],
                "divergence_score": session_data['divergence_score'],
                "constraint_type": self._classify_constraint(session_data['problem']),
                "timestamp": session_data['timestamp'],
                "type": "c2a_session"
            }],
            ids=[f"c2a_session_{session_data['session_id']}"]
        )

    def retrieve_context(self, query, n_results=5, level=1, min_g_score=None, diversity_mode=False):
        """
        Retrieve relevant past sessions with anti-plateau mechanisms
        
        Args:
            query: Search query
            n_results: Number of results to return
            level: Current user level (affects retrieval strategy)
            min_g_score: Minimum G-Score filter (challenge escalation)
            diversity_mode: Force diversity by penalizing recently-seen sessions
        """
        try:
            # Dynamic retrieval scaling: Higher levels get more context for diversity
            if level >= 70:
                over_retrieve = n_results * 3  # Retrieve 3x, then filter
            elif level >= 40:
                over_retrieve = n_results * 2  # Retrieve 2x, then filter
            else:
                over_retrieve = n_results  # Standard retrieval
            
            query_embedding = self.embedder.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=over_retrieve,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results["documents"][0]:
                return results
            
            # Apply filters and scoring
            scored_results = []
            for doc, meta, distance in zip(
                results["documents"][0], 
                results["metadatas"][0], 
                results["distances"][0]
            ):
                session_id = meta.get('session_id', 'unknown')
                g_score = meta.get('g_score', 0)
                
                # Challenge escalation: Filter low-scoring sessions at high levels
                if min_g_score and g_score < min_g_score:
                    continue
                
                # Novelty calculation: Penalize over-retrieved sessions
                novelty_bonus = self._calculate_novelty_score(session_id, diversity_mode)
                
                # Final score: (similarity × novelty_factor)
                # Lower distance = more similar, but we want novelty too
                adjusted_score = distance / (1.0 + novelty_bonus)
                
                scored_results.append((adjusted_score, doc, meta, distance))
            
            # Sort by adjusted score and take top n_results
            scored_results.sort(key=lambda x: x[0])
            final_results = scored_results[:n_results]
            
            # Track retrievals for future novelty calculations
            for _, _, meta, _ in final_results:
                session_id = meta.get('session_id', 'unknown')
                self._track_retrieval(session_id)
            
            # Reconstruct results in expected format
            return {
                "documents": [[item[1] for item in final_results]],
                "metadatas": [[item[2] for item in final_results]],
                "distances": [[item[3] for item in final_results]]
            }
            
        except Exception as e:
            print(f"Context retrieval error: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def enhanced_validation(self, description, problem, solutions, target, level=1):
        """Enhanced validation using memory context with anti-plateau mechanisms"""
        
        # ANTI-PLATEAU: Dynamic retrieval based on level
        if level >= 70:
            n_results = 12  # More diverse context at high levels
            diversity_mode = True
            min_g_score = 80  # Only show high-quality examples
        elif level >= 40:
            n_results = 10
            diversity_mode = True
            min_g_score = 70
        else:
            n_results = 8  # Standard for beginners
            diversity_mode = False
            min_g_score = None
        
        # Get relevant context from past sessions
        context_query = f"constraint: {problem} solutions: {' '.join(solutions)}"
        context = self.retrieve_context(
            context_query, 
            n_results=n_results,
            level=level,
            min_g_score=min_g_score,
            diversity_mode=diversity_mode
        )
        
        # Build context summary
        context_summary = ""
        if context["documents"][0]:
            context_summary = "\\n\\nRelevant past sessions:\\n"
            for i, (doc, meta) in enumerate(zip(context["documents"][0], context["metadatas"][0])):
                g_score = meta.get('g_score', 'N/A')
                context_summary += f"- Session {meta['session_id']}: G-Score {g_score}\\n"
                
                # Add brief excerpt
                lines = doc.split('\\n')
                constraint_line = next((line for line in lines if 'Core Constraint:' in line), '')
                alchemy_line = next((line for line in lines if 'Selected Alchemy:' in line), '')
                if constraint_line and alchemy_line:
                    context_summary += f"  {constraint_line.strip()}\\n  {alchemy_line.strip()}\\n\\n"
        
        # ADVERSARIAL PROMPTING: Scale difficulty with level
        if level >= 80:
            difficulty_instruction = """
        CRITICAL EVALUATION MODE (Level 80+):
        - This user is ADVANCED. Rate harshly. No participation trophies.
        - If their alchemies are derivative of past sessions, PENALIZE HEAVILY.
        - They should be producing novel angles you've NEVER seen before.
        - G-Scores below 85 at this level indicate regression.
        - Challenge them to transcend their previous patterns.
        - If they're repeating constraint-types they've solved 10+ times, call it out.
            """
        elif level >= 50:
            difficulty_instruction = """
        INTERMEDIATE EVALUATION MODE (Level 50-79):
        - This user should be showing pattern transfer across domains.
        - Rate with moderate harshness.
        - Expect 3+ distinct conceptual angles per session.
        - Push them toward meta-cognitive breakthroughs.
            """
        else:
            difficulty_instruction = """
        BEGINNER EVALUATION MODE (Level 1-49):
        - This user is building foundational skills.
        - Encourage experimentation and divergent thinking.
        - Focus on teaching core constraint-reframing principles.
            """
        
        # Enhanced validation prompt
        validation_prompt = f"""
        You are an expert C2A (Constraint-to-Advantage) trainer with access to this user's complete training history.
        
        USER LEVEL: {level}/100
        {difficulty_instruction}
        
        CURRENT SESSION:
        Challenge: {description}
        Core Constraint: {problem}
        Generated Alchemies: {solutions}
        Target Integration: {target}
        
        {context_summary}
        
        Based on the user's historical patterns and this current session, provide:
        
        1. VALIDATION SCORES (1-100):
        - Divergence Score: How unique/creative are these alchemies? (Compare against their history)
        - G-Score: Overall constraint-to-advantage transformation quality
        - Meta-Cognitive Score: Evidence of higher-order thinking
        
        SCORING CALIBRATION FOR LEVEL {level}:
        - Below {max(60, level - 10)}: Poor - Repeating old patterns
        - {max(60, level - 10)}-{level}: Average - Expected performance
        - {level}-{min(100, level + 10)}: Good - Showing growth
        - {min(100, level + 10)}+: Excellent - Breakthrough thinking
        
        2. PERSONALIZED COACHING:
        - What patterns do you see in their constraint-solving evolution?
        - Which alchemy shows the most sophisticated transmutation thinking?
        - How does this session compare to their previous breakthrough moments?
        - Are they getting stuck in "comfort zone" constraint types?
        
        3. GROWTH INSIGHTS:
        - What constraint-thinking skills are they developing?
        - Where do you see transfer potential to other domains?
        - What should they focus on to reach the next level?
        
        Be specific and reference their historical progress where relevant.
        """
        
        response = self.query_llm(validation_prompt)
        return self._parse_validation_response(response)

    def _classify_constraint(self, constraint):
        """Classify constraint type for metadata"""
        constraint_lower = constraint.lower()
        if any(word in constraint_lower for word in ['time', 'deadline', 'schedule']):
            return 'temporal'
        elif any(word in constraint_lower for word in ['money', 'budget', 'cost', 'resource']):
            return 'resource'
        elif any(word in constraint_lower for word in ['space', 'room', 'location', 'physical']):
            return 'spatial'
        elif any(word in constraint_lower for word in ['people', 'team', 'social', 'relationship']):
            return 'social'
        elif any(word in constraint_lower for word in ['skill', 'knowledge', 'ability', 'expertise']):
            return 'capability'
        else:
            return 'other'

    def _calculate_novelty_score(self, session_id, diversity_mode):
        """
        Calculate novelty bonus for a session
        
        Returns float: 0.0 (stale) to 1.0 (novel)
        """
        if not diversity_mode:
            return 0.0  # No novelty bonus if not in diversity mode
        
        # Check retrieval frequency
        frequency = self.retrieval_frequency.get(session_id, 0)
        
        # Check if in recent retrievals (last 20)
        recent_count = self.last_n_retrievals[-20:].count(session_id)
        
        # Novelty formula:
        # - Fresh session (never retrieved): 1.0
        # - Retrieved 1-3 times: 0.7
        # - Retrieved 4-10 times: 0.4
        # - Retrieved 10+ times: 0.1
        # - In recent 20 retrievals: Additional -0.3 penalty
        
        if frequency == 0:
            novelty = 1.0
        elif frequency <= 3:
            novelty = 0.7
        elif frequency <= 10:
            novelty = 0.4
        else:
            novelty = 0.1
        
        # Recency penalty
        if recent_count > 0:
            novelty -= 0.3 * (recent_count / 5.0)  # Scale penalty by recent appearances
        
        return max(0.0, novelty)  # Don't go negative
    
    def _track_retrieval(self, session_id):
        """Track that a session was retrieved (for novelty calculations)"""
        # Increment frequency counter
        self.retrieval_frequency[session_id] = self.retrieval_frequency.get(session_id, 0) + 1
        
        # Add to recent retrievals (keep last 50)
        self.last_n_retrievals.append(session_id)
        if len(self.last_n_retrievals) > 50:
            self.last_n_retrievals.pop(0)
    
    def _parse_validation_response(self, response):
        """Parse LLM validation response into structured format"""
        # Simple parsing - could be enhanced with regex
        lines = response.split('\n')
        validation_data = {
            'divergence_score': 75,
            'g_score': 75,
            'meta_cognitive_score': 75,
            'coaching_feedback': response,
            'growth_insights': "Analysis based on memory patterns."
        }
        
        # Try to extract numerical scores
        for line in lines:
            if 'divergence score:' in line.lower():
                try:
                    score = int(''.join(filter(str.isdigit, line)))
                    if 0 <= score <= 100:
                        validation_data['divergence_score'] = score
                except:
                    pass
            elif 'g-score:' in line.lower() or 'g score:' in line.lower():
                try:
                    score = int(''.join(filter(str.isdigit, line)))
                    if 0 <= score <= 100:
                        validation_data['g_score'] = score
                except:
                    pass
                    
        return validation_data

class C2ACortexTrainer:
    """Main C2A training system with Cortex integration"""

    def __init__(self, ollama_model="mistral:7b-instruct"):
        self.memory = CortexMemoryEngine(ollama_model=ollama_model)
        self.session_count = self._get_session_count()
        self.ui = TerminalUI()
        self.ollama_model = ollama_model

    def _get_session_count(self):
        """Get total session count from memory"""
        try:
            # Simple count - could query ChromaDB for actual count
            return 1
        except:
            return 1

    def run_training_session(self):
        """Run a complete C2A training session"""
        self.ui.clear_screen()
        self.ui.display_ascii_art()
        print(f"\n🧠 C2A Training Session #{self.session_count}")
        print("Enhanced with Cortex Photographic Memory")
        print("─" * 60)
        
        # Get session data through enhanced UI
        session_data = self._collect_session_data()
        
        # Check for Grandmaster Trial failure
        if session_data is None:
            return None
        
        # Enhanced validation with memory context (pass level for anti-plateau)
        level = session_data.get('estimated_level', 1)
        validation = self.memory.enhanced_validation(
            session_data['description'],
            session_data['problem'],
            session_data['solutions'],
            session_data['final_alchemy'],
            level=level
        )
        
        # Add validation results to session
        session_data.update(validation)
        session_data['session_id'] = self.session_count
        session_data['timestamp'] = datetime.datetime.now().isoformat()
        
        # Store in Cortex memory
        self.memory.store_session(session_data)
        
        # Display results
        self._display_session_results(session_data)
        
        self.session_count += 1
        return session_data

    def _get_mastery_level_and_alchemy_target(self):
        """Get current mastery level and required alchemy count"""
        # Query memory for past sessions to estimate level
        all_sessions = self.memory.retrieve_context("C2A Training Session", n_results=100)
        
        if not all_sessions["documents"][0]:
            # New user - start at level 1
            return 1, 1
            
        # Simple level estimation based on session count and average scores
        session_count = len(all_sessions["documents"][0])
        avg_g_score = sum(meta.get('g_score', 0) for meta in all_sessions["metadatas"][0]) / max(session_count, 1)
        
        # Basic level calculation (simplified from C2A.py)
        estimated_level = max(1, min(100, int((session_count * 0.5) + (avg_g_score / 10))))
        alchemy_target = max(1, min(10, (estimated_level // 10) + 1))
        
        return estimated_level, alchemy_target
    
    def _is_too_similar(self, new_input, existing_alchemies, threshold=0.7):
        """Check if new input is too similar to existing alchemies using Levenshtein-style comparison"""
        if not new_input or not existing_alchemies:
            return False
        
        new_lower = new_input.lower().strip()
        new_words = set(new_lower.split())
        
        for existing in existing_alchemies:
            existing_lower = existing.lower().strip()
            existing_words = set(existing_lower.split())
            
            # Exact match
            if new_lower == existing_lower:
                return True
            
            # Jaccard similarity (word overlap)
            if len(new_words) > 0 and len(existing_words) > 0:
                intersection = new_words.intersection(existing_words)
                union = new_words.union(existing_words)
                similarity = len(intersection) / len(union)
                
                if similarity > threshold:
                    return True
            
            # Simple substring check (catches minor variations)
            if len(new_lower) > 20 and len(existing_lower) > 20:
                if new_lower in existing_lower or existing_lower in new_lower:
                    return True
        
        return False

    def _collect_session_data(self):
        """Collect session data through enhanced UI with TIMERS"""
        session_data = {}
        
        # Get current level and alchemy target
        level, alchemy_target = self._get_mastery_level_and_alchemy_target()
        
        # Display level info
        self.ui.display_info_box(
            f"🎯 Current Level: {level}",
            f"Challenge: Generate {alchemy_target} distinct alchemy transmutations\nRULE: 90 Seconds per Alchemy."
        )
        
        # Challenge description (Untimed)
        session_data['description'] = self.ui.get_chat_input(
            "What are you optimize or synthesize?"
        )
        
        # Core constraint (Untimed)
        session_data['problem'] = self.ui.get_chat_input(
            "What is the core constraint you're facing?"
        )
        
        # ═══════════════════════════════════════════════════════════════
        # GRANDMASTER TRIAL (Level 90+)
        # ═══════════════════════════════════════════════════════════════
        if level >= 90:
            print("\n" + "=" * 62)
            print("⚡ GRANDMASTER TRIAL ACTIVATED ⚡")
            print("=" * 62)
            print("Condition: 10 DISTINCT Transmutations | Time Limit: 90 SECONDS TOTAL")
            print("Any repeated/similar answers will be REJECTED.")
            print("Failure = Immediate Exit. No validation.")
            print("=" * 62)
            input("\nPress Enter to BEGIN GRANDMASTER TRIAL...")
            
            alchemies = []
            start_time = time.time()
            rejected_count = 0
            
            while len(alchemies) < 10:
                remaining = int(90 - (time.time() - start_time))
                
                # Time expired - FAILURE
                if remaining <= 0:
                    print("\n" + "=" * 62)
                    print("💀 FAILURE: Time Expired.")
                    print(f"You generated {len(alchemies)}/10 transmutations.")
                    print("The Grandmaster Trial requires faster cognitive velocity.")
                    print("=" * 62)
                    input("\nPress Enter to return to menu...")
                    return None  # Signal failure
                
                # Get input with remaining time display
                print(f"\n⏱️  Alchemy #{len(alchemies)+1}/10 | ⚠️  {remaining}s remaining")
                print("-" * 60)
                user_input = input("> ").strip()
                
                # Check if too similar to previous answers
                if self._is_too_similar(user_input, alchemies):
                    rejected_count += 1
                    print(f"❌ REJECTED: Too similar to previous answer. ({rejected_count} rejections)")
                    if rejected_count >= 5:
                        print("\n💀 FAILURE: Too many rejected answers. Insufficient divergence.")
                        input("\nPress Enter to return to menu...")
                        return None
                else:
                    alchemies.append(user_input)
                    print(f"✅ Accepted ({len(alchemies)}/10)")
            
            # SUCCESS - They survived the speed test
            elapsed = time.time() - start_time
            print("\n" + "=" * 62)
            print(f"⚔️  GRANDMASTER TRIAL COMPLETE: {elapsed:.1f}s")
            print("⏱️  Time Stop. Validating Quality...")
            print("=" * 62)
            
            session_data['solutions'] = alchemies
            session_data['alchemy_target'] = 10
            session_data['estimated_level'] = level
            session_data['grandmaster_trial'] = True
            session_data['trial_time'] = elapsed
            
        # ═══════════════════════════════════════════════════════════════
        # NORMAL MODE (Level < 90)
        # ═══════════════════════════════════════════════════════════════
        else:
            alchemies = []
            total_time_penalty = 0
            
            print(f"\n⚡ ENTERING HIGH VELOCITY STATE ⚡")
            print("You have 90 seconds for each transmutation.")
            input("Press Enter to START TIMER...")

            for i in range(1, alchemy_target + 1):
                prompt = f"Generate Alchemy #{i} - How could this constraint become an advantage?"
                
                # 90 Second Hard Constraint
                response, duration = TimedInput.get_input_with_timeout(prompt, timeout=90)
                
                if duration > 90:
                    overtime = duration - 90
                    penalty = int(overtime // 30) + 1
                    total_time_penalty += penalty
                    print(f"\n⚠️  Too Slow! (+{overtime}s). Level Penalty: -{penalty}")
                else:
                    print(f"\n✅  Speed Bonus! ({duration}s)")
                
                alchemies.append(response)

            session_data['solutions'] = alchemies
            session_data['alchemy_target'] = alchemy_target
            # Apply level penalty for slowness
            session_data['estimated_level'] = max(1, level - total_time_penalty)
            session_data['grandmaster_trial'] = False
        
        # If multiple alchemies, let user select best one
        if len(alchemies) > 1:
            self.ui.display_info_box(
                "Your Generated Alchemies",
                '\n'.join(f"{i+1}. {alchemy}" for i, alchemy in enumerate(alchemies))
            )
            selection = self.ui.get_chat_input(
                f"Which alchemy best transforms the constraint? (1-{len(alchemies)} or describe your synthesis)",
                multiline=False
            )
            try:
                selection_num = int(selection)
                if 1 <= selection_num <= len(alchemies):
                    session_data['final_alchemy'] = alchemies[selection_num - 1]
                else:
                    session_data['final_alchemy'] = alchemies[0]
            except ValueError:
                session_data['final_alchemy'] = selection
        else:
            session_data['final_alchemy'] = alchemies[0]
            
        # Meta-reflection (Untimed)
        session_data['meta_reflection'] = self.ui.get_chat_input(
            "Meta-cognitive reflection: How did your thinking process evolve during this session?"
        )
        
        return session_data

    def _display_session_results(self, session_data):
        """Display session results with memory insights"""
        self.ui.clear_screen()
        
        # Grandmaster Trial Badge
        if session_data.get('grandmaster_trial', False):
            print("\n" + "=" * 62)
            print("⚔️  GRANDMASTER TRIAL COMPLETED ⚔️")
            print(f"10 Distinct Transmutations in {session_data.get('trial_time', 0):.1f}s")
            print("=" * 62 + "\n")
        
        # Display scores
        scores_text = f"""
G-Score: {session_data['g_score']}/100
Divergence Score: {session_data['divergence_score']}/100
Meta-Cognitive Score: {session_data.get('meta_cognitive_score', 'N/A')}/100
Level Penalty (Time): -{session_data.get('time_penalty', 0)} (Implicit)
""".strip()
        
        self.ui.display_info_box("🎯 Session Scores", scores_text)
        
        # Display coaching feedback
        self.ui.display_info_box("🧠 Memory-Enhanced Coaching", session_data['coaching_feedback'])
        
        # Display growth insights
        growth_insights = session_data.get('growth_insights', 'Building your constraint-thinking profile...')
        self.ui.display_info_box("📈 Growth Patterns", growth_insights)
        
        input("\nPress Enter to continue...")

    def query_memory(self):
        """Interactive memory querying"""
        self.ui.clear_screen()
        print("🔍 Query Your Constraint-Solving Memory")
        print("─" * 40)
        
        query = self.ui.get_chat_input("What would you like to explore from your training history?")
        results = self.memory.retrieve_context(query, n_results=10)
        
        if results["documents"][0]:
            response_text = "Found relevant sessions:\\n\\n"
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                response_text += f"Session {meta['session_id']} (G-Score: {meta['g_score']})\\n"
                
                # Extract key lines
                lines = doc.split('\\n')
                constraint_line = next((line for line in lines if 'Core Constraint:' in line), '')
                alchemy_line = next((line for line in lines if 'Selected Alchemy:' in line), '')
                response_text += f"{constraint_line}\\n{alchemy_line}\\n\\n"
        else:
            response_text = "No relevant sessions found. Keep training to build your memory!"
            
        self.ui.display_info_box("Memory Search Results", response_text)
        input("Press Enter to continue...")

    def show_profile(self):
        """Display user profile with level, stats, and progress"""
        self.ui.clear_screen()
        print("=" * 62)
        print("👤 YOUR PROFILE")
        print("=" * 62)
        
        level, alchemy_target = self._get_mastery_level_and_alchemy_target()
        
        print(f"\nMastery Level: {level}")
        print(f"Current Challenge: {alchemy_target} Alchemies per Session")
        print(f"Total Sessions: {self.session_count}")
        
        input("\nPress Enter to return to menu...")

    def _scenario_training(self):
        """Run scenario-based training (Constraint Game)"""
        if not SCENARIOS_AVAILABLE:
            print("\n⚠️ Scenario mode not available. constraint_scenarios.py not found.")
            input("Press Enter to continue...")
            return
        
        self.ui.clear_screen()
        print("=" * 62)
        print("🎮 CONSTRAINT GAME - Historical Scenario Training")
        print("=" * 62)
        
        level, _ = self._get_mastery_level_and_alchemy_target()
        
        # Get scenario for current level (pass session_count to prevent repeats)
        scenario = get_scenario(level, session_count=self.session_count)
        
        print(f"\n📜 Scenario #{min(level, 20)}: {scenario['title']}")
        print(f"📅 Year: {scenario['year']} | Domain: {scenario['domain']}")
        print(f"🎯 Difficulty: {scenario['difficulty']}")
        print("=" * 62)
        
        # Display situation
        self.ui.display_info_box("THE SITUATION", scenario['situation'])
        
        # For levels 11+, user must identify constraint first
        if scenario.get('explicit_constraint') is None:
            print(f"\n💡 Hint: {scenario['hint']}")
            print("\n🔍 STEP 1: IDENTIFY THE CONSTRAINT")
            print("What is the PRIMARY constraint in this situation?")
            user_constraint = input("> ").strip()
            
            # Validate constraint identification
            is_correct, feedback = validate_constraint_identification(user_constraint, scenario)
            print(f"\n{feedback}")
            
            if not is_correct:
                print("\nLearning moment: Constraint recognition is the foundation of C2A.")
                print(f"Historical context: {scenario['historical_outcome'][:200]}...")
                input("\nPress Enter to continue...")
                return
        else:
            print(f"\n🔒 THE CONSTRAINT: {scenario['explicit_constraint']}")
        
        # Generate transmutations
        print(f"\n⚗️ STEP 2: TRANSMUTE THE CONSTRAINT")
        print(f"Generate {scenario['target_transmutations']} transmutation(s)")
        print(f"💡 Hint: {scenario['hint']}")
        print("\n90-second timer per transmutation...\n")
        
        transmutations = []
        total_score = 0
        feedbacks = []
        
        for i in range(scenario['target_transmutations']):
            prompt = f"Transmutation #{i+1}: How do you turn this constraint into an advantage?"
            response, duration = TimedInput.get_input_with_timeout(prompt, timeout=90)
            
            if response.strip():
                transmutations.append(response)
                
                # Score the transmutation (now returns score and feedback)
                trans_score, feedback = score_transmutation(response, scenario)
                total_score += trans_score
                feedbacks.append(feedback)
                
                if duration <= 90:
                    print(f"✅ Time: {duration:.1f}s | Score: {trans_score}/100")
                    print(f"   {feedback['breakdown']}")
                    if feedback['patterns_found']:
                        print(f"   Patterns: {', '.join(feedback['patterns_found'])}")
                else:
                    print(f"⏰ Overtime: {duration:.1f}s | Score: {trans_score}/100")
                    print(f"   {feedback['breakdown']}")
                    if feedback['patterns_found']:
                        print(f"   Patterns: {', '.join(feedback['patterns_found'])}")
        
        # Calculate final score
        avg_score = total_score / max(len(transmutations), 1)
        
        # Display historical outcome
        print("\n" + "=" * 62)
        print("📚 HISTORICAL OUTCOME")
        print("=" * 62)
        self.ui.display_info_box("What Actually Happened", scenario['historical_outcome'])
        
        # Display constraint logic pattern (the learning!)
        if scenario.get('constraint_logic_pattern'):
            print("\n" + "=" * 62)
            print("🧠 CONSTRAINT LOGIC PATTERN (The Transferable Lesson)")
            print("=" * 62)
            self.ui.display_info_box("Pattern to Learn", scenario['constraint_logic_pattern'])
        
        # Display results
        print("\n" + "=" * 62)
        print("📊 YOUR RESULTS")
        print("=" * 62)
        print(f"Transmutations Generated: {len(transmutations)}")
        print(f"Average Score: {avg_score:.1f}/100")
        
        if avg_score >= 80:
            print("🏆 EXCELLENT: Your transmutations align with historical solutions!")
        elif avg_score >= 60:
            print("✅ GOOD: You're thinking in the right direction.")
        else:
            print("📈 LEARNING: Study the historical outcome for patterns.")
        
        # Store as session in memory
        session_data = {
            'description': f"Scenario: {scenario['title']}",
            'problem': scenario.get('explicit_constraint') or scenario.get('correct_constraint', 'Hidden constraint'),
            'solutions': transmutations,
            'final_alchemy': transmutations[0] if transmutations else "",
            'g_score': int(avg_score),
            'divergence_score': int(avg_score),
            'meta_reflection': f"Historical scenario training: {scenario['domain']}",
            'session_id': self.session_count,
            'timestamp': datetime.datetime.now().isoformat(),
            'training_mode': 'scenario'
        }
        
        self.memory.store_session(session_data)
        self.session_count += 1
        
        input("\n\nPress Enter to return to menu...")
    
    def _personal_training(self):
        """Run personal constraint training (original mode)"""
        return self.run_training_session()

    def main_menu(self):
        """Display main menu with level-gated modes"""
        while True:
            self.ui.clear_screen()
            self.ui.display_ascii_art()
            
            level, alchemy_target = self._get_mastery_level_and_alchemy_target()
            
            # Display status
            print(f"\n{'='*62}")
            print(f"📊 Your Level: {level}/100 | Challenge: {alchemy_target} Transmutations")
            print(f"{'='*62}")
            
            # Determine training mode recommendation
            if level <= 20:
                recommendation = "🎮 Scenario Mode (Building pattern library)"
            elif level <= 50:
                recommendation = "💭 Personal Mode (Applying to your life)"
            else:
                recommendation = "🔀 Mixed Mode (Maintenance + Depth)"
            
            print(f"\n💡 Recommended: {recommendation}")
            print(f"{'='*62}\n")
            
            # Menu options
            print("[1] 🎯 Auto-Training (System chooses optimal mode)")
            
            if SCENARIOS_AVAILABLE:
                print("[2] 🎮 Constraint Game (Historical Scenarios)")
            else:
                print("[2] 🎮 Constraint Game (⚠️ Unavailable)")
            
            if level >= 21:
                print("[3] 💭 Personal Mode (Your Life Constraints)")
            else:
                print("[3] 💭 Personal Mode (🔒 Unlocks at Level 21)")
            
            print("[4] 🔍 Query Memory")
            print("[5] 👤 View Profile")
            print("[6] ❌ Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                # Auto-optimal mode based on level
                if level <= 20:
                    print("\n🎮 Auto-selecting: Scenario Mode (Levels 1-20)")
                    input("Press Enter to begin...")
                    self._scenario_training()
                elif level <= 50:
                    print("\n💭 Auto-selecting: Personal Mode (Levels 21-50)")
                    input("Press Enter to begin...")
                    self._personal_training()
                else:
                    print("\n🔀 Mixed Mode: Choose your focus")
                    print("[1] Scenario (Maintenance)")
                    print("[2] Personal (Depth)")
                    sub_choice = input("Choice: ").strip()
                    if sub_choice == '1':
                        self._scenario_training()
                    else:
                        self._personal_training()
                        
            elif choice == '2':
                if SCENARIOS_AVAILABLE:
                    self._scenario_training()
                else:
                    print("\n⚠️ Scenario mode unavailable.")
                    input("Press Enter...")
                    
            elif choice == '3':
                if level >= 21:
                    self._personal_training()
                else:
                    print("\n🔒 Personal Mode unlocks at Level 21")
                    print("Complete 20+ scenario training sessions to unlock.")
                    input("Press Enter...")
                    
            elif choice == '4':
                self.query_memory()
            elif choice == '5':
                self.show_profile()
            elif choice == '6':
                print("\n✨ Training complete. Remember: The constraint IS the way.")
                sys.exit(0)
            else:
                input("Invalid option. Press Enter...")

def select_ollama_model():
    """Interactive model selection"""
    print("\nSelect Ollama Model:")
    print("1. mistral:7b-instruct (Recommended - Fast)")
    print("2. llama3:8b (Balanced)")
    print("3. gemma:7b (Google)")
    print("4. Custom (Enter model name)")
    
    choice = input("\nSelect (1-4): ").strip()
    
    if choice == '1': return "mistral:7b-instruct"
    if choice == '2': return "llama3:8b"
    if choice == '3': return "gemma:7b"
    if choice == '4': return input("Enter model name: ").strip()
    return "mistral:7b-instruct"

def main():
    try:
        # Check for required directories
        if not os.path.exists("cortex"):
            # Create dummy config if cortex dir missing (for standalone use)
            pass
            
        # Model selection at startup
        selected_model = select_ollama_model()
        
        trainer = C2ACortexTrainer(ollama_model=selected_model)
        trainer.main_menu()
        
    except KeyboardInterrupt:
        print("\n\n🧠 Session interrupted. Keep training!")
    except Exception as e:
        print(f"\nError: {e}")
        print("Please check your setup and try again.")

if __name__ == "__main__":
    main()
