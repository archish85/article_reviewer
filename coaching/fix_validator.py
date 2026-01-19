"""Fix validation for the Article Coach.

This module validates whether issues were successfully fixed after user edits.
"""

import sys
import os
from typing import Dict, Tuple

from rich.console import Console

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coaching.problem_detector import Issue, ProblemDetector

console = Console()


class FixValidator:
    """Validates whether fixes improved the article."""

    def __init__(self):
        """Initialize the validator."""
        self.detector = ProblemDetector()

    def validate_fix(self, original_text: str, edited_text: str, issue: Issue) -> Tuple[bool, str, Dict]:
        """Check if the edit improved the issue.

        Args:
            original_text: Original text before edit
            edited_text: Text after user edit
            issue: The issue that was being addressed

        Returns:
            Tuple of (improved: bool, message: str, metrics: dict)
        """
        # Re-analyze the edited text
        new_issues = self.detector.find_all_issues(edited_text)

        # Check if the specific issue type improved
        improved, message, metrics = self._check_improvement(
            original_text, edited_text, issue, new_issues
        )

        return improved, message, metrics

    def _check_improvement(self, original: str, edited: str, issue: Issue, new_issues: list) -> Tuple[bool, str, Dict]:
        """Check if the specific issue improved.

        Args:
            original: Original text
            edited: Edited text
            issue: Original issue
            new_issues: List of issues in edited text

        Returns:
            Tuple of (improved, message, metrics)
        """
        issue_type = issue.type

        # Spelling/Grammar - Check if specific issue no longer exists
        if issue_type in ['spelling', 'grammar']:
            # Count issues of this type in new text
            new_count = len([i for i in new_issues if i.type == issue_type])
            old_count = issue.metrics.get('issue_count', 0)

            if new_count < old_count:
                return True, f"✅ Fixed! Reduced {issue_type} issues from {old_count} to {new_count}", {'before': old_count, 'after': new_count}
            elif new_count == 0:
                return True, f"✅ Perfect! No {issue_type} issues remaining", {'before': old_count, 'after': 0}
            else:
                return False, f"⚠️  Still {new_count} {issue_type} issue(s) remaining", {'before': old_count, 'after': new_count}

        # Passive voice
        elif issue_type == 'passive_voice':
            if self.detector.quality_analyzer:
                new_analysis = self.detector.quality_analyzer.analyze(edited)
                new_pct = new_analysis['passive_voice']['percentage']
                old_pct = issue.metrics.get('percentage', 0)

                improvement = old_pct - new_pct

                if new_pct < 10:
                    return True, f"✅ Excellent! Passive voice reduced to {new_pct:.1f}% (target met)", {'before': old_pct, 'after': new_pct}
                elif improvement > 3:
                    return True, f"✅ Good improvement! Passive voice: {old_pct:.1f}% → {new_pct:.1f}%", {'before': old_pct, 'after': new_pct}
                elif improvement > 0:
                    return True, f"✓ Small improvement. Passive voice: {old_pct:.1f}% → {new_pct:.1f}%", {'before': old_pct, 'after': new_pct}
                else:
                    return False, f"⚠️  No improvement. Passive voice still at {new_pct:.1f}%", {'before': old_pct, 'after': new_pct}

        # Adverbs
        elif issue_type == 'adverbs':
            if self.detector.quality_analyzer:
                new_analysis = self.detector.quality_analyzer.analyze(edited)
                new_rate = new_analysis['adverbs']['per_100_words']
                old_rate = issue.metrics.get('rate', 0)

                improvement = old_rate - new_rate

                if new_rate < 3:
                    return True, f"✅ Excellent! Adverb rate reduced to {new_rate:.1f} per 100 words", {'before': old_rate, 'after': new_rate}
                elif improvement > 0.5:
                    return True, f"✅ Good! Adverbs: {old_rate:.1f} → {new_rate:.1f} per 100 words", {'before': old_rate, 'after': new_rate}
                else:
                    return False, f"⚠️  Still {new_rate:.1f} adverbs per 100 words (target: <3)", {'before': old_rate, 'after': new_rate}

        # Weak verbs
        elif issue_type == 'weak_verbs':
            if self.detector.quality_analyzer:
                new_analysis = self.detector.quality_analyzer.analyze(edited)
                new_pct = new_analysis['weak_verbs']['percentage']
                old_pct = issue.metrics.get('percentage', 0)

                improvement = old_pct - new_pct

                if new_pct < 30:
                    return True, f"✅ Great! Weak verbs reduced to {new_pct:.1f}%", {'before': old_pct, 'after': new_pct}
                elif improvement > 3:
                    return True, f"✅ Improved! Weak verbs: {old_pct:.1f}% → {new_pct:.1f}%", {'before': old_pct, 'after': new_pct}
                else:
                    return False, f"⚠️  Still {new_pct:.1f}% weak verbs (target: <30%)", {'before': old_pct, 'after': new_pct}

        # Readability
        elif issue_type == 'difficult_words':
            if self.detector.readability_analyzer:
                new_analysis = self.detector.readability_analyzer.analyze(edited)
                new_score = new_analysis['flesch_reading_ease']
                old_score = issue.metrics.get('flesch_score', 0)

                improvement = new_score - old_score

                if new_score >= 60:
                    return True, f"✅ Excellent! Readability improved to {new_score:.1f}", {'before': old_score, 'after': new_score}
                elif improvement > 5:
                    return True, f"✅ Better! Readability: {old_score:.1f} → {new_score:.1f}", {'before': old_score, 'after': new_score}
                elif improvement > 0:
                    return True, f"✓ Slight improvement: {old_score:.1f} → {new_score:.1f}", {'before': old_score, 'after': new_score}
                else:
                    return False, f"⚠️  Readability unchanged at {new_score:.1f}", {'before': old_score, 'after': new_score}

        # Sentence length
        elif issue_type == 'sentence_too_long':
            if self.detector.readability_analyzer:
                new_analysis = self.detector.readability_analyzer.analyze(edited)
                new_avg = new_analysis['avg_sentence_length']
                old_avg = issue.metrics.get('avg_sentence_length', 0)

                improvement = old_avg - new_avg

                if new_avg < 20:
                    return True, f"✅ Perfect! Average sentence length: {new_avg:.1f} words", {'before': old_avg, 'after': new_avg}
                elif improvement > 2:
                    return True, f"✅ Better! Sentence length: {old_avg:.1f} → {new_avg:.1f} words", {'before': old_avg, 'after': new_avg}
                else:
                    return False, f"⚠️  Still averaging {new_avg:.1f} words per sentence", {'before': old_avg, 'after': new_avg}

        # Paragraph length
        elif issue_type == 'paragraph_too_long':
            # Check paragraph lengths in edited text
            paragraphs = [p for p in edited.split('\n\n') if p.strip()]
            long_paras = [len(p.split()) for p in paragraphs if len(p.split()) > 150]

            old_count = len(issue.metrics.get('long_paragraphs', []))

            if len(long_paras) == 0:
                return True, f"✅ Excellent! All paragraphs are now <150 words", {'before': old_count, 'after': 0}
            elif len(long_paras) < old_count:
                return True, f"✅ Improved! Long paragraphs: {old_count} → {len(long_paras)}", {'before': old_count, 'after': len(long_paras)}
            else:
                return False, f"⚠️  Still {len(long_paras)} paragraph(s) over 150 words", {'before': old_count, 'after': len(long_paras)}

        # Word repetition
        elif issue_type == 'word_repetition':
            if self.detector.quality_analyzer:
                new_analysis = self.detector.quality_analyzer.analyze(edited)
                new_count = new_analysis['repetition']['total_repetitions']
                old_count = issue.metrics.get('total_repetitions', 0)

                if new_count < old_count:
                    return True, f"✅ Better! Repetitions reduced from {old_count} to {new_count}", {'before': old_count, 'after': new_count}
                else:
                    return False, f"⚠️  Still {new_count} repeated words", {'before': old_count, 'after': new_count}

        # Poor transitions
        elif issue_type == 'poor_transitions':
            if self.detector.quality_analyzer:
                new_analysis = self.detector.quality_analyzer.analyze(edited)
                new_count = new_analysis['transitions']['count']
                old_count = issue.metrics.get('transition_count', 0)

                para_count = len([p for p in edited.split('\n\n') if p.strip()])

                if new_count >= para_count:
                    return True, f"✅ Great! Added transition words ({new_count} transitions)", {'before': old_count, 'after': new_count}
                elif new_count > old_count:
                    return True, f"✅ Improved! Transitions: {old_count} → {new_count}", {'before': old_count, 'after': new_count}
                else:
                    return False, f"⚠️  Still only {new_count} transitions for {para_count} paragraphs", {'before': old_count, 'after': new_count}

        # Default
        return True, "✓ Text edited", {}

    def show_validation_result(self, improved: bool, message: str):
        """Display validation result to user.

        Args:
            improved: Whether the edit improved the issue
            message: Validation message to display
        """
        if improved:
            console.print(f"\n[green]{message}[/green]")
        else:
            console.print(f"\n[yellow]{message}[/yellow]")
            console.print("[yellow]Consider revising further.[/yellow]")

    def calculate_overall_improvements(self, original_text: str, coached_text: str) -> Dict:
        """Calculate overall improvements from original to coached text.

        Args:
            original_text: Original article text
            coached_text: Coached article text

        Returns:
            Dictionary of improvements by metric
        """
        improvements = {}

        # Readability
        if self.detector.readability_analyzer:
            orig_read = self.detector.readability_analyzer.analyze(original_text)
            new_read = self.detector.readability_analyzer.analyze(coached_text)

            improvements['readability'] = (
                orig_read['flesch_reading_ease'],
                new_read['flesch_reading_ease']
            )
            improvements['avg_sentence_length'] = (
                orig_read['avg_sentence_length'],
                new_read['avg_sentence_length']
            )

        # Writing quality
        if self.detector.quality_analyzer:
            orig_quality = self.detector.quality_analyzer.analyze(original_text)
            new_quality = self.detector.quality_analyzer.analyze(coached_text)

            improvements['passive_voice'] = (
                orig_quality['passive_voice']['percentage'],
                new_quality['passive_voice']['percentage']
            )
            improvements['adverbs'] = (
                orig_quality['adverbs']['per_100_words'],
                new_quality['adverbs']['per_100_words']
            )
            improvements['weak_verbs'] = (
                orig_quality['weak_verbs']['percentage'],
                new_quality['weak_verbs']['percentage']
            )

        # Grammar
        if self.detector.grammar_analyzer:
            orig_grammar = self.detector.grammar_analyzer.analyze(original_text)
            new_grammar = self.detector.grammar_analyzer.analyze(coached_text)

            improvements['grammar_issues'] = (
                orig_grammar['total_issues'],
                new_grammar['total_issues']
            )

        return improvements
