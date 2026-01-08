import requests
import urllib.parse
import os

class ImageProvider:
    def __init__(self):
        # Pollinations.ai is a free, URL-based generation service
        self.base_url = "https://image.pollinations.ai/prompt/"

    def generate_and_save(self, prompt: str, save_path: str) -> bool:
        """
        Generates an image from the prompt and saves it to save_path.
        Returns True if successful.
        """
        try:
            # Encode prompt for URL
            encoded_prompt = urllib.parse.quote(prompt)
            # Add parameters for better quality/style
            url = f"{self.base_url}{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
            
            print(f"Downloading image from: {url}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Ensure directory exists
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"Failed to download image. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error generating image: {e}")
            return False
