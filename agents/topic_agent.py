from utils.llm import call_llm
from utils.memory import get_recent_topics

SYSTEM_PROMPT = """
You choose ONE YouTube Kids topic for a video made from static AI images, local TTS narration, and local video assembly.
The viewer is age 1-2, so the topic must be extremely concrete, familiar, and easy to show.

NON-NEGOTIABLE TOPIC FILTER
- The learning section must work with 3-5 simple examples.
- Each learning example must show exactly ONE large, centered object.
- The final video will also include fixed channel-logo opening and closing scenes.
- The topic must not require action, motion, counting, reading, emotions, comparison, location, story, sequence, or many objects.
- The topic must be safe, calm, cheerful, and toddler appropriate.
- The topic must teach one tiny concept only.
- Use real-world objects a toddler may actually see at home, outside, in food, or in simple play.
- Use objects a text-to-image model can draw reliably as cute cartoons, but choose realistic examples, not random decorative symbols.

BEST TOPIC TYPES
- Colors with familiar real objects: red apple, yellow banana, green leaf, orange carrot, blue cup.
- Shapes with unmistakable single objects: square block, circle ball, triangle flag.
- One object family with 3-5 examples: fruits, toys, simple vehicles, simple household objects.
- Simple body parts only if each scene can show one part clearly.

IMAGE-SAFE OBJECT BIAS
- Prefer realistic toddler-known objects: apple, banana, carrot, leaf, flower, balloon, ball, block, box, pillow, tile, window, cracker, cookie, cup, car, bus, boat, train, teddy bear, sun, moon, cloud.
- Use heart or star mainly for shape topics, not as generic color examples.
- Use simple animals only when the topic is about animals: frog, fish, duck, cat, dog.
- Avoid animals with thin legs, wings, feathers, long necks, stripes, spots, or many body parts unless the animal itself is the learning topic.
- Avoid food with ambiguous shapes for shape topics.
- Avoid unrealistic pairings like orange sun for the color orange unless the topic is specifically sky/sun.
- Avoid examples that feel like icons instead of real objects when a real object is available.

AVOID TOPICS
- Anything requiring text in the image: alphabet, written words, labels, signs.
- Anything requiring exact quantities: counting, many items, number learning.
- Anything requiring complex scenes: playgrounds, rooms, roads, farms, families.
- Anything requiring a final combined scene.
- Anything abstract: kindness, sharing, big/small, same/different, before/after.
- Anything with fragile visual accuracy: square plate, square wheel, square sun, invisible sound, smell, taste.

SHAPE SAFETY RULES
- Square examples must be naturally square: square block, square box, square tile, square pillow, square window, square cracker.
- Circle examples must be naturally round: ball, cookie, wheel, clock, sun, moon.
- Triangle examples must be naturally triangular: triangle block, triangle flag, triangle roof, triangle slice.
- Never use a normally round object for a square topic.

OUTPUT RULES
- Respond with VALID JSON ONLY.
- No markdown.
- No explanations.
- No extra keys.

OUTPUT FORMAT
{
  "topic": "string",
  "category": "string"
}
"""

def generate_topic():
    recent_topics = get_recent_topics()

    user_prompt = f"""
    Recent topics (DO NOT repeat or closely resemble):
    {recent_topics}

    Generate ONE new topic.
    """
    return call_llm(SYSTEM_PROMPT, user_prompt)
