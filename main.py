import os
import argparse
from datetime import datetime
from dotenv import load_dotenv

from modules.generator import ContentGenerator
from modules.image_provider import ImageProvider
from modules.linkedin import LinkedInClient

# Load environment variables
load_dotenv()

def generate_draft():
    print("Initializing Generator...")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("Error: GEMINI_API_KEY not found in env.")
        exit(1)

    generator = ContentGenerator(gemini_key)
    image_provider = ImageProvider()
    
    # 1. Generate Topic & Text & Image Prompt (Single Call)
    print("Generating full content (Topic + Text + Image Prompt)...")
    content = generator.generate_full_content()
    
    print(f"Selected Topic: {content['topic']}")
    
    # 2. Generate Image
    print("Generating image...")
    # Clean filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    draft_dir = os.path.join(os.getcwd(), "drafts")
    os.makedirs(draft_dir, exist_ok=True)
    
    image_path = os.path.join(draft_dir, f"image_{date_str}.png")
    text_path = os.path.join(draft_dir, f"post_{date_str}.md")
    
    success = image_provider.generate_and_save(content['image_prompt'], image_path)
    if not success:
        print("Warning: Image generation failed. Proceeding with text only.")
    
    # 3. Save Draft
    # Sanitize YAML strings: Escape quotes and wrap in quotes to handle colons
    safe_topic = content['topic'].replace('"', '\\"')
    safe_prompt = content['image_prompt'].replace('"', '\\"')
    
    formatted_text = f"""---
topic: "{safe_topic}"
image_prompt: "{safe_prompt}"
---
{content['text']}
"""
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(formatted_text)
        
    print(f"Draft saved to:\n- {text_path}\n- {image_path}")
    
    # For GitHub Actions output (if needed)
    print(f"::set-output name=draft_text_path::{text_path}")
    print(f"::set-output name=draft_image_path::{image_path}")

def publish_post(draft_date=None):
    if not draft_date:
        draft_date = datetime.now().strftime("%Y-%m-%d")
        
    text_path = os.path.join("drafts", f"post_{draft_date}.md")
    image_path = os.path.join("drafts", f"image_{draft_date}.png")
    
    if not os.path.exists(text_path):
        print(f"Error: Draft not found at {text_path}")
        exit(1)
        
    # Read Text (Robust Skip Frontmatter)
    with open(text_path, 'r', encoding="utf-8") as f:
        content = f.read()
        
    print(f"File total length: {len(content)} chars")
    
    # Use regex to find frontmatter more reliably
    import re
    # Match from start, find --- and another ---
    match = re.split(r'^---.*?\n---\s*', content, flags=re.DOTALL | re.MULTILINE)
    
    if len(match) > 1:
        # The content after the second ---
        final_text = match[1].strip()
    else:
        # Fallback to the split method if regex fails
        parts = content.split("---", 2)
        if len(parts) >= 3:
            final_text = parts[2].strip()
        else:
            final_text = content
            
    print(f"Final text length to send: {len(final_text)} chars")
    if len(final_text) > 0:
        import sys
        print(f"Content Sample (First 300): {final_text[:300]}")
        print(f"Content Sample (Last 300): {final_text[-300:]}")
        sys.stdout.flush()
    else:
        print("WARNING: Final text is EMPTY!")
        
    # Publish
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")
    
    if not access_token or not author_urn:
        print("Error: LinkedIn Credentials missing.")
        exit(1)
        
    client = LinkedInClient(access_token, author_urn)
    
    if os.path.exists(image_path):
        client.post_image_and_text(final_text, image_path)
    else:
        print("Image not found, posting text only.")
        client.create_post(final_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["draft", "publish"], help="Action to perform")
    parser.add_argument("--date", help="Specific date for publish mode YYYY-MM-DD", default=None)
    
    args = parser.parse_args()
    
    if args.mode == "draft":
        generate_draft()
    elif args.mode == "publish":
        publish_post(args.date)
