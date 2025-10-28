# NASA Astronomy Picture of the Day MCP Server Implementation Guide

You are working on implementing the NASA Astronomy Picture of the Day MCP (Model Context Protocol) server. The basic structure has been set up, and your task is to implement the actual API integration.

## API Information

- **API Name**: NASA Astronomy Picture of the Day
- **Documentation**: [https://api.nasa.gov/](https://api.nasa.gov/)
- **Website**: [https://api.nasa.gov/planetary/apod](https://api.nasa.gov/planetary/apod)
- **SDK**: `nasapy` (already included in pyproject.toml)
- **Authentication**: Required - API key via `NASA_ASTRONOMY_PICTURE_OF_THE_DAY_API_KEY` environment variable
## Implementation Checklist

### 1. Update Deployment Configuration

**IMPORTANT**: Update the `deployment_params.json` file with all implemented capabilities:

```json
{
  "mcp_server": {
    "capabilities": [
      // Replace these with your actual implemented tool names
      "search_nasa_astronomy_picture_of_the_day",
      "get_nasa_astronomy_picture_of_the_day_info",
      // Add all other tools you implement
    ]
  },
  "tags": ["nasa astronomy picture of the day", "api", /* add relevant tags like "search", "data", etc. */]
}
```

### 2. Study the API Documentation

First, thoroughly review the API documentation at https://api.nasa.gov/ to understand:
- Available endpoints
- Request/response formats
- Rate limits
- Error handling
- Authentication method (API key placement in headers, query params, etc.)- Specific features and capabilities to expose as tools

### 3. Implement API Client Functions

Add functions to call the NASA Astronomy Picture of the Day API with retry support. Example pattern:

```python
from retry import retry

# Using the SDK with retry decorator
@retry(tries=2, delay=1, backoff=2, jitter=(1, 3))
def call_nasa_astronomy_picture_of_the_day_api(endpoint: str, params: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """Call NASA Astronomy Picture of the Day API using the SDK with automatic retry."""
    # Initialize the SDK client
    client = nasapy.Client(api_key=api_key)
    
    # Make the API call - will retry once on any exception
    try:
        response = client.call_endpoint(params)
        return response.to_dict()
    except Exception as e:
        raise Exception(f"NASA Astronomy Picture of the Day API error: {str(e)}")
```

#### Retry Configuration Explained

- `tries=2`: Total attempts (1 original + 1 retry)
- `delay=1`: Wait 1 second before retry
- `backoff=2`: Multiply delay by 2 for subsequent retries (if more than 2 tries)
- `jitter=(1, 3)`: Add random delay between 1-3 seconds to avoid thundering herd

### 4. Create MCP Tools

Replace the `example_tool` placeholder with actual tools. **Each tool you implement MUST be added to the `capabilities` array in `deployment_params.json`**.

#### Search/Query Tool
```python
@mcp.tool()
async def search_nasa_astronomy_picture_of_the_day(
    context: Context,
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search NASA Astronomy Picture of the Day for [specific data type].
    
    Args:
        context: MCP context (injected automatically)
        query: Search query
        limit: Maximum number of results
        
    Returns:
        Dictionary with search results
    """
    api_key = get_session_api_key(context)
    if not api_key:
        return {"error": "No API key found. Please authenticate with Authorization: Bearer YOUR_API_KEY"}
    
    try:
        # The call_nasa_astronomy_picture_of_the_day_api function already has retry logic
        results = call_nasa_astronomy_picture_of_the_day_api(
            "search",  # TODO: Use actual endpoint
            {"q": query, "limit": limit},
api_key)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}
```

#### Get/Fetch Tool
```python
@mcp.tool()
async def get_nasa_astronomy_picture_of_the_day_info(
    context: Context,
    item_id: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific item.
    
    Args:
        context: MCP context (injected automatically)
        item_id: ID of the item to fetch
        
    Returns:
        Dictionary with item details
    """
    # Similar implementation pattern
```

#### Create/Update Tool (if applicable)
```python
@mcp.tool()
async def create_nasa_astronomy_picture_of_the_day_item(
    context: Context,
    name: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new item in NASA Astronomy Picture of the Day.
    
    Args:
        context: MCP context (injected automatically)
        name: Name of the item
        data: Additional data for the item
        
    Returns:
        Dictionary with creation result
    """
    # Implementation here
```

### 5. Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks and return user-friendly error messages
2. **Input Validation**: Validate parameters before making API calls
3. **Rate Limiting**: Respect API rate limits, implement delays if needed
4. **Response Formatting**: Return consistent response structures across all tools
5. **Logging**: Use the logger for debugging but don't log sensitive data like API keys
6. **Documentation**: Write clear docstrings for each tool explaining parameters and return values
7. **Retry Strategy**: Use the `@retry` decorator on API client functions for resilience

#### Retry Best Practices

- **Only use retry for external API calls** - Don't add retry to internal functions, database operations, or file operations
- **Apply retry to API client functions**, not MCP tool functions directly
- **Use `tries=2`** (1 original attempt + 1 retry) to balance reliability and responsiveness
- **Add jitter** to prevent thundering herd when multiple clients retry simultaneously
- **Don't retry on authentication errors** - use conditional retry if needed:
  ```python
  from retry import retry
  import requests
  
  def retry_on_server_error(exception):
      """Only retry on server errors (5xx), not client errors (4xx)"""
      if isinstance(exception, requests.HTTPError):
          return 500 <= exception.response.status_code < 600
      return True  # Retry on other exceptions like network errors
  
  @retry(tries=2, delay=1, backoff=2, jitter=(1, 3), exceptions=retry_on_server_error)
  def call_api_with_smart_retry(endpoint, params, api_key):
      # API implementation
      pass
  ```
- **Log retry attempts** for debugging:
  ```python
  @retry(tries=2, delay=1, logger=logger)
  def call_nasa_astronomy_picture_of_the_day_api(...):
      # Implementation
  ```

#### When to Use Retry

**✅ DO use retry for:**
- HTTP requests to external APIs
- Network operations that can fail temporarily
- Remote service calls that may experience transient errors

**❌ DON'T use retry for:**
- MCP tool functions (they should handle errors gracefully instead)
- Local file operations
- Database queries (unless specifically needed for connection issues)
- Authentication/validation logic
- Data processing or computation functions

### 6. Testing

After implementing tools, test them:

1. Run the server locally:
   ```bash
   ./run_local_docker.sh
   ```

2. Use the health check script:
   ```bash
   python mcp_health_check.py
   ```

3. Test with CrewAI:
   ```python
from traia_iatp.mcp.traia_mcp_adapter import create_mcp_adapter_with_auth
   
   # Authenticated connection
   with create_mcp_adapter_with_auth(
       url="http://localhost:8000/mcp/",
       api_key="your-api-key"
   ) as tools:
       # Test your tools
       for tool in tools:
           print(f"Tool: {tool.name}")
   ```

### 7. Update Documentation

After implementing the tools:

1. **Update README.md**:
   - List all implemented tools with descriptions
   - Add usage examples for each tool
   - Include any specific setup instructions

2. **Update deployment_params.json**:
   - Ensure ALL tool names are in the `capabilities` array
   - Add relevant tags based on functionality
   - Verify authentication settings match implementation

3. **Add Tool Examples** in README.md:
   ```python
   # Example usage of each tool
   result = await tool.search_nasa_astronomy_picture_of_the_day(query="example", limit=5)
   ```

### 8. Pre-Deployment Checklist

Before marking the implementation as complete:

- [ ] All placeholder code has been replaced with actual implementation
- [ ] All tools are properly documented with docstrings
- [ ] Error handling is implemented for all API calls
- [ ] `deployment_params.json` contains all tool names in capabilities
- [ ] README.md has been updated with usage examples
- [ ] Server runs successfully with `./run_local_docker.sh`
- [ ] Health check passes
- [ ] At least one tool works end-to-end

### 9. Common NASA Astronomy Picture of the Day Use Cases

Based on the API documentation, consider implementing tools for these common use cases:

1. **TODO**: List specific use cases based on NASA Astronomy Picture of the Day capabilities
2. **TODO**: Add more relevant use cases
3. **TODO**: Include any special features of this API

### 10. Example API Calls

Here are some example API calls from the NASA Astronomy Picture of the Day documentation that you should implement:

```
TODO: Add specific examples from the API docs
```

## Need Help?

- Check the NASA Astronomy Picture of the Day API documentation: https://api.nasa.gov/
- Review the MCP specification: https://modelcontextprotocol.io
- Look at other MCP server examples in the Traia-IO organization

Remember: The goal is to make NASA Astronomy Picture of the Day's capabilities easily accessible to AI agents through standardized MCP tools. 