#!/usr/bin/env python3
"""
RLM (Recursive Language Model) Engine for C2A

This implements the recursive processing strategy from the RLM paper:
- Treat massive context as external data (Python REPL environment)
- LLM writes code to peek, decompose, process recursively, and aggregate
- Enables processing 10M+ tokens of constraint history without context rot

Philosophy: "The model becomes its own architect, decomposing complexity recursively."
"""

import json
import ollama
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from pathlib import Path
import ast
import traceback


@dataclass
class RLMQuery:
    """A query to process via recursive language modeling"""
    query: str
    context_size: int  # Estimated tokens in context
    max_depth: int = 3  # Maximum recursion depth
    user_profile: Optional[Dict] = None


@dataclass
class RLMResult:
    """Result from RLM processing"""
    answer: str
    code_executed: List[str]  # Code snippets that were executed
    recursive_calls: int  # How many recursive decompositions
    tokens_processed: int  # Estimated tokens processed
    insights: List[str]  # Discovered insights at each level


class SafeREPL:
    """Safe Python REPL environment with access to C2A data"""
    
    def __init__(self, memory_db, user_profile: Dict):
        self.memory_db = memory_db
        self.user_profile = user_profile
        self.execution_history = []
        
        # Build safe namespace with C2A data access
        self.namespace = {
            # Data access functions
            'get_all_sessions': self._get_all_sessions,
            'get_sessions_by_archetype': self._get_sessions_by_archetype,
            'get_recent_sessions': self._get_recent_sessions,
            'get_high_scoring_sessions': self._get_high_scoring_sessions,
            'search_sessions': self._search_sessions,
            'get_user_profile': lambda: self.user_profile,
            
            # Analysis utilities
            'calculate_average_score': self._calculate_average_score,
            'find_patterns': self._find_patterns,
            'group_by': self._group_by,
            'filter_sessions': self._filter_sessions,
            
            # Safe builtins
            'len': len,
            'sum': sum,
            'min': min,
            'max': max,
            'sorted': sorted,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'enumerate': enumerate,
            'zip': zip,
            'range': range,
            
            # Output
            'print': print,
            'results': []  # For storing results
        }
    
    def execute(self, code: str) -> Any:
        """
        Execute code in safe environment
        
        Returns:
            Result of execution or error message
        """
        try:
            # Validate code safety first
            self._validate_code_safety(code)
            
            # Execute
            exec(code, self.namespace)
            
            # Store in history
            self.execution_history.append(code)
            
            # Return results if any were added
            results = self.namespace.get('results', [])
            if results:
                return results[-1] if len(results) == 1 else results
            
            return None
            
        except Exception as e:
            error_msg = f"Execution error: {str(e)}\n{traceback.format_exc()}"
            return error_msg
    
    def _validate_code_safety(self, code: str):
        """Validate that code is safe to execute"""
        
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")
        
        # Check for dangerous operations
        dangerous_patterns = [
            'import os',
            'import sys',
            'import subprocess',
            '__import__',
            'eval(',
            'exec(',
            'compile(',
            'open(',
            'file(',
            'input(',
            'raw_input(',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                raise ValueError(f"Unsafe operation detected: {pattern}")
        
        # Check AST for dangerous nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                # Only allow safe imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in ['json', 're', 'math', 'statistics']:
                            raise ValueError(f"Import not allowed: {alias.name}")
    
    # Data access methods
    
    def _get_all_sessions(self) -> List[Dict]:
        """Get all training sessions"""
        try:
            results = self.memory_db.collection.get(
                include=["documents", "metadatas"]
            )
            
            sessions = []
            for doc, meta in zip(results['documents'], results['metadatas']):
                sessions.append({
                    'document': doc,
                    'metadata': meta
                })
            
            return sessions
        except Exception as e:
            return []
    
    def _get_sessions_by_archetype(self, archetype: str) -> List[Dict]:
        """Get sessions filtered by archetype"""
        all_sessions = self._get_all_sessions()
        return [s for s in all_sessions if s['metadata'].get('constraint_type') == archetype]
    
    def _get_recent_sessions(self, n: int = 10) -> List[Dict]:
        """Get N most recent sessions"""
        all_sessions = self._get_all_sessions()
        # Sort by timestamp if available
        sorted_sessions = sorted(
            all_sessions,
            key=lambda s: s['metadata'].get('timestamp', ''),
            reverse=True
        )
        return sorted_sessions[:n]
    
    def _get_high_scoring_sessions(self, min_score: int = 80) -> List[Dict]:
        """Get sessions with G-score above threshold"""
        all_sessions = self._get_all_sessions()
        return [s for s in all_sessions if s['metadata'].get('g_score', 0) >= min_score]
    
    def _search_sessions(self, query: str, n_results: int = 10) -> List[Dict]:
        """Search sessions by semantic similarity"""
        try:
            results = self.memory_db.retrieve_context(query, n_results=n_results)
            
            sessions = []
            if results['documents'][0]:
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    sessions.append({
                        'document': doc,
                        'metadata': meta
                    })
            
            return sessions
        except Exception as e:
            return []
    
    # Analysis utilities
    
    def _calculate_average_score(self, sessions: List[Dict], score_key: str = 'g_score') -> float:
        """Calculate average score across sessions"""
        scores = [s['metadata'].get(score_key, 0) for s in sessions if score_key in s['metadata']]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _find_patterns(self, sessions: List[Dict]) -> Dict[str, int]:
        """Find common patterns in sessions"""
        patterns = {}
        for session in sessions:
            doc = session['document'].lower()
            # Simple pattern extraction - could be enhanced
            if 'time' in doc or 'deadline' in doc:
                patterns['temporal'] = patterns.get('temporal', 0) + 1
            if 'resource' in doc or 'budget' in doc:
                patterns['resource'] = patterns.get('resource', 0) + 1
            if 'information' in doc or 'knowledge' in doc:
                patterns['information'] = patterns.get('information', 0) + 1
        
        return patterns
    
    def _group_by(self, sessions: List[Dict], key: str) -> Dict[Any, List[Dict]]:
        """Group sessions by metadata key"""
        groups = {}
        for session in sessions:
            value = session['metadata'].get(key, 'unknown')
            if value not in groups:
                groups[value] = []
            groups[value].append(session)
        
        return groups
    
    def _filter_sessions(self, sessions: List[Dict], predicate: Callable) -> List[Dict]:
        """Filter sessions by predicate function"""
        return [s for s in sessions if predicate(s)]


class RLMEngine:
    """Recursive Language Model engine for processing massive contexts"""
    
    def __init__(self, model: str = "qwen2.5:32b", memory_db=None, use_code_generation: bool = False):
        self.model = model
        self.memory_db = memory_db
        self.query_history = []
        self.use_code_generation = use_code_generation  # Set to False for your hardware
    
    def process_query(self, query: RLMQuery) -> RLMResult:
        """
        Process a query using recursive decomposition OR simplified analysis
        
        If use_code_generation=False, uses direct LLM analysis instead of code generation.
        This works on mid-range hardware (12GB VRAM).
        """
        
        if not self.use_code_generation:
            # Simplified approach - no code generation needed
            return self._process_query_simplified(query)
        
        # Original RLM approach with code generation (requires stronger model)
        # Initialize REPL with data access
        repl = SafeREPL(self.memory_db, query.user_profile or {})
        
        # Step 1: Generate exploration code
        exploration_code = self._generate_exploration_code(query, depth=0)
        
        # Execute and track
        code_executed = []
        insights = []
        recursive_calls = 0
        
        # Execute exploration
        result = repl.execute(exploration_code)
        code_executed.append(exploration_code)
        
        # Step 2: Generate decomposition if context is large
        if query.context_size > 10000 and recursive_calls < query.max_depth:
            decomposition_code = self._generate_decomposition_code(query, result)
            decomp_result = repl.execute(decomposition_code)
            code_executed.append(decomposition_code)
            recursive_calls += 1
            
            # Step 3: Generate aggregation code
            aggregation_code = self._generate_aggregation_code(query, decomp_result)
            final_result = repl.execute(aggregation_code)
            code_executed.append(aggregation_code)
        else:
            final_result = result
        
        # Step 4: Generate natural language answer
        answer = self._synthesize_answer(query, final_result, repl.execution_history)
        
        return RLMResult(
            answer=answer,
            code_executed=code_executed,
            recursive_calls=recursive_calls,
            tokens_processed=query.context_size,
            insights=insights
        )
    
    def _process_query_simplified(self, query: RLMQuery) -> RLMResult:
        """
        Simplified analysis for mid-range hardware (RTX 3060, 12GB)
        
        Instead of generating code, we:
        1. Retrieve relevant data chunks directly
        2. Analyze with focused prompts
        3. Synthesize insights
        
        This is less powerful but works on your hardware!
        """
        
        # Get data directly from memory
        repl = SafeREPL(self.memory_db, query.user_profile or {})
        
        # Retrieve relevant sessions (up to 50 for analysis)
        all_sessions = repl._get_all_sessions()[:50]
        
        # Build focused analysis prompt
        sessions_summary = self._summarize_sessions(all_sessions[:20])
        
        analysis_prompt = f"""You are analyzing a user's C2A training history.

USER QUERY: {query.query}

RECENT SESSIONS (sample):
{sessions_summary}

TASK: Provide insights based on this data. Be specific and reference session patterns.

Analysis:
"""
        
        # Get LLM analysis
        answer = self._query_llm(analysis_prompt)
        
        return RLMResult(
            answer=answer,
            code_executed=["# Simplified analysis - no code execution"],
            recursive_calls=0,
            tokens_processed=len(sessions_summary),
            insights=[]
        )
    
    def _summarize_sessions(self, sessions: List[Dict]) -> str:
        """Create compact summary of sessions"""
        summary = []
        for session in sessions:
            meta = session.get('metadata', {})
            summary.append(
                f"Session {meta.get('session_id', '?')}: "
                f"Archetype={meta.get('constraint_type', '?')}, "
                f"Score={meta.get('g_score', '?')}"
            )
        return '\n'.join(summary[:20])  # Limit to 20 for context
    
    def _generate_exploration_code(self, query: RLMQuery, depth: int = 0) -> str:
        """Generate code to explore the data"""
        
        prompt = f"""You are an expert Python programmer with access to a C2A training database.

USER QUERY: "{query.query}"

Available functions in your environment:
- get_all_sessions() -> List[Dict]: Get all training sessions
- get_sessions_by_archetype(archetype: str) -> List[Dict]: Filter by constraint type
- get_recent_sessions(n: int) -> List[Dict]: Get N most recent sessions
- get_high_scoring_sessions(min_score: int) -> List[Dict]: Filter by score
- search_sessions(query: str, n_results: int) -> List[Dict]: Semantic search
- get_user_profile() -> Dict: Get user profile data

Analysis utilities:
- calculate_average_score(sessions, score_key='g_score') -> float
- find_patterns(sessions) -> Dict[str, int]
- group_by(sessions, key) -> Dict[Any, List[Dict]]

Session structure:
- session['document']: Full text description
- session['metadata']: Dict with 'g_score', 'constraint_type', 'timestamp', etc.

TASK: Write Python code to answer the query. Store the final answer in results list.

CONSTRAINTS:
- Be efficient: Use filtering before iterating
- Be specific: Focus on what the query asks
- Be clear: Comment your code
- Use results.append(your_answer) to return data

Generate ONLY executable Python code (no markdown, no explanations):
"""
        
        response = self._query_llm(prompt)
        
        # Extract code from response
        code = self._extract_code(response)
        
        return code
    
    def _generate_decomposition_code(self, query: RLMQuery, initial_result: Any) -> str:
        """Generate code to decompose the problem"""
        
        prompt = f"""You have preliminary results from a large dataset analysis.

ORIGINAL QUERY: "{query.query}"
PRELIMINARY RESULTS: {str(initial_result)[:500]}

The dataset is too large to process at once. Generate code to:
1. Decompose into meaningful chunks (by archetype, time period, score range, etc.)
2. Process each chunk separately
3. Store chunk results in results list

Generate ONLY executable Python code:
"""
        
        response = self._query_llm(prompt)
        code = self._extract_code(response)
        
        return code
    
    def _generate_aggregation_code(self, query: RLMQuery, chunk_results: Any) -> str:
        """Generate code to aggregate chunk results"""
        
        prompt = f"""You have processed multiple chunks of data.

ORIGINAL QUERY: "{query.query}"
CHUNK RESULTS: {str(chunk_results)[:500]}

Generate code to aggregate these results into a final answer.
Store the aggregated result in results list.

Generate ONLY executable Python code:
"""
        
        response = self._query_llm(prompt)
        code = self._extract_code(response)
        
        return code
    
    def _synthesize_answer(self, query: RLMQuery, final_result: Any, execution_history: List[str]) -> str:
        """Synthesize natural language answer from results"""
        
        prompt = f"""You analyzed a C2A training database using Python code.

ORIGINAL QUERY: "{query.query}"
ANALYSIS RESULTS: {str(final_result)}

CODE EXECUTED:
{chr(10).join('- ' + code[:100] + '...' for code in execution_history)}

Generate a clear, insightful answer to the user's query based on these results.
Be specific, reference the data, and provide actionable insights.

Answer:
"""
        
        response = self._query_llm(prompt)
        
        return response.strip()
    
    def _query_llm(self, prompt: str) -> str:
        """Query LLM with error handling"""
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are an expert Python programmer and data analyst specializing in cognitive training data."
                }, {
                    "role": "user",
                    "content": prompt
                }]
            )
            return response["message"]["content"]
        except Exception as e:
            print(f"LLM Error: {e}")
            return "# Error generating code"
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response"""
        
        # Try to find code blocks
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()
        
        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()
        
        # No code blocks, assume entire response is code
        lines = response.split('\n')
        code_lines = [line for line in lines if not line.strip().startswith('#') or line.strip().startswith('# ')]
        
        return '\n'.join(lines).strip()


class RLMConstraintAnalyzer:
    """High-level RLM interface for constraint analysis"""
    
    def __init__(self, memory_db, model: str = "qwen2.5:32b", use_simplified: bool = True):
        # use_simplified=True: Works on 12GB VRAM (RTX 3060)
        # use_simplified=False: Needs 40GB+ VRAM (Full RLM with code generation)
        self.engine = RLMEngine(
            model=model, 
            memory_db=memory_db,
            use_code_generation=(not use_simplified)
        )
        self.memory_db = memory_db
    
    def analyze_plateau_patterns(self, user_profile: Dict) -> str:
        """Use RLM to analyze plateau patterns across entire history"""
        
        query = RLMQuery(
            query="Identify plateau patterns: sessions where the user's scores stopped improving or showed repeated constraint-thinking patterns. What specific patterns emerge?",
            context_size=100000,  # Assume large history
            max_depth=2,
            user_profile=user_profile
        )
        
        result = self.engine.process_query(query)
        return result.answer
    
    def find_archetype_weaknesses(self, user_profile: Dict) -> str:
        """Identify which constraint archetypes the user struggles with"""
        
        query = RLMQuery(
            query="Compare user's performance across all five constraint archetypes. Which archetype has the lowest average score? Show specific examples of where they struggled.",
            context_size=50000,
            max_depth=2,
            user_profile=user_profile
        )
        
        result = self.engine.process_query(query)
        return result.answer
    
    def discover_breakthrough_moments(self, user_profile: Dict) -> str:
        """Find sessions where the user had significant breakthroughs"""
        
        query = RLMQuery(
            query="Find breakthrough moments: sessions where the user's score significantly exceeded their recent average, or where they demonstrated a new constraint-thinking pattern. What triggered these breakthroughs?",
            context_size=75000,
            max_depth=2,
            user_profile=user_profile
        )
        
        result = self.engine.process_query(query)
        return result.answer
    
    def generate_personalized_training_plan(self, user_profile: Dict) -> str:
        """Generate a training plan based on comprehensive history analysis"""
        
        query = RLMQuery(
            query="Analyze the user's complete training history to create a personalized training plan. Consider: weak archetypes, plateau patterns, successful strategies, and optimal challenge level. Provide specific, actionable recommendations.",
            context_size=150000,
            max_depth=3,
            user_profile=user_profile
        )
        
        result = self.engine.process_query(query)
        return result.answer
    
    def compare_to_cohort(self, user_profile: Dict, level_range: Tuple[int, int]) -> str:
        """Compare user's performance to others in their level range"""
        
        query = RLMQuery(
            query=f"Compare this user's performance to others in level range {level_range[0]}-{level_range[1]}. How do their scores, patterns, and growth trajectories compare?",
            context_size=200000,
            max_depth=3,
            user_profile=user_profile
        )
        
        result = self.engine.process_query(query)
        return result.answer
    
    def analyze_detection_accuracy(self, user_profile: Dict) -> Dict:
        """
        Diagnose constraint detection failures - THE KEY TO INSTALLING C2A ON ANY BRAIN
        
        This analyzes:
        1. Overall detection accuracy (correct vs incorrect identifications)
        2. Archetype confusion patterns (which archetypes get confused for which)
        3. Common failure modes (symptom vs root, secondary vs primary, etc.)
        4. Accuracy by scenario complexity
        5. Improvement trajectory over time
        
        Returns a comprehensive diagnostic with specific recommendations.
        """
        
        query = RLMQuery(
            query="""Analyze the user's constraint DETECTION accuracy in detail:

1. OVERALL DETECTION METRICS:
   - Total detection attempts (sessions where detection_required=True)
   - Success rate (detection_success=True / total attempts)
   - Average partial_credit score on failures
   - Trend over time (improving, plateauing, declining?)

2. ARCHETYPE CONFUSION MATRIX:
   - For each archetype, what percentage correctly identified?
   - When wrong, which archetype did they THINK it was?
   - Pattern: Do they consistently confuse specific pairs?
     e.g., "User confuses Asymmetry for Friction 67% of the time"

3. FAILURE MODE ANALYSIS:
   - Count by confusion_type:
     * 'no_archetype_identified' - Didn't name any archetype
     * 'archetype_confusion:X_for_Y' - Named wrong archetype
     * 'symptom_not_root' - Identified symptom, not root constraint
     * 'secondary_not_primary' - Found a constraint, but not the main one
     * 'general_misidentification' - Other errors
   - Which failure mode is most common?

4. COMPLEXITY ANALYSIS:
   - Detection accuracy at different levels
   - Does accuracy drop as scenarios get harder?
   - At what level did detection start failing?

5. SPECIFIC EXAMPLES:
   - Show 3 worst detection failures with:
     * What they said (detection_user_answer)
     * What it actually was (detection_correct_answer)
     * The archetype confusion if any

6. RECOMMENDATIONS:
   - Which archetype needs the most practice?
   - What specific confusion pattern to address first?
   - Suggested training focus

Format response as structured analysis with clear sections.""",
            context_size=150000,
            max_depth=2,
            user_profile=user_profile
        )
        
        result = self.engine.process_query(query)
        
        # Also compute quick stats directly if simplified mode
        quick_stats = self._compute_detection_stats()
        
        return {
            'analysis': result.answer,
            'quick_stats': quick_stats
        }
    
    def _compute_detection_stats(self) -> Dict:
        """Compute quick detection statistics directly from database"""
        try:
            repl = SafeREPL(self.memory_db, {})
            all_sessions = repl._get_all_sessions()
            
            # Filter to detection-required sessions
            detection_sessions = [
                s for s in all_sessions 
                if s['metadata'].get('detection_required', False)
            ]
            
            if not detection_sessions:
                return {
                    'total_detection_attempts': 0,
                    'message': 'No detection sessions yet (Phase 2+ not reached)'
                }
            
            total = len(detection_sessions)
            successes = sum(1 for s in detection_sessions if s['metadata'].get('detection_success', False))
            
            # Archetype breakdown
            archetype_stats = {}
            confusion_counts = {}
            
            for session in detection_sessions:
                meta = session['metadata']
                correct_arch = meta.get('detection_correct_archetype', 'unknown')
                user_arch = meta.get('detection_user_archetype', 'unknown')
                success = meta.get('detection_success', False)
                
                if correct_arch not in archetype_stats:
                    archetype_stats[correct_arch] = {'total': 0, 'correct': 0}
                
                archetype_stats[correct_arch]['total'] += 1
                if success:
                    archetype_stats[correct_arch]['correct'] += 1
                else:
                    # Track confusion
                    confusion_key = f"{user_arch}_for_{correct_arch}"
                    confusion_counts[confusion_key] = confusion_counts.get(confusion_key, 0) + 1
            
            # Calculate accuracy per archetype
            archetype_accuracy = {
                arch: (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                for arch, stats in archetype_stats.items()
            }
            
            # Find weakest archetype
            weakest = min(archetype_accuracy.items(), key=lambda x: x[1]) if archetype_accuracy else ('none', 0)
            
            # Find most common confusion
            most_confused = max(confusion_counts.items(), key=lambda x: x[1]) if confusion_counts else ('none', 0)
            
            return {
                'total_detection_attempts': total,
                'successful_detections': successes,
                'overall_accuracy': round(successes / total * 100, 1) if total > 0 else 0,
                'archetype_accuracy': archetype_accuracy,
                'weakest_archetype': weakest[0],
                'weakest_archetype_accuracy': round(weakest[1], 1),
                'confusion_counts': confusion_counts,
                'most_common_confusion': most_confused[0],
                'most_common_confusion_count': most_confused[1]
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'message': 'Could not compute detection stats'
            }
    
    def get_detection_training_recommendations(self, user_profile: Dict) -> str:
        """Get specific recommendations for improving detection accuracy"""
        
        query = RLMQuery(
            query="""Based on the user's detection failure patterns, provide SPECIFIC training recommendations:

1. IMMEDIATE FOCUS:
   - Which ONE archetype should they focus on next session?
   - Why this archetype specifically?

2. CONFUSION REMEDIATION:
   - For their most common archetype confusion, explain:
     * The KEY difference between the two archetypes
     * A memorable way to distinguish them
     * Example scenario where the difference is clear

3. DETECTION DRILL:
   - Suggest a "detection-only" exercise:
     * 5 rapid scenarios where they ONLY identify the archetype (no transmutation)
     * Focus on their weak archetype
     * Build pattern recognition before requiring full transmutation

4. SIGNAL EXTRACTION TIPS:
   - Based on their failures, what "signal" do they keep missing?
   - What question should they ask themselves first when scanning a scenario?

Keep recommendations actionable and specific to THIS user's patterns.""",
            context_size=100000,
            max_depth=2,
            user_profile=user_profile
        )
        
        result = self.engine.process_query(query)
        return result.answer


if __name__ == "__main__":
    print("RLM Engine initialized.")
    print("\nCapabilities:")
    print("- Process 10M+ tokens of constraint history")
    print("- Recursive decomposition and analysis")
    print("- Generate code to explore data dynamically")
    print("- Identify patterns across massive context")
    print("\nIntegration with C2A enables:")
    print("  • Deep plateau pattern analysis")
    print("  • Archetype weakness identification")
    print("  • Breakthrough moment discovery")
    print("  • Personalized training plan generation")
    print("  • Cohort comparison analytics")
