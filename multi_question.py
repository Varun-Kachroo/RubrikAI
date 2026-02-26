"""
multi_question.py
Handles multi-question assignment structure with a single shared rubric.
"""

import pandas as pd
from typing import List, Dict, Any


class MultiQuestionAssignment:
    """
    Manages assignments with multiple questions sharing a single rubric.
    """
    
    def __init__(self):
        """Initialize empty assignment."""
        self.assignment_title = ""
        self.questions = []
        self.rubric = None  # Single rubric for all questions
        self.max_marks_per_question = 0
    
    def set_rubric(self, rubric_df: pd.DataFrame):
        """
        Set the rubric that will be used for all questions.
        
        Args:
            rubric_df: DataFrame with CRITERIA and TOTAL MARKS columns
        """
        self.rubric = rubric_df.copy()
        self.max_marks_per_question = self._calculate_max_marks(rubric_df)
    
    def _calculate_max_marks(self, rubric_df: pd.DataFrame) -> int:
        """Calculate total max marks from rubric."""
        total = 0
        for idx, row in rubric_df.iterrows():
            if pd.notna(row['TOTAL MARKS']) and str(row['CRITERIA']).strip():
                total += int(row['TOTAL MARKS'])
        return total
    
    def add_question(self, question_text: str) -> int:
        """
        Add a question to the assignment (uses shared rubric).
        
        Args:
            question_text: The question text
            
        Returns:
            int: Question number (1-indexed)
        """
        question_data = {
            "question_number": len(self.questions) + 1,
            "question_text": question_text
        }
        self.questions.append(question_data)
        return question_data["question_number"]
    
    def get_question(self, question_number: int) -> Dict:
        """Get question data by number."""
        if 0 < question_number <= len(self.questions):
            return self.questions[question_number - 1]
        return None
    
    def remove_question(self, question_number: int):
        """Remove a question and renumber remaining questions."""
        if 0 < question_number <= len(self.questions):
            self.questions.pop(question_number - 1)
            # Renumber questions
            for i, q in enumerate(self.questions):
                q["question_number"] = i + 1
    
    def get_total_marks(self) -> int:
        """Get total marks for entire assignment (marks per question × number of questions)."""
        return self.max_marks_per_question * len(self.questions)
    
    def get_question_count(self) -> int:
        """Get number of questions in assignment."""
        return len(self.questions)
    
    def format_rubric_for_evaluation(self) -> str:
        """
        Format the shared rubric for LLM evaluation.
        
        Returns:
            str: Formatted rubric string
        """
        if self.rubric is None:
            return ""
        
        rubric_formatted = "RUBRIC (applies to each question):\n\n"
        for idx, row in self.rubric.iterrows():
            if str(row['CRITERIA']).strip() and pd.notna(row['TOTAL MARKS']):
                rubric_formatted += f"Criterion: {row['CRITERIA']}\n"
                rubric_formatted += f"Maximum Marks: {row['TOTAL MARKS']}\n"
                rubric_formatted += "---\n"
        
        return rubric_formatted
    
    def to_dict(self) -> Dict:
        """Convert assignment to dictionary for saving."""
        return {
            "title": self.assignment_title,
            "rubric": self.rubric.to_dict('records') if self.rubric is not None else [],
            "max_marks_per_question": self.max_marks_per_question,
            "questions": [
                {
                    "question_number": q["question_number"],
                    "question_text": q["question_text"]
                }
                for q in self.questions
            ],
            "total_marks": self.get_total_marks()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MultiQuestionAssignment':
        """Load assignment from dictionary."""
        assignment = cls()
        assignment.assignment_title = data.get("title", "")
        
        # Load rubric
        if data.get("rubric"):
            rubric_df = pd.DataFrame(data["rubric"])
            assignment.set_rubric(rubric_df)
        
        # Load questions
        for q_data in data.get("questions", []):
            assignment.questions.append({
                "question_number": q_data["question_number"],
                "question_text": q_data["question_text"]
            })
        
        return assignment


def combine_evaluation_results(individual_results: List[Dict]) -> Dict[str, Any]:
    """
    Combine individual question evaluation results into overall summary.
    
    Args:
        individual_results: List of evaluation results for each question
        
    Returns:
        dict: Combined results with totals and overall metrics
    """
    total_score = 0
    total_max = 0
    all_feedback = []
    
    for result in individual_results:
        if "total_score" in result:
            total_score += result["total_score"]
        
        # Calculate max from scores
        if "scores" in result:
            for score_item in result["scores"]:
                total_max += score_item.get("max", 0)
        
        # Collect feedback
        if "feedback" in result:
            all_feedback.extend(result["feedback"])
    
    return {
        "individual_results": individual_results,
        "total_score": total_score,
        "total_max": total_max,
        "combined_feedback": all_feedback
    }
