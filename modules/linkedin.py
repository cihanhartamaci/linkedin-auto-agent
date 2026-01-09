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
        """Step 3: Create Post using new REST API"""
        
        # New LinkedIn REST API format (supports member posting!)
        post_data = {
            "author": self.author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }

        if image_urn:
            post_data['content'] = {
                "media": {
                    "title": "Generated Content",
                    "id": image_urn
                }
            }


        # Use new REST API endpoint (base URL is different for REST API)
        headers_for_rest = self.headers.copy()
        # Specifying a modern version (202501)
        headers_for_rest['LinkedIn-Version'] = '202501'
        
        # REST API uses https://api.linkedin.com/rest/* not /v2/rest/*
        rest_api_url = "https://api.linkedin.com/rest/posts"
        
        response = requests.post(
            rest_api_url,
            headers=headers_for_rest,
            json=post_data
        )
        
        if response.status_code not in [200, 201]:
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
