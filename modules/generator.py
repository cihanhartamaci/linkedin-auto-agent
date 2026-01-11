import os
import random
from google import genai
from typing import Dict

class ContentGenerator:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API Key is required")
        
        self.client = genai.Client(api_key=api_key)
        # Using nano-banana-pro-preview
        self.model_name = "nano-banana-pro-preview"
        
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
        Act as a Senior Logistics Systems Consultant with 20 years of experience. You are known for your direct, slightly skeptical, and highly technical perspective.
        
        Task 1: Select a specific, complex sub-topic from: [{context_cats}]. Pick something non-obvious (e.g., skip 'What is WMS', choose 'Deadlock resolution in automated sortation').
        
        Task 2: Write a high-quality LinkedIn post (MAX 280 words).
        - **VOICE**: Direct, professional, and zero-fluff. Write like you're talking to a peer, not a student.
        - **FORBIDDEN**: Do NOT use AI clichés like "In today's fast-paced world", "Unlocking potential", "Delve into", "The key to success is...", "Imagine a world...".
        - **STYLE**: Start with a hard statement or a technical "hot take." Use short paragraphs. Use bullet points for technical specs if needed.
        - **LIMIT**: Total length MUST be under 1900 characters.
        - Structure: 
            1. **The Hook** (A technical observation or a common industry failure).
            2. **The Reality Check** (Why traditional methods are failing in the field).
            3. **Brief Technical Insight** (One solid piece of advice or a specific API/EDI pattern).
            4. **The Closing Thought** (A question for the reader's own experience).
            5. Relevant Hashtags (2 empty lines before them).
        - Formatting: Use **double asterisks** for emphasis on critical technical terms only (max 5-6 per post).
        
        Task 3: Write a sophisticated, hyper-realistic image prompt (max 50 words).
        - **GOAL**: The image must look like a professional, high-end photograph or a crisp technical render. **Strictly NO paintings, illustrations, or artistic brushstrokes.**
        - **RANDOM STYLE**: For every post, choose a DIFFERENT technical style from this list: [High-End Product Photography, Cinematic Industrial Interior, Macro Technical Detail, Schematic 3D Visualization, High-Tech Server Room Aesthetic, Minimalist Tech Laboratory, Futuristic Logistics Hub].
        - **KEYWORDS**: Use "Hyper-realistic, 8k, photorealistic, sharp focus, depth of field, industrial lighting, ray-tracing, clean technical aesthetic."
        - **COMPOSITION**: Specify an interesting angle (e.g., "Macro close-up with bokeh", "Cinematic wide-angle view", "Isometric technical schematic").
        - **CONTENT**: Must be a technical representation of the post topic (e.g., automated scanners, server racks, conveyor sensors, data dashboards). No people.
        
        Output Format (STRICT):
        [TOPIC_START]
        Topic Title
        [TOPIC_END]
        [POST_START]
        Post content
        [POST_END]
        [IMAGE_PROMPT_START]
        Image prompt
        [IMAGE_PROMPT_END]
        """
        
        # Priority list of models (User preference first, then working previews, then stable)
        model_fallbacks = [
            "nano-banana-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash-latest"
        ]
        
        last_exception = None
        for current_model in model_fallbacks:
            try:
                print(f"Generating content with model: {current_model}...")
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=prompt
                )
                content = response.text.strip()
                # If we got here, it worked. Break the loop.
                break
            except Exception as e:
                print(f"Model {current_model} failed: {e}")
                last_exception = e
                continue
        else:
            # If the loop finished without breaking
            raise Exception(f"All models failed. Last error: {last_exception}")
            
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

    def _convert_markdown_bold(self, text: str) -> str:
        """
        Smart Unicode bold conversion:
        - Phrases with 20 words or less: Convert to Unicode bold
        - Longer phrases: Just strip ** markers
        """
        import re
        
        def smart_replace(match):
            content = match.group(1)
            # Remove existing bold if it's already unicode (unlikely but safe)
            word_count = len(content.split())
            
            if word_count <= 20: 
                normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
                mapping = str.maketrans(normal, bold)
                return content.translate(mapping)
            return content
        
        return re.sub(r'\*\*(.*?)\*\*', smart_replace, text)
