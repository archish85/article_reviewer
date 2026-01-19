"""Local analysis tools for article quality assessment.

This module provides rule-based analysis tools that run locally without API costs.
Used by both the Article Coach and the optimized review workflow.
"""

import re
from collections import Counter
from typing import Dict, List, Tuple

try:
    import language_tool_python
    GRAMMAR_AVAILABLE = True
except ImportError:
    GRAMMAR_AVAILABLE = False
    print("Warning: language-tool-python not installed. Grammar checking disabled.")

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    print("Warning: textstat not installed. Readability metrics disabled.")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not installed. Writing quality analysis disabled.")

try:
    from textblob import TextBlob
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("Warning: Sentiment analysis libraries not installed.")


class GrammarAnalyzer:
    """Analyzes grammar, spelling, and punctuation using LanguageTool."""

    def __init__(self, language='en-US'):
        if not GRAMMAR_AVAILABLE:
            raise ImportError("language-tool-python is required. Install with: pip install language-tool-python")

        self.tool = language_tool_python.LanguageTool(language)

    def analyze(self, text: str) -> Dict:
        """Analyze text for grammar and spelling issues.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with grammar and spelling analysis.
        """
        matches = self.tool.check(text)

        # Categorize issues
        grammar_issues = []
        spelling_issues = []
        punctuation_issues = []

        for match in matches:
            issue = {
                'message': match.message,
                'context': match.context,
                'offset': match.offset,
                'length': match.errorLength,
                'replacements': match.replacements[:3],  # Top 3 suggestions
                'rule': match.ruleId
            }

            if 'SPELL' in match.ruleId or 'MORFOLOGIK' in match.ruleId:
                spelling_issues.append(issue)
            elif 'PUNCT' in match.ruleId or 'COMMA' in match.ruleId:
                punctuation_issues.append(issue)
            else:
                grammar_issues.append(issue)

        return {
            'grammar_issues': grammar_issues,
            'spelling_issues': spelling_issues,
            'punctuation_issues': punctuation_issues,
            'total_issues': len(matches),
            'issue_breakdown': {
                'grammar': len(grammar_issues),
                'spelling': len(spelling_issues),
                'punctuation': len(punctuation_issues)
            }
        }

    def get_top_issues(self, analysis: Dict, limit: int = 5) -> List[Dict]:
        """Get the most important issues.

        Args:
            analysis: Analysis result from analyze()
            limit: Maximum number of issues to return

        Returns:
            List of top issues
        """
        all_issues = (
            analysis['spelling_issues'] +
            analysis['grammar_issues'] +
            analysis['punctuation_issues']
        )

        # Sort by severity (spelling first, then grammar, then punctuation)
        return all_issues[:limit]


class ReadabilityAnalyzer:
    """Analyzes text readability using various metrics."""

    def __init__(self):
        if not TEXTSTAT_AVAILABLE:
            raise ImportError("textstat is required. Install with: pip install textstat")

    def analyze(self, text: str) -> Dict:
        """Analyze text readability.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with readability metrics.
        """
        return {
            # Primary metrics
            'flesch_reading_ease': textstat.flesch_reading_ease(text),
            'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text),

            # Additional metrics
            'smog_index': textstat.smog_index(text),
            'coleman_liau_index': textstat.coleman_liau_index(text),
            'automated_readability_index': textstat.automated_readability_index(text),
            'dale_chall_readability_score': textstat.dale_chall_readability_score(text),
            'gunning_fog': textstat.gunning_fog(text),

            # Statistics
            'word_count': textstat.lexicon_count(text, removepunct=True),
            'sentence_count': textstat.sentence_count(text),
            'avg_sentence_length': textstat.avg_sentence_length(text),
            'syllable_count': textstat.syllable_count(text),
            'difficult_words': textstat.difficult_words(text),
            'char_count': len(text),

            # Interpretation
            'reading_level': self._interpret_grade_level(textstat.flesch_kincaid_grade(text)),
            'reading_ease_interpretation': self._interpret_reading_ease(textstat.flesch_reading_ease(text))
        }

    def _interpret_grade_level(self, grade: float) -> str:
        """Interpret Flesch-Kincaid grade level."""
        if grade < 6:
            return "Elementary"
        elif grade < 9:
            return "Middle School"
        elif grade < 13:
            return "High School"
        elif grade < 16:
            return "College"
        else:
            return "Graduate"

    def _interpret_reading_ease(self, score: float) -> str:
        """Interpret Flesch Reading Ease score."""
        if score >= 90:
            return "Very Easy"
        elif score >= 80:
            return "Easy"
        elif score >= 70:
            return "Fairly Easy"
        elif score >= 60:
            return "Standard"
        elif score >= 50:
            return "Fairly Difficult"
        elif score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"


class WritingQualityAnalyzer:
    """Analyzes writing quality using spaCy for linguistic patterns."""

    def __init__(self):
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy is required. Install with: pip install spacy && python -m spacy download en_core_web_sm")

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise ImportError("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")

    def analyze(self, text: str) -> Dict:
        """Analyze writing quality.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with writing quality metrics.
        """
        doc = self.nlp(text)

        return {
            'passive_voice': self._detect_passive_voice(doc),
            'adverbs': self._analyze_adverbs(doc),
            'weak_verbs': self._detect_weak_verbs(doc),
            'sentence_variety': self._analyze_sentence_variety(doc),
            'repetition': self._detect_repetition(doc),
            'transitions': self._analyze_transitions(doc),
            'paragraph_stats': self._analyze_paragraphs(text)
        }

    def _detect_passive_voice(self, doc) -> Dict:
        """Detect passive voice constructions."""
        passive_count = 0
        passive_sentences = []

        for sent in doc.sents:
            # Look for passive constructions (be + past participle)
            for token in sent:
                if token.dep_ == "auxpass":  # Passive auxiliary
                    passive_count += 1
                    passive_sentences.append(sent.text)
                    break

        total_sentences = len(list(doc.sents))
        percentage = (passive_count / total_sentences * 100) if total_sentences > 0 else 0

        return {
            'count': passive_count,
            'percentage': percentage,
            'examples': passive_sentences[:5],
            'is_excessive': percentage > 10  # >10% is considered excessive
        }

    def _analyze_adverbs(self, doc) -> Dict:
        """Analyze adverb usage."""
        adverbs = [token.text for token in doc if token.pos_ == "ADV"]

        return {
            'count': len(adverbs),
            'per_100_words': (len(adverbs) / len(doc)) * 100 if len(doc) > 0 else 0,
            'most_common': Counter(adverbs).most_common(10),
            'is_excessive': (len(adverbs) / len(doc) * 100) > 3 if len(doc) > 0 else False
        }

    def _detect_weak_verbs(self, doc) -> Dict:
        """Detect weak verbs (be, have, do, get, make)."""
        weak_verbs = {'be', 'is', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'get', 'got', 'make', 'made'}
        weak_verb_count = sum(1 for token in doc if token.pos_ == "VERB" and token.lemma_ in weak_verbs)
        total_verbs = sum(1 for token in doc if token.pos_ == "VERB")

        return {
            'count': weak_verb_count,
            'total_verbs': total_verbs,
            'percentage': (weak_verb_count / total_verbs * 100) if total_verbs > 0 else 0,
            'is_excessive': (weak_verb_count / total_verbs * 100) > 30 if total_verbs > 0 else False
        }

    def _analyze_sentence_variety(self, doc) -> Dict:
        """Analyze sentence length variety."""
        lengths = [len(list(sent)) for sent in doc.sents]

        if not lengths:
            return {'avg_length': 0, 'min_length': 0, 'max_length': 0, 'variety_score': 0}

        return {
            'avg_length': sum(lengths) / len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'variety_score': len(set(lengths)) / len(lengths),  # 0-1, higher is better
            'long_sentences': [i for i, length in enumerate(lengths) if length > 25]  # Sentence indices
        }

    def _detect_repetition(self, doc) -> Dict:
        """Detect word repetition within 50 words."""
        words = [token.lemma_.lower() for token in doc if not token.is_stop and token.is_alpha]

        word_positions = {}
        repetitions = []

        for i, word in enumerate(words):
            if word in word_positions:
                for prev_pos in word_positions[word]:
                    if i - prev_pos <= 50:  # Within 50 words
                        repetitions.append((word, i - prev_pos))

            if word not in word_positions:
                word_positions[word] = []
            word_positions[word].append(i)

        return {
            'repeated_words': Counter([r[0] for r in repetitions]).most_common(10),
            'total_repetitions': len(repetitions),
            'is_excessive': len(repetitions) > len(words) * 0.1  # >10% repetition
        }

    def _analyze_transitions(self, doc) -> Dict:
        """Analyze transition word usage."""
        transitions = {
            'however', 'therefore', 'moreover', 'furthermore', 'consequently',
            'nevertheless', 'additionally', 'meanwhile', 'thus', 'hence',
            'first', 'second', 'third', 'finally', 'in conclusion'
        }

        found_transitions = [token.text.lower() for token in doc if token.text.lower() in transitions]

        return {
            'count': len(found_transitions),
            'types_used': Counter(found_transitions),
            'variety': len(set(found_transitions))
        }

    def _analyze_paragraphs(self, text: str) -> Dict:
        """Analyze paragraph structure."""
        paragraphs = [p for p in text.split('\n\n') if p.strip()]

        if not paragraphs:
            return {'count': 0, 'avg_length': 0, 'lengths': []}

        lengths = [len(p.split()) for p in paragraphs]

        return {
            'count': len(paragraphs),
            'avg_length': sum(lengths) / len(lengths),
            'lengths': lengths,
            'long_paragraphs': [i for i, length in enumerate(lengths) if length > 150]  # >150 words
        }


class SentimentAnalyzer:
    """Analyzes text sentiment and tone."""

    def __init__(self):
        if not SENTIMENT_AVAILABLE:
            raise ImportError("Sentiment analysis libraries required. Install with: pip install textblob vaderSentiment")

        self.vader = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> Dict:
        """Analyze text sentiment.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with sentiment analysis.
        """
        # TextBlob analysis
        blob = TextBlob(text)

        # VADER analysis (better for social text and intensity)
        vader_scores = self.vader.polarity_scores(text)

        return {
            'textblob': {
                'polarity': blob.sentiment.polarity,  # -1 to 1
                'subjectivity': blob.sentiment.subjectivity  # 0 to 1
            },
            'vader': vader_scores,
            'tone': self._interpret_tone(blob.sentiment.polarity),
            'is_subjective': blob.sentiment.subjectivity > 0.6
        }

    def _interpret_tone(self, polarity: float) -> str:
        """Interpret polarity as tone."""
        if polarity > 0.3:
            return "Positive"
        elif polarity < -0.3:
            return "Negative"
        else:
            return "Neutral"


class LinguisticAnalyzer:
    """Analyzes linguistic features using spaCy."""

    def __init__(self):
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy is required. Install with: pip install spacy && python -m spacy download en_core_web_sm")

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise ImportError("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")

    def analyze(self, text: str) -> Dict:
        """Analyze linguistic features.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with linguistic analysis.
        """
        doc = self.nlp(text)

        return {
            'entities': self._extract_entities(doc),
            'pos_distribution': self._analyze_pos(doc),
            'key_phrases': self._extract_noun_phrases(doc)
        }

    def _extract_entities(self, doc) -> Dict:
        """Extract named entities."""
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)

        return {
            'by_type': entities,
            'total_count': len(doc.ents),
            'unique_entities': len(set(ent.text for ent in doc.ents))
        }

    def _analyze_pos(self, doc) -> Dict:
        """Analyze part-of-speech distribution."""
        pos_counts = Counter(token.pos_ for token in doc)

        return {
            'counts': dict(pos_counts),
            'percentages': {
                pos: (count / len(doc)) * 100
                for pos, count in pos_counts.items()
            }
        }

    def _extract_noun_phrases(self, doc) -> Dict:
        """Extract noun phrases (key concepts)."""
        phrases = [chunk.text for chunk in doc.noun_chunks]

        return {
            'count': len(phrases),
            'examples': phrases[:20],
            'most_common': Counter(phrases).most_common(10)
        }
