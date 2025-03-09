# API endpoint documentation with proper Python boolean values
API_DOCS = {
    "auth": {
        "title": "Authentication",
        "description": "Endpoints for user authentication and token management.",
        "endpoints": [
            {
                "path": "/api/auth/signup",
                "method": "POST",
                "summary": "User Registration",
                "description": "Register a new user account.",
                "request_body": "UserCreate",
                "responses": {
                    "201": {
                        "description": "User created successfully",
                        "content": {
                            "application/json": {
                                "model": "UserInDB"
                            }
                        }
                    },
                    "400": {
                        "description": "Username or email already exists"
                    }
                },
                "example_request": {
                    "email": "user@example.com",
                    "username": "johndoe",
                    "password": "Password123!",
                    "full_name": "John Doe"
                }
            },
            {
                "path": "/api/auth/token",
                "method": "POST",
                "summary": "Login",
                "description": "Login to get an access token.",
                "request_body": "OAuth2PasswordRequestForm",
                "responses": {
                    "200": {
                        "description": "Login successful",
                        "content": {
                            "application/json": {
                                "model": "Token"
                            }
                        }
                    },
                    "401": {
                        "description": "Incorrect username or password"
                    }
                },
                "example_request": {
                    "username": "johndoe",
                    "password": "Password123!"
                }
            },
            {
                "path": "/api/auth/logout",
                "method": "POST",
                "summary": "Logout",
                "description": "Logout and invalidate the current token.",
                "security": ["Bearer"],
                "responses": {
                    "200": {
                        "description": "Logout successful"
                    },
                    "401": {
                        "description": "Not authenticated"
                    }
                }
            },
            {
                "path": "/api/auth/me",
                "method": "GET",
                "summary": "Get Current User",
                "description": "Get information about the currently authenticated user.",
                "security": ["Bearer"],
                "responses": {
                    "200": {
                        "description": "Current user information",
                        "content": {
                            "application/json": {
                                "model": "UserInDB"
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated"
                    }
                }
            }
        ]
    },
    "api_keys": {
        "title": "API Keys",
        "description": "Endpoints for managing API keys.",
        "endpoints": [
            {
                "path": "/api/api-keys",
                "method": "POST",
                "summary": "Create API Key",
                "description": "Create a new API key for accessing the chat API.",
                "security": ["Bearer"],
                "request_body": "APIKeyCreate",
                "responses": {
                    "201": {
                        "description": "API key created successfully",
                        "content": {
                            "application/json": {
                                "model": "APIKeyResponse"
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated"
                    }
                },
                "example_request": {
                    "name": "My API Key",
                    "expires_at": "2024-12-31T23:59:59Z"
                }
            },
            {
                "path": "/api/api-keys",
                "method": "GET",
                "summary": "List API Keys",
                "description": "List all API keys for the current user.",
                "security": ["Bearer"],
                "responses": {
                    "200": {
                        "description": "List of API keys",
                        "content": {
                            "application/json": {
                                "model": "List[APIKeyResponse]"
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated"
                    }
                }
            },
            {
                "path": "/api/api-keys/{api_key_id}",
                "method": "GET",
                "summary": "Get API Key",
                "description": "Get details of a specific API key.",
                "security": ["Bearer"],
                "parameters": [
                    {
                        "name": "api_key_id",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "integer"
                        },
                        "description": "ID of the API key"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "API key details",
                        "content": {
                            "application/json": {
                                "model": "APIKeyResponse"
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated"
                    },
                    "404": {
                        "description": "API key not found"
                    }
                }
            },
            {
                "path": "/api/api-keys/{api_key_id}",
                "method": "DELETE",
                "summary": "Revoke API Key",
                "description": "Revoke a specific API key.",
                "security": ["Bearer"],
                "parameters": [
                    {
                        "name": "api_key_id",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "integer"
                        },
                        "description": "ID of the API key to revoke"
                    }
                ],
                "responses": {
                    "204": {
                        "description": "API key revoked successfully"
                    },
                    "401": {
                        "description": "Not authenticated"
                    },
                    "404": {
                        "description": "API key not found"
                    }
                }
            }
        ]
    },
    "users": {
        "title": "User Management",
        "description": "Endpoints for managing user profiles and viewing usage statistics.",
        "endpoints": [
            {
                "path": "/api/users/me/profile",
                "method": "GET",
                "summary": "Get Profile",
                "description": "Get the current user's profile information.",
                "security": ["Bearer"],
                "responses": {
                    "200": {
                        "description": "User profile information",
                        "content": {
                            "application/json": {
                                "model": "UserInDB"
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated"
                    }
                }
            },
            {
                "path": "/api/users/me/profile",
                "method": "PUT",
                "summary": "Update Profile",
                "description": "Update the current user's profile information.",
                "security": ["Bearer"],
                "request_body": "UserUpdate",
                "responses": {
                    "200": {
                        "description": "Profile updated successfully",
                        "content": {
                            "application/json": {
                                "model": "UserInDB"
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated"
                    }
                },
                "example_request": {
                    "email": "newemail@example.com",
                    "username": "newusername",
                    "full_name": "New Name",
                    "password": "NewPassword123!"
                }
            },
            {
                "path": "/api/users/me/usage",
                "method": "GET",
                "summary": "Get Usage History",
                "description": "Get the current user's API usage history.",
                "security": ["Bearer"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {
                            "type": "integer",
                            "default": 50
                        },
                        "description": "Maximum number of records to return"
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "required": False,
                        "schema": {
                            "type": "integer",
                            "default": 0
                        },
                        "description": "Number of records to skip"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of usage records",
                        "content": {
                            "application/json": {
                                "model": "List[UsageRecordResponse]"
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated"
                    }
                }
            },
            {
                "path": "/api/users/me/usage/summary",
                "method": "GET",
                "summary": "Get Usage Summary",
                "description": "Get a summary of the current user's API usage.",
                "security": ["Bearer"],
                "responses": {
                    "200": {
                        "description": "Usage summary",
                        "content": {
                            "application/json": {
                                "model": "UsageSummary"
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated"
                    }
                }
            }
        ]
    },
    "health": {
        "title": "Health Check",
        "description": "Check if the API is running and the LLM service is accessible.",
        "endpoints": [
            {
                "path": "/api/health",
                "method": "GET",
                "summary": "Health Check",
                "description": "Check if the API is running and the LLM service is accessible.",
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "API is running and LLM service is accessible",
                        "content": {
                            "application/json": {
                                "example": {
                                    "status": "ok",
                                    "ollama": "connected",
                                    "models": ["llama2", "mistral", "deepseek-r1"]
                                }
                            }
                        }
                    }
                }
            }
        ]
    },
    "chat": {
        "title": "Chat API",
        "description": "Endpoints for interacting with the LLM in various ways.",
        "endpoints": [
            {
                "path": "/api/chat",
                "method": "POST",
                "summary": "Basic Chat",
                "description": "Send a message to the LLM and get a response.",
                "request_body": "ChatMessage",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "model": "ChatResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "What is the capital of France?",
                    "model": "deepseek-r1:1.5b",
                    "temperature": 0.7
                }
            },
            {
                "path": "/api/chat/stream",
                "method": "POST",
                "summary": "Streaming Chat",
                "description": "Send a message to the LLM and get a streaming response.",
                "request_body": "ChatMessage",
                "responses": {
                    "200": {
                        "description": "Streaming response",
                        "content": {
                            "application/json": {
                                "example": {
                                    "content": "Partial response content",
                                    "full_response": "Full response so far"
                                }
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "Write a short poem about AI.",
                    "model": "deepseek-r1:1.5b",
                    "temperature": 0.8
                }
            },
            {
                "path": "/api/chat/advanced",
                "method": "POST",
                "summary": "Advanced Chat",
                "description": "Send a message with template support and additional options.",
                "request_body": "AdvancedChatMessage",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "model": "ChatResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "Explain quantum computing",
                    "template_id": "academic_explanation",
                    "prompt_type": "academic",
                    "context": "The user is a college student studying physics."
                }
            },
            {
                "path": "/api/chat/function",
                "method": "POST",
                "summary": "Function Calling Chat",
                "description": "Chat with function calling capabilities.",
                "request_body": "FunctionCallingMessage",
                "responses": {
                    "200": {
                        "description": "Successful response with function calls",
                        "content": {
                            "application/json": {
                                "model": "ChatResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "What's the weather in New York?",
                    "enable_function_calling": True,
                    "auto_execute_functions": True
                }
            },
            {
                "path": "/api/chat/document",
                "method": "POST",
                "summary": "Document Chat",
                "description": "Chat with context from a document.",
                "request_body": "DocumentChatMessage",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "model": "ChatResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "Summarize the main points of the document",
                    "document_id": "doc_123456",
                    "include_document_content": True
                }
            },
            {
                "path": "/api/chat/websearch",
                "method": "POST",
                "summary": "Web Search Chat",
                "description": "Chat with web search capabilities.",
                "request_body": "WebSearchChatMessage",
                "responses": {
                    "200": {
                        "description": "Successful response with search results",
                        "content": {
                            "application/json": {
                                "model": "WebSearchResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "prompt": "What are the latest developments in fusion energy?",
                    "search_enabled": True,
                    "num_results": 5,
                    "include_citations": True
                }
            },
            {
                "path": "/api/chat/complex-task",
                "method": "POST",
                "summary": "Complex Task Processing",
                "description": "Process complex tasks using advanced web surfing and visual understanding.",
                "request_body": "ComplexTaskRequest",
                "responses": {
                    "200": {
                        "description": "Successful response with processed task results",
                        "content": {
                            "application/json": {
                                "model": "ComplexTaskResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "task_description": "Compare the top 5 electric vehicles in 2023 based on range, price, and features.",
                    "task_type": "comparison",
                    "visual_understanding": True,
                    "max_depth": 2
                }
            }
        ]
    },
    "travel": {
        "title": "Travel API",
        "description": "Endpoints for travel-related services.",
        "endpoints": [
            {
                "path": "/api/travel/itinerary",
                "method": "POST",
                "summary": "Generate Travel Itinerary",
                "description": "Generate a detailed travel itinerary with real-time data.",
                "request_body": "TravelItineraryRequest",
                "responses": {
                    "200": {
                        "description": "Successful response with travel itinerary",
                        "content": {
                            "application/json": {
                                "model": "TravelItineraryResponse"
                            }
                        }
                    }
                },
                "example_request": {
                    "destination": "Japan",
                    "start_date": "2023-04-15",
                    "end_date": "2023-04-23",
                    "budget_range": "$2500-5000",
                    "interests": ["historical sites", "hidden gems", "Japanese culture"],
                    "special_requests": "Looking for a special location for a proposal"
                }
            }
        ]
    }
} 