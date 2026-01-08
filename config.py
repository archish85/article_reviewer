"""Configuration management for the Article Reviewer."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for managing API keys and settings."""

    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

    # Cost Control Settings
    REQUIRE_COST_APPROVAL = os.getenv('REQUIRE_COST_APPROVAL', 'true').lower() == 'true'
    MAX_AUTO_APPROVE_COST = float(os.getenv('MAX_AUTO_APPROVE_COST', '0.10'))

    # Gemini Pricing (per 1M tokens) - Update as needed
    # Source: https://ai.google.dev/pricing
    GEMINI_PRICING = {
        'gemini-2.5-flash': {
            'input': 0.075,  # $0.075 per 1M input tokens
            'output': 0.30   # $0.30 per 1M output tokens
        },
        'gemini-2.5-pro': {
            'input': 1.25,   # $1.25 per 1M input tokens
            'output': 5.00   # $5.00 per 1M output tokens
        },
        'gemini-flash-latest': {
            'input': 0.075,  # $0.075 per 1M input tokens
            'output': 0.30   # $0.30 per 1M output tokens
        },
        'gemini-pro-latest': {
            'input': 1.25,   # $1.25 per 1M input tokens
            'output': 5.00   # $5.00 per 1M output tokens
        }
    }

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in your .env file. "
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )

        if cls.GEMINI_MODEL not in cls.GEMINI_PRICING:
            raise ValueError(
                f"Invalid GEMINI_MODEL: {cls.GEMINI_MODEL}. "
                f"Available models: {', '.join(cls.GEMINI_PRICING.keys())}"
            )

    @classmethod
    def get_pricing(cls, model=None):
        """Get pricing information for a specific model."""
        model = model or cls.GEMINI_MODEL
        return cls.GEMINI_PRICING.get(model, cls.GEMINI_PRICING['gemini-2.5-flash'])
