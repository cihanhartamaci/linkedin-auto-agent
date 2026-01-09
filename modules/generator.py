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
        Act as a Logistics Technology Thought Leader.
        
        Task 1: Randomly select a specific, niche, and interesting sub-topic based on these categories: [{context_cats}].
        
        Task 2: Write a high-quality "Short Article" style LinkedIn post (300-500 words) about that specific selected topic.
        - Structure: 
            1. Strong Hook Headline (Use only text, no markdown #)
            2. The Problem/Context (Deep insight into industry challenges)
            3. The Solution/Innovation (Technical depth)
            4. Strategic Takeaway/Call to Action.
        - Tone: Professional, authoritative, yet accessible. Avoid generic AI fluff.
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
            
            # Formatting: Convert Markdown **Bold** to Unicode Bold for LinkedIn
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
        Converts markdown **bold** syntax to Unicode bold characters 
        which are supported by LinkedIn plain text posts.
        """
        normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
        mapping = str.maketrans(normal, bold)
        
        import re
        def replace(match):
            return match.group(1).translate(mapping)
            
        return re.sub(r'\*\*(.*?)\*\*', replace, text)
