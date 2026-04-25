import json

# Load Django schema
with open("schema_django.json") as f:
    schema_django = json.load(f)

# Load FastAPI schema
with open("schema_fastapi.json") as f:
    schema_fastapi = json.load(f)

# Detailed documentation for the Haystack Bot (streaming response)
haystack_bot_schema = {
    "/chat-stream/": {
        "get": {
            "summary": "Streamed Chat Response (Haystack + OpenAI)",
            "description": """
                Asynchronously streams a chatbot response character by character.

                This endpoint is powered by a hybrid pipeline using:
                - PgVector Document Store for semantic search.
                - SentenceTransformersTextEmbedder for embedding user questions.
                - PgvectorEmbeddingRetriever for retrieving relevant documents.
                - DocumentJoiner for combining retrieved documents.
                - ChatPromptBuilder for generating a structured prompt.
                - OpenAIChatGenerator for generating responses.
            """,
            "parameters": [
                {
                    "name": "message",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "User's input message."
                }
            ],
            "responses": {
                "200": {
                    "description": "Streamed chatbot response.",
                    "content": {
                        "text/event-stream": {
                            "example": "data: Hello\n\ndata: [DONE]\n\n"
                        }
                    }
                }
            }
        }
    },
    "/document-parse/": {
        "post": {
            "summary": "Document Parsing (PDF, TXT, DOCX)",
            "description": """
                Parses uploaded documents (PDF, TXT, DOCX) into a list of Haystack Document objects.

                Supported file types:
                - PDF (.pdf) - processed using PDFMinerToDocument.
                - Text (.txt) - processed using TextFileToDocument.
                - Word (.docx) - processed using DOCXToDocument.

                How it works:
                - User uploads a document.
                - The document is converted into Haystack Document objects.
                - Each document object retains metadata (file name).
            """,
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "file": {
                                    "type": "string",
                                    "format": "binary",
                                    "description": "The file to be parsed (PDF, TXT, DOCX)."
                                }
                            },
                            "required": ["file"]
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "List of parsed document objects.",
                    "content": {
                        "application/json": {
                            "example": {
                                "documents": [
                                    {
                                        "content": "Document text content...",
                                        "meta": {"file_name": "example.pdf"}
                                    }
                                ]
                            }
                        }
                    }
                },
                "400": {
                    "description": "Error - Unsupported file type.",
                    "content": {
                        "application/json": {
                            "example": {"error": "Unsupported file type: .xyz"}
                        }
                    }
                }
            }
        }
    }
}

# Combine all API schemas (Django + FastAPI + Haystack Bot + Document Parsing)
schema_combined = {
    "openapi": "3.0.0",
    "info": {
        "title": "GeeBOT Combined API Documentation",
        "description": "This documentation combines Django API, FastAPI (Haystack), and the Haystack Bot.",
        "version": "1.0.0"
    },
    "paths": {
        **schema_django.get("paths", {}),
        **schema_fastapi.get("paths", {}),
        **haystack_bot_schema
    },
    "components": {
        "schemas": {
            **schema_django.get("components", {}).get("schemas", {}),
            **schema_fastapi.get("components", {}).get("schemas", {})
        },
        "securitySchemes": {
            **schema_django.get("components", {}).get("securitySchemes", {}),
            **schema_fastapi.get("components", {}).get("securitySchemes", {})
        }
    }
}

# Save the combined schema
with open("schema_combined.json", "w", encoding="utf-8") as f:
    json.dump(schema_combined, f, indent=4, ensure_ascii=False)

print("✅ Combined schema saved as schema_combined.json")
