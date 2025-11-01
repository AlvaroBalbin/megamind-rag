# here we create a little wrapper for the llm that will be used
# its modular so you can swap out the llm quite easily

# each has its own API so this abstraction layer can remove that mess
# making it simpler to work with

# CURRENTLY this is a stub -> just returns a placeholder for now
# havent decided what LLM to use

import os 

class LLMProvider:
    """thin wrapper to swap out easily different LLMs"""

    def __init__(self, model_name: str="gpt-4o-mini", api_key: str = None, base_url: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        # call client and other stuff
        if self.api_key is None:
            raise ValueError("OPEN_API_KEY is not set in this environment")
        
        self.base_url = base_url or os.getenv("OPEN_API_KEY", "https://api.openai.com")

    def generate_answer(self, prompt: str) -> str:
        """call actual LLM here, send a prompt to the API, wait for a response,
        extract the models answer from JSON that is returned, return it as plain text"""
        return "LLM output placeholder"
    
        # api endpoint where we'll send the question
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-type": "applicaton/json",
        }

        # defining what we send
        payload = {
            "model": self.model_name,
            "messages": [ # might add other parameters like max_output_token or reasoning
                {
                "role": "developer",
                "content": prompt, 
                },
            ],
                "temperature": 0.1, # how random the model's text generation 
        }

        # send post
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        # check if there were any issues by checking status
        resp.raise_for_status()

        data = resp.json() # get data into json format

        # attempt to extract data text
        try:
            return data["choices"][0]["message"]["content"].strip() # usually there only one choice anyway
        except Exception as e:
            return "[LLM Provider] error occured in loading text: e"
    
