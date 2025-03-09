import httpx
import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin, urlparse
import logging
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import time

from app.core.config import settings
from app.core.logging import get_logger
from app.services.web_search import WebSearchService
from app.services.llm_service import get_llm_response

# Set up logging
logger = get_logger("web_surfing")

# Environment variables
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY", "")
BROWSERLESS_URL = os.getenv("BROWSERLESS_URL", "https://chrome.browserless.io")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

class WebSurfingService:
    """Service for advanced web surfing with visual understanding capabilities."""
    
    @staticmethod
    async def surf_web_for_task(query: str, task_description: str, task_type: str = "general") -> Dict[str, Any]:
        """
        Surf the web to complete a complex task using visual understanding.
        
        Args:
            query: The specific search query
            task_description: Detailed description of the task to complete
            task_type: Type of task (general, travel, research, shopping, comparison, etc.)
            
        Returns:
            Dictionary with structured data and content for the task
        """
        logger.info(f"Surfing web for task type '{task_type}': {task_description}")
        
        # Step 1: Analyze the task and break it down into subtasks
        subtasks = await WebSurfingService._analyze_task(task_description, task_type)
        
        # Step 2: Gather information for each subtask
        results = {}
        for subtask in subtasks:
            subtask_results = await WebSurfingService._gather_information_for_subtask(subtask, query)
            results[subtask["name"]] = subtask_results
        
        # Step 3: Synthesize the information into a structured response
        structured_response = await WebSurfingService._synthesize_information(results, task_description, task_type)
        
        return structured_response
    
    @staticmethod
    async def _analyze_task(task_description: str, task_type: str = "general") -> List[Dict[str, Any]]:
        """
        Analyze the task and break it down into subtasks.
        
        Args:
            task_description: Detailed description of the task
            task_type: Type of task (general, travel, research, shopping, comparison, etc.)
            
        Returns:
            List of subtasks with name, description, and search queries
        """
        # Use LLM to analyze the task and break it down
        prompt = f"""
        I need to break down the following {task_type} task into specific subtasks for web research:
        
        {task_description}
        
        For each subtask, provide:
        1. A name for the subtask
        2. A description of what information needs to be gathered
        3. Specific search queries that would be effective for this subtask
        4. Whether visual information (images, maps, charts, etc.) is needed
        5. What type of structured data should be extracted (e.g., prices, dates, specifications, locations)
        
        Format your response as a JSON array of subtasks.
        """
        
        response = await get_llm_response(prompt=prompt, prompt_type="code")
        
        # Extract JSON from the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response["response"])
        if json_match:
            subtasks_json = json_match.group(1)
        else:
            # Try to find JSON without markdown formatting
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response["response"], re.DOTALL)
            if json_match:
                subtasks_json = json_match.group(0)
            else:
                subtasks_json = response["response"]
        
        try:
            subtasks = json.loads(subtasks_json)
            return subtasks
        except json.JSONDecodeError:
            logger.error(f"Failed to parse subtasks JSON: {subtasks_json}")
            # Fallback to a basic structure if parsing fails
            return [
                {
                    "name": "General Information",
                    "description": f"Gather general information related to the {task_type} task",
                    "search_queries": [query],
                    "needs_visual": False,
                    "structured_data_type": "general"
                }
            ]
    
    @staticmethod
    async def _gather_information_for_subtask(subtask: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """
        Gather information for a specific subtask.
        
        Args:
            subtask: Dictionary with subtask details
            original_query: The original query for context
            
        Returns:
            Dictionary with gathered information
        """
        results = {
            "text_content": [],
            "visual_content": [],
            "structured_data": {}
        }
        
        # Process each search query for the subtask
        for query in subtask["search_queries"]:
            # Get search results
            search_results = await WebSearchService.search_web(query, num_results=5)
            
            # Process each search result
            for result in search_results:
                # Fetch and process webpage content
                content = await WebSurfingService._process_webpage(result["link"], query, subtask.get("needs_visual", False))
                if content:
                    results["text_content"].append({
                        "source": result["link"],
                        "title": result["title"],
                        "content": content["text"]
                    })
                    
                    # Add visual content if available
                    if "visuals" in content and content["visuals"]:
                        results["visual_content"].extend(content["visuals"])
        
        # Extract structured data based on the subtask
        results["structured_data"] = await WebSurfingService._extract_structured_data(
            results["text_content"], 
            subtask["name"], 
            subtask["description"],
            subtask.get("structured_data_type", "general")
        )
        
        return results
    
    @staticmethod
    async def _process_webpage(url: str, query: str, needs_visual: bool = False) -> Optional[Dict[str, Any]]:
        """
        Process a webpage to extract relevant content and visual information.
        
        Args:
            url: URL of the webpage
            query: Search query for relevance
            needs_visual: Whether visual information is needed
            
        Returns:
            Dictionary with text and visual content
        """
        try:
            # Use browserless.io for headless browser if API key is available
            if BROWSERLESS_API_KEY and needs_visual:
                return await WebSurfingService._process_with_browserless(url, query)
            else:
                # Fallback to simple HTTP request
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    response = await client.get(url)
                    if response.status_code != 200:
                        return None
                    
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()
                    
                    # Get text content
                    text = soup.get_text(separator=" ", strip=True)
                    
                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = " ".join(chunk for chunk in chunks if chunk)
                    
                    # Extract relevant portion based on query
                    relevant_text = WebSearchService.extract_relevant_info(text, query)
                    
                    return {
                        "text": relevant_text,
                        "visuals": []  # No visuals in simple mode
                    }
        except Exception as e:
            logger.error(f"Error processing webpage {url}: {str(e)}")
            return None
    
    @staticmethod
    async def _process_with_browserless(url: str, query: str) -> Dict[str, Any]:
        """
        Process a webpage using browserless.io for visual understanding.
        
        Args:
            url: URL of the webpage
            query: Search query for relevance
            
        Returns:
            Dictionary with text and visual content
        """
        try:
            # Prepare the script to execute in the browser
            script = {
                "url": url,
                "elements": [
                    {
                        "selector": "body",
                        "timeout": 10000
                    }
                ],
                "options": {
                    "waitFor": 2000,
                    "stealth": True,
                    "viewport": {
                        "width": 1280,
                        "height": 800
                    }
                }
            }
            
            # Call browserless.io API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{BROWSERLESS_URL}/scrape?token={BROWSERLESS_API_KEY}",
                    json=script
                )
                
                if response.status_code != 200:
                    logger.error(f"Browserless API error: {response.status_code} - {response.text}")
                    return {"text": "", "visuals": []}
                
                result = response.json()
                
                # Extract text content
                text_content = ""
                for element in result.get("data", []):
                    if "text" in element:
                        text_content += element["text"] + " "
                
                # Extract relevant portion based on query
                relevant_text = WebSearchService.extract_relevant_info(text_content, query)
                
                # Extract visual content (screenshots)
                visuals = []
                if "screenshot" in result:
                    visuals.append({
                        "type": "screenshot",
                        "source": url,
                        "data": result["screenshot"]
                    })
                
                # Extract images from the page
                for element in result.get("data", []):
                    if "attributes" in element and "src" in element["attributes"]:
                        if element["tagName"].lower() == "img":
                            img_url = element["attributes"]["src"]
                            if not img_url.startswith(("http://", "https://")):
                                img_url = urljoin(url, img_url)
                            
                            visuals.append({
                                "type": "image",
                                "source": img_url,
                                "alt": element["attributes"].get("alt", ""),
                                "data": None  # We don't fetch the actual image data here
                            })
                
                return {
                    "text": relevant_text,
                    "visuals": visuals
                }
        except Exception as e:
            logger.error(f"Error with browserless for {url}: {str(e)}")
            return {"text": "", "visuals": []}
    
    @staticmethod
    async def _extract_structured_data(
        text_contents: List[Dict[str, Any]], 
        subtask_name: str, 
        subtask_description: str,
        data_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Extract structured data from text content based on the subtask.
        
        Args:
            text_contents: List of text content from different sources
            subtask_name: Name of the subtask
            subtask_description: Description of the subtask
            data_type: Type of structured data to extract
            
        Returns:
            Dictionary with structured data
        """
        # Combine all text content
        combined_text = "\n\n".join([f"Source: {item['source']}\nTitle: {item['title']}\n{item['content']}" for item in text_contents])
        
        # Use LLM to extract structured data
        prompt = f"""
        I need to extract structured data of type "{data_type}" for the subtask "{subtask_name}" from the following web content:
        
        {combined_text[:10000]}  # Limit text to avoid token limits
        
        The subtask description is: {subtask_description}
        
        Extract the most relevant information and organize it into a structured JSON format that would be useful for this subtask.
        Include only factual information from the sources, and cite the source for each piece of information.
        
        Format your response as a JSON object.
        """
        
        response = await get_llm_response(prompt=prompt, prompt_type="code")
        
        # Extract JSON from the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response["response"])
        if json_match:
            structured_json = json_match.group(1)
        else:
            # Try to find JSON without markdown formatting
            json_match = re.search(r'\{\s*".*"\s*:.*\}', response["response"], re.DOTALL)
            if json_match:
                structured_json = json_match.group(0)
            else:
                structured_json = response["response"]
        
        try:
            structured_data = json.loads(structured_json)
            return structured_data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse structured data JSON: {structured_json}")
            return {"error": "Failed to parse structured data", "raw_text": response["response"]}
    
    @staticmethod
    async def _synthesize_information(
        results: Dict[str, Any], 
        task_description: str,
        task_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Synthesize the information gathered from all subtasks into a structured response.
        
        Args:
            results: Dictionary with results from all subtasks
            task_description: Original task description
            task_type: Type of task (general, travel, research, shopping, comparison, etc.)
            
        Returns:
            Dictionary with synthesized information
        """
        # Prepare the input for the LLM
        subtasks_data = json.dumps(results, indent=2)
        
        prompt = f"""
        I have gathered information for the following {task_type} task:
        
        {task_description}
        
        Here is the information gathered for each subtask:
        
        {subtasks_data[:15000]}  # Limit text to avoid token limits
        
        Please synthesize this information into a comprehensive response that addresses the original task.
        The response should be well-structured and include:
        
        1. A summary of the key findings
        2. Detailed information organized by relevant categories
        3. Any visual elements that should be included (described in detail)
        4. A structured HTML template that could be used to present this information
        
        Format your response as a JSON object with the following structure:
        {{
            "summary": "Summary text here",
            "detailed_sections": [
                {{
                    "title": "Section title",
                    "content": "Section content",
                    "visual_elements": [
                        {{
                            "type": "image/map/chart",
                            "description": "Description of what this should show",
                            "source": "Source URL if applicable"
                        }}
                    ]
                }}
            ],
            "html_template": "HTML code for displaying the information",
            "task_type": "{task_type}"
        }}
        """
        
        response = await get_llm_response(prompt=prompt, prompt_type="code", max_tokens=4096)
        
        # Extract JSON from the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response["response"])
        if json_match:
            synthesis_json = json_match.group(1)
        else:
            # Try to find JSON without markdown formatting
            json_match = re.search(r'\{\s*".*"\s*:.*\}', response["response"], re.DOTALL)
            if json_match:
                synthesis_json = json_match.group(0)
            else:
                synthesis_json = response["response"]
        
        try:
            synthesis = json.loads(synthesis_json)
            
            # Generate maps if needed for travel-related tasks
            if task_type == "travel" or "location" in task_description.lower() or "map" in task_description.lower():
                synthesis = await WebSurfingService._generate_maps(synthesis, task_description)
            
            # Generate charts if needed for data-related tasks
            if task_type == "data" or "comparison" in task_description.lower() or "statistics" in task_description.lower():
                synthesis = await WebSurfingService._generate_charts(synthesis, task_description)
            
            return synthesis
        except json.JSONDecodeError:
            logger.error(f"Failed to parse synthesis JSON: {synthesis_json}")
            return {
                "summary": "Failed to synthesize information properly",
                "detailed_sections": [
                    {
                        "title": "Raw Response",
                        "content": response["response"],
                        "visual_elements": []
                    }
                ],
                "html_template": "<div><h1>Error</h1><p>Failed to generate proper HTML template</p></div>",
                "task_type": task_type
            }
    
    @staticmethod
    async def _generate_maps(synthesis: Dict[str, Any], task_description: str) -> Dict[str, Any]:
        """
        Generate maps for the synthesized information if needed.
        
        Args:
            synthesis: Dictionary with synthesized information
            task_description: Original task description
            
        Returns:
            Updated synthesis dictionary with map URLs
        """
        if not GOOGLE_MAPS_API_KEY:
            return synthesis
        
        # Check if maps are needed
        needs_map = False
        map_locations = []
        
        # Extract location information from the synthesis
        for section in synthesis.get("detailed_sections", []):
            for visual in section.get("visual_elements", []):
                if visual.get("type") == "map":
                    needs_map = True
                    description = visual.get("description", "")
                    
                    # Extract location from description
                    locations = await WebSurfingService._extract_locations(description, task_description)
                    if locations:
                        for location in locations:
                            map_locations.append({
                                "name": location,
                                "visual_id": id(visual)  # Use object id as a unique identifier
                            })
        
        if needs_map and map_locations:
            # Generate static map URLs
            for location in map_locations:
                map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={quote_plus(location['name'])}&zoom=13&size=600x300&maptype=roadmap&markers=color:red%7C{quote_plus(location['name'])}&key={GOOGLE_MAPS_API_KEY}"
                
                # Update the corresponding visual element
                for section in synthesis.get("detailed_sections", []):
                    for visual in section.get("visual_elements", []):
                        if id(visual) == location["visual_id"]:
                            visual["map_url"] = map_url
        
        return synthesis
    
    @staticmethod
    async def _generate_charts(synthesis: Dict[str, Any], task_description: str) -> Dict[str, Any]:
        """
        Generate chart data for the synthesized information if needed.
        
        Args:
            synthesis: Dictionary with synthesized information
            task_description: Original task description
            
        Returns:
            Updated synthesis dictionary with chart data
        """
        # Check if charts are needed
        for section in synthesis.get("detailed_sections", []):
            for visual in section.get("visual_elements", []):
                if visual.get("type") in ["chart", "graph", "comparison"]:
                    # Extract chart data from description
                    chart_data = await WebSurfingService._extract_chart_data(visual.get("description", ""), task_description)
                    if chart_data:
                        visual["chart_data"] = chart_data
        
        return synthesis
    
    @staticmethod
    async def _extract_locations(description: str, task_description: str) -> List[str]:
        """
        Extract location names from text.
        
        Args:
            description: Description of the visual element
            task_description: Original task description
            
        Returns:
            List of location names
        """
        prompt = f"""
        Extract specific location names from the following text that should be displayed on a map:
        
        Visual description: {description}
        
        Task context: {task_description}
        
        Return only a JSON array of location strings, with no additional text.
        """
        
        response = await get_llm_response(prompt=prompt, prompt_type="code")
        
        # Extract JSON from the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response["response"])
        if json_match:
            locations_json = json_match.group(1)
        else:
            # Try to find JSON without markdown formatting
            json_match = re.search(r'\[\s*".*"\s*\]', response["response"], re.DOTALL)
            if json_match:
                locations_json = json_match.group(0)
            else:
                locations_json = response["response"]
        
        try:
            locations = json.loads(locations_json)
            return locations if isinstance(locations, list) else []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse locations JSON: {locations_json}")
            
            # Fallback: try to extract locations with regex
            location_matches = re.findall(r'"([^"]+)"', locations_json)
            return location_matches if location_matches else []
    
    @staticmethod
    async def _extract_chart_data(description: str, task_description: str) -> Dict[str, Any]:
        """
        Extract chart data from text.
        
        Args:
            description: Description of the visual element
            task_description: Original task description
            
        Returns:
            Dictionary with chart data
        """
        prompt = f"""
        Extract structured chart data from the following description:
        
        Visual description: {description}
        
        Task context: {task_description}
        
        Return a JSON object with the following structure:
        {{
            "chart_type": "bar/line/pie/etc.",
            "title": "Chart title",
            "labels": ["Label1", "Label2", ...],
            "datasets": [
                {{
                    "label": "Dataset label",
                    "data": [value1, value2, ...]
                }}
            ],
            "options": {{
                "x_axis_label": "X-axis label",
                "y_axis_label": "Y-axis label"
            }}
        }}
        """
        
        response = await get_llm_response(prompt=prompt, prompt_type="code")
        
        # Extract JSON from the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response["response"])
        if json_match:
            chart_json = json_match.group(1)
        else:
            # Try to find JSON without markdown formatting
            json_match = re.search(r'\{\s*".*"\s*:.*\}', response["response"], re.DOTALL)
            if json_match:
                chart_json = json_match.group(0)
            else:
                chart_json = response["response"]
        
        try:
            chart_data = json.loads(chart_json)
            return chart_data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse chart data JSON: {chart_json}")
            return {
                "chart_type": "bar",
                "title": "Error: Could not parse chart data",
                "labels": [],
                "datasets": []
            }
    
    @staticmethod
    async def generate_travel_itinerary(
        destination: str,
        start_date: str,
        end_date: str,
        budget_range: str,
        interests: List[str],
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a detailed travel itinerary with real-time data.
        
        Args:
            destination: Travel destination
            start_date: Start date of the trip
            end_date: End date of the trip
            budget_range: Budget range for the trip
            interests: List of traveler interests
            special_requests: Any special requests
            
        Returns:
            Dictionary with detailed itinerary and HTML travel handbook
        """
        # Construct the task description
        interests_str = ", ".join(interests)
        task_description = f"Create a detailed travel itinerary for {destination} from {start_date} to {end_date} with a budget of {budget_range}. "
        task_description += f"The traveler is interested in: {interests_str}. "
        
        if special_requests:
            task_description += f"Special requests: {special_requests}. "
        
        task_description += "Include daily activities, accommodation recommendations, transportation options, estimated costs, and local tips. "
        task_description += "Also create a simple HTML travel handbook with maps, attraction descriptions, essential phrases, and travel tips."
        
        # Use the web surfing service to gather information and create the itinerary
        result = await WebSurfingService.surf_web_for_task(destination, task_description, task_type="travel")
        
        return result
    
    @staticmethod
    async def process_complex_task(
        task_description: str, 
        task_type: str = "general",
        additional_context: Optional[str] = None,
        visual_understanding: bool = True,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Process a complex task using web surfing and visual understanding.
        
        This is a general-purpose method that can handle various types of tasks.
        
        Args:
            task_description: Detailed description of the task
            task_type: Type of task (general, travel, research, shopping, comparison, etc.)
            additional_context: Any additional context or information that might help with the task
            visual_understanding: Whether to use visual understanding capabilities
            max_depth: Maximum depth of web page exploration (1-3)
            
        Returns:
            Dictionary with processed information and response
        """
        # Extract the main query from the task description
        query = await WebSurfingService._extract_main_query(task_description, task_type)
        
        # Enhance the task description with additional context if provided
        enhanced_task_description = task_description
        if additional_context:
            enhanced_task_description = f"{task_description}\n\nAdditional context: {additional_context}"
        
        # Configure the web surfing process based on parameters
        search_depth = min(max(1, max_depth), 3)  # Ensure depth is between 1 and 3
        
        # Use the web surfing service to gather information and process the task
        result = await WebSurfingService._process_with_depth(
            query, 
            enhanced_task_description, 
            task_type, 
            visual_understanding,
            search_depth
        )
        
        return result
    
    @staticmethod
    async def _process_with_depth(
        query: str,
        task_description: str,
        task_type: str,
        use_visual: bool,
        depth: int
    ) -> Dict[str, Any]:
        """
        Process a task with specified depth of web exploration.
        
        Args:
            query: The search query
            task_description: Description of the task
            task_type: Type of task
            use_visual: Whether to use visual understanding
            depth: Depth of web exploration (1-3)
            
        Returns:
            Dictionary with processed information
        """
        # Adjust the number of search results and processing based on depth
        num_results_per_query = 3 * depth  # More depth = more results
        max_pages_to_process = 5 * depth   # More depth = more pages processed
        
        # Step 1: Analyze the task and break it down into subtasks
        subtasks = await WebSurfingService._analyze_task(task_description, task_type)
        
        # Step 2: Gather information for each subtask with depth control
        results = {}
        processed_pages = 0
        
        for subtask in subtasks:
            # Skip if we've reached the maximum pages to process
            if processed_pages >= max_pages_to_process:
                break
            
            subtask_results = {
                "text_content": [],
                "visual_content": [],
                "structured_data": {}
            }
            
            # Process each search query for the subtask
            for query in subtask["search_queries"][:depth]:  # Limit queries based on depth
                # Skip if we've reached the maximum pages to process
                if processed_pages >= max_pages_to_process:
                    break
                
                # Get search results
                search_results = await WebSearchService.search_web(query, num_results=num_results_per_query)
                
                # Process each search result
                for result in search_results:
                    # Skip if we've reached the maximum pages to process
                    if processed_pages >= max_pages_to_process:
                        break
                    
                    # Fetch and process webpage content
                    needs_visual = use_visual and subtask.get("needs_visual", False)
                    content = await WebSurfingService._process_webpage(result["link"], query, needs_visual)
                    
                    if content:
                        subtask_results["text_content"].append({
                            "source": result["link"],
                            "title": result["title"],
                            "content": content["text"]
                        })
                        
                        # Add visual content if available
                        if "visuals" in content and content["visuals"]:
                            subtask_results["visual_content"].extend(content["visuals"])
                        
                        processed_pages += 1
            
            # Extract structured data based on the subtask
            if subtask_results["text_content"]:
                subtask_results["structured_data"] = await WebSurfingService._extract_structured_data(
                    subtask_results["text_content"], 
                    subtask["name"], 
                    subtask["description"],
                    subtask.get("structured_data_type", "general")
                )
            
            results[subtask["name"]] = subtask_results
        
        # Step 3: Synthesize the information into a structured response
        structured_response = await WebSurfingService._synthesize_information(results, task_description, task_type)
        
        return structured_response
    
    @staticmethod
    async def _extract_main_query(task_description: str, task_type: str) -> str:
        """
        Extract the main search query from the task description.
        
        Args:
            task_description: Detailed description of the task
            task_type: Type of task
            
        Returns:
            Main search query
        """
        prompt = f"""
        Extract the main search query from the following {task_type} task description:
        
        {task_description}
        
        Return only the search query as a string, with no additional text.
        The query should be concise but contain the key information needed for a web search.
        """
        
        response = await get_llm_response(prompt=prompt)
        
        # Clean up the response
        query = response["response"].strip().strip('"\'')
        
        return query 