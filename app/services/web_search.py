import httpx
import os
import json
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import logging
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

# Set up logging
logger = get_logger("web_search")

# Default search engine settings
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

class WebSearchService:
    """Service for web search and information retrieval."""
    
    @staticmethod
    async def search_web(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using Google Search API or Serper API.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, link, and snippet
        """
        logger.info(f"Searching web for: {query}")
        
        # Try Serper API first if key is available
        if SERPER_API_KEY:
            try:
                return await WebSearchService._search_with_serper(query, num_results)
            except Exception as e:
                logger.error(f"Error with Serper API: {str(e)}")
        
        # Fall back to Google Search API if available
        if SEARCH_API_KEY and SEARCH_ENGINE_ID:
            try:
                return await WebSearchService._search_with_google_api(query, num_results)
            except Exception as e:
                logger.error(f"Error with Google Search API: {str(e)}")
        
        # Fall back to a basic web scraping approach
        try:
            return await WebSearchService._search_with_scraping(query, num_results)
        except Exception as e:
            logger.error(f"Error with web scraping: {str(e)}")
            return []
    
    @staticmethod
    async def _search_with_google_api(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API."""
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": SEARCH_API_KEY,
            "cx": SEARCH_ENGINE_ID,
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
        Note: This is a simplified implementation and may not work reliably.
        """
        encoded_query = quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            
            results = []
            for div in soup.find_all("div", class_="g")[:num_results]:
                try:
                    title_element = div.find("h3")
                    link_element = div.find("a")
                    snippet_element = div.find("div", class_="VwiC3b")
                    
                    if title_element and link_element and snippet_element:
                        title = title_element.text
                        link = link_element.get("href")
                        snippet = snippet_element.text
                        
                        results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet,
                            "source": "Web Scraping"
                        })
                except Exception as e:
                    logger.error(f"Error parsing search result: {str(e)}")
            
            return results
    
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

# Create a global instance
web_search = WebSearchService() 