# models/resume.py
from pydantic import BaseModel


class ResumeRequest(BaseModel):
    resume_text: str
