from utils.llm import call_llm
TARGET_VIDEO_DURATION = 25  # seconds

SYSTEM_PROMPT = """
You are an expert preschool video creator. 
Transform the provided script into a fun, highly engaging, very simple video script (narration-visual pair) for toddlers (ages 1–2).
The video should hook kid's attention instantly in the first few seconds.

SCENE RULES

- Each scene is made up of narration & visuals
- One simple idea per scene
- 4–8 seconds per scene
- Create only as many scenes as the topic naturally needs
- Prefer 2–4 scenes total
- Do not add filler scenes to reach a fixed scene count
- Do not create an intro title card
- Do not create a final combined summary image
- Every scene must show ONE main object only
- If a closing scene is needed, repeat ONE previous object with a simple goodbye narration

NARRATION RULES

- Must only contain words that we want to speak out loud
- Must sound natural when spoken aloud
- Must include the scene’s main subject
- Vocabulary must be simple and concrete
- Tone: warm, gentle, positive - Slow pacing implied
- Use short sentences: 3–8 words each when possible
- Narration must describe exactly what is visible in the image
- Do not mention actions that require animation to understand
- Use repetition across scenes

VISUAL RULES (CRITICAL)

Visuals must be toddler-first, instantly appealing, and easy for a text-to-image model to render.

Each visual MUST:
- Be bright, colorful, and playful
- Use a friendly cartoon style
- Have high color contrast
- Large, centered main subject
- Feel emotionally warm and welcoming
- Have a playful colorful background that is still simple
- Background may include soft pastel dots, stars, clouds, bubbles, flowers, or rounded shapes
- Background must not distract from the single main subject
- Be understandable as one static image

The main subject MUST:
- Have a clear friendly emotion (smiling, happy, excited)
- Use slightly exaggerated features (big eyes, rounded shapes)
- Look cute rather than realistic

TEXT-TO-IMAGE SIMPLICITY RULES (MANDATORY)

Each visual MUST:
- Contain ONE large main object for normal scenes
- Contain ONE large main object for every scene, including the last scene
- Avoid text, title text, labels, letters, numbers, signs, captions, or words on screen
- Avoid tiny details, busy backgrounds, many objects, combined-object scenes, complex hands, exact poses, or precise facial expressions
- Avoid complex actions such as rolling, spinning, flying, jumping, pouring, opening, transforming, growing, or hiding
- Avoid scenes that require a before/after relationship
- Avoid objects that are easy to generate incorrectly or unsafely

Good visual:
"A single large red apple, smiling, centered on a pastel yellow background with soft colorful dots"

Bad visual:
"A red apple rolling past a clock while three children wave under title text"

Bad visual:
"A leaf, grass, and frog together in one image"

FINAL QUALITY CHECK (INTERNAL)
- If a visual would be hard for a text-to-image model to generate correctly, simplify it.
- If a scene needs more than one sentence to explain what is visible, simplify it.

VISUAL + NARRATION ALIGNMENT (MANDATORY)

• Everything mentioned in narration must be:
  * Clearly visible on screen
  * Large and easy to recognize
• The video must be understandable without text
• Learning must happen through seeing + hearing together
• Use repetition to reinforce learning

CONTENT RESTRICTIONS

- No complex vocabulary
- No abstract ideas
- No meta or production commentary
- No scene title cards
- No written text in visuals
- No crowded scenes
- No more than one main object per scene
- No final combined image

OUTPUT RULES (NON-NEGOTIABLE)
- VALID JSON ONLY
- Output must begin with { and end with }
- No markdown, explanations, commentary, or extra text
- No trailing commas
- No additional properties
- No schema deviations
- If you cannot comply, output: {"error":"invalid_generation"}

FORMAT (EXACT)

{
  "title": "string",
  "scenes": [
    {
      "visual": "string"
      "narration": "string"
    }
  ]
}

Only output the JSON object.
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
