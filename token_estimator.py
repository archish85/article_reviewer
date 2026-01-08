"""Token estimation and cost calculation for Gemini API calls."""

import tiktoken
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from config import Config

console = Console()


class TokenEstimator:
    """Estimates token usage and costs for Gemini API calls."""

    def __init__(self, model=None):
        """Initialize the token estimator.

        Args:
            model: The Gemini model to use for pricing. Defaults to config model.
        """
        self.model = model or Config.GEMINI_MODEL
        self.pricing = Config.get_pricing(self.model)

        # Use cl100k_base encoding as approximation for Gemini
        # (Gemini doesn't have public tokenizer, so we use GPT's as proxy)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback to a default encoding
            self.encoding = tiktoken.get_encoding("gpt2")

        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def count_tokens(self, text):
        """Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for.

        Returns:
            Number of tokens in the text.
        """
        if not text:
            return 0
        return len(self.encoding.encode(str(text)))

    def estimate_cost(self, input_tokens, output_tokens=None):
        """Estimate the cost for a given number of tokens.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens (estimated if not provided).

        Returns:
            Estimated cost in USD.
        """
        # If output tokens not provided, estimate as 1.5x input tokens
        if output_tokens is None:
            output_tokens = int(input_tokens * 1.5)

        input_cost = (input_tokens / 1_000_000) * self.pricing['input']
        output_cost = (output_tokens / 1_000_000) * self.pricing['output']

        return input_cost + output_cost

    def estimate_prompt(self, prompt, expected_output_tokens=None):
        """Estimate tokens and cost for a single prompt.

        Args:
            prompt: The prompt text.
            expected_output_tokens: Expected number of output tokens.

        Returns:
            Dictionary with token counts and estimated cost.
        """
        input_tokens = self.count_tokens(prompt)

        if expected_output_tokens is None:
            # Estimate output as roughly same size as input for reviews
            expected_output_tokens = input_tokens

        cost = self.estimate_cost(input_tokens, expected_output_tokens)

        return {
            'input_tokens': input_tokens,
            'output_tokens': expected_output_tokens,
            'total_tokens': input_tokens + expected_output_tokens,
            'estimated_cost': cost
        }

    def display_estimate(self, estimates, title="Token & Cost Estimate"):
        """Display token and cost estimates in a formatted table.

        Args:
            estimates: List of estimation dictionaries or single estimation dict.
            title: Title for the display panel.
        """
        if not isinstance(estimates, list):
            estimates = [estimates]

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        total_input = sum(e['input_tokens'] for e in estimates)
        total_output = sum(e['output_tokens'] for e in estimates)
        total_tokens = total_input + total_output
        total_cost = sum(e['estimated_cost'] for e in estimates)

        table.add_row("Model", self.model)
        table.add_row("Input Tokens", f"{total_input:,}")
        table.add_row("Output Tokens (est.)", f"{total_output:,}")
        table.add_row("Total Tokens", f"{total_tokens:,}")
        table.add_row("Estimated Cost", f"${total_cost:.6f}")

        console.print(Panel(table, title=title, border_style="blue"))

        return total_cost

    def request_approval(self, estimates):
        """Request user approval for estimated costs.

        Args:
            estimates: List of estimation dictionaries or single estimation dict.

        Returns:
            True if approved, False otherwise.
        """
        total_cost = self.display_estimate(estimates, "Cost Estimate - Approval Required")

        # Auto-approve if below threshold and auto-approve is enabled
        if not Config.REQUIRE_COST_APPROVAL or total_cost <= Config.MAX_AUTO_APPROVE_COST:
            console.print(f"[green]✓ Auto-approved (below ${Config.MAX_AUTO_APPROVE_COST} threshold)[/green]\n")
            return True

        console.print(f"\n[yellow]⚠ Estimated cost exceeds auto-approval threshold (${Config.MAX_AUTO_APPROVE_COST})[/yellow]")
        response = console.input("[bold]Proceed with API calls? (y/n): [/bold]")

        approved = response.lower().strip() in ['y', 'yes']
        if approved:
            console.print("[green]✓ Approved[/green]\n")
        else:
            console.print("[red]✗ Cancelled[/red]\n")

        return approved

    def track_usage(self, input_tokens, output_tokens):
        """Track actual token usage.

        Args:
            input_tokens: Actual input tokens used.
            output_tokens: Actual output tokens used.
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        cost = self.estimate_cost(input_tokens, output_tokens)
        self.total_cost += cost

    def display_final_report(self):
        """Display final usage and cost report."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Total Input Tokens", f"{self.total_input_tokens:,}")
        table.add_row("Total Output Tokens", f"{self.total_output_tokens:,}")
        table.add_row("Total Tokens", f"{self.total_input_tokens + self.total_output_tokens:,}")
        table.add_row("Total Cost", f"${self.total_cost:.6f}")

        console.print(Panel(table, title="Final Usage Report", border_style="green"))

    def get_summary(self):
        """Get a summary of token usage and costs.

        Returns:
            Dictionary with usage summary.
        """
        return {
            'model': self.model,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'total_cost': self.total_cost
        }
