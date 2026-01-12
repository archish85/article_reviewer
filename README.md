# Article Reviewer - Multi-Agent AI System

A powerful multi-agent article review system powered by Google's Gemini AI and CrewAI. This tool uses 5 different AI personas to provide comprehensive feedback on your articles, with built-in token estimation and cost tracking.

## Features

- **5 Expert Reviewers**: Senior Historian of Astronomy, Professional Editor, General Reader, Critical Skeptic, and Lead Data Scientist
- **Token & Cost Estimation**: Estimates and displays token usage and costs before making API calls
- **Cost Control**: Configurable approval prompts to control spending
- **Debate Mode**: Optional debate feature where reviewers discuss their findings
- **Comprehensive Reports**: Detailed markdown reports with individual reviews and synthesized feedback
- **Flexible Input**: Support for text files, markdown files, or direct text input
- **Rich Terminal Output**: Beautiful, color-coded terminal interface using Rich

## Prerequisites

- Python 3.9 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Installation

### 1. Clone or download this repository

```bash
cd article_reviewer
```

### 2. Create and activate a virtual environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

Copy the example environment file and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-pro
REQUIRE_COST_APPROVAL=true
MAX_AUTO_APPROVE_COST=0.10
```

## Usage

### Basic Usage

Review an article from a file:

```bash
python main.py path/to/your/article.txt
```

Review direct text (use quotes):

```bash
python main.py "Your article text goes here. This is a great way to test the system quickly."
```

### Advanced Options

Specify output file:

```bash
python main.py article.txt --output my_review.md
```

Use a specific Gemini model:

```bash
python main.py article.txt --model gemini-1.5-flash
```

Enable debate mode (reviewers discuss their findings):

```bash
python main.py article.txt --debate
```

Skip cost approval prompt (use with caution):

```bash
python main.py article.txt --no-approval
```

Combine options:

```bash
python main.py article.txt --model gemini-1.5-flash --debate --output detailed_review.md
```

### Full Command Reference

```bash
python main.py <article> [options]

Arguments:
  article              Path to article file or direct text in quotes

Options:
  --model MODEL        Gemini model to use (gemini-pro, gemini-1.5-pro, gemini-1.5-flash)
  --output, -o FILE    Output file path (default: review_report.md)
  --no-approval        Skip cost approval prompt
  --debate             Enable debate mode for reviewer discussion
  --help, -h           Show help message
```

## Copywriting Assistant (New!)

After receiving your review, use the **Copywriting Assistant** to get detailed copywriting suggestions and an AI-likeness rating.

### Usage

```bash
# Run copywriting analysis on your review report
python copywriter.py review_report.md

# If article was truncated in report, provide original article file
python copywriter.py review_report.md --article original_article.txt

# Generate a fully rewritten draft (AI does the rewriting for you!)
python copywriter.py review_report.md --generate-draft

# Specify custom output files for suggestions and draft
python copywriter.py review_report.md -o my_suggestions.md --generate-draft --draft-output my_draft.md

# Use a specific model
python copywriter.py review_report.md --model gemini-2.5-pro

# Complete workflow with draft generation
python copywriter.py review_report.md --article my_article.txt --generate-draft --model gemini-2.5-pro
```

### What It Provides

1. **AI Likeness Rating (1-10 scale)**
   - 1 = Entirely human-written, natural voice
   - 10 = Obviously AI-generated, formulaic
   - Identifies specific AI tells in your writing

2. **Specific Line Edits**
   - Before/after examples with explanations
   - Concrete suggestions for improvement

3. **Copywriting Recommendations**
   - Voice and tone adjustments
   - Engagement improvements
   - Flow and pacing suggestions

4. **Priority Fixes**
   - Top 3 most important changes

5. **Fully Rewritten Draft** (with `--generate-draft` flag)
   - Complete rewritten version of your article
   - Implements all copywriting suggestions automatically
   - More natural, human-like writing
   - Saves you time - let AI do the rewriting!

### Example Workflows

**Workflow 1: Manual Revision (you make the changes)**
```bash
# Step 1: Get comprehensive review
python main.py my_article.md -o review_report.md

# Step 2: Get copywriting suggestions
python copywriter.py review_report.md -o copywriting.md

# Step 3: Review both reports and manually revise your article
```

**Workflow 2: AI-Assisted Rewriting (AI does the work!)**
```bash
# Step 1: Get comprehensive review
python main.py my_article.md -o review_report.md

# Step 2: Get copywriting suggestions AND a fully rewritten draft
python copywriter.py review_report.md --generate-draft

# Step 3: Review the draft (article_draft.md) and suggestions (copywriting_suggestions.md)
# Use the draft as-is or as a starting point for your final version
```

---

## The Review Panel

Your article will be reviewed by 5 different AI personas:

1. **Senior Historian of Astronomy** - Ensures historical accuracy regarding the Geocentric and Heliocentric models, specializing in the Copernican Revolution
2. **Professional Editor** - Assesses structure, flow, grammar, and writing quality
3. **General Reader** - Checks readability and engagement for non-expert audiences
4. **Critical Skeptic** - Challenges assumptions and identifies logical gaps
5. **Lead Data Scientist** - Verifies technical accuracy of data science analogies, focusing on concepts like Concept Drift, Model Fitting, and Bias

After individual reviews, a **Review Moderator** synthesizes all feedback into a comprehensive, actionable report.

## Cost Management

### Token Estimation

Before making any API calls, the system:
1. Estimates the number of tokens required
2. Calculates the estimated cost based on Gemini pricing
3. Displays this information in a clear table
4. Requests your approval (unless disabled)

### Pricing Information

Current Gemini pricing (per 1 million tokens):

| Model | Input | Output |
|-------|-------|--------|
| gemini-pro | $0.50 | $1.50 |
| gemini-1.5-pro | $1.25 | $5.00 |
| gemini-1.5-flash | $0.075 | $0.30 |

**Tip**: For cost-effective reviews, use `gemini-1.5-flash` which is 6-10x cheaper than gemini-pro.

### Controlling Costs

Edit `.env` to configure cost controls:

```env
# Require approval before API calls
REQUIRE_COST_APPROVAL=true

# Auto-approve if estimated cost is below this (in USD)
MAX_AUTO_APPROVE_COST=0.10
```

## Example Workflow

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Review your article with cost-effective model
python main.py my_article.md --model gemini-1.5-flash --output review.md

# 3. Review the report
cat review.md

# 4. Deactivate when done
deactivate
```

## Output Report

The generated report includes:

- **Article Information**: Word count, character count, reviewers
- **Executive Summary**: High-level overview of all feedback
- **Individual Reviews**: Detailed feedback from each of the 5 reviewers
- **Debate & Discussion**: (if enabled) Reviewers' responses to each other
- **Final Synthesis**: Comprehensive recommendations and action plan
- **Cost Summary**: Total tokens used and actual cost
- **Appendix**: Original article for reference

## Configuration

### Available Models

- `gemini-pro`: Standard model, good balance of quality and cost
- `gemini-1.5-pro`: Higher quality, more expensive
- `gemini-1.5-flash`: Fastest and cheapest, good for most articles

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Your Google Gemini API key |
| `GEMINI_MODEL` | gemini-pro | Default model to use |
| `REQUIRE_COST_APPROVAL` | true | Whether to require approval before API calls |
| `MAX_AUTO_APPROVE_COST` | 0.10 | Auto-approve threshold in USD |

## Troubleshooting

### "GEMINI_API_KEY not found"

Make sure you've:
1. Created a `.env` file (copy from `.env.example`)
2. Added your actual API key to the `.env` file
3. Saved the file

### "crewai" or dependency errors

Make sure you've:
1. Activated the virtual environment: `source venv/bin/activate`
2. Installed dependencies: `pip install -r requirements.txt`

### High costs

- Use `gemini-1.5-flash` for cheaper reviews
- Review shorter articles
- Disable debate mode (saves ~30% on tokens)
- Set `MAX_AUTO_APPROVE_COST` to a low value to get warned

## Tips for Best Results

1. **Article Length**: 500-2000 words works best. Very long articles will cost more and may hit token limits.

2. **Model Selection**:
   - Use `gemini-1.5-flash` for quick, cost-effective reviews
   - Use `gemini-1.5-pro` for more nuanced, in-depth feedback
   - Use `gemini-pro` as a middle ground

3. **Debate Mode**: Enable for articles where you want deeper analysis and cross-reviewer discussion. Adds ~30% to cost but provides richer insights.

4. **Clear Writing**: The better your article is written initially, the more actionable the feedback will be.

## License

This project is open source and available for personal and commercial use.

## Support

For issues, questions, or contributions, please open an issue or submit a pull request.

## Acknowledgments

- Powered by [Google Gemini](https://ai.google.dev/)
- Built with [CrewAI](https://www.crewai.com/)
- Terminal UI by [Rich](https://rich.readthedocs.io/)
