import os
import httpx
from typing import List, Dict, Any
from . import schemas

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"

def get_api_key() -> str:
    """
    Retrieves the trimmed GROQ_API_KEY from environment variables.
    """
    key = os.environ.get("GROQ_API_KEY", "")
    return key.strip()

async def check_api_key_valid() -> bool:
    """
    Sends a test request to Groq serverless model to verify if the configured 
    API key is authenticated and active.
    """
    api_key = get_api_key()
    if not api_key:
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            return response.status_code == 200
    except (httpx.HTTPError, httpx.TimeoutException):
        return False
    except Exception:
        return False

async def fetch_groq_completion(messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
    """
    Executes a chat completion query against the Groq API.
    
    Args:
        messages: A list of chat message dictionaries containing roles and contents.
        temperature: Controls completion creativity (0.0 = deterministic, 1.0 = creative).
        
    Returns:
        The text response content from the AI model.
        
    Raises:
        ValueError: If the Groq API key is missing.
        Exception: If the server returns an error code status.
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in the environment variables.")
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(GROQ_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            err_msg = f"Groq API returned status {response.status_code}: {response.text}"
            raise Exception(err_msg)
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

async def get_coaching_response(
    habit: schemas.HabitSchema, 
    history: List[schemas.MessageSchema], 
    user_message: str, 
    is_sos: bool = False
) -> str:
    """
    Generates a personalized CBT coaching response based on the active habit settings,
    recent message dialog strings, and whether the emergency grounding SOS switch is activated.
    
    Args:
        habit: Pydantic Habit schema containing settings (triggers, target reductions).
        history: Conversation message schema records representing historical context.
        user_message: Latest user request or message string.
        is_sos: Triggers brief somatic grounding guidelines when active.
        
    Returns:
        Empathetic, action-oriented behavioral advice from Aura.
    """
    # Build System Prompt
    system_prompt = (
        "You are Aura, an empathetic, supportive, and scientifically-grounded behavioral coach specializing "
        "in habit modification and addiction recovery using Cognitive Behavioral Therapy (CBT) and Acceptance and "
        "Commitment Therapy (ACT) principles. The user is trying to break the habit of '{habit_name}' "
        "({habit_description}). Their target is to '{target_reduction}'. Their core motivation is '{motivation}' "
        "and their primary triggers are '{triggers}'.\n\n"
    ).format(
        habit_name=habit.name,
        habit_description=habit.description or "No description provided",
        target_reduction=habit.target_reduction or "not specified yet",
        motivation=habit.motivation or "general self-improvement",
        triggers=habit.triggers or "unknown triggers"
    )

    if is_sos:
        system_prompt += (
            "EMERGENCY/SOS MODE ACTIVATED: The user is experiencing an intense craving/urge right now and has requested immediate assistance.\n"
            "Instruct them through a brief, effective, somatic grounding exercise (e.g., the 5-4-3-2-1 technique, box breathing, or Urge Surfing: "
            "identifying physical sensations, breathing into the craving, and observing it peak/subside like a wave without acting on it).\n"
            "Keep the response comforting, highly tactical, extremely clear, and under 150 words total."
        )
    else:
        system_prompt += (
            "General coaching guidelines:\n"
            "- Be conversational, encouraging, and non-judgmental.\n"
            "- Provide small, actionable advice.\n"
            "- Ask reflective questions to help them uncover insights about their patterns.\n"
            "- Keep your response brief, clear, and structured (under 3 paragraphs or a couple of short lists).\n"
            "- Never hallucinate metrics; focus on validating their efforts."
        )

    # Build messages sequence
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append conversation history
    for msg in history:
        role = "assistant" if msg.sender == "coach" else "user"
        messages.append({"role": role, "content": msg.message})
        
    # Append current message
    messages.append({"role": "user", "content": user_message})
    
    return await fetch_groq_completion(messages, temperature=0.7)

async def generate_nudge(habit: schemas.HabitSchema, recent_logs: List[schemas.LogSchema]) -> str:
    """
    Analyzes historical habit metrics to draft a single tailored nudge sentence.
    
    Args:
        habit: User habit properties.
        recent_logs: Log schema entries covering the recent period.
        
    Returns:
        A highly targeted motivating nudge (max 40 words).
    """
    system_prompt = (
        "You are Aura, a supportive habit coach. Your job is to output a single, highly tailored, "
        "daily nudge (exactly 1-2 sentences, maximum 40 words) for a user trying to overcome '{habit_name}'."
    ).format(habit_name=habit.name)

    logs_context = ""
    if not recent_logs:
        logs_context = "The user has just started. Write a warm onboarding nudge to encourage them to log their first daily check-in."
    else:
        last_log = recent_logs[-1]
        slip_up_count = sum(1 for log in recent_logs if log.slip_up)
        avg_craving = sum(log.craving_level for log in recent_logs) / len(recent_logs)
        
        logs_context = (
            f"Here is their recent tracking history:\n"
            f"- Days logged: {len(recent_logs)}\n"
            f"- Latest Log: Date={last_log.date}, Value={last_log.metric_value}, Craving={last_log.craving_level}/10, Slip-up={last_log.slip_up}\n"
            f"- Total slip-ups: {slip_up_count} in recent days\n"
            f"- Average craving: {avg_craving:.1f}/10\n\n"
            "Write a prompt-specific daily nudge. If they slipped up, give brief, constructive motivation. "
            "If they did well, celebrate their discipline. Keep it short, sharp, and highly tailored."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": logs_context}
    ]
    
    try:
        # Low temperature for highly focused nudge
        return await fetch_groq_completion(messages, temperature=0.5)
    except Exception:
        return f"Stay strong! Every step toward breaking {habit.name} counts. Keep tracking your progress."

async def generate_analysis(habit: schemas.HabitSchema, recent_logs: List[schemas.LogSchema]) -> str:
    """
    Processes all logs to formulate a comprehensive weekly behavioral assessment report.
    
    Args:
        habit: User habit properties.
        recent_logs: Entire set of logged entries.
        
    Returns:
        Structured Markdown assessment of trigger trends and tactical adjustments.
    """
    system_prompt = (
        "You are Aura, an analytical behavior expert specializing in habit architecture and CBT. "
        "Your task is to write a comprehensive weekly progress analysis and behavioral review based "
        "on the user's logged data. The user wants to break '{habit_name}'. Triggers: '{triggers}'. "
        "Motivation: '{motivation}'."
    ).format(
        habit_name=habit.name,
        triggers=habit.triggers or "unknown",
        motivation=habit.motivation or "general growth"
    )

    if not recent_logs:
        return (
            "### Weekly Assessment: Setup Complete\n\n"
            "You have configured your habit profile successfully. To receive a personalized weekly "
            "behavioral assessment, please begin tracking your daily triggers and metric levels in the Log tab."
        )

    logs_text = "\n".join([
        f"- {log.date}: Value={log.metric_value}, Craving={log.craving_level}/10, Slip-up={log.slip_up}, Note={log.notes or 'None'}"
        for log in recent_logs
    ])

    user_prompt = (
        f"Analyze the following daily logs:\n{logs_text}\n\n"
        "Provide a structured assessment in Markdown format containing:\n"
        "1. **Trigger & Urge Patterns**: Correlate cravings and slip-ups (if any) with notes and triggers.\n"
        "2. **Progress Metrics**: Note streaks, average craving level, and performance against baseline.\n"
        "3. **Aura's Strategic Advice**: 2-3 specific adjustments using CBT techniques they can try next week.\n\n"
        "Keep the analysis professional, supportive, under 250 words, and write in Markdown. Do not include signature blocks."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        return await fetch_groq_completion(messages, temperature=0.6)
    except Exception as e:
        return f"Unable to generate analysis: {str(e)}"
