"""
evaluator.py
Handles all LLM interaction logic for rubric-based evaluation.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()


class RubricEvaluator:
    """
    Handles communication with Groq LLM for rubric-based evaluation.
    """
    
    def __init__(self):
        """Initialize Groq client."""
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama-3.3-70b-versatile"
        self.mode = "moderate"  # Default mode
        self.temperature = 0.2  # Default temperature
    
    def set_mode(self, mode: str):
        """
        Set evaluation mode (strict, moderate, or lenient).
        
        Args:
            mode: Evaluation mode ('strict', 'moderate', or 'lenient')
        """
        mode = mode.lower()
        
        # Map modes to temperature values
        mode_settings = {
            "strict": 0.05,     # Very low temperature = very conservative/strict
            "moderate": 0.3,    # Balanced approach
            "lenient": 0.6      # Higher temperature = more generous/creative
        }
        
        if mode in mode_settings:
            self.mode = mode
            self.temperature = mode_settings[mode]
        else:
            # Default to moderate if invalid mode
            self.mode = "moderate"
            self.temperature = 0.3
    
    def get_mode_instructions(self) -> str:
        """
        Get mode-specific instructions for the LLM.
        
        Returns:
            str: Instructions based on current evaluation mode
        """
        instructions = {
            "strict": """
EVALUATION MODE: STRICT - YOU MUST BE HIGHLY CRITICAL

STRICT GRADING RULES (FOLLOW EXACTLY):
1. Award MAXIMUM points ONLY for perfect, comprehensive answers
2. Deduct points heavily for ANY missing details or minor errors
3. Partial answers get AT MOST 50% of maximum points
4. If anything is unclear or ambiguous, assume it's wrong
5. Look for reasons to deduct points, not reasons to award them
6. Standard for "excellent" is exceptionally high
7. Average understanding should receive 40-60% of points
8. Be harsh and unforgiving in your evaluation

REASONING REQUIREMENTS:
- Clearly identify EVERY gap, omission, or weakness
- Explain specifically what is missing and why it's important
- Reference exact parts of the answer that are insufficient
- Compare to what a perfect answer would include
- Be detailed and specific in your criticism

MINDSET: "What's wrong with this answer? What's missing?"
""",
            "moderate": """
EVALUATION MODE: MODERATE - BALANCED AND FAIR

MODERATE GRADING RULES (FOLLOW EXACTLY):
1. Award points when criteria are reasonably demonstrated
2. Give proportional partial credit based on understanding shown
3. Minor errors should reduce score by 10-20%
4. Major errors or missing key points reduce score by 30-50%
5. Balance between recognizing effort and maintaining standards
6. Average understanding should receive 60-75% of points
7. Be fair - neither overly harsh nor overly generous

REASONING REQUIREMENTS:
- Acknowledge what the student did well (with specifics)
- Identify areas needing improvement (with specifics)
- Explain the reasoning behind the score awarded
- Provide balanced, constructive feedback
- Reference specific parts of the answer as evidence
- Suggest concrete ways to improve

MINDSET: "Does this answer demonstrate reasonable understanding?"
""",
            "lenient": """
EVALUATION MODE: LENIENT - GENEROUS AND ENCOURAGING

LENIENT GRADING RULES (FOLLOW EXACTLY):
1. Award points for any evidence of understanding or effort
2. Give generous partial credit even for incomplete answers
3. Focus on what the student got RIGHT, not what's wrong
4. Minor errors should have minimal impact (5-10% deduction max)
5. Even basic understanding should receive 60-70% of points
6. Average understanding should receive 75-85% of points
7. Be encouraging and look for reasons to award points
8. Give benefit of the doubt when answer is unclear

REASONING REQUIREMENTS:
- Highlight strengths and positive aspects first
- Frame weaknesses as "opportunities for growth"
- Acknowledge effort and partial understanding
- Provide encouraging, supportive feedback
- Reference specific good points from the answer
- Suggest improvements gently

MINDSET: "What did the student understand? How can I reward their effort?"
"""
        }
        
        return instructions.get(self.mode, instructions["moderate"])
    
    def evaluate(self, prompt: str) -> str:
        """
        Send evaluation prompt to LLM and return JSON response.
        
        Args:
            prompt: The formatted evaluation prompt
            
        Returns:
            str: JSON response from the model
        """
        structured_prompt = self._wrap_prompt(prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": structured_prompt}
                ],
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f'{{"error": "API Error: {str(e)}"}}'
    
    def _wrap_prompt(self, prompt: str) -> str:
        """
        Wrap the evaluation prompt with strict JSON instructions and mode settings.
        
        Args:
            prompt: The base evaluation prompt
            
        Returns:
            str: Wrapped prompt with JSON formatting instructions and mode
        """
        mode_instructions = self.get_mode_instructions()
        
        mode_emphasis = {
            "strict": "REMEMBER: You are in STRICT mode. Be HARSH and CRITICAL. Deduct points aggressively.",
            "moderate": "REMEMBER: You are in MODERATE mode. Be FAIR and BALANCED in your scoring.",
            "lenient": "REMEMBER: You are in LENIENT mode. Be GENEROUS and ENCOURAGING. Award points liberally."
        }
        
        return f"""
You are an academic evaluator.
Evaluate the student's answer based on the rubric.

{mode_instructions}

{mode_emphasis.get(self.mode, "")}

IMPORTANT JSON FORMAT:
- Return ONLY valid JSON.
- Do NOT return explanation text outside JSON.
- Do NOT use markdown.
- Do NOT use backticks.
- Apply the {self.mode.upper()} evaluation mode consistently across ALL criteria.

Now evaluate:

{prompt}
"""
