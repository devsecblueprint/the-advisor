# services/resume_reviewer.py
import os
from dotenv import load_dotenv
import cohere

load_dotenv()


class ResumeReviewService:
    def __init__(self, model: str = "command-r-plus"):
        self.client = cohere.Client(os.getenv("COHERE_API_KEY"))
        self.model = model

    def generate_feedback(self, prompt: str) -> str:
        response = self.client.generate(
            model=self.model, prompt=prompt, temperature=0.4
        )
        return response.generations[0].text.strip()
