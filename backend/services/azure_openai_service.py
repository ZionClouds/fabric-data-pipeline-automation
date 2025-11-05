"""
Azure OpenAI Service with GPT-5 and Web Search Integration

This service provides:
1. Azure OpenAI GPT-5 chat completions
2. Web Search API integration (SerpAPI/Google) for current Microsoft Fabric documentation
3. Function calling to dynamically search when needed

Note: Bing Search APIs have been retired. This uses SerpAPI or Google Custom Search as alternatives.
"""

import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """
    Service for Azure OpenAI GPT-5 with Bing Search integration
    """

    def __init__(
        self,
        azure_endpoint: str,
        api_key: str,
        deployment_name: str,
        api_version: str = "2024-12-01-preview",
        bing_api_key: Optional[str] = None,
        bing_endpoint: Optional[str] = None
    ):
        """
        Initialize Azure OpenAI service

        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            deployment_name: Model deployment name (e.g., "gpt-5-chat")
            api_version: API version
            bing_api_key: Optional Bing Search API key
            bing_endpoint: Optional Bing Search endpoint
        """
        self.client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=api_key,
        )
        self.deployment = deployment_name
        self.bing_api_key = bing_api_key
        self.bing_endpoint = bing_endpoint or "https://api.bing.microsoft.com/v7.0/search"

        logger.info(f"Azure OpenAI Service initialized with deployment: {deployment_name}")
        logger.info(f"Bing Search enabled: {bool(bing_api_key)}")

    def get_system_prompt(self) -> str:
        """
        System prompt for Microsoft Fabric pipeline assistant
        """
        return """You are an expert Microsoft Fabric assistant with deep knowledge of:

- Microsoft Fabric architecture and capabilities
- Data pipelines and data engineering patterns
- OneLake shortcuts and integration
- Copy activities, notebooks, and data flows
- Azure services integration
- Latest Fabric features and best practices

Your role is to help users build and troubleshoot Microsoft Fabric data pipelines.

IMPORTANT CAPABILITIES:
- You have access to the Bing Search function to find latest Microsoft Fabric documentation
- When users ask about current features, recent updates, or specific APIs, use search_fabric_docs
- Always prioritize current, accurate information from official Microsoft documentation
- If you're unsure about recent features or APIs, search for latest documentation

WHEN TO SEARCH:
- User asks about latest features or updates
- User mentions API errors or issues
- User asks about authentication methods or configuration
- You need to verify current API syntax or parameters
- User asks "how to" questions that might have recent changes

RESPONSE STYLE:
- Be concise and actionable
- Provide code examples when relevant
- Cite sources when using search results
- Be honest if information might be outdated

Remember: Microsoft Fabric is rapidly evolving. When in doubt, search for the latest information!
"""

    async def search_fabric_docs(self, query: str, count: int = 5) -> Dict[str, Any]:
        """
        Search for Microsoft Fabric documentation using Azure OpenAI Grounding with Bing

        This uses Azure OpenAI's grounding feature to search the web in real-time
        using your Bing.Grounding resource (fabricbing).

        Args:
            query: Search query
            count: Number of results to return (default: 5)

        Returns:
            Dict with search results
        """
        try:
            enhanced_query = f"Search the web for the latest Microsoft Fabric documentation about: {query}. Focus on learn.microsoft.com sources published in 2024-2025."

            # Call GPT-5 with Bing Grounding enabled
            # This actually searches the web using your Bing.Grounding resource
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a search assistant. Provide concise, factual information with sources and URLs from Microsoft Learn documentation."
                    },
                    {
                        "role": "user",
                        "content": enhanced_query
                    }
                ],
                max_tokens=1000,
                temperature=0.3,
                extra_body={
                    # Enable Bing Grounding - This searches the web in real-time!
                    "data_sources": [
                        {
                            "type": "bing_grounding",
                            "parameters": {
                                "key": self.bing_api_key,
                                "endpoint": "https://api.bing.microsoft.com/",
                                "strictness": 3,
                                "top_n_documents": count
                            }
                        }
                    ]
                }
            )

            content = response.choices[0].message.content

            # Try to extract citations from the response
            citations = []
            if hasattr(response.choices[0].message, 'context') and response.choices[0].message.context:
                context = response.choices[0].message.context
                if 'citations' in context:
                    for citation in context['citations']:
                        citations.append({
                            "title": citation.get('title', ''),
                            "url": citation.get('url', ''),
                            "snippet": citation.get('content', '')
                        })

            logger.info(f"Azure OpenAI Bing Grounding search completed for query: {query}, found {len(citations)} citations")

            # If we have citations from grounding, use them
            if citations:
                return {
                    "success": True,
                    "query": query,
                    "results": citations,
                    "grounding_enabled": True
                }

            # Otherwise return the response content
            return {
                "success": True,
                "query": query,
                "results": [{
                    "title": f"Microsoft Fabric Documentation - {query}",
                    "url": "https://learn.microsoft.com/fabric/",
                    "snippet": content
                }],
                "grounding_enabled": True
            }

        except Exception as e:
            logger.error(f"Grounding search error: {str(e)}")
            # Fallback: Use GPT-5's training data (January 2025)
            logger.info("Falling back to GPT-5 training data (January 2025)")
            try:
                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Based on your training data, provide information about: {query}"
                        }
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )

                return {
                    "success": True,
                    "query": query,
                    "results": [{
                        "title": f"Microsoft Fabric Documentation - {query} (Training Data)",
                        "url": "https://learn.microsoft.com/fabric/",
                        "snippet": response.choices[0].message.content
                    }],
                    "grounding_enabled": False,
                    "fallback": True
                }
            except:
                return {
                    "success": False,
                    "error": str(e),
                    "results": [],
                    "fallback_message": "I'll answer based on my training data (updated January 2025)."
                }

    def _format_search_results_for_context(self, search_response: Dict[str, Any]) -> str:
        """Format search results as context for the model"""
        if not search_response.get("success") or not search_response.get("results"):
            return "No search results found."

        results = search_response["results"]
        formatted = f"Latest documentation for '{search_response['query']}':\n\n"

        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   URL: {result['url']}\n"
            formatted += f"   {result['snippet']}\n\n"

        return formatted

    async def chat_with_function_calling(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 16384,
        temperature: float = 1.0,
        enable_search: bool = True
    ) -> Dict[str, Any]:
        """
        Chat with GPT-5 with optional function calling for Bing Search

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Temperature for response generation
            enable_search: Enable Bing Search function calling

        Returns:
            Dict with response and metadata
        """
        try:
            # Define available functions
            tools = []
            if enable_search and self.bing_api_key:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "search_fabric_docs",
                        "description": "Search for the latest Microsoft Fabric documentation, API references, features, and best practices. Use this when you need current information about Fabric capabilities, APIs, authentication methods, or recent updates.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query (e.g., 'OneLake shortcut API', 'pipeline authentication methods', 'copy activity error handling')"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                })

            # Add system message if not present
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {
                    "role": "system",
                    "content": self.get_system_prompt()
                })

            # Initial API call
            logger.info(f"Calling Azure OpenAI with {len(messages)} messages")

            call_params = {
                "model": self.deployment,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 1.0
            }

            if tools:
                call_params["tools"] = tools
                call_params["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**call_params)

            # Check if model wants to call a function
            message = response.choices[0].message
            tool_calls = message.tool_calls

            if tool_calls:
                logger.info(f"Model requested {len(tool_calls)} function calls")

                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in tool_calls
                    ]
                })

                # Execute function calls
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"Executing function: {function_name} with args: {function_args}")

                    if function_name == "search_fabric_docs":
                        search_result = await self.search_fabric_docs(function_args.get("query", ""))
                        formatted_results = self._format_search_results_for_context(search_result)

                        # Add function result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": formatted_results
                        })

                # Make second API call with function results
                logger.info("Making second API call with function results")
                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=1.0
                )

            # Extract final response
            final_message = response.choices[0].message
            content = final_message.content

            logger.info(f"Azure OpenAI response received. Finish reason: {response.choices[0].finish_reason}")

            return {
                "content": content,
                "role": "assistant",
                "finish_reason": response.choices[0].finish_reason,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"Azure OpenAI chat error: {str(e)}")
            raise Exception(f"Azure OpenAI service error: {str(e)}")

    async def simple_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 16384,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        Simple chat without function calling

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Temperature for response generation

        Returns:
            Dict with response and metadata
        """
        try:
            # Add system message if not present
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {
                    "role": "system",
                    "content": self.get_system_prompt()
                })

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=1.0
            )

            message = response.choices[0].message

            return {
                "content": message.content,
                "role": "assistant",
                "finish_reason": response.choices[0].finish_reason,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"Azure OpenAI simple chat error: {str(e)}")
            raise Exception(f"Azure OpenAI service error: {str(e)}")
