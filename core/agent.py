# core/agent.py
import os
from typing import Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class DreamReconstruction(BaseModel):
    response_message: str = Field(
        description="Your reply to the user. If details are missing, ask 1-2 thoughtful clarifying questions about sensory details, emotions, or setting. If ready, provide the final psychological dream analysis."
    )
    ready_for_reconstruction: bool = Field(
        description="Set to FALSE if the user just greeted, provided a vague fragment, or if you still need clarifying details. Set to TRUE ONLY when the user has described sufficient dream narrative to produce accurate visual reconstructions."
    )
    confidence_score: int = Field(
        description="Integer between 10 and 100 representing how much detail and clarity has been gathered so far. Needs to be >= 75 to trigger reconstruction."
    )
    prompt_realistic: Optional[str] = Field(
        default=None,
        description="Detailed prompt for realistic scene reconstruction. ONLY provide when ready_for_reconstruction is TRUE."
    )
    prompt_surreal: Optional[str] = Field(
        default=None,
        description="Detailed prompt for surreal/distorted emotional reconstruction. ONLY provide when ready_for_reconstruction is TRUE."
    )

class ForensicAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chat_history = []
        self.system_instruction = (
            "You are Detective Morpheus, an intuitive, analytical, and empathetic dream reconstruction specialist.\n"
            "Your objective is to help the user uncover and reconstruct the vivid details of their dream.\n"
            "RULES OF ENGAGEMENT:\n"
            "1. DO NOT rush to generate visual reconstructions on the first exchange unless the user provides an exhaustive, multi-paragraph dream description.\n"
            "2. If the user merely greets you, says 'hi', or provides a brief, vague fragment, set ready_for_reconstruction to FALSE and confidence_score under 40. Ask targeted questions about what they saw, felt, heard, or feared.\n"
            "3. Progressively increase confidence_score as more context is revealed across turns.\n"
            "4. Only set ready_for_reconstruction to TRUE when you have gathered enough setting, subject, lighting, and mood details to justify generating TWO distinct art panels (Realistic and Surreal)."
        )

    def load_history(self, messages: list):
        """Restores memory from previous sessions."""
        self.chat_history = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            self.chat_history.append(
                types.Content(role=role, parts=[types.Part.from_text(text=m.get("content", ""))])
            )

    def process_input(self, user_text: str) -> DreamReconstruction:
        self.chat_history.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
        )
        
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=self.chat_history,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                response_mime_type="application/json",
                response_schema=DreamReconstruction,
                temperature=0.7,
            ),
        )
        
        self.chat_history.append(
            types.Content(role="model", parts=[types.Part.from_text(text=response.text)])
        )
        return response.parsed