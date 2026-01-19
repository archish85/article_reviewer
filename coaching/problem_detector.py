"""Problem detection for the Article Coach.

This module identifies writing issues and prioritizes them for user attention.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimization.local_analyzer import (
    GrammarAnalyzer,
    ReadabilityAnalyzer,
    WritingQualityAnalyzer,
    SentimentAnalyzer,
    LinguisticAnalyzer
)


@dataclass
class Issue:
    """Represents a writing issue."""
    type: str  # 'grammar', 'spelling', 'readability', 'style', 'structure'
    severity: int  # 1-10, higher is more important
    location: str  # Description of where the issue is
    context: str  # The problematic text
    description: str  # What's wrong
    why: str  # Why it matters
    suggested_approach: List[str]  # Steps to fix
    metrics: Dict  # Relevant metrics


class IssuePrioritizer:
    """Prioritizes issues based on severity and impact."""

    SEVERITY_SCORES = {
        # Correctness (must fix)
        'spelling': 10,
        'grammar': 9,
        'factual_error': 10,

        # Readability (important)
        'sentence_too_long': 7,
        'difficult_words': 6,
        'poor_transitions': 6,
        'paragraph_too_long': 6,

        # Style (nice to have)
        'passive_voice': 5,
        'weak_verbs': 4,
        'adverbs': 3,
        'word_repetition': 4,
    }

    def score_issue(self, issue: Issue) -> int:
        """Score issue importance (1-10)."""
        return self.SEVERITY_SCORES.get(issue.type, 3)

    def top_issues(self, issues: List[Issue], limit: int = 10) -> List[Issue]:
        """Get top priority issues.

        Args:
            issues: List of all detected issues
            limit: Maximum number of issues to return

        Returns:
            List of top priority issues, sorted by severity
        """
        # Sort by severity (descending)
        sorted_issues = sorted(issues, key=lambda x: x.severity, reverse=True)

        # Filter to only issues above minimum threshold (severity >= 5)
        important_issues = [i for i in sorted_issues if i.severity >= 5]

        return important_issues[:limit]


class ProblemDetector:
    """Detects writing problems in articles."""

    def __init__(self):
        """Initialize all analyzers."""
        try:
            self.grammar_analyzer = GrammarAnalyzer()
        except ImportError as e:
            print(f"Warning: GrammarAnalyzer not available: {e}")
            self.grammar_analyzer = None

        try:
            self.readability_analyzer = ReadabilityAnalyzer()
        except ImportError as e:
            print(f"Warning: ReadabilityAnalyzer not available: {e}")
            self.readability_analyzer = None

        try:
            self.quality_analyzer = WritingQualityAnalyzer()
        except ImportError as e:
            print(f"Warning: WritingQualityAnalyzer not available: {e}")
            self.quality_analyzer = None

        try:
            self.sentiment_analyzer = SentimentAnalyzer()
        except ImportError as e:
            print(f"Warning: SentimentAnalyzer not available: {e}")
            self.sentiment_analyzer = None

        try:
            self.linguistic_analyzer = LinguisticAnalyzer()
        except ImportError as e:
            print(f"Warning: LinguisticAnalyzer not available: {e}")
            self.linguistic_analyzer = None

        self.prioritizer = IssuePrioritizer()

    def find_all_issues(self, text: str) -> List[Issue]:
        """Find all writing issues in the text.

        Args:
            text: The article text to analyze

        Returns:
            List of detected issues
        """
        issues = []

        # Grammar and spelling issues
        if self.grammar_analyzer:
            issues.extend(self._detect_grammar_issues(text))

        # Readability issues
        if self.readability_analyzer:
            issues.extend(self._detect_readability_issues(text))

        # Writing quality issues
        if self.quality_analyzer:
            issues.extend(self._detect_quality_issues(text))

        # Structure issues
        issues.extend(self._detect_structure_issues(text))

        # Add severity scores
        for issue in issues:
            issue.severity = self.prioritizer.score_issue(issue)

        return issues

    def _detect_grammar_issues(self, text: str) -> List[Issue]:
        """Detect grammar and spelling issues."""
        analysis = self.grammar_analyzer.analyze(text)
        issues = []

        # Spelling issues (high priority)
        for spell_issue in analysis['spelling_issues'][:5]:  # Top 5
            issues.append(Issue(
                type='spelling',
                severity=10,
                location=f"Character {spell_issue['offset']}",
                context=spell_issue['context'],
                description=spell_issue['message'],
                why="Spelling errors hurt credibility and distract readers",
                suggested_approach=[
                    f"Replace with: {', '.join(spell_issue['replacements'][:3])}" if spell_issue['replacements'] else "Check spelling"
                ],
                metrics={'issue_count': len(analysis['spelling_issues'])}
            ))

        # Grammar issues (high priority)
        for gram_issue in analysis['grammar_issues'][:5]:  # Top 5
            issues.append(Issue(
                type='grammar',
                severity=9,
                location=f"Character {gram_issue['offset']}",
                context=gram_issue['context'],
                description=gram_issue['message'],
                why="Grammar errors reduce clarity and professionalism",
                suggested_approach=[
                    f"Consider: {', '.join(gram_issue['replacements'][:3])}" if gram_issue['replacements'] else "Review grammar rule"
                ],
                metrics={'issue_count': len(analysis['grammar_issues'])}
            ))

        return issues

    def _detect_readability_issues(self, text: str) -> List[Issue]:
        """Detect readability issues."""
        analysis = self.readability_analyzer.analyze(text)
        issues = []

        # Low readability score
        if analysis['flesch_reading_ease'] < 50:
            issues.append(Issue(
                type='difficult_words',
                severity=6,
                location="Throughout article",
                context=f"Readability score: {analysis['flesch_reading_ease']:.1f} ({analysis['reading_ease_interpretation']})",
                description="Article is difficult to read",
                why="Lower readability scores mean fewer people can easily understand your writing",
                suggested_approach=[
                    "Use simpler words where possible",
                    "Break long sentences into shorter ones",
                    f"Target: Flesch Reading Ease above 60 (currently {analysis['flesch_reading_ease']:.1f})"
                ],
                metrics={
                    'flesch_score': analysis['flesch_reading_ease'],
                    'difficult_words': analysis['difficult_words'],
                    'avg_sentence_length': analysis['avg_sentence_length']
                }
            ))

        # Long sentences
        if analysis['avg_sentence_length'] > 20:
            issues.append(Issue(
                type='sentence_too_long',
                severity=7,
                location="Throughout article",
                context=f"Average sentence length: {analysis['avg_sentence_length']:.1f} words",
                description="Sentences are too long on average",
                why="Long sentences are harder to follow and can lose readers",
                suggested_approach=[
                    "Break long sentences (>25 words) into two shorter ones",
                    "Use periods instead of commas to separate ideas",
                    f"Target: Average sentence length under 20 words (currently {analysis['avg_sentence_length']:.1f})"
                ],
                metrics={'avg_sentence_length': analysis['avg_sentence_length']}
            ))

        return issues

    def _detect_quality_issues(self, text: str) -> List[Issue]:
        """Detect writing quality issues."""
        analysis = self.quality_analyzer.analyze(text)
        issues = []

        # Passive voice
        if analysis['passive_voice']['is_excessive']:
            passive_pct = analysis['passive_voice']['percentage']
            issues.append(Issue(
                type='passive_voice',
                severity=5,
                location="Multiple paragraphs",
                context=f"{len(analysis['passive_voice']['examples'])} passive constructions found",
                description=f"Excessive passive voice ({passive_pct:.1f}%)",
                why="Passive voice makes writing less direct and engaging. Active voice is clearer and stronger.",
                suggested_approach=[
                    "Identify the actor (who did the action)",
                    "Make the actor the subject of the sentence",
                    "Use active verbs",
                    f"Target: <10% passive voice (currently {passive_pct:.1f}%)"
                ],
                metrics={
                    'percentage': passive_pct,
                    'count': analysis['passive_voice']['count'],
                    'examples': analysis['passive_voice']['examples'][:3]
                }
            ))

        # Excessive adverbs
        if analysis['adverbs']['is_excessive']:
            adverb_rate = analysis['adverbs']['per_100_words']
            issues.append(Issue(
                type='adverbs',
                severity=3,
                location="Throughout article",
                context=f"{analysis['adverbs']['count']} adverbs ({adverb_rate:.1f} per 100 words)",
                description="Too many adverbs",
                why="Excessive adverbs weaken writing. Stronger verbs are better than weak verbs + adverbs.",
                suggested_approach=[
                    "Replace 'walked slowly' with 'ambled' or 'strolled'",
                    "Remove unnecessary intensifiers like 'very', 'really', 'quite'",
                    f"Target: <3 adverbs per 100 words (currently {adverb_rate:.1f})"
                ],
                metrics={
                    'count': analysis['adverbs']['count'],
                    'rate': adverb_rate,
                    'most_common': analysis['adverbs']['most_common'][:5]
                }
            ))

        # Weak verbs
        if analysis['weak_verbs']['is_excessive']:
            weak_verb_pct = analysis['weak_verbs']['percentage']
            issues.append(Issue(
                type='weak_verbs',
                severity=4,
                location="Throughout article",
                context=f"{analysis['weak_verbs']['count']} weak verbs ({weak_verb_pct:.1f}%)",
                description="Too many weak verbs (be, have, do, get)",
                why="Weak verbs create passive, lifeless writing. Strong verbs make writing vivid.",
                suggested_approach=[
                    "Replace 'is able to' with 'can'",
                    "Replace 'has impact on' with 'affects' or 'influences'",
                    "Use action verbs instead of 'to be' constructions",
                    f"Target: <30% weak verbs (currently {weak_verb_pct:.1f}%)"
                ],
                metrics={
                    'percentage': weak_verb_pct,
                    'count': analysis['weak_verbs']['count']
                }
            ))

        # Word repetition
        if analysis['repetition']['is_excessive']:
            issues.append(Issue(
                type='word_repetition',
                severity=4,
                location="Multiple sections",
                context=f"{analysis['repetition']['total_repetitions']} repeated words",
                description="Excessive word repetition",
                why="Repeating the same words too often makes writing monotonous. Use synonyms for variety.",
                suggested_approach=[
                    "Use synonyms for variety",
                    "Rephrase sentences to avoid repetition",
                    "Most repeated: " + ", ".join([f"{word} ({count}x)" for word, count in analysis['repetition']['repeated_words'][:3]])
                ],
                metrics={
                    'total_repetitions': analysis['repetition']['total_repetitions'],
                    'repeated_words': analysis['repetition']['repeated_words'][:10]
                }
            ))

        # Poor transitions
        if analysis['transitions']['count'] < analysis['paragraph_stats']['count']:
            issues.append(Issue(
                type='poor_transitions',
                severity=6,
                location="Between paragraphs",
                context=f"{analysis['transitions']['count']} transitions in {analysis['paragraph_stats']['count']} paragraphs",
                description="Few transition words between ideas",
                why="Transition words help readers follow your logic and connect ideas smoothly.",
                suggested_approach=[
                    "Add transitions like 'however', 'therefore', 'moreover'",
                    "Connect paragraphs with transitional sentences",
                    "Show relationships between ideas explicitly"
                ],
                metrics={
                    'transition_count': analysis['transitions']['count'],
                    'paragraph_count': analysis['paragraph_stats']['count']
                }
            ))

        return issues

    def _detect_structure_issues(self, text: str) -> List[Issue]:
        """Detect structural issues."""
        issues = []

        # Analyze paragraphs
        paragraphs = [p for p in text.split('\n\n') if p.strip()]

        # Long paragraphs
        long_paragraphs = []
        for i, para in enumerate(paragraphs):
            word_count = len(para.split())
            if word_count > 150:
                long_paragraphs.append((i + 1, word_count))

        if long_paragraphs:
            issues.append(Issue(
                type='paragraph_too_long',
                severity=6,
                location=f"Paragraph(s) {', '.join([str(p[0]) for p in long_paragraphs[:3]])}",
                context=f"{len(long_paragraphs)} paragraphs over 150 words",
                description="Some paragraphs are too long",
                why="Long paragraphs are intimidating and hard to follow. Readers may skip them.",
                suggested_approach=[
                    "Break long paragraphs into smaller chunks",
                    "Each paragraph should focus on one main idea",
                    "Target: <150 words per paragraph",
                    f"Longest: {max([p[1] for p in long_paragraphs])} words"
                ],
                metrics={
                    'long_paragraphs': long_paragraphs,
                    'total_paragraphs': len(paragraphs)
                }
            ))

        return issues
