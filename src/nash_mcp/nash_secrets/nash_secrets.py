import json

from nash_mcp.constants import MAC_SECRETS_PATH


def nash_secrets() -> str:
    """List all available API keys and credentials that can be used in your code.

    ALWAYS CHECK FOR AVAILABLE SECRETS FIRST before requesting API keys from users
    or hardcoding credentials in your code. This tool provides safe access to the user's
    stored credentials while protecting their actual values.

    HOW TO USE SECRETS:
    1. Call nash_secrets() to see what secrets are available
    2. Note the key names (e.g., OPENAI_API_KEY, GITHUB_TOKEN)
    3. In execute_python(), access secrets as environment variables:
       ```python
       import os

       # Get an API key from the environment
       api_key = os.environ.get('SECRET_NAME')

       # Check if the key exists before using
       if api_key:
           # Use the API key safely
           print(f"Using API key: {api_key[:4]}...")  # Only show first few chars

           # Use with API clients
           # client = SomeApiClient(api_key=api_key)
       else:
           print("Required API key not found")
       ```

    SECURITY BEST PRACTICES:
    - Never print full secret values in your code output
    - Only use secrets for their intended purpose
    - Don't transmit secrets to external services not related to their purpose
    - Always handle the case where a secret might not exist
    - Don't modify or delete the secrets file

    IMPLEMENTATION DETAILS:
    - Each secret has a 'key' and 'description' field
    - Only key names and descriptions are returned, not actual values
    - Secret values are automatically loaded as environment variables by execute_python()
    - No need to manually load secrets; they're available via os.environ.get()

    Returns:
        A formatted list of all available secrets with their keys and descriptions
        Does not include actual secret values for security reasons
    """
    try:
        if not MAC_SECRETS_PATH.exists():
            return "No secrets file found."

        with open(MAC_SECRETS_PATH, "r") as f:
            secrets = json.load(f)

        if not secrets:
            return "No secrets available."

        result = "Available secrets:\n\n"
        for secret in secrets:
            key = secret.get("key", "N/A")
            desc = secret.get("description", "No description")
            result += f"Key: {key}\n"
            result += f"Description: {desc}\n\n"

        return result
    except Exception as e:
        return f"Error reading secrets: {str(e)}"
