# Contributing to Automated Essay Grader

Thank you for your interest in contributing to the Automated Essay Grader project! This document provides guidelines for contributing to this educational AI tool.

## Project Overview

The Automated Essay Grader is an AI-powered system designed to help educators and students by providing comprehensive essay analysis and grading. Built from Hasif's Workspace, this project aims to enhance the learning experience through innovative technology.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git for version control
- Basic understanding of AI/ML concepts
- Familiarity with Flask and LangChain

### Development Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/Hasif50/Automated-Essay-Grader.git
   cd Automated-Essay-Grader
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   ```bash
   cp .env.sample .env
   # Edit .env with your API keys
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality
- **Code Contributions**: Implement new features or fix bugs
- **Documentation**: Improve or expand documentation
- **Testing**: Add or improve test coverage
- **UI/UX Improvements**: Enhance user experience

### Contribution Process

1. **Check Existing Issues**
   - Look through existing issues to avoid duplicates
   - Comment on issues you'd like to work on

2. **Create an Issue** (for new features or bugs)
   - Use clear, descriptive titles
   - Provide detailed descriptions
   - Include steps to reproduce (for bugs)
   - Add relevant labels

3. **Fork and Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

4. **Make Changes**
   - Follow coding standards (see below)
   - Write clear commit messages
   - Add tests for new functionality
   - Update documentation as needed

5. **Test Your Changes**
   ```bash
   python -m pytest tests/
   python app.py  # Manual testing
   ```

6. **Submit a Pull Request**
   - Use a clear, descriptive title
   - Reference related issues
   - Provide a detailed description of changes
   - Include screenshots for UI changes

## Coding Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise
- Use type hints where appropriate

### Code Organization

- Place new features in appropriate modules
- Keep related functionality together
- Maintain clear separation of concerns
- Follow the existing project structure

### Documentation

- Update README.md for significant changes
- Add docstrings to new functions/classes
- Include inline comments for complex logic
- Update API documentation as needed

### Example Code Style

```python
def analyze_essay_content(
    essay_text: str,
    rubric_type: str = "standard",
    enable_ai_analysis: bool = True
) -> Dict[str, Any]:
    """
    Analyze essay content using specified rubric.
    
    Args:
        essay_text: The essay content to analyze
        rubric_type: Type of rubric to use for analysis
        enable_ai_analysis: Whether to include AI-powered analysis
        
    Returns:
        Dictionary containing analysis results
        
    Raises:
        ValueError: If essay_text is empty or rubric_type is invalid
    """
    if not essay_text.strip():
        raise ValueError("Essay text cannot be empty")
    
    # Implementation here
    return analysis_results
```

## Testing Guidelines

### Writing Tests

- Write unit tests for all new functions
- Include integration tests for complex features
- Test edge cases and error conditions
- Maintain good test coverage

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_analyzer.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Test Structure

```python
import pytest
from src.essay_analyzer import EssayAnalyzer

class TestEssayAnalyzer:
    def test_analyze_essay_valid_input(self):
        """Test essay analysis with valid input."""
        analyzer = EssayAnalyzer()
        result = analyzer.analyze_essay("Sample essay text")
        assert "basic_stats" in result
        assert result["basic_stats"]["word_count"] > 0
    
    def test_analyze_essay_empty_input(self):
        """Test essay analysis with empty input."""
        analyzer = EssayAnalyzer()
        with pytest.raises(ValueError):
            analyzer.analyze_essay("")
```

## Issue Guidelines

### Bug Reports

When reporting bugs, please include:

- **Environment**: OS, Python version, package versions
- **Steps to Reproduce**: Clear, numbered steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Screenshots**: If applicable
- **Error Messages**: Full error text

### Feature Requests

For feature requests, please provide:

- **Problem Description**: What problem does this solve?
- **Proposed Solution**: How should it work?
- **Alternatives Considered**: Other approaches you've thought of
- **Additional Context**: Any other relevant information

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No merge conflicts with main branch

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (please describe)

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots here

## Related Issues
Closes #issue_number
```

## Code Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Peer Review**: At least one maintainer reviews the code
3. **Feedback**: Address any requested changes
4. **Approval**: PR is approved and merged

## Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Be Collaborative

- Help others learn and grow
- Share knowledge and resources
- Provide constructive feedback
- Support fellow contributors

## Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes for significant contributions
- Project documentation

## Getting Help

If you need help:

1. **Check Documentation**: README.md and docs/
2. **Search Issues**: Look for similar questions
3. **Ask Questions**: Create an issue with the "question" label
4. **Contact Maintainers**: Reach out directly if needed

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Attribution

This project is maintained by Hasif50 and built from Hasif's Workspace. All contributions are valued and appreciated.

---

Thank you for contributing to the Automated Essay Grader project! Your efforts help make educational technology more accessible and effective.