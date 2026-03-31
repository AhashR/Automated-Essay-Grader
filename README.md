# HvA Learning Story Feedback Agent

## Overview

The HvA Learning Story Feedback Agent is a Python-based application that provides AI-generated feedback on student learning stories. It leverages Google Gemini via LangChain to process and evaluate learning stories efficiently.

## Features

- **AI-Powered Learning Story Analysis** - Comprehensive evaluation of learning story content, structure, and quality
- **Multi-Criteria Grading** - Assessment across dimensions including grammar, coherence, reflection depth, and creativity
- **Real-time Feedback** - Instant detailed feedback with suggestions for improvement
- **Rubric-Based Scoring** - Customizable grading rubrics for different learning story types
- **Export Capabilities** - Generate detailed reports in PDF and CSV formats
- **Grounded Feedback** - Prioritizes internal learning story examples (vector search) for tailored responses

## Future Features

- Integration with Learning Management Systems (LMS)
- Multi-language support for essay grading
- Batch processing for multiple essays
- Teacher dashboard for class-wide analytics
- Student progress tracking over time

## Setup Instructions

**Clone the Repository**:
```bash
git clone https://github.com/<your-org>/HvA-Feedback-Agent.git
cd HvA-Feedback-Agent
```

**Install Dependencies**:
```bash
pip install -r requirements.txt
```

**Set Up Environment Variables**:
Copy `.env.sample` to `.env` and fill in your API keys:
```bash
cp .env.sample .env
```

Edit the `.env` file with your API credentials:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Run the Application**:
```bash
python app.py
```

## Context grounding

- Internal examples: stored in `data/examples/learning_stories.json` and searched with TF-IDF; edit or replace with your own HvA learning stories.
- Custom location: point `LEARNING_STORY_VECTOR_PATH` to a different JSON file with example learning stories.

## How to Contribute

We welcome contributions from the community! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## Project Structure

```
HvA-Feedback-Agent/
│
├── .env.sample
├── .gitignore
├── .env
├── app.py
├── requirements.txt
├── README.md
├── CONTRIBUTING.md
├── LICENSE
│
├── src/
│   ├── __init__.py
│   ├── essay_analyzer.py
│   ├── grading_engine.py
│   ├── feedback_generator.py
│   └── utils.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── prompts.py
│
├── data/
│   ├── sample_essays/
│   ├── rubrics/
│   └── outputs/
│
├── tests/
│   ├── __init__.py
│   ├── test_analyzer.py
│   ├── test_grading.py
│   └── test_utils.py
│
└── docs/
    ├── user_guide.md
    ├── api_reference.md
    └── deployment_guide.md
```

## Code Flow

**Environment and Configuration Files**:
- `.env` - Contains API keys and configuration settings
- `.env.sample` - Template for environment variables
- `.gitignore` - Specifies files to ignore in version control

**Python Scripts**:
- `app.py` - Main Flask application entry point
- `src/essay_analyzer.py` - Core essay analysis functionality
- `src/grading_engine.py` - Grading logic and scoring algorithms
- `src/feedback_generator.py` - AI-powered feedback generation
- `config/prompts.py` - LLM prompt templates for different grading criteria

**Data Handling**:
- `data/` - Contains sample essays, grading rubrics, and output files
- Essay parsing and text extraction from various formats (PDF, DOCX, TXT)

**Essay Grading Process**:
- Upload essay through the Flask web interface
- Text extraction and preprocessing
- Multi-criteria analysis using AI models
- Score calculation based on rubric
- Detailed feedback generation
- Report generation and export

**Dependencies**:
- `requirements.txt` - All required Python packages

**Documentation**:
- `README.md` - Project overview and setup instructions
- `docs/` - Comprehensive documentation for users and developers

## Key Components

### **`app.py`**:
Main Flask application that provides the user interface for uploading essays and displaying results.

### **`src/essay_analyzer.py`**:
Core analysis engine that processes learning stories and extracts key features for grading.

### **`src/grading_engine.py`**:
Implements the grading logic using AI models to evaluate learning stories across multiple criteria.

### **`src/feedback_generator.py`**:
Generates detailed, constructive feedback to help students improve their learning stories.

### **`config/prompts.py`**:
Contains all prompt templates used for different aspects of learning story evaluation.

## Technology Stack

- **Language**: Python 3.10+
- **Framework**: Flask for web interface
- **AI Models**: Google Gemini
- **Libraries**: LangChain, pandas, numpy, nltk
- **Cloud**: Flexible (container-ready)

## About

Real-world Problem Solved: Assists HvA students with actionable AI feedback on their learning stories.
The HvA Learning Story Feedback Agent is designed to assist educators and students by providing consistent, detailed, and constructive feedback on learning stories. This tool aims to enhance the learning experience through AI-powered analysis.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 

## Acknowledgments

- Built with modern AI technologies for educational enhancement
- Designed to support both educators and students
