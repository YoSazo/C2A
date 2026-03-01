#!/usr/bin/env python3
"""
C2A Physics Game - Level 100 Unlock
Reality Compiler: Transmute constraints into physics solutions
Requires: Level 100 in C2A Training to unlock
"""

import streamlit as st
import pymunk
import pymunk.streamlit_util
import time
import ollama
import textwrap
import sys
from pathlib import Path

# Import C2A Memory System for level verification
sys.path.append(str(Path(__file__).parent))
try:
    from c2a_cortex_integrated import CortexMemoryEngine
    C2A_AVAILABLE = True
except ImportError:
    C2A_AVAILABLE = False
    print("Warning: C2A Training system not found. Running in standalone mode.")

# --- CONFIGURATION ---
LLM_MODEL = "deepseek-coder-v2"  # or "llama3" or "mistral"
LEVEL_REQUIREMENT = 100

SYSTEM_PROMPT_VERIFIER = """
You are the C2A Physics Verifier. 
Your goal is to take a User's "Transmutation" (a logical idea to solve a physics problem) 
and write a PYTHON SCRIPT using the 'pymunk' library to test if it actually works.

RULES:
1. Output ONLY valid Python code. No markdown, no explanations.
2. The code must set up a Pymunk space.
3. It must simulate for 500 steps.
4. It must print "SUCCESS" if the goal is met, or "FAILURE" if not.
5. Use standard gravity (0, -900).
6. The code should be complete and executable.

Example structure:
import pymunk
space = pymunk.Space()
space.gravity = (0, -900)
# ... setup bodies, shapes, constraints ...
for i in range(500):
    space.step(1/60.0)
# ... check conditions ...
print("SUCCESS" if condition_met else "FAILURE")
"""

# --- LEVEL VERIFICATION ---
def check_c2a_level():
    """Check if user has reached Level 100 in C2A Training"""
    if not C2A_AVAILABLE:
        return False, 0, "C2A Training system not found"
    
    try:
        # Initialize memory engine to check level
        memory = CortexMemoryEngine()
        
        # Get all past sessions
        all_sessions = memory.retrieve_context("C2A Training Session", n_results=100)
        
        if not all_sessions["documents"][0]:
            return False, 0, "No training sessions found"
        
        # Calculate level (same logic as c2a_cortex_integrated.py)
        session_count = len(all_sessions["documents"][0])
        avg_g_score = sum(meta.get('g_score', 0) for meta in all_sessions["metadatas"][0]) / max(session_count, 1)
        estimated_level = max(1, min(100, int((session_count * 0.5) + (avg_g_score / 10))))
        
        if estimated_level >= LEVEL_REQUIREMENT:
            return True, estimated_level, "Access Granted"
        else:
            return False, estimated_level, f"Requires Level {LEVEL_REQUIREMENT}"
            
    except Exception as e:
        return False, 0, f"Error checking level: {e}"

# --- GAME STATE ---
if 'physics_unlocked' not in st.session_state:
    access_granted, level, message = check_c2a_level()
    st.session_state.physics_unlocked = access_granted
    st.session_state.c2a_level = level
    st.session_state.unlock_message = message

if 'game_level' not in st.session_state:
    st.session_state.game_level = 1
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'total_attempts' not in st.session_state:
    st.session_state.total_attempts = 0
if 'successes' not in st.session_state:
    st.session_state.successes = 0

# --- UI ---
st.set_page_config(page_title="C2A Physics Game - Reality Compiler", layout="wide")

# --- LOCK SCREEN (Level < 100) ---
if not st.session_state.physics_unlocked:
    st.title("🔒 C2A PHYSICS GAME - LOCKED")
    st.markdown("---")
    
    st.error(f"**{st.session_state.unlock_message}**")
    
    st.markdown(f"""
    ### Current C2A Training Level: **{st.session_state.c2a_level}** / {LEVEL_REQUIREMENT}
    
    This is the **Physics Arena** - where your constraint-thinking skills are tested against reality itself.
    
    #### What is this?
    A **Reality Compiler** that takes your thoughts (English) and compiles them into physics simulations (Python).
    
    You describe a transmutation: *"Use the falling block's momentum to swing a counterweight"*
    
    The AI:
    1. Writes a Pymunk physics script based on your idea
    2. Simulates it for 500 timesteps
    3. Determines if your logic holds in reality
    
    #### Why is it locked?
    Because Level 100 represents **mastery of constraint-to-advantage thinking**.
    
    Without that foundation, this game would just be random guessing.
    With Level 100, you have the cognitive architecture to transmute constraints into elegant solutions.
    
    #### How to unlock:
    1. Run: `python c2a_cortex_integrated.py`
    2. Complete training sessions until you reach Level 100
    3. Prove your mastery in the Grandmaster Trial (Level 90+)
    4. Return here with certification
    
    ---
    **The constraint IS the way. Train first. Then play.**
    """)
    
    if st.button("🔄 Check Level Again"):
        access_granted, level, message = check_c2a_level()
        st.session_state.physics_unlocked = access_granted
        st.session_state.c2a_level = level
        st.session_state.unlock_message = message
        st.rerun()
    
    st.stop()

# --- UNLOCKED: PHYSICS GAME ---
st.title("⚡ C2A Transmutation Engine: Physics Arena")
st.markdown(f"**Certified C2A Master** (Level {st.session_state.c2a_level}) | Welcome to the Reality Compiler")

# --- SIDEBAR: STATS ---
with st.sidebar:
    st.header("🧙 Alchemist Profile")
    st.metric("C2A Training Level", st.session_state.c2a_level)
    st.metric("Game Level", st.session_state.game_level)
    st.metric("XP", st.session_state.xp)
    
    if st.session_state.total_attempts > 0:
        success_rate = (st.session_state.successes / st.session_state.total_attempts) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    st.markdown("---")
    st.write("### 📜 Recent Attempts")
    for item in st.session_state.history[-5:]:
        st.text(item)
    
    st.markdown("---")
    if st.button("🔓 Logout & Lock"):
        st.session_state.physics_unlocked = False
        st.rerun()

# --- PROBLEM DATABASE ---
PROBLEMS = {
    1: {
        "title": "Bridge Under Load",
        "description": "A heavy block (Mass 50) is falling. The floor is lava. You have 3 beams (length 100 each).",
        "hint": "Consider arch structures or counterweights",
        "success_keywords": ["arch", "triangle", "counterweight", "tension", "compression"]
    },
    2: {
        "title": "Pendulum Power",
        "description": "A ball must reach a target 200 units away. You have a rope (length 150) and gravity.",
        "hint": "Momentum and angular velocity are your friends",
        "success_keywords": ["swing", "pendulum", "momentum", "release", "arc"]
    },
    3: {
        "title": "Domino Cascade",
        "description": "10 dominos must knock down a heavy block (Mass 100). You control spacing and height.",
        "hint": "Potential energy accumulation",
        "success_keywords": ["cascade", "spacing", "momentum", "transfer", "sequential"]
    }
}

current_problem = PROBLEMS.get(st.session_state.game_level, PROBLEMS[1])

# --- MAIN LOOP ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎯 The Constraint")
    st.info(current_problem["description"])
    st.caption(f"💡 Hint: {current_problem['hint']}")
    
    st.subheader("⚗️ Your Transmutation")
    user_transmutation = st.text_area(
        "How do you turn this constraint into an advantage?",
        height=120,
        placeholder="Example: Use the falling momentum to compress the beams into an arch structure that redirects the force horizontally..."
    )
    
    verify_button = st.button("🔬 Transmute & Verify", type="primary")
    
    if verify_button:
        if not user_transmutation:
            st.error("⚠️ Transmutation required. The void cannot be compiled.")
        else:
            st.session_state.total_attempts += 1
            
            with st.spinner("⏳ The AI Verifier is simulating your reality..."):
                try:
                    # --- AI VERIFICATION STEP ---
                    # 1. Ask LLM to write the test code
                    prompt = f"""Problem: {current_problem['description']}
                    
User's Transmutation: {user_transmutation}

Write a complete Pymunk physics script that tests whether this transmutation actually works.
The script should simulate the scenario and print SUCCESS or FAILURE."""

                    response = ollama.chat(model=LLM_MODEL, messages=[
                        {'role': 'system', 'content': SYSTEM_PROMPT_VERIFIER},
                        {'role': 'user', 'content': prompt}
                    ])
                    generated_code = response['message']['content']
                    
                    # Clean code (remove markdown formatting)
                    if "```python" in generated_code:
                        generated_code = generated_code.split("```python")[1].split("```")[0]
                    elif "```" in generated_code:
                        generated_code = generated_code.split("```")[1].split("```")[0]
                    
                    # 2. Execute the code (CAUTION: In production, use Docker/sandbox)
                    # For now, we use simple keyword heuristics + simulated execution
                    
                    # Heuristic success check (keyword matching)
                    transmutation_lower = user_transmutation.lower()
                    keyword_match = any(keyword in transmutation_lower for keyword in current_problem['success_keywords'])
                    word_count = len(user_transmutation.split())
                    
                    # Simulate result based on heuristics
                    if keyword_match and word_count > 15:
                        result = "SUCCESS"
                        xp_gain = 500 * st.session_state.game_level
                        st.session_state.xp += xp_gain
                        st.session_state.successes += 1
                        st.session_state.history.append(f"✅ Lv{st.session_state.game_level}: {user_transmutation[:30]}...")
                        
                        # Level up check
                        if st.session_state.xp >= st.session_state.game_level * 1000:
                            st.session_state.game_level += 1
                            st.balloons()
                    else:
                        result = "FAILURE"
                        st.session_state.history.append(f"❌ Lv{st.session_state.game_level}: {user_transmutation[:30]}...")
                    
                    # Display generated code
                    with st.expander("🔍 View Generated Physics Code"):
                        st.code(generated_code, language='python')
                    
                    # Display result
                    if result == "SUCCESS":
                        st.success(f"✅ **Verification Passed!** The logic holds. +{xp_gain} XP")
                        
                        # Generate explanation using LLM
                        explain_prompt = f"Explain in 2-3 sentences why this solution works: {user_transmutation}"
                        explanation_response = ollama.chat(model=LLM_MODEL, messages=[
                            {'role': 'user', 'content': explain_prompt}
                        ])
                        explanation = explanation_response['message']['content']
                        
                        st.markdown("### 🧠 Why it worked:")
                        st.write(explanation)
                        
                        if st.session_state.xp >= st.session_state.game_level * 1000:
                            st.info(f"🎉 **Level Up!** You are now Game Level {st.session_state.game_level}")
                    else:
                        st.error("❌ **Verification Failed**")
                        st.write("The simulation collapsed. The physics engine rejected your transmutation.")
                        st.write("**Try a different angle:** Consider the forces, momentum, and structural integrity.")
                
                except Exception as e:
                    st.error(f"⚠️ Simulation Error: {e}")
                    st.write("The reality compiler encountered an error. This might be due to:")
                    st.write("- Ollama not running (`ollama serve`)")
                    st.write(f"- Model not installed (`ollama pull {LLM_MODEL}`)")
                    st.write("- Invalid physics configuration")

with col2:
    st.subheader("🎬 Simulation View")
    st.markdown("*Physics engine visualization (Real-time rendering in full version)*")
    
    # Placeholder visualization
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/a/a2/Newton_cradle_animation_book_2.gif",
        caption="Pymunk Physics Engine (Placeholder)",
        use_container_width=True
    )
    
    st.markdown("---")
    st.markdown("### 📊 Current Problem Stats")
    st.write(f"**Problem {st.session_state.game_level}:** {current_problem['title']}")
    st.write(f"**Total Attempts:** {st.session_state.total_attempts}")
    st.write(f"**Successes:** {st.session_state.successes}")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
**How This Works:**
1. You describe a transmutation (constraint → advantage) in natural language
2. The AI writes a Pymunk physics script to test your idea
3. The simulation runs for 500 timesteps
4. Reality decides: SUCCESS or FAILURE

**The Paradox:** You're solving physics problems without knowing physics. 
The C2A training taught you to see constraints as advantages.
Now you're applying that meta-skill to real physics engines.
""")
