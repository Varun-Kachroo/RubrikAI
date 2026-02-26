"""
database.py
SQLite database integration for RubriqAI - handles persistence of assignments and evaluations.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager


class Database:
    """
    Manages SQLite database for storing assignments, questions, rubrics, and evaluations.
    """
    
    def __init__(self, db_path: str = "rubriqai.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Assignments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_questions INTEGER NOT NULL,
                    max_marks_per_question INTEGER NOT NULL,
                    total_marks INTEGER NOT NULL,
                    assignment_type TEXT NOT NULL
                )
            """)
            
            # Questions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assignment_id INTEGER NOT NULL,
                    question_number INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE
                )
            """)
            
            # Rubrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rubrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assignment_id INTEGER NOT NULL,
                    criteria TEXT NOT NULL,
                    total_marks INTEGER NOT NULL,
                    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE
                )
            """)
            
            # Evaluations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assignment_id INTEGER NOT NULL,
                    student_name TEXT,
                    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_score REAL NOT NULL,
                    max_score REAL NOT NULL,
                    percentage REAL NOT NULL,
                    evaluation_mode TEXT NOT NULL,
                    results_json TEXT NOT NULL,
                    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
    
    # ===== ASSIGNMENT OPERATIONS =====
    
    def save_assignment(self, assignment_data: Dict) -> int:
        """
        Save assignment to database.
        
        Args:
            assignment_data: Dictionary with assignment details from MultiQuestionAssignment.to_dict()
            
        Returns:
            int: Assignment ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Determine assignment type
            assignment_type = "multi" if assignment_data.get('questions') else "single"
            
            # Insert assignment
            cursor.execute("""
                INSERT INTO assignments (title, total_questions, max_marks_per_question, total_marks, assignment_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                assignment_data.get('title', 'Untitled Assignment'),
                len(assignment_data.get('questions', [])),
                assignment_data.get('max_marks_per_question', 0),
                assignment_data.get('total_marks', 0),
                assignment_type
            ))
            
            assignment_id = cursor.lastrowid
            
            # Insert questions
            for question in assignment_data.get('questions', []):
                cursor.execute("""
                    INSERT INTO questions (assignment_id, question_number, question_text)
                    VALUES (?, ?, ?)
                """, (assignment_id, question['question_number'], question['question_text']))
            
            # Insert rubric
            for rubric_item in assignment_data.get('rubric', []):
                cursor.execute("""
                    INSERT INTO rubrics (assignment_id, criteria, total_marks)
                    VALUES (?, ?, ?)
                """, (assignment_id, rubric_item['CRITERIA'], rubric_item['TOTAL MARKS']))
            
            conn.commit()
            return assignment_id
    
    def load_assignment(self, assignment_id: int) -> Optional[Dict]:
        """
        Load assignment from database.
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            Dict: Assignment data compatible with MultiQuestionAssignment.from_dict()
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get assignment
            cursor.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
            assignment = cursor.fetchone()
            
            if not assignment:
                return None
            
            # Get questions
            cursor.execute("""
                SELECT question_number, question_text 
                FROM questions 
                WHERE assignment_id = ? 
                ORDER BY question_number
            """, (assignment_id,))
            questions = [
                {
                    'question_number': row['question_number'],
                    'question_text': row['question_text']
                }
                for row in cursor.fetchall()
            ]
            
            # Get rubric
            cursor.execute("""
                SELECT criteria, total_marks 
                FROM rubrics 
                WHERE assignment_id = ?
            """, (assignment_id,))
            rubric = [
                {
                    'CRITERIA': row['criteria'],
                    'TOTAL MARKS': row['total_marks']
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'title': assignment['title'],
                'questions': questions,
                'rubric': rubric,
                'max_marks_per_question': assignment['max_marks_per_question'],
                'total_marks': assignment['total_marks']
            }
    
    def get_all_assignments(self) -> List[Dict]:
        """
        Get list of all assignments.
        
        Returns:
            List[Dict]: List of assignment summaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, created_at, total_questions, total_marks, assignment_type
                FROM assignments 
                ORDER BY created_at DESC
            """)
            
            return [
                {
                    'id': row['id'],
                    'title': row['title'],
                    'created_at': row['created_at'],
                    'total_questions': row['total_questions'],
                    'total_marks': row['total_marks'],
                    'assignment_type': row['assignment_type']
                }
                for row in cursor.fetchall()
            ]
    
    def delete_assignment(self, assignment_id: int) -> bool:
        """
        Delete assignment and all related data.
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            bool: Success status
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
            return cursor.rowcount > 0
    
    def rename_assignment(self, assignment_id: int, new_title: str) -> bool:
        """
        Rename an assignment.
        
        Args:
            assignment_id: Assignment ID
            new_title: New title for the assignment
            
        Returns:
            bool: Success status
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE assignments SET title = ? WHERE id = ?",
                (new_title, assignment_id)
            )
            return cursor.rowcount > 0
    
    def delete_all_assignments(self) -> int:
        """
        Delete all assignments and related data.
        
        Returns:
            int: Number of assignments deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM assignments")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM assignments")
            return count
    
    # ===== EVALUATION OPERATIONS =====
    
    def save_evaluation(self, assignment_id: int, evaluation_data: Dict, student_name: str = "Anonymous") -> int:
        """
        Save evaluation result to database.
        
        Args:
            assignment_id: Assignment ID
            evaluation_data: Evaluation results with scores, feedback, etc.
            student_name: Student name (optional)
            
        Returns:
            int: Evaluation ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO evaluations 
                (assignment_id, student_name, total_score, max_score, percentage, evaluation_mode, results_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                assignment_id,
                student_name,
                evaluation_data.get('total_score', 0),
                evaluation_data.get('total_max', 0),
                evaluation_data.get('percentage', 0),
                evaluation_data.get('mode', 'moderate'),
                json.dumps(evaluation_data)
            ))
            
            return cursor.lastrowid
    
    def get_evaluations_by_assignment(self, assignment_id: int) -> List[Dict]:
        """
        Get all evaluations for an assignment.
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            List[Dict]: List of evaluations
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM evaluations 
                WHERE assignment_id = ? 
                ORDER BY evaluated_at DESC
            """, (assignment_id,))
            
            return [
                {
                    'id': row['id'],
                    'student_name': row['student_name'],
                    'evaluated_at': row['evaluated_at'],
                    'total_score': row['total_score'],
                    'max_score': row['max_score'],
                    'percentage': row['percentage'],
                    'evaluation_mode': row['evaluation_mode'],
                    'results_json': json.loads(row['results_json'])
                }
                for row in cursor.fetchall()
            ]
    
    def search_evaluations_by_student(self, assignment_id: int, student_name: str) -> List[Dict]:
        """
        Search evaluations by student name within an assignment.
        
        Args:
            assignment_id: Assignment ID
            student_name: Student name to search for (partial match)
            
        Returns:
            List[Dict]: Matching evaluations
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM evaluations 
                WHERE assignment_id = ? AND student_name LIKE ?
                ORDER BY evaluated_at DESC
            """, (assignment_id, f"%{student_name}%"))
            
            return [
                {
                    'id': row['id'],
                    'student_name': row['student_name'],
                    'evaluated_at': row['evaluated_at'],
                    'total_score': row['total_score'],
                    'max_score': row['max_score'],
                    'percentage': row['percentage'],
                    'evaluation_mode': row['evaluation_mode'],
                    'results_json': json.loads(row['results_json'])
                }
                for row in cursor.fetchall()
            ]
    
    def get_recent_evaluations(self, limit: int = 10) -> List[Dict]:
        """
        Get recent evaluations across all assignments.
        
        Args:
            limit: Maximum number of evaluations to return
            
        Returns:
            List[Dict]: List of recent evaluations with assignment info
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, a.title as assignment_title
                FROM evaluations e
                JOIN assignments a ON e.assignment_id = a.id
                ORDER BY e.evaluated_at DESC
                LIMIT ?
            """, (limit,))
            
            return [
                {
                    'id': row['id'],
                    'assignment_id': row['assignment_id'],
                    'assignment_title': row['assignment_title'],
                    'student_name': row['student_name'],
                    'evaluated_at': row['evaluated_at'],
                    'total_score': row['total_score'],
                    'max_score': row['max_score'],
                    'percentage': row['percentage'],
                    'evaluation_mode': row['evaluation_mode']
                }
                for row in cursor.fetchall()
            ]
    
    def delete_evaluation(self, evaluation_id: int) -> bool:
        """Delete an evaluation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM evaluations WHERE id = ?", (evaluation_id,))
            return cursor.rowcount > 0
    
    def update_evaluation_student_name(self, evaluation_id: int, new_name: str) -> bool:
        """
        Update student name for an evaluation.
        
        Args:
            evaluation_id: Evaluation ID
            new_name: New student name
            
        Returns:
            bool: Success status
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE evaluations SET student_name = ? WHERE id = ?",
                (new_name, evaluation_id)
            )
            return cursor.rowcount > 0
    
    def delete_all_evaluations(self, assignment_id: Optional[int] = None) -> int:
        """
        Delete all evaluations (optionally for specific assignment).
        
        Args:
            assignment_id: Optional assignment ID to filter by
            
        Returns:
            int: Number of evaluations deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if assignment_id:
                cursor.execute("SELECT COUNT(*) FROM evaluations WHERE assignment_id = ?", (assignment_id,))
                count = cursor.fetchone()[0]
                cursor.execute("DELETE FROM evaluations WHERE assignment_id = ?", (assignment_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM evaluations")
                count = cursor.fetchone()[0]
                cursor.execute("DELETE FROM evaluations")
            
            return count
    
    # ===== EXPORT OPERATIONS =====
    
    def export_evaluations_to_csv(self, assignment_id: Optional[int] = None) -> pd.DataFrame:
        """
        Export evaluations to DataFrame for CSV export.
        
        Args:
            assignment_id: Optional assignment ID to filter by
            
        Returns:
            pd.DataFrame: Evaluations data
        """
        with self.get_connection() as conn:
            if assignment_id:
                query = """
                    SELECT e.*, a.title as assignment_title
                    FROM evaluations e
                    JOIN assignments a ON e.assignment_id = a.id
                    WHERE e.assignment_id = ?
                    ORDER BY e.evaluated_at DESC
                """
                df = pd.read_sql_query(query, conn, params=(assignment_id,))
            else:
                query = """
                    SELECT e.*, a.title as assignment_title
                    FROM evaluations e
                    JOIN assignments a ON e.assignment_id = a.id
                    ORDER BY e.evaluated_at DESC
                """
                df = pd.read_sql_query(query, conn)
            
            return df
    
    def export_assignment_to_json(self, assignment_id: int) -> Optional[str]:
        """
        Export assignment to JSON string.
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            str: JSON string of assignment data
        """
        assignment_data = self.load_assignment(assignment_id)
        if assignment_data:
            return json.dumps(assignment_data, indent=2)
        return None
    
    def import_assignment_from_json(self, json_str: str) -> int:
        """
        Import assignment from JSON string.
        
        Args:
            json_str: JSON string with assignment data
            
        Returns:
            int: New assignment ID
        """
        assignment_data = json.loads(json_str)
        return self.save_assignment(assignment_data)
    
    def import_assignment_from_csv(self, csv_content: str, title: str = "Imported Assignment") -> dict:
        """
        Import assignment from CSV format with optional student answers.
        
        CSV Format Expected:
        Row 1: CRITERIA,TOTAL MARKS
        Rows 2+: Criterion name, marks
        Row with "QUESTIONS,"
        Rows: question_number,question_text
        Row with "STUDENTS," (optional)
        Rows: student_name,answer1,answer2,... (optional)
        
        Args:
            csv_content: CSV file content as string
            title: Assignment title
            
        Returns:
            dict: {'assignment_id': int, 'students': list of dicts with student answers}
        """
        import csv
        from io import StringIO
        
        reader = csv.reader(StringIO(csv_content))
        rows = list(reader)
        
        if len(rows) < 2:
            raise ValueError("CSV must have at least 2 rows (header + data)")
        
        rubric = []
        questions = []
        students = []  # Store student answers separately
        
        section = "rubric"  # rubric, questions, or students
        
        for i, row in enumerate(rows):
            if len(row) == 0 or all(cell.strip() == '' for cell in row):
                continue
            
            first_cell = row[0].strip().upper()
            
            # Detect section transitions
            if first_cell in ['QUESTIONS', 'QUESTION']:
                section = "questions"
                continue
            elif first_cell in ['STUDENTS', 'STUDENT', 'ANSWERS']:
                section = "students"
                continue
            
            # Skip header rows
            if i == 0 and ('CRITERIA' in first_cell or 'CRITERION' in first_cell):
                continue
            
            # Process based on current section
            if section == "rubric":
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    try:
                        rubric.append({
                            'CRITERIA': row[0].strip(),
                            'TOTAL MARKS': int(row[1].strip())
                        })
                    except ValueError:
                        continue
            
            elif section == "questions":
                if len(row) >= 2 and row[1].strip():
                    questions.append({
                        'question_number': len(questions) + 1,
                        'question_text': row[1].strip()
                    })
            
            elif section == "students":
                if len(row) >= 2 and row[0].strip():
                    student_name = row[0].strip()
                    # Remaining columns are answers to questions
                    answers = {}
                    for idx, answer in enumerate(row[1:], 1):
                        if idx <= len(questions):  # Only store answers for existing questions
                            answers[idx] = answer.strip() if answer else ""
                    
                    if answers:
                        students.append({
                            'student_name': student_name,
                            'answers': answers  # Dict: {question_number: answer}
                        })
        
        # Validation
        if not rubric:
            # Use default rubric
            rubric = [
                {'CRITERIA': 'Correctness', 'TOTAL MARKS': 5},
                {'CRITERIA': 'Explanation', 'TOTAL MARKS': 3},
                {'CRITERIA': 'Clarity', 'TOTAL MARKS': 2}
            ]
        
        if not questions:
            raise ValueError("No questions found in CSV")
        
        # Calculate marks
        max_marks_per_question = sum(r['TOTAL MARKS'] for r in rubric)
        
        # Create assignment data (without students)
        assignment_data = {
            'title': title,
            'questions': questions,
            'rubric': rubric,
            'max_marks_per_question': max_marks_per_question,
            'total_marks': max_marks_per_question * len(questions)
        }
        
        # Save assignment
        assignment_id = self.save_assignment(assignment_data)
        
        # Return both assignment ID and student answers
        return {
            'assignment_id': assignment_id,
            'students': students,
            'questions_count': len(questions)
        }
        """
        Import assignment from CSV format with optional student answers.
        
        CSV Format Expected:
        Row 1: CRITERIA,TOTAL MARKS
        Rows 2+: Criterion name, marks
        Row with "QUESTIONS,"
        Rows: question_number,question_text
        Row with "STUDENTS," (optional)
        Rows: student_name,answer1,answer2,... (optional)
        
        Args:
            csv_content: CSV file content as string
            title: Assignment title
            
        Returns:
            int: New assignment ID
        """
        import csv
        from io import StringIO
        
        reader = csv.reader(StringIO(csv_content))
        rows = list(reader)
        
        if len(rows) < 2:
            raise ValueError("CSV must have at least 2 rows (header + data)")
        
        rubric = []
        questions = []
        students = []  # New: store student answers
        
        section = "rubric"  # rubric, questions, or students
        
        for i, row in enumerate(rows):
            if len(row) == 0 or all(cell.strip() == '' for cell in row):
                continue
            
            first_cell = row[0].strip().upper()
            
            # Detect section transitions
            if first_cell in ['QUESTIONS', 'QUESTION']:
                section = "questions"
                continue
            elif first_cell in ['STUDENTS', 'STUDENT', 'ANSWERS']:
                section = "students"
                continue
            
            # Skip header rows
            if i == 0 and ('CRITERIA' in first_cell or 'CRITERION' in first_cell):
                continue
            
            # Process based on current section
            if section == "rubric":
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    try:
                        rubric.append({
                            'CRITERIA': row[0].strip(),
                            'TOTAL MARKS': int(row[1].strip())
                        })
                    except ValueError:
                        continue
            
            elif section == "questions":
                if len(row) >= 2 and row[1].strip():
                    questions.append({
                        'question_number': len(questions) + 1,
                        'question_text': row[1].strip()
                    })
            
            elif section == "students":
                if len(row) >= 2 and row[0].strip():
                    # First column is student name
                    student_name = row[0].strip()
                    # Remaining columns are answers to questions
                    answers = [cell.strip() for cell in row[1:] if cell.strip()]
                    
                    if answers:  # Only add if there are answers
                        students.append({
                            'student_name': student_name,
                            'answers': answers
                        })
        
        # Validation
        if not rubric:
            # Use default rubric
            rubric = [
                {'CRITERIA': 'Correctness', 'TOTAL MARKS': 5},
                {'CRITERIA': 'Explanation', 'TOTAL MARKS': 3},
                {'CRITERIA': 'Clarity', 'TOTAL MARKS': 2}
            ]
        
        if not questions:
            raise ValueError("No questions found in CSV")
        
        # Calculate marks
        max_marks_per_question = sum(r['TOTAL MARKS'] for r in rubric)
        
        # Create assignment data
        assignment_data = {
            'title': title,
            'questions': questions,
            'rubric': rubric,
            'max_marks_per_question': max_marks_per_question,
            'total_marks': max_marks_per_question * len(questions),
            'students': students  # Include student answers
        }
        
        return self.save_assignment(assignment_data)
        """
        Import assignment from CSV format.
        
        CSV Format Expected:
        Row 1: Rubric criteria (CRITERIA,TOTAL MARKS)
        Rows 2+: Question Number, Question Text
        
        Alternative Format:
        question_number,question_text,criterion_1,criterion_2,...
        
        Args:
            csv_content: CSV file content as string
            title: Assignment title
            
        Returns:
            int: New assignment ID
        """
        import csv
        from io import StringIO
        
        reader = csv.reader(StringIO(csv_content))
        rows = list(reader)
        
        if len(rows) < 2:
            raise ValueError("CSV must have at least 2 rows (header + data)")
        
        # Detect format based on first row
        header = rows[0]
        
        # Format 1: Simple format with questions only
        # question_number,question_text
        if len(header) == 2 and 'question' in header[0].lower():
            questions = []
            for row in rows[1:]:
                if len(row) >= 2 and row[1].strip():
                    questions.append({
                        'question_number': len(questions) + 1,
                        'question_text': row[1].strip()
                    })
            
            # Default rubric for simple format
            rubric = [
                {'CRITERIA': 'Correctness', 'TOTAL MARKS': 5},
                {'CRITERIA': 'Explanation', 'TOTAL MARKS': 3},
                {'CRITERIA': 'Clarity', 'TOTAL MARKS': 2}
            ]
            
        # Format 2: Full format with rubric
        # CRITERIA,TOTAL MARKS (first row is rubric header)
        elif 'CRITERIA' in header[0] or 'criteria' in header[0].lower():
            # First section: Rubric
            rubric = []
            questions = []
            in_questions = False
            
            for i, row in enumerate(rows[1:], 1):
                if len(row) < 2:
                    continue
                    
                # Check if this is start of questions section
                if row[0].lower().strip() in ['questions', 'question', 'q']:
                    in_questions = True
                    continue
                
                if not in_questions:
                    # Still in rubric section
                    if row[0].strip() and row[1].strip():
                        rubric.append({
                            'CRITERIA': row[0].strip(),
                            'TOTAL MARKS': int(row[1].strip())
                        })
                else:
                    # In questions section
                    if row[1].strip():  # Has question text
                        questions.append({
                            'question_number': len(questions) + 1,
                            'question_text': row[1].strip()
                        })
        else:
            raise ValueError("Unrecognized CSV format. Please use standard format.")
        
        if not questions:
            raise ValueError("No questions found in CSV")
        
        if not rubric:
            raise ValueError("No rubric found in CSV")
        
        # Calculate marks
        max_marks_per_question = sum(r['TOTAL MARKS'] for r in rubric)
        
        # Create assignment data
        assignment_data = {
            'title': title,
            'questions': questions,
            'rubric': rubric,
            'max_marks_per_question': max_marks_per_question,
            'total_marks': max_marks_per_question * len(questions)
        }
        
        return self.save_assignment(assignment_data)
    
    
    # ===== STATISTICS =====
    
    def get_assignment_statistics(self, assignment_id: int) -> Dict:
        """
        Get statistics for an assignment's evaluations.
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            Dict: Statistics including avg, min, max scores
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_evaluations,
                    AVG(percentage) as avg_percentage,
                    MIN(percentage) as min_percentage,
                    MAX(percentage) as max_percentage,
                    AVG(total_score) as avg_score
                FROM evaluations
                WHERE assignment_id = ?
            """, (assignment_id,))
            
            row = cursor.fetchone()
            if row and row['total_evaluations'] > 0:
                return {
                    'total_evaluations': row['total_evaluations'],
                    'avg_percentage': round(row['avg_percentage'], 2),
                    'min_percentage': round(row['min_percentage'], 2),
                    'max_percentage': round(row['max_percentage'], 2),
                    'avg_score': round(row['avg_score'], 2)
                }
            return {
                'total_evaluations': 0,
                'avg_percentage': 0,
                'min_percentage': 0,
                'max_percentage': 0,
                'avg_score': 0
            }
