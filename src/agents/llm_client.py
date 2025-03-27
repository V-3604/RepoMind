"""
LLM client module.
Provides interface to interact with LLMs for generating text and answering queries.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
import requests

from config import LLM_API_KEY, LLM_API_URL, LLM_MODEL


class LLMClient:
    """Client for interacting with Language Model APIs."""
    
    def __init__(self, 
                 api_key: str = LLM_API_KEY, 
                 api_url: str = LLM_API_URL,
                 model: str = LLM_MODEL):
        """
        Initialize the LLM client.
        
        Args:
            api_key: API key for the language model service
            api_url: API endpoint URL
            model: Model identifier
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        
        if not self.api_key:
            self.logger.warning("No API key provided for LLM client. Some features may not work.")
    
    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.3) -> str:
        """
        Generate text using the language model.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more creative)
            
        Returns:
            str: Generated text
        """
        if not self.api_key:
            self.logger.error("Cannot generate text: No API key provided")
            return "Error: LLM API key not configured"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                self.logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return f"Error: API request failed with status {response.status_code}"
            
            result = response.json()
            
            # Extract the generated text
            generated_text = result["choices"][0]["message"]["content"]
            return generated_text
        
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    def generate_code(self, prompt: str, language: str = "", max_tokens: int = 1000, temperature: float = 0.2) -> str:
        """
        Generate code using the language model.
        
        Args:
            prompt: Input prompt describing the code to generate
            language: Programming language for the generated code
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more creative)
            
        Returns:
            str: Generated code
        """
        # Add language-specific instructions to the prompt
        if language:
            prompt = f"Generate {language} code for the following request:\n\n{prompt}"
        else:
            prompt = f"Generate code for the following request:\n\n{prompt}"
        
        # Add instructions to return only code
        prompt += "\n\nReturn only the code without explanations or commentary."
        
        return self.generate_text(prompt, max_tokens, temperature)
    
    def answer_question(self, 
                       question: str, 
                       context: Optional[List[Dict[str, str]]] = None, 
                       max_tokens: int = 500, 
                       temperature: float = 0.3) -> Dict[str, str]:
        """
        Answer a question based on provided context.
        
        Args:
            question: Question to answer
            context: List of context items (file contents, summaries, etc.)
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            
        Returns:
            dict: Answer with references
        """
        prompt = f"Question: {question}\n\n"
        
        # Add context if provided
        if context:
            prompt += "Context:\n"
            for i, item in enumerate(context):
                prompt += f"[{i+1}] {item.get('title', 'Item ' + str(i+1))}\n"
                prompt += f"{item.get('content', '')}\n\n"
        
        prompt += """
        Using the provided context (if any), please answer the question.
        If the question cannot be answered based on the context, say so.
        If code examples would be helpful, include them.
        
        Format your answer as follows:
        
        Answer: <your detailed answer>
        
        References: <list any specific parts of the context you used>
        """
        
        response = self.generate_text(prompt, max_tokens, temperature)
        
        # Parse the response to extract answer and references
        try:
            answer_part = response.split("Answer:")[1].split("References:")[0].strip()
        except IndexError:
            answer_part = response.strip()
        
        try:
            references_part = response.split("References:")[1].strip()
        except IndexError:
            references_part = ""
        
        return {
            "text": answer_part,
            "references": references_part
        }
    
    def batch_generate(self, prompts: List[str], max_tokens: int = 500, temperature: float = 0.3) -> List[str]:
        """
        Generate text for multiple prompts.
        
        Args:
            prompts: List of prompts
            max_tokens: Maximum tokens per response
            temperature: Sampling temperature
            
        Returns:
            list: List of generated responses
        """
        responses = []
        
        # Simple approach: process sequentially with rate limiting
        for i, prompt in enumerate(prompts):
            if i > 0:
                # Add a small delay to avoid hitting API rate limits
                time.sleep(1)
            
            response = self.generate_text(prompt, max_tokens, temperature)
            responses.append(response)
        
        return responses 