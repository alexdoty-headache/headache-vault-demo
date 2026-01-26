import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# Try to import data_flow module, create stub if not available
try:
    from data_flow import SessionStateManager, SidebarHelper, SearchService, PAGenerator
except ImportError:
    # Stub classes for standalone testing
    class SessionStateManager:
        @staticmethod
        def initialize():
            defaults = {
                'current_page': 'Dashboard',
                'search_results': None,
                'parsed_data': None,
                'show_pa_text': False,
                'patient_age': 35,
                'headache_type': 'Chronic Migraine',
                'show_moh_check': False,
                'user_mode': 'pcp',
                'fallback_used': False,
                'fallback_message': '',
                'data_collection_state': None,
            }
            for key, value in defaults.items():
                if key not in st.session_state:
                    st.session_state[key] = value
        
        @staticmethod
        def set_from_ai_parse(data):
            if data:
                st.session_state.parsed_data = data
    class SidebarHelper:
        pass
    class SearchService:
        pass
    class PAGenerator:
        pass

# Page configuration
st.set_page_config(
    page_title="The Headache Vault - PA Automation Demo",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light theme
st.markdown("""
<script>
    window.parent.document.documentElement.setAttribute('data-theme', 'light');
</script>
""", unsafe_allow_html=True)

# Custom CSS with Headache Vault brand identity + Guided Data Collection styles
st.markdown("""
<style>
    /* Import brand fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Source+Sans+Pro:wght@400;600&display=swap');
    
    /* Force light theme and readable backgrounds */
    .stApp { background-color: #FFFFFF !important; }
    .main .block-container { background-color: #FFFFFF !important; }
    
    /* Global font override */
    html, body, [class*="css"] { font-family: 'Source Sans Pro', sans-serif; color: #262730 !important; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Inter', sans-serif; font-weight: 700; color: #262730 !important; }
    
    .main-header { font-size: 2.5rem; color: #4B0082; font-weight: 700; margin-bottom: 0.5rem; font-family: 'Inter', sans-serif; }
    .sub-header { font-size: 1.2rem; color: #5A5A5A; margin-bottom: 2rem; font-family: 'Source Sans Pro', sans-serif; }
    .step-box { background-color: #f0f2f6; padding: 1rem; border-radius: 8px; border-left: 4px solid #4B0082; margin: 1rem 0; color: #262730; }
    .warning-box { background-color: #FFF9E6; padding: 1rem; border-radius: 8px; border-left: 4px solid #FFD700; margin: 1rem 0; color: #856404; }
    .success-box { background-color: #F5F0FF; padding: 1rem; border-radius: 8px; border-left: 4px solid #FFD700; margin: 1rem 0; color: #262730; }
    .evidence-tag { display: inline-block; background-color: #E6E6FA; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem; margin: 0.25rem; color: #262730; font-weight: 600; }
    
    /* Button colors */
    .stButton > button[kind="primary"] { background-color: #4B0082 !important; color: white !important; }
    .stButton > button[kind="primary"]:hover { background-color: #6A0DAD !important; }
    .stButton > button[kind="secondary"] { background-color: #FFFFFF !important; color: #4B0082 !important; border: 2px solid #4B0082 !important; }
    .stButton > button[kind="secondary"]:hover { background-color: #F5F0FF !important; color: #4B0082 !important; }
    .stButton > button { color: #262730 !important; }
    
    /* Stat cards */
    .stat-card { background: linear-gradient(135deg, #4B0082 0%, #6A0DAD 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(75, 0, 130, 0.3); }
    .stat-number { font-size: 2.75rem; font-weight: 800; font-family: 'Inter', sans-serif; margin: 0; color: white !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }
    .stat-label { font-size: 1rem; font-weight: 600; margin-top: 0.5rem; color: white !important; text-transform: uppercase; letter-spacing: 0.5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }
    
    /* Policy cards */
    .policy-card { background: white; border: 2px solid #E6E6FA; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: all 0.3s ease; }
    .policy-card:hover { border-color: #4B0082; box-shadow: 0 4px 12px rgba(75, 0, 130, 0.15); }
    .policy-header { display: flex; align-items: center; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 2px solid #F0F0F0; }
    .policy-title { font-size: 1.3rem; font-weight: 700; color: #4B0082; margin: 0; }
    .policy-badge { display: inline-block; background: #E6E6FA; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; color: #4B0082; margin-left: 0.5rem; }
    .policy-section { margin: 1rem 0; }
    .policy-section-title { font-size: 0.9rem; font-weight: 600; color: #708090; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; }
    .step-item { display: flex; align-items: flex-start; padding: 0.75rem; background: #FAFAFA; border-radius: 8px; margin: 0.5rem 0; color: #262730; }
    .step-item strong { color: #262730; }
    .step-item small { color: #708090; }
    .step-number { background: #4B0082; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; margin-right: 0.75rem; flex-shrink: 0; }
    .gold-card-badge { background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 700; display: inline-block; margin: 0.5rem 0; }
    
    /* Copy button */
    .copy-button { background: #4B0082; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-weight: 600; display: inline-flex; align-items: center; gap: 0.5rem; transition: all 0.2s ease; }
    .copy-button:hover { background: #6A0DAD; transform: translateY(-1px); }
    
    /* Success toast */
    .success-toast { position: fixed; top: 20px; right: 20px; background: #10B981; color: white; padding: 1rem 1.5rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 9999; animation: slideIn 0.3s ease; }
    @keyframes slideIn { from { transform: translateX(400px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    
    /* Footer */
    .production-footer { margin-top: 3rem; padding: 2rem 0; border-top: 2px solid #E6E6FA; text-align: center; color: #708090; }
    .footer-badge { display: inline-block; margin: 0 0.5rem; font-size: 0.85rem; color: #4B0082; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #FAFAFA !important; }
    section[data-testid="stSidebar"] .stSelectbox > div > div { background-color: #FFFFFF !important; color: #262730 !important; }
    section[data-testid="stSidebar"] input { background-color: #FFFFFF !important; color: #262730 !important; }
    section[data-testid="stSidebar"] [data-baseweb="select"] { background-color: #FFFFFF !important; }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #262730 !important; }
    [data-baseweb="popover"] { background-color: #FFFFFF !important; }
    [role="option"] { background-color: #FFFFFF !important; color: #262730 !important; }
    [role="option"]:hover { background-color: #F0F0F0 !important; }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label { color: #262730 !important; }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div { color: #262730 !important; }
    section[data-testid="stSidebar"] input[type="number"] { background-color: #FFFFFF !important; color: #262730 !important; }
    section[data-testid="stSidebar"] label { color: #262730 !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] h2 { color: #262730 !important; }
    
    /* Metrics */
    [data-testid="stMetricValue"] { color: #262730; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #5A5A5A; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { font-family: 'Inter', sans-serif; font-weight: 600; color: #5A5A5A; background-color: transparent !important; }
    .stTabs [aria-selected="true"] { color: #262730 !important; border-bottom-color: #4B0082 !important; background-color: transparent !important; }
    
    /* Form elements */
    .stSelectbox > div > div, .stTextInput > div > div, .stTextArea > div > div { background-color: #FFFFFF !important; color: #262730 !important; }
    input, textarea, select { background-color: #FFFFFF !important; color: #262730 !important; }
    .streamlit-expanderHeader { background-color: #F8F9FA !important; color: #262730 !important; }
    .stAlert { background-color: #F8F9FA !important; }
    .stAlert [data-testid="stMarkdownContainer"] { color: #262730 !important; }
    .stAlert strong { color: #262730 !important; }
    .stCaption { color: #708090 !important; }
    
    /* Nuclear option - force text visible */
    p:not(.stButton [kind="primary"] *):not(.stat-card *):not(.stat-number):not(.stat-label), 
    span:not(.stButton [kind="primary"] *):not(.stat-card *):not(.stat-number):not(.stat-label), 
    div:not(.stButton [kind="primary"] *):not(.stat-card):not(.stat-number):not(.stat-label), 
    label, li, td, th, h1, h2, h3, h4, h5, h6 { color: #262730 !important; }
    
    .stButton > button[kind="primary"], .stButton > button[kind="primary"] *, button[kind="primary"] span, button[kind="primary"] div, button[kind="primary"] p { color: white !important; }
    .stat-card, .stat-card *, .stat-card div, .stat-card span { color: white !important; }
    .stat-number, .stat-number span { color: #FFFFFF !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.4) !important; }
    .stat-label, .stat-label span { color: #E6E6FA !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.3) !important; }
    .step-number * { color: white !important; }
    [data-baseweb="select"] span, [data-baseweb="select"] div, [role="listbox"] *, [role="option"] * { color: #262730 !important; }
    button:not([kind="primary"]) * { color: #4B0082 !important; }
    .dataframe, .dataframe *, table, table * { color: #262730 !important; background-color: #FFFFFF !important; }
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] *, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span, [data-testid="stMarkdownContainer"] div { color: #262730 !important; }
    textarea, input, select { color: #262730 !important; background-color: #FFFFFF !important; }
    code, pre, .stCode { color: #262730 !important; background-color: #F8F9FA !important; }
    
    /* Persona/mode toggle styles */
    .mode-toggle { background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%); border: 2px solid #E6E6FA; border-radius: 12px; padding: 0.75rem 1.5rem; margin: 1rem 0; display: flex; align-items: center; justify-content: center; gap: 1rem; }
    .mode-label { font-size: 0.9rem; color: #5A5A5A; font-weight: 500; }
    .learning-moment { background: linear-gradient(135deg, #FFF9E6 0%, #FFFEF5 100%); border: 1px solid #FFD700; border-left: 4px solid #FFD700; border-radius: 8px; padding: 1rem 1.25rem; margin: 1rem 0; }
    .learning-moment-title { color: #B8860B; font-weight: 700; font-size: 0.95rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
    .learning-moment-content { color: #5A5A5A; font-size: 0.9rem; line-height: 1.6; }
    .learning-moment-content ul { margin: 0.5rem 0; padding-left: 1.25rem; }
    .learning-moment-content li { margin: 0.25rem 0; color: #5A5A5A !important; }
    .pcp-guidance { background: #F0F8FF; border: 1px solid #B0D4F1; border-left: 4px solid #4A90D9; border-radius: 8px; padding: 1rem 1.25rem; margin: 0.75rem 0; }
    .pcp-guidance-title { color: #2C5282; font-weight: 600; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; }
    .pcp-guidance-content { color: #4A5568; font-size: 0.85rem; line-height: 1.6; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #B0D4F1; }
    .doc-checklist { background: #F0FFF4; border: 1px solid #9AE6B4; border-radius: 8px; padding: 1rem; margin: 0.75rem 0; }
    .doc-checklist-title { color: #276749; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.5rem; }
    .doc-checklist-item { color: #2F855A; font-size: 0.85rem; padding: 0.25rem 0; display: flex; align-items: flex-start; gap: 0.5rem; }
    .pitfall-warning { background: #FFF5F5; border: 1px solid #FEB2B2; border-left: 4px solid #E53E3E; border-radius: 8px; padding: 1rem 1.25rem; margin: 0.75rem 0; }
    .pitfall-warning-title { color: #C53030; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.5rem; }
    .pitfall-warning-content { color: #742A2A; font-size: 0.85rem; line-height: 1.5; }
    .pro-tip { background: linear-gradient(135deg, #EBF8FF 0%, #F0FFFF 100%); border: 1px solid #90CDF4; border-left: 4px solid #4299E1; border-radius: 8px; padding: 1rem 1.25rem; margin: 0.75rem 0; }
    .pro-tip-title { color: #2B6CB0; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.5rem; }
    .pro-tip-content { color: #2C5282; font-size: 0.85rem; line-height: 1.5; }
    
    /* ===== GUIDED DATA COLLECTION STYLES ===== */
    .quality-indicator { padding: 0.75rem 1rem; border-radius: 8px; margin: 1rem 0; display: flex; align-items: center; gap: 0.75rem; }
    .quality-excellent { background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; }
    .quality-good { background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; }
    .quality-fair { background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; }
    .quality-limited { background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); color: white; }
    .required-field-box { background: #FEF2F2; border: 2px solid #FECACA; border-left: 4px solid #EF4444; border-radius: 8px; padding: 1.25rem; margin: 1rem 0; }
    .improvement-suggestion-box { background: #FEF3C7; border: 2px solid #FDE68A; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
    .data-collected-box { background: #ECFDF5; border: 2px solid #A7F3D0; border-left: 4px solid #10B981; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# GUIDED DATA COLLECTION SYSTEM
# ============================================================================

class FieldPriority(Enum):
    """Priority levels for data collection fields"""
    REQUIRED = "required"      # Must have before search (state)
    IMPORTANT = "important"    # Strongly recommended (payer, drug)
    HELPFUL = "helpful"        # Nice to have (diagnosis, age, prior meds)

@dataclass
class DataCollectionState:
    """Tracks what data has been collected and what's missing"""
    state: Optional[str] = None
    payer: Optional[str] = None
    drug_class: Optional[str] = None
    diagnosis: Optional[str] = None
    age: Optional[int] = None
    prior_medications: List[str] = field(default_factory=list)
    confidence: str = "medium"
    raw_parsed_data: Dict = field(default_factory=dict)
    
    def get_collected_fields(self) -> List[str]:
        """Return list of fields that have values"""
        collected = []
        if self.state: collected.append('state')
        if self.payer: collected.append('payer')
        if self.drug_class: collected.append('drug_class')
        if self.diagnosis: collected.append('diagnosis')
        if self.age: collected.append('age')
        if self.prior_medications: collected.append('prior_medications')
        return collected
    
    def get_missing_required_fields(self) -> List[str]:
        """Return list of required fields that are missing"""
        missing = []
        if not self.state:
            missing.append('state')
        return missing
    
    def get_missing_important_fields(self) -> List[str]:
        """Return list of important fields that are missing"""
        missing = []
        if not self.payer:
            missing.append('payer')
        if not self.drug_class:
            missing.append('drug_class')
        return missing
    
    def can_proceed_to_search(self) -> Tuple[bool, str]:
        """Check if we have enough data to search"""
        missing_required = self.get_missing_required_fields()
        if missing_required:
            return False, "State is required to find applicable payer policies. PA requirements vary dramatically by state."
        return True, "Ready to search"
    
    def get_search_quality_score(self) -> Tuple[int, str]:
        """Calculate search quality score (0-100) based on collected data"""
        score = 0
        
        # State: 40 points (required)
        if self.state:
            score += 40
        
        # Payer: 30 points (important)
        if self.payer:
            score += 30
        
        # Drug class: 20 points (important)
        if self.drug_class:
            score += 20
        
        # Diagnosis: 4 points (helpful)
        if self.diagnosis:
            score += 4
        
        # Age: 3 points (helpful)
        if self.age:
            score += 3
        
        # Prior medications: 3 points (helpful)
        if self.prior_medications:
            score += 3
        
        # Generate description
        if score >= 90:
            desc = "Excellent - highly targeted results"
        elif score >= 70:
            desc = "Good - relevant policies found"
        elif score >= 50:
            desc = "Fair - may need filtering"
        elif score >= 40:
            desc = "Limited - broad results, add payer/medication to narrow"
        else:
            desc = "Insufficient - state is required"
        
        return score, desc

def analyze_parsed_data(parsed_data: Dict) -> DataCollectionState:
    """Convert AI-parsed data into a DataCollectionState"""
    if not parsed_data:
        return DataCollectionState()
    
    return DataCollectionState(
        state=parsed_data.get('state'),
        payer=parsed_data.get('payer'),
        drug_class=parsed_data.get('drug_class'),
        diagnosis=parsed_data.get('diagnosis'),
        age=parsed_data.get('age'),
        prior_medications=parsed_data.get('prior_medications', []),
        confidence=parsed_data.get('confidence', 'medium'),
        raw_parsed_data=parsed_data
    )

def get_quality_indicator_html(score: int, description: str) -> str:
    """Generate HTML for quality indicator"""
    if score >= 90:
        css_class = "quality-excellent"
        emoji = "🎯"
    elif score >= 70:
        css_class = "quality-good"
        emoji = "✅"
    elif score >= 50:
        css_class = "quality-fair"
        emoji = "⚠️"
    else:
        css_class = "quality-limited"
        emoji = "📊"
    
    return f'''
    <div class="quality-indicator {css_class}">
        <span style="font-size: 1.5rem;">{emoji}</span>
        <div>
            <div style="font-weight: 700; font-size: 1.1rem;">Search Quality: {score}%</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">{description}</div>
        </div>
    </div>
    '''

def expand_payer_keywords(payer_input: str) -> List[str]:
    """Expand payer abbreviations and common names to search keywords"""
    if not payer_input:
        return []
    payer_lower = payer_input.lower().strip()
    
    # Abbreviation mappings
    expansions = {
        'ibx': ['independence', 'blue cross'],
        'bcbs': ['blue cross', 'blue shield', 'bcbs'],
        'uhc': ['united', 'unitedhealthcare', 'uhc'],
        'anthem': ['anthem', 'elevance'],
        'horizon': ['horizon'],
        'aetna': ['aetna'],
        'cigna': ['cigna'],
        'humana': ['humana'],
        'kaiser': ['kaiser'],
        'highmark': ['highmark'],
        'upmc': ['upmc'],
        'geisinger': ['geisinger'],
        'independence': ['independence'],
        'emblem': ['emblem'],
        'oscar': ['oscar'],
        'molina': ['molina'],
        'centene': ['centene'],
        'wellcare': ['wellcare'],
        'caresource': ['caresource'],
    }
    
    # Check for known abbreviations first
    for abbrev, keywords in expansions.items():
        if abbrev in payer_lower:
            return keywords
    
    # Default: use first word and full input
    words = payer_input.split()
    if words:
        return [words[0].lower(), payer_lower]
    return [payer_lower]

def render_required_field_prompt(collection_state: DataCollectionState, db_b) -> Optional[str]:
    """
    Render UI for collecting required missing fields (state).
    Returns selected state if user provides it, None otherwise.
    """
    missing = collection_state.get_missing_required_fields()
    
    if 'state' in missing:
        st.markdown("""
        <div class="required-field-box">
            <div style="font-weight: 700; color: #DC2626; margin-bottom: 0.5rem; font-size: 1.1rem;">
                🔴 State Required
            </div>
            <div style="color: #7F1D1D; margin-bottom: 1rem;">
                Prior authorization requirements vary dramatically by state. We need to know where the patient's insurance is based to show accurate policy information.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Get available states from database
        available_states = sorted([s for s in db_b['State'].unique() if s != 'ALL'])
        
        selected_state = st.selectbox(
            "Patient's Insurance State",
            options=['-- Select State --'] + available_states,
            key="required_state_selector",
            help="Select the state where the patient's insurance is based"
        )
        
        if selected_state and selected_state != '-- Select State --':
            return selected_state
    
    return None

def render_improvement_suggestions(collection_state: DataCollectionState, db_b) -> Dict:
    """
    Render UI for optional improvement suggestions.
    Returns dict of any additional data provided.
    """
    score, desc = collection_state.get_search_quality_score()
    missing_important = collection_state.get_missing_important_fields()
    
    if score >= 90 or not missing_important:
        return {}
    
    # Show quality indicator
    st.markdown(get_quality_indicator_html(score, desc), unsafe_allow_html=True)
    
    improvements = {}
    
    with st.expander("💡 Improve Search Results (Optional)", expanded=score < 70):
        if 'payer' in missing_important:
            st.markdown("**Insurance Carrier** - Narrow results to specific payer")
            
            # Get payers for the selected state
            state_payers = sorted(db_b[db_b['State'] == collection_state.state]['Payer_Name'].unique().tolist())
            
            # Add common payer suggestions
            common_payers = ['Aetna', 'Anthem', 'Blue Cross Blue Shield', 'Cigna', 'Humana', 'UnitedHealthcare']
            st.caption(f"Common in {collection_state.state}: " + ", ".join([p for p in common_payers if any(p.lower() in sp.lower() for sp in state_payers)][:4]))
            
            selected_payer = st.selectbox(
                "Select Payer",
                options=['-- Show All Payers --'] + state_payers,
                key="improvement_payer_selector"
            )
            
            if selected_payer and selected_payer != '-- Show All Payers --':
                improvements['payer'] = selected_payer
        
        if 'drug_class' in missing_important:
            st.markdown("**Medication Class** - Show requirements for specific drug")
            
            # Get drug classes for the selected state
            state_drugs = sorted(db_b[db_b['State'] == collection_state.state]['Drug_Class'].unique().tolist())
            
            selected_drug = st.selectbox(
                "Select Medication",
                options=['-- Show All Medications --'] + state_drugs,
                key="improvement_drug_selector"
            )
            
            if selected_drug and selected_drug != '-- Show All Medications --':
                improvements['drug_class'] = selected_drug
    
    return improvements

def render_search_quality_context(collection_state: DataCollectionState, result_count: int):
    """Render context about search quality and what to expect"""
    score, desc = collection_state.get_search_quality_score()
    
    # Show quality indicator
    st.markdown(get_quality_indicator_html(score, desc), unsafe_allow_html=True)
    
    # Add context based on quality
    if score < 70:
        missing = []
        if not collection_state.payer:
            missing.append("insurance carrier")
        if not collection_state.drug_class:
            missing.append("medication")
        
        if missing:
            st.info(f"💡 **Tip:** Adding {' and '.join(missing)} will narrow these {result_count} results to the most relevant policy.")

# ============================================================================
# DATABASE LOADING
# ============================================================================

@st.cache_data
def load_databases():
    """
    Load all Headache Vault databases from CSV files.
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
# HELPER FUNCTIONS
# ============================================================================

def get_step_therapy_details(row):
    """Get step therapy details with column name fallback for DB compatibility."""
    requirement = row.get('Step_1_Requirement') or row.get('Step_Therapy_Requirements') or 'Not specified'
    duration = row.get('Step_1_Duration') or row.get('Step_Therapy_Duration') or 'Trial duration not specified'
    return str(requirement), str(duration)

def search_policies_with_fallback(db_b, state, payer=None, drug_class=None):
    """
    Search for policies with automatic fallback to national (ALL) entries
    and drug class cascading for preventive gepants.
    
    Returns: (results_df, fallback_used: bool, fallback_message: str)
    """
    fallback_used = False
    fallback_message = ""
    
    # Step 1: Try state-specific search
    query = db_b[db_b['State'] == state].copy()
    query = query.reset_index(drop=True)
    
    # Apply payer filter with flexible matching
    if payer:
        payer_keywords = expand_payer_keywords(payer)
        
        # Build flexible payer match
        payer_mask = pd.Series([False] * len(query))
        for kw in payer_keywords:
            payer_mask = payer_mask | query['Payer_Name'].str.contains(kw, case=False, na=False)
        
        payer_query = query[payer_mask]
        
        # If no state match, try national fallback
        if len(payer_query) == 0:
            national_query = db_b[db_b['State'] == 'ALL'].copy()
            national_query = national_query.reset_index(drop=True)
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
            
            # Define cascade order for preventive gepants
            if drug_class == 'Gepants (Preventive)':
                cascade_classes = ['Qulipta', 'CGRP mAbs']
            elif drug_class == 'Qulipta':
                cascade_classes = ['Gepants (Preventive)', 'CGRP mAbs']
            elif drug_class in ['CGRP mAb (Cluster)', 'Emgality (Cluster)', 'Cluster CGRP']:
                cascade_classes = ['CGRP mAbs']
            
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
                national_query = national_query.reset_index(drop=True)
                if payer:
                    payer_keywords = expand_payer_keywords(payer)
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

def search_policies_guided(db_b, collection_state: DataCollectionState):
    """
    Search policies using the guided data collection state.
    Only searches if required fields are present.
    
    Returns: (results_df, success: bool, message: str, metadata: dict)
    """
    can_proceed, reason = collection_state.can_proceed_to_search()
    
    if not can_proceed:
        return pd.DataFrame(), False, reason, {}
    
    # Perform search
    results, fallback_used, fallback_message = search_policies_with_fallback(
        db_b,
        state=collection_state.state,
        payer=collection_state.payer,
        drug_class=collection_state.drug_class
    )
    
    # Apply diagnosis filter if applicable
    if collection_state.diagnosis and not results.empty:
        if collection_state.diagnosis == "Cluster Headache":
            cluster_filtered = results[results['Drug_Class'].str.contains('Cluster', case=False, na=False)]
            if not cluster_filtered.empty:
                results = cluster_filtered
        elif collection_state.diagnosis == "Chronic Migraine":
            if 'Medication_Category' in results.columns:
                chronic_filtered = results[results['Medication_Category'].str.contains('Chronic|Preventive', case=False, na=False)]
                if not chronic_filtered.empty:
                    results = chronic_filtered
    
    score, desc = collection_state.get_search_quality_score()
    
    metadata = {
        'fallback_used': fallback_used,
        'fallback_message': fallback_message,
        'quality_score': score,
        'quality_description': desc,
        'filters_applied': {
            'state': collection_state.state,
            'payer': collection_state.payer,
            'drug_class': collection_state.drug_class,
            'diagnosis': collection_state.diagnosis
        }
    }
    
    return results, True, f"Found {len(results)} matching policies", metadata

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
        
        if ' or ' in step_req_lower:
            if verapamil_tried or lithium_tried:
                med_name = 'Verapamil' if verapamil_tried else 'Lithium'
                criteria_status.append(("Verapamil OR lithium failure", True, f"{med_name} trial documented"))
            else:
                criteria_status.append(("Verapamil OR lithium failure", False, "Neither documented"))
        elif ' and ' in step_req_lower:
            if verapamil_tried and lithium_tried:
                criteria_status.append(("Verapamil AND lithium failure", True, "Both documented"))
            else:
                missing = []
                if not verapamil_tried: missing.append("verapamil")
                if not lithium_tried: missing.append("lithium")
                criteria_status.append(("Verapamil AND lithium failure", False, f"Missing: {', '.join(missing)}"))
    
    return criteria_status

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

# ============================================================================
# CLINICAL NOTE PARSER
# ============================================================================

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
    payers = sorted(db_a['Payer_Name'].unique().tolist())[:50]
    drug_classes = sorted(db_b['Drug_Class'].unique().tolist())
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""Extract patient information from this clinical note. Return ONLY a JSON object.

CRITICAL: Look for insurance/payer information carefully. Examples:
- "Has Independence Blue Cross" → payer: "Independence Blue Cross"
- "Has Highmark insurance" → payer: "Highmark Blue Cross Blue Shield"
- "Aetna commercial plan" → payer: "Aetna"
- "UnitedHealthcare" → payer: "UnitedHealthcare"

JSON format:
{{
  "state": "two-letter state code (PA, NY, CA, etc) or null",
  "payer": "EXACT insurance company name or null - LOOK FOR THIS CAREFULLY", 
  "drug_class": "medication class from drug list or null",
  "diagnosis": "Chronic Migraine, Episodic Migraine, or Cluster Headache",
  "age": integer age or null,
  "prior_medications": ["medications that failed"],
  "confidence": "high/medium/low"
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

Return ONLY the JSON object with all fields filled in. If you see ANY mention of insurance or payer, include it in the "payer" field."""
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
                        if payer_input in p.lower() or p.lower() in payer_input:
                            exact_match = p
                            break
                
                # Update with matched name
                if exact_match:
                    parsed['payer'] = exact_match
            
            return parsed
        except:
            # If not valid JSON, try to extract it
            import re
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            st.error("Failed to parse AI response. Please try again.")
            return None
            
    except Exception as e:
        st.error(f"Error calling Claude API: {str(e)}")
        return None

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

SessionStateManager.initialize()

# Additional session state for guided data collection
if 'data_collection_state' not in st.session_state:
    st.session_state.data_collection_state = None
if 'pending_state_selection' not in st.session_state:
    st.session_state.pending_state_selection = None

# Load data
payer_registry, payer_policies, denial_codes, pediatric_overrides, state_regulations, icd10_codes, therapeutic_doses, otc_medications = load_databases()

# Create aliases for backward compatibility
db_a = payer_registry
db_b = payer_policies
db_c = denial_codes
db_e = pediatric_overrides
db_f = state_regulations
icd10 = icd10_codes
therapeutic = therapeutic_doses
otc = otc_medications

# ============================================================================
# HEADER
# ============================================================================

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
        st.session_state.data_collection_state = None
        st.rerun()

# ============================================================================
# PERSONA TOGGLE
# ============================================================================

toggle_col1, toggle_col2, toggle_col3 = st.columns([3, 6, 3])
with toggle_col2:
    mode_options = {
        'pcp': '👨‍⚕️ PCP / New to CGRPs (Show Guidance)',
        'specialist': '⚡ Specialist (Fast Mode)'
    }
    
    selected_mode = st.radio(
        "Experience Level",
        options=['pcp', 'specialist'],
        format_func=lambda x: mode_options[x],
        horizontal=True,
        label_visibility="collapsed",
        key="mode_selector"
    )
    
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

# ============================================================================
# PAGE NAVIGATION
# ============================================================================

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
    if st.button("🤖 AI Parser", use_container_width=True, type="primary" if st.session_state.current_page == 'AI Parser' else "secondary"):
        st.session_state.current_page = 'AI Parser'
        st.rerun()
with col4:
    if st.button("📋 ICD-10", use_container_width=True, type="primary" if st.session_state.current_page == 'ICD-10' else "secondary"):
        st.session_state.current_page = 'ICD-10'
        st.rerun()

st.markdown("---")

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

if st.session_state.current_page == 'Dashboard':
    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(db_a):,}</div>
            <div class="stat-label">Payers</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(db_b):,}</div>
            <div class="stat-label">Policies</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(db_f):,}</div>
            <div class="stat-label">States</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(db_b['Drug_Class'].unique())}</div>
            <div class="stat-label">Drug Classes</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick actions
    st.subheader("Quick Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        st.markdown("""
        <div class="step-box">
            <h4>🔍 Search Policies</h4>
            <p>Look up PA requirements by state, payer, and medication class.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Search →", key="dash_search"):
            st.session_state.current_page = 'Search'
            st.rerun()
    
    with action_col2:
        st.markdown("""
        <div class="step-box">
            <h4>🤖 AI Clinical Note Parser</h4>
            <p>Paste a clinical note and let AI extract the key information.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Parse Note →", key="dash_parse"):
            st.session_state.current_page = 'AI Parser'
            st.rerun()
    
    with action_col3:
        st.markdown("""
        <div class="step-box">
            <h4>📋 ICD-10 Lookup</h4>
            <p>Find diagnosis codes for headache disorders.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Look Up Codes →", key="dash_icd"):
            st.session_state.current_page = 'ICD-10'
            st.rerun()
    
    # Educational content for PCP mode
    if st.session_state.user_mode == 'pcp':
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="learning-moment">
            <div class="learning-moment-title">💡 Why Prior Authorization Matters</div>
            <div class="learning-moment-content">
                CGRP medications (Aimovig, Ajovy, Emgality, Nurtec, Qulipta) offer transformative relief for migraine patients,
                but insurance often requires prior authorization showing:
                <ul>
                    <li><strong>Step therapy:</strong> Trial of 2+ oral preventives (topiramate, propranolol, etc.)</li>
                    <li><strong>Frequency documentation:</strong> ≥4 migraine days/month for CGRP mAbs</li>
                    <li><strong>Diagnosis codes:</strong> Appropriate ICD-10 code (e.g., G43.709 for chronic migraine)</li>
                </ul>
                This platform helps you navigate these requirements efficiently.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# PAGE: SEARCH
# ============================================================================

elif st.session_state.current_page == 'Search':
    st.subheader("🔍 Policy Search")
    
    # Check if we have data from AI Parser
    parsed_data = st.session_state.get('parsed_data', {})
    collection_state = st.session_state.get('data_collection_state')
    
    # Initialize collection state from parsed data if available
    if parsed_data and not collection_state:
        collection_state = analyze_parsed_data(parsed_data)
        st.session_state.data_collection_state = collection_state
    
    # Manual search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        # Get default values from collection state or parsed data
        default_state = None
        default_payer = None
        default_drug = None
        
        if collection_state:
            default_state = collection_state.state
            default_payer = collection_state.payer
            default_drug = collection_state.drug_class
        elif parsed_data:
            default_state = parsed_data.get('state')
            default_payer = parsed_data.get('payer')
            default_drug = parsed_data.get('drug_class')
        
        with col1:
            states = sorted([s for s in db_b['State'].unique() if s != 'ALL'])
            state_options = ['-- Select State (Required) --'] + states
            
            # Find default index
            state_idx = 0
            if default_state and default_state in states:
                state_idx = states.index(default_state) + 1
            
            selected_state = st.selectbox(
                "State *",
                options=state_options,
                index=state_idx,
                help="⚠️ Required - PA requirements vary by state"
            )
            
            # Payer selection
            if selected_state and selected_state != '-- Select State (Required) --':
                state_payers = sorted(db_b[db_b['State'] == selected_state]['Payer_Name'].unique().tolist())
                payer_options = ['-- All Payers --'] + state_payers
                
                payer_idx = 0
                if default_payer:
                    for i, p in enumerate(state_payers):
                        if default_payer.lower() in p.lower() or p.lower() in default_payer.lower():
                            payer_idx = i + 1
                            break
                
                selected_payer = st.selectbox(
                    "Insurance Payer",
                    options=payer_options,
                    index=payer_idx,
                    help="Optional - Narrow results to specific payer"
                )
            else:
                selected_payer = st.selectbox("Insurance Payer", options=['-- Select State First --'], disabled=True)
        
        with col2:
            drug_classes = sorted(db_b['Drug_Class'].unique().tolist())
            drug_options = ['-- All Drug Classes --'] + drug_classes
            
            drug_idx = 0
            if default_drug and default_drug in drug_classes:
                drug_idx = drug_classes.index(default_drug) + 1
            
            selected_drug = st.selectbox(
                "Drug Class",
                options=drug_options,
                index=drug_idx,
                help="Optional - Filter by medication class"
            )
        
        submitted = st.form_submit_button("🔍 Search Policies", type="primary", use_container_width=True)
    
    # Handle search
    if submitted:
        if selected_state == '-- Select State (Required) --':
            st.markdown("""
            <div class="required-field-box">
                <div style="font-weight: 700; color: #DC2626; margin-bottom: 0.5rem; font-size: 1.1rem;">
                    🔴 State is Required
                </div>
                <div style="color: #7F1D1D;">
                    Prior authorization requirements vary dramatically by state. Please select a state to see applicable policies.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Perform search
            search_state = selected_state
            search_payer = selected_payer if selected_payer != '-- All Payers --' else None
            search_drug = selected_drug if selected_drug != '-- All Drug Classes --' else None
            
            results, fallback_used, fallback_msg = search_policies_with_fallback(
                db_b, search_state, search_payer, search_drug
            )
            
            st.session_state.search_results = results
            st.session_state.fallback_used = fallback_used
            st.session_state.fallback_message = fallback_msg
            
            # Calculate and show quality score
            temp_state = DataCollectionState(
                state=search_state,
                payer=search_payer,
                drug_class=search_drug
            )
            score, desc = temp_state.get_search_quality_score()
            
            st.markdown(get_quality_indicator_html(score, desc), unsafe_allow_html=True)
            
            if fallback_used and fallback_msg:
                st.info(fallback_msg)
    
    # Display results
    if st.session_state.search_results is not None:
        results = st.session_state.search_results
        
        if len(results) == 0:
            st.warning("No policies found matching your criteria. Try broadening your search.")
        else:
            st.success(f"Found {len(results)} matching policies")
            
            # Display each result as a card
            for idx, row in results.iterrows():
                payer_name = row.get('Payer_Name', 'Unknown Payer')
                drug_class = row.get('Drug_Class', 'Unknown')
                state = row.get('State', 'Unknown')
                step_required = row.get('Step_Therapy_Required', 'Unknown')
                step_req, step_dur = get_step_therapy_details(row)
                gold_card = row.get('Gold_Card_Available', 'N/A')
                
                st.markdown(f"""
                <div class="policy-card">
                    <div class="policy-header">
                        <span class="policy-title">{payer_name}</span>
                        <span class="policy-badge">{drug_class}</span>
                        <span class="policy-badge">{state}</span>
                    </div>
                    <div class="policy-section">
                        <div class="policy-section-title">Step Therapy</div>
                        <div class="step-item">
                            <span class="step-number">1</span>
                            <div>
                                <strong>Required:</strong> {step_required}<br>
                                <strong>Requirement:</strong> {step_req}<br>
                                <small>Duration: {step_dur}</small>
                            </div>
                        </div>
                    </div>
                    {"<div class='gold-card-badge'>🏆 Gold Card Available</div>" if gold_card == 'Yes' else ""}
                </div>
                """, unsafe_allow_html=True)
                
                # Show action buttons
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    if st.button(f"📋 Generate PA", key=f"gen_pa_{idx}"):
                        st.session_state.selected_policy = row.to_dict()
                        st.session_state.show_pa_text = True
                
                # Show PA text if requested
                if st.session_state.get('show_pa_text') and st.session_state.get('selected_policy') == row.to_dict():
                    pa_text = f"""PRIOR AUTHORIZATION REQUEST

Patient Information:
- Diagnosis: {parsed_data.get('diagnosis', '[Complete from chart]')}
- Age: {parsed_data.get('age', '[Complete from chart]')}

Medication Requested: {drug_class}

Clinical Justification:
Patient has {parsed_data.get('diagnosis', 'chronic migraine')} with documented failure of the following medications:
{chr(10).join(['- ' + m for m in parsed_data.get('prior_medications', ['[List prior medications]'])])}

Step therapy requirements have been met per {payer_name} policy.

Prescriber Attestation:
I attest that the above information is accurate and that this medication is medically necessary for this patient.
"""
                    st.text_area("Generated PA Text", pa_text, height=300, key=f"pa_text_{idx}")
                    st.markdown(create_copy_button(pa_text, f"copy_pa_{idx}"), unsafe_allow_html=True)

# ============================================================================
# PAGE: AI PARSER
# ============================================================================

elif st.session_state.current_page == 'AI Parser':
    st.subheader("🤖 AI Clinical Note Parser")
    
    if st.session_state.user_mode == 'pcp':
        st.markdown("""
        <div class="learning-moment">
            <div class="learning-moment-title">💡 How the AI Parser Helps</div>
            <div class="learning-moment-content">
                Paste your clinical note below and our AI will extract:
                <ul>
                    <li>Patient's insurance and state</li>
                    <li>Diagnosis (chronic vs episodic migraine, cluster headache)</li>
                    <li>Prior medications tried (for step therapy documentation)</li>
                    <li>Requested medication class</li>
                </ul>
                This saves time and ensures nothing is missed for the PA.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Sample note
    sample_note = """45 yo female with chronic migraine, 15 headache days/month.
Has Independence Blue Cross (PA).
Failed topiramate (cognitive side effects) and propranolol (fatigue).
Currently using sumatriptan PRN with 8+ doses/month.
Requesting Aimovig for migraine prevention.
MIDAS score 48 (severe disability)."""
    
    with st.expander("📝 Sample Clinical Note (Click to expand)"):
        st.code(sample_note)
        if st.button("Use Sample Note"):
            st.session_state.sample_note = sample_note
            st.rerun()
    
    # Note input
    default_note = st.session_state.get('sample_note', '')
    clinical_note = st.text_area(
        "Paste Clinical Note",
        value=default_note,
        height=200,
        placeholder="Paste clinical documentation here..."
    )
    
    if st.button("🔍 Parse Note", type="primary", use_container_width=True):
        if not clinical_note.strip():
            st.warning("Please enter a clinical note to parse.")
        else:
            with st.spinner("Analyzing clinical note..."):
                parsed = parse_clinical_note(clinical_note, db_a, db_b)
                
                if parsed:
                    st.session_state.parsed_data = parsed
                    
                    # Create collection state from parsed data
                    collection_state = analyze_parsed_data(parsed)
                    st.session_state.data_collection_state = collection_state
                    
                    st.success("✅ Note parsed successfully!")
                    
                    # Show quality indicator
                    score, desc = collection_state.get_search_quality_score()
                    st.markdown(get_quality_indicator_html(score, desc), unsafe_allow_html=True)
                    
                    # Display parsed data
                    st.markdown("""
                    <div class="data-collected-box">
                        <div style="font-weight: 700; color: #059669; margin-bottom: 0.75rem; font-size: 1.1rem;">
                            ✅ Data Extracted from Note
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Patient Information:**")
                        st.write(f"- **State:** {parsed.get('state', 'Not found')}")
                        st.write(f"- **Payer:** {parsed.get('payer', 'Not found')}")
                        st.write(f"- **Age:** {parsed.get('age', 'Not found')}")
                        st.write(f"- **Diagnosis:** {parsed.get('diagnosis', 'Not found')}")
                    
                    with col2:
                        st.markdown("**Treatment Information:**")
                        st.write(f"- **Drug Class:** {parsed.get('drug_class', 'Not found')}")
                        st.write(f"- **Confidence:** {parsed.get('confidence', 'medium')}")
                        
                        prior_meds = parsed.get('prior_medications', [])
                        if prior_meds:
                            st.write(f"- **Prior Medications:** {', '.join(prior_meds)}")
                        else:
                            st.write("- **Prior Medications:** None documented")
                    
                    # Show what's missing and suggestions
                    missing_required = collection_state.get_missing_required_fields()
                    missing_important = collection_state.get_missing_important_fields()
                    
                    if missing_required:
                        st.markdown("""
                        <div class="required-field-box">
                            <div style="font-weight: 700; color: #DC2626; margin-bottom: 0.5rem;">
                                🔴 Required Information Missing
                            </div>
                            <div style="color: #7F1D1D;">
                                State was not found in the clinical note. Please select the patient's state before searching.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show state selector
                        states = sorted([s for s in db_b['State'].unique() if s != 'ALL'])
                        selected_state = st.selectbox(
                            "Select Patient's State",
                            options=['-- Select State --'] + states,
                            key="ai_parser_state_fix"
                        )
                        
                        if selected_state and selected_state != '-- Select State --':
                            # Update parsed data and collection state
                            parsed['state'] = selected_state
                            st.session_state.parsed_data = parsed
                            collection_state.state = selected_state
                            st.session_state.data_collection_state = collection_state
                            st.rerun()
                    
                    elif missing_important:
                        st.markdown("""
                        <div class="improvement-suggestion-box">
                            <div style="font-weight: 700; color: #D97706; margin-bottom: 0.5rem;">
                                💡 Optional: Add More Details
                            </div>
                            <div style="color: #92400E;">
                                Adding payer or medication info will improve search accuracy.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Search button
                    if not missing_required:
                        st.markdown("---")
                        if st.button("🔍 Search Policies with Parsed Data", type="primary", use_container_width=True):
                            st.session_state.current_page = 'Search'
                            st.rerun()

# ============================================================================
# PAGE: ICD-10 LOOKUP
# ============================================================================

elif st.session_state.current_page == 'ICD-10':
    st.subheader("📋 ICD-10 Code Lookup")
    
    if st.session_state.user_mode == 'pcp':
        st.markdown("""
        <div class="learning-moment">
            <div class="learning-moment-title">💡 Why ICD-10 Codes Matter for PAs</div>
            <div class="learning-moment-content">
                The right diagnosis code is critical for PA approval:
                <ul>
                    <li><strong>G43.709</strong> (Chronic migraine) - Required for Botox, preferred for CGRP mAbs</li>
                    <li><strong>G43.909</strong> (Migraine, unspecified) - May be rejected for some medications</li>
                    <li><strong>G44.009</strong> (Cluster headache) - Required for Emgality 300mg cluster indication</li>
                </ul>
                Use the most specific code that applies to your patient.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Search box
    search_term = st.text_input("Search ICD-10 codes", placeholder="Enter code or description...")
    
    if search_term:
        # Filter ICD-10 codes
        mask = (
            icd10['ICD10_Code'].str.contains(search_term, case=False, na=False) |
            icd10['ICD10_Description'].str.contains(search_term, case=False, na=False)
        )
        filtered = icd10[mask]
        
        if len(filtered) == 0:
            st.warning("No matching codes found.")
        else:
            st.success(f"Found {len(filtered)} matching codes")
            
            for _, row in filtered.iterrows():
                code = row['ICD10_Code']
                desc = row['ICD10_Description']
                billable = row.get('Billable', 'Unknown')
                
                st.markdown(f"""
                <div class="policy-card">
                    <div class="policy-header">
                        <span class="policy-title">{code}</span>
                        <span class="policy-badge">{'✓ Billable' if billable == 'Yes' else '⚠️ Not Billable'}</span>
                    </div>
                    <div style="padding: 0.5rem 0;">
                        <strong>{desc}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Show common codes
        st.markdown("### Common Headache Codes")
        
        common_codes = [
            ("G43.709", "Chronic migraine without aura, not intractable", "Required for Botox"),
            ("G43.719", "Chronic migraine with aura, not intractable", "Required for Botox"),
            ("G43.909", "Migraine, unspecified, not intractable", "General migraine code"),
            ("G44.009", "Cluster headache syndrome, unspecified", "For cluster headache"),
            ("G44.221", "Chronic tension-type headache, intractable", "Tension-type"),
        ]
        
        for code, desc, note in common_codes:
            st.markdown(f"""
            <div class="step-item">
                <span class="step-number" style="width: 80px; border-radius: 4px;">{code}</span>
                <div>
                    <strong>{desc}</strong><br>
                    <small style="color: #4B0082;">{note}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div class="production-footer">
    <div style="font-weight: 600; margin-bottom: 0.5rem;">The Headache Vault</div>
    <div style="font-size: 0.85rem;">
        <span class="footer-badge">📊 Demo Version</span>
        <span class="footer-badge">🔒 HIPAA-Ready Architecture</span>
        <span class="footer-badge">🧠 Built for Headache Medicine</span>
    </div>
    <div style="margin-top: 1rem; font-size: 0.8rem; color: #708090;">
        © 2026 The Headache Vault. Prior authorization automation for headache medicine.
    </div>
</div>
""", unsafe_allow_html=True)
