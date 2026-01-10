import requests
import json
import os

class LinkedInClient:
    def __init__(self, access_token: str, author_urn: str):
        """
        access_token: LinkedIn OAuth2 Access Token
        author_urn: Should be in format 'urn:li:person:XXXX' (JNVW-03WF1)
        """
        self.access_token = access_token
        self.author_urn = author_urn
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json; charset=utf-8',
            'LinkedIn-Version': '202501',
            'X-Restli-Protocol-Version': '2.0.0'
        }

    def register_image(self) -> dict:
        """Step 1: Register image upload using REST API /rest/images"""
        # Ensure author is in person format for REST API
        owner_urn = self.author_urn
        
        # REST API v202501 requires 'urn:li:person' for member profiles
        if "urn:li:member:" in owner_urn:
            owner_urn = owner_urn.replace("urn:li:member:", "urn:li:person:")

        data = {
            "initializeUploadRequest": {
                "owner": owner_urn
            }
        }
        
        response = requests.post(
            "https://api.linkedin.com/rest/images?action=initializeUpload", 
            headers=self.headers, 
            json=data
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to register image upload: {response.text}")
            
        return response.json()

    def upload_image(self, upload_url: str, file_path: str):
        """Step 2: Upload binary file directly to LinkedIn's storage"""
        with open(file_path, 'rb') as f:
            response = requests.put(
                upload_url, 
                data=f, 
                headers={"Content-Type": "application/octet-stream"}
            )
            
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload image binary: {response.text}")

    def _escape_linkedin_text(self, text: str) -> str:
        """
        LinkedIn's /rest/posts API has a known bug where it truncates text 
        at special characters like ( ) [ ] { } etc.
        This helper escapes them to prevent truncation.
        """
        # List of characters known to cause issues in some LinkedIn API versions
        special_chars = ['(', ')', '[', ']', '{', '}', '<', '>', '@', '|', '~', '_']
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text

    def create_post(self, text: str, image_urn: str = None) -> str:
        """Step 3: Create the Post using /rest/posts (2025 Standard)"""
        
        # Ensure author uses person URN
        author_urn = self.author_urn
        if "urn:li:member:" in author_urn:
            author_urn = author_urn.replace("urn:li:member:", "urn:li:person:")

        # 1. Normalize text to prevent truncation bugs
        # Replace Windows line endings (\r\n) with Unix (\n)
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Replace problematic unicode dashes
        text = text.replace('—', '-').replace('–', '-')
        
        # 2. Fix known LinkedIn API bugs by escaping special characters
        text = self._escape_linkedin_text(text)
        
        # 3. Hard Limit Check: LinkedIn maximum is 3000 chars for commentary
        # Use a safe margin for JSON encoding
        if len(text) > 3000:
            print(f"Warning: Text too long ({len(text)}). Truncating to 2900.")
            text = text[:2900] + "... [Full post on profile]"

        post_data = {
            "author": author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }

        if image_urn:
            post_data['content'] = {
                "media": {
                    "title": "Daily Logistics Insight",
                    "id": image_urn
                }
            }

        # DEEP DEBUG: Log everything before sending
        import sys
        print(f"\n[DEEP DEBUG] TEXT PREVIEW (Total {len(text)} chars):")
        print("-" * 40)
        print(f"START: {text[:500]}")
        print("...")
        print(f"END: {text[-500:]}")
        print("-" * 40)
        
        # Explicitly encode to UTF-8
        payload = json.dumps(post_data, ensure_ascii=False).encode('utf-8')
        
        # Add explicit Content-Length
        current_headers = self.headers.copy()
        current_headers['Content-Length'] = str(len(payload))
        
        print(f"[DEEP DEBUG] JSON Payload size: {len(payload)} bytes")
        sys.stdout.flush()
        
        response = requests.post(
            "https://api.linkedin.com/rest/posts",
            headers=current_headers,
            data=payload
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to publish post: {response.text}")
            
        # REST API returns 201 Created with EMPTY body. 
        # The Post ID is in the 'x-restli-id' header.
        post_id = response.headers.get('x-restli-id')
        if not post_id:
             # Fallback to x-linkedin-id just in case
             post_id = response.headers.get('x-linkedin-id', 'Unknown ID')

        return post_id

    def post_image_and_text(self, text: str, image_file_path: str):
        # 1. Register Image (New REST Way)
        print("Registering image via REST API...")
        reg_info = self.register_image()
        upload_url = reg_info['value']['uploadUrl']
        image_urn = reg_info['value']['image']
        
        # 2. Upload Binary
        print(f"Uploading image binary...")
        self.upload_image(upload_url, image_file_path)
        
        # 3. Create Post
        print(f"Publishing post with image {image_urn}...")
        post_id = self.create_post(text, image_urn)
        print(f"Successfully posted! ID: {post_id}")
        return post_id
