"""Copywriting review tool for article enhancement."""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from config import Config
from personas import ReviewerPersonas, create_llm
from token_estimator import TokenEstimator
from utils import extract_article_from_report, save_report
from crewai import Task, Crew

console = Console()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Get copywriting suggestions and AI-likeness rating for your article'
    )
    parser.add_argument(
        'review_report',
        type=str,
        help='Path to the review report markdown file'
    )
    parser.add_argument(
        '--article',
        '-a',
        type=str,
        default=None,
        help='Path to original article file (use if article is truncated in review report)'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        default='copywriting_suggestions.md',
        help='Output file path for copywriting suggestions (default: copywriting_suggestions.md)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Gemini model to use (overrides .env setting)'
    )
    parser.add_argument(
        '--no-approval',
        action='store_true',
        help='Skip cost approval prompt (use with caution)'
    )
    parser.add_argument(
        '--generate-draft',
        '-d',
        action='store_true',
        help='Generate a fully rewritten draft of the article based on copywriting suggestions'
    )
    parser.add_argument(
        '--draft-output',
        type=str,
        default='article_draft.md',
        help='Output file path for rewritten draft (default: article_draft.md)'
    )

    return parser.parse_args()


def display_banner():
    """Display the application banner."""
    banner = """
[bold cyan]╔═══════════════════════════════════════════════════╗
║                                                   ║
║        Copywriting Assistant - AI Powered        ║
║          Professional Copy Enhancement           ║
║                                                   ║
╚═══════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner)


def create_copywriting_task(agent, article_text):
    """Create a copywriting task for the agent.

    Args:
        agent: The copywriter agent.
        article_text: The article text to review.

    Returns:
        A CrewAI Task instance.
    """
    description = f"""Review the following article and provide detailed copywriting suggestions.

Article to review:
---
{article_text}
---

Provide a comprehensive copywriting analysis with:

1. **AI Likeness Rating (1-10)**
   - Rate how AI-generated this article appears
   - 1 = Entirely human-written, natural voice
   - 10 = Obviously AI-generated, formulaic
   - Explain your rating with specific examples

2. **Overall Copywriting Assessment**
   - What works well
   - What needs improvement
   - Target audience considerations

3. **Specific Line Edits (at least 5-10 examples)**
   Format each as:
   ```
   BEFORE: [original text]
   AFTER: [improved text]
   WHY: [explanation]
   ```

4. **Key Copywriting Recommendations**
   - Voice and tone adjustments
   - Engagement improvements
   - Flow and pacing suggestions
   - Word choice enhancements

5. **Priority Fixes**
   - Top 3 most important changes to make

Be specific and actionable. Provide concrete examples from the text."""

    expected_output = """A comprehensive copywriting analysis including:
- AI Likeness Rating (1-10) with justification
- Overall assessment
- 5-10 specific before/after line edit examples
- Key recommendations
- Priority fixes"""

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output
    )


def create_draft_generation_task(agent, article_text, suggestions):
    """Create a task for generating a fully rewritten draft.

    Args:
        agent: The copywriter agent.
        article_text: The original article text.
        suggestions: The copywriting suggestions from the analysis.

    Returns:
        A CrewAI Task instance.
    """
    description = f"""Based on the copywriting analysis below, rewrite the entire article to implement all suggested improvements.

Original Article:
---
{article_text}
---

Copywriting Analysis & Suggestions:
---
{suggestions}
---

Your task:
1. Rewrite the ENTIRE article from start to finish
2. Implement all the copywriting suggestions and line edits
3. Improve AI-likeness score by making the writing more natural and human
4. Use stronger verbs, active voice, and varied sentence structure
5. Eliminate fluff and wordiness
6. Maintain the original message and key points
7. Make it engaging and punchy

Provide ONLY the rewritten article text, without any explanatory comments or meta-discussion.
Start directly with the rewritten content."""

    expected_output = """A complete, fully rewritten version of the article that:
- Implements all copywriting suggestions
- Uses more natural, human-like writing
- Has improved flow, pacing, and engagement
- Contains only the article text (no explanations or commentary)"""

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output
    )


def format_copywriting_report(article, suggestions, cost_summary):
    """Format the copywriting suggestions into a markdown report.

    Args:
        article: The original article text.
        suggestions: The copywriter's suggestions.
        cost_summary: Cost and usage summary.

    Returns:
        Formatted markdown report.
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# Copywriting Suggestions & AI Likeness Analysis

**Generated:** {timestamp}
**Tool:** Copywriting Assistant (Powered by Gemini)

---

{suggestions}

---

## Original Article Reference

```
{article}
```

---

## Cost & Usage Summary

- **Model Used:** {cost_summary.get('model', 'N/A')}
- **Total Input Tokens:** {cost_summary.get('total_input_tokens', 0):,}
- **Total Output Tokens:** {cost_summary.get('total_output_tokens', 0):,}
- **Total Tokens:** {cost_summary.get('total_tokens', 0):,}
- **Total Cost:** ${cost_summary.get('total_cost', 0):.6f}

---

*Generated with Article Reviewer - Copywriting Assistant*
"""

    return report


def main():
    """Main function to run the copywriting assistant."""
    try:
        # Display banner
        display_banner()

        # Parse arguments
        args = parse_arguments()

        # Validate configuration
        Config.validate()

        # Override model if specified
        if args.model:
            Config.GEMINI_MODEL = args.model

        # Load article - either from file or extract from review report
        if args.article:
            # Load from provided article file
            console.print(f"\n[bold]Loading article from {args.article}...[/bold]")
            try:
                from utils import load_article
                article_text = load_article(args.article)
                word_count = len(article_text.split())
                console.print(f"[green]✓ Loaded article ({word_count} words)[/green]\n")
            except Exception as e:
                console.print(f"[red]Error loading article: {e}[/red]")
                sys.exit(1)
        else:
            # Extract from review report
            console.print("\n[bold]Extracting article from review report...[/bold]")
            try:
                article_text = extract_article_from_report(args.review_report)
                word_count = len(article_text.split())
                console.print(f"[green]✓ Extracted article ({word_count} words)[/green]\n")
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print("[yellow]Tip: If the article was truncated in the review report, use --article to specify the original article file:[/yellow]")
                console.print(f"[yellow]  python copywriter.py {args.review_report} --article <original_article.txt>[/yellow]\n")
                sys.exit(1)

        # Initialize token estimator
        estimator = TokenEstimator(model=Config.GEMINI_MODEL)

        # Estimate tokens for the copywriting task
        console.print("[bold]Estimating token usage and costs...[/bold]\n")

        # Estimate input (article + copywriter instructions ~1000 tokens)
        estimated_input = estimator.count_tokens(article_text) + 1000
        # Copywriters typically provide detailed feedback
        estimated_output = int(estimated_input * 1.2)

        # If draft generation is enabled, add additional token estimates
        if args.generate_draft:
            # Draft generation requires: original article + suggestions as input
            # Output will be approximately the same length as original article
            article_tokens = estimator.count_tokens(article_text)
            draft_input_additional = article_tokens + estimated_output + 500  # 500 for instructions
            draft_output_additional = article_tokens  # Rewritten article approximately same length

            estimated_input += draft_input_additional
            estimated_output += draft_output_additional

            console.print("[yellow]Draft generation enabled - including additional token estimates[/yellow]\n")

        estimate = {
            'input_tokens': estimated_input,
            'output_tokens': estimated_output,
            'estimated_cost': estimator.estimate_cost(estimated_input, estimated_output)
        }

        # Request approval unless disabled
        if not args.no_approval:
            approved = estimator.request_approval(estimate)
            if not approved:
                console.print("[yellow]Copywriting analysis cancelled by user[/yellow]")
                sys.exit(0)
        else:
            estimator.display_estimate(estimate)
            console.print("[yellow]⚠ Running without approval (--no-approval flag set)[/yellow]\n")

        # Create LLM instance
        console.print(f"[bold]Initializing {Config.GEMINI_MODEL}...[/bold]")
        llm = create_llm(
            api_key=Config.GEMINI_API_KEY,
            model=Config.GEMINI_MODEL,
            temperature=0.7
        )
        console.print("[green]✓ LLM initialized[/green]\n")

        # Create copywriter agent
        console.print("[bold]Analyzing your article...[/bold]")
        personas = ReviewerPersonas(llm)
        copywriter = personas.copywriter()

        console.print(Panel(
            "[yellow]The copywriter is reviewing your article for engagement, clarity, and AI-likeness.[/yellow]",
            title="Please Wait",
            border_style="yellow"
        ))

        # Create and run the copywriting task
        task = create_copywriting_task(copywriter, article_text)
        crew = Crew(
            agents=[copywriter],
            tasks=[task],
            verbose=False
        )

        suggestions = crew.kickoff()

        # Display and save the report
        console.print("\n[bold green]✓ Copywriting analysis complete![/bold green]\n")

        # Show final cost report
        estimator.display_final_report()

        # Format and save report
        console.print(f"\n[bold]Saving suggestions to {args.output}...[/bold]")
        formatted_report = format_copywriting_report(
            article_text,
            str(suggestions),
            estimator.get_summary()
        )

        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(formatted_report)

        console.print(f"[green]✓ Suggestions saved to {args.output}[/green]\n")

        # Display preview
        console.print(Panel(
            str(suggestions)[:500] + "..." if len(str(suggestions)) > 500 else str(suggestions),
            title="Suggestions Preview",
            border_style="green"
        ))

        console.print(f"\n[bold cyan]Full suggestions available at: {args.output}[/bold cyan]\n")

        # Generate draft if requested
        if args.generate_draft:
            console.print("\n[bold]Generating rewritten draft based on suggestions...[/bold]")
            console.print(Panel(
                "[yellow]The copywriter is now rewriting your entire article...[/yellow]",
                title="Please Wait",
                border_style="yellow"
            ))

            # Create and run the draft generation task
            draft_task = create_draft_generation_task(copywriter, article_text, str(suggestions))
            draft_crew = Crew(
                agents=[copywriter],
                tasks=[draft_task],
                verbose=False
            )

            draft = draft_crew.kickoff()

            # Save the draft
            console.print(f"\n[bold]Saving rewritten draft to {args.draft_output}...[/bold]")
            with open(args.draft_output, 'w', encoding='utf-8') as f:
                f.write(str(draft))

            console.print(f"[green]✓ Draft saved to {args.draft_output}[/green]\n")

            # Display preview
            draft_str = str(draft)
            console.print(Panel(
                draft_str[:500] + "..." if len(draft_str) > 500 else draft_str,
                title="Draft Preview",
                border_style="green"
            ))

            console.print(f"\n[bold cyan]Full rewritten draft available at: {args.draft_output}[/bold cyan]\n")

            # Show updated final cost report
            console.print("[bold]Updated Cost Summary:[/bold]")
            estimator.display_final_report()

    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
