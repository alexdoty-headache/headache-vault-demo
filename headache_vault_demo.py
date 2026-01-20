import streamlit as st
import pandas as pd
from datetime import datetime

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

</style>
""", unsafe_allow_html=True)

# Load databases
@st.cache_data
def load_databases():
    """Load all databases from CSV files"""
    db_a = pd.read_csv('Database_A_FINAL_WITH_LOB_CODE.csv')
    db_b = pd.read_csv('Database_B_CLUSTER_UPDATED.csv')
    db_c = pd.read_csv('Database_C_CLUSTER_UPDATED.csv')
    db_e = pd.read_csv('Database_E_Pediatric_Overrides.csv')
    db_f = pd.read_csv('Database_F_State_Regulatory_Framework.csv')
    icd10 = pd.read_csv('Master_ICD10_CLUSTER_UPDATED.csv')
    therapeutic = pd.read_csv('Master_Therapeutic_Doses_CLUSTER_UPDATED.csv')
    otc = pd.read_csv('Master_OTC_Medications.csv')
    
    return db_a, db_b, db_c, db_e, db_f, icd10, therapeutic, otc

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'show_pa_text' not in st.session_state:
    st.session_state.show_pa_text = False
if 'show_moh_check' not in st.session_state:
    st.session_state.show_moh_check = False

# Load data
db_a, db_b, db_c, db_e, db_f, icd10, therapeutic, otc = load_databases()

# Clinical note parser
def parse_clinical_note(note_text, db_a, db_b):
    """Parse clinical note using Claude API to extract structured data"""
    import anthropic
    import json
    
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
    payers = sorted(db_a['Payer Name'].unique().tolist())[:50]  # Top 50 for context
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
- Aimovig, Ajovy, Emgality, erenumab → "CGRP mAbs"
- Ubrelvy, Nurtec ODT, ubrogepant, rimegepant → "Gepants"
- Qulipta, atogepant → "Qulipta"
- Botox, onabotulinumtoxinA → "Botox"
- Vyepti, eptinezumab → "Vyepti"

Clinical note:
{note_text}

Return ONLY the JSON object with all fields filled in. If you see ANY mention of insurance or payer, include it in the "payer" field."""
            }]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text
        
        # Debug: Show raw response
        st.write("🔍 DEBUG - Raw AI Response:")
        st.code(response_text, language="json")
        
        # Try to parse JSON
        try:
            parsed = json.loads(response_text)
            
            # Validate and fuzzy-match payer name
            if parsed.get('payer'):
                payer_input = parsed['payer'].lower().strip()
                all_payers = db_a['Payer Name'].unique()
                
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
                    st.write(f"✅ DEBUG - Payer matched: '{payer_input}' → '{exact_match}'")
                else:
                    st.write(f"❌ DEBUG - No payer match found for: '{payer_input}'")
            else:
                st.write("⚠️ DEBUG - No payer in AI response")
            
            return parsed
        except:
            # If not valid JSON, try to extract it
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
            else:
                st.error("Failed to parse API response")
                return None
                
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Header
st.markdown("""
<div style="text-align: left; margin-bottom: 2rem;">
    <div class="main-header">The Headache Vault</div>
    <div class="sub-header">Prior Authorization Automation for Headache Medicine</div>
    <div style="color: #262730; font-size: 0.95rem; font-weight: 400; font-family: 'Source Sans Pro', sans-serif;">
        Infrastructure to Scale Specialist-Level Care
    </div>
</div>
""", unsafe_allow_html=True)

# Tab interface
tab1, tab2 = st.tabs(["🔍 Quick Search", "📝 Clinical Note Input"])

with tab1:
    st.markdown("### Search by filters")
    quick_search_mode = True
    
with tab2:
    st.markdown("### Parse clinical notes with AI")
    
    st.info("💡 Paste clinic notes or describe the patient. AI will extract structured data for you.")
    
    # Example button
    if st.button("📋 Load Example Note"):
        example_note = """45-year-old female with chronic migraine, approximately 20 headache days per month. 
Lives in Philadelphia, Pennsylvania. Has Independence Blue Cross commercial insurance. 
Previously tried topiramate 100mg daily for 12 weeks - discontinued due to cognitive side effects. 
Also failed propranolol 80mg BID for 8 weeks - inadequate response with less than 30% reduction in headache frequency.
Patient is interested in trying Aimovig (erenumab) for migraine prevention."""
        st.session_state.clinical_note = example_note
    
    # Text area for clinical note
    clinical_note = st.text_area(
        "Clinical Note",
        value=st.session_state.get('clinical_note', ''),
        height=200,
        placeholder="Paste patient information here...\n\nExample:\n45yo F with chronic migraine, 20+ days/month. Lives in PA, has Highmark BCBS. Failed topiramate and propranolol. Considering Aimovig.",
        help="Include: location, insurance, diagnosis, medications tried, medication considering"
    )
    
    # Parse button
    if st.button("🤖 Parse Note with AI", type="primary", use_container_width=True):
        if not clinical_note.strip():
            st.warning("Please enter a clinical note to parse.")
        else:
            with st.spinner("🧠 Analyzing note..."):
                parsed_data = parse_clinical_note(clinical_note, db_a, db_b)
                
                if parsed_data:
                    st.session_state.parsed_data = parsed_data
                    st.success("✅ Note parsed successfully!")
    
    # Display parsed data if available
    if 'parsed_data' in st.session_state:
        parsed = st.session_state.parsed_data
        
        st.markdown("---")
        st.markdown("### 📊 Extracted Information")
        
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
        
        # Payer info
        if parsed.get('payer'):
            st.info(f"**Insurance:** {parsed['payer']}")
        
        # Prior medications
        if parsed.get('prior_medications') and len(parsed['prior_medications']) > 0:
            st.markdown("**Prior Medications:**")
            for med in parsed['prior_medications']:
                st.markdown(f"- {med}")
        
        # Edit mode
        with st.expander("✏️ Edit Extracted Data", expanded=False):
            st.markdown("Review and modify the extracted information before searching:")
            
            edited_state = st.selectbox("State", options=sorted(db_b['State'].unique().tolist()), 
                                       index=sorted(db_b['State'].unique().tolist()).index(parsed.get('state', 'PA')) if parsed.get('state') in db_b['State'].unique() else 0)
            
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
            if parsed.get('drug_class') and parsed['drug_class'] in state_drugs:
                drug_index = state_drugs.index(parsed['drug_class'])
            
            edited_drug = st.selectbox("Drug Class", options=state_drugs, index=drug_index)
            
            diagnosis_options = ["Chronic Migraine", "Episodic Migraine", "Cluster Headache"]
            diag_index = 0
            if parsed.get('diagnosis') and parsed['diagnosis'] in diagnosis_options:
                diag_index = diagnosis_options.index(parsed['diagnosis'])
            
            edited_diagnosis = st.selectbox("Diagnosis", options=diagnosis_options, index=diag_index)
            
            edited_age = st.number_input("Age", min_value=1, max_value=120, value=parsed.get('age', 35))
            
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
        
        # Search button
        if st.button("🔎 Search with Extracted Data", type="primary", use_container_width=True):
            # Perform search with parsed data
            query = db_b[db_b['State'] == parsed['state']]
            
            if parsed.get('payer') and parsed['payer'] != 'All Payers':
                # Try to match payer name flexibly
                payer_matches = db_b[db_b['State'] == parsed['state']]['Payer_Name'].unique()
                matched_payer = None
                for p in payer_matches:
                    if parsed['payer'].lower() in p.lower() or p.lower() in parsed['payer'].lower():
                        matched_payer = p
                        break
                if matched_payer:
                    query = query[query['Payer_Name'] == matched_payer]
            
            if parsed.get('drug_class'):
                query = query[query['Drug_Class'] == parsed['drug_class']]
            
            # Filter by diagnosis
            if parsed.get('diagnosis') == "Cluster Headache":
                query = query[query['Drug_Class'].str.contains('Cluster', case=False, na=False)]
            elif parsed.get('diagnosis') == "Chronic Migraine":
                query = query[query['Medication_Category'].str.contains('Chronic|Preventive', case=False, na=False)]
            else:  # Episodic
                query = query[~query['Medication_Category'].str.contains('Chronic', case=False, na=False)]
            
            st.session_state.search_results = query
            st.session_state.patient_age = parsed.get('age', 35)
            st.session_state.show_results = True
            st.rerun()
    
    quick_search_mode = False

# Sidebar filters
st.sidebar.header("🔍 Search Filters")

# State selection
states = sorted(db_b['State'].unique().tolist())
selected_state = st.sidebar.selectbox(
    "State",
    options=states,
    index=states.index('PA') if 'PA' in states else 0
)

# Filter payers by state
state_payers = db_b[db_b['State'] == selected_state]['Payer_Name'].unique().tolist()
selected_payer = st.sidebar.selectbox(
    "Payer",
    options=['All Payers'] + sorted(state_payers)
)

# Drug class selection - filtered by state
state_drug_classes = sorted(db_b[db_b['State'] == selected_state]['Drug_Class'].unique().tolist())
selected_drug = st.sidebar.selectbox(
    "Medication Class",
    options=state_drug_classes,
    help=f"{len(state_drug_classes)} drug classes available in {selected_state}"
)

# Headache type
headache_type = st.sidebar.radio(
    "Headache Type",
    options=["Chronic Migraine", "Episodic Migraine", "Cluster Headache"],
    help="Select the primary diagnosis"
)

# Patient age (for pediatric overrides)
patient_age = st.sidebar.number_input(
    "Patient Age (years)",
    min_value=1,
    max_value=120,
    value=35,
    help="Used to check pediatric prescribing restrictions"
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

search_clicked = st.sidebar.button("🔎 Search Policies", type="primary", use_container_width=True)

# Main content area - show results from either search method
if (search_clicked or st.session_state.search_results is not None) or st.session_state.get('show_results', False):
    if search_clicked:
        # Perform search from sidebar
        query = db_b[db_b['State'] == selected_state]
        
        if selected_payer != 'All Payers':
            query = query[query['Payer_Name'] == selected_payer]
        
        query = query[query['Drug_Class'] == selected_drug]
        
        # Filter by headache type
        if headache_type == "Cluster Headache":
            query = query[query['Drug_Class'].str.contains('Cluster', case=False, na=False)]
        elif headache_type == "Chronic Migraine":
            query = query[query['Medication_Category'].str.contains('Chronic|Preventive', case=False, na=False)]
        else:  # Episodic
            query = query[~query['Medication_Category'].str.contains('Chronic', case=False, na=False)]
        
        st.session_state.search_results = query
        st.session_state.patient_age = patient_age
    
    results = st.session_state.search_results
    patient_age_display = st.session_state.get('patient_age', patient_age)
    
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
        
        # Display each policy
        for idx, row in results.iterrows():
            with st.expander(f"📋 {row['Payer_Name']} - {row['Drug_Class']}", expanded=True):
                
                # Payer info
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Payer:** {row['Payer_Name']}")
                    st.markdown(f"**State:** {row['State']}")
                    st.markdown(f"**Line of Business:** {row['LOB']}")
                    st.markdown(f"**Medication Category:** {row['Medication_Category']}")
                
                with col2:
                    # Gold Card status
                    if pd.notna(row.get('Gold_Card_Available')) and row['Gold_Card_Available'] == 'Yes':
                        st.markdown('<div class="success-box">✅ <strong>Gold Card Available</strong><br>' + 
                                  f"{row.get('Gold_Card_Threshold', 'Check state requirements')}</div>", 
                                  unsafe_allow_html=True)
                
                # Step therapy requirements
                if row['Step_Therapy_Required'] == 'Yes':
                    st.markdown("### 🔄 Step Therapy Requirements")
                    
                    # Use Streamlit info box instead of custom HTML
                    st.info(f"**Step 1:** {row['Step_1_Requirement']}\n\n**Duration:** {row['Step_1_Duration']}")
                    
                    if pd.notna(row['Step_2_Requirement']) and row['Step_2_Requirement'] != 'N/A':
                        st.info(f"**Step 2:** {row['Step_2_Requirement']}\n\n**Duration:** {row.get('Step_2_Duration', 'See policy')}")
                else:
                    st.markdown('<div class="success-box">✅ No step therapy required</div>', unsafe_allow_html=True)
                
                # Contraindication bypass
                if pd.notna(row.get('Contraindication_Bypass')) and row['Contraindication_Bypass'] != 'None':
                    st.markdown("### 🚫 Exception Criteria")
                    st.info(f"**Contraindication Bypass:** {row['Contraindication_Bypass']}")
                
                # Quantity limits
                if pd.notna(row.get('Quantity_Limit')):
                    st.markdown(f"**Quantity Limit:** {row['Quantity_Limit']}")
                
                # Episodic vs Chronic handling
                if pd.notna(row.get('Episodic_Same_As_Chronic')):
                    if row['Episodic_Same_As_Chronic'] == False:
                        st.markdown('<div class="warning-box">⚠️ <strong>Different rules for episodic vs chronic</strong><br>' +
                                  f"{row.get('Episodic_Notes', 'See policy details')}</div>",
                                  unsafe_allow_html=True)
                
                # Get denial code details
                if pd.notna(row.get('Vault_Denial_Code')):
                    denial_info = db_c[db_c['Vault_Denial_Code'] == row['Vault_Denial_Code']]
                    if len(denial_info) > 0:
                        denial_row = denial_info.iloc[0]
                        
                        with st.expander("💬 Clinical Appeal Language"):
                            st.markdown(f"**Denial Code:** {denial_row['Vault_Denial_Code']}")
                            st.markdown(f"**Reason:** {denial_row.get('Denial_Reason', 'N/A')}")
                            
                            if pd.notna(denial_row.get('Winning_Clinical_Phrases_Universal')):
                                st.markdown("**Recommended Appeal Language:**")
                                st.markdown(f"> {denial_row['Winning_Clinical_Phrases_Universal']}")
                            
                            if pd.notna(denial_row.get('Source_Authority')):
                                st.markdown(f'<span class="evidence-tag">📚 {denial_row["Source_Authority"]}</span>', 
                                          unsafe_allow_html=True)
                
                # Pediatric check
                if patient_age_display < 18:
                    # Get drug class from results if not using sidebar
                    check_drug = selected_drug if 'selected_drug' in dir() else (results.iloc[0]['Drug_Class'] if len(results) > 0 else None)
                    
                    if check_drug:
                        ped_overrides = db_e[
                            (db_e['Medication_Name'].str.contains(check_drug, case=False, na=False)) |
                            (db_e['Drug_Class'] == check_drug)
                        ]
                        
                        if len(ped_overrides) > 0:
                            st.markdown('<div class="warning-box">👶 <strong>Pediatric Considerations</strong></div>', 
                                      unsafe_allow_html=True)
                            for _, ped_row in ped_overrides.iterrows():
                                age_range = ped_row.get('Age_Range', 'See policy')
                                restriction = ped_row.get('Restriction_Type', 'Age restriction')
                                st.markdown(f"- **{age_range}:** {restriction}")

# Action buttons
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📝 Generate PA Documentation", type="primary", use_container_width=True):
        st.session_state.show_pa_text = True

with col2:
    if st.button("⚕️ Check MOH Risk", use_container_width=True):
        st.session_state.show_moh_check = True

with col3:
    if st.button("📊 View ICD-10 Codes", use_container_width=True):
        with st.expander("ICD-10 Diagnosis Codes", expanded=True):
            # Filter ICD-10 codes by headache type
            if headache_type == "Cluster Headache":
                icd_filter = icd10[icd10['ICD10_Code'].str.startswith('G44.0')]
            elif headache_type == "Chronic Migraine":
                icd_filter = icd10[icd10['ICD10_Code'].str.contains('G43.*1', regex=True)]
            else:
                icd_filter = icd10[icd10['ICD10_Code'].str.contains('G43.*0', regex=True)]
            
            st.dataframe(
                icd_filter[['ICD10_Code', 'ICD10_Description', 'Diagnostic_Criteria_Summary']],
                use_container_width=True,
                hide_index=True
            )

# PA Text Generator
if st.session_state.show_pa_text and st.session_state.search_results is not None:
    st.markdown("---")
    st.markdown("### 📝 Prior Authorization Documentation")
    
    results = st.session_state.search_results
    if len(results) > 0:
        row = results.iloc[0]
        
        pa_text = f"""
**PRIOR AUTHORIZATION REQUEST**
Generated: {datetime.now().strftime('%B %d, %Y')}

**PATIENT INFORMATION**
Diagnosis: {headache_type}
Age: {patient_age} years

**REQUESTED MEDICATION**
Drug Class: {selected_drug}
Category: {row['Medication_Category']}

**PAYER INFORMATION**
Payer: {row['Payer_Name']}
State: {selected_state}
Line of Business: {row['LOB']}

**CLINICAL JUSTIFICATION**
"""
        
        if row['Step_Therapy_Required'] == 'Yes':
            pa_text += f"\n**Step Therapy Documentation:**\n"
            pa_text += f"Step 1 Requirement: {row['Step_1_Requirement']}\n"
            pa_text += f"Duration Completed: {row['Step_1_Duration']}\n"
            pa_text += f"\nPatient has completed the required prior trials with documented inadequate response or contraindications.\n"
        
        # Add denial code language
        if pd.notna(row.get('Vault_Denial_Code')):
            denial_info = db_c[db_c['Vault_Denial_Code'] == row['Vault_Denial_Code']]
            if len(denial_info) > 0:
                denial_row = denial_info.iloc[0]
                if pd.notna(denial_row.get('Winning_Clinical_Phrases_Universal')):
                    pa_text += f"\n**Clinical Rationale:**\n{denial_row['Winning_Clinical_Phrases_Universal']}\n"
        
        pa_text += f"\n**REFERENCE CITATIONS**\n"
        pa_text += "- American Headache Society Position Statement 2024\n"
        pa_text += "- American College of Physicians Guidelines 2025\n"
        
        st.code(pa_text, language=None)
        
        if st.button("📋 Copy to Clipboard"):
            st.success("✅ PA text copied! (Feature will be enabled in deployed version)")

# MOH Checker
if st.session_state.show_moh_check:
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

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #5A5A5A; font-size: 0.9rem; font-family: Source Sans Pro, sans-serif;'>
    <strong style='color: #4B0082;'>The Headache Vault</strong> | Demo Version 1.0 | February 2026<br>
    Infrastructure to Scale Specialist-Level Care<br>
    752 payer policies • 50 states • 1,088 payers • Coverage expanding weekly<br>
    Clinical logic based on AHS 2021/2024, ACP 2025, ICHD-3 Criteria
</div>
""", unsafe_allow_html=True)
