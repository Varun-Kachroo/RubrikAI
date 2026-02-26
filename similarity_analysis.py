"""
similarity_analysis.py - Answer Similarity, Performance Analytics, Confidence Scoring & AI Detection
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import re


class ConfidenceAnalyzer:
    """Analyzes grading confidence and flags uncertain evaluations"""
    
    def __init__(self):
        pass
    
    def calculate_confidence(self, evaluation_result):
        """
        Calculate confidence score for an evaluation
        
        Args:
            evaluation_result: Dict with evaluation data
        
        Returns:
            Dict with confidence score and reasoning
        """
        confidence_factors = []
        weights = []
        reasons = []
        
        # Factor 1: Answer length (longer = more confident)
        answer_length = evaluation_result.get('answer_length', 0)
        if answer_length > 200:
            confidence_factors.append(95)
            weights.append(0.15)
            reasons.append("Detailed answer provided")
        elif answer_length > 100:
            confidence_factors.append(85)
            weights.append(0.15)
            reasons.append("Adequate answer length")
        elif answer_length > 50:
            confidence_factors.append(70)
            weights.append(0.15)
            reasons.append("Brief answer")
        else:
            confidence_factors.append(50)
            weights.append(0.15)
            reasons.append("Very short answer - difficult to assess")
        
        # Factor 2: Rubric criteria coverage
        scores = evaluation_result.get('scores', [])
        if scores:
            awarded = [s.get('awarded', 0) for s in scores]
            max_scores = [s.get('max', 1) for s in scores]
            
            # Check if all criteria addressed
            percentages = [(a/m*100) if m > 0 else 0 for a, m in zip(awarded, max_scores)]
            
            if all(p > 0 for p in percentages):
                confidence_factors.append(90)
                weights.append(0.25)
                reasons.append("All rubric criteria addressed")
            elif any(p > 0 for p in percentages):
                confidence_factors.append(70)
                weights.append(0.25)
                reasons.append("Some criteria not fully addressed")
            else:
                confidence_factors.append(40)
                weights.append(0.25)
                reasons.append("Multiple criteria missing")
        
        # Factor 3: Score distribution (balanced scoring = more confident)
        if scores:
            percentages = [(s.get('awarded', 0)/s.get('max', 1)*100) if s.get('max', 0) > 0 else 0 
                          for s in scores]
            std_dev = np.std(percentages) if len(percentages) > 1 else 0
            
            if std_dev < 15:  # Consistent scoring
                confidence_factors.append(85)
                weights.append(0.20)
                reasons.append("Consistent performance across criteria")
            elif std_dev < 30:
                confidence_factors.append(75)
                weights.append(0.20)
                reasons.append("Some variation in criterion scores")
            else:
                confidence_factors.append(60)
                weights.append(0.20)
                reasons.append("High variation - some criteria much stronger")
        
        # Factor 4: Clarity of reasoning
        feedback = evaluation_result.get('feedback', [])
        has_clear_feedback = len(feedback) >= 2 and all(len(f) > 20 for f in feedback)
        
        if has_clear_feedback:
            confidence_factors.append(90)
            weights.append(0.20)
            reasons.append("Clear reasoning provided")
        else:
            confidence_factors.append(70)
            weights.append(0.20)
            reasons.append("Limited feedback detail")
        
        # Factor 5: Edge case detection
        total_score = evaluation_result.get('total_score', 0)
        max_score = sum(s.get('max', 0) for s in scores)
        
        if max_score > 0:
            percentage = (total_score / max_score) * 100
            
            # Very high or very low scores are clear
            if percentage >= 90 or percentage <= 20:
                confidence_factors.append(95)
                weights.append(0.20)
                reasons.append("Clear-cut performance level")
            elif 40 <= percentage <= 70:
                # Middle range is harder to evaluate
                confidence_factors.append(70)
                weights.append(0.20)
                reasons.append("Borderline performance - recommend review")
            else:
                confidence_factors.append(85)
                weights.append(0.20)
        
        # Calculate weighted average
        if confidence_factors and weights:
            # Normalize weights
            total_weight = sum(weights)
            normalized_weights = [w/total_weight for w in weights]
            
            confidence_score = sum(c * w for c, w in zip(confidence_factors, normalized_weights))
            confidence_score = round(confidence_score, 1)
        else:
            confidence_score = 75.0
            reasons = ["Standard confidence level"]
        
        # Determine confidence level
        if confidence_score >= 90:
            level = "Very High"
            recommendation = "Trust this grade"
            color = "#44ff88"  # Green
        elif confidence_score >= 75:
            level = "High"
            recommendation = "Grade is reliable"
            color = "#88ff44"  # Light green
        elif confidence_score >= 60:
            level = "Moderate"
            recommendation = "Consider quick review"
            color = "#ffbb44"  # Yellow
        else:
            level = "Low"
            recommendation = "Manual review recommended"
            color = "#ff8844"  # Orange
        
        return {
            'confidence_score': confidence_score,
            'confidence_level': level,
            'recommendation': recommendation,
            'color': color,
            'reasons': reasons,
            'needs_review': confidence_score < 70
        }


class AIWritingDetector:
    """Detects AI-generated answers (ChatGPT, Claude, etc.)"""
    
    def __init__(self):
        self.ai_indicators = {
            # Common AI phrases
            'formal_transitions': ['furthermore', 'moreover', 'consequently', 'nevertheless', 'thus', 'hence', 'therefore'],
            'ai_patterns': ['it is important to note', 'in conclusion', 'to summarize', 'in summary', 'as mentioned', 'as previously stated'],
            'hedging': ['arguably', 'potentially', 'presumably', 'seemingly', 'apparently'],
            'perfect_structure': ['firstly', 'secondly', 'thirdly', 'finally', 'in conclusion']
        }
    
    def analyze_answer(self, answer, student_baseline=None):
        """
        Analyze if answer is likely AI-generated
        
        Args:
            answer: Text to analyze
            student_baseline: Optional dict with student's writing profile
        
        Returns:
            Dict with detection results
        """
        if not answer or len(answer.strip()) < 50:
            return {
                'is_ai_likely': False,
                'confidence': 0,
                'reason': 'Answer too short to analyze',
                'indicators': []
            }
        
        indicators = []
        score = 0
        
        # Analyze text characteristics
        text_stats = self._analyze_text_characteristics(answer)
        
        # Check 1: Excessive formal transitions
        formal_count = sum(1 for phrase in self.ai_indicators['formal_transitions'] 
                          if phrase in answer.lower())
        if formal_count >= 3:
            score += 25
            indicators.append(f"Excessive formal transitions ({formal_count} found)")
        
        # Check 2: AI-specific patterns
        pattern_count = sum(1 for phrase in self.ai_indicators['ai_patterns'] 
                           if phrase in answer.lower())
        if pattern_count >= 2:
            score += 30
            indicators.append(f"AI-typical phrases detected ({pattern_count} found)")
        
        # Check 3: Perfect grammar (no contractions, typos)
        has_contractions = any(word in answer for word in ["don't", "can't", "won't", "it's", "that's"])
        has_informal = any(word in answer.lower() for word in ["gonna", "wanna", "gotta", "yeah", "ok", "like,"])
        
        if not has_contractions and not has_informal and len(answer) > 100:
            score += 20
            indicators.append("Unusually perfect grammar - no contractions or informal language")
        
        # Check 4: Sentence length consistency (AI tends to be very consistent)
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        if len(sentences) >= 3:
            lengths = [len(s.split()) for s in sentences]
            std_dev = np.std(lengths)
            
            if std_dev < 3:  # Very consistent length
                score += 15
                indicators.append("Extremely consistent sentence lengths")
        
        # Check 5: Over-structured (intro-body-conclusion in short answer)
        has_structure = any(phrase in answer.lower() 
                           for phrase in self.ai_indicators['perfect_structure'])
        if has_structure and len(answer) < 300:
            score += 20
            indicators.append("Over-structured for answer length")
        
        # Check 6: Compare with student baseline if available
        if student_baseline:
            baseline_comparison = self._compare_with_baseline(text_stats, student_baseline)
            if baseline_comparison['is_anomaly']:
                score += 30
                indicators.extend(baseline_comparison['differences'])
        
        # Check 7: Vocabulary sophistication
        words = answer.split()
        long_words = [w for w in words if len(w) > 10]
        if len(long_words) / len(words) > 0.15:  # More than 15% long words
            score += 15
            indicators.append(f"Unusually sophisticated vocabulary ({len(long_words)} complex words)")
        
        # Determine if AI-likely
        is_ai_likely = score >= 60
        
        if is_ai_likely:
            confidence = min(score, 95)
            level = "High" if score >= 75 else "Moderate"
        else:
            confidence = score
            level = "Low"
        
        return {
            'is_ai_likely': is_ai_likely,
            'confidence': confidence,
            'confidence_level': level,
            'total_score': score,
            'indicators': indicators,
            'text_stats': text_stats,
            'recommendation': self._get_recommendation(score)
        }
    
    def _analyze_text_characteristics(self, text):
        """Extract text statistics"""
        words = text.split()
        sentences = [s for s in text.split('.') if s.strip()]
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'has_contractions': any("'" in w for w in words),
            'has_questions': '?' in text,
            'has_exclamations': '!' in text
        }
    
    def _compare_with_baseline(self, current_stats, baseline):
        """Compare current answer with student's baseline"""
        differences = []
        is_anomaly = False
        
        # Compare sentence length
        if abs(current_stats['avg_sentence_length'] - baseline.get('avg_sentence_length', 0)) > 10:
            differences.append(f"Sentence length changed significantly")
            is_anomaly = True
        
        # Compare word length
        if abs(current_stats['avg_word_length'] - baseline.get('avg_word_length', 0)) > 2:
            differences.append("Vocabulary complexity differs from student's typical style")
            is_anomaly = True
        
        return {
            'is_anomaly': is_anomaly,
            'differences': differences
        }
    
    def _get_recommendation(self, score):
        """Get recommendation based on score"""
        if score >= 75:
            return "High likelihood of AI use - Review manually and discuss with student"
        elif score >= 60:
            return "Possible AI use - Consider reviewing"
        elif score >= 40:
            return "Some AI indicators - Monitor"
        else:
            return "Appears to be student's own work"
    
    def create_student_baseline(self, previous_answers):
        """
        Create writing profile for a student
        
        Args:
            previous_answers: List of student's previous answers
        
        Returns:
            Dict with baseline writing characteristics
        """
        if not previous_answers or len(previous_answers) < 2:
            return None
        
        all_stats = [self._analyze_text_characteristics(ans) for ans in previous_answers]
        
        return {
            'avg_sentence_length': np.mean([s['avg_sentence_length'] for s in all_stats]),
            'avg_word_length': np.mean([s['avg_word_length'] for s in all_stats]),
            'typically_uses_contractions': sum(s['has_contractions'] for s in all_stats) / len(all_stats) > 0.5,
            'sample_size': len(previous_answers)
        }


class SimilarityAnalyzer:
    """Analyzes answer similarity to detect potential plagiarism"""
    
    def __init__(self):
        # Use multiple vectorizers for better detection
        self.vectorizer_word = TfidfVectorizer(
            lowercase=True,
            strip_accents='unicode',
            ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
            min_df=1,
            max_df=0.95
        )
        
        self.vectorizer_char = TfidfVectorizer(
            lowercase=True,
            analyzer='char',
            ngram_range=(3, 5),  # Character-level n-grams
            min_df=1
        )
    
    def calculate_similarity_matrix(self, students_answers):
        """
        Calculate similarity matrix for all students with enhanced detection
        
        Args:
            students_answers: List of dicts with {'student_name': str, 'answers': dict}
        
        Returns:
            DataFrame with similarity scores
        """
        if len(students_answers) < 2:
            return None
        
        # Combine all answers for each student into single text
        student_names = []
        combined_answers = []
        
        for student in students_answers:
            student_names.append(student['student_name'])
            # Combine all answers into one text
            answers_list = [str(ans).strip() for ans in student['answers'].values() if ans]
            combined_text = " ".join(answers_list)
            combined_answers.append(combined_text)
        
        # Calculate similarity using multiple methods and take the maximum
        try:
            # Method 1: Word-level TF-IDF
            tfidf_word = self.vectorizer_word.fit_transform(combined_answers)
            similarity_word = cosine_similarity(tfidf_word)
            
            # Method 2: Character-level TF-IDF (catches paraphrasing)
            tfidf_char = self.vectorizer_char.fit_transform(combined_answers)
            similarity_char = cosine_similarity(tfidf_char)
            
            # Method 3: Simple word overlap (catches direct copying)
            similarity_overlap = np.zeros((len(combined_answers), len(combined_answers)))
            for i in range(len(combined_answers)):
                for j in range(len(combined_answers)):
                    if i != j:
                        words_i = set(combined_answers[i].lower().split())
                        words_j = set(combined_answers[j].lower().split())
                        # Remove common words
                        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'}
                        words_i = words_i - common_words
                        words_j = words_j - common_words
                        
                        if len(words_i) > 0 and len(words_j) > 0:
                            overlap = len(words_i & words_j) / min(len(words_i), len(words_j))
                            similarity_overlap[i][j] = overlap
            
            # Combine methods: take weighted average with emphasis on higher scores
            # This makes the detector more sensitive to copying
            similarity_matrix = (
                similarity_word * 0.4 +      # Word-level semantic similarity
                similarity_char * 0.3 +      # Character-level (catches paraphrasing)
                similarity_overlap * 0.3     # Direct word overlap (catches copying)
            )
            
            # Apply amplification to make differences more visible
            # Scores below 0.3 stay low, scores above 0.5 get boosted
            for i in range(len(similarity_matrix)):
                for j in range(len(similarity_matrix)):
                    score = similarity_matrix[i][j]
                    if i != j:  # Don't modify diagonal
                        if score > 0.5:
                            # Amplify high similarities
                            similarity_matrix[i][j] = min(0.95, score * 1.3)
                        elif score > 0.3:
                            # Moderate amplification
                            similarity_matrix[i][j] = score * 1.1
            
            # Create DataFrame
            df = pd.DataFrame(
                similarity_matrix,
                index=student_names,
                columns=student_names
            )
            
            # Convert to percentages
            df = df * 100
            
            # Ensure diagonal is 100%
            for name in student_names:
                df.loc[name, name] = 100.0
            
            return df
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_suspicious_pairs(self, similarity_df, threshold=70):
        """
        Get pairs of students with high similarity
        
        Args:
            similarity_df: Similarity matrix DataFrame
            threshold: Minimum similarity percentage to flag
        
        Returns:
            List of tuples (student1, student2, similarity)
        """
        if similarity_df is None:
            return []
        
        suspicious = []
        
        # Iterate through upper triangle (avoid duplicates)
        for i in range(len(similarity_df.index)):
            for j in range(i + 1, len(similarity_df.columns)):
                similarity = similarity_df.iloc[i, j]
                if similarity >= threshold:
                    suspicious.append((
                        similarity_df.index[i],
                        similarity_df.columns[j],
                        round(similarity, 1)
                    ))
        
        # Sort by similarity (highest first)
        suspicious.sort(key=lambda x: x[2], reverse=True)
        
        return suspicious
    
    def calculate_question_similarity_matrix(self, students_answers, question_number):
        """
        Calculate similarity for a specific question
        
        Args:
            students_answers: List of dicts with student data
            question_number: Which question to analyze
            
        Returns:
            DataFrame with similarity scores for that question
        """
        if len(students_answers) < 2:
            return None
        
        student_names = []
        question_answers = []
        
        for student in students_answers:
            student_names.append(student['student_name'])
            answer = student['answers'].get(question_number, '')
            question_answers.append(str(answer).strip())
        
        # Check if we have valid answers
        if not any(len(ans) > 10 for ans in question_answers):
            return None
        
        try:
            # Word-level similarity
            vectorizer = TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 3),
                min_df=1
            )
            tfidf = vectorizer.fit_transform(question_answers)
            similarity = cosine_similarity(tfidf)
            
            # Create DataFrame
            df = pd.DataFrame(
                similarity * 100,
                index=student_names,
                columns=student_names
            )
            
            # Ensure diagonal is 100%
            for name in student_names:
                df.loc[name, name] = 100.0
            
            return df
            
        except Exception as e:
            print(f"Error in question similarity: {e}")
            return None
    
    def compare_answers_detailed(self, answer1, answer2):
        """
        Detailed comparison of two answers
        
        Returns:
            Dict with similarity score and matching phrases
        """
        if not answer1 or not answer2:
            return {'similarity': 0, 'matches': []}
        
        try:
            # Calculate similarity
            tfidf = self.vectorizer.fit_transform([answer1, answer2])
            similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
            
            # Find common significant words (beyond stop words)
            words1 = set(answer1.lower().split())
            words2 = set(answer2.lower().split())
            
            # Filter out very short words
            words1 = {w for w in words1 if len(w) > 3}
            words2 = {w for w in words2 if len(w) > 3}
            
            common_words = words1 & words2
            
            return {
                'similarity': round(similarity, 1),
                'common_words': sorted(list(common_words))[:10],  # Top 10
                'unique_to_1': len(words1 - words2),
                'unique_to_2': len(words2 - words1)
            }
            
        except Exception as e:
            return {'similarity': 0, 'matches': [], 'error': str(e)}
    
    def get_color_for_similarity(self, similarity):
        """Get color code for similarity percentage"""
        if similarity >= 80:
            return "#ff4444"  # Red - very suspicious
        elif similarity >= 65:
            return "#ff8844"  # Orange - suspicious
        elif similarity >= 50:
            return "#ffbb44"  # Yellow - moderate
        else:
            return "#44ff88"  # Green - unique


class PerformanceAnalyzer:
    """Analyzes class performance and generates insights"""
    
    def __init__(self):
        pass
    
    def analyze_class_performance(self, evaluations):
        """
        Analyze overall class performance
        
        Args:
            evaluations: List of evaluation results
        
        Returns:
            Dict with analytics
        """
        if not evaluations:
            return None
        
        # Extract scores
        scores = [e['percentage'] for e in evaluations]
        total_scores = [e['total_score'] for e in evaluations]
        
        analytics = {
            'total_students': len(evaluations),
            'class_average': round(np.mean(scores), 1),
            'median': round(np.median(scores), 1),
            'std_dev': round(np.std(scores), 1),
            'min_score': round(min(scores), 1),
            'max_score': round(max(scores), 1),
            'passing_rate': round(len([s for s in scores if s >= 60]) / len(scores) * 100, 1)
        }
        
        # Performance distribution
        analytics['distribution'] = {
            'excellent': len([s for s in scores if s >= 90]),  # A
            'good': len([s for s in scores if 80 <= s < 90]),  # B
            'average': len([s for s in scores if 70 <= s < 80]),  # C
            'below_average': len([s for s in scores if 60 <= s < 70]),  # D
            'failing': len([s for s in scores if s < 60])  # F
        }
        
        return analytics
    
    def analyze_by_question(self, evaluations):
        """
        Analyze performance by question
        
        Returns:
            Dict with question-level analytics
        """
        if not evaluations:
            return None
        
        question_stats = {}
        
        for eval_data in evaluations:
            individual_results = eval_data.get('individual_results', [])
            
            for result in individual_results:
                if 'error' in result:
                    continue
                
                q_num = result.get('question_number')
                if not q_num:
                    continue
                
                if q_num not in question_stats:
                    question_stats[q_num] = {
                        'scores': [],
                        'max_score': 0
                    }
                
                score = result.get('total_score', 0)
                max_score = sum(s.get('max', 0) for s in result.get('scores', []))
                
                question_stats[q_num]['scores'].append(score)
                question_stats[q_num]['max_score'] = max_score
        
        # Calculate statistics
        analysis = {}
        for q_num, data in question_stats.items():
            if not data['scores']:
                continue
            
            scores = data['scores']
            max_score = data['max_score']
            
            percentages = [(s / max_score * 100) if max_score > 0 else 0 for s in scores]
            
            analysis[q_num] = {
                'average_score': round(np.mean(scores), 1),
                'average_percentage': round(np.mean(percentages), 1),
                'max_possible': max_score,
                'students_full_marks': len([s for s in scores if s == max_score]),
                'students_failed': len([p for p in percentages if p < 50]),
                'difficulty': self._calculate_difficulty(np.mean(percentages))
            }
        
        return analysis
    
    def analyze_by_criteria(self, evaluations):
        """
        Analyze performance by rubric criteria
        
        Returns:
            Dict with criteria-level analytics
        """
        if not evaluations:
            return None
        
        criteria_stats = {}
        
        for eval_data in evaluations:
            individual_results = eval_data.get('individual_results', [])
            
            for result in individual_results:
                if 'error' in result:
                    continue
                
                scores = result.get('scores', [])
                
                for score_item in scores:
                    criterion = score_item.get('criterion')
                    if not criterion:
                        continue
                    
                    if criterion not in criteria_stats:
                        criteria_stats[criterion] = {
                            'scores': [],
                            'max_scores': []
                        }
                    
                    criteria_stats[criterion]['scores'].append(score_item.get('awarded', 0))
                    criteria_stats[criterion]['max_scores'].append(score_item.get('max', 0))
        
        # Calculate statistics
        analysis = {}
        for criterion, data in criteria_stats.items():
            if not data['scores']:
                continue
            
            scores = data['scores']
            max_scores = data['max_scores']
            
            # Calculate percentages
            percentages = []
            for i, score in enumerate(scores):
                max_score = max_scores[i]
                if max_score > 0:
                    percentages.append(score / max_score * 100)
            
            if percentages:
                analysis[criterion] = {
                    'average_percentage': round(np.mean(percentages), 1),
                    'students_full_marks': len([p for p in percentages if p >= 99]),
                    'students_struggled': len([p for p in percentages if p < 50]),
                    'strength_level': self._get_strength_level(np.mean(percentages))
                }
        
        return analysis
    
    def identify_struggling_students(self, evaluations, threshold=60):
        """Identify students who need help"""
        struggling = []
        
        for eval_data in evaluations:
            if eval_data['percentage'] < threshold:
                struggling.append({
                    'name': eval_data.get('student_name', 'Unknown'),
                    'percentage': eval_data['percentage'],
                    'score': eval_data['total_score']
                })
        
        struggling.sort(key=lambda x: x['percentage'])
        return struggling
    
    def identify_top_performers(self, evaluations, threshold=85):
        """Identify top performing students"""
        top = []
        
        for eval_data in evaluations:
            if eval_data['percentage'] >= threshold:
                top.append({
                    'name': eval_data.get('student_name', 'Unknown'),
                    'percentage': eval_data['percentage'],
                    'score': eval_data['total_score']
                })
        
        top.sort(key=lambda x: x['percentage'], reverse=True)
        return top
    
    def _calculate_difficulty(self, avg_percentage):
        """Determine question difficulty"""
        if avg_percentage >= 80:
            return "Easy"
        elif avg_percentage >= 60:
            return "Moderate"
        elif avg_percentage >= 40:
            return "Hard"
        else:
            return "Very Hard"
    
    def _get_strength_level(self, avg_percentage):
        """Determine class strength in criteria"""
        if avg_percentage >= 80:
            return "Strong"
        elif avg_percentage >= 65:
            return "Good"
        elif avg_percentage >= 50:
            return "Adequate"
        else:
            return "Weak"