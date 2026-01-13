from google import genai
from google.genai import types
from duckduckgo_search import DDGS
import requests
import os

class ImageProvider:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_and_save(self, prompt: str, save_path: str) -> bool:
        """
        Attempts to generate image via Gemini (Imagen 3). 
        Falls back to DuckDuckGo image search if Gemini is unavailable or fails.
        """
        # 1. Try Gemini (Imagen 3)
        if self.client:
            # Try standard Stable ID and the preferred Preview ID
            image_models = ["imagen-3.0-generate-001", "nano-banana-pro-preview"]
            for model_id in image_models:
                try:
                    print(f"Attempting image generation via Gemini: {model_id}...")
                    response = self.client.models.generate_images(
                        model=model_id,
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
                        print(f"Successfully generated image via Gemini ({model_id}).")
                        return True
                    else:
                        print(f"Gemini ({model_id}) returned no images.")
                except Exception as e:
                    print(f"Gemini image generation ({model_id}) failed: {e}")
                    continue
        else:
            print("No Gemini API Key provided for images. Using DuckDuckGo Search...")

        # 2. Fallback: DuckDuckGo Image Search
        return self._search_via_duckduckgo(prompt, save_path)

    def _search_via_duckduckgo(self, prompt: str, save_path: str) -> bool:
        """
        Searches for a real-world image on DuckDuckGo and downloads it.
        """
        try:
            print(f"Searching DuckDuckGo for: {prompt[:100]}...")
            with DDGS() as ddgs:
                # Search for high-quality, professional images
                results = list(ddgs.images(
                    keywords=prompt,
                    region="wt-wt",
                    safesearch="on",
                    size="Large",
                    type_image="photo"
                ))
            
            if not results:
                print("No images found on DuckDuckGo.")
                return False
            
            # Try the first few results in case one fails to download
            for result in results[:5]:
                try:
                    img_url = result['image']
                    print(f"Downloading image from: {img_url}")
                    response = requests.get(img_url, timeout=15)
                    if response.status_code == 200:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Successfully downloaded image from DuckDuckGo.")
                        return True
                except Exception as e:
                    print(f"Failed to download from {img_url}: {e}")
                    continue
            
            return False
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            return False
