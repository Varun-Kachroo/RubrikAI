"""
utils.py
Helper functions for score calculations and performance metrics.
"""

import re


def calculate_percentage(score: float, max_score: float) -> float:
    """
    Calculate percentage score.
    
    Args:
        score: Awarded score
        max_score: Maximum possible score
        
    Returns:
        float: Percentage (0-100)
    """
    if max_score == 0:
        return 0.0
    return round((score / max_score) * 100, 2)


def extract_numerical_answer(text: str) -> list:
    """
    Extract numerical values from text for mathematical validation.
    
    Args:
        text: Answer text
        
    Returns:
        list: List of numbers found in text
    """
    # Match integers and decimals (including negative)
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(m) for m in matches if m]


def validate_mathematical_answer(student_answer: str, correct_answer: str, tolerance: float = 0.001) -> dict:
    """
    Validate mathematical answers with exact numerical checking.
    
    Args:
        student_answer: Student's answer text
        correct_answer: Correct answer (can be number or expression)
        tolerance: Acceptable difference for floating point (default: 0.001)
        
    Returns:
        dict: {is_exact_match: bool, student_values: list, expected_values: list}
    """
    student_nums = extract_numerical_answer(student_answer)
    correct_nums = extract_numerical_answer(correct_answer)
    
    if not student_nums or not correct_nums:
        return {
            'is_exact_match': None,  # Can't validate, no numbers found
            'student_values': student_nums,
            'expected_values': correct_nums
        }
    
    # Check if all expected numbers are present in student answer
    is_match = True
    for expected in correct_nums:
        found = False
        for student in student_nums:
            if abs(student - expected) <= tolerance:
                found = True
                break
        if not found:
            is_match = False
            break
    
    return {
        'is_exact_match': is_match,
        'student_values': student_nums,
        'expected_values': correct_nums
    }


def get_performance_label(percentage: float) -> str:
    """
    Determine performance label based on percentage.
    
    Args:
        percentage: Score percentage (0-100)
        
    Returns:
        str: Performance label (Poor/Below Average/Average/Good/Excellent)
    """
    if percentage >= 90:
        return "Excellent"
    elif percentage >= 75:
        return "Good"
    elif percentage >= 60:
        return "Average"
    elif percentage >= 40:
        return "Below Average"
    else:
        return "Poor"


def get_performance_color(label: str) -> str:
    """
    Get color code for performance label (for progress bars/UI).
    
    Args:
        label: Performance label
        
    Returns:
        str: Color name for Streamlit
    """
    colors = {
        "Excellent": "green",
        "Good": "blue",
        "Average": "orange",
        "Below Average": "red",
        "Poor": "red"
    }
    return colors.get(label, "gray")


def calculate_total_score(scores: list) -> dict:
    """
    Calculate total score and max score from criterion scores.
    
    Args:
        scores: List of score dictionaries with 'awarded' and 'max' keys
        
    Returns:
        dict: {"total": awarded_total, "max": max_total}
    """
    total = sum(item.get('awarded', 0) for item in scores)
    max_total = sum(item.get('max', 0) for item in scores)
    
    return {
        "total": total,
        "max": max_total
    }


def format_score_display(score: float, max_score: float) -> str:
    """
    Format score for display (e.g., "8/10" or "8.5/10").
    
    Args:
        score: Awarded score
        max_score: Maximum possible score
        
    Returns:
        str: Formatted score string
    """
    # If both are whole numbers, display without decimals
    if score == int(score) and max_score == int(max_score):
        return f"{int(score)}/{int(max_score)}"
    return f"{score}/{max_score}"


def get_performance_emoji(label: str) -> str:
    """
    Get emoji for performance label.
    
    Args:
        label: Performance label
        
    Returns:
        str: Emoji representation
    """
    emojis = {
        "Excellent": "🌟",
        "Good": "✅",
        "Average": "👍",
        "Below Average": "⚠️",
        "Poor": "❌"
    }
    return emojis.get(label, "📊")
