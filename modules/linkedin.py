import requests
import json
import os

class LinkedInClient:
    def __init__(self, access_token: str, author_urn: str):
        """
        access_token: LinkedIn OAuth2 Access Token
        author_urn: 'urn:li:person:MVPdF8A...' or 'urn:li:organization:1234'
        """
        self.access_token = access_token
        self.author_urn = author_urn
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        self.api_url = "https://api.linkedin.com/v2"

    def register_image(self) -> dict:
        """Step 1: Register upload to get URL"""
        data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": self.author_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }
        
        response = requests.post(f"{self.api_url}/assets?action=registerUpload", headers=self.headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Failed to register upload: {response.text}")
            
        return response.json()

    def upload_image(self, upload_url: str, file_path: str):
        """Step 2: Upload binary file"""
        with open(file_path, 'rb') as f:
            # Note: No Authorization header for the upload URL usually, but standard requests handles it 
            # if we just pass the binary. SAS URL usually includes auth token in query.
            # We must NOT send the Bearer token to the AWS/Azure upload URL.
            response = requests.put(upload_url, data=f, headers={"Content-Type": "application/octet-stream"})
            
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload image binary: {response.text}")

    def create_post(self, text: str, image_urn: str = None) -> str:
        """Step 3: Create the UGC Post"""
        
        # Convert urn:li:member to urn:li:person if needed
        # LinkedIn UGC API sometimes requires person URN for personal profiles
        author_urn_for_post = self.author_urn
        if "urn:li:member:" in self.author_urn:
            member_id = self.author_urn.split(":")[-1]
            author_urn_for_post = f"urn:li:person:{member_id}"
            print(f"Converting member URN to person URN: {author_urn_for_post}")
        
        post_data = {
            "author": author_urn_for_post,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE" if not image_urn else "IMAGE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        if image_urn:
            post_data['specificContent']['com.linkedin.ugc.ShareContent']['media'] = [{
                "status": "READY",
                "description": {"text": "Generated Image"},
                "media": image_urn,
                "title": {"text": "Content Image"}
            }]

        response = requests.post(f"{self.api_url}/ugcPosts", headers=self.headers, json=post_data)
        
        if response.status_code != 201:
            raise Exception(f"Failed to publish post: {response.text}")
            
        return response.json().get('id', 'Unknown ID')

    def post_image_and_text(self, text: str, image_file_path: str):
        # 1. Register
        reg_info = self.register_image()
        upload_url = reg_info['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = reg_info['value']['asset']
        
        # 2. Upload
        print(f"Uploading image to {upload_url[:50]}...")
        self.upload_image(upload_url, image_file_path)
        
        # 3. Post
        print(f"Publishing post with asset {asset_urn}...")
        post_id = self.create_post(text, asset_urn)
        print(f"Successfully posted! ID: {post_id}")
        return post_id
