"""Main entry point for the Article Reviewer system."""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from config import Config
from personas import ReviewerPersonas, create_llm
from token_estimator import TokenEstimator
from workflow import ArticleReviewWorkflow
from utils import load_article, save_report

console = Console()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Review an article using multiple AI personas powered by Gemini'
    )
    parser.add_argument(
        'article',
        type=str,
        help='Path to the article file or direct text (use quotes for text)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Gemini model to use (overrides .env setting)'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        default='review_report.md',
        help='Output file path for the review report (default: review_report.md)'
    )
    parser.add_argument(
        '--no-approval',
        action='store_true',
        help='Skip cost approval prompt (use with caution)'
    )
    parser.add_argument(
        '--debate',
        action='store_true',
        help='Enable debate mode where reviewers discuss their findings'
    )

    return parser.parse_args()


def display_banner():
    """Display the application banner."""
    banner = """
[bold cyan]╔═══════════════════════════════════════════════════╗
║                                                   ║
║        Article Reviewer - Multi-Agent AI         ║
║          Powered by Gemini & CrewAI              ║
║                                                   ║
╚═══════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner)


def main():
    """Main function to run the article reviewer."""
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

        # Load article
        console.print("\n[bold]Loading article...[/bold]")
        article_text = load_article(args.article)

        if not article_text:
            console.print("[red]Error: Article is empty or could not be loaded[/red]")
            sys.exit(1)

        word_count = len(article_text.split())
        console.print(f"[green]✓ Loaded article ({word_count} words)[/green]\n")

        # Initialize token estimator
        estimator = TokenEstimator(model=Config.GEMINI_MODEL)

        # Estimate tokens for the workflow
        console.print("[bold]Estimating token usage and costs...[/bold]\n")

        # Estimate for each reviewer (5 reviewers)
        num_reviewers = 5
        estimates = []

        for i in range(num_reviewers):
            # Each reviewer will receive the article + their role context
            # Estimate ~500 tokens for role context
            estimated_input = estimator.count_tokens(article_text) + 500
            # Reviewers typically generate detailed feedback
            estimated_output = estimated_input * 0.8  # Assuming substantial review

            estimates.append({
                'input_tokens': estimated_input,
                'output_tokens': int(estimated_output),
                'estimated_cost': estimator.estimate_cost(estimated_input, estimated_output)
            })

        # Add estimate for moderator synthesis
        # Moderator receives all reviews plus original article
        moderator_input = estimator.count_tokens(article_text) + (num_reviewers * 1500)
        moderator_output = int(moderator_input * 0.5)
        estimates.append({
            'input_tokens': moderator_input,
            'output_tokens': moderator_output,
            'estimated_cost': estimator.estimate_cost(moderator_input, moderator_output)
        })

        # Request approval unless disabled
        if not args.no_approval:
            approved = estimator.request_approval(estimates)
            if not approved:
                console.print("[yellow]Review cancelled by user[/yellow]")
                sys.exit(0)
        else:
            estimator.display_estimate(estimates)
            console.print("[yellow]⚠ Running without approval (--no-approval flag set)[/yellow]\n")

        # Create LLM instance
        console.print(f"[bold]Initializing {Config.GEMINI_MODEL}...[/bold]")
        llm = create_llm(
            api_key=Config.GEMINI_API_KEY,
            model=Config.GEMINI_MODEL,
            temperature=0.7
        )
        console.print("[green]✓ LLM initialized[/green]\n")

        # Create reviewer personas
        console.print("[bold]Assembling review panel...[/bold]")
        personas = ReviewerPersonas(llm)
        console.print(f"[green]✓ Panel assembled: {', '.join(personas.get_reviewer_names())}[/green]\n")

        # Run the review workflow
        console.print("[bold magenta]Starting article review...[/bold magenta]\n")
        console.print(Panel(
            "[yellow]This may take several minutes as each reviewer analyzes the article.[/yellow]",
            title="Please Wait",
            border_style="yellow"
        ))

        workflow = ArticleReviewWorkflow(
            article_text=article_text,
            personas=personas,
            estimator=estimator,
            enable_debate=args.debate
        )

        final_report = workflow.run()

        # Display and save the report
        console.print("\n[bold green]✓ Review complete![/bold green]\n")

        # Show final cost report
        estimator.display_final_report()

        # Save report to file
        console.print(f"\n[bold]Saving report to {args.output}...[/bold]")
        save_report(final_report, args.output, estimator.get_summary())
        console.print(f"[green]✓ Report saved to {args.output}[/green]\n")

        # Display report summary
        console.print(Panel(
            final_report[:500] + "..." if len(final_report) > 500 else final_report,
            title="Report Preview",
            border_style="green"
        ))

        console.print(f"\n[bold cyan]Full report available at: {args.output}[/bold cyan]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Review interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
