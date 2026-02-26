"""
app.py
Main Streamlit application for RubriqAI.
"""

import streamlit as st
import pandas as pd
import json
from evaluator import RubricEvaluator
from prompts import build_prompt
from utils import (
    calculate_percentage,
    get_performance_label,
    get_performance_color,
    calculate_total_score,
    format_score_display,
    get_performance_emoji
)
from multi_question import MultiQuestionAssignment, combine_evaluation_results
from database import Database
from datetime import datetime
import io

# ============================================================================
# DARK THEME CSS - ONLY VISUAL CHANGES
# ============================================================================
st.markdown("""
<style>
    /* Dark Theme */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Sidebar Dark */
    [data-testid="stSidebar"] {
        background-color: #1a1d24;
    }
    
    [data-testid="stSidebar"] * {
        color: #FAFAFA !important;
    }
    
    /* Main text visibility */
    .stMarkdown, p, span, div {
        color: #FAFAFA !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #FAFAFA !important;
    }
    
    /* Input fields dark */
    .stTextInput input, .stTextArea textarea {
        background-color: #262730 !important;
        color: #FAFAFA !important;
        border-color: #404040 !important;
    }
    
    /* Select boxes dark */
    .stSelectbox > div > div {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }
    
    /* Buttons keep their colors */
    .stButton > button {
        color: #FAFAFA !important;
    }
    
    /* Data editor dark */
    .stDataFrame {
        background-color: #1a1d24 !important;
    }
    
    /* Expanders dark */
    .streamlit-expanderHeader {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }
    
    .streamlit-expanderContent {
        background-color: #1a1d24 !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #6366F1 !important;
    }
    
    /* Labels */
    label {
        color: #FAFAFA !important;
    }
    
    /* Captions */
    .stCaptionContainer {
        color: #A0A0A0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# ORIGINAL CODE CONTINUES BELOW
# ============================================================================

# Initialize evaluator
evaluator = RubricEvaluator()

# Initialize database
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Initialize multi-question assignment in session state
if 'assignment' not in st.session_state:
    st.session_state.assignment = MultiQuestionAssignment()

if 'assignment_mode' not in st.session_state:
    st.session_state.assignment_mode = None  # None = not selected yet

if 'current_assignment_id' not in st.session_state:
    st.session_state.current_assignment_id = None

st.set_page_config(
    page_title="RubriqAI", 
    layout="centered",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ===== SIDEBAR: DATABASE FEATURES =====
with st.sidebar:
    # ===== SAVE CURRENT ASSIGNMENT =====
    if st.session_state.assignment_mode == "multi" and st.session_state.assignment.get_question_count() > 0:
        st.subheader("💾 Save Assignment")
        
        # Show if currently linked to a saved assignment
        if st.session_state.current_assignment_id:
            st.info(f"📌 Currently linked to Assignment #{st.session_state.current_assignment_id}")
            save_button_text = "💾 Save as New Copy"
        else:
            save_button_text = "💾 Save Current Assignment"
        
        if st.button(save_button_text, use_container_width=True):
            try:
                assignment_data = st.session_state.assignment.to_dict()
                assignment_id = st.session_state.db.save_assignment(assignment_data)
                st.session_state.current_assignment_id = assignment_id
                st.success(f"✅ Saved as Assignment #{assignment_id}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving: {str(e)}")
        
        st.markdown("---")
    
    # ===== LOAD ASSIGNMENT =====
    st.subheader("📂 Load Assignment")
    
    saved_assignments = st.session_state.db.get_all_assignments()
    
    if saved_assignments:
        # Show count and delete all option
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"📊 {len(saved_assignments)} assignment(s)")
        with col2:
            if st.button("🗑️ All", help="Delete all assignments", key="delete_all_btn"):
                st.session_state.confirm_delete_all = True
        
        # Confirmation dialog
        if st.session_state.get('confirm_delete_all', False):
            st.warning("⚠️ Delete ALL assignments and evaluations?")
            st.caption("This will permanently delete all saved assignments and their evaluation history.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete All", type="primary", key="confirm_yes"):
                    try:
                        count = st.session_state.db.delete_all_assignments()
                        st.session_state.confirm_delete_all = False
                        st.session_state.current_assignment_id = None
                        st.success(f"✅ Deleted {count} assignment(s)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            with col2:
                if st.button("❌ Cancel", key="confirm_no"):
                    st.session_state.confirm_delete_all = False
                    st.rerun()
        
        st.markdown("---")
        
        for assignment in saved_assignments:
            # Create unique title display with ID
            display_title = f"{assignment['title'][:25]}..."
            if len(assignment['title']) <= 25:
                display_title = assignment['title']
            
            with st.expander(f"📋 {display_title} (#{assignment['id']})", expanded=False):
                st.write(f"**Questions:** {assignment['total_questions']}")
                st.write(f"**Total Marks:** {assignment['total_marks']}")
                st.write(f"**Created:** {assignment['created_at'][:16]}")
                st.write(f"**Type:** {assignment['assignment_type']}")
                
                # Action buttons row 1
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📥", key=f"load_{assignment['id']}", help="Load"):
                        try:
                            assignment_data = st.session_state.db.load_assignment(assignment['id'])
                            st.session_state.assignment = MultiQuestionAssignment.from_dict(assignment_data)
                            st.session_state.assignment_mode = "multi"
                            st.session_state.current_assignment_id = assignment['id']
                            
                            # CRITICAL: Sync rubric to shared_rubric for UI display
                            if st.session_state.assignment.rubric is not None:
                                st.session_state.shared_rubric = st.session_state.assignment.rubric.copy()
                            
                            st.success(f"✅ Loaded #{assignment['id']}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                with col2:
                    # Export assignment to JSON
                    json_data = st.session_state.db.export_assignment_to_json(assignment['id'])
                    if json_data:
                        st.download_button(
                            "📄",
                            data=json_data,
                            file_name=f"{assignment['title'].replace(' ', '_')}_id{assignment['id']}.json",
                            mime="application/json",
                            key=f"export_{assignment['id']}",
                            help="Export JSON"
                        )
                
                with col3:
                    if st.button("🗑️", key=f"del_{assignment['id']}", help="Delete"):
                        if st.session_state.db.delete_assignment(assignment['id']):
                            st.success(f"✅ Deleted #{assignment['id']}")
                            st.rerun()
                
                # Rename section
                if st.button("✏️ Rename", key=f"rename_btn_{assignment['id']}", use_container_width=True):
                    st.session_state[f'renaming_{assignment["id"]}'] = True
                
                if st.session_state.get(f'renaming_{assignment["id"]}', False):
                    new_title = st.text_input(
                        "New Title",
                        value=assignment['title'],
                        key=f"rename_input_{assignment['id']}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Save", key=f"save_rename_{assignment['id']}"):
                            if new_title.strip():
                                if st.session_state.db.rename_assignment(assignment['id'], new_title.strip()):
                                    st.session_state[f'renaming_{assignment["id"]}'] = False
                                    st.success("✅ Renamed!")
                                    st.rerun()
                            else:
                                st.warning("Title cannot be empty")
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_rename_{assignment['id']}"):
                            st.session_state[f'renaming_{assignment["id"]}'] = False
                            st.rerun()
    else:
        st.info("No saved assignments yet")
    
    st.markdown("---")
    
    # ===== IMPORT ASSIGNMENT =====
    st.subheader("📥 Import Assignment")
    
    # File uploader for both JSON and CSV
    uploaded_file = st.file_uploader("Upload JSON or CSV", type=['json', 'csv'], key="import_file")
    
    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        # JSON Import
        if file_type == 'json' and 'last_imported_file' not in st.session_state:
            try:
                json_str = uploaded_file.read().decode('utf-8')
                assignment_id = st.session_state.db.import_assignment_from_json(json_str)
                st.session_state.last_imported_file = uploaded_file.name
                st.success(f"✅ Imported '{uploaded_file.name}' as ID: {assignment_id}")
            except Exception as e:
                st.error(f"❌ JSON Error: {str(e)}")
        
        # CSV Import
        elif file_type == 'csv' and 'last_imported_file' not in st.session_state:
            # Ask for assignment title
            if 'csv_import_title' not in st.session_state:
                st.session_state.csv_import_title = ""
            
            csv_title = st.text_input(
                "Assignment Title", 
                value=st.session_state.csv_import_title,
                placeholder="e.g., Math Quiz",
                key="csv_title_input"
            )
            
            if st.button("✅ Import CSV", key="confirm_csv_import"):
                if csv_title.strip():
                    try:
                        csv_content = uploaded_file.read().decode('utf-8')
                        
                        # Import returns dict with assignment_id and students
                        import_result = st.session_state.db.import_assignment_from_csv(
                            csv_content, 
                            csv_title.strip()
                        )
                        
                        # Handle return value - should be dict
                        if isinstance(import_result, dict):
                            assignment_id = import_result['assignment_id']
                            students = import_result.get('students', [])
                        else:
                            # Fallback for old behavior (shouldn't happen)
                            assignment_id = import_result
                            students = []
                        
                        # Load the imported assignment into current session
                        assignment_data = st.session_state.db.load_assignment(assignment_id)
                        st.session_state.assignment = MultiQuestionAssignment.from_dict(assignment_data)
                        st.session_state.assignment_mode = "multi"
                        st.session_state.current_assignment_id = assignment_id
                        
                        # Sync rubric to UI
                        if st.session_state.assignment.rubric is not None:
                            st.session_state.shared_rubric = st.session_state.assignment.rubric.copy()
                        
                        # Store students for batch evaluation
                        if students:
                            st.session_state.pending_students = students
                            st.session_state.students_count = len(students)
                            st.success(f"✅ Imported Assignment #{assignment_id} with {len(students)} students!")
                            st.info("📋 Rubric, questions, and student answers loaded. Ready for batch evaluation!")
                        else:
                            st.success(f"✅ Imported Assignment #{assignment_id}")
                            st.info("📋 Rubric and questions loaded. No student answers found in CSV.")
                        
                        st.session_state.last_imported_file = uploaded_file.name
                        st.session_state.csv_import_title = ""
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ CSV Error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                else:
                    st.warning("Please enter an assignment title")
            
            # Show CSV format help
            with st.expander("ℹ️ CSV Format Guide"):
                st.markdown("""
                ### 📋 Universal CSV Format
                
                Your CSV file should have **three sections**:
                
                #### 1️⃣ CRITERIA Section (Required)
                Define your grading rubric:
                ```csv
                CRITERIA,TOTAL MARKS
                Understanding,5
                Accuracy,5
                Explanation,3
                Critical Thinking,2
                ```
                - First column: Criterion name (e.g., "Understanding", "Accuracy")
                - Second column: Maximum marks for that criterion
                
                #### 2️⃣ QUESTIONS Section (Required)
                List all assignment questions:
                ```csv
                QUESTIONS,
                1,What is the main concept? Explain in detail.
                2,How does this process work? Include examples.
                3,Why is this important? Discuss implications.
                ```
                - First column: Question number
                - Second column: Question text
                
                #### 3️⃣ STUDENTS Section (Optional)
                Add student answers for batch evaluation:
                ```csv
                STUDENTS,
                Alice,"Detailed answer to Q1","Answer to Q2","Answer to Q3"
                Bob,"Short answer","Another answer","Third answer"
                ```
                - First column: Student name
                - Following columns: Answers to each question (in order)
                
                ### 💡 Important Tips
                
                **For English/Long Answers:**
                - ✅ Use double quotes: `"This is a long answer, with commas, and details"`
                - ✅ Commas inside quotes are preserved
                - ❌ Don't use quotes for simple one-word answers
                
                **Examples:**
                ```csv
                STUDENTS,
                Alice,42,30,"The process works by converting inputs to outputs through sequential steps"
                Bob,43,31,"It converts materials using specialized structures"
                ```
                
                ### 📦 What You Can Upload
                
                **Option A:** Questions only (no students)
                - Upload just CRITERIA and QUESTIONS sections
                - Add student answers manually later
                
                **Option B:** Complete batch (with students)
                - Upload all three sections
                - Click "Evaluate All Students" for instant grading
                
                ### 🎯 Quick Start
                1. Download "📄 Empty Template" or "📋 Sample Template" above
                2. Fill in your data
                3. Save as CSV
                4. Upload here
                5. Done! ✨
                """)
        
        # Show if already imported
        elif uploaded_file and st.session_state.get('last_imported_file') == uploaded_file.name:
            st.info(f"✅ Already imported: {uploaded_file.name}")
    
    # Reset button
    if 'last_imported_file' in st.session_state and st.button("🔄 Import Another File", key="reset_import"):
        del st.session_state.last_imported_file
        if 'csv_import_title' in st.session_state:
            del st.session_state.csv_import_title
        st.rerun()
    
    st.markdown("---")
    
    # Download Template Section
    st.subheader("📥 CSV Templates")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Universal Empty Template
        empty_template = """CRITERIA,TOTAL MARKS
Understanding,5
Accuracy,5
Explanation,3
QUESTIONS,
1,Enter your first question here
2,Enter your second question here
3,Enter your third question here
STUDENTS,
Student Name,"Answer to question 1","Answer to question 2","Answer to question 3"
"""
        st.download_button(
            "📄 Empty",
            data=empty_template,
            file_name="assignment_template.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Sample Template (generic but shows proper format)
        sample_template = """CRITERIA,TOTAL MARKS
Understanding,4
Accuracy,5
Explanation,3
Critical Analysis,3
QUESTIONS,
1,Explain the main concept and its significance. Include key components.
2,Describe the structure and function. How does it work?
3,What is the theoretical framework? Provide examples.
STUDENTS,
Alice,"The process involves converting inputs into outputs through controlled steps. Key components include processing units and catalytic elements operating in sequential phases.","The element has a complex structure with paired components in specific configuration. This ensures continuity through template-based copying maintaining consistency.","The framework proposes that elements suited to their context persist. Environmental factors like resources and pressures create selective forces."
Bob,"Process converts materials. Happens in structures. Multiple steps involved.","Has specific shape. Components pair together. Copying makes identical versions.","Framework explains trait inheritance. Environment affects beneficial traits."
Chen,"Metabolic pathway transforms substrates through enzymatic catalysis. Components include protein catalysts and electron carriers in specialized compartments.","Double-stranded helical configuration with antiparallel orientation. Semi-conservative replication with high-fidelity mechanisms.","Differential success based on heritable variation and constraints. Selection from limited resources and competition."
"""
        st.download_button(
            "📋 Sample",
            data=sample_template,
            file_name="assignment_sample.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # ===== EVALUATION HISTORY =====
    st.subheader("📊 Evaluations by Assignment")
    
    # Get all saved assignments
    saved_assignments = st.session_state.db.get_all_assignments()
    
    if saved_assignments:
        # Delete all evaluations button
        col1, col2 = st.columns([2, 1])
        with col1:
            total_evals = len(st.session_state.db.get_recent_evaluations(limit=1000))
            st.caption(f"📊 {total_evals} total evaluation(s)")
        with col2:
            if st.button("🗑️ All", help="Delete all evaluations", key="delete_all_evals_btn"):
                st.session_state.confirm_delete_all_evals = True
        
        # Confirmation dialog for delete all
        if st.session_state.get('confirm_delete_all_evals', False):
            st.warning("⚠️ Delete ALL evaluations?")
            st.caption("This will permanently delete all evaluation history.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete All", type="primary", key="confirm_yes_evals"):
                    try:
                        count = st.session_state.db.delete_all_evaluations()
                        st.session_state.confirm_delete_all_evals = False
                        st.success(f"✅ Deleted {count} evaluation(s)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            with col2:
                if st.button("❌ Cancel", key="confirm_no_evals"):
                    st.session_state.confirm_delete_all_evals = False
                    st.rerun()
        
        st.markdown("---")
        
        # Group evaluations by assignment
        for assignment in saved_assignments:
            assignment_id = assignment['id']
            assignment_title = assignment['title']
            
            # Get evaluations for this assignment
            evals = st.session_state.db.get_evaluations_by_assignment(assignment_id)
            
            if evals:  # Only show assignments that have evaluations
                with st.expander(f"📋 {assignment_title} ({len(evals)} students)", expanded=False):
                    
                    # Search bar
                    search_query = st.text_input(
                        "🔍 Search student",
                        key=f"search_{assignment_id}",
                        placeholder="Type student name..."
                    )
                    
                    # Filter evaluations based on search
                    if search_query:
                        filtered_evals = [e for e in evals if search_query.lower() in e['student_name'].lower()]
                    else:
                        filtered_evals = evals
                    
                    if not filtered_evals:
                        st.info("No students found matching search.")
                    else:
                        st.caption(f"Showing {len(filtered_evals)} of {len(evals)} students")
                        
                        # Show each student's evaluation
                        for eval_item in filtered_evals:
                            perf_label = get_performance_label(eval_item['percentage'])
                            perf_emoji = get_performance_emoji(perf_label)
                            
                            with st.container():
                                # Student summary row
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    if st.button(
                                        f"{perf_emoji} {eval_item['student_name']} - {eval_item['percentage']}%",
                                        key=f"view_{eval_item['id']}",
                                        use_container_width=True
                                    ):
                                        # Toggle detail view
                                        key = f"show_detail_{eval_item['id']}"
                                        st.session_state[key] = not st.session_state.get(key, False)
                                        st.rerun()
                                
                                with col2:
                                    st.caption(f"{eval_item['total_score']}/{eval_item['max_score']}")
                                
                                # Show details if expanded
                                if st.session_state.get(f"show_detail_{eval_item['id']}", False):
                                    st.markdown("---")
                                    st.write(f"**Date:** {eval_item['evaluated_at'][:16]}")
                                    st.write(f"**Mode:** {eval_item['evaluation_mode']}")
                                    
                                    # Show individual question scores if available
                                    results = eval_item.get('results_json', {})
                                    individual_results = results.get('individual_results', [])
                                    
                                    if individual_results:
                                        st.markdown("**Question Scores:**")
                                        for q_result in individual_results:
                                            if 'error' not in q_result:
                                                q_num = q_result.get('question_number', '?')
                                                q_score = q_result.get('total_score', 0)
                                                q_max = sum(s.get('max', 0) for s in q_result.get('scores', []))
                                                st.caption(f"Q{q_num}: {q_score}/{q_max}")
                                    
                                    # Action buttons
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("✏️ Edit Name", key=f"edit_{eval_item['id']}", use_container_width=True):
                                            st.session_state[f'editing_{eval_item["id"]}'] = True
                                    with col2:
                                        if st.button("🗑️ Delete", key=f"del_{eval_item['id']}", use_container_width=True):
                                            if st.session_state.db.delete_evaluation(eval_item['id']):
                                                st.success("Deleted!")
                                                st.rerun()
                                    
                                    # Edit name inline
                                    if st.session_state.get(f'editing_{eval_item["id"]}', False):
                                        new_name = st.text_input("New name", value=eval_item['student_name'], key=f"name_{eval_item['id']}")
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if st.button("✅ Save", key=f"save_{eval_item['id']}"):
                                                if st.session_state.db.update_evaluation_student_name(eval_item['id'], new_name):
                                                    st.session_state[f'editing_{eval_item["id"]}'] = False
                                                    st.success("Updated!")
                                                    st.rerun()
                                        with col2:
                                            if st.button("❌ Cancel", key=f"cancel_{eval_item['id']}"):
                                                st.session_state[f'editing_{eval_item["id"]}'] = False
                                                st.rerun()
                                    
                                    st.markdown("---")
                    
                    # Download button for this assignment
                    st.markdown("---")
                    if st.button(f"📥 Download Assessment Report", key=f"download_{assignment_id}", use_container_width=True):
                        st.session_state[f'download_trigger_{assignment_id}'] = True
                        st.rerun()
                    
                    # Generate download if triggered
                    if st.session_state.get(f'download_trigger_{assignment_id}', False):
                        try:
                            # Create Excel/CSV report
                            import pandas as pd
                            
                            # Get all evaluation details
                            report_data = []
                            for eval_item in evals:
                                row = {
                                    'Student Name': eval_item['student_name'],
                                    'Total Score': eval_item['total_score'],
                                    'Max Score': eval_item['max_score'],
                                    'Percentage': eval_item['percentage'],
                                    'Grade': get_performance_label(eval_item['percentage']),
                                    'Evaluation Mode': eval_item['evaluation_mode'],
                                    'Date': eval_item['evaluated_at']
                                }
                                
                                # Add individual question scores
                                results = eval_item.get('results_json', {})
                                individual_results = results.get('individual_results', [])
                                for q_result in individual_results:
                                    if 'error' not in q_result:
                                        q_num = q_result.get('question_number', '?')
                                        q_score = q_result.get('total_score', 0)
                                        q_max = sum(s.get('max', 0) for s in q_result.get('scores', []))
                                        row[f'Q{q_num} Score'] = f"{q_score}/{q_max}"
                                
                                report_data.append(row)
                            
                            df = pd.DataFrame(report_data)
                            
                            # Convert to CSV
                            csv = df.to_csv(index=False)
                            
                            st.download_button(
                                "⬇️ Download CSV Report",
                                data=csv,
                                file_name=f"{assignment_title.replace(' ', '_')}_assessment_report.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key=f"dl_btn_{assignment_id}"
                            )
                            
                            # Reset trigger after showing download
                            if st.button("Done", key=f"done_{assignment_id}"):
                                st.session_state[f'download_trigger_{assignment_id}'] = False
                                st.rerun()
                        
                        except Exception as e:
                            st.error(f"Error generating report: {str(e)}")
    
    else:
        st.info("No assignments with evaluations yet.")
    
    st.markdown("---")
    
    # ===== EXPORT ALL EVALUATIONS =====
    st.subheader("📤 Export Data")
    
    if st.button("📥 Export All Evaluations (CSV)", use_container_width=True):
        try:
            df = st.session_state.db.export_evaluations_to_csv()
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    data=csv,
                    file_name=f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("No evaluations to export")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Header
st.title("📊 RubriqAI - AI Rubric Evaluation Assistant")
st.markdown("""
**Intelligent AI-powered grading** using custom rubrics. Get instant, detailed evaluations 
with criterion-by-criterion feedback and performance metrics.
""")
st.markdown("---")

# ===== MODE SELECTION =====
st.subheader("📋 Select Assignment Type")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Single Question", use_container_width=True, type="primary" if st.session_state.assignment_mode == "single" else "secondary"):
        st.session_state.assignment_mode = "single"
        st.rerun()

with col2:
    if st.button("📚 Multi-Question Assignment", use_container_width=True, type="primary" if st.session_state.assignment_mode == "multi" else "secondary"):
        st.session_state.assignment_mode = "multi"
        st.rerun()

with col3:
    if st.button("🌐 Online Test", use_container_width=True, type="primary" if st.session_state.assignment_mode == "online" else "secondary"):
        st.session_state.assignment_mode = "online"
        st.rerun()

# Stop here if no mode selected yet
if st.session_state.assignment_mode is None:
    st.info("👆 Please select an assignment type to begin.")
    st.stop()

st.markdown("---")

# ===== ONLINE TEST MODE =====
if st.session_state.assignment_mode == "online":
    
    st.subheader("🌐 Online Test Hosting")
    
    # Create layout: main content (70%) + info panel (30%)
    col_main, col_info = st.columns([7, 3])
    
    with col_main:
        st.info("""
        **📋 Features:**
        • Schedule tests (start/end times)
        • Get unique test codes
        • Track submissions live
        • Download CSV for grading
        
        **Student URL:** `localhost:8000/student.html`
        """)
        
        try:
            from test_hosting import (
                TestHosting,
                render_teacher_test_creator,
                render_teacher_test_manager
            )
            
            tab1, tab2 = st.tabs(["📝 Create Test", "📊 Manage Tests"])
            
            with tab1:
                render_teacher_test_creator()
            
            with tab2:
                render_teacher_test_manager()
                
        except ImportError as e:
            st.error(f"❌ test_hosting.py not found or has errors: {str(e)}")
            st.info("Make sure test_hosting.py is in the same folder as app.py")
    
    # Info panel on the right
    with col_info:
        try:
            from test_hosting import render_right_sidebar
            render_right_sidebar()
        except Exception as e:
            st.caption("Info unavailable")
    
    st.stop()

st.markdown("---")

# ===== SINGLE QUESTION MODE =====
if st.session_state.assignment_mode == "single":
    # ===== QUESTION INPUT =====
    st.subheader("Enter Question")
    question = st.text_area("Question", key="question_input")
    st.write("\n")

    # ===== RUBRIC INPUT WITH TABLE FORMAT =====
    st.subheader("Enter Rubric")

    # Initialize rubric dataframe in session state with new structure (ONLY 1 ROW)
    if 'rubric' not in st.session_state:
        st.session_state.rubric = pd.DataFrame({
            "CRITERIA": [""],
            "TOTAL MARKS": [0],
        })

    # Button to add new row
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("➕ Add Row"):
            new_row = pd.DataFrame({
                "CRITERIA": [""],
                "TOTAL MARKS": [0]
            })
            st.session_state.rubric = pd.concat([st.session_state.rubric, new_row], ignore_index=True)
            st.rerun()

    # Display the editable table with restrictions
    edited_rubric = st.data_editor(
        st.session_state.rubric,
        num_rows="fixed",  # Changed from "dynamic" to "fixed" - prevents adding rows via table
        use_container_width=True,
        height=min(200, 50 + len(st.session_state.rubric) * 35),  # Dynamic height based on rows
        key="rubric_editor",
        hide_index=True,  # Hide row numbers
        column_config={
            "CRITERIA": st.column_config.TextColumn(
                "CRITERIA",
                help="Enter the evaluation criterion",
                required=True,
                width="large"
            ),
            "TOTAL MARKS": st.column_config.NumberColumn(
                "TOTAL MARKS",
                help="Maximum marks for this criterion",
                min_value=0,
                max_value=100,
                step=1,
                required=True,
                width="medium"
            )
        },
        disabled=False,  # Allow editing cells
        column_order=["CRITERIA", "TOTAL MARKS"]  # Lock column order
    )

    st.write("\n")

    # ===== STUDENT ANSWER INPUT =====
    st.subheader("Enter Student Answer")
    answer = st.text_area("Student Answer", key="answer_input")
    st.write("\n")

# ===== MULTI-QUESTION MODE =====
else:
    # Assignment title
    st.subheader("📚 Assignment Setup")
    assignment_title = st.text_input("Assignment Title", value=st.session_state.assignment.assignment_title, key="assignment_title_input", placeholder="e.g., Biology Midterm Exam")
    st.session_state.assignment.assignment_title = assignment_title
    
    st.markdown("---")
    
    # Step 1: Set up SHARED rubric
    st.subheader("Step 1: Define Evaluation Rubric")
    st.info("📌 This rubric will be used to evaluate ALL questions in the assignment.")
    
    # Initialize shared rubric - but check if assignment already has one
    if 'shared_rubric' not in st.session_state:
        # Check if current assignment has a rubric
        if st.session_state.assignment.rubric is not None:
            st.session_state.shared_rubric = st.session_state.assignment.rubric.copy()
        else:
            st.session_state.shared_rubric = pd.DataFrame({
                "CRITERIA": [""],
                "TOTAL MARKS": [0],
            })
    
    # AI Rubric Features Row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Add Criterion", key="add_criterion_shared", use_container_width=True):
            new_row = pd.DataFrame({
                "CRITERIA": [""],
                "TOTAL MARKS": [0]
            })
            st.session_state.shared_rubric = pd.concat([st.session_state.shared_rubric, new_row], ignore_index=True)
            st.rerun()
    
    with col2:
        # Auto-Generate Rubric Button
        if st.button("🤖 Auto-Generate", key="auto_gen_rubric", help="AI creates rubric from your questions", use_container_width=True):
            if st.session_state.assignment.get_question_count() > 0:
                st.session_state.show_auto_generate = True
                st.rerun()
            else:
                st.warning("⚠️ Add questions first in Step 2!")
    
    with col3:
        # Analyze Rubric Button
        has_rubric = any(st.session_state.shared_rubric['CRITERIA'].str.strip() != '') and any(st.session_state.shared_rubric['TOTAL MARKS'] > 0)
        if st.button("🔍 Analyze", key="analyze_rubric", help="AI analyzes and improves your rubric", disabled=not has_rubric, use_container_width=True):
            if st.session_state.assignment.get_question_count() > 0:
                st.session_state.show_analyze = True
                st.rerun()
            else:
                st.warning("⚠️ Add questions first in Step 2!")
    
    # Auto-Generate Rubric Process
    if st.session_state.get('show_auto_generate', False):
        st.markdown("---")
        st.subheader("🤖 AI Rubric Generation")
        
        with st.spinner("🤖 Analyzing questions and generating optimal rubric..."):
            from prompts import build_rubric_generation_prompt
            
            # Get all question texts
            questions = [q['question_text'] for q in st.session_state.assignment.questions]
            
            # Generate rubric
            prompt = build_rubric_generation_prompt(questions)
            evaluator.temperature = 0.3
            result = evaluator.evaluate(prompt)
            
            try:
                # Parse JSON response
                import re
                # Extract JSON array from response
                json_match = re.search(r'\[.*?\]', result, re.DOTALL)
                if json_match:
                    rubric_data = json.loads(json_match.group())
                    
                    # Convert to DataFrame
                    new_rubric = pd.DataFrame({
                        'CRITERIA': [item['criterion'] for item in rubric_data],
                        'TOTAL MARKS': [item['marks'] for item in rubric_data]
                    })
                    
                    st.success(f"✅ Generated {len(rubric_data)} criteria based on your questions!")
                    
                    # Show what was generated
                    with st.expander("📋 Generated Rubric Preview", expanded=True):
                        for item in rubric_data:
                            st.write(f"**{item['criterion']}** - {item['marks']} marks")
                            if 'description' in item and item['description']:
                                st.caption(f"_{item['description']}_")
                    
                    # Apply or cancel
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Use This Rubric", type="primary", key="use_generated", use_container_width=True):
                            st.session_state.shared_rubric = new_rubric
                            st.session_state.show_auto_generate = False
                            st.success("✅ Rubric applied!")
                            st.rerun()
                    with col_b:
                        if st.button("❌ Cancel", key="cancel_generated", use_container_width=True):
                            st.session_state.show_auto_generate = False
                            st.rerun()
                else:
                    st.error("❌ Could not parse AI response. Try again.")
                    if st.button("❌ Close", key="close_gen_error"):
                        st.session_state.show_auto_generate = False
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if st.button("❌ Close", key="close_gen_exception"):
                    st.session_state.show_auto_generate = False
                    st.rerun()
        st.markdown("---")
    
    # Analyze Rubric Process
    if st.session_state.get('show_analyze', False):
        st.markdown("---")
        st.subheader("🔍 AI Rubric Analysis")
        
        with st.spinner("🔍 Analyzing your rubric against the questions..."):
            from prompts import build_rubric_analysis_prompt
            
            # Get questions and current rubric
            questions = [q['question_text'] for q in st.session_state.assignment.questions]
            current_rubric = st.session_state.shared_rubric.to_dict('records')
            
            # Analyze rubric
            prompt = build_rubric_analysis_prompt(questions, current_rubric)
            evaluator.temperature = 0.3
            result = evaluator.evaluate(prompt)
            
            try:
                # Parse JSON response
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    
                    st.success("✅ Analysis complete!")
                    
                    # Show analysis
                    st.write("**AI Assessment:**")
                    st.info(analysis.get('analysis', 'Analysis not available'))
                    
                    st.write("**Recommended Changes:**")
                    suggestions = analysis.get('suggestions', [])
                    if suggestions:
                        for idx, suggestion in enumerate(suggestions, 1):
                            action_emoji = {
                                'ADD': '🟢',
                                'MODIFY': '🟡', 
                                'REMOVE': '🔴'
                            }.get(suggestion.get('action', ''), '⚪')
                            
                            with st.expander(f"{action_emoji} {suggestion.get('action')} - {suggestion.get('criterion')}", expanded=True):
                                st.write(f"**Marks:** {suggestion.get('marks', 0)}")
                                if 'description' in suggestion:
                                    st.write(f"**What it measures:** {suggestion.get('description', '')}")
                                st.caption(f"**Why:** {suggestion.get('reasoning', '')}")
                    else:
                        st.write("✅ Your rubric looks good! No major changes needed.")
                    
                    # Apply button
                    st.markdown("---")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Apply Improvements", type="primary", key="apply_improved", use_container_width=True):
                            improved = analysis.get('improved_rubric', [])
                            if improved:
                                new_rubric = pd.DataFrame({
                                    'CRITERIA': [item['criterion'] for item in improved],
                                    'TOTAL MARKS': [item['marks'] for item in improved]
                                })
                                st.session_state.shared_rubric = new_rubric
                                st.session_state.show_analyze = False
                                st.success("✅ Rubric updated with improvements!")
                                st.rerun()
                    with col_b:
                        if st.button("❌ Keep Current", key="cancel_analyze", use_container_width=True):
                            st.session_state.show_analyze = False
                            st.rerun()
                else:
                    st.error("❌ Could not parse AI response. Try again.")
                    if st.button("❌ Close", key="close_analyze_error"):
                        st.session_state.show_analyze = False
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if st.button("❌ Close", key="close_analyze_exception"):
                    st.session_state.show_analyze = False
                    st.rerun()
        st.markdown("---")
    
    shared_rubric_edited = st.data_editor(
        st.session_state.shared_rubric,
        num_rows="fixed",
        use_container_width=True,
        height=min(200, 50 + len(st.session_state.shared_rubric) * 35),
        key="shared_rubric_editor",
        hide_index=True,
        column_config={
            "CRITERIA": st.column_config.TextColumn("CRITERIA", required=True, width="large"),
            "TOTAL MARKS": st.column_config.NumberColumn("TOTAL MARKS", min_value=0, max_value=100, step=1, required=True, width="medium")
        },
        column_order=["CRITERIA", "TOTAL MARKS"]
    )
    
    # Always update the assignment rubric
    if st.session_state.assignment.rubric is None or not st.session_state.shared_rubric.equals(st.session_state.assignment.rubric if st.session_state.assignment.rubric is not None else pd.DataFrame()):
        # Check if rubric is valid
        valid_rubric = False
        for idx, row in shared_rubric_edited.iterrows():
            if str(row['CRITERIA']).strip() and pd.notna(row['TOTAL MARKS']) and row['TOTAL MARKS'] > 0:
                valid_rubric = True
                break
        
        if valid_rubric:
            st.session_state.assignment.set_rubric(shared_rubric_edited)
            # Update shared_rubric to match
            st.session_state.shared_rubric = shared_rubric_edited.copy()
            st.success(f"✅ Rubric set! Each question is worth **{st.session_state.assignment.max_marks_per_question} marks**")
        else:
            st.warning("⚠️ Please add at least one valid criterion with marks > 0")
    else:
        if st.session_state.assignment.rubric is not None:
            st.success(f"✅ Rubric is active! Each question is worth **{st.session_state.assignment.max_marks_per_question} marks**")
    
    st.markdown("---")
    
    # Step 2: Add Questions
    st.subheader("Step 2: Add Questions")
    
    with st.expander("➕ Add New Question", expanded=len(st.session_state.assignment.questions) == 0):
        new_question_text = st.text_area("Question Text", key="new_question_text", height=100, placeholder="Enter your question here...")
        
        if st.button("✅ Add Question to Assignment", type="primary", key="add_question_btn"):
            if new_question_text.strip():
                if st.session_state.assignment.rubric is not None:
                    q_num = st.session_state.assignment.add_question(new_question_text)
                    st.success(f"✅ Question {q_num} added!")
                    st.rerun()
                else:
                    st.error("⚠️ Please set a valid rubric first (Step 1)!")
            else:
                st.error("⚠️ Please enter question text.")
    
    # Display Added Questions
    if st.session_state.assignment.get_question_count() > 0:
        st.markdown(f"#### 📝 Questions in Assignment ({st.session_state.assignment.get_question_count()})")
        
        for q_data in st.session_state.assignment.questions:
            col1, col2 = st.columns([5, 1])
            
            with col1:
                st.write(f"**Q{q_data['question_number']}.** {q_data['question_text']}")
            
            with col2:
                if st.button("🗑️", key=f"remove_q_{q_data['question_number']}", help=f"Remove Q{q_data['question_number']}"):
                    st.session_state.assignment.remove_question(q_data['question_number'])
                    st.rerun()
        
        st.info(f"📊 **Total Assignment Marks:** {st.session_state.assignment.get_total_marks()} ({st.session_state.assignment.get_question_count()} questions × {st.session_state.assignment.max_marks_per_question} marks each)")
    else:
        st.info("👆 Click 'Add New Question' above to add questions to your assignment.")
    
    st.markdown("---")
    
    # Step 3: Batch Student Evaluation
    st.subheader("Step 3: Batch Evaluation")
    
    if st.session_state.assignment.get_question_count() > 0:
        # Check if we have pending students from CSV import
        if 'pending_students' in st.session_state and st.session_state.pending_students:
            students = st.session_state.pending_students
            st.success(f"✅ {len(students)} students loaded from CSV and ready for evaluation!")
            
            # Show student list
            with st.expander(f"👥 View Students ({len(students)})", expanded=False):
                for idx, student in enumerate(students, 1):
                    answer_count = len(student.get('answers', {}))
                    st.write(f"{idx}. **{student['student_name']}** - {answer_count} answers provided")
            
            st.markdown("---")
            
            # Batch evaluation not yet run
            if 'batch_evaluation_complete' not in st.session_state:
                st.session_state.batch_evaluation_complete = False
            
            if not st.session_state.batch_evaluation_complete:
                st.info("💡 Click below to evaluate all students automatically using AI.")
                # This button will be in the evaluation section
            else:
                st.success("✅ Batch evaluation completed! Check results in sidebar.")
                if st.button("🔄 Run Evaluation Again", key="rerun_batch"):
                    st.session_state.batch_evaluation_complete = False
                    st.rerun()
        
        else:
            # No students from CSV - show instructions
            st.info("📤 To evaluate multiple students:")
            st.markdown("""
            1. Create a CSV file with student answers
            2. Use format: `STUDENTS,` section with `student_name,answer1,answer2,...`
            3. Upload via sidebar → Import Assignment
            4. Students will appear here for batch evaluation
            """)
            
            # Show CSV example
            with st.expander("📄 CSV Format Example"):
                st.code("""CRITERIA,TOTAL MARKS
Understanding,3
Correctness,5
QUESTIONS,
1,What is photosynthesis?
2,Why is it important?
STUDENTS,
Alice,"Photosynthesis is the process where plants convert sunlight into energy","It provides oxygen and food"
Bob,"Plants make food from light","Essential for life on Earth"
""")
    
    else:
        st.info("💡 Add questions first (Step 2) to enable student evaluation.")
    
    # Set dummy values for single-question variables (will not be used)
    question = ""
    answer = ""
    edited_rubric = None

# ===== EVALUATION MODE SELECTION =====
st.subheader("⚙️ Evaluation Mode")
mode = st.selectbox(
    "Select evaluation strictness",
    ["Moderate", "Strict", "Lenient"],
    help="Strict: High standards, minimal partial credit | Moderate: Balanced approach | Lenient: Generous partial credit"
)

# Display mode description
mode_descriptions = {
    "Strict": "🔴 **Strict Mode**: High standards, awards points only when criteria are fully met with clear evidence.",
    "Moderate": "🟡 **Moderate Mode**: Balanced evaluation, gives fair partial credit for reasonable understanding.",
    "Lenient": "🟢 **Lenient Mode**: Generous evaluation, focuses on what student got right and encourages learning."
}
st.info(mode_descriptions[mode])
st.write("\n")

# ===== EVALUATION BUTTON =====
# Different button text based on mode
if st.session_state.assignment_mode == "multi" and 'pending_students' in st.session_state and st.session_state.pending_students:
    button_text = f"🎯 Evaluate All {len(st.session_state.pending_students)} Students"
else:
    button_text = "🎯 Evaluate"

if st.button(button_text):
    
    # ===== SINGLE QUESTION MODE EVALUATION =====
    if st.session_state.assignment_mode == "single":
        rubric_filled = False
        rubric_formatted = ""
        
        # Validate table rubric
        if edited_rubric is not None:
            for idx, row in edited_rubric.iterrows():
                if (str(row['CRITERIA']).strip() != '' and 
                    str(row['TOTAL MARKS']).strip() != ''):
                    rubric_filled = True
                    break
        
        if rubric_filled:
            # Convert table to structured format for the model
            rubric_formatted = "RUBRIC:\n\n"
            for idx, row in edited_rubric.iterrows():
                if (str(row['CRITERIA']).strip() and 
                    str(row['TOTAL MARKS']).strip()):
                    rubric_formatted += f"Criterion: {row['CRITERIA']}\n"
                    rubric_formatted += f"Maximum Marks: {row['TOTAL MARKS']}\n"
                    rubric_formatted += "---\n"
        else:
            st.error("⚠️ Please enter at least one complete rubric criterion with CRITERIA and TOTAL MARKS.")
        
        # Validate question and answer
        if not question:
            st.error("⚠️ Please enter a question.")
        if not answer:
            st.error("⚠️ Please enter an answer.")
        
        # Proceed if all validations pass
        if question and answer and rubric_filled:
            # Save rubric to session state
            st.session_state.rubric = edited_rubric
            
            # Set evaluation mode
            evaluator.set_mode(mode.lower())
            
            # Build prompt and evaluate using evaluator module
            prompt = build_prompt(question, rubric_formatted, answer)
            
            with st.spinner("🔄 Evaluating..."):
                result = evaluator.evaluate(prompt)
            
            # Store result in session state for display
            st.session_state.evaluation_result = result
            st.session_state.evaluation_mode_used = mode
            st.session_state.evaluated_rubric = edited_rubric
    
    # ===== MULTI-QUESTION MODE - BATCH EVALUATION =====
    else:
        # Check if we have students to evaluate
        if 'pending_students' not in st.session_state or not st.session_state.pending_students:
            st.error("⚠️ No students found. Please upload a CSV with student answers in the STUDENTS section.")
        elif st.session_state.assignment.get_question_count() == 0:
            st.error("⚠️ Please add at least one question to the assignment.")
        else:
            # BATCH EVALUATION
            students = st.session_state.pending_students
            total_students = len(students)
            
            st.info(f"🚀 Starting batch evaluation for {total_students} students...")
            
            # Set evaluation mode
            evaluator.set_mode(mode.lower())
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Track all evaluations
            all_evaluations_saved = []
            
            # Evaluate each student
            for student_idx, student in enumerate(students):
                student_name = student['student_name']
                student_answers = student['answers']  # Dict: {question_num: answer}
                
                status_text.text(f"📝 Evaluating {student_name}... ({student_idx + 1}/{total_students})")
                progress_bar.progress(student_idx / total_students)
                
                # Evaluate all questions for this student
                individual_results = []
                
                for q_data in st.session_state.assignment.questions:
                    q_num = q_data['question_number']
                    q_text = q_data['question_text']
                    
                    # Get student's answer for this question
                    student_answer = student_answers.get(q_num, "")
                    
                    if not student_answer:
                        # No answer provided for this question
                        individual_results.append({
                            'question_number': q_num,
                            'question_text': q_text,
                            'error': 'No answer provided'
                        })
                        continue
                    
                    # Format rubric
                    rubric_formatted = st.session_state.assignment.format_rubric_for_evaluation()
                    
                    # Build prompt and evaluate
                    prompt = build_prompt(q_text, rubric_formatted, student_answer)
                    result = evaluator.evaluate(prompt)
                    
                    # Parse result
                    try:
                        parsed_result = json.loads(result)
                        parsed_result['question_number'] = q_num
                        parsed_result['question_text'] = q_text
                        individual_results.append(parsed_result)
                    except:
                        individual_results.append({
                            'question_number': q_num,
                            'question_text': q_text,
                            'error': result
                        })
                
                # Combine results for this student
                combined = combine_evaluation_results(individual_results)
                percentage = calculate_percentage(combined['total_score'], combined['total_max'])
                
                # Auto-save this student's evaluation
                if st.session_state.current_assignment_id:
                    try:
                        evaluation_data = {
                            'total_score': combined['total_score'],
                            'total_max': combined['total_max'],
                            'percentage': percentage,
                            'mode': mode,
                            'individual_results': individual_results
                        }
                        eval_id = st.session_state.db.save_evaluation(
                            st.session_state.current_assignment_id,
                            evaluation_data,
                            student_name=student_name
                        )
                        all_evaluations_saved.append({
                            'eval_id': eval_id,
                            'student_name': student_name,
                            'score': combined['total_score'],
                            'max': combined['total_max'],
                            'percentage': percentage
                        })
                    except Exception as e:
                        st.warning(f"Could not save evaluation for {student_name}: {str(e)}")
            
            # Complete
            progress_bar.progress(1.0)
            status_text.text(f"✅ All {total_students} students evaluated!")
            
            # Mark batch as complete
            st.session_state.batch_evaluation_complete = True
            st.session_state.batch_results = all_evaluations_saved
            
            # Clear pending students
            del st.session_state.pending_students
            
            st.success(f"🎉 Batch evaluation complete! {len(all_evaluations_saved)} students evaluated and saved.")
            st.info("📊 View results in sidebar → Evaluations by Assignment")
            
            # Show summary
            if all_evaluations_saved:
                st.markdown("### 📊 Quick Summary")
                summary_df = pd.DataFrame(all_evaluations_saved)
                summary_df = summary_df[['student_name', 'score', 'max', 'percentage']]
                summary_df.columns = ['Student', 'Score', 'Max', 'Percentage']
                st.dataframe(summary_df, use_container_width=True)
                
                st.markdown("---")
                
                # ===== POWER FEATURES =====
                st.markdown("## 🔥 AI-Powered Analytics")
                
                tab_analytics, tab_plagiarism, tab_ai_detector = st.tabs([
                    "📊 Performance Dashboard", 
                    "🔍 Similarity Analysis",
                    "🤖 AI Writing Detector"
                ])
                
                # TAB 1: PERFORMANCE DASHBOARD
                with tab_analytics:
                    try:
                        from similarity_analysis import PerformanceAnalyzer
                        
                        analyzer = PerformanceAnalyzer()
                        
                        # Prepare evaluation data
                        eval_data = []
                        for student in students:
                            student_name = student['student_name']
                            # Find this student's result
                            student_result = next((e for e in all_evaluations_saved if e['student_name'] == student_name), None)
                            if student_result:
                                eval_data.append({
                                    'student_name': student_name,
                                    'percentage': student_result['percentage'],
                                    'total_score': student_result['score'],
                                    'individual_results': []  # Would need to get from db
                                })
                        
                        # Class Overview
                        st.markdown("### 📈 Class Performance Overview")
                        class_stats = analyzer.analyze_class_performance(eval_data)
                        
                        if class_stats:
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Class Average", f"{class_stats['class_average']}%")
                            with col2:
                                st.metric("Median", f"{class_stats['median']}%")
                            with col3:
                                st.metric("Passing Rate", f"{class_stats['passing_rate']}%")
                            with col4:
                                st.metric("Std Dev", f"{class_stats['std_dev']}%")
                            
                            st.markdown("---")
                            
                            # Performance Distribution
                            st.markdown("### 📊 Grade Distribution")
                            dist = class_stats['distribution']
                            
                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            with col1:
                                st.metric("A (90%+)", dist['excellent'], delta="Excellent")
                            with col2:
                                st.metric("B (80-89%)", dist['good'], delta="Good")
                            with col3:
                                st.metric("C (70-79%)", dist['average'], delta="Average")
                            with col4:
                                st.metric("D (60-69%)", dist['below_average'], delta="Below Avg")
                            with col5:
                                st.metric("F (<60%)", dist['failing'], delta="Failing" if dist['failing'] > 0 else None)
                            
                            st.markdown("---")
                            
                            # Student Segmentation
                            col_left, col_right = st.columns(2)
                            
                            with col_left:
                                st.markdown("### 🌟 Top Performers (85%+)")
                                top = analyzer.identify_top_performers(eval_data, 85)
                                if top:
                                    for i, student in enumerate(top[:5], 1):
                                        st.write(f"{i}. **{student['name']}** - {student['percentage']}%")
                                else:
                                    st.info("No students above 85%")
                            
                            with col_right:
                                st.markdown("### 📚 Need Support (<60%)")
                                struggling = analyzer.identify_struggling_students(eval_data, 60)
                                if struggling:
                                    for i, student in enumerate(struggling[:5], 1):
                                        st.write(f"{i}. **{student['name']}** - {student['percentage']}%")
                                else:
                                    st.success("All students passing!")
                        
                    except ImportError:
                        st.error("❌ Analytics module not found. Make sure similarity_analysis.py is in the folder.")
                    except Exception as e:
                        st.error(f"Error generating analytics: {str(e)}")
                
                # TAB 2: SIMILARITY ANALYSIS
                with tab_plagiarism:
                    try:
                        from similarity_analysis import SimilarityAnalyzer
                        
                        analyzer = SimilarityAnalyzer()
                        
                        st.markdown("### 🔍 Answer Similarity Detection")
                        st.info("💡 Detects potential plagiarism by analyzing answer similarity across all students")
                        
                        # Prepare student answers
                        student_answers = []
                        for student in students:
                            student_answers.append({
                                'student_name': student['student_name'],
                                'answers': student['answers']
                            })
                        
                        if len(student_answers) >= 2:
                            with st.spinner("🔍 Analyzing answer similarity..."):
                                # Calculate overall similarity matrix
                                similarity_df = analyzer.calculate_similarity_matrix(student_answers)
                                
                                if similarity_df is not None:
                                    # Get suspicious pairs with LOWER threshold (more sensitive)
                                    suspicious = analyzer.get_suspicious_pairs(similarity_df, threshold=60)
                                    
                                    if suspicious:
                                        st.warning(f"⚠️ Found {len(suspicious)} suspicious pair(s) with >60% similarity")
                                        
                                        # Show top suspicious pairs
                                        st.markdown("#### 🚨 Flagged Pairs")
                                        for student1, student2, similarity in suspicious[:10]:
                                            color = analyzer.get_color_for_similarity(similarity)
                                            
                                            # Determine severity
                                            if similarity >= 80:
                                                severity = "🔴 VERY HIGH"
                                            elif similarity >= 70:
                                                severity = "🟠 HIGH"
                                            else:
                                                severity = "🟡 MODERATE"
                                            
                                            st.markdown(
                                                f"{severity} - **{student1}** ↔ **{student2}**: "
                                                f"<span style='color: {color}; font-weight: bold; font-size: 1.2em;'>{similarity}%</span> similar",
                                                unsafe_allow_html=True
                                            )
                                    else:
                                        st.success("✅ No high similarity detected. Answers appear reasonably unique.")
                                    
                                    st.markdown("---")
                                    
                                    # Show overall heatmap
                                    st.markdown("#### 🗺️ Overall Similarity Heatmap")
                                    st.caption("Shows overall similarity across all questions. Hover to see percentages.")
                                    
                                    # Color the dataframe
                                    def color_similarity(val):
                                        if val >= 80:
                                            return 'background-color: #ff4444; color: white; font-weight: bold;'
                                        elif val >= 70:
                                            return 'background-color: #ff8844; color: white; font-weight: bold;'
                                        elif val >= 60:
                                            return 'background-color: #ffbb44; font-weight: bold;'
                                        elif val >= 50:
                                            return 'background-color: #ffdd88;'
                                        else:
                                            return 'background-color: #88ff88;'
                                    
                                    # Style and display
                                    styled_df = similarity_df.style.applymap(color_similarity).format("{:.1f}%")
                                    st.dataframe(styled_df, use_container_width=True)
                                    
                                    st.markdown("---")
                                    
                                    # Question-by-question analysis
                                    st.markdown("#### 📋 Question-by-Question Analysis")
                                    st.caption("See which specific questions show high similarity")
                                    
                                    # Get question numbers
                                    if students and len(students) > 0:
                                        question_nums = sorted(students[0]['answers'].keys())
                                        
                                        for q_num in question_nums:
                                            with st.expander(f"Question {q_num} Similarity"):
                                                q_similarity = analyzer.calculate_question_similarity_matrix(
                                                    student_answers, 
                                                    q_num
                                                )
                                                
                                                if q_similarity is not None:
                                                    # Find suspicious pairs for this question
                                                    q_suspicious = analyzer.get_suspicious_pairs(q_similarity, threshold=65)
                                                    
                                                    if q_suspicious:
                                                        st.warning(f"{len(q_suspicious)} suspicious pair(s) in this question")
                                                        for s1, s2, sim in q_suspicious[:3]:
                                                            st.write(f"• {s1} ↔ {s2}: {sim}%")
                                                    else:
                                                        st.success("No high similarity in this question")
                                                    
                                                    # Show mini heatmap
                                                    styled_q = q_similarity.style.applymap(color_similarity).format("{:.1f}%")
                                                    st.dataframe(styled_q, use_container_width=True)
                                                else:
                                                    st.info("Insufficient data for this question")
                                    
                                    st.markdown("---")
                                    
                                    # Interpretation guide
                                    with st.expander("📖 How to Read the Results"):
                                        st.markdown("""
                                        **Similarity Scores:**
                                        - 🔴 **80%+ (Red)**: Very suspicious - likely plagiarism or direct copying
                                        - 🟠 **70-79% (Orange)**: Suspicious - investigate these pairs
                                        - 🟡 **60-69% (Yellow)**: Moderate - similar thinking or minor collaboration
                                        - 🟢 **50-59% (Light Yellow)**: Some overlap - normal for same questions
                                        - 🟢 **<50% (Green)**: Unique answers - no concern
                                        
                                        **What to do:**
                                        - **80%+**: Review both answers immediately - very likely copying
                                        - **70-79%**: Compare answers manually - probable collaboration
                                        - **60-69%**: Check for unusual patterns - possible similarity
                                        - **<60%**: Generally acceptable - students thinking similarly
                                        
                                        **Detection Methods:**
                                        - Word-level semantic matching (TF-IDF)
                                        - Character-level analysis (catches paraphrasing)
                                        - Direct word overlap (catches copying)
                                        - Combined scoring for maximum accuracy
                                        
                                        **Note:** The algorithm is sensitive - some similarity is normal when answering 
                                        the same questions. Focus on pairs with 70%+ similarity.
                                        """)
                                else:
                                    st.warning("Could not calculate similarity. Answers may be too short or identical.")
                        else:
                            st.info("Need at least 2 students to perform similarity analysis")
                    
                    except ImportError:
                        st.error("❌ Similarity module not found. Make sure similarity_analysis.py is in the folder.")
                    except Exception as e:
                        st.error(f"Error in similarity analysis: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                
                # TAB 3: AI WRITING DETECTOR
                with tab_ai_detector:
                    try:
                        from similarity_analysis import AIWritingDetector
                        
                        detector = AIWritingDetector()
                        
                        st.markdown("### 🤖 AI-Generated Answer Detection")
                        st.info("💡 Detects if students used ChatGPT/AI to write their answers")
                        
                        flagged_students = []
                        
                        with st.spinner("🤖 Analyzing writing patterns..."):
                            for student in students:
                                student_name = student['student_name']
                                answers = student['answers']
                                
                                # Combine all answers
                                combined_answer = " ".join([str(ans) for ans in answers.values()])
                                
                                # Analyze
                                analysis = detector.analyze_answer(combined_answer)
                                
                                if analysis['is_ai_likely']:
                                    flagged_students.append({
                                        'name': student_name,
                                        'confidence': analysis['confidence'],
                                        'level': analysis['confidence_level'],
                                        'indicators': analysis['indicators'],
                                        'recommendation': analysis['recommendation']
                                    })
                        
                        # Show results
                        if flagged_students:
                            st.warning(f"⚠️ {len(flagged_students)} student(s) flagged for potential AI use")
                            
                            st.markdown("#### 🚨 Flagged Students")
                            
                            for student in flagged_students:
                                with st.expander(
                                    f"**{student['name']}** - {student['confidence']}% AI likelihood ({student['level']})",
                                    expanded=True
                                ):
                                    # Confidence bar
                                    confidence_color = "#ff4444" if student['confidence'] >= 75 else "#ff8844"
                                    st.markdown(f"**AI Confidence:** {student['confidence']}%")
                                    st.progress(student['confidence'] / 100)
                                    
                                    st.markdown(f"**Recommendation:** {student['recommendation']}")
                                    
                                    st.markdown("**AI Indicators Detected:**")
                                    for indicator in student['indicators']:
                                        st.write(f"• {indicator}")
                        else:
                            st.success("✅ No AI-generated answers detected! All submissions appear authentic.")
                        
                        st.markdown("---")
                        
                        # Detection methodology
                        with st.expander("🔬 How AI Detection Works"):
                            st.markdown("""
                            **Multi-Layer Analysis:**
                            
                            1. **Formal Transitions**
                               - Checks for AI-typical words: "furthermore", "moreover", "consequently"
                               - AI tends to overuse formal connectors
                            
                            2. **Perfect Grammar**
                               - Detects lack of contractions ("don't", "can't")
                               - AI rarely makes typos or uses informal language
                            
                            3. **Sentence Structure**
                               - Analyzes consistency in sentence length
                               - AI produces very uniform sentences
                            
                            4. **Over-Structuring**
                               - Detects "intro-body-conclusion" in short answers
                               - AI over-organizes even brief responses
                            
                            5. **Vocabulary Sophistication**
                               - Checks for unusually complex words
                               - AI often uses higher-level vocabulary
                            
                            6. **AI-Specific Phrases**
                               - Identifies phrases like "it is important to note"
                               - Common in AI outputs, rare in student writing
                            
                            **Scoring:**
                            - 75%+: High likelihood of AI use
                            - 60-74%: Possible AI use
                            - 40-59%: Some AI indicators
                            - <40%: Appears authentic
                            
                            **Note:** This is a detection tool, not proof. Use it to guide conversations with students.
                            """)
                        
                    except ImportError:
                        st.error("❌ AI Detection module not found. Make sure similarity_analysis.py is in the folder.")
                    except Exception as e:
                        st.error(f"Error in AI detection: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

# ===== DISPLAY RESULTS =====

# ===== SINGLE QUESTION RESULTS =====
if 'evaluation_result' in st.session_state and st.session_state.assignment_mode == "single":
    result = st.session_state.evaluation_result
    mode = st.session_state.evaluation_mode_used
    edited_rubric = st.session_state.evaluated_rubric
    
    st.success("✅ Evaluation Complete!")
    st.subheader("📊 Evaluation Results")
    
    # Show evaluation mode used
    mode_badges = {
        "strict": "🔴 STRICT MODE",
        "moderate": "🟡 MODERATE MODE", 
        "lenient": "🟢 LENIENT MODE"
    }
    st.markdown(f"**Evaluation Mode:** {mode_badges.get(mode.lower(), mode.upper())}")
    st.markdown("---")
    
    try:
        parsed = json.loads(result)
        
        # Check for API errors
        if "error" in parsed:
            st.error(f"❌ {parsed['error']}")
        else:
            # Calculate percentage and performance metrics
            total_score = parsed["total_score"]
            
            # Calculate max score from scores array
            score_data = calculate_total_score(parsed["scores"])
            max_score = score_data["max"]
            
            percentage = calculate_percentage(total_score, max_score)
            performance_label = get_performance_label(percentage)
            performance_emoji = get_performance_emoji(performance_label)
            
            # 🔢 Total Score with Progress Bar
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.metric(
                    "🎯 Total Score", 
                    format_score_display(total_score, max_score)
                )
            
            with col2:
                st.metric("📊 Percentage", f"{percentage}%")
            
            with col3:
                st.metric("🏆 Grade", f"{performance_emoji} {performance_label}")
            
            # Progress bar
            st.progress(percentage / 100)
            
            st.markdown("---")
            
            # Show rubric used (ONLY FOR SINGLE QUESTION)
            st.markdown("### 📋 Rubric Used")
            st.dataframe(edited_rubric, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # 📋 Criterion Breakdown with individual progress bars (ONLY FOR SINGLE QUESTION)
            st.markdown("### 📋 Criterion Breakdown")
            for item in parsed["scores"]:
                criterion_percentage = calculate_percentage(
                    item['awarded'], 
                    item['max']
                )
                criterion_label = get_performance_label(criterion_percentage)
                criterion_emoji = get_performance_emoji(criterion_label)
                
                with st.expander(
                    f"**{item['criterion']}** - {criterion_emoji} {format_score_display(item['awarded'], item['max'])} ({criterion_percentage}%)", 
                    expanded=True
                ):
                    # Progress bar for this criterion
                    st.progress(criterion_percentage / 100)
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.metric("Score", format_score_display(item['awarded'], item['max']))
                        st.caption(f"{criterion_label}")
                    with col2:
                        st.write(f"**Reason:** {item['reason']}")
            
            st.markdown("---")
            
            # 📝 Feedback
            st.markdown("### 📝 Feedback")
            for fb in parsed["feedback"]:
                st.write(f"• {fb}")
            
            st.markdown("---")
            
            # 🎯 AI Confidence Meter
            st.markdown("### 🎯 AI Confidence Analysis")
            
            try:
                from similarity_analysis import ConfidenceAnalyzer
                
                conf_analyzer = ConfidenceAnalyzer()
                
                # Prepare evaluation data
                answer_text = st.session_state.get('answer_input', answer)
                eval_data = {
                    'answer_length': len(answer_text),
                    'scores': parsed.get('scores', []),
                    'feedback': parsed.get('feedback', []),
                    'total_score': parsed.get('total_score', 0)
                }
                
                # Calculate confidence
                confidence_result = conf_analyzer.calculate_confidence(eval_data)
                
                # Display confidence meter
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.metric(
                        "Confidence Score", 
                        f"{confidence_result['confidence_score']}%",
                        delta=confidence_result['confidence_level']
                    )
                    
                    # Color-coded indicator
                    st.markdown(
                        f"<div style='background-color: {confidence_result['color']}; "
                        f"padding: 10px; border-radius: 5px; text-align: center; color: black;'>"
                        f"<b>{confidence_result['recommendation']}</b></div>",
                        unsafe_allow_html=True
                    )
                
                with col2:
                    # Progress bar
                    st.progress(confidence_result['confidence_score'] / 100)
                    
                    st.markdown("**Analysis Factors:**")
                    for reason in confidence_result['reasons']:
                        st.caption(f"• {reason}")
                
                # Show review flag if needed
                if confidence_result['needs_review']:
                    st.warning("⚠️ **Manual Review Recommended** - AI flagged this evaluation for human verification")
                else:
                    st.success("✅ **High Confidence** - This grade can be trusted")
                
            except ImportError:
                # Fallback to basic confidence
                confidence = parsed.get("confidence", "N/A")
                st.info(f"Basic Confidence Level: {confidence}")
            except Exception as e:
                st.warning(f"Could not calculate advanced confidence: {str(e)}")
        
    except json.JSONDecodeError:
        st.error("❌ Model did not return valid JSON.")
        st.write("**Raw Output:**")
        st.code(result)
    except KeyError as e:
        st.error(f"❌ Missing expected field in response: {e}")
        st.write("**Raw Output:**")
        st.code(result)
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.write("**Raw Output:**")
        st.code(result)

# ===== MULTI-QUESTION RESULTS DISPLAY =====
if 'multi_evaluation_results' in st.session_state and st.session_state.assignment_mode == "multi":
    st.success("✅ All Questions Evaluated!")
    st.subheader("📊 Assignment Evaluation Results")
    
    mode = st.session_state.evaluation_mode_used
    mode_badges = {
        "strict": "🔴 STRICT MODE",
        "moderate": "🟡 MODERATE MODE", 
        "lenient": "🟢 LENIENT MODE"
    }
    st.markdown(f"**Evaluation Mode:** {mode_badges.get(mode.lower(), mode.upper())}")
    st.markdown(f"**Assignment:** {st.session_state.evaluated_assignment['title']}")
    st.markdown("---")
    
    # Calculate overall metrics
    combined = st.session_state.multi_combined_results
    total_score = combined['total_score']
    total_max = combined['total_max']
    percentage = calculate_percentage(total_score, total_max)
    performance_label = get_performance_label(percentage)
    performance_emoji = get_performance_emoji(performance_label)
    
    # Overall Score Display
    st.markdown("### 🎯 Overall Performance")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.metric(
            "🎯 Total Score", 
            format_score_display(total_score, total_max)
        )
    
    with col2:
        st.metric("📊 Percentage", f"{percentage}%")
    
    with col3:
        st.metric("🏆 Grade", f"{performance_emoji} {performance_label}")
    
    # Progress bar
    st.progress(percentage / 100)
    
    st.markdown("---")
    
    # Individual Question Results
    st.markdown("### 📝 Individual Question Results")
    
    for result in st.session_state.multi_evaluation_results:
        if 'error' not in result:
            q_num = result['question_number']
            q_text = result['question_text']
            q_score = result['total_score']
            
            # Calculate max for this question
            q_max = sum(item.get('max', 0) for item in result.get('scores', []))
            q_percentage = calculate_percentage(q_score, q_max)
            q_label = get_performance_label(q_percentage)
            q_emoji = get_performance_emoji(q_label)
            
            with st.expander(
                f"**Question {q_num}** - {q_emoji} {format_score_display(q_score, q_max)} ({q_percentage}%)",
                expanded=False
            ):
                st.write(f"**Question:** {q_text}")
                st.progress(q_percentage / 100)
                
                # Feedback for this question
                if result.get('feedback'):
                    st.markdown("#### 📝 Feedback")
                    for fb in result['feedback']:
                        st.write(f"• {fb}")
                
                # Confidence
                if result.get('confidence'):
                    st.info(f"**Confidence:** {result['confidence']}")
        else:
            # Error in this question's evaluation
            st.error(f"❌ Question {result['question_number']} evaluation failed")
            st.code(result['error'])
    
    st.markdown("---")
    
    # Combined Feedback Summary
    st.markdown("### 📋 Overall Feedback Summary")
    all_feedback = combined.get('combined_feedback', [])
    if all_feedback:
        for fb in all_feedback[:10]:  # Limit to 10 feedback points
            st.write(f"• {fb}")
    else:
        st.write("No combined feedback available.")
    
    # Show assignment statistics if assignment is saved
    if st.session_state.current_assignment_id:
        st.markdown("---")
        st.markdown("### 📊 Assignment Statistics")
        
        try:
            stats = st.session_state.db.get_assignment_statistics(st.session_state.current_assignment_id)
            
            if stats['total_evaluations'] > 0:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Evaluations", stats['total_evaluations'])
                with col2:
                    st.metric("Average %", f"{stats['avg_percentage']}%")
                with col3:
                    st.metric("Highest %", f"{stats['max_percentage']}%")
                with col4:
                    st.metric("Lowest %", f"{stats['min_percentage']}%")
            else:
                st.info("This is the first evaluation for this assignment.")
        except Exception as e:
            st.warning(f"Could not load statistics: {str(e)}")

# ===== MODEL ANSWER KEY GENERATION =====
if st.session_state.assignment_mode == "multi" and st.session_state.assignment.get_question_count() > 0:
    st.markdown("---")
    st.subheader("📚 Generate Model Answer Key")
    
    if st.button("🎯 Generate", type="primary", use_container_width=True, key="generate_model_answers"):
        st.session_state.generate_model_key = True
        st.rerun()
    
    # Generate and display model answers
    if st.session_state.get('generate_model_key', False):
        with st.spinner("🤖 Generating model answers..."):
            from prompts import build_model_answer_prompt
            
            model_answers = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Generate answer for each question
            for idx, q_data in enumerate(st.session_state.assignment.questions):
                q_num = q_data['question_number']
                q_text = q_data['question_text']
                
                status_text.text(f"Generating model answer for Question {q_num}/{st.session_state.assignment.get_question_count()}...")
                progress_bar.progress((idx) / st.session_state.assignment.get_question_count())
                
                # Format rubric
                rubric_formatted = st.session_state.assignment.format_rubric_for_evaluation()
                
                # Build model answer prompt
                prompt = build_model_answer_prompt(q_text, rubric_formatted)
                
                # Generate using evaluator (with moderate temperature for quality)
                evaluator.temperature = 0.4  # Balanced for quality answers
                model_answer = evaluator.evaluate(prompt)
                
                model_answers.append({
                    'question_number': q_num,
                    'question_text': q_text,
                    'model_answer': model_answer,
                    'max_marks': st.session_state.assignment.max_marks_per_question
                })
            
            progress_bar.progress(1.0)
            status_text.text("✅ Model answer key generated!")
            
            # Store in session state
            st.session_state.model_answers = model_answers
        
        # Display model answers
        if 'model_answers' in st.session_state:
            st.success("✅ Model Answer Key Generated!")
            
            # Download button
            st.markdown("### 📥 Download Options")
            
            # Create formatted document
            doc_content = f"""MODEL ANSWER KEY
{st.session_state.assignment.assignment_title or 'Assignment'}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'='*80}

RUBRIC:
{st.session_state.assignment.format_rubric_for_evaluation()}

Maximum marks per question: {st.session_state.assignment.max_marks_per_question}
Total assignment marks: {st.session_state.assignment.get_total_marks()}

{'='*80}

"""
            
            for ans in st.session_state.model_answers:
                doc_content += f"""
QUESTION {ans['question_number']}:
{ans['question_text']}

MODEL ANSWER:
{ans['model_answer']}

Maximum Marks: {ans['max_marks']}

{'-'*80}

"""
            
            # Download as text file
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📄 Download as Text",
                    data=doc_content,
                    file_name=f"model_answers_{st.session_state.assignment.assignment_title.replace(' ', '_') if st.session_state.assignment.assignment_title else 'assignment'}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # Download as markdown
                md_content = f"""# Model Answer Key\n\n**{st.session_state.assignment.assignment_title or 'Assignment'}**  \n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n---\n\n## Rubric\n\n{st.session_state.assignment.format_rubric_for_evaluation()}\n\n**Maximum marks per question:** {st.session_state.assignment.max_marks_per_question}  \n**Total assignment marks:** {st.session_state.assignment.get_total_marks()}\n\n---\n\n"""
                
                for ans in st.session_state.model_answers:
                    md_content += f"""## Question {ans['question_number']}\n\n**Question:** {ans['question_text']}\n\n**Model Answer:**\n\n{ans['model_answer']}\n\n**Maximum Marks:** {ans['max_marks']}\n\n---\n\n"""
                
                st.download_button(
                    "📝 Download as Markdown",
                    data=md_content,
                    file_name=f"model_answers_{st.session_state.assignment.assignment_title.replace(' ', '_') if st.session_state.assignment.assignment_title else 'assignment'}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            st.markdown("---")
            
            # Display each model answer
            st.markdown("### 📖 Model Answers Preview")
            
            for ans in st.session_state.model_answers:
                with st.expander(f"**Question {ans['question_number']}** - {ans['question_text'][:50]}...", expanded=False):
                    st.markdown(f"**Question:** {ans['question_text']}")
                    st.markdown("**Model Answer:**")
                    st.write(ans['model_answer'])
                    st.caption(f"Maximum Marks: {ans['max_marks']}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <small>
        Built with ❤️ using Streamlit & Groq AI | 
        <a href='https://github.com/yourusername/rubriqai' target='_blank'>GitHub</a> | 
        Version 1.0.0
    </small>
</div>
""", unsafe_allow_html=True)