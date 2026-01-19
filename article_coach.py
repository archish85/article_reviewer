#!/usr/bin/env python3
"""Article Coach - Interactive Writing Improvement Assistant

This tool helps you improve your writing by identifying issues and letting you
fix them interactively. It's designed for active learning - you do the editing,
building your writing skills over time.

Usage:
    python article_coach.py my_article.md
    python article_coach.py my_article.txt --quick
    python article_coach.py my_article.md --skip-style

Features:
    - FREE local analysis (no API costs)
    - Interactive issue-by-issue coaching
    - Tracks your improvement over time
    - Educational explanations for each issue
    - Saves coached version of your article
"""

import argparse
import sys
from pathlib import Path
from typing import List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from coaching.problem_detector import ProblemDetector, Issue
from coaching.issue_presenter import IssuePresenter, edit_text_inline, open_in_external_editor
from coaching.fix_validator import FixValidator

console = Console()


class ArticleCoach:
    """Main coaching application."""

    def __init__(self, skip_types: List[str] = None, quick_mode: bool = False):
        """Initialize the coach.

        Args:
            skip_types: List of issue types to skip (e.g., ['style', 'grammar'])
            quick_mode: If True, only show top 3 issues
        """
        self.detector = ProblemDetector()
        self.presenter = IssuePresenter()
        self.validator = FixValidator()
        self.skip_types = skip_types or []
        self.quick_mode = quick_mode

        self.original_text = ""
        self.coached_text = ""
        self.fixed_count = 0
        self.skipped_count = 0

    def coach_article(self, filepath: Path) -> bool:
        """Run interactive coaching session on an article.

        Args:
            filepath: Path to article file

        Returns:
            True if coaching completed, False if user quit early
        """
        # Load article
        if not self._load_article(filepath):
            return False

        # Analyze article
        console.print("\n[cyan]Analyzing your article...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running local analysis (FREE)", total=None)

            # Find all issues
            issues = self.detector.find_all_issues(self.original_text)
            progress.update(task, description="✓ Local analysis complete")

        # Filter issues
        issues = self._filter_issues(issues)

        if not issues:
            self.presenter.show_no_issues()
            return True

        console.print(f"[cyan]✓ Found {len(issues)} problem sections[/cyan]\n")

        # Present issues one by one
        completed = self._present_issues(issues)

        if not completed:
            return False

        # Save coached article
        coached_filepath = self._save_coached_article(filepath)

        # Show summary
        improvements = self.validator.calculate_overall_improvements(
            self.original_text,
            self.coached_text
        )

        self.presenter.show_progress_summary(
            self.fixed_count,
            self.skipped_count,
            improvements
        )

        self.presenter.show_file_saved(coached_filepath)

        return True

    def _load_article(self, filepath: Path) -> bool:
        """Load article from file.

        Args:
            filepath: Path to article file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.original_text = f.read()
                self.coached_text = self.original_text

            if not self.original_text.strip():
                console.print("[red]Error: Article file is empty[/red]")
                return False

            return True

        except FileNotFoundError:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            return False

    def _filter_issues(self, issues: List[Issue]) -> List[Issue]:
        """Filter issues based on user preferences.

        Args:
            issues: List of all detected issues

        Returns:
            Filtered and prioritized list of issues
        """
        # Filter by type if skip_types specified
        if self.skip_types:
            issues = [i for i in issues if i.type not in self.skip_types]

        # Get top priority issues
        priority_issues = self.detector.prioritizer.top_issues(
            issues,
            limit=3 if self.quick_mode else 10
        )

        return priority_issues

    def _present_issues(self, issues: List[Issue]) -> bool:
        """Present issues interactively to user.

        Args:
            issues: List of issues to present

        Returns:
            True if completed, False if user quit
        """
        total = len(issues)

        for i, issue in enumerate(issues, 1):
            # Present issue
            action = self.presenter.present_issue(issue, i, total)

            if action == 'quit':
                if self.presenter.confirm_quit():
                    return False
                else:
                    # Continue with this issue
                    i -= 1
                    continue

            elif action == 'skip':
                self.skipped_count += 1
                continue

            elif action == 'edit_inline':
                # Edit inline with nano
                edited = edit_text_inline(issue.context, issue.description)

                if edited and edited != issue.context:
                    # Update coached text
                    self.coached_text = self.coached_text.replace(issue.context, edited, 1)

                    # Validate fix
                    improved, message, metrics = self.validator.validate_fix(
                        issue.context,
                        edited,
                        issue
                    )

                    self.validator.show_validation_result(improved, message)

                    if improved:
                        self.fixed_count += 1

                    # Pause for user to read
                    console.print("\n[dim]Press Enter to continue...[/dim]")
                    input()

            elif action == 'edit_external':
                # Save current version to temp file
                temp_file = Path('.coaching_progress') / 'temp_article.txt'
                temp_file.parent.mkdir(exist_ok=True)

                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(self.coached_text)

                # Open in external editor
                if open_in_external_editor(str(temp_file)):
                    # Load edited version
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        self.coached_text = f.read()

                    console.print("[green]✓ Changes loaded[/green]")
                    self.fixed_count += 1

                # Clean up temp file
                try:
                    temp_file.unlink()
                except:
                    pass

        return True

    def _save_coached_article(self, original_filepath: Path) -> str:
        """Save coached article to file.

        Args:
            original_filepath: Original article filepath

        Returns:
            Path to saved coached article
        """
        # Generate coached filename
        stem = original_filepath.stem
        suffix = original_filepath.suffix
        coached_filepath = original_filepath.parent / f"{stem}_coached{suffix}"

        # Save
        with open(coached_filepath, 'w', encoding='utf-8') as f:
            f.write(self.coached_text)

        return str(coached_filepath)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Article Coach - Interactive Writing Improvement Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python article_coach.py my_article.md
  python article_coach.py article.txt --quick
  python article_coach.py article.md --skip-style

Features:
  • FREE local analysis (no API costs)
  • Interactive issue-by-issue coaching
  • Educational explanations
  • Tracks improvement over time
        """
    )

    parser.add_argument(
        'article',
        type=str,
        help='Path to article file (markdown, text, etc.)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode: only show top 3 issues'
    )

    parser.add_argument(
        '--skip-style',
        action='store_true',
        help='Skip style issues (passive voice, adverbs, weak verbs)'
    )

    parser.add_argument(
        '--skip-grammar',
        action='store_true',
        help='Skip grammar and spelling checks'
    )

    parser.add_argument(
        '--skip-readability',
        action='store_true',
        help='Skip readability analysis'
    )

    args = parser.parse_args()

    # Build skip list
    skip_types = []
    if args.skip_style:
        skip_types.extend(['passive_voice', 'adverbs', 'weak_verbs'])
    if args.skip_grammar:
        skip_types.extend(['spelling', 'grammar'])
    if args.skip_readability:
        skip_types.extend(['sentence_too_long', 'difficult_words', 'paragraph_too_long'])

    # Validate file exists
    filepath = Path(args.article)
    if not filepath.exists():
        console.print(f"[red]Error: File not found: {args.article}[/red]")
        sys.exit(1)

    # Create coach
    coach = ArticleCoach(skip_types=skip_types, quick_mode=args.quick)

    # Run coaching session
    try:
        success = coach.coach_article(filepath)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Coaching session interrupted by user[/yellow]")
        sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
