"""
LLM client for RepoMind.
Handles communication with various LLM providers.
"""

import os
import json
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional, Union, Literal

from config import LLM_API_KEY, LLM_API_URL, LLM_MODEL, MAX_TOKENS


class LLMClient:
    """Client for interacting with Language Model APIs."""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            api_key: API key for LLM provider (default: from config)
            api_url: API URL for LLM provider (default: from config)
            model: Model to use (default: from config)
        """
        self.api_key = api_key or LLM_API_KEY
        self.api_url = api_url or LLM_API_URL
        self.model = model or LLM_MODEL
        self.logger = logging.getLogger(__name__)
        
        # Detect provider based on URL
        if "openai.com" in str(self.api_url) or not self.api_url:
            self.provider = "openai"
        elif "anthropic.com" in str(self.api_url):
            self.provider = "anthropic"
        else:
            self.provider = "custom"
        
        self.logger.info(f"Initialized LLM client with provider: {self.provider}, model: {self.model}")
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """
        Generate text using the configured LLM.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: Generated text
        """
        try:
            # Call the appropriate provider method
            if self.provider == "openai":
                return self._call_openai_direct(prompt, max_tokens, temperature)
            elif self.provider == "anthropic":
                return self._call_anthropic(prompt, max_tokens, temperature)
            else:
                return self._call_custom(prompt, max_tokens, temperature)
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    async def generate_text_async(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """
        Generate text asynchronously.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: Generated text
        """
        try:
            # Call the appropriate provider method
            if self.provider == "openai":
                return await self._call_openai_direct_async(prompt, max_tokens, temperature)
            elif self.provider == "anthropic":
                return await self._call_anthropic_async(prompt, max_tokens, temperature)
            else:
                return await self._call_custom_async(prompt, max_tokens, temperature)
        except Exception as e:
            self.logger.error(f"Error generating text asynchronously: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    def _call_openai_direct(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """
        Call OpenAI API directly using httpx instead of the OpenAI client.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: Generated text
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant specializing in code analysis and understanding."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            api_endpoint = "https://api.openai.com/v1/chat/completions"
            
            response = httpx.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                    return result["choices"][0]["message"]["content"].strip()
            
            return "No response generated"
                
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    async def _call_openai_direct_async(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """
        Call OpenAI API asynchronously using httpx directly.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: Generated text
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant specializing in code analysis and understanding."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            api_endpoint = "https://api.openai.com/v1/chat/completions"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                        return result["choices"][0]["message"]["content"].strip()
                
                return "No response generated"
                    
        except Exception as e:
            self.logger.error(f"OpenAI API error (async): {str(e)}")
            return f"Error generating text: {str(e)}"
    
    def _call_anthropic(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """
        Call Anthropic API.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: Generated text
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "stop_sequences": ["\n\nHuman:"]
        }
        
        try:
            response = httpx.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["completion"].strip()
            
        except Exception as e:
            self.logger.error(f"Anthropic API error: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    async def _call_anthropic_async(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """
        Call Anthropic API asynchronously.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: Generated text
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "stop_sequences": ["\n\nHuman:"]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result["completion"].strip()
                
        except Exception as e:
            self.logger.error(f"Anthropic API error (async): {str(e)}")
            return f"Error generating text: {str(e)}"
    
    def _call_custom(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """
        Call custom LLM API.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: Generated text
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Generic payload structure - modify based on your API
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = httpx.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the generated text from the response
            # Adjust this based on the actual structure of your API response
            if "text" in result:
                return result["text"].strip()
            elif "generated_text" in result:
                return result["generated_text"].strip()
            elif "output" in result:
                return result["output"].strip()
            else:
                return str(result)
                
        except Exception as e:
            self.logger.error(f"Custom API error: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    async def _call_custom_async(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """
        Call custom LLM API asynchronously.
        
        Args:
            prompt: Prompt to generate text from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation
            
        Returns:
            str: Generated text
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Generic payload structure - modify based on your API
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract the generated text from the response
                # Adjust this based on the actual structure of your API response
                if "text" in result:
                    return result["text"].strip()
                elif "generated_text" in result:
                    return result["generated_text"].strip()
                elif "output" in result:
                    return result["output"].strip()
                else:
                    return str(result)
                    
        except Exception as e:
            self.logger.error(f"Custom API error (async): {str(e)}")
            return f"Error generating text: {str(e)}"
    
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
    
    async def analyze_code(self, 
                          code: str, 
                          language: str, 
                          analysis_type: Literal["summary", "review", "refactor", "explain"] = "summary", 
                          max_tokens: int = 500) -> str:
        """
        Analyze code using LLM.
        
        Args:
            code: Code to analyze
            language: Programming language
            analysis_type: Type of analysis to perform
            max_tokens: Maximum tokens for response
            
        Returns:
            str: Analysis result
        """
        prompt_templates = {
            "summary": """
                Provide a concise summary of the following {language} code:
                
                ```{language}
                {code}
                ```
                
                Focus on:
                1. Main purpose of the code
                2. Key functions/components
                3. Important algorithms or patterns used
                """,
            
            "review": """
                Review the following {language} code and identify potential issues, improvements, 
                or best practices that could be applied:
                
                ```{language}
                {code}
                ```
                
                Focus on:
                1. Bugs or logical errors
                2. Performance issues
                3. Readability and maintainability
                4. Security concerns
                5. Adherence to {language} best practices
                """,
            
            "refactor": """
                Suggest refactoring improvements for the following {language} code:
                
                ```{language}
                {code}
                ```
                
                Focus on:
                1. Code structure and organization
                2. Reducing complexity
                3. Improving performance
                4. Enhancing maintainability
                5. Following {language} best practices
                
                Provide both explanation and refactored code examples.
                """,
            
            "explain": """
                Explain the following {language} code in detail:
                
                ```{language}
                {code}
                ```
                
                Please explain:
                1. What each section does
                2. The purpose of key variables and functions
                3. The overall logic and flow
                4. Any algorithms or design patterns used
                5. How the code works step by step
                """
        }
        
        # Get the appropriate template and fill it
        template = prompt_templates.get(analysis_type, prompt_templates["summary"])
        prompt = template.format(language=language, code=code)
        
        # Generate response
        return await self.generate_text_async(prompt, max_tokens=max_tokens, temperature=0.2)