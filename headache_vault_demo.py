import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="The Headache Vault - PA Automation Demo",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for medical professional interface
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4788;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .step-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f4788;
        margin: 1rem 0;
        color: #262730;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
        color: #856404;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        color: #155724;
    }
    .evidence-tag {
        display: inline-block;
        background-color: #e7f3ff;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        margin: 0.25rem;
        color: #0366d6;
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

# Header
st.markdown('<div class="main-header">🧠 The Headache Vault</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Prior Authorization Automation for Headache Medicine</div>', unsafe_allow_html=True)

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
st.sidebar.info(f"📊 {total_in_state} policies in {selected_state}")

# Database coverage note
st.sidebar.caption("💡 Database includes 752 policies across 50 states. Preventive gepant coverage expanding weekly.")

search_clicked = st.sidebar.button("🔎 Search Policies", type="primary", use_container_width=True)

# Main content area
if search_clicked or st.session_state.search_results is not None:
    if search_clicked:
        # Perform search
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
    
    results = st.session_state.search_results
    
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
                if patient_age < 18:
                    ped_overrides = db_e[
                        (db_e['Medication_Name'].str.contains(selected_drug, case=False, na=False)) |
                        (db_e['Drug_Class'] == selected_drug)
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
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <strong>The Headache Vault</strong> | Demo Version 1.0 | February 2026<br>
    752 payer policies • 50 states • 1,088 payers • Coverage expanding weekly<br>
    Clinical logic based on AHS 2021/2024, ACP 2025, ICHD-3 Criteria
</div>
""", unsafe_allow_html=True)
