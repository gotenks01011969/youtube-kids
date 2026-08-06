from utils.llm import call_llm
from utils.memory import get_recent_formats

SYSTEM_PROMPT = """
Create ONE video idea for the given topic.
This pipeline can only make static images, one image per scene, plus spoken narration.
The idea must be simple enough for a text-to-image model to draw well.

IDEA CONTRACT
- Provide 3-5 learning examples when the topic naturally supports it.
- Each learning example introduces ONE object.
- Use the same sentence pattern across scenes.
- Do not include a final recap scene with multiple objects.
- Do not include an intro title card.
- Do not include actions, movement, transformations, hiding, finding, counting, questions, quizzes, or stories.
- The viewer is age 1-2, so use familiar objects and very simple words.
- The final video will add fixed opening and closing scenes separately.

WHAT THE IDEA STRING MUST INCLUDE
- The exact object for each learning example.
- The learning word repeated for each object, such as the color, shape, animal name, or object family.
- A short note that every image is one large cute object on a bright colorful background.

GOOD IDEA
"A three-example color video. Example 1: one red apple. Example 2: one red strawberry. Example 3: one red balloon. The narration repeats: This is red. The images are cute, bright, and simple."

BAD IDEA
"A red apple rolls past a strawberry and a fire truck, then all red things appear together."

IMAGE-SAFE OBJECT RULES
- Prefer objects with simple silhouettes.
- Avoid objects that need tiny details, exact text, hands, faces of people, rooms, roads, or multiple parts.
- For shape topics, every object must naturally match the target shape.
- Square: use square block, square box, square tile, square pillow, square window, square cracker.
- Circle: use ball, cookie, wheel, clock, sun, moon.
- Triangle: use triangle block, triangle flag, triangle roof, triangle slice.
- Do not use plate, ball, wheel, clock, cookie, moon, or sun for square.

OUTPUT RULES
- Output VALID JSON only.
- No markdown.
- No explanations.
- No extra keys.

OUTPUT FORMAT
{
  "idea": "string"
}
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
