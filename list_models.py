import os
import google.generativeai as genai

# Configure your API key
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# List available models
models = genai.list_models()
for model in models:
    print(f"Model Name: {model.name}, Supported Methods: {model.supported_methods}")
