"""Utility functions for the Article Reviewer."""

import os
from pathlib import Path
from reporter import ReportGenerator


def load_article(source):
    """Load article from file or direct text.

    Args:
        source: File path or direct text string.

    Returns:
        Article text as string.
    """
    # Check if source is a file path
    if os.path.isfile(source):
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read file {source}: {str(e)}")

    # Otherwise, treat as direct text
    return source


def save_report(report_content, output_path, cost_summary=None):
    """Save the review report to a file.

    Args:
        report_content: The report content as a string.
        output_path: Path where the report should be saved.
        cost_summary: Optional cost summary dictionary to append.
    """
    try:
        # Add cost summary if provided
        if cost_summary:
            cost_section = ReportGenerator.format_cost_summary(cost_summary)
            full_report = f"{report_content}\n\n{cost_section}"
        else:
            full_report = report_content

        # Ensure parent directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write the report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_report)

    except Exception as e:
        raise ValueError(f"Failed to save report to {output_path}: {str(e)}")


def validate_file_exists(file_path):
    """Validate that a file exists.

    Args:
        file_path: Path to the file.

    Returns:
        True if file exists.

    Raises:
        FileNotFoundError if file doesn't exist.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return True


def get_file_info(file_path):
    """Get information about a file.

    Args:
        file_path: Path to the file.

    Returns:
        Dictionary with file information.
    """
    path = Path(file_path)

    return {
        'name': path.name,
        'size': path.stat().st_size,
        'extension': path.suffix,
        'absolute_path': str(path.absolute())
    }


def format_file_size(size_bytes):
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string (e.g., "1.5 KB", "2.3 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
