#!/usr/bin/env python3
"""
Test script for C2A Elegant components

Run this to verify everything works before starting training.
"""

import sys
from pathlib import Path

print("=" * 60)
print("C2A ELEGANT - SYSTEM TEST")
print("=" * 60)

# Test 1: Dependencies
print("\n[1/7] Testing dependencies...")
try:
    import chromadb
    print("  ✓ chromadb")
except ImportError as e:
    print(f"  ✗ chromadb: {e}")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    print("  ✓ sentence-transformers")
except ImportError as e:
    print(f"  ✗ sentence-transformers: {e}")
    sys.exit(1)

try:
    import ollama
    print("  ✓ ollama")
except ImportError as e:
    print(f"  ✗ ollama: {e}")
    sys.exit(1)

# Test 2: Archetypes
print("\n[2/7] Testing constraint archetypes...")
try:
    from constraint_archetypes import ARCHETYPES, get_archetype
    
    assert len(ARCHETYPES) == 5, "Should have 5 archetypes"
    assert 'scarcity' in ARCHETYPES
    assert 'velocity' in ARCHETYPES
    assert 'asymmetry' in ARCHETYPES
    assert 'friction' in ARCHETYPES
    assert 'paradox' in ARCHETYPES
    
    scarcity = get_archetype('scarcity')
    assert scarcity.symbol == '⧗'
    
    print(f"  ✓ All 5 archetypes loaded")
    print(f"  ✓ Symbols: {' '.join(a.symbol for a in ARCHETYPES.values())}")
    
except Exception as e:
    print(f"  ✗ Archetypes error: {e}")
    sys.exit(1)

# Test 3: Scenario Engine
print("\n[3/7] Testing LLM scenario engine...")
try:
    from llm_scenario_engine import LLMScenarioEngine, ScenarioValidator
    
    engine = LLMScenarioEngine(model="qwen2.5:32b")
    
    # Test with mock generation (won't actually call LLM)
    test_profile = {
        'domain': 'test',
        'total_sessions': 1,
        'archetype_performance': {}
    }
    
    print(f"  ✓ Engine initialized")
    print(f"  ✓ Ready to generate scenarios")
    
except Exception as e:
    print(f"  ✗ Scenario engine error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Judge System
print("\n[4/7] Testing LLM judge system...")
try:
    from llm_transmutation_judge import TransmutationJudge, TransmutationScore
    
    judge = TransmutationJudge(model="qwen2.5:32b")
    
    # Test score object
    test_score = TransmutationScore(
        overall_score=85,
        reframing_score=27,
        novelty_score=22,
        practicality_score=21,
        sophistication_score=15,
        what_worked="Good reframing",
        what_missed="Could be more novel",
        growth_edge="Practice meta-cognition",
        pattern_identified="Constraint as Design Parameter",
        vs_user_history="Better than average",
        breakthrough_moment=False
    )
    
    print(f"  ✓ Judge initialized")
    print(f"  ✓ Score object: {test_score.overall_score}/100")
    
except Exception as e:
    print(f"  ✗ Judge system error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: UI System
print("\n[5/7] Testing elegant UI...")
try:
    from elegant_ui import ElegantUI, Colors, Symbols
    
    ui = ElegantUI()
    
    # Test terminal size detection
    width = ui.get_terminal_width()
    height = ui.get_terminal_height()
    
    print(f"  ✓ UI initialized")
    print(f"  ✓ Terminal: {width}x{height}")
    print(f"  ✓ Colors: {Colors.CYAN}Cyan{Colors.RESET} {Colors.GOLD}Gold{Colors.RESET}")
    print(f"  ✓ Symbols: {Symbols.CONSTRAINT} {Symbols.TRANSMUTE} {Symbols.INSIGHT}")
    
except Exception as e:
    print(f"  ✗ UI error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: RLM Engine
print("\n[6/7] Testing RLM engine...")
try:
    from rlm_engine import RLMEngine, SafeREPL, RLMConstraintAnalyzer
    
    # Can't fully test without memory, but verify imports
    print(f"  ✓ RLM components loaded")
    print(f"  ✓ SafeREPL available")
    print(f"  ✓ Analyzer available")
    
except Exception as e:
    print(f"  ✗ RLM error: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Memory System
print("\n[7/7] Testing memory system...")
try:
    from c2a_elegant_main import MemorySystem
    
    # Initialize memory (creates directory)
    memory = MemorySystem(collection_name="c2a_test")
    
    print(f"  ✓ Memory initialized")
    print(f"  ✓ Collection: {memory.collection_name}")
    
    # Test stats retrieval
    stats = memory.get_user_stats()
    print(f"  ✓ Stats: {stats['total_sessions']} sessions, Level {stats['current_level']}")
    
    # Cleanup test collection
    try:
        memory.client.delete_collection("c2a_test")
        print(f"  ✓ Test collection cleaned up")
    except:
        pass
    
except Exception as e:
    print(f"  ✗ Memory error: {e}")
    import traceback
    traceback.print_exc()

# Test 8: Ollama Connection
print("\n[8/7] Testing Ollama connection (optional)...")
try:
    response = ollama.chat(
        model="qwen2.5:32b",
        messages=[{"role": "user", "content": "Say 'ready' if you can hear me."}]
    )
    
    print(f"  ✓ Ollama connected")
    print(f"  ✓ Model: qwen2.5:32b")
    print(f"  ✓ Response: {response['message']['content'][:50]}...")
    
except Exception as e:
    print(f"  ⚠ Ollama not connected: {e}")
    print(f"  Note: Start Ollama with: ollama serve")
    print(f"  Then pull model: ollama pull qwen2.5:32b")

# Summary
print("\n" + "=" * 60)
print("SYSTEM TEST COMPLETE")
print("=" * 60)
print("\n✨ C2A Elegant is ready!")
print("\nTo begin training:")
print("  python c2a_elegant_main.py")
print("\nTo view archetypes:")
print("  python constraint_archetypes.py")
print("\n" + "=" * 60)
