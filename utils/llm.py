import json
from openai import OpenAI
from utils.secrets import get_groqcloud_key

GROQCLOUD_MODEL = "openai/gpt-oss-20b"

client = OpenAI(
    api_key=get_groqcloud_key(),
    base_url="https://api.groq.com/openai/v1",
)

def call_llm(system_prompt: str, user_prompt: str) -> dict:
    """
    Calls GroqCloud LLM and returns parsed JSON.
    Model MUST return valid JSON only.
    """

    full_prompt = f"""
    SYSTEM:
    {system_prompt}

    USER:
    {user_prompt}

    IMPORTANT:
    - Respond with VALID JSON ONLY
    - No markdown
    - No explanation
    """

    response = client.responses.create(
        model=GROQCLOUD_MODEL,
        input=full_prompt,
    )

    raw_text = response.output_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned invalid JSON.\nRaw output:\n{raw_text}"
        ) from e
