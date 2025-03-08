from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime
from pydantic import BaseModel, Field

class PromptTemplate(BaseModel):
    """Model for prompt templates with versioning."""
    id: str
    name: str
    description: str
    template: str
    version: str
    created_at: str
    updated_at: str
    tags: List[str] = []
    parameters: Dict[str, Any] = {}
    is_active: bool = True
    
class PromptTemplateManager:
    """Manager for prompt templates with versioning and persistence."""
    
    def __init__(self, templates_dir: str = "data/templates"):
        """Initialize the template manager."""
        self.templates_dir = templates_dir
        self.templates: Dict[str, PromptTemplate] = {}
        self._ensure_dir_exists()
        self._load_templates()
    
    def _ensure_dir_exists(self):
        """Ensure the templates directory exists."""
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def _load_templates(self):
        """Load templates from disk."""
        if not os.path.exists(self.templates_dir):
            return
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.templates_dir, filename), "r") as f:
                        template_data = json.load(f)
                        template = PromptTemplate(**template_data)
                        self.templates[template.id] = template
                except Exception as e:
                    print(f"Error loading template {filename}: {str(e)}")
    
    def save_template(self, template: PromptTemplate):
        """Save a template to disk."""
        template_path = os.path.join(self.templates_dir, f"{template.id}.json")
        with open(template_path, "w") as f:
            f.write(json.dumps(template.dict(), indent=2))
        self.templates[template.id] = template
    
    def create_template(
        self,
        name: str,
        description: str,
        template: str,
        tags: List[str] = [],
        parameters: Dict[str, Any] = {}
    ) -> PromptTemplate:
        """Create a new template."""
        # Generate a unique ID
        template_id = f"{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create the template
        now = datetime.now().isoformat()
        new_template = PromptTemplate(
            id=template_id,
            name=name,
            description=description,
            template=template,
            version="1.0.0",
            created_at=now,
            updated_at=now,
            tags=tags,
            parameters=parameters,
            is_active=True
        )
        
        # Save the template
        self.save_template(new_template)
        
        return new_template
    
    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> PromptTemplate:
        """Update an existing template."""
        if template_id not in self.templates:
            raise ValueError(f"Template with ID {template_id} not found")
        
        # Get the existing template
        existing = self.templates[template_id]
        
        # Create a new version
        version_parts = existing.version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        new_version = ".".join(version_parts)
        
        # Update the template
        updated = PromptTemplate(
            id=existing.id,
            name=name if name is not None else existing.name,
            description=description if description is not None else existing.description,
            template=template if template is not None else existing.template,
            version=new_version,
            created_at=existing.created_at,
            updated_at=datetime.now().isoformat(),
            tags=tags if tags is not None else existing.tags,
            parameters=parameters if parameters is not None else existing.parameters,
            is_active=is_active if is_active is not None else existing.is_active
        )
        
        # Save the updated template
        self.save_template(updated)
        
        return updated
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    def get_templates(self, tag: Optional[str] = None, active_only: bool = True) -> List[PromptTemplate]:
        """Get all templates, optionally filtered by tag and active status."""
        templates = list(self.templates.values())
        
        if active_only:
            templates = [t for t in templates if t.is_active]
        
        if tag:
            templates = [t for t in templates if tag in t.tags]
        
        return templates
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id not in self.templates:
            return False
        
        # Remove from memory
        del self.templates[template_id]
        
        # Remove from disk
        template_path = os.path.join(self.templates_dir, f"{template_id}.json")
        if os.path.exists(template_path):
            os.remove(template_path)
        
        return True
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Render a template with variables."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        # Simple string formatting
        rendered = template.template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        
        return rendered

# Initialize the template manager
template_manager = PromptTemplateManager()

# Create default templates if they don't exist
def initialize_default_templates():
    """Initialize default templates."""
    # Check if we already have templates
    existing_templates = template_manager.get_templates()
    if existing_templates:
        return
    
    # General assistant template
    template_manager.create_template(
        name="General Assistant",
        description="A general-purpose assistant template",
        template="""You are a helpful AI assistant that provides accurate and concise information.

IMPORTANT INSTRUCTIONS ABOUT RESPONSE FORMAT:
1. You can use <think>...</think> tags to show your thinking process.
2. AFTER your thinking, you MUST provide a clear, direct answer WITHOUT any thinking tags.
3. Your final answer should appear AFTER the </think> tag.
4. DO NOT put your entire response inside thinking tags.
5. ALWAYS include a response outside of the thinking tags.

{{custom_instructions}}

User query: {{prompt}}""",
        tags=["general", "assistant"],
        parameters={
            "prompt": "The user's query",
            "custom_instructions": "Any custom instructions for the model"
        }
    )
    
    # Code assistant template
    template_manager.create_template(
        name="Code Assistant",
        description="A template for code-related queries",
        template="""You are a coding assistant. Provide clear, efficient, and well-documented code examples.

IMPORTANT INSTRUCTIONS ABOUT RESPONSE FORMAT:
1. You can use <think>...</think> tags to show your thinking process.
2. AFTER your thinking, you MUST provide a clear, direct answer with code examples WITHOUT any thinking tags.
3. Your final answer should appear AFTER the </think> tag.
4. DO NOT put your entire response inside thinking tags.
5. ALWAYS include a response outside of the thinking tags.

{{custom_instructions}}

Language: {{language}}
Context: {{context}}

User query: {{prompt}}""",
        tags=["code", "programming"],
        parameters={
            "prompt": "The user's query",
            "language": "The programming language",
            "context": "Any code context",
            "custom_instructions": "Any custom instructions for the model"
        }
    )

# Initialize default templates
initialize_default_templates() 