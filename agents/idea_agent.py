from utils.llm import call_llm
from utils.memory import get_recent_formats

SYSTEM_PROMPT = """
Based on a given topic, create ONE simple, engaging animated video "idea" for children aged 1–3,
The idea must be suitable for a 50–60 second YouTube Kids animated video with simple visuals and narration.

CORE REQUIREMENTS (NON-NEGOTIABLE)

• Total video length: 50–60 seconds
• Predictable and repeatable structure
• No challenges, quizzes, scoring, or testing

AGE-APPROPRIATENESS (CRITICAL)

• Designed specifically for ages 1–3
• Use only simple, familiar, everyday objects
• Focus on concrete, visible concepts only
• The idea must follow a simple, repeatable pattern

OUTPUT RULES (STRICT)

• Output VALID JSON only
• No markdown
• No explanations
• No extra text
• Format exactly as:

{
  "idea": "string"
}

Only output the JSON object.
"""

def generate_idea(topic_data: dict):
    recent_formats = get_recent_formats()

    user_prompt = f"""
    Topic: {topic_data["topic"]}
    Category: {topic_data["category"]}

    Recently used formats (avoid repeating the last one):
    {recent_formats}
    """
    return call_llm(SYSTEM_PROMPT, user_prompt)
