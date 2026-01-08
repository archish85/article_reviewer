"""Report generation and formatting for article reviews."""

from datetime import datetime


class ReportGenerator:
    """Generates formatted reports from article reviews."""

    def __init__(self):
        """Initialize the report generator."""
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_report(self, original_article, reviews, synthesis, debate_results=None):
        """Generate a comprehensive formatted report.

        Args:
            original_article: The original article text.
            reviews: Dictionary of individual reviews.
            synthesis: The moderator's synthesis.
            debate_results: Optional debate results if debate mode was enabled.

        Returns:
            Formatted report as a markdown string.
        """
        report_parts = []

        # Header
        report_parts.append(self._generate_header())

        # Article info
        report_parts.append(self._generate_article_info(original_article))

        # Executive summary (from synthesis)
        report_parts.append(self._generate_executive_summary(synthesis))

        # Individual reviews
        report_parts.append(self._generate_individual_reviews(reviews))

        # Debate results (if applicable)
        if debate_results:
            report_parts.append(self._generate_debate_section(debate_results))

        # Final synthesis
        report_parts.append(self._generate_final_synthesis(synthesis))

        # Appendix - Original article
        report_parts.append(self._generate_appendix(original_article))

        return "\n\n".join(report_parts)

    def _generate_header(self):
        """Generate report header."""
        return f"""# Article Review Report

**Generated:** {self.timestamp}
**Review System:** Multi-Agent Article Reviewer (Powered by Gemini & CrewAI)

---
"""

    def _generate_article_info(self, article):
        """Generate article information section."""
        word_count = len(article.split())
        char_count = len(article)

        return f"""## Article Information

- **Word Count:** {word_count:,} words
- **Character Count:** {char_count:,} characters
- **Reviewers:** 5 AI personas (Technical Expert, Editor, General Reader, Skeptic, Domain Expert)
"""

    def _generate_executive_summary(self, synthesis):
        """Generate executive summary from synthesis."""
        # Try to extract the first paragraph or two from the synthesis
        lines = synthesis.split('\n')
        summary_lines = []

        for line in lines[:10]:  # Take first 10 lines as a heuristic
            if line.strip():
                summary_lines.append(line)
            if len(summary_lines) >= 3 and len(' '.join(summary_lines).split()) > 100:
                break

        summary = '\n'.join(summary_lines) if summary_lines else synthesis[:500]

        return f"""## Executive Summary

{summary}

*For the complete synthesis, see the Final Synthesis section below.*
"""

    def _generate_individual_reviews(self, reviews):
        """Generate individual reviews section."""
        sections = ["## Individual Reviews\n"]

        for name, review in reviews.items():
            sections.append(f"""### {name}

{review}

---
""")

        return "\n".join(sections)

    def _generate_debate_section(self, debate_results):
        """Generate debate section."""
        sections = ["## Debate & Discussion\n"]
        sections.append("The reviewers engaged in a discussion about their findings:\n")

        for name, debate_content in debate_results.items():
            sections.append(f"""### {name}

{debate_content}

---
""")

        return "\n".join(sections)

    def _generate_final_synthesis(self, synthesis):
        """Generate final synthesis section."""
        return f"""## Final Synthesis & Recommendations

{synthesis}
"""

    def _generate_appendix(self, article):
        """Generate appendix with original article."""
        # Truncate if too long
        if len(article) > 5000:
            article_display = article[:5000] + "\n\n[... article truncated for report brevity ...]"
        else:
            article_display = article

        return f"""## Appendix: Original Article

```
{article_display}
```

---

*End of Report*
"""

    @staticmethod
    def format_cost_summary(cost_summary):
        """Format cost summary for inclusion in report.

        Args:
            cost_summary: Dictionary with cost information.

        Returns:
            Formatted cost summary string.
        """
        return f"""## Cost & Usage Summary

- **Model Used:** {cost_summary.get('model', 'N/A')}
- **Total Input Tokens:** {cost_summary.get('total_input_tokens', 0):,}
- **Total Output Tokens:** {cost_summary.get('total_output_tokens', 0):,}
- **Total Tokens:** {cost_summary.get('total_tokens', 0):,}
- **Total Cost:** ${cost_summary.get('total_cost', 0):.6f}
"""
