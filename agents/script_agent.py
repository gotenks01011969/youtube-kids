from utils.llm import call_llm
TARGET_VIDEO_DURATION = 25  # seconds

SYSTEM_PROMPT = """
Convert the provided content into final scene JSON for a small educational YouTube Kids video.
The pipeline will generate one still image per learning scene, one Piper TTS narration clip per scene, then assemble a horizontal video.
The viewer is age 1-2, so the video must feel like a short, warm lesson.

VIDEO TEMPLATE
- Scene 1 is always an opening scene using the channel logo background.
- Then create 3-5 learning scenes when the topic naturally supports it.
- If the provided content has fewer than 3 learning examples, repeat the strongest example once with a slightly different simple narration.
- Last scene is always a closing scene using the channel logo background.
- Opening narration pattern: "Hi friends. Today we learn about {topic}."
- Closing narration pattern: "Great job friends. See you next time."

HARD LIMITS
- Every learning scene must show exactly ONE main object.
- Opening and closing scenes use the fixed channel logo background and do not need generated images.
- Do not create a final recap image with multiple objects.
- Do not add story, quiz, counting, or action scenes.

NARRATION RULES
- Narration is spoken aloud exactly as written.
- Use 2 short sentences per scene when possible.
- Use 3-8 simple words per sentence when possible.
- Keep each sentence caption-friendly, ideally 2-5 words.
- Repeat the same pattern across scenes.
- Mention only the object and the learning word.
- Do not ask questions.
- Do not mention action, motion, or anything not visible in the image.

VISUAL RULES
- Learning scene visual text must be short, direct, and easy for a text-to-image model.
- Start every learning scene visual with: "One large ..."
- Name the exact object.
- State the exact color or shape if relevant.
- Require the full object to be visible with clear empty margin around it.
- Add "cute smiling cartoon" and "bright colorful simple background".
- Do not describe more than one object.
- Do not describe a scene, room, landscape, crowd, road, table, hands, or sign.
- Do not request written text, labels, letters, numbers, logos, or captions.
- Do not request motion: rolling, jumping, flying, opening, spinning, growing, hiding, changing.
- Opening visual must be exactly: "Channel logo background"
- Closing visual must be exactly: "Channel logo background"

OBJECT SELECTION RULES
- Use only objects from the provided content.
- Prefer realistic, familiar toddler objects from daily life.
- Prefer simple real objects over decorative symbols when the topic is colors, foods, toys, vehicles, animals, or household objects.
- Use heart and star mainly for shape topics.
- Avoid fragile or ambiguous objects.
- Square: square block, square box, square tile, square pillow, square window, square cracker.
- Circle: ball, cookie, wheel, clock, sun, moon.
- Triangle: triangle block, triangle flag, triangle roof, triangle slice.
- Do not use plate for square.
- Do not use round objects for square.

GOOD SCENE
{
  "scene_type": "learning",
  "visual": "One large square toy block, square shape with four equal sides, cute smiling cartoon, bright colorful simple background",
  "narration": "Square block. Block is square."
}

BAD SCENE
{
  "scene_type": "learning",
  "visual": "A square plate on a table with other square things",
  "narration": "Can you find all the squares?"
}

OUTPUT RULES
- VALID JSON ONLY.
- Output must begin with { and end with }.
- No markdown.
- No explanations.
- No trailing commas.
- No additional properties.
- If you cannot comply, output: {"error":"invalid_generation"}

FORMAT
{
  "title": "string",
  "scenes": [
    {
      "scene_type": "opening | learning | closing",
      "visual": "string",
      "narration": "string"
    }
  ]
}
"""

def generate_script(topic_data, idea_data, content_data, feedback=None):
    feedback_text = (
        f"\nPREVIOUS ERROR:\n{feedback}\nPlease fix it.\n"
        if feedback else ""
    )

    user_prompt = f"""
    Target duration: {TARGET_VIDEO_DURATION} seconds
    Script: {content_data["content"]}

    INSTRUCTION:
    Convert the Script into the required JSON format.

    {feedback_text}
    """

    return call_llm(SYSTEM_PROMPT, user_prompt)
