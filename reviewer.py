import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-2.0-flash"
_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

MODES = {
    "general": {
        "label": "General Review",
        "prompt": """
You are a senior software engineer doing a code review.

Review the following code and provide:
1. BUGS — any logic errors, edge cases, or crashes waiting to happen
2. CODE QUALITY — readability, structure, naming, duplication
3. PERFORMANCE — any obvious inefficiencies
4. QUICK WINS — top 3 specific improvements with rewritten code snippets

Be direct. Skip praise. Flag real issues only.
""",
    },
    "security": {
        "label": "Security Review",
        "prompt": """
You are a security engineer specializing in LLM systems and web APIs.

Do a security-focused review of the following code. Check for:
1. INJECTION RISKS — prompt injection, SQL injection, shell injection
2. AUTH & SECRETS — hardcoded keys, missing auth, insecure token handling
3. INPUT VALIDATION — unvalidated inputs, missing sanitization
4. DATA EXPOSURE — logging sensitive data, over-permissive responses
5. DEPENDENCY RISKS — any obviously unsafe libraries or patterns

Rate overall security: LOW / MEDIUM / HIGH risk.
Be specific. Point to exact lines or patterns.
""",
    },
    "explain": {
        "label": "Explain Code",
        "prompt": """
You are a senior engineer explaining code to a junior developer.

For the following code:
1. What does it do at a high level? (2-3 sentences)
2. Walk through the key logic step by step
3. What assumptions or dependencies does it rely on?
4. What would break it?

Keep it clear and concrete.
""",
    },
    "refactor": {
        "label": "Refactor Suggestions",
        "prompt": """
You are a senior engineer focused on clean, maintainable code.

Suggest concrete refactoring improvements for this code:
1. STRUCTURE — better organization, separation of concerns
2. PATTERNS — design patterns that apply here
3. REWRITE — provide a cleaner version of the most problematic section

Show actual rewritten code, not just advice.
""",
    },
}


def review(code: str, mode: str = "general", context: str = "") -> str:
    """Run a code review using the specified mode."""
    mode_config = MODES.get(mode, MODES["general"])
    system_prompt = mode_config["prompt"].strip()

    context_block = f"\nContext about this code: {context}\n" if context else ""

    prompt = f"""
{system_prompt}
{context_block}
Code:
```
{code}
```
"""
    response = get_client().models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()


def review_diff(diff: str, mode: str = "security") -> str:
    """Review a git diff specifically."""
    mode_config = MODES.get(mode, MODES["security"])
    system_prompt = mode_config["prompt"].strip()

    prompt = f"""
{system_prompt}

This is a git diff (lines starting with + are additions, - are removals):

{diff}

Focus your review on what changed, not the full context.
"""
    response = get_client().models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()
