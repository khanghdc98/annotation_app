import requests
import os 
from constant import base_path

class RestClient:
    _instance = None  # Private class attribute to store the single instance

    def __new__(cls, base_url=None):
        if cls._instance is None:
            if base_url is None:
                raise ValueError("First instantiation requires a base_url.")
            cls._instance = super(RestClient, cls).__new__(cls)
            cls._instance.base_url = base_url  # Set the base URL only once
        return cls._instance

    def send_annotation(self, image_name, no_return_records):
        url = f"{self.base_url}/get_similar"  # Adjust endpoint as needed
        payload = {"image_id": image_name, "no_return_records": no_return_records}  # Fix key

        try:
            response = requests.get(url, params=payload, timeout=5)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            data = response.json()  # Convert response to JSON first
            print("Response:", data)
            data = data['data']
            print("Response:", data)

            # Append base_path to each response item if needed
            for i in range(len(data)):
                data[i] = os.path.join(base_path, data[i])  
                

            return data
        except requests.exceptions.RequestException as e:
            print(f"Error sending annotation: {e}")
            return None