from google import genai
from google.genai import types
import requests
import urllib.parse
import os

class ImageProvider:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.pollinations_base_url = "https://image.pollinations.ai/prompt/"
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_and_save(self, prompt: str, save_path: str) -> bool:
        """
        Attempts to generate image via Gemini (Imagen 3). 
        Falls back to Pollinations.ai if Gemini is unavailable or fails.
        """
        # 1. Try Gemini (Imagen 3 / "Nano Banana Pro")
        if self.client:
            try:
                print(f"Attempting image generation via Gemini Nano Banana Pro...")
                response = self.client.models.generate_image(
                    model='nano-banana-pro-preview',
                    prompt=prompt,
                    config=types.GenerateImageConfig(
                        number_of_images=1,
                        include_rai_reason=True,
                        output_mime_type='image/png'
                    )
                )
                
                if response.generated_images:
                    image_bytes = response.generated_images[0].image.image_bytes
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(image_bytes)
                    print("Successfully generated image via Gemini.")
                    return True
                else:
                    print("Gemini returned no images.")
            except Exception as e:
                print(f"Gemini image generation failed: {e}. Falling back to Pollinations...")
        else:
            print("No Gemini API Key provided for images. Using Pollinations...")

        # 2. Fallback: Pollinations.ai
        return self._generate_via_pollinations(prompt, save_path)

    def _generate_via_pollinations(self, prompt: str, save_path: str) -> bool:
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"{self.pollinations_base_url}{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
            print(f"Downloading fallback image from: {url}")
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"Pollinations fallback failed: {e}")
            return False
