from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = FastAPI()

# Pydantic models for request validation
class SignRequest(BaseModel):
    request_type: str  # Initial request or style choice
    content: str      # The actual request content
    conversation_id: Optional[str] = None  # To track conversations

# Store conversations
conversations = {}

# Initialize Anthropic client
client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a design assistant for Villa Klint, specializing in creating LaTeX signs that strictly adhere to their brand guidelines. 

When generating LaTeX code:
1. Ensure it's Overleaf-compatible using pdfLaTeX
2. Use standard LaTeX packages
3. Avoid XeLaTeX-specific packages like fontspec
4. Use fallback fonts that are available in standard LaTeX distributions

Key Brand Elements:
- Colors:
  * Washed Green (#61603F) - Primary
  * Light Washed Green (#B1B79B)
  * Pure White (#FFFFFF)
  * Off Black (#1A1A1A)
  * Burnt Orange (#E47436)
  * Pale Sky Blue (#CDE7E9)

- Typography:
  * Headings: GT Alpina Thin & Extended Thin Italic
  * Subheadings: Söhne Buch
  * Body Text: Söhne Leicht
  * Fallback Fonts: Georgia (headings), Arial (body)

When users request materials, you should:
1. First ask about styling preferences, offering options that align with the brand
2. Provide clear examples based on their guidelines
3. Only after receiving preferences, generate appropriate LaTeX code

Never generate code without first confirming style preferences."""

class SignGenerator:
    def __init__(self):
        self.conversation_history = []
    
    def generate_sign(self, user_request):
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_request}
            ]
        )
        self.conversation_history.extend([
            {"role": "user", "content": user_request},
            {"role": "assistant", "content": response.content}
        ])
        return response.content
    
    def generate_latex(self, user_choice):
        messages = self.conversation_history + [
            {"role": "user", "content": f"I choose option {user_choice}. Please generate the LaTeX code directly without asking any additional questions."}
        ]
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=SYSTEM_PROMPT + "\nImportant: When a user selects an option, generate the LaTeX code immediately without asking additional questions.",
            messages=messages
        )
        return response.content

@app.post("/generate-sign")
async def generate_sign(request: SignRequest):
    try:
        if request.conversation_id and request.conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if request.request_type == "initial":
            # Create new conversation
            generator = SignGenerator()
            conversation_id = str(len(conversations))
            conversations[conversation_id] = generator
            
            # Generate initial options
            response = generator.generate_sign(request.content)
            
            return {
                "conversation_id": conversation_id,
                "content": response,
                "status": "options_generated"
            }
            
        elif request.request_type == "style_choice":
            # Generate LaTeX based on style choice
            if not request.conversation_id:
                raise HTTPException(status_code=400, detail="Conversation ID required for style choice")
                
            generator = conversations[request.conversation_id]
            latex_code = generator.generate_latex(request.content)
            
            return {
                "conversation_id": request.conversation_id,
                "content": latex_code,
                "status": "latex_generated"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optional: Cleanup endpoint
@app.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")