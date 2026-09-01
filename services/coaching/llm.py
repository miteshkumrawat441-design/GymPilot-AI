import os
from services.config.workout_config import PROMPT


class LLMCoach:
    AVAILABLE_MODELS = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "groq/compound-mini",
        "groq/compound",
        "llama-3.3-70b-versatile"
    ]

    def __init__(self, groq_client):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT

    def give_feedback(self, event, issue=None):
        prompt = f"Event: {event}"

        if issue:
            prompt += f" Form Issue: {issue}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-8:],
            {"role": "user", "content": prompt}
        ]

        text = None
        for model_name in self.AVAILABLE_MODELS:
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.4,
                    max_tokens=60,
                )
                if response.choices and response.choices[0].message.content:
                    text = response.choices[0].message.content.strip()
                    break
            except Exception as e:
                continue

        if not text:
            # Fallback coaching lines if offline or API failure
            if event == "workout_started":
                text = "Let's go! Maintain solid form and stay focused."
            elif event == "workout_completed":
                text = "Great job finishing your workout! Excellent effort."
            elif event == "set_completed":
                text = "Set complete! Take a quick breath and get ready."
            elif issue:
                text = f"Keep your form tight: {issue}"
            else:
                text = "Looking strong! Keep that pace going."

        self.history.append({"role": "assistant", "content": text})
        return text