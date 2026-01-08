import os
import random
from google import genai
from typing import Dict

class ContentGenerator:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API Key is required")
        
        self.client = genai.Client(api_key=api_key)
        # Switching to gemini-flash-latest to avoid 2.0-flash quota limits
        self.model_name = "gemini-flash-latest"
        
    def generate_full_content(self) -> Dict[str, str]:
        """
        Generates Topic, Post, and Image Prompt in a single API call to avoid 429 Rate Limits.
        """
        categories = [
            "Warehouse Management Systems (WMS)",
            "Fulfillment Management Systems (FMS)", 
            "Electronic Data Interchange (EDI)",
            "API Integration in Logistics",
            "Supply Chain Automation"
        ]
        
        # We give the LLM the list and ask IT to pick one and expand on it.
        context_cats = ", ".join(categories)
        
        prompt = f"""
        Act as a Logistics Technology Expert.
        
        Task 1: Randomly select a specific, niche, and interesting sub-topic based on these categories: [{context_cats}].
        
        Task 2: Write a professional, insightful LinkedIn post in English about that specific selected topic.
        - Structure: Hook -> Insight -> Call to Action.
        - Tone: Professional but engaging.
        - Length: ~150-200 words.
        
        Task 3: Write a short image generation prompt (max 40 words) that describes a modern, photorealistic image for this post.
        
        Output Format (STRICT):
        [TOPIC_START]
        ...write the selected topic title here...
        [TOPIC_END]
        [POST_START]
        ...write the post text here...
        [POST_END]
        [IMAGE_PROMPT_START]
        ...write the image prompt here...
        [IMAGE_PROMPT_END]
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            content = response.text.strip()
            
            # Helper to extract content between tags
            def extract(tag_start, tag_end, text):
                try:
                    return text.split(tag_start)[1].split(tag_end)[0].strip()
                except IndexError:
                    return ""

            topic = extract("[TOPIC_START]", "[TOPIC_END]", content)
            post_text = extract("[POST_START]", "[POST_END]", content)
            image_prompt = extract("[IMAGE_PROMPT_START]", "[IMAGE_PROMPT_END]", content)
            
            # Fallbacks if parsing fails (rare with strict prompting)
            if not topic: topic = "Logistics Tech Update"
            if not post_text: post_text = content # If tags missing, assume whole text is post
            if not image_prompt: image_prompt = f"Futuristic logistics technology visualization related to {topic}"

            return {
                "topic": topic,
                "text": post_text,
                "image_prompt": image_prompt
            }
            
        except Exception as e:
            print(f"Error during generation: {e}")
            raise Exception(f"Failed to generate content. Please check quota or keys.")
