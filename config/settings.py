"""
Settings Configuration

Application settings and configuration management.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings configuration."""

    # Application Information
    APP_TITLE = os.getenv("APP_TITLE", "HvA Learning Story Feedback Agent")
    APP_DESCRIPTION = os.getenv(
        "APP_DESCRIPTION",
        "AI-generated feedback for HvA students' learning stories",
    )
    APP_VERSION = "1.0.0"
    WORKSPACE_ATTRIBUTION = os.getenv("WORKSPACE_ATTRIBUTION", "HvA Feedback Agent")
    DEVELOPER_NAME = os.getenv("DEVELOPER_NAME", "HvA Feedback Agent Team")

    # Google Gemini Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Cohere Configuration
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")

    # Learning Story Processing Configuration
    MAX_LEARNING_STORY_LENGTH = int(
        os.getenv("MAX_LEARNING_STORY_LENGTH", os.getenv("MAX_ESSAY_LENGTH", "10000"))
    )
    MIN_LEARNING_STORY_LENGTH = int(os.getenv("MIN_LEARNING_STORY_LENGTH", "50"))
    # Backward compatibility for legacy naming
    MAX_ESSAY_LENGTH = MAX_LEARNING_STORY_LENGTH
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "nl": "Nederlands",
    }

    # Grading Configuration
    ENABLE_GRAMMAR_CHECK = os.getenv("ENABLE_GRAMMAR_CHECK", "true").lower() == "true"
    ENABLE_STYLE_ANALYSIS = os.getenv("ENABLE_STYLE_ANALYSIS", "true").lower() == "true"
    DEFAULT_RUBRIC = os.getenv("DEFAULT_RUBRIC", "learning_story")

    # File Upload Configuration
    MAX_FILE_SIZE = os.getenv("MAX_FILE_SIZE", "10MB")
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,txt").split(",")

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///learning_stories.db")

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

    # Available Models
    AVAILABLE_MODELS = {
        "gemini": {
            "gemini-2.5-flash": {
                "name": "Gemini 2.5 Flash",
                "description": "Best all-rounder for fast, reasoning-capable feedback",
                "max_tokens": 4000,
                "cost_tier": "low",
            },
            "gemini-2.5-pro": {
                "name": "Gemini 2.5 Pro",
                "description": "Highest quality option for complex rubric-based evaluation",
                "max_tokens": 4000,
                "cost_tier": "high",
            },
            "gemini-2.5-flash-lite": {
                "name": "Gemini 2.5 Flash Lite",
                "description": "Lightweight option for high-volume batch processing",
                "max_tokens": 2000,
                "cost_tier": "low",
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
            "description": "Learning story organization and paragraph structure",
        },
        "vocabulary_analysis": {
            "enabled": True,
            "description": "Vocabulary complexity and diversity",
        },
        "sentiment_analysis": {
            "enabled": True,
            "description": "Emotional tone and sentiment evaluation",
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

