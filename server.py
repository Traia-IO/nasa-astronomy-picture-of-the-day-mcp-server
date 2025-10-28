#!/usr/bin/env python3
"""
NASA Astronomy Picture of the Day MCP Server with Authentication

A Model Context Protocol server providing NASA APOD API integration for astronomy data
using the NASA Astronomy Picture of the Day API with authentication via Bearer tokens.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Third-party imports
import requests
from fastmcp import FastMCP, Context
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_request, get_context
from starlette.requests import Request
from starlette.responses import JSONResponse
from retry import retry
# NASA Astronomy Picture of the Day SDK
# TODO: Adjust the import based on the SDK documentation
# Common patterns:
#   - from nasapy import Client
#   - from nasapy import NASA Astronomy Picture of the DayClient  
#   - import nasapy
# Check the SDK docs for the correct import statement
import nasapy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('nasa-astronomy-picture-of-the-day_mcp')

# Get stage from environment (useful for different API endpoints)
STAGE = os.getenv("STAGE", "MAINNET").upper()


class AuthMiddleware(Middleware):
    """Middleware to extract and store API keys from Authorization headers."""
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """Extract bearer token on each request and bind to context state."""
        try:
            # Access the raw HTTP request
            request: Request = get_http_request()
            
            # Debug: log all headers
            logger.info(f"AuthMiddleware: Received request with headers: {dict(request.headers)}")
            logger.info(f"AuthMiddleware: Method: {request.method}, URL: {request.url}")
            
            # Extract bearer token from Authorization header
            auth = request.headers.get("Authorization", "")
            token = auth[7:].strip() if auth.lower().startswith("bearer ") else None
            
            if not token:
                # Check X-API-KEY header as alternative
                token = request.headers.get("X-API-KEY", "")
            
            if token:
                # Store the API key in the context state
                # This will be accessible in tools via get_context()
                if hasattr(context, 'state'):
                    context.state.api_key = token
                    logger.info(f"API key bound to context state: {token[:10]}...")
                else:
                    # Try to store it in the request state as fallback
                    request.state.api_key = token
                    logger.info(f"API key bound to request state: {token[:10]}...")
            else:
                logger.warning(f"No API key provided in request headers")
            
        except Exception as e:
            # This might happen in non-HTTP transports or if get_http_request fails
            logger.debug(f"Could not extract API key from request: {e}")
            
        # Proceed with the request (authentication check happens in the tools)
        return await call_next(context)


# Initialize FastMCP server with middleware
mcp = FastMCP("NASA Astronomy Picture of the Day MCP Server", middleware=[AuthMiddleware()])


# Add health check endpoint using FastMCP's custom_route
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for container orchestration."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "nasa-astronomy-picture-of-the-day-mcp-server",
            "timestamp": datetime.now().isoformat()
        }
    )


def get_session_api_key(context: Context) -> Optional[str]:
    """Get the API key for the current session."""
    try:
        # Try to get the API key from the context state
        # The middleware should have stored it there
        if hasattr(context, 'state') and hasattr(context.state, 'api_key'):
            return context.state.api_key
        
        # Fallback: try to get it from the current HTTP request
        try:
            request: Request = get_http_request()
            if hasattr(request.state, 'api_key'):
                return request.state.api_key
        except Exception:
            pass
        
        # If we're in a tool context, try to get the context using the dependency
        try:
            ctx = get_context()
            if hasattr(ctx, 'state') and hasattr(ctx.state, 'api_key'):
                return ctx.state.api_key
        except Exception:
            pass
            
    except Exception as e:
        logger.debug(f"Could not retrieve API key from context: {e}")
    
    return None


# TODO: Add your API-specific functions here
# Use @retry decorator ONLY for external API calls (not internal functions):
# @retry(tries=2, delay=1, backoff=2, jitter=(1, 3))
# def call_nasa-astronomy-picture-of-the-day_api(query: str, api_key: str) -> Dict[str, Any]:
#     """Call the NASA Astronomy Picture of the Day API with the given query."""
#     # You can use STAGE to determine which API endpoint to use:
#     # base_url = "https://api-testnet.example.com" if STAGE == "TESTNET" else "https://api.example.com"
#     # Implement your API logic here (HTTP requests, SDK calls, etc.)
#     pass


@mcp.tool()
async def example_tool(
    context: Context,
    query: str
) -> Dict[str, Any]:
    """
    Example tool for NASA Astronomy Picture of the Day API.
    
    TODO: Replace this with your actual tool implementation.
    
    Args:
        context: MCP context (injected automatically)
        query: Query parameter
        
    Returns:
        Dictionary with results
    """
    # Check for API key
    api_key = get_session_api_key(context)
    if not api_key:
        return {"error": "No API key found. Please authenticate with Authorization: Bearer YOUR_API_KEY"}
    
    # TODO: Implement your tool logic here
    return {
        "status": "success",
        "message": "This is a placeholder. Implement your NASA Astronomy Picture of the Day logic here.",
        "query": query,
        "timestamp": datetime.now().isoformat()
    }


@mcp.tool()
async def get_api_info(context: Context) -> Dict[str, Any]:
    """
    Get information about the NASA Astronomy Picture of the Day API service.
    
    Args:
        context: MCP context (injected automatically)
    
    Returns:
        Dictionary containing API information and status
    """
    # Check authentication status
    api_key = get_session_api_key(context)
    auth_status = "authenticated" if api_key else "not authenticated"
    
    return {
        "status": "ready",
"auth_status": auth_status,        "api_name": "NASA Astronomy Picture of the Day",
        "api_url": "https://api.nasa.gov/planetary/apod",
        "documentation": "https://api.nasa.gov/",
        "description": "Nasa apod api integration for astronomy data",
"authentication": "Bearer token required in Authorization header"    }


def run_server():
    """Entry point for the executable script"""
    logger.info("Starting NASA Astronomy Picture of the Day MCP server with Authentication...")
    logger.info("Authentication: Clients must provide Authorization: Bearer YOUR_API_KEY")
    
    # Get configuration from environment
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logger.info(f"Server will listen on port {port}")
    
    try:
        mcp.run(
            transport="streamable-http",
            port=port,
            host="0.0.0.0",
            path="/mcp",
            log_level=log_level.lower()
        )
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        raise


if __name__ == "__main__":
    run_server() 