"""
test_hosting.py - Online Test Creation & Hosting System with Scheduling
Integrated into RubriqAI Streamlit app
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import random
import string
from datetime import datetime, timedelta
import io

class TestHosting:
    def __init__(self, db_path='rubriqai.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize test hosting tables with scheduling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Online tests table with scheduling
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS online_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                subject TEXT,
                duration_minutes INTEGER DEFAULT 60,
                rubric TEXT NOT NULL,
                questions TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                starts_at TIMESTAMP,
                closes_at TIMESTAMP,
                status TEXT DEFAULT 'draft',
                total_submissions INTEGER DEFAULT 0,
                teacher_notes TEXT
            )
        ''')
        
        # Test submissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS online_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_code TEXT NOT NULL,
                student_name TEXT NOT NULL,
                student_email TEXT,
                answers TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_taken_minutes INTEGER,
                FOREIGN KEY (test_code) REFERENCES online_tests(test_code)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_test_code(self):
        """Generate unique test code"""
        year = datetime.now().year
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"TEST-{year}-{random_part}"
    
    def create_test(self, title, subject, duration, rubric_df, questions_list, starts_at=None, closes_at=None, teacher_notes=''):
        """Create a new online test with scheduling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        test_code = self.generate_test_code()
        
        # Convert rubric to dict
        rubric = rubric_df.to_dict('records')
        
        # Convert questions to list of dicts
        questions = [
            {"number": i+1, "text": q} 
            for i, q in enumerate(questions_list)
        ]
        
        # Determine status based on times
        now = datetime.now()
        if starts_at and starts_at > now:
            status = 'scheduled'
        elif closes_at and closes_at < now:
            status = 'closed'
        elif starts_at is None and closes_at is None:
            status = 'active'  # Immediate start if no times set
        else:
            status = 'active'
        
        cursor.execute('''
            INSERT INTO online_tests 
            (test_code, title, subject, duration_minutes, rubric, questions, 
             starts_at, closes_at, status, teacher_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_code,
            title,
            subject,
            duration,
            json.dumps(rubric),
            json.dumps(questions),
            starts_at.isoformat() if starts_at else None,
            closes_at.isoformat() if closes_at else None,
            status,
            teacher_notes
        ))
        
        conn.commit()
        conn.close()
        
        return test_code
    
    def get_test(self, test_code):
        """Retrieve test by code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, subject, duration_minutes, rubric, questions, 
                   status, starts_at, closes_at, total_submissions
            FROM online_tests
            WHERE test_code = ?
        ''', (test_code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'title': row[0],
                'subject': row[1],
                'duration': row[2],
                'rubric': json.loads(row[3]),
                'questions': json.loads(row[4]),
                'status': row[5],
                'starts_at': row[6],
                'closes_at': row[7],
                'total_submissions': row[8]
            }
        return None
    
    def update_test_status(self):
        """Update test statuses based on current time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Set scheduled tests to active if start time passed
        cursor.execute('''
            UPDATE online_tests
            SET status = 'active'
            WHERE status = 'scheduled' AND starts_at <= ?
        ''', (now,))
        
        # Set active tests to closed if end time passed
        cursor.execute('''
            UPDATE online_tests
            SET status = 'closed'
            WHERE status = 'active' AND closes_at <= ? AND closes_at IS NOT NULL
        ''', (now,))
        
        conn.commit()
        conn.close()
    
    def submit_answers(self, test_code, student_name, student_email, answers, time_taken):
        """Student submits answers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO online_submissions
            (test_code, student_name, student_email, answers, time_taken_minutes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            test_code,
            student_name,
            student_email or '',
            json.dumps(answers),
            time_taken
        ))
        
        # Update submission count
        cursor.execute('''
            UPDATE online_tests
            SET total_submissions = total_submissions + 1
            WHERE test_code = ?
        ''', (test_code,))
        
        conn.commit()
        conn.close()
    
    def get_submissions(self, test_code):
        """Get all submissions for a test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_name, student_email, answers, submitted_at, time_taken_minutes
            FROM online_submissions
            WHERE test_code = ?
            ORDER BY submitted_at DESC
        ''', (test_code,))
        
        rows = cursor.fetchall()
        conn.close()
        
        submissions = []
        for row in rows:
            submissions.append({
                'student_name': row[0],
                'student_email': row[1],
                'answers': json.loads(row[2]),
                'submitted_at': row[3],
                'time_taken': row[4]
            })
        
        return submissions
    
    def export_to_csv(self, test_code):
        """Export test + submissions to CSV format for RubriqAI"""
        test = self.get_test(test_code)
        if not test:
            return None
        
        submissions = self.get_submissions(test_code)
        
        csv_lines = []
        
        # CRITERIA section
        csv_lines.append("CRITERIA,TOTAL MARKS")
        for criterion in test['rubric']:
            csv_lines.append(f"{criterion['CRITERIA']},{criterion['TOTAL MARKS']}")
        
        # QUESTIONS section
        csv_lines.append("QUESTIONS,")
        for q in test['questions']:
            question_text = q['text'].replace('"', '""')
            csv_lines.append(f'{q["number"]},"{question_text}"')
        
        # STUDENTS section
        csv_lines.append("STUDENTS,")
        for sub in submissions:
            student_name = sub['student_name']
            answer_values = []
            for q in test['questions']:
                answer = sub['answers'].get(str(q['number']), '')
                answer = answer.replace('"', '""')
                answer_values.append(f'"{answer}"')
            
            csv_lines.append(f"{student_name}," + ",".join(answer_values))
        
        csv_content = "\n".join(csv_lines)
        return csv_content, test['title']
    
    def get_all_tests(self):
        """Get all tests created"""
        self.update_test_status()  # Update statuses first
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT test_code, title, subject, total_submissions, 
                   created_at, status, starts_at, closes_at
            FROM online_tests
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        tests = []
        for row in rows:
            tests.append({
                'test_code': row[0],
                'title': row[1],
                'subject': row[2],
                'submissions': row[3],
                'created_at': row[4],
                'status': row[5],
                'starts_at': row[6],
                'closes_at': row[7]
            })
        
        return tests
    
    def manually_close_test(self, test_code):
        """Manually close test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE online_tests
            SET status = 'closed', closes_at = ?
            WHERE test_code = ?
        ''', (datetime.now().isoformat(), test_code))
        
        conn.commit()
        conn.close()
    
    def activate_test(self, test_code):
        """Manually activate a test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE online_tests
            SET status = 'active', starts_at = ?
            WHERE test_code = ?
        ''', (datetime.now().isoformat(), test_code))
        
        conn.commit()
        conn.close()


# Streamlit UI Components

def render_teacher_test_creator():
    """UI for teachers to create online tests with scheduling"""
    st.subheader("📝 Create Online Test")
    
    hosting = TestHosting()
    
    with st.form("create_test_form"):
        st.write("**Basic Information:**")
        title = st.text_input("Test Title *", placeholder="Biology Midterm Exam")
        
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject", placeholder="Biology")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=5, max_value=180, value=60)
        
        st.markdown("---")
        st.write("**Scheduling (Optional):**")
        
        schedule_test = st.checkbox("Schedule test for later")
        
        starts_at = None
        closes_at = None
        
        if schedule_test:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now())
                start_time = st.time_input("Start Time", value=datetime.now().time())
                starts_at = datetime.combine(start_date, start_time)
            
            with col2:
                end_date = st.date_input("End Date", value=datetime.now() + timedelta(days=1))
                end_time = st.time_input("End Time", value=datetime.now().time())
                closes_at = datetime.combine(end_date, end_time)
        else:
            st.info("💡 Test will go live immediately and stay open until manually closed")
        
        st.markdown("---")
        st.write("**Questions:**")
        
        num_questions = st.number_input("Number of questions", min_value=1, max_value=20, value=3)
        
        questions = []
        for i in range(num_questions):
            q = st.text_area(f"Question {i+1} *", key=f"q_{i}", placeholder="Enter your question here...")
            if q.strip():
                questions.append(q.strip())
        
        st.markdown("---")
        st.write("**Rubric:**")
        
        if 'temp_rubric' not in st.session_state:
            st.session_state.temp_rubric = pd.DataFrame({
                "CRITERIA": ["Understanding", "Accuracy"],
                "TOTAL MARKS": [5, 5]
            })
        
        rubric_df = st.data_editor(
            st.session_state.temp_rubric,
            num_rows="dynamic",
            use_container_width=True
        )
        
        st.markdown("---")
        teacher_notes = st.text_area("Notes (optional)", placeholder="Internal notes about this test...")
        
        submitted = st.form_submit_button("🚀 Create Test", type="primary", use_container_width=True)
        
        if submitted:
            if not title or not questions:
                st.error("❌ Please enter title and at least one question!")
            elif rubric_df.empty or rubric_df['CRITERIA'].isna().any():
                st.error("❌ Please set up a valid rubric!")
            elif schedule_test and closes_at and closes_at <= starts_at:
                st.error("❌ End time must be after start time!")
            else:
                try:
                    test_code = hosting.create_test(
                        title, subject, duration, rubric_df, questions,
                        starts_at, closes_at, teacher_notes
                    )
                    
                    st.success("✅ Test created and saved!")
                    st.balloons()
                    
                    # Determine status message
                    test = hosting.get_test(test_code)
                    
                    st.markdown("---")
                    st.markdown(f"### 🎯 Test Code: `{test_code}`")
                    
                    if test['status'] == 'scheduled':
                        st.info(f"📅 **Scheduled** - Goes live on {starts_at.strftime('%Y-%m-%d at %H:%M')}")
                    elif test['status'] == 'active':
                        st.success(f"🟢 **LIVE NOW** - Students can take it immediately!")
                    
                    if closes_at:
                        st.warning(f"⏰ Closes on {closes_at.strftime('%Y-%m-%d at %H:%M')}")
                    
                    st.info(f"✅ {len(questions)} questions • {duration} minutes • {subject or 'General'}")
                    
                except Exception as e:
                    st.error(f"❌ Error creating test: {str(e)}")


def render_teacher_test_manager():
    """UI for teachers to manage tests"""
    st.subheader("📊 Manage Online Tests")
    
    hosting = TestHosting()
    tests = hosting.get_all_tests()
    
    if not tests:
        st.info("📝 No tests created yet. Go to 'Create Test' tab to make your first test!")
        return
    
    # Status filter
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**You have {len(tests)} test(s):**")
    with col2:
        status_filter = st.selectbox(
            "Filter",
            ["All", "Active", "Scheduled", "Closed"],
            label_visibility="collapsed"
        )
    
    # Filter tests
    if status_filter != "All":
        tests = [t for t in tests if t['status'] == status_filter.lower()]
    
    # Display tests
    for test in tests:
        status_emoji = {
            'active': '🟢',
            'scheduled': '🟡',
            'closed': '🔴',
            'draft': '⚪'
        }.get(test['status'], '⚪')
        
        with st.expander(f"{status_emoji} {test['title']} ({test['test_code']}) - {test['submissions']} submissions"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Code", test['test_code'])
            with col2:
                st.metric("Submissions", test['submissions'])
            with col3:
                st.metric("Status", f"{status_emoji} {test['status'].title()}")
            with col4:
                st.metric("Subject", test['subject'] or 'General')
            
            # Timing info
            if test['starts_at']:
                start = datetime.fromisoformat(test['starts_at'])
                st.caption(f"🕐 Starts: {start.strftime('%Y-%m-%d %H:%M')}")
            if test['closes_at']:
                close = datetime.fromisoformat(test['closes_at'])
                st.caption(f"🕐 Closes: {close.strftime('%Y-%m-%d %H:%M')}")
            
            st.caption(f"Created: {test['created_at']}")
            
            st.markdown("---")
            
            # Action buttons
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                if test['submissions'] > 0:
                    if st.button("📥 CSV", key=f"dl_{test['test_code']}", use_container_width=True):
                        csv_content, title = hosting.export_to_csv(test['test_code'])
                        
                        st.download_button(
                            label="💾 Download",
                            data=csv_content,
                            file_name=f"{title.replace(' ', '_')}_submissions.csv",
                            mime="text/csv",
                            key=f"dlbtn_{test['test_code']}",
                            use_container_width=True
                        )
            
            with col_b:
                if st.button("👥 View", key=f"view_{test['test_code']}", use_container_width=True):
                    submissions = hosting.get_submissions(test['test_code'])
                    
                    if submissions:
                        st.write("**Recent Submissions:**")
                        for i, sub in enumerate(submissions[:5], 1):
                            st.caption(f"{i}. {sub['student_name']} - {sub['submitted_at']}")
                        if len(submissions) > 5:
                            st.caption(f"... and {len(submissions) - 5} more")
                    else:
                        st.info("No submissions yet")
            
            with col_c:
                if test['status'] == 'active':
                    if st.button("🔒 Close", key=f"close_{test['test_code']}", use_container_width=True):
                        hosting.manually_close_test(test['test_code'])
                        st.success("Test closed!")
                        st.rerun()
                elif test['status'] == 'scheduled':
                    if st.button("▶️ Start Now", key=f"start_{test['test_code']}", use_container_width=True):
                        hosting.activate_test(test['test_code'])
                        st.success("Test activated!")
                        st.rerun()
            
            with col_d:
                if st.button("🔗 Share", key=f"share_{test['test_code']}", use_container_width=True):
                    st.code(test['test_code'])
                    st.caption("Give this code to students")


def render_right_sidebar():
    """Render right sidebar with live test info"""
    hosting = TestHosting()
    tests = hosting.get_all_tests()
    
    # Get active and scheduled tests
    active_tests = [t for t in tests if t['status'] == 'active']
    scheduled_tests = [t for t in tests if t['status'] == 'scheduled']
    
    st.markdown("### 📊 Live Tests")
    
    if active_tests:
        for test in active_tests[:3]:  # Show top 3
            with st.container():
                st.markdown(f"**🟢 {test['title']}**")
                st.caption(f"Code: `{test['test_code']}`")
                st.metric("Submissions", test['submissions'], delta=None)
                
                if test['closes_at']:
                    close_time = datetime.fromisoformat(test['closes_at'])
                    time_left = close_time - datetime.now()
                    hours_left = int(time_left.total_seconds() / 3600)
                    if hours_left < 2:
                        st.warning(f"⏰ Closes in {hours_left}h")
                
                st.markdown("---")
    else:
        st.info("No active tests")
    
    if scheduled_tests:
        st.markdown("### 🟡 Scheduled")
        for test in scheduled_tests[:2]:
            st.caption(f"{test['title']}")
            start = datetime.fromisoformat(test['starts_at'])
            st.caption(f"Starts: {start.strftime('%m/%d %H:%M')}")
            st.markdown("---")
    
    # Quick stats
    st.markdown("### 📈 Stats")
    total_submissions = sum(t['submissions'] for t in tests)
    st.metric("Total Submissions", total_submissions)
    st.metric("Total Tests", len(tests))

    def __init__(self, db_path='rubriqai.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize test hosting tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Online tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS online_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                subject TEXT,
                duration_minutes INTEGER DEFAULT 60,
                rubric TEXT NOT NULL,
                questions TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                total_submissions INTEGER DEFAULT 0
            )
        ''')
        
        # Test submissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS online_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_code TEXT NOT NULL,
                student_name TEXT NOT NULL,
                student_email TEXT,
                answers TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_taken_minutes INTEGER,
                FOREIGN KEY (test_code) REFERENCES online_tests(test_code)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_test_code(self):
        """Generate unique test code"""
        year = datetime.now().year
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"TEST-{year}-{random_part}"
    
    def create_test(self, title, subject, duration, rubric_df, questions_list):
        """Create a new online test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        test_code = self.generate_test_code()
        
        # Convert rubric to dict
        rubric = rubric_df.to_dict('records')
        
        # Convert questions to list of dicts
        questions = [
            {"number": i+1, "text": q} 
            for i, q in enumerate(questions_list)
        ]
        
        cursor.execute('''
            INSERT INTO online_tests 
            (test_code, title, subject, duration_minutes, rubric, questions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            test_code,
            title,
            subject,
            duration,
            json.dumps(rubric),
            json.dumps(questions)
        ))
        
        conn.commit()
        conn.close()
        
        return test_code
    
    def get_test(self, test_code):
        """Retrieve test by code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, subject, duration_minutes, rubric, questions, status
            FROM online_tests
            WHERE test_code = ?
        ''', (test_code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'title': row[0],
                'subject': row[1],
                'duration': row[2],
                'rubric': json.loads(row[3]),
                'questions': json.loads(row[4]),
                'status': row[5]
            }
        return None
    
    def submit_answers(self, test_code, student_name, student_email, answers, time_taken):
        """Student submits answers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO online_submissions
            (test_code, student_name, student_email, answers, time_taken_minutes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            test_code,
            student_name,
            student_email or '',
            json.dumps(answers),
            time_taken
        ))
        
        # Update submission count
        cursor.execute('''
            UPDATE online_tests
            SET total_submissions = total_submissions + 1
            WHERE test_code = ?
        ''', (test_code,))
        
        conn.commit()
        conn.close()
    
    def get_submissions(self, test_code):
        """Get all submissions for a test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_name, student_email, answers, submitted_at, time_taken_minutes
            FROM online_submissions
            WHERE test_code = ?
            ORDER BY submitted_at DESC
        ''', (test_code,))
        
        rows = cursor.fetchall()
        conn.close()
        
        submissions = []
        for row in rows:
            submissions.append({
                'student_name': row[0],
                'student_email': row[1],
                'answers': json.loads(row[2]),
                'submitted_at': row[3],
                'time_taken': row[4]
            })
        
        return submissions
    
    def export_to_csv(self, test_code):
        """Export test + submissions to CSV format for RubriqAI"""
        test = self.get_test(test_code)
        if not test:
            return None
        
        submissions = self.get_submissions(test_code)
        
        csv_lines = []
        
        # CRITERIA section
        csv_lines.append("CRITERIA,TOTAL MARKS")
        for criterion in test['rubric']:
            csv_lines.append(f"{criterion['CRITERIA']},{criterion['TOTAL MARKS']}")
        
        # QUESTIONS section
        csv_lines.append("QUESTIONS,")
        for q in test['questions']:
            # Escape quotes in question text
            question_text = q['text'].replace('"', '""')
            csv_lines.append(f'{q["number"]},"{question_text}"')
        
        # STUDENTS section
        csv_lines.append("STUDENTS,")
        for sub in submissions:
            student_name = sub['student_name']
            # Get answers in order of questions
            answer_values = []
            for q in test['questions']:
                answer = sub['answers'].get(str(q['number']), '')
                # Escape quotes and wrap in quotes
                answer = answer.replace('"', '""')
                answer_values.append(f'"{answer}"')
            
            csv_lines.append(f"{student_name}," + ",".join(answer_values))
        
        csv_content = "\n".join(csv_lines)
        return csv_content, test['title']
    
    def get_all_tests(self):
        """Get all tests created"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT test_code, title, subject, total_submissions, created_at, status
            FROM online_tests
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        tests = []
        for row in rows:
            tests.append({
                'test_code': row[0],
                'title': row[1],
                'subject': row[2],
                'submissions': row[3],
                'created_at': row[4],
                'status': row[5]
            })
        
        return tests
    
    def close_test(self, test_code):
        """Close test (stop accepting submissions)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE online_tests
            SET status = 'closed'
            WHERE test_code = ?
        ''', (test_code,))
        
        conn.commit()
        conn.close()


# Streamlit UI Components

def render_teacher_test_creator():
    """UI for teachers to create online tests"""
    st.subheader("📝 Create Online Test")
    st.info("💡 Create a test, get a code, students take it online, you get automatic CSV!")
    
    hosting = TestHosting()
    
    with st.form("create_test_form"):
        title = st.text_input("Test Title", placeholder="Biology Midterm Exam")
        
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject", placeholder="Biology")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=5, max_value=180, value=60)
        
        st.markdown("---")
        st.write("**Add Questions:**")
        
        num_questions = st.number_input("Number of questions", min_value=1, max_value=20, value=3)
        
        questions = []
        for i in range(num_questions):
            q = st.text_area(f"Question {i+1}", key=f"q_{i}", placeholder="Enter your question here...")
            if q.strip():
                questions.append(q.strip())
        
        st.markdown("---")
        st.write("**Set Rubric:**")
        
        if 'temp_rubric' not in st.session_state:
            st.session_state.temp_rubric = pd.DataFrame({
                "CRITERIA": ["Understanding", "Accuracy"],
                "TOTAL MARKS": [5, 5]
            })
        
        rubric_df = st.data_editor(
            st.session_state.temp_rubric,
            num_rows="dynamic",
            use_container_width=True
        )
        
        submitted = st.form_submit_button("🚀 Create & Publish Test", type="primary")
        
        if submitted:
            if not title or not questions:
                st.error("Please enter title and at least one question!")
            elif rubric_df.empty or rubric_df['CRITERIA'].isna().any():
                st.error("Please set up a valid rubric!")
            else:
                try:
                    test_code = hosting.create_test(title, subject, duration, rubric_df, questions)
                    
                    st.success(f"✅ Test created successfully!")
                    st.balloons()
                    
                    # Show test code prominently
                    st.markdown("---")
                    st.markdown(f"### 🎯 Share this code with students:")
                    st.code(test_code, language=None)
                    
                    st.info(f"📊 Students can access at: Student Mode (change to Student tab)")
                    st.info(f"✅ {len(questions)} questions • {duration} minutes • {subject or 'General'}")
                    
                except Exception as e:
                    st.error(f"Error creating test: {str(e)}")


def render_teacher_test_manager():
    """UI for teachers to manage and download submissions"""
    st.subheader("📊 Manage Online Tests")
    
    hosting = TestHosting()
    tests = hosting.get_all_tests()
    
    if not tests:
        st.info("📝 No tests created yet. Create your first test above!")
        return
    
    st.write(f"**You have {len(tests)} test(s):**")
    
    for test in tests:
        with st.expander(f"📋 {test['title']} ({test['test_code']}) - {test['submissions']} submissions"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Code", test['test_code'])
            with col2:
                st.metric("Submissions", test['submissions'])
            with col3:
                status_emoji = "🟢" if test['status'] == 'active' else "🔴"
                st.metric("Status", f"{status_emoji} {test['status'].title()}")
            
            st.caption(f"Created: {test['created_at']} • Subject: {test['subject'] or 'N/A'}")
            
            # Action buttons
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if test['submissions'] > 0:
                    csv_content, title = hosting.export_to_csv(test['test_code'])
                    
                    if csv_content:
                        st.download_button(
                            label="📥 CSV",
                            data=csv_content,
                            file_name=f"{title.replace(' ', '_')}_submissions.csv",
                            mime="text/csv",
                            key=f"dlbtn_{test['test_code']}",
                            use_container_width=True
                        )
            
            with col_b:
                if st.button("👥 View Submissions", key=f"view_{test['test_code']}"):
                    submissions = hosting.get_submissions(test['test_code'])
                    
                    if submissions:
                        st.write("**Submissions:**")
                        for i, sub in enumerate(submissions, 1):
                            st.write(f"{i}. {sub['student_name']} - {sub['submitted_at']}")
                    else:
                        st.info("No submissions yet")
            
            with col_c:
                if test['status'] == 'active':
                    if st.button("🔒 Close", key=f"close_{test['test_code']}", use_container_width=True):
                        hosting.manually_close_test(test['test_code'])
                        st.success("Test closed!")
                        st.rerun()
                elif test['status'] == 'scheduled':
                    if st.button("▶️ Start Now", key=f"start_{test['test_code']}", use_container_width=True):
                        hosting.activate_test(test['test_code'])
                        st.success("Test activated!")
                        st.rerun()


def render_student_test_interface():
    """UI for students to take tests"""
    st.subheader("🎓 Student: Take Test")
    
    hosting = TestHosting()
    
    # Step 1: Enter test code
    if 'test_loaded' not in st.session_state:
        st.session_state.test_loaded = False
        st.session_state.test_started = False
    
    if not st.session_state.test_loaded:
        st.write("Enter the test code provided by your teacher:")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            test_code = st.text_input("Test Code", placeholder="TEST-2024-XXXX").strip().upper()
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("Load Test", type="primary"):
                if test_code:
                    test = hosting.get_test(test_code)
                    if test:
                        if test['status'] != 'active':
                            st.error("❌ This test is no longer accepting submissions")
                        else:
                            st.session_state.current_test = test
                            st.session_state.current_test_code = test_code
                            st.session_state.test_loaded = True
                            st.rerun()
                    else:
                        st.error("❌ Invalid test code. Please check and try again.")
                else:
                    st.warning("Please enter a test code")
        
        return
    
    # Step 2: Show test info and start
    test = st.session_state.current_test
    
    if not st.session_state.test_started:
        st.success(f"✅ Test found: **{test['title']}**")
        
        # Test details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Subject", test['subject'] or 'General')
        with col2:
            st.metric("Questions", len(test['questions']))
        with col3:
            st.metric("Duration", f"{test['duration']} min")
        
        st.markdown("---")
        
        # Student info
        st.write("**Enter your details:**")
        student_name = st.text_input("Your Full Name *", key="student_name")
        student_email = st.text_input("Email (optional)", key="student_email")
        
        if st.button("🚀 Start Test", type="primary"):
            if student_name.strip():
                st.session_state.student_name = student_name
                st.session_state.student_email = student_email
                st.session_state.test_started = True
                st.session_state.start_time = datetime.now()
                st.session_state.test_answers = {}
                st.rerun()
            else:
                st.error("Please enter your name")
        
        return
    
    # Step 3: Taking test
    st.success(f"📝 Taking: **{test['title']}**")
    st.caption(f"Student: {st.session_state.student_name}")
    
    # Timer
    elapsed = (datetime.now() - st.session_state.start_time).seconds // 60
    remaining = test['duration'] - elapsed
    
    if remaining > 0:
        col1, col2 = st.columns([4, 1])
        with col2:
            if remaining <= 5:
                st.error(f"⏰ {remaining} min left")
            else:
                st.info(f"⏰ {remaining} min left")
    
    st.markdown("---")
    
    # Questions
    for q in test['questions']:
        st.write(f"**Question {q['number']}:**")
        st.write(q['text'])
        
        answer = st.text_area(
            "Your answer:",
            key=f"answer_{q['number']}",
            height=150,
            placeholder="Type your answer here..."
        )
        
        st.session_state.test_answers[str(q['number'])] = answer
        st.markdown("---")
    
    # Submit
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✅ Submit Test", type="primary", use_container_width=True):
            # Check if all questions answered
            unanswered = [
                q['number'] for q in test['questions'] 
                if not st.session_state.test_answers.get(str(q['number']), '').strip()
            ]
            
            if unanswered:
                st.warning(f"⚠️ Questions {', '.join(map(str, unanswered))} are empty. Submit anyway?")
                if st.button("Yes, Submit", type="secondary"):
                    submit_test(hosting)
            else:
                submit_test(hosting)


def submit_test(hosting):
    """Handle test submission"""
    time_taken = (datetime.now() - st.session_state.start_time).seconds // 60
    
    hosting.submit_answers(
        st.session_state.current_test_code,
        st.session_state.student_name,
        st.session_state.student_email,
        st.session_state.test_answers,
        time_taken
    )
    
    st.success("🎉 Test submitted successfully!")
    st.balloons()
    st.info("✅ Your answers have been recorded. Your teacher will grade them soon.")
    
    # Clear session
    st.session_state.test_loaded = False
    st.session_state.test_started = False
    
    st.button("Take Another Test", on_click=lambda: st.rerun())