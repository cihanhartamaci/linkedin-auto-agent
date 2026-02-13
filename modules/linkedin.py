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
            'LinkedIn-Version': '202511',
            'X-Restli-Protocol-Version': '2.0.0'
        }

    def register_image(self) -> dict:
        """Step 1: Register image upload using v2/assets API"""
        # Ensure author is in person format for v2 API
        owner_urn = self.author_urn
        
        # v2 API uses urn:li:person or urn:li:organization
        if "urn:li:member:" in owner_urn:
            owner_urn = owner_urn.replace("urn:li:member:", "urn:li:person:")

        data = {
            "registerUploadRequest": {
                "recipes": [
                    "urn:li:digitalmediaRecipe:feedshare-image"
                ],
                "owner": owner_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        
        response = requests.post(
            "https://api.linkedin.com/v2/assets?action=registerUpload", 
            headers=self.headers, 
            json=data
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to register image upload: {response.text}")
            
        return response.json()

    def upload_image(self, upload_url: str, image_path: str):
        """Step 2: Upload binary image data"""
        with open(image_path, "rb") as f:
            image_data = f.read()
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        # v2/assets uploadUrl is usually a single URL
        response = requests.put(upload_url, headers=headers, data=image_data)
        
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

    def create_post(self, text: str, asset_urn: str = None) -> str:
        """Step 3: Create the Post using v2/ugcPosts (Compatible with v2/assets)"""
        
        # Ensure author uses person URN
        author_urn = self.author_urn
        if "urn:li:member:" in author_urn:
            author_urn = author_urn.replace("urn:li:member:", "urn:li:person:")

        # 1. Normalize text to prevent truncation bugs
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('—', '-').replace('–', '-')
        text = self._escape_linkedin_text(text)
        
        if len(text) > 3000:
            print(f"Warning: Text too long ({len(text)}). Truncating to 2900.")
            text = text[:2900] + "... [Full post on profile]"

        # Construct v2/ugcPosts payload
        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        if asset_urn:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "description": {
                        "text": "Image from LinkedIn Automation"
                    },
                    "media": asset_urn,
                    "title": {
                        "text": "LinkedIn Post Image"
                    }
                }
            ]

        # DEEP DEBUG: Log everything before sending
        import sys
        print(f"\n[DEEP DEBUG] TEXT PREVIEW (Total {len(text)} chars):")
        print("-" * 40)
        print(f"START: {text[:500]}")
        print("...")
        print(f"END: {text[-500:]}")
        print("-" * 40)
        
        payload = json.dumps(post_data, ensure_ascii=False).encode('utf-8')
        
        current_headers = self.headers.copy()
        current_headers['Content-Length'] = str(len(payload))
        
        # v2/ugcPosts doesn't strictly need LinkedIn-Version, but it's safer to keep or remove if issues arise.
        # We'll use the existing headers for now.
        
        print(f"[DEEP DEBUG] JSON Payload size: {len(payload)} bytes")
        sys.stdout.flush()
        
        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=current_headers,
            data=payload
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to publish post: {response.text}")
            
        post_id = response.json().get('id')
        return post_id

    def post_image_and_text(self, text: str, image_file_path: str):
        # 1. Register Image (v2/assets Way)
        print("Registering image via v2/assets API...")
        reg_info = self.register_image()
        
        # Parse v2/assets response
        try:
            upload_url = reg_info['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset_urn = reg_info['value']['asset']
        except KeyError:
             print(f"Unexpected response structure: {reg_info}")
             raise Exception("Could not parse upload URL or Asset URN from v2/assets response")
        
        # 2. Upload Binary
        print(f"Uploading image binary to {upload_url[:50]}...")
        self.upload_image(upload_url, image_file_path)
        
        # 3. Create Post
        print(f"Publishing post with asset {asset_urn}...")
        post_id = self.create_post(text, asset_urn)
        print(f"Successfully posted! ID: {post_id}")
        return post_id
