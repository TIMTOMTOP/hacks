from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
import base64
import httpx
from typing import Optional

app = FastAPI()



class BrandAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def analyze_brand_guidelines(self, pdf_url: str, brand_name: Optional[str] = None) -> str:
        """
        Analyze a brand guidelines PDF and generate a structured system prompt
        """
        try:
            # Download the PDF content
            content = httpx.get(pdf_url).content
            pdf_data = base64.b64encode(content).decode('utf-8')
            
            analysis_prompt = """You are a brand guidelines analyzer. Extract and structure the key elements of this brand guide into a system prompt format.

            Focus on extracting:
            1. Brand identity and purpose
            2. Color schemes (primary and accent colors with hex codes)
            3. Typography (fonts, sizes, spacing, usage rules)
            4. Logo usage rules and placement
            5. Any specific design elements or patterns
            6. Image guidelines and usage

            Format the output as a system prompt that:
            1. Starts with a clear role definition
            2. Lists all brand elements in a structured manner
            3. Includes specific rules and measurements
            4. Provides clear guidelines for usage
            5. Ends with instructions for handling user requests

            Use clear hierarchical formatting with main categories and subcategories."""
            
            # Analyze the PDF
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                system=analysis_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            },
                            {
                                "type": "text", 
                                "text": f"Analyze this brand guideline document{' for ' + brand_name if brand_name else ''} and create a structured system prompt that captures all key brand elements and usage rules."
                            }
                        ]
                    }
                ]
            )
            
            return message.content
            
        except Exception as e:
            raise Exception(f"Error analyzing brand guidelines: {str(e)}")


"""url = "https://dsgjssiyprmqymrpraxf.supabase.co/storage/v1/object/public/AAK//grafiskmanual-2.0.1-2024.pdf"""

"""if __name__ == "__main__":
    analyzer = BrandAnalyzer(api_key="")
    system_prompt = analyzer.analyze_brand_guidelines(
        url,
        "LUND"
    )
    print(system_prompt)"""

