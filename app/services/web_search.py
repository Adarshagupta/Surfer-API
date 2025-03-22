import httpx
import os
import json
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, urljoin
import logging
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

# Set up logging
logger = get_logger("web_search")

# Provider selection
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "serper").lower()

# Search provider settings
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY", "")
USE_DUCKDUCKGO = os.getenv("USE_DUCKDUCKGO", "false").lower() == "true"

# Normalize settings for backwards compatibility
if not GOOGLE_SEARCH_API_KEY and SEARCH_API_KEY:
    GOOGLE_SEARCH_API_KEY = SEARCH_API_KEY
if not GOOGLE_SEARCH_ENGINE_ID and SEARCH_ENGINE_ID:
    GOOGLE_SEARCH_ENGINE_ID = SEARCH_ENGINE_ID

class WebSearchService:
    """Service for web search and information retrieval."""
    
    @staticmethod
    async def search_web(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using the configured search provider.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, link, and snippet
        """
        logger.info(f"Searching web for: {query}")
        
        # Select the appropriate search provider based on configuration
        if SEARCH_PROVIDER == "serper":
            if SERPER_API_KEY:
                try:
                    return await WebSearchService._search_with_serper(query, num_results)
                except Exception as e:
                    logger.error(f"Error with Serper API: {str(e)}")
            else:
                logger.warning("Serper API key not provided but Serper is configured as provider")
        
        elif SEARCH_PROVIDER == "google":
            if GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID:
                try:
                    return await WebSearchService._search_with_google_api(query, num_results)
                except Exception as e:
                    logger.error(f"Error with Google Search API: {str(e)}")
            else:
                logger.warning("Google Search API key or engine ID not provided but Google is configured as provider")
        
        elif SEARCH_PROVIDER == "bing":
            if BING_SEARCH_API_KEY:
                try:
                    return await WebSearchService._search_with_bing(query, num_results)
                except Exception as e:
                    logger.error(f"Error with Bing Search API: {str(e)}")
            else:
                logger.warning("Bing Search API key not provided but Bing is configured as provider")
        
        elif SEARCH_PROVIDER == "duckduckgo" or USE_DUCKDUCKGO:
            try:
                return await WebSearchService._search_with_duckduckgo(query, num_results)
            except Exception as e:
                logger.error(f"Error with DuckDuckGo search: {str(e)}")
        
        # Fall back logic - try available providers in sequence
        fallback_providers = []
        
        # Add available providers to fallback list
        if SERPER_API_KEY and SEARCH_PROVIDER != "serper":
            fallback_providers.append(("serper", WebSearchService._search_with_serper))
        
        if (GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID) and SEARCH_PROVIDER != "google":
            fallback_providers.append(("google", WebSearchService._search_with_google_api))
        
        if BING_SEARCH_API_KEY and SEARCH_PROVIDER != "bing":
            fallback_providers.append(("bing", WebSearchService._search_with_bing))
        
        if SEARCH_PROVIDER != "duckduckgo" and not USE_DUCKDUCKGO:
            fallback_providers.append(("duckduckgo", WebSearchService._search_with_duckduckgo))
        
        # Try fallback providers
        for provider_name, provider_func in fallback_providers:
            try:
                logger.info(f"Trying fallback search provider: {provider_name}")
                return await provider_func(query, num_results)
            except Exception as e:
                logger.error(f"Error with {provider_name}: {str(e)}")
        
        # If all else fails, use web scraping as a last resort
        logger.warning("All configured search providers failed, falling back to web scraping")
        try:
            return await WebSearchService._search_with_scraping(query, num_results)
        except Exception as e:
            logger.error(f"Error with web scraping: {str(e)}")
            # Return empty list as last resort
            return []
    
    @staticmethod
    async def _search_with_google_api(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API."""
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": min(num_results, 10)  # API limit is 10
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if "items" not in data:
                return []
            
            results = []
            for item in data["items"]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google Search API"
                })
            
            return results
    
    @staticmethod
    async def _search_with_serper(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Serper API."""
        url = "https://serpapi.com/search"
        params = {
            "api_key": SERPER_API_KEY,
            "q": query,
            "num": num_results
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if "organic" not in data:
                return []
            
            results = []
            for item in data["organic"][:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Serper API"
                })
            
            return results
    
    @staticmethod
    async def _search_with_scraping(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Basic web scraping fallback for search.
        This implementation has been improved for better reliability but is still not as reliable as API-based searches.
        """
        # Try multiple search engines for better reliability
        search_engines = [
            {
                "name": "Google",
                "url": f"https://www.google.com/search?q={quote_plus(query)}",
                "result_selector": "div.g",
                "title_selector": "h3",
                "link_selector": "a",
                "snippet_selector": "div.VwiC3b"
            },
            {
                "name": "Bing",
                "url": f"https://www.bing.com/search?q={quote_plus(query)}",
                "result_selector": "li.b_algo",
                "title_selector": "h2",
                "link_selector": "a",
                "snippet_selector": "div.b_caption p"
            }
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        results = []
        
        # Try each search engine until we get results or exhaust all options
        for engine in search_engines:
            if len(results) >= num_results:
                break
                
            try:
                logger.info(f"Attempting to scrape search results from {engine['name']}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        engine["url"], 
                        headers=headers,
                        follow_redirects=True,
                        timeout=10.0
                    )
                    
                    # Check if we got a valid response
                    if response.status_code != 200:
                        logger.warning(f"Failed to get results from {engine['name']}, status code: {response.status_code}")
                        continue
                        
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Find all result elements
                    result_elements = soup.select(engine["result_selector"])
                    
                    engine_results = []
                    for element in result_elements:
                        try:
                            title_element = element.select_one(engine["title_selector"])
                            link_element = element.select_one(engine["link_selector"])
                            snippet_element = element.select_one(engine["snippet_selector"])
                            
                            if title_element and link_element:
                                title = title_element.get_text(strip=True)
                                link = link_element.get("href", "")
                                
                                # Fix relative URLs
                                if link.startswith("/"):
                                    parsed_url = urlparse(engine["url"])
                                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                    link = urljoin(base_url, link)
                                
                                # Extract snippet or use a placeholder
                                snippet = ""
                                if snippet_element:
                                    snippet = snippet_element.get_text(strip=True)
                                
                                # Skip if title or link is empty
                                if not title or not link:
                                    continue
                                    
                                # Skip if link is not a valid URL
                                if not link.startswith(("http://", "https://")):
                                    continue
                                
                                engine_results.append({
                                    "title": title,
                                    "link": link,
                                    "snippet": snippet,
                                    "source": f"{engine['name']} (Scraped)"
                                })
                        except Exception as e:
                            logger.error(f"Error parsing individual search result from {engine['name']}: {str(e)}")
                    
                    # Deduplicate results based on URLs
                    seen_urls = {r["link"] for r in results}
                    unique_results = [r for r in engine_results if r["link"] not in seen_urls]
                    
                    # Add unique results
                    results.extend(unique_results[:num_results - len(results)])
                    
                    if len(results) >= num_results:
                        break
            
            except Exception as e:
                logger.error(f"Error scraping search results from {engine['name']}: {str(e)}")
        
        return results[:num_results]
    
    @staticmethod
    async def fetch_webpage_content(url: str) -> Optional[str]:
        """
        Fetch and extract the main content from a webpage.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text
                text = soup.get_text()
                
                # Break into lines and remove leading and trailing space
                lines = (line.strip() for line in text.splitlines())
                
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                
                # Remove blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text
        except Exception as e:
            logger.error(f"Error fetching webpage content: {str(e)}")
            return None
    
    @staticmethod
    def extract_relevant_info(text: str, query: str, max_chars: int = 1000) -> str:
        """
        Extract the most relevant information from text based on the query.
        
        Args:
            text: The text to extract from
            query: The search query
            max_chars: Maximum characters to extract
            
        Returns:
            Extracted relevant information
        """
        if not text:
            return ""
        
        # Split query into keywords
        keywords = query.lower().split()
        
        # Split text into paragraphs
        paragraphs = text.split('\n')
        
        # Score paragraphs based on keyword matches
        scored_paragraphs = []
        for para in paragraphs:
            if len(para) < 20:  # Skip very short paragraphs
                continue
                
            score = 0
            para_lower = para.lower()
            for keyword in keywords:
                if keyword in para_lower:
                    score += 1
            
            scored_paragraphs.append((score, para))
        
        # Sort by score (highest first)
        scored_paragraphs.sort(reverse=True)
        
        # Combine top paragraphs up to max_chars
        result = ""
        for _, para in scored_paragraphs:
            if len(result) + len(para) + 1 <= max_chars:
                result += para + "\n"
            else:
                break
        
        return result
    
    @staticmethod
    def format_search_results_for_llm(results: List[Dict[str, Any]], contents: List[str]) -> str:
        """
        Format search results and contents for the LLM.
        
        Args:
            results: List of search results
            contents: List of webpage contents corresponding to results
            
        Returns:
            Formatted text for the LLM
        """
        if not results:
            return "No search results found."
        
        formatted_text = "### Search Results:\n\n"
        
        for i, (result, content) in enumerate(zip(results, contents)):
            formatted_text += f"[{i+1}] {result['title']}\n"
            formatted_text += f"URL: {result['link']}\n"
            formatted_text += f"Snippet: {result['snippet']}\n"
            
            if content:
                # Truncate content if too long
                if len(content) > 500:
                    content = content[:497] + "..."
                formatted_text += f"Content: {content}\n"
            
            formatted_text += "\n"
        
        formatted_text += f"Search performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return formatted_text
    
    @staticmethod
    async def search_and_retrieve(query: str, num_results: int = 3) -> Dict[str, Any]:
        """
        Search the web and retrieve content from top results.
        
        Args:
            query: The search query
            num_results: Number of results to process
            
        Returns:
            Dictionary with search results, contents, and formatted text
        """
        # Search the web
        search_results = await WebSearchService.search_web(query, num_results)
        
        # Fetch content from each result
        contents = []
        for result in search_results:
            content = await WebSearchService.fetch_webpage_content(result["link"])
            if content:
                # Extract relevant information
                relevant_content = WebSearchService.extract_relevant_info(content, query)
                contents.append(relevant_content)
            else:
                contents.append("")
        
        # Format for LLM
        formatted_text = WebSearchService.format_search_results_for_llm(search_results, contents)
        
        return {
            "search_results": search_results,
            "contents": contents,
            "formatted_text": formatted_text
        }
    
    @staticmethod
    async def _search_with_bing(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using Bing Search API.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, link, and snippet
        """
        headers = {
            "Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY
        }
        
        params = {
            "q": query,
            "count": num_results,
            "offset": 0,
            "mkt": "en-US",
            "safesearch": "moderate"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.bing.microsoft.com/v7.0/search",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"Bing search error: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            results = []
            
            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"][:num_results]:
                    results.append({
                        "title": item.get("name", ""),
                        "link": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "Bing Search API"
                    })
            
            return results
    
    @staticmethod
    async def _search_with_duckduckgo(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using DuckDuckGo.
        This is a lightweight implementation that doesn't require an API key.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, link, and snippet
        """
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            
            results = []
            for result in soup.select(".result")[:num_results]:
                title_element = result.select_one(".result__a")
                snippet_element = result.select_one(".result__snippet")
                
                if title_element and snippet_element:
                    title = title_element.text.strip()
                    link = title_element.get("href", "")
                    
                    # Extract the actual URL from DuckDuckGo's redirect
                    if link.startswith("/"):
                        # Parse the URL from the redirect
                        try:
                            params = dict(param.split("=") for param in link.split("?")[1].split("&"))
                            if "uddg" in params:
                                link = params["uddg"]
                        except:
                            # If parsing fails, use the original link
                            pass
                    
                    snippet = snippet_element.text.strip()
                    
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "source": "DuckDuckGo"
                    })
            
            return results

# Create a global instance
web_search = WebSearchService() 