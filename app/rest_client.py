import requests
import os 
from constant import base_path
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

class RestClient:
    _instance = None  # Private class attribute to store the single instance

    user_id = os.getenv('USER_ID')  # Public instance attribute to store the user ID

    def __new__(cls, base_url=None):
        if cls._instance is None:
            if base_url is None:
                raise ValueError("First instantiation requires a base_url.")
            cls._instance = super(RestClient, cls).__new__(cls)
            cls._instance.base_url = base_url  # Set the base URL only once
        return cls._instance

    def get_similars(self, image_name, no_return_records):
        url = f"{self.base_url}/get_similar"  # Adjust endpoint as needed
        payload = {"image_id": image_name, "no_return_records": no_return_records}  # Fix key

        response = requests.get(url, params=payload, timeout=5)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()  # Convert response to JSON first
        data = data['data']

        # Append base_path to each response item if needed
        for i in range(len(data)):
            data[i] = os.path.join(base_path, data[i])  
            

        return data
    
    def send_annotated_data(self, annotated_images, session_id=None):
        if session_id is None:
            session_id = self.user_id
        url = f"{self.base_url}/send_annotated_data"
        payload = {"session_id": session_id, "annotated_images": annotated_images}

        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            return True
        else:
            print(response.text)
            return False
        
    def clear_session(self, session_id=None):
        if session_id is None:
            session_id = self.user_id
        url = f"{self.base_url}/clear_session"
        payload = {"session_id": session_id}

        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            return True
        else:
            print(response.text)
            return False
        
    def send_accepted_data(self, accepted_images, session_id=None):
        if session_id is None:
            session_id = self.user_id
        url = f"{self.base_url}/send_accepted_data"
        payload = {"session_id": session_id, "accepted_images": accepted_images}

        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            return True
        else:
            print(response.text)
            return False
    