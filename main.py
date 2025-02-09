from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv
from typing import Optional
from profile_generator import BrandAnalyzer

load_dotenv()

app = FastAPI()

# Pydantic models for request validation
class LatexRequest(BaseModel):
    request_type: str  # Initial request or style choice
    content: str      # The actual request content
    conversation_id: Optional[str] = None  # To track conversations
    latex: Optional[str] = None

class BrandGuidelineRequest(BaseModel):
    pdf_url: str
    brand_name: Optional[str] = None


    

# Store conversations
conversations = {}

# Initialize Anthropic client
client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a professional design assistant for Villa Klint—an exclusive alpine skii resort——specialized in creating LaTeX code for design elements always strictly adhereing to their brand guidelines. You create anything from posters, and pamphlets to invitations, and letters.

When generating LaTeX code ensure it is compatible with pdfxe

Key Brand Elements:
- Color Schemes:
  * Primary:
     + Pure White (#FFFFFF) text on Washed Green (#61603F) background
     + Washed Green (#61603F) text on  background Pure White (#FFFFFF)
     + Off Black (#1A1A1A) text on Light Gray (#F4F3F1) background
     + Off Black (#1A1A1A) text on Pure White (#FFFFFF) background
  * accent colors
     + Off Black (#1A1A1A) text on Light Washed Green (#B1B79B) background
     + Off Black (#1A1A1A) text on Burnt Orange (#E47436) background
     + Off Black (#1A1A1A) text on Pale Sky Blue (#CDE7E9) background

- Typography (use package fontspec):
  * Headings: GT-Alpina-Standard-Thin.otf & GT-Alpina-Extended-Thin-Italic.otf, Size 100%, letter spacing -2%, leading 110%
  * Smaller heading/preamble: Söhne-Buch.otf, Size 30-40% to H1, leetter spacing -0.5%, leading 110%
  * Body Text: Söhne-Leicht.otf, size 20-30% to H1, letter spacing 0%, leading 130%
  * Example
    \setmainfont{GT-Alpina-Standard-Thin}[
        Path = /tmp/fonts,
        Extension = .otf
        ]

  
- Rules for usage of brand name and logo:
  * Brand name (primary)
    + always written as "Villa Klint"
    + Written using 'GT Alpina Thin'
    + the brand name always have a margin of its own height on the sides, below, and above of any other elements
  * Logo (secondary)
    + brand_avatar_on_transparent_background.png
  * Placements
    + The logo/brand name is primarily placed centered at the top or bottom of the document.
    + On occasions when the logo/brand name appears without other elements (typography, images, etc.), it can preferably be centered both horizontally and vertically.
    + In exceptional cases, the logo/brand name can be placed left-aligned at the top or bottom edge.
    + Always include the either the brand name or the logo.
  
- Images to select from (inside dir /images, never change relative dimensions, you may scale the brand avatar logo):
  * images/alpine_skiing_descent.png
  * images/cozy_breakfast.png
  * images/green_nature.png
  * images/ambient_photo_of_hotel_interior.png
  * images/cozy_fireplace_in_the_sunset.png
  * images/handpainted_illustration_on_alps_and_hotel_in_light_wash_green_on_transparent_background.png
  * Example
    + \includegraphics[width=8cm]{images/brand_avatar_on_transparent_background.png}
  

When users request materials, you should:
1. First ask about styling preferences, offering options that align with the brand
2. Provide clear examples based on their guidelines
3. Only after receiving preferences, generate appropriate LaTeX code

Never generate code without first confirming style preferences."""

class LatexGenerator:
    def __init__(self):
        self.conversation_history = []
    
    def generate_suggestions(self, user_request):
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Remember, only return suggestions for this request: \n \n {user_request}"}
            ]
        )
        self.conversation_history.extend([
            {"role": "user", "content": user_request},
            {"role": "assistant", "content": response.content}
        ])
        return response.content
    
    def generate_latex(self, user_choice: str) -> str:
        # Construct the new message for the style choice
        user_message = f"I choose option {user_choice}. Please generate the LaTeX code directly without asking any additional questions."
        messages = self.conversation_history + [
            {"role": "user", "content": user_message}
        ]

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=SYSTEM_PROMPT + "\nImportant: When a user selects an option, generate the LaTeX code immediately without asking additional questions. LaTeX code only!!!",
            messages=messages
        )
        # Append this turn to the conversation history
        self.conversation_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response.content}
        ])
        return response.content
    
    def generate_update(self, user_update: str) -> str:
        # Construct the new message for the update request
        user_message = f"This is an update request to the last latex code: {user_update}.\nPlease generate the LaTeX code directly without asking any additional questions."
        messages = self.conversation_history + [
            {"role": "user", "content": user_message}
        ]

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system="Important: When a user requests an update, generate the LaTeX code immediately without asking additional questions. LaTeX code only!!! DO NOT CHANGE MORE THAN THE REQUESTED\n" + SYSTEM_PROMPT,
            messages=messages
        )
        # Append this turn to the conversation history
        self.conversation_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response.content}
        ])
        return response.content

@app.post("/generate-latex")
async def generate_latex(request: LatexRequest):
    try:
        if request.conversation_id and request.conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if request.request_type == "initial":
            # Create new conversation
            generator = LatexGenerator()
            conversation_id = str(len(conversations))
            conversations[conversation_id] = generator
            
            # Generate initial options
            response = generator.generate_suggestions(request.content)
            
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
        
        elif request.request_type == "update":
            if not request.conversation_id:
                raise HTTPException(status_code=400, detail="Conversation ID required for update")
            if not request.latex:
                raise HTTPException(status_code=400, detail="LaTeX code required for update")
            
            generator = conversations[request.conversation_id]
            latex_code = generator.generate_update(request.content)
            
            return {
                "conversation_id": request.conversation_id,
                "content": latex_code,
                "status": "latex_update"
            }
        
        
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/analyze-brand-guidelines")
async def analyze_brand_guidelines(request: BrandGuidelineRequest):
    try:
        analyzer = BrandAnalyzer(api_key="API KEY HERE")
        system_prompt = analyzer.analyze_brand_guidelines(
            request.pdf_url,
            request.brand_name
        )
    
        return {
            "status": "success",
            "system_prompt": system_prompt
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