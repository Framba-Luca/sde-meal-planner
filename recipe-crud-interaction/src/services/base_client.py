import requests
from typing import Optional, Dict, Any
from src.core.config import settings

class BaseInternalClient:
    
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.INTERNAL_SERVICE_SECRET}",
            "Content-Type": "application/json"
        }

    def _req(self, method: str, url: str, json: Optional[Dict] = None, params: Optional[Dict] = None) -> Any:

        try:
            method = method.upper()
            timeout = 10 
            
            response = None

            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=json, timeout=timeout)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=json, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=timeout)
            else:
                print(f"Metodo HTTP non supportato: {method}")
                return None
            
            if response.status_code == 404:
                return None
            
            if response.status_code == 204:
                return True

            response.raise_for_status()

            return response.json()
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error calling {url}: {e}")
            return {"error": str(e)}
            
        except requests.exceptions.ConnectionError:
            print(f"Connection Error: Impossible to reach {url}")
            return {"error": "Service Unavailable"}
            
        except requests.exceptions.Timeout:
            print(f"Timeout Error calling {url}")
            return {"error": "Service Timeout"}
            
        except Exception as e:
            print(f"Generic Error calling Internal Service: {e}")
            return None