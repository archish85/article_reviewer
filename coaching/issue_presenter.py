"""Interactive issue presentation for the Article Coach.

This module provides a beautiful CLI interface for displaying writing issues
and collecting user actions.
"""

import sys
import os
import subprocess
import tempfile
from typing import Optional, Tuple
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coaching.problem_detector import Issue

console = Console()


class IssuePresenter:
    """Presents writing issues interactively to the user."""

    def __init__(self):
        """Initialize the presenter."""
        self.current_issue_num = 0
        self.total_issues = 0

    def present_issue(self, issue: Issue, issue_num: int, total: int) -> str:
        """Present a single issue to the user and get their action.

        Args:
            issue: The Issue to present
            issue_num: Current issue number (1-indexed)
            total: Total number of issues

        Returns:
            User action: 'edit_inline', 'edit_external', 'skip', or 'quit'
        """
        self.current_issue_num = issue_num
        self.total_issues = total

        # Clear screen for clean presentation
        console.clear()

        # Header
        self._print_header()

        # Issue number
        console.print(f"\n[bold cyan]ISSUE {issue_num} of {total}: {self._format_issue_type(issue.type)}[/bold cyan]")
        console.print("━" * 60)

        # Location
        console.print(f"\n[yellow]Location:[/yellow] {issue.location}")

        # Context (the problematic text)
        self._print_context(issue.context)

        # Description
        console.print(f"\n[red]⚠️  Issues detected:[/red]")
        console.print(f"   • {issue.description}")

        # Why it matters
        self._print_why(issue.why)

        # Metrics (if available)
        if issue.metrics:
            self._print_metrics(issue.metrics, issue.type)

        # Suggested approach
        self._print_suggestions(issue.suggested_approach)

        # Get user action
        action = self._get_user_action()

        return action

    def _print_header(self):
        """Print the application header."""
        header = Panel.fit(
            "[bold white]Article Coach - Writing Improvement Assistant[/bold white]",
            border_style="cyan"
        )
        console.print(header)

    def _format_issue_type(self, issue_type: str) -> str:
        """Format issue type for display."""
        type_map = {
            'spelling': 'Spelling Error',
            'grammar': 'Grammar Issue',
            'sentence_too_long': 'Sentence Too Long',
            'difficult_words': 'Difficult to Read',
            'poor_transitions': 'Missing Transitions',
            'paragraph_too_long': 'Paragraph Too Long',
            'passive_voice': 'Passive Voice Overuse',
            'weak_verbs': 'Weak Verbs',
            'adverbs': 'Excessive Adverbs',
            'word_repetition': 'Word Repetition'
        }
        return type_map.get(issue_type, issue_type.replace('_', ' ').title())

    def _print_context(self, context: str):
        """Print the problematic text context."""
        console.print("\n[bold]Current text:[/bold]")

        # Create a panel with the context
        panel = Panel(
            context,
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(panel)

    def _print_why(self, why: str):
        """Print the 'why it matters' explanation."""
        console.print(f"\n[blue]💡 Why this matters:[/blue]")
        console.print(f"   {why}")

    def _print_metrics(self, metrics: dict, issue_type: str):
        """Print relevant metrics."""
        console.print("\n[green]📊 Metrics:[/green]")

        # Format based on issue type
        if issue_type == 'passive_voice':
            console.print(f"   • Passive voice in article: {metrics.get('percentage', 0):.1f}%")
            console.print(f"   • Target: <10%")
            if 'examples' in metrics:
                console.print(f"   • Found {len(metrics['examples'])} instances")

        elif issue_type == 'adverbs':
            console.print(f"   • Adverbs per 100 words: {metrics.get('rate', 0):.1f}")
            console.print(f"   • Target: <3")
            if 'most_common' in metrics and metrics['most_common']:
                top_adverbs = ', '.join([word for word, _ in metrics['most_common'][:3]])
                console.print(f"   • Most common: {top_adverbs}")

        elif issue_type == 'weak_verbs':
            console.print(f"   • Weak verb percentage: {metrics.get('percentage', 0):.1f}%")
            console.print(f"   • Target: <30%")

        elif issue_type == 'sentence_too_long':
            console.print(f"   • Average sentence length: {metrics.get('avg_sentence_length', 0):.1f} words")
            console.print(f"   • Target: <20 words")

        elif issue_type == 'difficult_words':
            console.print(f"   • Flesch Reading Ease: {metrics.get('flesch_score', 0):.1f}")
            console.print(f"   • Target: >60")
            console.print(f"   • Difficult words: {metrics.get('difficult_words', 0)}")

        elif issue_type == 'paragraph_too_long':
            if 'long_paragraphs' in metrics:
                para_list = ', '.join([f"#{p[0]}" for p in metrics['long_paragraphs'][:3]])
                console.print(f"   • Long paragraphs: {para_list}")
            console.print(f"   • Target: <150 words per paragraph")

        elif issue_type == 'word_repetition':
            if 'repeated_words' in metrics and metrics['repeated_words']:
                top_words = ', '.join([f"{word} ({count}x)" for word, count in metrics['repeated_words'][:3]])
                console.print(f"   • Most repeated: {top_words}")

        elif issue_type in ['spelling', 'grammar']:
            console.print(f"   • Total issues found: {metrics.get('issue_count', 0)}")

    def _print_suggestions(self, suggestions: list):
        """Print suggested approaches."""
        console.print("\n[magenta]🎯 Suggested approach:[/magenta]")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"   {i}. {suggestion}")

    def _get_user_action(self) -> str:
        """Get user action choice."""
        console.print("\n[bold]Options:[/bold]")
        console.print("  [E] Edit inline (nano editor)")
        console.print("  [O] Open in your default editor")
        console.print("  [S] Skip this issue")
        console.print("  [Q] Quit coaching session")
        console.print()

        while True:
            choice = Prompt.ask(
                "[bold cyan]Your choice[/bold cyan]",
                choices=['e', 'E', 'o', 'O', 's', 'S', 'q', 'Q'],
                default='s'
            ).lower()

            if choice == 'e':
                return 'edit_inline'
            elif choice == 'o':
                return 'edit_external'
            elif choice == 's':
                return 'skip'
            elif choice == 'q':
                return 'quit'

    def show_progress_summary(self, fixed_count: int, skipped_count: int, improvements: dict):
        """Show summary of improvements after coaching session.

        Args:
            fixed_count: Number of issues fixed
            skipped_count: Number of issues skipped
            improvements: Dictionary of metric improvements
        """
        console.print("\n" + "═" * 60)
        console.print("[bold green]✅ Coaching Session Complete![/bold green]")
        console.print("═" * 60)

        # Stats
        console.print(f"\n[cyan]Session Stats:[/cyan]")
        console.print(f"  • Issues addressed: {fixed_count}")
        console.print(f"  • Issues skipped: {skipped_count}")

        # Improvements
        if improvements:
            console.print(f"\n[green]📈 Improvements:[/green]")

            if 'passive_voice' in improvements:
                before, after = improvements['passive_voice']
                change = after - before
                console.print(f"  • Passive voice: {before:.1f}% → {after:.1f}% ({change:+.1f}%)")

            if 'readability' in improvements:
                before, after = improvements['readability']
                change = after - before
                console.print(f"  • Readability score: {before:.1f} → {after:.1f} ({change:+.1f})")

            if 'avg_sentence_length' in improvements:
                before, after = improvements['avg_sentence_length']
                change = after - before
                console.print(f"  • Avg sentence length: {before:.1f} → {after:.1f} words ({change:+.1f})")

            if 'adverbs' in improvements:
                before, after = improvements['adverbs']
                change = after - before
                console.print(f"  • Adverbs per 100 words: {before:.1f} → {after:.1f} ({change:+.1f})")

        console.print(f"\n[bold cyan]💡 Keep practicing! Your writing is improving.[/bold cyan]\n")

    def show_no_issues(self):
        """Show message when no issues are found."""
        console.clear()
        self._print_header()

        console.print("\n[bold green]✅ Excellent work![/bold green]\n")
        console.print("No significant issues found in your article.")
        console.print("Your writing meets all quality thresholds:\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Status", style="green")

        table.add_row("Grammar & Spelling", "✓ Clean")
        table.add_row("Readability", "✓ Good")
        table.add_row("Passive Voice", "✓ Minimal")
        table.add_row("Sentence Length", "✓ Appropriate")
        table.add_row("Paragraph Structure", "✓ Well-balanced")

        console.print(table)
        console.print("\n[cyan]Your article is ready for review![/cyan]\n")

    def confirm_quit(self) -> bool:
        """Confirm if user wants to quit.

        Returns:
            True if user confirms quit, False otherwise
        """
        console.print("\n[yellow]⚠️  Are you sure you want to quit?[/yellow]")
        console.print("Remaining issues won't be addressed.\n")

        choice = Prompt.ask(
            "Quit coaching session?",
            choices=['y', 'n', 'Y', 'N'],
            default='n'
        ).lower()

        return choice == 'y'

    def show_file_saved(self, filepath: str):
        """Show message about saved file.

        Args:
            filepath: Path to the saved file
        """
        console.print(f"\n[green]✅ Coached article saved:[/green] {filepath}\n")


def edit_text_inline(text: str, issue_description: str) -> Optional[str]:
    """Open text in nano editor for inline editing.

    Args:
        text: The text to edit
        issue_description: Description to show at top of file

    Returns:
        Edited text, or None if user cancelled
    """
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # Add instruction comment at top
        f.write(f"# Fix: {issue_description}\n")
        f.write("# Delete this line and edit the text below.\n")
        f.write("# Save and exit (Ctrl+X, then Y, then Enter)\n\n")
        f.write(text)
        temp_path = f.name

    try:
        # Open in nano
        subprocess.run(['nano', temp_path], check=True)

        # Read edited content
        with open(temp_path, 'r') as f:
            edited = f.read()

        # Remove instruction lines
        lines = edited.split('\n')
        lines = [line for line in lines if not line.startswith('#')]
        edited = '\n'.join(lines).strip()

        return edited if edited else None

    except subprocess.CalledProcessError:
        console.print("[red]Error: Could not open editor[/red]")
        return None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass


def open_in_external_editor(filepath: str) -> bool:
    """Open file in user's default editor.

    Args:
        filepath: Path to file to open

    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', filepath], check=True)
        elif sys.platform == 'win32':  # Windows
            subprocess.run(['start', filepath], shell=True, check=True)
        else:  # Linux
            subprocess.run(['xdg-open', filepath], check=True)

        console.print(f"\n[cyan]Opened {filepath} in your default editor.[/cyan]")
        console.print("[cyan]Press Enter when you're done editing...[/cyan]")
        input()

        return True

    except subprocess.CalledProcessError:
        console.print("[red]Error: Could not open external editor[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False
