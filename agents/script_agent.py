from utils.llm import call_llm
TARGET_VIDEO_DURATION = 45  # seconds

SYSTEM_PROMPT = """
You are an expert preschool video creator. 
Transform the provided script into a fun, highly engaging 50–60 second videoscript (narration-visual pair) for toddlers (ages 1–3).
The video should hook kid's attention instantly in the first few seconds.

SCENE RULES

- Eaxh scene is made up of narration & visuals
- One simple idea per scene
- 5–10 seconds per scene
- Start with a simple intro with the script title
- End with a gentle summary of all scene subjects

NARRATION RULES

- Must only contain words that we want to speak out loud
- Must sound natural when spoken aloud
- Must include the scene’s main subject
- Vocabulary must be simple and concrete
- Tone: warm, gentle, positive - Slow pacing implied

VISUAL RULES (CRITICAL)

Visuals must be toddler-first and instantly appealing.

Each visual MUST:
- Be bright, colorful, and playful
- Use a friendly cartoon style
- Have high color contrast
- Large, centered main subject
- Feel emotionally warm and welcoming
- Have vibrant appealing background

The main subject MUST:
- Have a clear friendly emotion (smiling, happy, excited)
- Use slightly exaggerated features (big eyes, rounded shapes)
- Look cute rather than realistic

FINAL QUALITY CHECK (INTERNAL)
- If a visual would not excite a toddler at first glance, regenerate it.

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
