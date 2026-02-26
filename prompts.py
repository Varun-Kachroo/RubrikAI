"""
prompts.py
Prompt templates for rubric-based evaluation.
"""


def build_prompt(question: str, rubric: str, answer: str) -> str:
    """
    Builds structured evaluation prompt.
    
    Args:
        question: The question being answered
        rubric: The evaluation rubric (formatted)
        answer: The student's answer
        
    Returns:
        str: Complete evaluation prompt
    """
    return f"""
You are a strict academic evaluator with expertise in all subjects including mathematics.

🔴 CRITICAL RULES FOR MATHEMATICAL ACCURACY - READ CAREFULLY:
1. Mathematical calculations MUST be EXACTLY correct - ZERO tolerance for arithmetic errors
2. Examples of WRONG math that get ZERO points:
   - "3+4=8" is WRONG (correct: 7)
   - "5×6=31" is WRONG (correct: 30)  
   - "10-3=8" is WRONG (correct: 7)
   - "12÷4=4" is WRONG (correct: 3)
3. Do NOT award ANY points for incorrect calculations - even if off by 1
4. Do NOT give partial credit for wrong arithmetic - wrong = 0 points
5. VERIFY every calculation yourself BEFORE scoring
6. If the math is wrong, the entire answer is wrong - no exceptions
7. "Close enough" does NOT exist in mathematics - only correct or incorrect

For non-mathematical content, evaluate normally based on rubric criteria.

Question:
{question}

{rubric}

Student Answer:
{answer}

EVALUATION INSTRUCTIONS:
For each criterion, provide:
1. A thorough analysis of what the student demonstrated
2. Specific strengths with concrete examples from the answer
3. Specific weaknesses or gaps with concrete examples
4. Clear justification for the score awarded
5. Constructive feedback on how to improve

⚠️ MATHEMATICS CHECK: If this involves any calculations, verify EVERY number is correct!

Your reasoning should be:
- Professional and academic in tone
- Specific and detailed (reference actual content from the answer)
- Balanced (acknowledge both strengths and areas for improvement)
- Constructive (explain what's missing and why it matters)
- Evidence-based (cite specific parts of the answer)
- Mathematically accurate (verify all calculations - no tolerance for errors)

Example of GOOD reasoning:
"The student demonstrates a solid foundational understanding by correctly identifying the three main stages of photosynthesis. They accurately explained the light-dependent reactions occurring in the thylakoids (mentioning chlorophyll and ATP production), which shows strong grasp of the biochemical process. However, the explanation of the Calvin Cycle lacks depth - while they mention carbon fixation, they omit the critical role of RuBisCO enzyme and the regeneration of RuBP. The answer would be strengthened by including the specific products at each stage and explaining the interdependence between the two reaction phases."

Example of BAD reasoning:
"Good answer but incomplete. Missing some details."

Return ONLY valid JSON in this format:
{{
  "scores": [
    {{"criterion": "...", "awarded": X, "max": Y, "reason": "detailed, specific, constructive explanation here"}}
  ],
  "total_score": Z,
  "feedback": ["specific improvement point 1", "specific improvement point 2", "specific strength to maintain"],
  "confidence": "High/Medium/Low"
}}
"""


# -----------------------------------------------------------------------------
# Model Answer Key Generation
# -----------------------------------------------------------------------------

MODEL_ANSWER_INSTRUCTIONS = """You are creating a MODEL ANSWER KEY for educators.

Your task: Generate an exemplary answer that would receive MAXIMUM marks according to the rubric.

Requirements:
1. Demonstrate complete understanding of the topic
2. Address every criterion in the rubric comprehensively
3. Include accurate facts, clear explanations, and relevant examples
4. Use appropriate academic language and structure
5. Be thorough but concise - aim for completeness without unnecessary length
6. For mathematics: show all work, calculations must be perfectly accurate
7. For conceptual questions: explain reasoning, provide evidence, make connections

The answer should serve as:
- A gold standard for students to compare against
- Teaching material showing what excellence looks like
- Reference for understanding rubric expectations

Write the model answer as if you are an expert student who fully understands the material."""


def build_model_answer_prompt(question: str, rubric: str) -> str:
    """
    Build a prompt to generate an ideal model answer for a given question.
    
    Args:
        question: The question to answer
        rubric: The evaluation rubric (formatted)
        
    Returns:
        str: Prompt for generating model answer
    """
    return f"""You are an experienced educator creating a model answer key.

{MODEL_ANSWER_INSTRUCTIONS}

---
QUESTION
---
{question}

---
RUBRIC (Your answer must address all these criteria to receive maximum marks)
---
{rubric}

---
TASK
---
Write an exemplary model answer that would receive maximum marks on this rubric.

Return ONLY the model answer text. No JSON, no meta-commentary, just the answer itself.
Write as if you are an excellent student demonstrating perfect understanding."""


# -----------------------------------------------------------------------------
# AI Rubric Generation
# -----------------------------------------------------------------------------

RUBRIC_GENERATION_INSTRUCTIONS = """You are an expert educator designing evaluation rubrics.

Your task: Analyze the given questions and create an optimal rubric for evaluating student answers.

RUBRIC DESIGN PRINCIPLES:
1. Identify key competencies being tested (understanding, accuracy, analysis, etc.)
2. Allocate marks proportionally to question complexity
3. Use 3-6 criteria (not too few, not too many)
4. Ensure criteria are measurable and specific
5. Total marks should be reasonable (typically 10-20 per question)
6. Consider Bloom's Taxonomy levels (remember, understand, apply, analyze, evaluate, create)

COMMON CRITERIA TO CONSIDER:
- Understanding/Comprehension (basic grasp of concept)
- Accuracy/Correctness (factual accuracy, no errors)
- Depth of Explanation (detail, thoroughness)
- Critical Analysis (evaluation, reasoning)
- Application of Concepts (real-world examples, connections)
- Clarity of Expression (organization, communication)
- Use of Evidence (supporting examples, data)
- Creativity/Originality (for creative questions)

OUTPUT FORMAT:
Return ONLY a JSON array of criteria with marks:
[
  {"criterion": "Understanding", "marks": 4, "description": "Demonstrates clear grasp of core concept"},
  {"criterion": "Accuracy", "marks": 5, "description": "Factually correct with no errors"},
  {"criterion": "Explanation", "marks": 3, "description": "Provides detailed reasoning"}
]

MARK ALLOCATION GUIDELINES:
- Simple recall questions: 5-10 marks total
- Moderate explanation questions: 10-15 marks total  
- Complex analysis questions: 15-20 marks total
- Essay questions: 20-30 marks total"""


def build_rubric_generation_prompt(questions: list) -> str:
    """
    Build a prompt to generate an optimal rubric from questions.
    
    Args:
        questions: List of question texts
        
    Returns:
        str: Prompt for generating rubric
    """
    questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    return f"""{RUBRIC_GENERATION_INSTRUCTIONS}

---
QUESTIONS TO ANALYZE
---
{questions_text}

---
TASK
---
Analyze these questions and create an optimal rubric that can be used to evaluate answers to ALL of them.

Consider:
- What competencies do these questions test?
- What level of cognitive complexity is required?
- How should marks be distributed?
- What criteria best capture quality answers?

Return ONLY the JSON array of criteria. No explanations, no markdown, just the JSON array."""


RUBRIC_ANALYSIS_INSTRUCTIONS = """You are an expert educator reviewing and improving evaluation rubrics.

Your task: Analyze the current rubric and questions, then suggest improvements.

ANALYSIS CRITERIA:
1. Alignment: Do criteria match what questions actually test?
2. Completeness: Are important aspects missing?
3. Redundancy: Are criteria overlapping or redundant?
4. Mark Distribution: Are marks allocated appropriately?
5. Measurability: Are criteria specific and measurable?
6. Balance: Is the rubric well-balanced across competencies?

IMPROVEMENT TYPES:
- ADD: Suggest new criteria if important aspects are missing
- MODIFY: Suggest changes to existing criteria (name, marks, description)
- REMOVE: Suggest removing redundant or inappropriate criteria
- REDISTRIBUTE: Suggest better mark allocation

OUTPUT FORMAT:
Return a JSON object with analysis and suggestions:
{{
  "analysis": "Brief assessment of current rubric strengths and weaknesses",
  "suggestions": [
    {{
      "action": "ADD" | "MODIFY" | "REMOVE",
      "criterion": "Criterion name",
      "marks": 5,
      "description": "What this measures",
      "reasoning": "Why this change improves the rubric"
    }}
  ],
  "improved_rubric": [
    {{"criterion": "Name", "marks": 5, "description": "Description"}}
  ]
}}"""


def build_rubric_analysis_prompt(questions: list, current_rubric: list) -> str:
    """
    Build a prompt to analyze and improve existing rubric.
    
    Args:
        questions: List of question texts
        current_rubric: Current rubric as list of dicts with criterion and marks
        
    Returns:
        str: Prompt for analyzing rubric
    """
    questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    rubric_text = "\n".join([
        f"- {r.get('criterion', r.get('CRITERIA', 'Unknown'))}: {r.get('marks', r.get('TOTAL MARKS', 0))} marks"
        for r in current_rubric
    ])
    
    return f"""{RUBRIC_ANALYSIS_INSTRUCTIONS}

---
QUESTIONS
---
{questions_text}

---
CURRENT RUBRIC
---
{rubric_text}

---
TASK
---
Analyze the current rubric against these questions and suggest improvements.

Consider:
- Does the rubric fully capture what these questions test?
- Are any important evaluation criteria missing?
- Are marks distributed appropriately?
- Could any criteria be improved or consolidated?

Return ONLY the JSON object. No markdown, no explanations, just the JSON."""
