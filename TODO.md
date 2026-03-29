# Fix GitHub Secret Scanning Block - TODO Steps

## Approved Plan Breakdown
1. [x] Edit backend/ai_engine.py: Add import os and replace hardcoded Groq API key with os.getenv("GROQ_API_KEY")
2. [x] Create .env file at root with GROQ_API_KEY placeholder
3. [x] Create .gitignore at root to exclude .env and caches
4. [ ] Test: Run app.py and verify AI functions use env or fallback
5. [ ] Git commit and push (now safe)

Track progress by updating this file after each step.

