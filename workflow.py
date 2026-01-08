"""Workflow orchestration for article review using CrewAI."""

from crewai import Task, Crew
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from reporter import ReportGenerator

console = Console()


class ArticleReviewWorkflow:
    """Orchestrates the article review workflow using CrewAI."""

    def __init__(self, article_text, personas, estimator, enable_debate=False):
        """Initialize the workflow.

        Args:
            article_text: The article text to review.
            personas: ReviewerPersonas instance.
            estimator: TokenEstimator instance for tracking usage.
            enable_debate: Whether to enable debate mode.
        """
        self.article_text = article_text
        self.personas = personas
        self.estimator = estimator
        self.enable_debate = enable_debate
        self.reviews = {}

    def create_review_task(self, agent, agent_name):
        """Create a review task for a specific agent.

        Args:
            agent: The CrewAI agent to perform the review.
            agent_name: Name of the agent for identification.

        Returns:
            A CrewAI Task instance.
        """
        description = f"""Review the following article from your perspective as a {agent_name}.

Article to review:
---
{self.article_text}
---

Provide a comprehensive review covering:
1. Your overall assessment (1-3 paragraphs)
2. Key strengths (bullet points)
3. Areas for improvement (bullet points)
4. Specific recommendations (numbered list)
5. Overall rating (1-10 scale)

Be specific, constructive, and provide actionable feedback."""

        expected_output = f"""A detailed review from the {agent_name} perspective including:
- Overall assessment
- Key strengths (3-5 points)
- Areas for improvement (3-5 points)
- Specific recommendations (3-5 items)
- Overall rating with justification"""

        return Task(
            description=description,
            agent=agent,
            expected_output=expected_output
        )

    def create_synthesis_task(self, moderator, all_reviews):
        """Create a task for the moderator to synthesize all reviews.

        Args:
            moderator: The moderator agent.
            all_reviews: Dictionary of all reviewer feedback.

        Returns:
            A CrewAI Task instance.
        """
        reviews_text = "\n\n".join([
            f"## {name} Review:\n{review}"
            for name, review in all_reviews.items()
        ])

        description = f"""You are moderating a review panel for an article. You've received
reviews from multiple experts with different perspectives. Your task is to synthesize
all feedback into a comprehensive, actionable report for the author.

Original Article:
---
{self.article_text}
---

Reviews from the panel:
---
{reviews_text}
---

Create a comprehensive synthesis report that:
1. Provides an executive summary of all feedback
2. Identifies common themes across reviewers
3. Highlights both consensus points and disagreements
4. Prioritizes recommendations (must-fix vs. nice-to-have)
5. Provides a clear action plan for the author
6. Includes specific examples and quotes from reviewers where relevant

Be balanced, constructive, and ensure the author has a clear path forward."""

        expected_output = """A comprehensive synthesis report including:
- Executive Summary
- Common Themes
- Consensus & Disagreements
- Prioritized Recommendations
- Action Plan
- Conclusion"""

        return Task(
            description=description,
            agent=moderator,
            expected_output=expected_output
        )

    def run_sequential_reviews(self):
        """Run reviews sequentially from all personas.

        Returns:
            Dictionary mapping reviewer names to their reviews.
        """
        console.print("[bold]Running sequential reviews...[/bold]\n")

        reviewers = {
            'Senior Historian of Astronomy': self.personas.historian(),
            'Editor': self.personas.editor(),
            'General Reader': self.personas.general_reader(),
            'Skeptic': self.personas.skeptic(),
            'Lead Data Scientist': self.personas.data_scientist()
        }

        reviews = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            for name, agent in reviewers.items():
                task_progress = progress.add_task(
                    f"[cyan]{name} reviewing...",
                    total=None
                )

                # Create and run the review task
                task = self.create_review_task(agent, name)
                crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    verbose=False
                )

                result = crew.kickoff()
                reviews[name] = str(result)

                progress.update(task_progress, completed=True)
                console.print(f"[green]✓ {name} completed review[/green]")

        console.print()
        return reviews

    def run_debate_mode(self, initial_reviews):
        """Run a debate phase where reviewers discuss their findings.

        Args:
            initial_reviews: Dictionary of initial reviews from each persona.

        Returns:
            Dictionary of updated reviews after debate.
        """
        console.print("[bold]Running debate phase...[/bold]\n")
        console.print("[yellow]Reviewers are discussing their findings...[/yellow]\n")

        # Create a debate task where reviewers respond to each other
        reviewers = self.personas.get_all_reviewers()

        reviews_summary = "\n\n".join([
            f"**{name}**: {review[:300]}..."
            for name, review in initial_reviews.items()
        ])

        debate_description = f"""You've seen the other reviewers' initial assessments:

{reviews_summary}

Reflect on the other reviews and provide:
1. Points where you agree with other reviewers
2. Points where you disagree and why
3. Any new insights after seeing others' perspectives
4. Your final, refined assessment

Be respectful but don't hesitate to maintain your perspective if you believe it's valid."""

        debate_results = {}

        for name, agent in zip(initial_reviews.keys(), reviewers):
            task = Task(
                description=f"{debate_description}\n\nProvide your response as {name}.",
                agent=agent,
                expected_output=f"Updated perspective from {name} after considering other reviews"
            )

            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )

            result = crew.kickoff()
            debate_results[f"{name} (after debate)"] = str(result)

            console.print(f"[green]✓ {name} contributed to debate[/green]")

        console.print()
        return debate_results

    def run(self):
        """Run the complete review workflow.

        Returns:
            Final synthesized report as a string.
        """
        # Step 1: Sequential reviews
        self.reviews = self.run_sequential_reviews()

        # Step 2: Optional debate phase
        if self.enable_debate:
            debate_results = self.run_debate_mode(self.reviews)
            # Combine original reviews with debate insights
            all_feedback = {**self.reviews, **debate_results}
        else:
            all_feedback = self.reviews

        # Step 3: Moderator synthesis
        console.print("[bold]Synthesizing final report...[/bold]\n")

        moderator = self.personas.moderator()
        synthesis_task = self.create_synthesis_task(moderator, all_feedback)

        crew = Crew(
            agents=[moderator],
            tasks=[synthesis_task],
            verbose=False
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task_progress = progress.add_task(
                "[cyan]Moderator synthesizing feedback...",
                total=None
            )
            final_report = crew.kickoff()
            progress.update(task_progress, completed=True)

        console.print("[green]✓ Final report generated[/green]\n")

        # Generate formatted report
        report_generator = ReportGenerator()
        formatted_report = report_generator.generate_report(
            original_article=self.article_text,
            reviews=self.reviews,
            synthesis=str(final_report),
            debate_results=debate_results if self.enable_debate else None
        )

        return formatted_report
