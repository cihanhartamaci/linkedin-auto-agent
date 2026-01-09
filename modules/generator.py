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
        Act as a Senior Integration Developer & Logistics Tech Expert (Specializing in API, EDI, ERP).
        
        Task 1: Randomly select a specific, niche, and interesting sub-topic based on these categories: [{context_cats}].
        
        Task 2: Write a high-quality "Short Article" style LinkedIn post (300-500 words) about that specific selected topic.
        - **PERSPECTIVE**: Write as an expert sharing knowledge. **DO NOT** make up fake stories like "In my recent project..." or "I built X...". instead, say "Have you ever noticed..." or "A common mistake is...".
        - **STYLE**: Informative, educational, and engaging. Use **Rhetorical Questions** to guide the reader.
        - Structure: 
            1. **The provocative question** (Start with a question that makes a developer/CTO think).
            2. **The Deep Dive** (Explain the concept/problem technically. Why does this existing standard fail? What is the modern approach?).
            3. **The 'What If'** (Ask a question about the reader's current stack/approach).
            4. **Strategic Advice** (Solid, actionable recommendation).
            5. Relevant Hashtags (Ensure there are 2 empty lines before the hashtags).
        - Tone: Senior, consultative, inquisitive. Not boasting, but teaching/discussing.
        - Formatting: Use **double asterisks** for ANY key phrases or headlines you want to be BOLD. My code will convert them to real bold text.
        
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
            
            # Formatting: Strip Markdown **markers** (LinkedIn doesn't support formatting)
            post_text = self._convert_markdown_bold(post_text)

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

    def _convert_markdown_bold(self, text: str) -> str:
        """
        Simply removes **markdown** markers from text.
        LinkedIn doesn't support formatting, so we keep it clean.
        """
        import re
        return re.sub(r'\*\*(.*?)\*\*', r'\1', text)
