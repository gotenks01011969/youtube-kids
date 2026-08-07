from utils.llm import call_llm

SYSTEM_PROMPT = """
Write the plain narration plan for a toddler learning video.
The next step will convert this content into scene JSON, so the content must be extremely structured and image-safe.

CONTENT CONTRACT
- Use only the objects named or clearly implied by the Idea.
- Use 3-5 object lines total when the topic naturally supports it.
- Use at least 3 object lines unless the topic truly has only 2 safe examples.
- One line equals one future scene.
- Each line mentions ONE object only.
- Use the same short sentence pattern for every object.
- Use words suitable for age 1-2.
- Keep each line easy to speak slowly with Piper TTS.
- Do not write opening or closing lines; the script stage adds those with the channel logo background.
- Prefer realistic toddler-known examples from daily life.
- Do not turn the topic into decorative icons when real examples are available.
- For orange fruit, say "Orange fruit. Fruit is orange." Do not write "Orange orange."

ALLOWED LINE PATTERNS
- "Red apple. Apple is red."
- "Square block. Block is square."
- "Frog. Frog is green."
- "Blue car. Car is blue."

DO NOT WRITE
- A story.
- A question or quiz.
- A title card.
- A final recap combining all objects.
- Motion words such as rolls, jumps, flies, grows, opens, hides, changes, spins.
- Visual instructions that require many objects, rooms, roads, people, hands, text, signs, labels, numbers, or tiny details.
- Abstract language such as same, different, before, after, near, far, kind, best, favorite.
- Unrealistic examples such as "orange sun" for color orange when simple real orange objects are available.

SHAPE SAFETY RULES
- Square objects must be naturally square: square block, square box, square tile, square pillow, square window, square cracker.
- Circle objects must be naturally round: ball, cookie, wheel, clock, sun, moon.
- Triangle objects must be naturally triangular: triangle block, triangle flag, triangle roof, triangle slice.
- Never call a normally round object square.
- Never use plate for square.

OUTPUT RULES
- VALID JSON ONLY.
- No markdown.
- No explanations.
- No extra keys.

OUTPUT FORMAT
{
  "content": "string"
}
"""

def generate_content(topic_data: dict, idea_data: dict):
    user_prompt = f"""
    Topic: {topic_data["topic"]}
    Idea: {idea_data["idea"]}
    """
    return call_llm(SYSTEM_PROMPT, user_prompt)
