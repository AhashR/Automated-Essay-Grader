# API Reference - HvA Learning Story Feedback Agent

This document provides technical reference for the HvA Learning Story Feedback Agent components and modules.

## Table of Contents

1. [Core Modules](#core-modules)
2. [Learning Story Analyzer](#learning-story-analyzer)
3. [Grading Engine](#grading-engine)
4. [Feedback Generator](#feedback-generator)
5. [Utilities](#utilities)
6. [Configuration](#configuration)
7. [Data Structures](#data-structures)
8. [Error Handling](#error-handling)

## Core Modules

### Module Structure

```
src/
├── essay_analyzer.py      # Core analysis engine
├── grading_engine.py      # Grading and scoring
├── feedback_generator.py  # Feedback generation
└── utils.py              # Utility functions

config/
├── settings.py           # Application settings
└── prompts.py           # AI prompt templates
```

## Learning Story Analyzer

### Class: `EssayAnalyzer`

Main class for learning story analysis functionality.

#### Constructor

```python
EssayAnalyzer(
    model_provider: str = "gemini",
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.3,
    max_tokens: int = 2000
)
```

**Parameters:**
- `model_provider`: AI model provider ("gemini" or "mock" for testing)
- `model_name`: Specific model to use
- `temperature`: Model temperature for response generation
- `max_tokens`: Maximum tokens for model responses

#### Methods

##### `analyze_essay()`

```python
analyze_essay(
    essay_text: str,
    prompt: Optional[str] = None,
    enable_grammar: bool = True,
    enable_style: bool = True,
    enable_sentiment: bool = True
) -> Dict[str, Any]
```

Performs comprehensive learning story analysis.

**Parameters:**
- `essay_text`: The learning story content to analyze
- `prompt`: Optional learning story prompt/topic
- `enable_grammar`: Whether to perform grammar analysis
- `enable_style`: Whether to perform style analysis
- `enable_sentiment`: Whether to perform sentiment analysis

**Returns:**
```python
{
    "basic_stats": {
        "word_count": int,
        "sentence_count": int,
        "paragraph_count": int,
        "character_count": int,
        "avg_words_per_sentence": float,
        "avg_sentences_per_paragraph": float
    },
    "readability": {
        "flesch_reading_ease": float,
        "flesch_kincaid_grade": float,
        "gunning_fog": float,
        "automated_readability_index": float,
        "coleman_liau_index": float,
        "reading_time_minutes": float
    },
    "structure": {
        "paragraph_count": int,
        "avg_paragraph_length": float,
        "has_clear_introduction": bool,
        "has_clear_conclusion": bool,
        "transition_word_count": int,
        "paragraph_lengths": List[int]
    },
    "vocabulary": {
        "total_words": int,
        "unique_words": int,
        "lexical_diversity": float,
        "avg_word_length": float,
        "complex_word_count": int,
        "complex_word_ratio": float
    },
    "grammar": {
        "grammar_issues": List[Dict],
        "issue_count": int,
        "polarity": float,
        "subjectivity": float
    },
    "style": {
        "sentence_variety_score": float,
        "sentence_starter_variety": float,
        "avg_sentence_length": float,
        "sophisticated_word_ratio": float,
        "style_issues": List[Dict]
    },
    "sentiment": {
        "positive": float,
        "negative": float,
        "neutral": float,
        "compound": float,
        "overall_tone": str
    },
    "content_analysis": {
        "ai_analysis": str,
        "analysis_provider": str,
        "workspace_attribution": str
    }
}
```

##### Private Methods

- `_get_basic_statistics(text: str) -> Dict[str, int]`
- `_analyze_readability(text: str) -> Dict[str, float]`
- `_analyze_structure(text: str) -> Dict[str, Any]`
- `_analyze_vocabulary(text: str) -> Dict[str, Any]`
- `_analyze_grammar(text: str) -> Dict[str, Any]`
- `_analyze_style(text: str) -> Dict[str, Any]`
- `_analyze_sentiment(text: str) -> Dict[str, float]`

## Grading Engine

### Class: `GradingEngine`

Handles essay grading based on customizable rubrics.

#### Constructor

```python
GradingEngine(
    rubric_type: str = "standard",
    analyzer: EssayAnalyzer = None
)
```

**Parameters:**
- `rubric_type`: Type of rubric ("standard", "academic", "creative_writing", "argumentative")
- `analyzer`: EssayAnalyzer instance for AI capabilities

#### Methods

##### `grade_essay()`

```python
grade_essay(
    essay_text: str,
    analysis_results: Dict[str, Any],
    prompt: Optional[str] = None
) -> Dict[str, Any]
```

Grades an essay based on the selected rubric.

**Returns:**
```python
{
    "overall_score": float,
    "letter_grade": str,
    "criteria_scores": Dict[str, float],
    "content_score": float,
    "organization_score": float,
    "grammar_score": float,
    "style_score": float,
    "detailed_feedback": str,
    "rubric_used": str,
    "grading_breakdown": Dict[str, Any],
    "workspace_attribution": str
}
```

### Data Classes

#### `GradingCriteria`

```python
@dataclass
class GradingCriteria:
    name: str
    weight: float
    max_score: int
    description: str
```

#### `GradeResult`

```python
@dataclass
class GradeResult:
    overall_score: float
    letter_grade: str
    criteria_scores: Dict[str, float]
    feedback: str
    rubric_used: str
```

## Feedback Generator

### Class: `FeedbackGenerator`

Generates detailed, constructive feedback for essays.

#### Constructor

```python
FeedbackGenerator(analyzer: EssayAnalyzer = None)
```

#### Methods

##### `generate_feedback()`

```python
generate_feedback(
    essay_text: str,
    analysis_results: Dict[str, Any],
    grade_results: Dict[str, Any],
    prompt: Optional[str] = None
) -> Dict[str, str]
```

**Returns:**
```python
{
    "ai_comprehensive_feedback": str,
    "strengths": str,
    "improvements": str,
    "suggestions": str,
    "grammar_feedback": str,
    "style_feedback": str,
    "structure_feedback": str,
    "workspace_attribution": str
}
```

## Utilities

### Document Processing

#### `load_document()`

```python
load_document(uploaded_file) -> str
```

Loads and extracts text from uploaded documents.

**Supported formats:** TXT, PDF, DOCX

#### `validate_file()`

```python
validate_file(uploaded_file) -> bool
```

Validates uploaded file for size and format.

### Report Generation

#### `generate_report()`

```python
generate_report(
    essay_text: str,
    analysis_results: Dict[str, Any],
    grade_results: Dict[str, Any],
    feedback: Dict[str, str],
    format: str = 'pdf',
    filename: Optional[str] = None
) -> str
```

Generates comprehensive reports in PDF or HTML format.

#### `save_results()`

```python
save_results(
    analysis_results: Dict[str, Any],
    grade_results: Dict[str, Any],
    feedback: Dict[str, str],
    format: str = 'json',
    filename: Optional[str] = None
) -> str
```

Saves analysis results to file in JSON or CSV format.

### Utility Functions

- `format_score_display(score: float, max_score: float) -> str`
- `get_performance_color(percentage: float) -> str`
- `truncate_text(text: str, max_length: int) -> str`
- `clean_text_for_analysis(text: str) -> str`
- `get_workspace_info() -> Dict[str, str]`

## Configuration

### Settings Class

#### `Settings`

Main configuration class with application settings.

**Key Properties:**
- `APP_TITLE`: Application title
- `GEMINI_API_KEY`: Google Gemini API key
- `MAX_LEARNING_STORY_LENGTH`: Maximum learning story length
- `AVAILABLE_MODELS`: Available AI models
- `AVAILABLE_RUBRICS`: Available grading rubrics
- `GRADE_SCALE`: Grade scale definitions

**Methods:**
- `get_model_config(provider: str, model: str) -> Dict[str, Any]`
- `get_rubric_config(rubric_type: str) -> Dict[str, Any]`
- `is_feature_enabled(feature: str) -> bool`
- `validate_configuration() -> List[str]`

### Prompt Templates

#### `PromptTemplates`

Collection of AI prompt templates.

**Available Prompts:**
- `CONTENT_ANALYSIS_PROMPT`
- `ORGANIZATION_ANALYSIS_PROMPT`
- `STYLE_ANALYSIS_PROMPT`
- `GRAMMAR_ANALYSIS_PROMPT`
- `COMPREHENSIVE_FEEDBACK_PROMPT`

**Methods:**
- `get_prompt(prompt_type: str, **kwargs) -> str`
- `format_prompt_context(prompt: str) -> str`
- `format_score_summary(scores: Dict[str, Any]) -> str`

## Data Structures

### Analysis Result Structure

```python
AnalysisResult = {
    "basic_stats": BasicStats,
    "readability": ReadabilityMetrics,
    "structure": StructureAnalysis,
    "vocabulary": VocabularyAnalysis,
    "grammar": GrammarAnalysis,
    "style": StyleAnalysis,
    "sentiment": SentimentAnalysis,
    "content_analysis": ContentAnalysis
}
```

### Grade Result Structure

```python
GradeResult = {
    "overall_score": float,
    "letter_grade": str,
    "criteria_scores": Dict[str, float],
    "detailed_feedback": str,
    "rubric_used": str,
    "grading_breakdown": Dict[str, Any]
}
```

### Feedback Structure

```python
FeedbackResult = {
    "strengths": str,
    "improvements": str,
    "suggestions": str,
    "grammar_feedback": str,
    "style_feedback": str,
    "structure_feedback": str,
    "ai_comprehensive_feedback": str
}
```

## Error Handling

### Common Exceptions

#### `ValueError`
- Raised for invalid input parameters
- Empty essay text
- Invalid rubric types

#### `Exception`
- AI model initialization failures
- API connection errors
- File processing errors

### Error Response Format

```python
{
    "error": True,
    "message": str,
    "error_type": str,
    "workspace_attribution": "HvA Feedback Agent"
}
```

## Usage Examples

### Basic Analysis

```python
from src.essay_analyzer import EssayAnalyzer

analyzer = EssayAnalyzer()
results = analyzer.analyze_essay("Your essay text here")
print(results["basic_stats"]["word_count"])
```

### Complete Grading Workflow

```python
from src.essay_analyzer import EssayAnalyzer
from src.grading_engine import GradingEngine
from src.feedback_generator import FeedbackGenerator

# Initialize components
analyzer = EssayAnalyzer()
grader = GradingEngine(rubric_type="standard", analyzer=analyzer)
feedback_gen = FeedbackGenerator(analyzer=analyzer)

# Analyze essay
essay_text = "Your essay content..."
analysis = analyzer.analyze_essay(essay_text)

# Grade essay
grades = grader.grade_essay(essay_text, analysis)

# Generate feedback
feedback = feedback_gen.generate_feedback(essay_text, analysis, grades)

print(f"Score: {grades['overall_score']}/100")
print(f"Grade: {grades['letter_grade']}")
```

### Custom Configuration

```python
from config.settings import Settings

# Check configuration
issues = Settings.validate_configuration()
if issues:
    print("Configuration issues:", issues)

# Get model info
model_info = Settings.get_model_config("gemini", "gemini-2.5-flash")
print(model_info)
```

---

## Version Information

**Version**: 1.0.0  
**Author**: HvA Feedback Agent Team  
**Workspace**: HvA Feedback Agent  
**Last Updated**: 2025

For technical support or questions about the API, please refer to the user guide or contact the development team.