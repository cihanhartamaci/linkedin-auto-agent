import requests
import json
import os

class LinkedInClient:
    def __init__(self, access_token: str, author_urn: str):
        self.access_token = access_token
        self.author_urn = author_urn
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        self.api_url = "https://api.linkedin.com/v2"

    def register_image(self) -> dict:
        """Register image using V2 Assets API"""
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
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, data=f, headers={"Content-Type": "application/octet-stream"})
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload image binary: {response.text}")

    def create_post(self, text: str, image_urn: str = None) -> str:
        """Create post using V2 ugcPosts API (Most stable for members)"""
        post_data = {
            "author": self.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
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
                "description": {"text": "Logistics Insight"},
                "media": image_urn,
                "title": {"text": "Daily Content"}
            }]

        response = requests.post(f"{self.api_url}/ugcPosts", headers=self.headers, json=post_data)
        if response.status_code != 201:
            raise Exception(f"Failed to publish post: {response.text}")
        return response.json().get('id', 'Unknown ID')

    def post_image_and_text(self, text: str, image_file_path: str):
        reg_info = self.register_image()
        upload_url = reg_info['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = reg_info['value']['asset']
        self.upload_image(upload_url, image_file_path)
        return self.create_post(text, asset_urn)
