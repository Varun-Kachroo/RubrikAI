"""
styles.py
Professional CSS styling for RubriqAI
"""

def get_custom_css():
    """Returns custom CSS for professional, clean UI"""
    return """
    <style>
    /* ==========================================
       GLOBAL STYLES
       ========================================== */
    
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables - DARK THEME */
    :root {
        --primary-color: #6366F1;
        --primary-dark: #4F46E5;
        --primary-light: #818CF8;
        --secondary-color: #10B981;
        --danger-color: #EF4444;
        --warning-color: #F59E0B;
        --info-color: #3B82F6;
        --success-color: #10B981;
        
        --text-primary: #F9FAFB;
        --text-secondary: #E5E7EB;
        --text-muted: #9CA3AF;
        
        --bg-primary: #1F2937;
        --bg-secondary: #111827;
        --bg-tertiary: #374151;
        
        --border-color: #374151;
        --border-radius: 12px;
        --border-radius-sm: 8px;
        
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    
    /* Force dark background everywhere */
    .stApp {
        background-color: var(--bg-secondary);
    }
    
    /* Main App Container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ==========================================
       TYPOGRAPHY
       ========================================== */
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text-primary);
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        letter-spacing: -0.025em;
        color: var(--text-primary);
    }
    
    h1 {
        font-size: 2.25rem;
        line-height: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        font-size: 1.5rem;
        line-height: 2rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        font-size: 1.25rem;
        line-height: 1.75rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    /* ==========================================
       SIDEBAR STYLING
       ========================================== */
    
    /* Sidebar Container */
    [data-testid="stSidebar"] {
        background: var(--bg-primary);
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1rem;
        background: var(--bg-primary);
    }
    
    /* Sidebar text - ensure visibility */
    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }
    
    /* Sidebar Headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
    }
    
    /* Sidebar Dividers */
    [data-testid="stSidebar"] hr {
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid var(--border-color);
    }
    
    /* ==========================================
       BUTTONS
       ========================================== */
    
    /* Primary Buttons - Dark Theme */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
        color: white !important;
        border: none;
        border-radius: var(--border-radius-sm);
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    /* Secondary/Regular Buttons - Dark Theme */
    .stButton > button {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1.5px solid var(--border-color);
        border-radius: var(--border-radius-sm);
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        border-color: var(--primary-color);
        background: var(--bg-primary) !important;
    }
    
    /* Download Buttons - Dark Theme */
    .stDownloadButton > button {
        background: var(--success-color) !important;
        color: white !important;
        border: none;
        border-radius: var(--border-radius-sm);
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton > button:hover {
        background: #059669 !important;
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    /* File Uploader - Dark Theme */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--border-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        background: var(--bg-tertiary) !important;
        transition: all 0.2s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-color);
        background: var(--bg-primary) !important;
    }
    
    [data-testid="stFileUploader"] * {
        color: var(--text-primary) !important;
    }
    
    /* ==========================================
       INPUT FIELDS
       ========================================== */
    
    /* Text Inputs - Dark Theme */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1.5px solid var(--border-color);
        border-radius: var(--border-radius-sm);
        padding: 0.625rem 0.875rem;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        outline: none;
        background: var(--bg-primary) !important;
    }
    
    /* Select Boxes - Dark Theme */
    .stSelectbox > div > div > div {
        border: 1.5px solid var(--border-color);
        border-radius: var(--border-radius-sm);
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }
    
    .stSelectbox label {
        color: var(--text-secondary) !important;
    }
    
    /* ==========================================
       CARDS & CONTAINERS
       ========================================== */
    
    /* Info Boxes - Dark Theme */
    .stAlert {
        border-radius: var(--border-radius);
        border: none;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Success - Dark */
    .stSuccess {
        background: #064E3B !important;
        color: #D1FAE5 !important;
        border-left: 4px solid var(--success-color) !important;
    }
    
    /* Info - Dark */
    .stInfo {
        background: #1E3A8A !important;
        color: #DBEAFE !important;
        border-left: 4px solid var(--info-color) !important;
    }
    
    /* Warning - Dark */
    .stWarning {
        background: #78350F !important;
        color: #FEF3C7 !important;
        border-left: 4px solid var(--warning-color) !important;
    }
    
    /* Error - Dark */
    .stError {
        background: #7F1D1D !important;
        color: #FEE2E2 !important;
        border-left: 4px solid var(--danger-color) !important;
    }
    
    /* Expanders - Dark Theme */
    .streamlit-expanderHeader {
        background: var(--bg-tertiary) !important;
        border-radius: var(--border-radius-sm);
        border: 1px solid var(--border-color);
        padding: 0.75rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
        color: var(--text-primary) !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--bg-primary) !important;
        border-color: var(--primary-light);
    }
    
    .streamlit-expanderContent {
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 var(--border-radius-sm) var(--border-radius-sm);
        padding: 1rem;
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    
    /* Data Editor / Tables - Dark Theme */
    .stDataFrame {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
        background: var(--bg-primary) !important;
    }
    
    .stDataFrame * {
        color: var(--text-primary) !important;
        background: var(--bg-primary) !important;
    }
    
    .stDataFrame thead {
        background: var(--bg-tertiary) !important;
    }
    
    /* Data Editor specific */
    [data-testid="stDataFrameResizable"] {
        background: var(--bg-primary) !important;
    }
    
    [data-testid="stDataFrameResizable"] * {
        color: var(--text-primary) !important;
    }
    
    /* ==========================================
       PROGRESS BARS
       ========================================== */
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--primary-light) 100%);
        border-radius: 10px;
        height: 8px;
    }
    
    /* ==========================================
       METRICS
       ========================================== */
    
    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* ==========================================
       FILE UPLOADER
       ========================================== */
    
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--border-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        background: var(--bg-secondary);
        transition: all 0.2s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-color);
        background: var(--bg-primary);
    }
    
    /* ==========================================
       TABS
       ========================================== */
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--bg-secondary);
        padding: 0.5rem;
        border-radius: var(--border-radius);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--border-radius-sm);
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        background: transparent;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: var(--shadow-sm);
    }
    
    /* ==========================================
       CUSTOM COMPONENTS
       ========================================== */
    
    /* Card Component */
    .custom-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    
    .custom-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem 0;
        border-bottom: 2px solid var(--border-color);
        margin-bottom: 1.5rem;
    }
    
    .section-header h2 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    /* Badge */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-primary {
        background: #EEF2FF;
        color: var(--primary-color);
    }
    
    .badge-success {
        background: #ECFDF5;
        color: var(--success-color);
    }
    
    .badge-warning {
        background: #FFFBEB;
        color: var(--warning-color);
    }
    
    .badge-danger {
        background: #FEF2F2;
        color: var(--danger-color);
    }
    
    /* ==========================================
       RESPONSIVE
       ========================================== */
    
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        h1 {
            font-size: 1.875rem;
        }
        
        h2 {
            font-size: 1.25rem;
        }
    }
    
    /* ==========================================
       ANIMATIONS
       ========================================== */
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* ==========================================
       SPACING UTILITIES
       ========================================== */
    
    .mt-1 { margin-top: 0.5rem; }
    .mt-2 { margin-top: 1rem; }
    .mt-3 { margin-top: 1.5rem; }
    .mt-4 { margin-top: 2rem; }
    
    .mb-1 { margin-bottom: 0.5rem; }
    .mb-2 { margin-bottom: 1rem; }
    .mb-3 { margin-bottom: 1.5rem; }
    .mb-4 { margin-bottom: 2rem; }
    
    .p-1 { padding: 0.5rem; }
    .p-2 { padding: 1rem; }
    .p-3 { padding: 1.5rem; }
    .p-4 { padding: 2rem; }
    
    </style>
    """
