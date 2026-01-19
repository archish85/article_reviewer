#!/usr/bin/env python3
"""Test script for Article Coach.

This script tests the Article Coach components to ensure they work correctly.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from coaching.problem_detector import ProblemDetector, IssuePrioritizer
from coaching.fix_validator import FixValidator


def test_problem_detector():
    """Test the ProblemDetector."""
    print("Testing ProblemDetector...")

    # Sample text with issues
    text = """
    The geocentric model was challenged by Copernicus and was later proven wrong by Galileo's observations.
    This paradigm shift was really very significant and had a major impact on scientific thinking.
    The old model was based on observations that were very carefully made by ancient astronomers who were working
    without modern instruments and were trying very hard to understand the cosmos.
    """

    try:
        detector = ProblemDetector()
        issues = detector.find_all_issues(text)

        print(f"✓ Found {len(issues)} issues")

        # Test prioritizer
        prioritizer = IssuePrioritizer()
        top_issues = prioritizer.top_issues(issues, limit=5)

        print(f"✓ Prioritized to top {len(top_issues)} issues")

        for i, issue in enumerate(top_issues, 1):
            print(f"  {i}. {issue.type} (severity: {issue.severity})")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_fix_validator():
    """Test the FixValidator."""
    print("\nTesting FixValidator...")

    original = "The model was challenged by Copernicus."
    edited = "Copernicus challenged the model."

    try:
        validator = FixValidator()

        # Test with a mock issue
        from coaching.problem_detector import Issue
        issue = Issue(
            type='passive_voice',
            severity=5,
            location='Test',
            context=original,
            description='Passive voice',
            why='Test',
            suggested_approach=['Use active voice'],
            metrics={'percentage': 100}
        )

        improved, message, metrics = validator.validate_fix(original, edited, issue)

        print(f"✓ Validation result: {improved}")
        print(f"  Message: {message}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_analyzers():
    """Test the local analyzers."""
    print("\nTesting Local Analyzers...")

    text = "This is a simple test sentence. It should be easy to analyze."

    try:
        from optimization.local_analyzer import (
            ReadabilityAnalyzer,
            WritingQualityAnalyzer
        )

        # Test ReadabilityAnalyzer
        print("  Testing ReadabilityAnalyzer...")
        readability = ReadabilityAnalyzer()
        read_results = readability.analyze(text)
        print(f"    ✓ Flesch Reading Ease: {read_results['flesch_reading_ease']:.1f}")

        # Test WritingQualityAnalyzer
        print("  Testing WritingQualityAnalyzer...")
        quality = WritingQualityAnalyzer()
        quality_results = quality.analyze(text)
        print(f"    ✓ Passive voice: {quality_results['passive_voice']['percentage']:.1f}%")

        return True

    except ImportError as e:
        print(f"  ⚠ Skipping analyzer tests (dependencies not installed): {e}")
        return True  # Not a failure, just skip

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Article Coach - Component Tests")
    print("=" * 60)

    results = []

    # Test analyzers
    results.append(("Analyzers", test_analyzers()))

    # Test problem detector
    results.append(("ProblemDetector", test_problem_detector()))

    # Test fix validator
    results.append(("FixValidator", test_fix_validator()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + ("All tests passed!" if all_passed else "Some tests failed"))

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
