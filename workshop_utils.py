"""
Workshop Utilities

Common helper functions used across all workshop notebooks.
"""

import os
from dotenv import load_dotenv


def validate_env(required_vars: list[str] | None = None) -> bool:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names.
                      If None, uses default Azure OpenAI variables.
    
    Returns:
        True if all required variables are set, False otherwise.
    
    Example:
        >>> from workshop_utils import validate_env
        >>> validate_env()  # Uses default Azure OpenAI vars
        >>> validate_env(["AZURE_OPENAI_ENDPOINT", "CUSTOM_VAR"])  # Custom vars
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Default required variables for Azure OpenAI
    if required_vars is None:
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"
        ]
    
    # Check for missing variables
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n📝 Please create a .env file with these variables or set them in your environment.")
        return False
    else:
        print("✅ Setup validated! All required environment variables are set.")
        return True