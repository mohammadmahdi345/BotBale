from openai import AsyncOpenAI

from app.config.settings import Settings

SYSTEM_PROMPT = """
You are a Persian-speaking immigration consultation assistant for Bale Messenger.
Answer only immigration and migration questions: visas, study/work/investment migration,
startup visas, permanent residency, settlement planning, documents, eligibility and country
selection. Be clear that your answer is guidance, not legal advice. If the user asks about
unrelated topics, politely refuse in Persian and redirect them to immigration questions.
Use a warm, concise, human-like Persian tone.
"""

RECOMMENDATION_PROMPT = """
Analyze this immigration profile and recommend the most suitable countries.
Return the answer in Persian with:
1. Top recommended countries.
2. Why each country fits the profile.
3. Main risks or missing requirements.
4. Practical next steps.
Do not invent guaranteed outcomes. Treat the answer as consultation guidance, not legal advice.
"""


class AIConsultant:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

    async def answer_question(self, user_question: str, history: list[dict] | None = None) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-8:])
        messages.append({"role": "user", "content": user_question})
        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content or "متاسفم، پاسخ مناسبی تولید نشد."

    async def recommend_countries(self, category: str, answers: dict[str, str]) -> str:
        profile_lines = "\n".join(f"- {key}: {value}" for key, value in answers.items())
        user_prompt = f"{RECOMMENDATION_PROMPT}\n\nروش مهاجرت: {category}\n{profile_lines}"
        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or "امکان تهیه پیشنهاد در حال حاضر وجود ندارد."
