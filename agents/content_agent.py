from utils.llm import call_llm

SYSTEM_PROMPT = """
Create a highly engaging 50–60 second YouTube Kids video script for toddlers aged 1–3.
Create this video based only on the provided Topic and Idea.
The content must be suitable for an animated video with simple visuals and narration.

The script must:

- Use very simple language appropriate for ages 1–3.
- Include content/sentences appropriate for toddlers.
- Be high-energy, joyful, and emotionally positive.
- Stay focused on the learning topic/idea
- Use short sentences that can be matched to simple static images.
- Mention only things that can be shown clearly in one image.
- Use a repeated sentence pattern across examples.

IMAGE-FRIENDLY CONTENT RULES

- Keep each example focused on ONE familiar object.
- Do not require motion, timing, sequence, transformation, or cause/effect to understand the scene.
- Avoid crowded scenes, many objects, small details, text on screen, letters, numbers, signs, labels, or complex backgrounds.
- Avoid abstract descriptions like "kind", "different", "same but bigger", "near/far", or "before/after".
- Prefer concrete lines such as "This is a red apple. The apple is red."

Do not introduce unrelated themes.

OUTPUT RULES:
- VALID JSON ONLY
- No markdown
- No explanations

OUTPUT FORMAT:
{
  "content": "string"
}
Only output the JSON object.
"""

def generate_content(topic_data: dict, idea_data: dict):
    user_prompt = f"""
    Topic: {topic_data["topic"]}
    Idea: {idea_data["idea"]}
    """
    return call_llm(SYSTEM_PROMPT, user_prompt)
