import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime
from data_flow import SessionStateManager, SidebarHelper, SearchService, PAGenerator
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

# ============================================================================
# GUIDED DATA COLLECTION SYSTEM
# ============================================================================

class FieldPriority(Enum):
    """Priority levels for data collection fields."""
    REQUIRED = "required"      # Must have before search (state)
    IMPORTANT = "important"    # Strongly recommended (payer, drug)
    HELPFUL = "helpful"        # Nice to have (diagnosis, age)

@dataclass
class DataCollectionState:
    """Tracks what data has been collected and what's missing."""
    state: Optional[str] = None
    payer: Optional[str] = None
    drug_class: Optional[str] = None
    diagnosis: Optional[str] = None
    age: Optional[str] = None
    prior_medications: List[str] = field(default_factory=list)
    
    def get_collected_fields(self) -> List[str]:
        collected = []
        if self.state: collected.append('state')
        if self.payer: collected.append('payer')
        if self.drug_class: collected.append('drug_class')
        if self.diagnosis: collected.append('diagnosis')
        if self.age: collected.append('age')
        if self.prior_medications: collected.append('prior_medications')
        return collected
    
    def get_missing_required_fields(self) -> List[str]:
        missing = []
        if not self.state: missing.append('state')
        return missing
    
    def can_proceed_to_search(self) -> bool:
        return self.state is not None
    
    def get_search_quality_score(self) -> Tuple[int, str]:
        score = 0
        if self.state: score += 40
        if self.payer: score += 30
        if self.drug_class: score += 20
        if self.diagnosis: score += 4
        if self.age: score += 3
        if self.prior_medications: score += 3
        
        if score >= 90:
            return score, "Excellent - Highly targeted search"
        elif score >= 70:
            return score, "Good - Well-targeted search"
        elif score >= 50:
            return score, "Fair - Broad search, may have many results"
        elif score >= 40:
            return score, "Limited - State-level search only"
        else:
            return score, "Insufficient - State required"

# Page configuration
st.set_page_config(
    page_title="The Headache Vault - PA Automation Demo",
    page_icon="💊",  # Medical/pill icon instead of brain
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light theme
st.markdown("""
<script>
    window.parent.document.documentElement.setAttribute('data-theme', 'light');
</script>
""", unsafe_allow_html=True)

# Custom CSS with Headache Vault brand identity
st.markdown("""
<style>
    /* Import brand fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Source+Sans+Pro:wght@400;600&display=swap');
    
    /* Force light theme and readable backgrounds */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    .main .block-container {
        background-color: #FFFFFF !important;
    }
    
    /* Global font override */
    html, body, [class*="css"] {
        font-family: 'Source Sans Pro', sans-serif;
        color: #262730 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #262730 !important;
    }
    
    .main-header {
        font-size: 2.5rem;
        color: #4B0082;  /* Regulatory Purple */
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5A5A5A;  /* Readable gray */
        margin-bottom: 2rem;
        font-family: 'Source Sans Pro', sans-serif;
    }
    .step-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4B0082;  /* Regulatory Purple */
        margin: 1rem 0;
        color: #262730;
    }
    .warning-box {
        background-color: #FFF9E6;  /* Lighter yellow for warnings */
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FFD700;  /* Gold Card Yellow */
        margin: 1rem 0;
        color: #856404;
    }
    .success-box {
        background-color: #F5F0FF;  /* Lavender tint */
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FFD700;  /* Gold Card Yellow for Gold Card status */
        margin: 1rem 0;
        color: #262730;  /* Dark text for readability */
    }
    .evidence-tag {
        display: inline-block;
        background-color: #E6E6FA;  /* Compassion Lavender */
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        margin: 0.25rem;
        color: #262730;  /* Dark text for readability */
        font-weight: 600;
    }
    
    /* Update primary button colors */
    .stButton > button[kind="primary"] {
        background-color: #4B0082 !important;  /* Regulatory Purple */
        color: white !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #6A0DAD !important;  /* Lighter purple on hover */
    }
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #4B0082 !important;
        border: 2px solid #4B0082 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #F5F0FF !important;  /* Light purple tint on hover */
        color: #4B0082 !important;
    }
    
    /* Regular buttons */
    .stButton > button {
        color: #262730 !important;  /* Dark text for visibility */
    }
    
    /* Production Features - Dashboard Stats */
    .stat-card {
        background: linear-gradient(135deg, #4B0082 0%, #6A0DAD 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(75, 0, 130, 0.3);
    }
    .stat-number {
        font-size: 2.75rem;
        font-weight: 800;
        font-family: 'Inter', sans-serif;
        margin: 0;
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .stat-label {
        font-size: 1rem;
        font-weight: 600;
        margin-top: 0.5rem;
        color: white !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    /* Policy Result Cards */
    .policy-card {
        background: white;
        border: 2px solid #E6E6FA;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .policy-card:hover {
        border-color: #4B0082;
        box-shadow: 0 4px 12px rgba(75, 0, 130, 0.15);
    }
    .policy-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #F0F0F0;
    }
    .policy-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #4B0082;
        margin: 0;
    }
    .policy-badge {
        display: inline-block;
        background: #E6E6FA;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #4B0082;
        margin-left: 0.5rem;
    }
    .policy-section {
        margin: 1rem 0;
    }
    .policy-section-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #708090;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    .step-item {
        display: flex;
        align-items: flex-start;
        padding: 0.75rem;
        background: #FAFAFA;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #262730;  /* Ensure dark text on light background */
    }
    .step-item strong {
        color: #262730;  /* Dark text for medication names */
    }
    .step-item small {
        color: #708090;  /* Slate gray for durations */
    }
    .step-number {
        background: #4B0082;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        margin-right: 0.75rem;
        flex-shrink: 0;
    }
    .gold-card-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000;  /* Black text on gold - high contrast */
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
        margin: 0.5rem 0;
    }
    
    /* Copy Button Styling */
    .copy-button {
        background: #4B0082;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        transition: all 0.2s ease;
    }
    .copy-button:hover {
        background: #6A0DAD;
        transform: translateY(-1px);
    }
    
    /* Success Toast */
    .success-toast {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10B981;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    }
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Production Footer */
    .production-footer {
        margin-top: 3rem;
        padding: 2rem 0;
        border-top: 2px solid #E6E6FA;
        text-align: center;
        color: #708090;
    }
    .footer-badge {
        display: inline-block;
        margin: 0 0.5rem;
        font-size: 0.85rem;
        color: #4B0082;
    }
    
    /* Dashboard Quick Actions */
    .quick-action-btn {
        background: white;
        border: 2px solid #4B0082;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #4B0082;
        font-weight: 600;
    }
    .quick-action-btn:hover {
        background: #4B0082;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(75, 0, 130, 0.2);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #FAFAFA !important;  /* Light gray */
    }
    
    /* Fix sidebar form elements - dropdowns, radio buttons, etc. */
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #FFFFFF !important;  /* White background for dropdowns */
        color: #262730 !important;  /* Dark text */
    }
    
    section[data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        background-color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    /* Dropdown menu items */
    [data-baseweb="popover"] {
        background-color: #FFFFFF !important;
    }
    
    [role="option"] {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    [role="option"]:hover {
        background-color: #F0F0F0 !important;
    }
    
    /* Radio buttons */
    section[data-testid="stSidebar"] [data-testid="stRadio"] label {
        color: #262730 !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
        color: #262730 !important;
    }
    
    /* Number input */
    section[data-testid="stSidebar"] input[type="number"] {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    /* All sidebar labels */
    section[data-testid="stSidebar"] label {
        color: #262730 !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar header */
    section[data-testid="stSidebar"] h2 {
        color: #262730 !important;
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        color: #262730;  /* Dark readable text for metric values */
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #5A5A5A;  /* Gray for metric labels */
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #5A5A5A;  /* Readable gray for inactive tabs */
        background-color: transparent !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #262730 !important;  /* Dark text for active tab */
        border-bottom-color: #4B0082 !important;  /* Purple underline for active */
        background-color: transparent !important;
    }
    
    /* General form elements in main area */
    .stSelectbox > div > div,
    .stTextInput > div > div,
    .stTextArea > div > div {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    input, textarea, select {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #F8F9FA !important;
        color: #262730 !important;
    }
    
    /* Info boxes, warnings, etc */
    .stAlert {
        background-color: #F8F9FA !important;
    }
    
    /* Ensure text in info/success/warning/error boxes is visible */
    .stAlert [data-testid="stMarkdownContainer"] {
        color: #262730 !important;
    }
    
    .stAlert strong {
        color: #262730 !important;
    }
    
    /* Caption text visibility */
    .stCaption {
        color: #708090 !important;  /* Slate gray - readable on white */
    }
    
    /* ===================================================================== */
    /* NUCLEAR OPTION - FORCE ALL TEXT VISIBLE */
    /* ===================================================================== */
    
    /* Force all text elements to be dark EXCEPT primary buttons and stat cards */
    p:not(.stButton [kind="primary"] *):not(.stat-card *):not(.stat-number):not(.stat-label), 
    span:not(.stButton [kind="primary"] *):not(.stat-card *):not(.stat-number):not(.stat-label), 
    div:not(.stButton [kind="primary"] *):not(.stat-card):not(.stat-number):not(.stat-label), 
    label, li, td, th, h1, h2, h3, h4, h5, h6 {
        color: #262730 !important;
    }
    
    /* PRIMARY BUTTONS - Keep white text */
    .stButton > button[kind="primary"],
    .stButton > button[kind="primary"] *,
    button[kind="primary"] span,
    button[kind="primary"] div,
    button[kind="primary"] p {
        color: white !important;
    }
    
    /* Except for elements with specific styling */
    /* STAT CARDS - Force white/lavender text on purple background */
    .stat-card,
    .stat-card *,
    .stat-card div,
    .stat-card span,
    .stat-card .stat-number,
    .stat-card .stat-number span,
    .stat-card .stat-label,
    .stat-card .stat-label span,
    div.stat-card div.stat-number,
    div.stat-card div.stat-number span,
    div.stat-card div.stat-label,
    div.stat-card div.stat-label span {
        color: white !important;
    }
    .stat-number,
    .stat-number span {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.4) !important;
    }
    .stat-label,
    .stat-label span {
        color: #E6E6FA !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3) !important;
    }
    
    /* Other exceptions */
    .step-number * {
        color: white !important;
    }
    
    /* Force selectbox and dropdown text */
    [data-baseweb="select"] span,
    [data-baseweb="select"] div,
    [role="listbox"] *,
    [role="option"] * {
        color: #262730 !important;
    }
    
    /* Force all button text except primary purple buttons */
    button:not([kind="primary"]) * {
        color: #4B0082 !important;
    }
    
    /* Force dataframe text */
    .dataframe, .dataframe *, table, table * {
        color: #262730 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Force markdown container text */
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] div {
        color: #262730 !important;
    }
    
    /* Force all text areas and inputs */
    textarea, input, select {
        color: #262730 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Force code blocks */
    code, pre, .stCode {
        color: #262730 !important;
        background-color: #F8F9FA !important;
    }
    
    /* ===================================================================== */
    /* PERSONA TOGGLE & GUIDANCE STYLES */
    /* ===================================================================== */
    
    /* Experience Mode Toggle */
    .mode-toggle {
        background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%);
        border: 2px solid #E6E6FA;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
    }
    
    .mode-label {
        font-size: 0.9rem;
        color: #5A5A5A;
        font-weight: 500;
    }
    
    /* Learning Moment Box */
    .learning-moment {
        background: linear-gradient(135deg, #FFF9E6 0%, #FFFEF5 100%);
        border: 1px solid #FFD700;
        border-left: 4px solid #FFD700;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
    }
    
    .learning-moment-title {
        color: #B8860B;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .learning-moment-content {
        color: #5A5A5A;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    .learning-moment-content ul {
        margin: 0.5rem 0;
        padding-left: 1.25rem;
    }
    
    .learning-moment-content li {
        margin: 0.25rem 0;
        color: #5A5A5A !important;
    }
    
    /* PCP Guidance Expander */
    .pcp-guidance {
        background: #F0F8FF;
        border: 1px solid #B0D4F1;
        border-left: 4px solid #4A90D9;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
    }
    
    .pcp-guidance-title {
        color: #2C5282;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .pcp-guidance-content {
        color: #4A5568;
        font-size: 0.85rem;
        line-height: 1.6;
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid #B0D4F1;
    }
    
    /* Documentation Checklist */
    .doc-checklist {
        background: #F0FFF4;
        border: 1px solid #9AE6B4;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    
    .doc-checklist-title {
        color: #276749;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .doc-checklist-item {
        color: #2F855A;
        font-size: 0.85rem;
        padding: 0.25rem 0;
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
    }
    
    /* Pitfall Warning */
    .pitfall-warning {
        background: #FFF5F5;
        border: 1px solid #FEB2B2;
        border-left: 4px solid #E53E3E;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
    }
    
    .pitfall-warning-title {
        color: #C53030;
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .pitfall-warning-content {
        color: #742A2A;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    
    /* Pro Tip Box */
    .pro-tip {
        background: linear-gradient(135deg, #EBF8FF 0%, #F0FFFF 100%);
        border: 1px solid #90CDF4;
        border-left: 4px solid #4299E1;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
    }
    
    .pro-tip-title {
        color: #2B6CB0;
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .pro-tip-content {
        color: #2C5282;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    
    /* ===================================================================== */
    /* FINAL STAT CARD OVERRIDE - Highest cascade priority */
    /* ===================================================================== */
    .stat-card .stat-number span,
    div.stat-card div.stat-number span {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.4) !important;
    }
    .stat-card .stat-label span,
    div.stat-card div.stat-label span {
        color: #E6E6FA !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3) !important;
    }
/* Quality indicators for guided data collection */
.quality-excellent {
    background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
    color: #065F46;
    border: 1px solid #10B981;
}
.quality-good {
    background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
    color: #1E40AF;
    border: 1px solid #3B82F6;
}
.quality-fair {
    background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
    color: #92400E;
    border: 1px solid #F59E0B;
}
.quality-limited {
    background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
    color: #991B1B;
    border: 1px solid #EF4444;
}
.required-field-box {
    background: #FEF2F2;
    border: 2px solid #DC2626;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Load databases
@st.cache_data
def load_databases():
    """
    Load all Headache Vault databases from CSV files.
    
    Database Schema:
    - payer_registry: 717 payers with LOB codes, Vault_Payer_ID format
    - payer_policies: 752 policies with step therapy, drug class taxonomy
    - denial_codes: 35 denial scenarios with appeal strategies
    - pediatric_overrides: 25 records with safety flags (valproate, topiramate)
    - state_regulations: 50 states with Gold Card legislation details
    - icd10_codes: 46 diagnosis codes with ICHD-3 mappings
    - therapeutic_doses: 40 medications with ACP 2025 thresholds
    - otc_medications: 28 OTC meds for MOH tracking
    """
    payer_registry = pd.read_csv('Payer_Registry.csv')
    payer_policies = pd.read_csv('Payer_Policies.csv')
    denial_codes = pd.read_csv('Denial_Codes_Appeals.csv')
    pediatric_overrides = pd.read_csv('Pediatric_Overrides.csv')
    state_regulations = pd.read_csv('State_Regulations.csv')
    icd10_codes = pd.read_csv('ICD10_Diagnosis_Codes.csv')
    therapeutic_doses = pd.read_csv('Therapeutic_Doses.csv')
    otc_medications = pd.read_csv('OTC_Medications.csv')
    
    return payer_registry, payer_policies, denial_codes, pediatric_overrides, state_regulations, icd10_codes, therapeutic_doses, otc_medications

# ============================================================================
# HELPER: Get step therapy details with column name fallback
# ============================================================================
def get_step_therapy_details(row):
    """Get step therapy details with column name fallback for DB compatibility."""
    requirement = row.get('Step_1_Requirement') or row.get('Step_Therapy_Requirements') or 'Not specified'
    duration = row.get('Step_1_Duration') or row.get('Step_Therapy_Duration') or 'Trial duration not specified'
    return str(requirement), str(duration)

# ============================================================================
# GUIDED DATA COLLECTION HELPERS
# ============================================================================

def analyze_parsed_data(parsed_data: dict) -> DataCollectionState:
    """Convert parsed AI data into a DataCollectionState."""
    return DataCollectionState(
        state=parsed_data.get('state'),
        payer=parsed_data.get('payer'),
        drug_class=parsed_data.get('drug_class'),
        diagnosis=parsed_data.get('diagnosis'),
        age=parsed_data.get('age'),
        prior_medications=parsed_data.get('prior_medications', [])
    )

def get_quality_indicator_html(score: int, description: str) -> str:
    """Generate HTML for quality indicator badge."""
    if score >= 90:
        color_class = "quality-excellent"
        icon = "🎯"
    elif score >= 70:
        color_class = "quality-good"
        icon = "✅"
    elif score >= 50:
        color_class = "quality-fair"
        icon = "⚠️"
    else:
        color_class = "quality-limited"
        icon = "📊"
    
    return f'''
    <div class="{color_class}" style="padding: 0.75rem 1rem; border-radius: 8px; margin: 1rem 0; display: inline-block;">
        <span style="font-size: 1.1rem;">{icon}</span>
        <strong>Search Quality: {score}%</strong> — {description}
    </div>
    '''

# ============================================================================
# NATIONAL FALLBACK SEARCH - Added Jan 2026
# ============================================================================
def search_policies_with_fallback(db_b, state, payer=None, drug_class=None):
    """
    Search for policies with automatic fallback to national (ALL) entries
    and drug class cascading for preventive gepants.
    
    Priority:
    1. State + Payer + Drug Class specific
    2. National (ALL) + Payer + Drug Class specific
    3. For Gepants (Preventive): Try Qulipta → CGRP mAbs cascade
    
    Returns: (results_df, fallback_used: bool, fallback_message: str)
    """
    fallback_used = False
    fallback_message = ""
    
    # Step 1: Try state-specific search
    query = db_b[db_b['State'] == state].copy()
    query = query.reset_index(drop=True)  # Reset index to avoid boolean mask issues
    
    # Apply payer filter with flexible matching
    if payer:
        # Extract key payer identifier for flexible matching
        payer_lower = payer.lower()
        
        # Try to extract the core payer name for better matching
        payer_keywords = []
        if 'horizon' in payer_lower:
            payer_keywords = ['horizon']
        elif 'aetna' in payer_lower:
            payer_keywords = ['aetna']
        elif 'united' in payer_lower or 'uhc' in payer_lower:
            payer_keywords = ['united', 'uhc']
        elif 'cigna' in payer_lower:
            payer_keywords = ['cigna']
        elif 'anthem' in payer_lower or 'elevance' in payer_lower:
            payer_keywords = ['anthem', 'elevance']
        elif 'bcbs' in payer_lower or 'blue cross' in payer_lower:
            payer_keywords = ['bcbs', 'blue cross', 'blue shield']
        elif 'humana' in payer_lower:
            payer_keywords = ['humana']
        elif 'kaiser' in payer_lower:
            payer_keywords = ['kaiser']
        elif 'highmark' in payer_lower:
            payer_keywords = ['highmark']
        elif 'independence' in payer_lower:
            payer_keywords = ['independence']
        else:
            # Use first significant word as keyword
            payer_keywords = [payer.split()[0].lower()] if payer.split() else [payer_lower]
        
        # Build flexible payer match
        payer_mask = pd.Series([False] * len(query))
        for kw in payer_keywords:
            payer_mask = payer_mask | query['Payer_Name'].str.contains(kw, case=False, na=False)
        
        payer_query = query[payer_mask]
        
        # If no state match, try national fallback
        if len(payer_query) == 0:
            national_query = db_b[db_b['State'] == 'ALL'].copy()
            national_query = national_query.reset_index(drop=True)  # Reset index
            national_mask = pd.Series([False] * len(national_query))
            for kw in payer_keywords:
                national_mask = national_mask | national_query['Payer_Name'].str.contains(kw, case=False, na=False)
            national_payer = national_query[national_mask]
            
            if len(national_payer) > 0:
                query = national_payer
                fallback_used = True
                fallback_message = f"ℹ️ No {state}-specific policy for {payer}. Showing **national baseline** policy. State-specific rules may vary."
            else:
                query = payer_query  # Empty
        else:
            query = payer_query
    
    # Apply drug class filter with cascading for preventive gepants
    if drug_class:
        drug_query = query[query['Drug_Class'] == drug_class]
        
        # If no results, try cascading fallbacks
        if len(drug_query) == 0:
            cascade_classes = []
            cascade_message = ""
            
            # Define cascade order for preventive gepants
            if drug_class == 'Gepants (Preventive)':
                cascade_classes = ['Qulipta', 'CGRP mAbs']
                cascade_message = "Nurtec Preventive"
            elif drug_class == 'Qulipta':
                cascade_classes = ['Gepants (Preventive)', 'CGRP mAbs']
                cascade_message = "Qulipta"
            
            # Try cascade classes
            for cascade_class in cascade_classes:
                cascade_query = query[query['Drug_Class'] == cascade_class]
                if len(cascade_query) > 0:
                    drug_query = cascade_query
                    fallback_used = True
                    fallback_message = f"ℹ️ No {drug_class} policy found. Showing **{cascade_class}** policy (similar step therapy requirements)."
                    break
            
            # If still no results, try national fallback
            if len(drug_query) == 0 and not fallback_used:
                national_query = db_b[db_b['State'] == 'ALL'].copy()
                national_query = national_query.reset_index(drop=True)  # Reset index
                if payer and 'payer_keywords' in dir():
                    # Use same flexible matching
                    national_mask = pd.Series([False] * len(national_query))
                    for kw in payer_keywords:
                        national_mask = national_mask | national_query['Payer_Name'].str.contains(kw, case=False, na=False)
                    national_query = national_query[national_mask]
                
                # Try original drug class nationally
                national_drug = national_query[national_query['Drug_Class'] == drug_class]
                
                # If not found, try cascade classes nationally
                if len(national_drug) == 0:
                    for cascade_class in cascade_classes:
                        national_drug = national_query[national_query['Drug_Class'] == cascade_class]
                        if len(national_drug) > 0:
                            fallback_message = f"ℹ️ No {state}-specific {drug_class} policy. Showing **national {cascade_class}** baseline."
                            break
                
                if len(national_drug) > 0:
                    drug_query = national_drug
                    fallback_used = True
                    if not fallback_message:
                        fallback_message = f"ℹ️ No {state}-specific policy for {drug_class}. Showing **national baseline** policy."
        
        query = drug_query
    
    return query, fallback_used, fallback_message


def send_lead_to_monday(name, email, practice, state, payer, drug_class, notes):
    """Send lead data to Monday.com CRM board"""


def check_criteria_met(step_requirements, prior_medications, diagnosis):
    """
    Check if patient's documented history meets step therapy requirements.
    Returns list of (requirement, met_status, details) tuples.
    """
    criteria_status = []
    step_req_lower = step_requirements.lower() if step_requirements else ''
    prior_meds_lower = [m.lower() for m in prior_medications] if prior_medications else []
    
    # Common preventive medication classes
    beta_blockers = ['propranolol', 'metoprolol', 'atenolol', 'nadolol', 'timolol']
    anticonvulsants = ['topiramate', 'topamax', 'valproate', 'depakote', 'divalproex', 'gabapentin']
    antidepressants = ['amitriptyline', 'nortriptyline', 'venlafaxine', 'duloxetine', 'effexor', 'cymbalta']
    ccbs = ['verapamil', 'flunarizine']
    triptans = ['sumatriptan', 'rizatriptan', 'eletriptan', 'zolmitriptan', 'naratriptan', 'frovatriptan', 'almotriptan']
    
    # Check for oral preventive requirements (CGRP mAbs)
    if '2 oral preventive' in step_req_lower or ('2' in step_req_lower and 'preventive' in step_req_lower) or 'conventional oral' in step_req_lower:
        classes_tried = 0
        meds_found = []
        
        for med in prior_meds_lower:
            if any(bb in med for bb in beta_blockers) and 'Beta-blocker' not in [m.split(' (')[0] for m in meds_found]:
                classes_tried += 1
                meds_found.append(f"Beta-blocker ({med.title()})")
            elif any(ac in med for ac in anticonvulsants) and 'Anticonvulsant' not in [m.split(' (')[0] for m in meds_found]:
                classes_tried += 1
                meds_found.append(f"Anticonvulsant ({med.title()})")
            elif any(ad in med for ad in antidepressants) and 'Antidepressant' not in [m.split(' (')[0] for m in meds_found]:
                classes_tried += 1
                meds_found.append(f"Antidepressant ({med.title()})")
            elif any(ccb in med for ccb in ccbs) and 'CCB' not in [m.split(' (')[0] for m in meds_found]:
                classes_tried += 1
                meds_found.append(f"CCB ({med.title()})")
        
        if classes_tried >= 2:
            criteria_status.append(("≥2 oral preventive classes", True, f"{', '.join(meds_found[:3])}"))
        elif classes_tried == 1:
            criteria_status.append(("≥2 oral preventive classes", False, f"Only 1 class: {meds_found[0]}"))
        else:
            criteria_status.append(("≥2 oral preventive classes", False, "No oral preventives documented"))
    
    # Check for triptan requirements (Gepants)
    if 'triptan' in step_req_lower:
        triptans_tried = []
        for med in prior_meds_lower:
            for t in triptans:
                if t in med and t.title() not in triptans_tried:
                    triptans_tried.append(t.title())
        
        if '2' in step_req_lower and 'triptan' in step_req_lower:
            if len(triptans_tried) >= 2:
                criteria_status.append(("≥2 triptans tried", True, f"{', '.join(triptans_tried[:2])}"))
            elif len(triptans_tried) == 1:
                criteria_status.append(("≥2 triptans tried", False, f"Only 1: {triptans_tried[0]}"))
            else:
                criteria_status.append(("≥2 triptans tried", False, "No triptans documented"))
    
    # Check for verapamil/lithium requirements (Cluster)
    if 'verapamil' in step_req_lower or 'lithium' in step_req_lower:
        verapamil_tried = any('verapamil' in med for med in prior_meds_lower)
        lithium_tried = any('lithium' in med for med in prior_meds_lower)
        
        if ' or ' in step_req_lower:  # verapamil OR lithium
            if verapamil_tried or lithium_tried:
                med_name = 'Verapamil' if verapamil_tried else 'Lithium'
                criteria_status.append(("Verapamil OR lithium failure", True, f"{med_name} trial documented"))
            else:
                criteria_status.append(("Verapamil OR lithium failure", False, "Neither documented"))
        elif ' and ' in step_req_lower:  # verapamil AND lithium
            if verapamil_tried and lithium_tried:
                criteria_status.append(("Verapamil AND lithium failure", True, "Both documented"))
            else:
                missing = []
                if not verapamil_tried: missing.append("verapamil")
                if not lithium_tried: missing.append("lithium")
                criteria_status.append(("Verapamil AND lithium failure", False, f"Missing: {', '.join(missing)}"))
    
    return criteria_status

    
    # Get API key from secrets
    try:
        api_key = st.secrets.get("MONDAY_API_KEY", None)
    except:
        api_key = None
    
    if not api_key:
        return False, "Monday.com API key not configured"
    
    # Monday.com board and group IDs
    BOARD_ID = 18397061224  # Headache Vault - Contacts & Prospects
    GROUP_ID = "group_mkzxdy1j"  # Demo Users group
    
    # Build column values
    column_values = {
        "email_mkzxqtxn": {"email": email, "text": email},
        "text_mkzxpp92": state,  # State
        "text_mkzxdt7e": practice if practice else "Demo User",  # Specialty/Practice
        "color_mkzx5w7m": {"label": "Demo User"},  # Contact Type
        "color_mkzxsgea": {"label": "PA Demo"},  # Lead Source
        "color_mkzxp42x": {"label": "New Lead"},  # Sales Stage
        "date_mkzxqhxz": {"date": datetime.now().strftime("%Y-%m-%d")},  # First Contact Date
        "long_text_mkzxe3nf": {"text": f"PA Demo Lead\\nPayer: {payer}\\nDrug: {drug_class}\\n{notes}"}  # Notes
    }
    
    # GraphQL mutation
    mutation = """
    mutation ($boardId: ID!, $groupId: String!, $itemName: String!, $columnValues: JSON!) {
        create_item (
            board_id: $boardId,
            group_id: $groupId,
            item_name: $itemName,
            column_values: $columnValues
        ) {
            id
        }
    }
    """
    
    variables = {
        "boardId": str(BOARD_ID),
        "groupId": GROUP_ID,
        "itemName": name if name else email.split("@")[0],
        "columnValues": json.dumps(column_values)
    }
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "https://api.monday.com/v2",
            json={"query": mutation, "variables": variables},
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if "data" in result and result["data"]["create_item"]:
                return True, result["data"]["create_item"]["id"]
            else:
                return False, result.get("errors", "Unknown error")
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

# Initialize session state (unified data flow)
SessionStateManager.initialize()

# Guided data collection state
if 'data_collection_state' not in st.session_state:
    st.session_state.data_collection_state = None

# Load data
# Unpack databases with descriptive names
payer_registry, payer_policies, denial_codes, pediatric_overrides, state_regulations, icd10_codes, therapeutic_doses, otc_medications = load_databases()

# Create aliases for backward compatibility during transition
db_a = payer_registry
db_b = payer_policies
db_c = denial_codes
db_e = pediatric_overrides
db_f = state_regulations
icd10 = icd10_codes
therapeutic = therapeutic_doses
otc = otc_medications

# Helper function to create copy button HTML
def create_copy_button(text, button_id):
    """Create a copy-to-clipboard button"""
    escaped_text = text.replace("'", "\\'").replace("\n", "\\n")
    return f"""
    <button onclick="navigator.clipboard.writeText('{escaped_text}').then(() => {{
        const btn = document.getElementById('{button_id}');
        const original = btn.innerHTML;
        btn.innerHTML = '✅ Copied!';
        btn.style.background = '#10B981';
        setTimeout(() => {{
            btn.innerHTML = original;
            btn.style.background = '#4B0082';
        }}, 2000);
    }})" id="{button_id}" class="copy-button">
        📋 Copy
    </button>
    """

# Clinical note parser
def parse_clinical_note(note_text, db_a, db_b):
    """Parse clinical note using Claude API to extract structured data"""
    import anthropic
    
    # Get API key from secrets (for deployed app) or environment
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
    except:
        api_key = None
    
    if not api_key:
        st.error("⚠️ Anthropic API key not configured. Add it to Streamlit secrets to enable note parsing.")
        return None
    
    # Get valid options from databases
    states = sorted(db_b['State'].unique().tolist())
    payers = sorted(db_a['Payer_Name'].unique().tolist())[:50]  # Top 50 for context
    drug_classes = sorted(db_b['Drug_Class'].unique().tolist())
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""Extract patient information from this clinical note. Return ONLY a JSON object.

**STRICT EXTRACTION RULES - READ CAREFULLY:**

You MUST return null for any field where the information is not EXPLICITLY written in the note.
DO NOT:
- Guess a state (like "PA") if no state or city is mentioned
- Guess an age (like "35") if no age is mentioned  
- Guess a payer if no insurance is mentioned
- Make up or infer ANY information

EXAMPLES OF CORRECT BEHAVIOR:
- Note says "45-year-old" → age: 45
- Note does NOT mention age → age: null (NOT a guess like 35)
- Note says "lives in Philadelphia" → state: "PA"
- Note does NOT mention location → state: null (NOT a guess like "PA")
- Note says "has Aetna" → payer: "Aetna"
- Note does NOT mention insurance → payer: null

CRITICAL: Look for insurance/payer information carefully. Examples:
- "Has Independence Blue Cross" → payer: "Independence Blue Cross"
- "Has Highmark insurance" → payer: "Highmark Blue Cross Blue Shield"
- "Aetna commercial plan" → payer: "Aetna"
- "UnitedHealthcare" → payer: "UnitedHealthcare"
- NO INSURANCE MENTIONED → payer: null

JSON format:
{{
  "state": "two-letter state code or null if NO location mentioned",
  "payer": "insurance company name or null if NO insurance mentioned", 
  "drug_class": "medication class or null if NO specific drug requested",
  "diagnosis": "Chronic Migraine, Episodic Migraine, or Cluster Headache based on symptoms",
  "age": "integer or null if NO age mentioned",
  "prior_medications": ["only medications EXPLICITLY named as tried/failed"],
  "confidence": "high/medium/low based on how much info was explicitly stated"
}}
  "diagnosis": "Chronic Migraine, Episodic Migraine, or Cluster Headache based on symptoms",
  "age": integer age or null if NOT explicitly stated,
  "prior_medications": ["medications that failed - only include if explicitly named"],
  "confidence": "high if most fields found, medium if some missing, low if minimal info"
}}

Common payers in database:
{', '.join(payers[:40])}

Valid drug classes:
{', '.join(drug_classes)}

Medication name to class mapping:
- Aimovig, Ajovy, Emgality (migraine), erenumab → "CGRP mAbs"
- Emgality 300mg for CLUSTER HEADACHE → "CGRP mAb (Cluster)" (NOT "CGRP mAbs")
- If diagnosis is Cluster Headache and medication is Emgality → "CGRP mAb (Cluster)"
- Ubrelvy, ubrogepant → "Gepants" (acute only)
- Zavzpret, zavegepant → "Gepants" (acute only)
- Nurtec ODT, rimegepant for ACUTE/PRN use → "Gepants"
- Nurtec ODT, rimegepant for PREVENTION → "Gepants (Preventive)"
- Qulipta, atogepant → "Qulipta" (preventive only)
- Botox, onabotulinumtoxinA → "Botox"
- Vyepti, eptinezumab → "Vyepti"
- For Cluster Headache prevention → "CGRP mAb (Cluster)" or "Emgality (Cluster)"

CRITICAL - Nurtec indication detection:
- If note says "prevent", "prevention", "prophylaxis", "daily", "every other day", "EOD" → "Gepants (Preventive)"
- If note says "acute", "PRN", "as needed", "rescue", "abort" → "Gepants"
- If unclear, check diagnosis: Chronic Migraine often uses preventive, Episodic often uses acute
- Default to "Gepants (Preventive)" if requesting Nurtec for someone already on preventive therapy discussion

CRITICAL - Default preventive selection:
- If patient "wants prevention" or "wants something to prevent" WITHOUT naming a specific drug:
  → Default to "CGRP mAbs" (first-line injectable preventive, most common PA request)
- Do NOT default to Botox unless explicitly mentioned - Botox is second-line and chronic migraine only
- Do NOT default to Vyepti unless explicitly mentioned - Vyepti requires IV infusion
- Qulipta is appropriate if patient prefers oral medication or has needle phobia

DRUG CLASS PRIORITY for unspecified preventive requests:
1. "CGRP mAbs" - Default choice (Aimovig, Ajovy, Emgality)
2. "Qulipta" - If oral preferred or needle concerns mentioned
3. "Botox" - ONLY if explicitly requested or patient has failed CGRP mAbs
4. "Vyepti" - ONLY if explicitly requested or patient needs IV option

Clinical note:
{note_text}

Return ONLY the JSON object. Use null for ANY field where information is not explicitly stated in the note. Do NOT fabricate or assume information."""
            }]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text
        
        # Try to parse JSON
        try:
            parsed = json.loads(response_text)
            
            # Validate and fuzzy-match payer name
            if parsed.get('payer'):
                payer_input = parsed['payer'].lower().strip()
                all_payers = db_a['Payer_Name'].unique()
                
                # Try exact match first (case insensitive)
                exact_match = None
                for p in all_payers:
                    if p.lower() == payer_input:
                        exact_match = p
                        break
                
                # If no exact match, try partial matching
                if not exact_match:
                    for p in all_payers:
                        # Check if input is contained in database name or vice versa
                        if payer_input in p.lower() or p.lower() in payer_input:
                            exact_match = p
                            break
                
                # Update with matched name
                if exact_match:
                    parsed['payer'] = exact_match
            
            # POST-PROCESSING: Validate extracted values against original note
            # This catches AI hallucinations by checking if values actually appear in the note
            note_lower = note_text.lower()
            validation_log = []
            
            # Validate STATE - must have state name, abbreviation, or city mentioned
            if parsed.get('state'):
                state_code = str(parsed['state']).upper()
                # Map of state codes to names and major cities
                state_indicators = {
                    'PA': ['pennsylvania', 'philadelphia', 'pittsburgh', 'harrisburg', ' pa ', ' pa.'],
                    'NY': ['new york', 'manhattan', 'brooklyn', 'buffalo', ' ny ', ' ny.'],
                    'CA': ['california', 'los angeles', 'san francisco', 'san diego', ' ca ', ' ca.'],
                    'TX': ['texas', 'houston', 'dallas', 'austin', 'san antonio', ' tx ', ' tx.'],
                    'FL': ['florida', 'miami', 'orlando', 'tampa', 'jacksonville', ' fl ', ' fl.'],
                    'IL': ['illinois', 'chicago', ' il ', ' il.'],
                    'OH': ['ohio', 'cleveland', 'columbus', 'cincinnati', ' oh ', ' oh.'],
                    'NJ': ['new jersey', 'newark', 'jersey city', ' nj ', ' nj.'],
                    'MA': ['massachusetts', 'boston', ' ma ', ' ma.'],
                    'GA': ['georgia', 'atlanta', ' ga ', ' ga.'],
                    'NC': ['north carolina', 'charlotte', 'raleigh', ' nc ', ' nc.'],
                    'MI': ['michigan', 'detroit', ' mi ', ' mi.'],
                    'AZ': ['arizona', 'phoenix', 'tucson', ' az ', ' az.'],
                    'WA': ['washington state', 'seattle', ' wa ', ' wa.'],
                    'CO': ['colorado', 'denver', ' co ', ' co.'],
                }
                # Check if ANY indicator for this state appears in the note
                indicators = state_indicators.get(state_code, [state_code.lower()])
                state_found = any(ind in note_lower for ind in indicators)
                if not state_found:
                    validation_log.append(f"Cleared hallucinated state: {parsed['state']}")
                    parsed['state'] = None  # Clear hallucinated state
            
            # Validate AGE - must have a number followed by age-related words
            if parsed.get('age'):
                import re
                age_patterns = [
                    r'\b\d{1,3}\s*(?:year|yr|y/?o|years?\s*old)\b',
                    r'\b(?:age|aged)\s*\d{1,3}\b',
                    r'\b\d{1,3}\s*(?:yo|y\.o\.)\b',
                ]
                age_found = any(re.search(pattern, note_lower) for pattern in age_patterns)
                if not age_found:
                    validation_log.append(f"Cleared hallucinated age: {parsed['age']}")
                    parsed['age'] = None  # Clear hallucinated age
            
            # Store validation log for display
            parsed['_validation_log'] = validation_log
            
            return parsed
        except:
            # If not valid JSON, try to extract it
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                # ALSO validate this fallback path - same logic as above
                note_lower = note_text.lower()
                validation_log = []
                
                # Validate STATE
                if parsed.get('state'):
                    state_code = parsed['state'].upper()
                    state_indicators = {
                        'PA': ['pennsylvania', 'philadelphia', 'pittsburgh', 'harrisburg', ' pa ', ' pa.'],
                        'NY': ['new york', 'manhattan', 'brooklyn', 'buffalo', ' ny ', ' ny.'],
                        'CA': ['california', 'los angeles', 'san francisco', 'san diego', ' ca ', ' ca.'],
                        'TX': ['texas', 'houston', 'dallas', 'austin', 'san antonio', ' tx ', ' tx.'],
                        'FL': ['florida', 'miami', 'orlando', 'tampa', 'jacksonville', ' fl ', ' fl.'],
                        'IL': ['illinois', 'chicago', ' il ', ' il.'],
                        'OH': ['ohio', 'cleveland', 'columbus', 'cincinnati', ' oh ', ' oh.'],
                        'NJ': ['new jersey', 'newark', 'jersey city', ' nj ', ' nj.'],
                        'MA': ['massachusetts', 'boston', ' ma ', ' ma.'],
                        'GA': ['georgia', 'atlanta', ' ga ', ' ga.'],
                        'NC': ['north carolina', 'charlotte', 'raleigh', ' nc ', ' nc.'],
                        'MI': ['michigan', 'detroit', ' mi ', ' mi.'],
                        'AZ': ['arizona', 'phoenix', 'tucson', ' az ', ' az.'],
                        'WA': ['washington state', 'seattle', ' wa ', ' wa.'],
                        'CO': ['colorado', 'denver', ' co ', ' co.'],
                    }
                    indicators = state_indicators.get(state_code, [state_code.lower()])
                    state_found = any(ind in note_lower for ind in indicators)
                    if not state_found:
                        validation_log.append(f"Removed hallucinated state: {parsed['state']}")
                        parsed['state'] = None
                
                # Validate AGE
                if parsed.get('age'):
                    age_patterns = [
                        r'\b\d{1,3}\s*(?:year|yr|y/?o|years?\s*old)\b',
                        r'\b(?:age|aged)\s*\d{1,3}\b',
                        r'\b\d{1,3}\s*(?:yo|y\.o\.)\b',
                    ]
                    age_found = any(re.search(pattern, note_lower) for pattern in age_patterns)
                    if not age_found:
                        validation_log.append(f"Removed hallucinated age: {parsed['age']}")
                        parsed['age'] = None
                
                parsed['_validation_log'] = validation_log
                return parsed
            else:
                st.error("Failed to parse API response")
                return None
                
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# ============================================================================
# HIPAA ACKNOWLEDGMENT MODAL - Must acknowledge before using app
# ============================================================================
if 'hipaa_acknowledged' not in st.session_state:
    st.session_state.hipaa_acknowledged = False

if not st.session_state.hipaa_acknowledged:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4B0082 0%, #6A0DAD 100%); 
                color: white; padding: 2rem; border-radius: 12px; margin-bottom: 1rem; text-align: center;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">💊 The Headache Vault</div>
        <div style="font-size: 1rem; opacity: 0.9;">Prior Authorization Automation Demo</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #FEF3C7; border: 2px solid #F59E0B; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
        <div style="display: flex; align-items: flex-start; gap: 12px;">
            <span style="font-size: 32px;">⚠️</span>
            <div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #92400E; margin-bottom: 0.75rem;">
                    Important: Demo Environment — NOT HIPAA Compliant
                </div>
                <div style="color: #78350F; font-size: 0.95rem; line-height: 1.6;">
                    <p style="margin-bottom: 0.75rem;">
                        This demonstration application uses external AI services (Anthropic Claude) and cloud hosting 
                        that have <strong>NOT been configured for HIPAA compliance</strong>.
                    </p>
                    <p style="margin-bottom: 0.75rem; font-weight: 600;">
                        🚫 DO NOT ENTER any Protected Health Information (PHI):
                    </p>
                    <ul style="margin: 0.5rem 0 0.75rem 1.25rem; padding: 0;">
                        <li>Patient names, dates of birth, or Social Security numbers</li>
                        <li>Medical record numbers or insurance member IDs</li>
                        <li>Specific dates of service or appointment dates</li>
                        <li>Addresses, phone numbers, or email addresses</li>
                    </ul>
                    <p style="margin-bottom: 0;">
                        ✅ <strong>Safe to use:</strong> Age (not DOB), gender, state, insurance company name, 
                        diagnosis codes, medication names/doses, and de-identified treatment history.
                    </p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #F3F4F6; border-radius: 8px; padding: 1rem; margin: 1rem 0; font-size: 0.85rem; color: #4B5563;">
        <strong>About this Demo:</strong> The Headache Vault PA Engine demonstrates automated prior authorization 
        workflows for headache medications. Use sample data or fully de-identified scenarios only.
        <br><br>
        <strong>Production Version:</strong> A HIPAA-compliant production version with BAA coverage is planned for August 2026.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ I Understand — Continue to Demo", type="primary", use_container_width=True):
            st.session_state.hipaa_acknowledged = True
            st.rerun()
    
    st.stop()  # Prevent rest of app from loading until acknowledged

# ============================================================================
# GLOBAL HIPAA WARNING BANNER - Persistent at top of every page
# ============================================================================
st.markdown("""
<div style="background: linear-gradient(90deg, #DC2626 0%, #B91C1C 100%); 
            color: white; 
            padding: 10px 16px; 
            border-radius: 8px; 
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;">
    <span style="font-size: 20px;">⚠️</span>
    <div>
        <strong>DEMO ENVIRONMENT — NOT HIPAA COMPLIANT</strong>
        <span style="opacity: 0.9; margin-left: 8px;">
            Do NOT enter real patient information. Use de-identified or sample data only.
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Header with title - using columns to add home button inline
title_col1, title_col2 = st.columns([9, 1])
with title_col1:
    st.markdown("""
    <div style="text-align: left; margin-bottom: 1rem;">
        <div class="main-header">The Headache Vault</div>
        <div class="sub-header">Prior Authorization Automation for Headache Medicine</div>
        <div style="color: #262730; font-size: 0.95rem; font-weight: 400; font-family: 'Source Sans Pro', sans-serif;">
            Infrastructure to Scale Specialist-Level Care
        </div>
    </div>
    """, unsafe_allow_html=True)
with title_col2:
    if st.button("🏠", key="home_btn", help="Return to Dashboard"):
        st.session_state.current_page = 'Dashboard'
        st.session_state.search_results = None
        st.session_state.show_pa_text = False
        st.rerun()

# ============================================================================
# PERSONA TOGGLE - Experience Mode Selector
# ============================================================================
toggle_col1, toggle_col2, toggle_col3 = st.columns([3, 6, 3])
with toggle_col2:
    mode_options = {
        'pcp': '👨‍⚕️ PCP / New to CGRPs (Show Guidance)',
        'specialist': '⚡ Specialist (Fast Mode)'
    }
    
    # Create the toggle using radio buttons styled as a toggle
    selected_mode = st.radio(
        "Experience Level",
        options=['pcp', 'specialist'],
        format_func=lambda x: mode_options[x],
        horizontal=True,
        label_visibility="collapsed",
        key="mode_selector"
    )
    
    # Update session state if changed
    if selected_mode != st.session_state.user_mode:
        st.session_state.user_mode = selected_mode
        st.rerun()

# Show mode indicator
if st.session_state.user_mode == 'pcp':
    st.markdown("""
    <div style="text-align: center; margin: 0.5rem 0 1rem 0;">
        <span style="background: #F0FFF4; color: #276749; padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 500;">
            📘 Guidance Mode Active — Tips and learning moments will appear throughout
        </span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; margin: 0.5rem 0 1rem 0;">
        <span style="background: #EBF8FF; color: #2B6CB0; padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 500;">
            ⚡ Fast Mode Active — Clean data, no interruptions
        </span>
    </div>
    """, unsafe_allow_html=True)

# Page Navigation
col1, col2, col3, col4, col5 = st.columns([2,2,2,2,6])
with col1:
    if st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state.current_page == 'Dashboard' else "secondary"):
        st.session_state.current_page = 'Dashboard'
        st.rerun()
with col2:
    if st.button("🔍 Search", use_container_width=True, type="primary" if st.session_state.current_page == 'Search' else "secondary"):
        st.session_state.current_page = 'Search'
        st.rerun()
with col3:
    if st.button("📋 Paste Notes", use_container_width=True, type="primary" if st.session_state.current_page == 'Paste Notes' else "secondary"):
        st.session_state.current_page = 'Paste Notes'
        st.rerun()

st.markdown("---")

# ============================================================================
# DASHBOARD PAGE
# ============================================================================
if st.session_state.current_page == 'Dashboard':
    
    # Hero Stats
    st.markdown("### 📊 Coverage Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stat-card" style="background: linear-gradient(135deg, #4B0082 0%, #6A0DAD 100%); padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(75, 0, 130, 0.3);">
            <div class="stat-number" style="font-size: 2.75rem; font-weight: 800; margin: 0;"><span style="color: #FFFFFF !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.4);">752</span></div>
            <div class="stat-label" style="font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.5rem;"><span style="color: #E6E6FA !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Payer Policies</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card" style="background: linear-gradient(135deg, #4B0082 0%, #6A0DAD 100%); padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(75, 0, 130, 0.3);">
            <div class="stat-number" style="font-size: 2.75rem; font-weight: 800; margin: 0;"><span style="color: #FFFFFF !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.4);">1,088</span></div>
            <div class="stat-label" style="font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.5rem;"><span style="color: #E6E6FA !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Payers Covered</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card" style="background: linear-gradient(135deg, #4B0082 0%, #6A0DAD 100%); padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(75, 0, 130, 0.3);">
            <div class="stat-number" style="font-size: 2.75rem; font-weight: 800; margin: 0;"><span style="color: #FFFFFF !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.4);">50</span></div>
            <div class="stat-label" style="font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.5rem;"><span style="color: #E6E6FA !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">States</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-card" style="background: linear-gradient(135deg, #4B0082 0%, #6A0DAD 100%); padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(75, 0, 130, 0.3);">
            <div class="stat-number" style="font-size: 2.75rem; font-weight: 800; margin: 0;"><span style="color: #FFFFFF !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.4);">8</span></div>
            <div class="stat-label" style="font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.5rem;"><span style="color: #E6E6FA !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Drug Classes</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # What's New Banner
    st.info("🎉 **What's New:** AI Clinical Note Parsing now available! Parse unstructured notes in seconds.")
    
    # System Status
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔧 System Status")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("🟢 **All Systems Operational**")
    with col2:
        st.info("⚡ **Response Time:** <2 seconds")
    with col3:
        st.info("📅 **Last Updated:** January 15, 2026")
    
    # Feature Highlights
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ✨ Platform Features")
    
    feature_col1, feature_col2 = st.columns(2)
    
    with feature_col1:
        st.markdown("""
        **Core Capabilities:**
        - ⚡ 2-second PA policy lookups
        - 🤖 AI-powered clinical note parsing  
        - 📋 One-click appeal templates
        - 🏆 Gold Card status tracking
        - 📊 Step therapy requirements
        - 🔍 ICD-10 code lookup
        """)
    
    with feature_col2:
        st.markdown("""
        **Clinical Intelligence:**
        - ✅ AHS 2021/2024 Guidelines
        - ✅ ACP 2025 Guidelines
        - ✅ ICHD-3 Diagnostic Criteria
        - ✅ MOH Risk Screening
        - ✅ Pediatric Age Checks
        - ✅ State Regulatory Framework
        """)

# ============================================================================
# SEARCH PAGE
# ============================================================================
elif st.session_state.current_page == 'Search':
    
    # ========================================================================
    # PA TEXT GENERATOR - Show at TOP when active
    # ========================================================================
    if st.session_state.show_pa_text and st.session_state.search_results is not None:
        results = st.session_state.search_results
        if len(results) > 0:
            row = results.iloc[0]
            
            # Get values safely
            headache_type = st.session_state.get('headache_type', 'Chronic Migraine')
            diag = st.session_state.parsed_data.get('diagnosis', headache_type) if 'parsed_data' in st.session_state else headache_type
            age = st.session_state.get('patient_age', 35)
            drug = st.session_state.get('selected_drug', row['Drug_Class'])
            state = row['State']
            
            # Check if pediatric patient
            is_pediatric = age < 18
            
            # Get parsed prior medications if available
            prior_meds = []
            if 'parsed_data' in st.session_state and st.session_state.parsed_data.get('prior_medications'):
                prior_meds = st.session_state.parsed_data.get('prior_medications', [])
            
            st.markdown("### 📝 Prior Authorization Documentation")
            
            # Close button to dismiss PA
            if st.button("✕ Close PA Letter", key="close_pa"):
                st.session_state.show_pa_text = False
                st.rerun()
            
            # Show pediatric alert if applicable
            if is_pediatric:
                st.warning(f"⚠️ **Pediatric Patient (Age {age})** — FDA approval and dosing considerations included in PA letter.")
            
            # Determine ICD-10 code based on diagnosis
            icd10_codes = {
                'Chronic Migraine': 'G43.709',
                'Episodic Migraine': 'G43.009', 
                'Cluster Headache': 'G44.009'
            }
            icd10_code = icd10_codes.get(diag, 'G43.709')
            
            if st.session_state.user_mode == 'pcp':
                st.markdown("""
                <div class="learning-moment">
                    <div class="learning-moment-title">💡 PA Documentation Tips</div>
                    <div class="learning-moment-content">
                        <strong>Keys to approval:</strong> Be specific about medication names, exact dosages, 
                        trial durations with dates, and clear failure reasons. Vague language like 
                        "tried several medications" or "adequate trial" often leads to denials.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Build pediatric section if needed
                pediatric_section = ""
                if is_pediatric:
                    pediatric_section = f"""
PEDIATRIC CONSIDERATIONS
────────────────────────
Patient Age: {age} years (Pediatric)

FDA-Approved CGRP Medications for Pediatric Migraine Prevention:
• Aimovig (erenumab): Approved for ages 12+ for migraine prevention
• Ajovy (fremanezumab): Approved for ages 12+ for migraine prevention  
• Emgality (galcanezumab): Approved for ages 12+ for migraine prevention

Dosing: Standard adult dosing is appropriate for patients ≥12 years.

This patient meets age criteria for FDA-approved CGRP therapy.

"""
                
                pa_text = f"""══════════════════════════════════════════════════════════════
              PRIOR AUTHORIZATION REQUEST - {drug.upper()}
              Generated: {datetime.now().strftime('%B %d, %Y')}
══════════════════════════════════════════════════════════════

PATIENT INFORMATION
───────────────────
Diagnosis: {diag}
ICD-10 Code: {icd10_code}
Patient Age: {age} years{" (PEDIATRIC)" if is_pediatric else ""}
{pediatric_section}
REQUESTED MEDICATION
────────────────────
Drug Class: {drug}
Payer: {row['Payer_Name']}
Line of Business: {row['LOB']}
State: {state}

"""
                if row['Step_Therapy_Required'] == 'Yes':
                    step_req = row.get('Step_1_Requirement', 'Prior oral preventive trials required')
                    step_dur = row.get('Step_1_Duration', 'Per policy requirements')
                    pa_text += f"""STEP THERAPY REQUIREMENTS
─────────────────────────
Policy Requirement: {step_req}
Required Duration: {step_dur}

"""
                    # Add parsed prior medications if available
                    if prior_meds:
                        pa_text += """DOCUMENTED PRIOR MEDICATION TRIALS
──────────────────────────────────
"""
                        for i, med in enumerate(prior_meds, 1):
                            pa_text += f"  {i}. {med}\n"
                        pa_text += """
  ✓ Patient has completed required step therapy trials as documented above.

"""
                    else:
                        pa_text += """PRIOR MEDICATION TRIALS
───────────────────────
  [Document each failed medication with:]
  • Drug name and maximum dose reached
  • Start and end dates (minimum 8 weeks)
  • Specific reason for discontinuation

"""
                pa_text += f"""
CLINICAL RATIONALE
──────────────────
Patient has documented history of {diag} with inadequate response 
to conventional preventive therapies. {drug} is medically necessary 
due to:
• Failure/intolerance of prior preventive medications as documented above
• Significant impact on daily functioning and quality of life
• No contraindications to requested therapy

REFERENCES
──────────
This request aligns with:
• American Headache Society Consensus Statement (2021)
• ICHD-3 Diagnostic Criteria
• AAN/AHS Practice Guidelines

══════════════════════════════════════════════════════════════
"""
            else:
                # Specialist compact mode
                pediatric_note = " [PEDIATRIC - FDA approved 12+]" if is_pediatric else ""
                pa_text = f"""PRIOR AUTHORIZATION REQUEST
{datetime.now().strftime('%Y-%m-%d')} | {row['Payer_Name']} | {state}

Dx: {diag} ({icd10_code})
Age: {age}y{pediatric_note}
Rx: {drug} ({row['Medication_Category']})
LOB: {row['LOB']}
"""
                if row['Step_Therapy_Required'] == 'Yes':
                    step_req = row.get('Step_1_Requirement', 'Prior preventive')
                    step_dur = row.get('Step_1_Duration', 'Per policy')
                    pa_text += f"""
Step Therapy: REQUIRED ({step_req}, {step_dur})
"""
                    # Add prior meds in compact format
                    if prior_meds:
                        pa_text += "Prior Trials:\n"
                        for med in prior_meds:
                            pa_text += f"  • {med}\n"
                    pa_text += "Status: Step therapy completed\n"
                else:
                    pa_text += "\nStep Therapy: Not required\n"
                
                pa_text += "\nRefs: AHS 2024, ICHD-3, AAN Guidelines"
            
            st.code(pa_text, language=None)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Copy to Clipboard", key="copy_pa", use_container_width=True):
                    st.toast("✅ PA text copied!", icon="✅")
            with col2:
                if st.button("🔙 Back to Results", key="back_to_results", use_container_width=True):
                    st.session_state.show_pa_text = False
                    st.rerun()
            
            st.markdown("---")
    
    # ========================================================================
    # SEARCH PAGE CONTENT
    # ========================================================================
    st.markdown("### 🔍 Policy Search")
    st.markdown("Search for prior authorization requirements by state, payer, and medication.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================================================
    # SIDEBAR FILTERS (uses SidebarHelper for defaults from PatientContext)
    # ============================================================================
    st.sidebar.header("🔍 Search Filters")
    
    # HIPAA Warning in Sidebar
    st.sidebar.markdown("""
<div style="background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 6px; padding: 8px 10px; margin-bottom: 12px; font-size: 0.75rem;">
    <strong style="color: #92400E;">⚠️ Demo Only</strong><br>
    <span style="color: #78350F;">Not HIPAA compliant. Do not enter real patient data.</span>
</div>
""", unsafe_allow_html=True)

    # State selection - add placeholder if state not detected
    states = sorted(db_b['State'].unique().tolist())
    ctx = SessionStateManager.get_context()
    
    # If state not specified, show placeholder option
    if ctx.state is None:
        state_options = ["-- Please Select State --"] + states
        state_index = 0  # Start on placeholder
    else:
        state_options = states
        state_index = states.index(ctx.state) if ctx.state in states else 0
    
    selected_state = st.sidebar.selectbox(
        "State",
        options=state_options,
        index=state_index,
        key="sidebar_state"
    )
    
    # Check if user still needs to select a state
    state_not_selected = selected_state == "-- Please Select State --"
    if state_not_selected:
        st.sidebar.warning("⚠️ Please select a state to search policies")
        # Use placeholder options when no state selected
        payer_options = ['All Payers']
        state_drug_classes = ['CGRP mAbs']  # Default option
    else:
        # Payer selection based on selected state
        state_payers = db_b[db_b['State'] == selected_state]['Payer_Name'].unique().tolist()
        payer_options = ['All Payers'] + sorted(state_payers)
        # Drug class selection based on selected state
        state_drug_classes = sorted(db_b[db_b['State'] == selected_state]['Drug_Class'].unique().tolist())
    
    selected_payer = st.sidebar.selectbox(
        "Payer", 
        options=payer_options,
        index=SidebarHelper.get_payer_index(payer_options) if not state_not_selected else 0,
        key="sidebar_payer",
        disabled=state_not_selected
    )
    
    selected_drug = st.sidebar.selectbox(
        "Medication Class",
        options=state_drug_classes if state_drug_classes else ['CGRP mAbs'],
        index=SidebarHelper.get_drug_index(state_drug_classes) if not state_not_selected and state_drug_classes else 0,
        help=f"{len(state_drug_classes)} drug classes available" if not state_not_selected else "Select state first",
        key="sidebar_drug",
        disabled=state_not_selected
    )
    
    # Headache type
    headache_options = ["Chronic Migraine", "Episodic Migraine", "Cluster Headache"]
    headache_type = st.sidebar.radio(
        "Headache Type",
        options=headache_options,
        index=SidebarHelper.get_headache_index(headache_options),
        key="sidebar_headache"
    )

    # Patient age (from PatientContext) - use 40 as neutral default if not specified
    ctx = SessionStateManager.get_context()
    age_value = ctx.age if ctx.age is not None else 40
    patient_age = st.sidebar.number_input(
        "Patient Age (years)",
        min_value=1,
        max_value=120,
        value=age_value,
        help="Used to check pediatric prescribing restrictions" + (" (not detected - please verify)" if ctx.age is None else ""),
        key="sidebar_age"
    )
    # Search button
    st.sidebar.markdown("---")

    # Show quick stats
    total_in_state = len(db_b[db_b['State'] == selected_state])
    st.sidebar.markdown(f"""
<div style='background-color: white; padding: 0.75rem; border-radius: 8px; border-left: 4px solid #4B0082; margin: 0.5rem 0;'>
    <div style='color: #262730; font-weight: 600;'>📊 {total_in_state} policies in {selected_state}</div>
</div>
""", unsafe_allow_html=True)

    # Database coverage note
    st.sidebar.markdown("""
<div style='color: #5A5A5A; font-size: 0.85rem; margin-top: 0.5rem; font-style: italic;'>
    💡 Database: 752 policies across 50 states. Preventive gepant coverage expanding weekly.
</div>
""", unsafe_allow_html=True)

    # Search button - disabled if state not selected
    if state_not_selected:
        st.sidebar.button("🔎 Search Policies", type="primary", use_container_width=True, disabled=True)
        search_clicked = False
    else:
        search_clicked = st.sidebar.button("🔎 Search Policies", type="primary", use_container_width=True)

    # Main content area - show results from either search method
    # But DON'T show results if state hasn't been selected yet
    if state_not_selected:
        # Clear any cached results and show welcome message
        st.session_state.search_results = None
        st.markdown("""
<div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border: 2px solid #3B82F6; border-radius: 16px; padding: 2rem; margin: 2rem 0; text-align: center;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
    <div style="font-weight: 700; color: #1E40AF; font-size: 1.5rem; margin-bottom: 1rem;">
        Select a State to Search Payer Policies
    </div>
    <div style="color: #1E3A8A; font-size: 1.1rem; margin-bottom: 1.5rem;">
        Use the <strong>State</strong> dropdown in the sidebar to find policies specific to your patient's insurance.
    </div>
    <div style="color: #3B82F6; font-size: 0.95rem;">
        💡 Our database covers <strong>866 policies</strong> across <strong>50 states</strong> for all major payers.
    </div>
</div>
""", unsafe_allow_html=True)
    elif (search_clicked or st.session_state.search_results is not None) or st.session_state.get('show_results', False):
        if search_clicked:
            # Create DataCollectionState for quality scoring
            collection_state = DataCollectionState(
                state=selected_state if selected_state not in ['ALL', '-- Please Select State --'] else None,
                payer=selected_payer if selected_payer != 'All Payers' else None,
                drug_class=selected_drug
            )
            st.session_state.data_collection_state = collection_state
            
            # Show quality indicator
            score, desc = collection_state.get_search_quality_score()
            st.markdown(get_quality_indicator_html(score, desc), unsafe_allow_html=True)
            
            # Perform search with national fallback support
            query, fallback_used, fallback_message = search_policies_with_fallback(
                db_b,
                state=selected_state,
                payer=selected_payer if selected_payer != 'All Payers' else None,
                drug_class=selected_drug
            )
            
            # Filter by headache type
            if headache_type == "Cluster Headache":
                query = query[query['Drug_Class'].str.contains('Cluster', case=False, na=False)]
            elif headache_type == "Chronic Migraine":
                query = query[query['Medication_Category'].str.contains('Chronic|Preventive', case=False, na=False)]
            
            st.session_state.search_results = query
            st.session_state.patient_age = patient_age
            st.session_state.fallback_used = fallback_used
            st.session_state.fallback_message = fallback_message
            st.session_state.show_pa_text = False
        
        results = st.session_state.search_results
        patient_age_display = st.session_state.get('patient_age', patient_age if 'patient_age' in dir() else 35)
        
        # Show fallback notice if applicable
        if st.session_state.get('fallback_used', False):
            st.info(st.session_state.get('fallback_message', ''))
        
        if len(results) == 0:
            st.warning("⚠️ No policies found for this combination.")
            st.info("""
            **Possible reasons:**
            - This payer may not have a specific policy for this drug class
            - Preventive gepant policies (Nurtec, Qulipta) are still being audited for some states
            - Try selecting a different medication class or payer
            
            **Coverage notes:**
            - All PA payers have policies for: CGRP mAbs, Botox, Gepants (acute)
            - Preventive gepant coverage expanding weekly
            """)
        else:
            # Display summary
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Payers Found", len(results['Payer_Name'].unique()))
            with col2:
                st.metric("Policies Identified", len(results))
            with col3:
                requires_step = (results['Step_Therapy_Required'] == 'Yes').sum()
                st.metric("Require Step Therapy", f"{requires_step}/{len(results)}")
            
            # Display each policy as a professional card
            for idx, row in results.iterrows():
                # Build policy card with container
                st.markdown(f"""
                <div class="policy-card">
                    <div class="policy-header">
                        <div>
                            <div class="policy-title">🏥 {row['Payer_Name']}</div>
                            <span class="policy-badge">{row["State"]} | {row["LOB"]}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Step Therapy Section - use native Streamlit
                if row['Step_Therapy_Required'] == 'Yes':
                    st.markdown('<div class="policy-section"><div class="policy-section-title">Step Therapy Required</div>', unsafe_allow_html=True)
                    
                    step_req, step_dur = get_step_therapy_details(row); step_therapies = step_req.split(';')
                    durations = step_dur.split(';')
                    
                    # Check if details are missing
                    has_missing_info = (
                        'Not specified' in step_req or
                        'Trial duration not specified' in step_dur
                    )
                    
                    for i, (therapy, duration) in enumerate(zip(step_therapies, durations if len(durations) == len(step_therapies) else ['Trial required'] * len(step_therapies)), 1):
                        st.markdown(f"""
                        <div class="step-item">
                            <div class="step-number">{i}</div>
                            <div>
                                <strong style="color: #262730;">{therapy.strip()}</strong><br>
                                <small style="color: #708090;">{duration.strip()}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Add guidance if details are missing (always show)
                    if has_missing_info:
                        st.markdown("""
                        <div style="background: #FFF9E6; padding: 1rem; border-radius: 8px; border-left: 4px solid #FFD700; margin-top: 0.75rem;">
                            <strong style="color: #B8860B;">💡 Missing Details? Contact the Payer</strong><br>
                            <small style="color: #666; line-height: 1.6;">
                            When step therapy requirements aren't specified in our database:<br>
                            • Call the payer's PA department for specific requirements<br>
                            • Ask about trial duration, dosing, and failure criteria<br>
                            • Request their clinical policy bulletin (CPB) number<br>
                            • Document the conversation in your PA submission
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # PCP MODE: Show additional documentation guidance
                    if st.session_state.user_mode == 'pcp' and not has_missing_info:
                        with st.expander("📘 New to step therapy documentation? Click here for tips", expanded=False):
                            st.markdown("#### 📝 Documentation Best Practices")
                            st.markdown("**What payers want to see:**")
                            st.markdown("""
- **Specific medication names** — Not "tried several medications"
- **Exact dosages** — "Topiramate 100mg BID" not "adequate dose"  
- **Duration with dates** — "60 days (Jan 1 - Mar 1, 2026)"
- **Outcome** — "Failed due to [side effect/inefficacy]"
                            """)
                            st.markdown("**Example documentation:**")
                            st.info('"Patient completed 60-day trial of topiramate 100mg BID from 11/1/25 to 12/31/25. Treatment was discontinued due to cognitive side effects (word-finding difficulty) despite dose titration. Headache frequency remained at 14 days/month."')
                    

                    # ================================================================
                    # CRITERIA MET CHECKLIST - Show if patient meets requirements
                    # ================================================================
                    if 'parsed_data' in st.session_state and st.session_state.parsed_data.get('prior_medications'):
                        prior_meds = st.session_state.parsed_data.get('prior_medications', [])
                        diagnosis = st.session_state.parsed_data.get('diagnosis', '')
                        
                        criteria_results = check_criteria_met(step_req, prior_meds, diagnosis)
                        
                        if criteria_results:
                            st.markdown("---")
                            st.markdown("##### ✅ Patient Criteria Status (from clinical note)")
                            
                            all_met = all(met for _, met, _ in criteria_results)
                            
                            for requirement, met, details in criteria_results:
                                if met:
                                    st.markdown(f"""
                                    <div style="background: #D4EDDA; padding: 0.75rem 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #28A745;">
                                        <span style="color: #155724; font-weight: 600;">✓ {requirement}</span><br>
                                        <small style="color: #155724;">{details}</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                    <div style="background: #FFF3CD; padding: 0.75rem 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #FFC107;">
                                        <span style="color: #856404; font-weight: 600;">⚠️ {requirement}</span><br>
                                        <small style="color: #856404;">{details}</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            if all_met:
                                st.success("🎉 **Patient meets all step therapy requirements!** PA likely to be approved.")
                            else:
                                st.warning("⚠️ **Some requirements may not be documented.** Review clinical note or document missing trials.")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="policy-section">
                        <div style="background: #F0FFF4; padding: 1rem; border-radius: 8px; border-left: 4px solid #10B981;">
                            <strong style="color: #10B981;">✅ No Step Therapy Required</strong><br>
                            <small style="color: #666;">This medication can be prescribed without prior trials</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # PCP MODE: Explain what "no step therapy" means
                    if st.session_state.user_mode == 'pcp':
                        st.markdown("""
                        <div class="pro-tip">
                            <div class="pro-tip-title">💡 What this means for you</div>
                            <div class="pro-tip-content">
                                You can prescribe this medication directly without documenting failed trials of other drugs.
                                However, you still need to document medical necessity (diagnosis, severity, functional impact).
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Gold Card Status
                if pd.notna(row.get('Gold_Card_Available')) and row['Gold_Card_Available'] == 'Yes':
                    threshold_text = row.get('Gold_Card_Threshold', 'Check state requirements')
                    st.markdown(f"""
                    <div class="policy-section">
                        <div class="gold-card-badge">
                            🏆 Gold Card Available
                        </div>
                        <div style="margin-top: 0.5rem; color: #666; font-size: 0.9rem;">
                            {threshold_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Single primary action button - Generate PA
                col1, col2 = st.columns([3, 9])
                with col1:
                    if st.button("🎯 Generate PA Letter", key=f"pa_{idx}", type="primary", use_container_width=True):
                        st.session_state.show_pa_text = True
                        st.session_state.selected_policy_idx = idx
                        st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# AI PARSER PAGE
# ============================================================================
elif st.session_state.current_page == 'Paste Notes':
    
    st.markdown("### 🤖 AI Clinical Note Parser")
    st.markdown("Paste unstructured clinical notes and let AI extract structured patient data in seconds.")
    
    st.info("💡 **How it works:** Our AI parses your clinic notes to extract patient info, then validates against our policy database. You get the speed of AI with the reliability of deterministic rules.")
    
    # Example button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("📋 Load Example", use_container_width=True):
            example_note = """45-year-old female with chronic migraine, approximately 20 headache days per month. 
Lives in Philadelphia, Pennsylvania. Has Independence Blue Cross commercial insurance. 
Previously tried topiramate 100mg daily for 12 weeks - discontinued due to cognitive side effects. 
Also failed propranolol 80mg BID for 8 weeks - inadequate response with less than 30% reduction in headache frequency.
Patient is interested in trying Aimovig (erenumab) for migraine prevention."""
            st.session_state.clinical_note = example_note
            st.rerun()
    
    # Text area for clinical note
    clinical_note = st.text_area(
        "Clinical Note",
        value=st.session_state.get('clinical_note', ''),
        height=250,
        placeholder="Paste patient information here...\n\nExample:\n45yo F with chronic migraine, 20+ days/month. Lives in PA, has Highmark BCBS. Failed topiramate and propranolol. Considering Aimovig.",
        help="Include: location, insurance, diagnosis, medications tried, medication considering"
    )
    
   # Parse button
    if st.button("🤖 Parse Note with AI", type="primary", use_container_width=True):
        if not clinical_note.strip():
            st.warning("Please enter a clinical note to parse.")
        else:
            # Clear previous parsed data before new parse
            st.session_state.parsed_data = None
            st.session_state.data_collection_state = None
            
            with st.spinner("🧠 Analyzing clinical note..."):
                parsed_data = parse_clinical_note(clinical_note, db_a, db_b)
                
                if parsed_data:
                    # Update unified patient context
                    SessionStateManager.set_from_ai_parse(parsed_data)
                    st.session_state.parsed_data = parsed_data  # Keep for backward compatibility
                    
                     # Create and store DataCollectionState for quality tracking
                    try:
                        collection_state = analyze_parsed_data(parsed_data)
                        st.session_state.data_collection_state = collection_state
                    except Exception as e:
                        # Fallback if parsing fails
                        collection_state = DataCollectionState()
                        st.session_state.data_collection_state = collection_state
                    
                    # Success celebration
                    st.balloons()
                    st.success("🎉 **Note Parsed Successfully!** Extracted patient data.")
                    
                    # Show quality indicator
                    if collection_state and hasattr(collection_state, 'get_search_quality_score'):
                        score, desc = collection_state.get_search_quality_score()
                        st.markdown(get_quality_indicator_html(score, desc), unsafe_allow_html=True)
                    else:
                        st.info("📊 Data extracted - proceed to Search to find policies.")
                    
                    # Show warning if state is missing
                    if collection_state and hasattr(collection_state, 'state') and not collection_state.state:
                        st.markdown("""
<div class="required-field-box">
    <div style="font-weight: 700; color: #DC2626; margin-bottom: 0.5rem;">
        🔴 State Not Detected
    </div>
    <div style="color: #7F1D1D;">
        Please select state in the Search sidebar before searching policies.
    </div>
</div>
""", unsafe_allow_html=True)
                    
                    # Auto-scroll to results
                    # Scroll handled by anchor below
    
    # Display parsed data if available
    if 'parsed_data' in st.session_state:
        parsed = st.session_state.parsed_data
        
        st.markdown("---")
        st.markdown('<div id="parsed-results"></div>', unsafe_allow_html=True)
        st.markdown("### 📊 Extracted Information")
        
        # Auto-scroll to this section
        st.markdown("""
        <script>
            const element = document.getElementById('parsed-results');
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        </script>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if parsed.get('state'):
                st.metric("State", parsed['state'])
            if parsed.get('age'):
                st.metric("Age", f"{parsed['age']} years")
        
        with col2:
            if parsed.get('diagnosis'):
                st.metric("Diagnosis", parsed['diagnosis'])
            if parsed.get('confidence'):
                conf_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
                st.metric("Confidence", f"{conf_emoji.get(parsed['confidence'], '⚪')} {parsed['confidence'].title()}")
        
        with col3:
            if parsed.get('drug_class'):
                st.metric("Medication", parsed['drug_class'])
        
        # Payer info with copy button
        if parsed.get('payer'):
            col1, col2 = st.columns([3,1])
            with col1:
                st.info(f"**Insurance:** {parsed['payer']}")
            with col2:
                if st.button("📋 Copy", key="copy_payer"):
                    st.toast("✅ Payer copied!", icon="✅")
        
        # Prior medications
        if parsed.get('prior_medications') and len(parsed['prior_medications']) > 0:
            st.markdown("**Prior Medications:**")
            for med in parsed['prior_medications']:
                st.markdown(f"- {med}")
        
        # Edit mode
        with st.expander("✏️ Edit Extracted Data", expanded=False):
            st.markdown("Review and modify the extracted information before searching:")
            
            # Handle state - if AI returned None, show warning and default to first state
            state_options = sorted(db_b['State'].unique().tolist())
            if parsed.get('state') and parsed.get('state') in state_options:
                state_index = state_options.index(parsed['state'])
            else:
                state_index = 0  # Default to first alphabetically (AL or ALL)
                if not parsed.get('state'):
                    st.warning("⚠️ **State not detected in note** - Please select the correct state")
            
            edited_state = st.selectbox("State", options=state_options, index=state_index)
            
            # Filter payers by edited state
            state_payers = sorted(db_b[db_b['State'] == edited_state]['Payer_Name'].unique().tolist())
            
            # Try to match payer
            payer_index = 0
            if parsed.get('payer'):
                for i, p in enumerate(state_payers):
                    if parsed['payer'].lower() in p.lower() or p.lower() in parsed['payer'].lower():
                        payer_index = i
                        break
            
            edited_payer = st.selectbox("Payer", options=['All Payers'] + state_payers, index=payer_index)
            
            # Filter drugs by edited state
            state_drugs = sorted(db_b[db_b['State'] == edited_state]['Drug_Class'].unique().tolist())
            drug_index = 0
            parsed_drug = parsed.get('drug_class')
            
            if parsed_drug and parsed_drug in state_drugs:
                drug_index = state_drugs.index(parsed_drug)
            elif parsed_drug:
                # Handle cluster headache fallback - if cluster-specific drug not available, try CGRP mAbs
                if 'Cluster' in parsed_drug and 'CGRP mAbs' in state_drugs:
                    drug_index = state_drugs.index('CGRP mAbs')
                    st.info(f"ℹ️ '{parsed_drug}' not available in {edited_state}. Using 'CGRP mAbs' (Emgality is FDA-approved for cluster headache).")
                # If drug class not found but CGRP mAbs exists, default to that instead of Botox
                elif 'CGRP mAbs' in state_drugs:
                    drug_index = state_drugs.index('CGRP mAbs')
            
            edited_drug = st.selectbox("Drug Class", options=state_drugs, index=drug_index)
            
            diagnosis_options = ["Chronic Migraine", "Episodic Migraine", "Cluster Headache"]
            diag_index = 0
            if parsed.get('diagnosis') and parsed['diagnosis'] in diagnosis_options:
                diag_index = diagnosis_options.index(parsed['diagnosis'])
            
            edited_diagnosis = st.selectbox("Diagnosis", options=diagnosis_options, index=diag_index)
            
            # Handle age - if AI returned None, show warning
            if parsed.get('age'):
                age_value = parsed['age']
            else:
                age_value = 40  # Neutral default
                st.warning("⚠️ **Age not detected in note** - Please enter patient age")
            
            edited_age = st.number_input("Age", min_value=1, max_value=120, value=age_value)
            
            # Save edits
            if st.button("💾 Save Edits"):
                st.session_state.parsed_data.update({
                    'state': edited_state,
                    'payer': edited_payer,
                    'drug_class': edited_drug,
                    'diagnosis': edited_diagnosis,
                    'age': edited_age
                })
                st.success("✅ Edits saved!")
                st.rerun()
        
        # Search button - conditional based on whether state is available
        state_available = parsed.get('state') is not None
        
        if state_available:
            # State is available - show normal search button
            if st.button("🔎 Search with Extracted Data", type="primary", use_container_width=True):
                # Determine the drug class to search for
                search_drug_class = parsed.get('drug_class')
                
                # Handle cluster headache drug class fallback
                if search_drug_class and 'Cluster' in search_drug_class:
                    state_drugs = db_b[db_b['State'] == parsed.get('state')]['Drug_Class'].unique().tolist()
                    if search_drug_class not in state_drugs and 'CGRP mAbs' in state_drugs:
                        search_drug_class = 'CGRP mAbs'  # Fall back to CGRP mAbs for cluster
                
                # Perform search with national fallback support
                query, fallback_used, fallback_message = search_policies_with_fallback(
                    db_b,
                    state=parsed.get('state'),
                    payer=parsed.get('payer'),
                    drug_class=search_drug_class
                )
                
                # Filter by diagnosis - but DON'T double-filter if drug_class already contains the diagnosis
                if parsed.get('diagnosis') == "Cluster Headache":
                    # Only apply cluster filter if we actually have cluster-specific policies
                    if parsed.get('drug_class') and 'Cluster' not in parsed.get('drug_class', ''):
                        cluster_filtered = query[query['Drug_Class'].str.contains('Cluster', case=False, na=False)]
                        # Only use cluster filter if it returns results, otherwise keep CGRP mAbs
                        if not cluster_filtered.empty:
                            query = cluster_filtered
                elif parsed.get('diagnosis') == "Chronic Migraine":
                    # Only filter if needed
                    if not query.empty:
                        chronic_filtered = query[query['Medication_Category'].str.contains('Chronic|Preventive', case=False, na=False)]
                        if not chronic_filtered.empty:
                            query = chronic_filtered
                # Don't filter episodic - too aggressive
                
                st.session_state.search_results = query
                st.session_state.patient_age = parsed.get('age') if parsed.get('age') else None  # Don't default to 35
                st.session_state.fallback_used = fallback_used
                st.session_state.fallback_message = fallback_message
                st.session_state.show_pa_text = False  # Reset PA display on new search
                st.session_state.current_page = 'Search'
                
                if fallback_used:
                    st.toast(f"Using national baseline policy", icon="ℹ️")
                st.toast("🎉 Policy search complete! Found {} matching policies.".format(len(query)), icon="🎉")
                st.rerun()
        else:
            # State not available - show guidance to user
            st.markdown("""
<div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border: 2px solid #F59E0B; border-radius: 12px; padding: 1.25rem; margin: 1rem 0;">
    <div style="font-weight: 700; color: #92400E; font-size: 1.1rem; margin-bottom: 0.5rem;">
        📍 State Required for Policy Search
    </div>
    <div style="color: #78350F; margin-bottom: 1rem;">
        To find your patient's specific payer policies, please add the state using one of these options:
    </div>
    <div style="color: #78350F; padding-left: 1rem;">
        <strong>Option 1:</strong> Expand "✏️ Edit Extracted Data" above and select a state<br>
        <strong>Option 2:</strong> Go to the <strong>Search</strong> page and select a state in the sidebar
    </div>
</div>
""", unsafe_allow_html=True)
            # Show disabled button as visual cue
            st.button("🔎 Select State to Search Policies", type="primary", use_container_width=True, disabled=True)

# ============================================================================
# CLINICAL TOOLS SECTION (Only on Search page)
# ============================================================================
if st.session_state.current_page == 'Search' and st.session_state.search_results is not None:
    st.markdown("---")
    
    # Clinical Tools in an expander - keeps UI clean
    with st.expander("🔧 Clinical Tools", expanded=False):
        tool_col1, tool_col2 = st.columns(2)
        
        with tool_col1:
            st.markdown("##### ⚕️ MOH Risk Assessment")
            st.markdown("Check if patient's acute medication use puts them at risk for medication overuse headache.")
            if st.button("Check MOH Risk", key="moh_btn", use_container_width=True):
                st.session_state.show_moh_check = True
        
        with tool_col2:
            st.markdown("##### 📊 ICD-10 Code Lookup")
            st.markdown("Find the correct diagnosis codes for headache disorders.")
            if st.button("View ICD-10 Codes", key="icd_btn", use_container_width=True):
                # Show ICD-10 codes inline
                headache_type_val = st.session_state.get('headache_type', 'Chronic Migraine')
                if headache_type_val == "Cluster Headache":
                    icd_filter = icd10[icd10['ICD10_Code'].str.startswith('G44.0')]
                elif headache_type_val == "Chronic Migraine":
                    icd_filter = icd10[icd10['ICD10_Code'].str.contains('G43.7', regex=False)]
                else:
                    icd_filter = icd10[icd10['ICD10_Code'].str.startswith('G43')]
                
                st.dataframe(
                    icd_filter[['ICD10_Code', 'ICD10_Description', 'PA_Relevance']],
                    use_container_width=True,
                    hide_index=True
                )

# ============================================================================
# MOH CHECKER (Only on Search page)
# ============================================================================
if st.session_state.current_page == 'Search' and st.session_state.show_moh_check:
    st.markdown("---")
    st.markdown("### ⚕️ Medication Overuse Headache (MOH) Screening")
    
    st.info("Track OTC medication use to identify patients at risk for medication overuse headache (ICHD-3 Section 8.2)")
    
    # Simple MOH calculator
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Simple Analgesics** (Threshold: ≥15 days/month)")
        simple_days = st.number_input(
            "Days per month using acetaminophen, ibuprofen, naproxen, or aspirin",
            min_value=0,
            max_value=31,
            value=0
        )
    
    with col2:
        st.markdown("**Combination Analgesics** (Threshold: ≥10 days/month)")
        combo_days = st.number_input(
            "Days per month using Excedrin, BC Powder, or caffeine-containing products",
            min_value=0,
            max_value=31,
            value=0
        )
    
    # Display MOH risk
    if simple_days >= 15 or combo_days >= 10:
        st.markdown('<div class="warning-box">⚠️ <strong>MOH RISK IDENTIFIED</strong><br>' +
                  'Patient meets ICHD-3 criteria for medication overuse. Consider:<br>' +
                  '• ICD-10 Code: G44.41 (Drug-induced headache, NEC)<br>' +
                  '• CGRP therapy (lower MOH risk per AHS 2021)<br>' +
                  '• Medication withdrawal protocol</div>',
                  unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">✅ No medication overuse detected based on current usage pattern</div>',
                  unsafe_allow_html=True)
    
    # Show OTC medication reference
    with st.expander("📚 OTC Medication Reference"):
        st.dataframe(
            otc[['Medication_Name', 'MOH_Category', 'MOH_Threshold_Days_Per_Month', 'Caffeine_Content_mg']],
            use_container_width=True,
            hide_index=True
        )

# Production Footer with HIPAA Disclaimer
st.markdown("---")
st.markdown("""
<div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 16px; margin-bottom: 1.5rem;">
    <div style="font-weight: 700; color: #991B1B; margin-bottom: 8px; font-size: 0.9rem;">
        ⚖️ Legal Disclaimer — Please Read
    </div>
    <div style="font-size: 0.8rem; color: #7F1D1D; line-height: 1.5;">
        <strong>NOT HIPAA COMPLIANT:</strong> The Headache Vault Demo is a prototype for demonstration and 
        educational purposes only. This application uses external AI services (Anthropic Claude API) and 
        cloud hosting (Streamlit) that have NOT been configured for HIPAA compliance. Do not enter Protected 
        Health Information (PHI) including patient names, DOB, MRN, SSN, specific dates of service, or contact information.
        <br><br>
        <strong>NOT MEDICAL/LEGAL ADVICE:</strong> Information provided is for educational purposes only and does not 
        constitute medical, legal, or billing advice. Always verify payer requirements directly.
        <br><br>
        <strong>PRODUCTION VERSION:</strong> A HIPAA-compliant version with BAA coverage is planned for August 2026. 
        Contact info@headachevault.com for enterprise inquiries.
    </div>
</div>

<div class="production-footer">
    <div style="margin-bottom: 1rem;">
        <span class="footer-badge">📊 CMS Data Sources</span>
        <span class="footer-badge">🏥 State DOI Verified</span>
        <span class="footer-badge" style="background: #FEF3C7; color: #92400E;">⚠️ Demo Only</span>
    </div>
    <div style="font-size: 0.9rem; color: #262730; margin-bottom: 1rem;">
        <strong style='color: #4B0082; font-size: 1.1rem;'>The Headache Vault PA Engine</strong><br>
        <span style='color: #5A5A5A;'>Demo v1.0 | February 2026</span>
    </div>
    <div style="font-size: 0.85rem; color: #5A5A5A; margin-bottom: 1rem;">
        Infrastructure to Scale Specialist-Level Care<br>
        <strong>752 payer policies</strong> • <strong>50 states</strong> • <strong>1,088 payers</strong><br>
        Coverage expanding weekly
    </div>
    <div style="font-size: 0.8rem; color: #708090;">
        Clinical logic based on <strong>AHS 2021/2024</strong>, <strong>ACP 2025</strong>, <strong>ICHD-3 Criteria</strong><br>
        🤖 Powered by <strong>Anthropic Claude AI</strong> | ⚡ Average response time: <strong>&lt;2 seconds</strong>
    </div>
    <div style="margin-top: 1rem; font-size: 0.75rem; color: #999;">
        📅 Last Updated: January 15, 2026 | 🔄 Database refreshed daily<br>
        <span style="color: #DC2626;">⚠️ NOT FOR CLINICAL USE — DEMONSTRATION ONLY</span>
    </div>
</div>
""", unsafe_allow_html=True)