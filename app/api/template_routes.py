from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.services.prompt_templates import template_manager, PromptTemplate

# Create router
template_router = APIRouter(tags=["templates"])

class TemplateCreate(BaseModel):
    """Model for creating a new template."""
    name: str
    description: str
    template: str
    tags: List[str] = []
    parameters: Dict[str, Any] = {}

class TemplateUpdate(BaseModel):
    """Model for updating an existing template."""
    name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None
    tags: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class TemplateRender(BaseModel):
    """Model for rendering a template."""
    variables: Dict[str, Any]

# Get all templates
@template_router.get("/templates", response_model=List[PromptTemplate])
async def get_templates(tag: Optional[str] = None, active_only: bool = True):
    """Get all templates, optionally filtered by tag and active status."""
    templates = template_manager.get_templates(tag=tag, active_only=active_only)
    return templates

# Get a template by ID
@template_router.get("/templates/{template_id}", response_model=PromptTemplate)
async def get_template(template_id: str):
    """Get a template by ID."""
    template = template_manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template with ID {template_id} not found")
    return template

# Create a new template
@template_router.post("/templates", response_model=PromptTemplate)
async def create_template(template_data: TemplateCreate):
    """Create a new template."""
    try:
        template = template_manager.create_template(
            name=template_data.name,
            description=template_data.description,
            template=template_data.template,
            tags=template_data.tags,
            parameters=template_data.parameters
        )
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update a template
@template_router.put("/templates/{template_id}", response_model=PromptTemplate)
async def update_template(template_id: str, template_data: TemplateUpdate):
    """Update an existing template."""
    try:
        template = template_manager.update_template(
            template_id=template_id,
            name=template_data.name,
            description=template_data.description,
            template=template_data.template,
            tags=template_data.tags,
            parameters=template_data.parameters,
            is_active=template_data.is_active
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Delete a template
@template_router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a template."""
    success = template_manager.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Template with ID {template_id} not found")
    return {"status": "success", "message": f"Template with ID {template_id} deleted"}

# Render a template
@template_router.post("/templates/{template_id}/render")
async def render_template(template_id: str, render_data: TemplateRender):
    """Render a template with variables."""
    try:
        rendered = template_manager.render_template(
            template_id=template_id,
            variables=render_data.variables
        )
        return {"rendered": rendered}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 