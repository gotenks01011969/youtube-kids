from utils.llm import call_llm
from utils.memory import get_recent_formats

SYSTEM_PROMPT = """
Based on a given topic, create ONE extremely simple animated video "idea" for children aged 1–2.
The idea must be suitable for a short YouTube Kids video made from simple static images and narration.

CORE REQUIREMENTS (NON-NEGOTIABLE)

• Use only as many scenes as the topic naturally needs
• Prefer 2–4 object scenes
• Do not add filler scenes just to reach a fixed duration
• Predictable and repeatable structure
• No challenges, quizzes, scoring, or testing
• Must work as a sequence of simple static images with spoken narration

AGE-APPROPRIATENESS (CRITICAL)

• Designed specifically for ages 1–2
• Use only simple, familiar, everyday objects
• Focus on concrete, visible concepts only
• The idea must follow a simple, repeatable pattern

IMAGE SIMPLICITY REQUIREMENTS

• Each scene should need only ONE main object on screen
• Do not create a final combined image scene
• Do not ask for multiple examples in one image
• Avoid scenes that require text, letters, numbers, signs, labels, tiny details, exact facial expressions, complex backgrounds, or multiple actions
• Avoid motion-dependent ideas like rolling, spinning, flying, growing, opening, changing, hiding, or transforming
• Prefer ideas where the narrator can say the same simple sentence pattern for each object
• Good pattern: "Red apple. Red apple is red."
• Bad pattern: "The apple rolls past the clock while the sun rises."
• Bad pattern: "Apple, strawberry, and fire truck appear together."

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
