"""
Settings Configuration
From Hasif's Workspace

Application settings and configuration management.
Author: Hasif50
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings configuration."""

    # Application Information
    APP_TITLE = os.getenv("APP_TITLE", "Automated Essay Grader")
    APP_DESCRIPTION = os.getenv(
        "APP_DESCRIPTION", "AI-Powered Essay Analysis and Grading System"
    )
    APP_VERSION = "1.0.0"
    WORKSPACE_ATTRIBUTION = os.getenv("WORKSPACE_ATTRIBUTION", "Hasif's Workspace")
    DEVELOPER_NAME = os.getenv("DEVELOPER_NAME", "Hasif50")

    # AI Model Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

    # Azure Configuration
    AZURE_API_KEY = os.getenv("AZURE_API_KEY")
    AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2023-05-15")

    # Cohere Configuration
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")

    # Essay Processing Configuration
    MAX_ESSAY_LENGTH = int(os.getenv("MAX_ESSAY_LENGTH", "10000"))
    MIN_ESSAY_LENGTH = 50
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "nl": "Nederlands",
    }

    # Grading Configuration
    ENABLE_PLAGIARISM_CHECK = (
        os.getenv("ENABLE_PLAGIARISM_CHECK", "true").lower() == "true"
    )
    ENABLE_GRAMMAR_CHECK = os.getenv("ENABLE_GRAMMAR_CHECK", "true").lower() == "true"
    ENABLE_STYLE_ANALYSIS = os.getenv("ENABLE_STYLE_ANALYSIS", "true").lower() == "true"
    DEFAULT_RUBRIC = os.getenv("DEFAULT_RUBRIC", "learning_story")

    # File Upload Configuration
    MAX_FILE_SIZE = os.getenv("MAX_FILE_SIZE", "10MB")
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,txt").split(",")

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///essays.db")

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

    # Available Models
    AVAILABLE_MODELS = {
        "openai": {
            "gpt-4": {
                "name": "GPT-4",
                "description": "Most capable model for complex analysis",
                "max_tokens": 4000,
                "cost_tier": "high",
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "description": "Fast and efficient for most tasks",
                "max_tokens": 4000,
                "cost_tier": "medium",
            },
        },
        "azure_openai": {
            "gpt-4": {
                "name": "Azure GPT-4",
                "description": "Enterprise-grade GPT-4",
                "max_tokens": 4000,
                "cost_tier": "high",
            },
            "gpt-35-turbo": {
                "name": "Azure GPT-3.5 Turbo",
                "description": "Enterprise-grade GPT-3.5",
                "max_tokens": 4000,
                "cost_tier": "medium",
            },
        },
    }

    # Rubric Types
    AVAILABLE_RUBRICS = {
        "learning_story": {
            "name": "Learning Story Rubric",
            "description": "For learning stories with context, goals, approach, and substantiation",
            "criteria": [
                "context",
                "learning_goals",
                "learning_approach",
                "substantiation",
            ],
        },
    }

    # Grade Scale
    GRADE_SCALE = {
        "A+": {"min": 97, "max": 100, "description": "Exceptional"},
        "A": {"min": 93, "max": 96, "description": "Excellent"},
        "A-": {"min": 90, "max": 92, "description": "Very Good"},
        "B+": {"min": 87, "max": 89, "description": "Good"},
        "B": {"min": 83, "max": 86, "description": "Above Average"},
        "B-": {"min": 80, "max": 82, "description": "Satisfactory"},
        "C+": {"min": 77, "max": 79, "description": "Fair"},
        "C": {"min": 73, "max": 76, "description": "Average"},
        "C-": {"min": 70, "max": 72, "description": "Below Average"},
        "D+": {"min": 67, "max": 69, "description": "Poor"},
        "D": {"min": 63, "max": 66, "description": "Very Poor"},
        "D-": {"min": 60, "max": 62, "description": "Minimal"},
        "F": {"min": 0, "max": 59, "description": "Failing"},
    }

    # Analysis Features
    ANALYSIS_FEATURES = {
        "basic_stats": {
            "enabled": True,
            "description": "Word count, sentence count, paragraph analysis",
        },
        "readability": {
            "enabled": True,
            "description": "Flesch-Kincaid, Gunning Fog, and other readability metrics",
        },
        "grammar_analysis": {
            "enabled": ENABLE_GRAMMAR_CHECK,
            "description": "Grammar, mechanics, and sentence structure analysis",
        },
        "style_analysis": {
            "enabled": ENABLE_STYLE_ANALYSIS,
            "description": "Writing style, voice, and word choice evaluation",
        },
        "structure_analysis": {
            "enabled": True,
            "description": "Essay organization and paragraph structure",
        },
        "vocabulary_analysis": {
            "enabled": True,
            "description": "Vocabulary complexity and diversity",
        },
        "sentiment_analysis": {
            "enabled": True,
            "description": "Emotional tone and sentiment evaluation",
        },
        "plagiarism_check": {
            "enabled": ENABLE_PLAGIARISM_CHECK,
            "description": "Basic plagiarism and similarity detection",
        },
    }

    # UI Configuration
    UI_CONFIG = {
        "theme": {
            "primary_color": "#1f77b4",
            "secondary_color": "#ff7f0e",
            "success_color": "#2ca02c",
            "warning_color": "#ff7f0e",
            "error_color": "#d62728",
        },
        "layout": {
            "sidebar_width": 300,
            "main_content_width": 800,
            "max_content_width": 1200,
        },
        "display": {
            "show_debug_info": False,
            "show_analysis_details": True,
            "show_workspace_attribution": True,
        },
    }

    # Export Configuration
    EXPORT_CONFIG = {
        "formats": ["pdf", "html", "json", "csv"],
        "default_format": "pdf",
        "include_essay_text": False,  # For privacy
        "include_detailed_feedback": True,
        "include_analysis_data": True,
    }

    @classmethod
    def get_model_config(cls, provider: str, model: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        return cls.AVAILABLE_MODELS.get(provider, {}).get(model, {})

    @classmethod
    def get_rubric_config(cls, rubric_type: str) -> Dict[str, Any]:
        """Get configuration for a specific rubric."""
        return cls.AVAILABLE_RUBRICS.get(
            rubric_type, cls.AVAILABLE_RUBRICS["learning_story"]
        )

    @classmethod
    def is_feature_enabled(cls, feature: str) -> bool:
        """Check if a specific analysis feature is enabled."""
        return cls.ANALYSIS_FEATURES.get(feature, {}).get("enabled", False)

    @classmethod
    def get_max_file_size_bytes(cls) -> int:
        """Get maximum file size in bytes."""
        size_str = cls.MAX_FILE_SIZE.upper()
        if size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        else:
            return int(size_str)

    @classmethod
    def validate_configuration(cls) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check required API keys
        if not cls.OPENAI_API_KEY and not cls.AZURE_API_KEY:
            issues.append(
                "No AI API keys configured. Set OPENAI_API_KEY or AZURE_API_KEY."
            )

        if cls.AZURE_API_KEY and not cls.AZURE_ENDPOINT:
            issues.append("Azure API key provided but AZURE_ENDPOINT not set.")

        # Check file size configuration
        try:
            cls.get_max_file_size_bytes()
        except ValueError:
            issues.append(
                "Invalid MAX_FILE_SIZE format. Use format like '10MB' or '5000KB'."
            )

        # Check numeric configurations
        try:
            float(cls.OPENAI_TEMPERATURE)
            if not 0 <= float(cls.OPENAI_TEMPERATURE) <= 1:
                issues.append("OPENAI_TEMPERATURE must be between 0 and 1.")
        except ValueError:
            issues.append("Invalid OPENAI_TEMPERATURE value.")

        try:
            int(cls.OPENAI_MAX_TOKENS)
            if int(cls.OPENAI_MAX_TOKENS) <= 0:
                issues.append("OPENAI_MAX_TOKENS must be positive.")
        except ValueError:
            issues.append("Invalid OPENAI_MAX_TOKENS value.")

        return issues

    @classmethod
    def get_workspace_info(cls) -> Dict[str, str]:
        """Get workspace attribution information."""
        return {
            "workspace": cls.WORKSPACE_ATTRIBUTION,
            "developer": cls.DEVELOPER_NAME,
            "version": cls.APP_VERSION,
            "title": cls.APP_TITLE,
            "description": cls.APP_DESCRIPTION,
        }


# Create global settings instance
settings = Settings()

# Validate configuration on import
config_issues = settings.validate_configuration()
if config_issues:
    print("Configuration Issues Found:")
    for issue in config_issues:
        print(f"  - {issue}")
