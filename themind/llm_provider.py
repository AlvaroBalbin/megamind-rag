# here we create a little wrapper for the llm that will be used
# its modular so you can swap out the llm quite easily

# each has its own API so this abstraction layer can remove that mess
# making it simpler to work with

# CURRENTLY this is a stub -> just returns a placeholder for now
# havent decided what LLM to use
class LLMProvider:
    """thin wrapper to swap out easily different LLMs"""

    def __init__(self, model_name: str="gpt-4o-mini"):
        self.model_name = model_name
        # call client and other stuff

    def generate_answer(self, prompt: str) -> str:
        """call actual LLM here, for now return placeholder"""
        return "LLM output placeholder"
    
    