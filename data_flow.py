"""
The Headache Vault - Unified Data Flow Module
=============================================

This module provides centralized session state management for the PA automation platform.
All components should read from and write to the PatientContext through the SessionStateManager.

Usage:
    # At app startup
    from data_flow import SessionStateManager
    SessionStateManager.initialize()
    
    # In AI Parser
    SessionStateManager.set_from_ai_parse(parsed_data)
    
    # In Sidebar
    ctx = SessionStateManager.get_context()
    # Use ctx.state, ctx.payer, ctx.age, etc.
    
    # To update from user input
    SessionStateManager.update_context(state='NY', age=42)
"""

import streamlit as st
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json


# =============================================================================
# PATIENT CONTEXT MODEL
# =============================================================================

@dataclass
class PatientContext:
    """
    Unified patient data model for all components.
    
    This is the single source of truth for patient information throughout
    the application. All components should read from and write to this model
    via the SessionStateManager.
    
    Attributes:
        state: Two-letter state code (e.g., 'PA', 'NY')
        payer: Insurance company name (exact match to database)
        drug_class: Medication class being requested
        diagnosis: Primary diagnosis (Chronic Migraine, Episodic Migraine, Cluster Headache)
        age: Patient age in years
        headache_type: Same as diagnosis (for backward compatibility)
        prior_medications: List of previously tried medications
        confidence: AI parsing confidence level (high/medium/low)
        clinical_note: Raw clinical note text (if parsed)
        last_updated: Timestamp of last update
        source: Origin of data ('ai_parsed', 'manual', 'edited')
    """
    
    # Core clinical data
    state: str = "PA"
    payer: Optional[str] = None
    drug_class: Optional[str] = None
    diagnosis: str = "Chronic Migraine"
    age: int = 35
    headache_type: str = "Chronic Migraine"
    
    # Treatment history
    prior_medications: List[str] = field(default_factory=list)
    
    # AI parsing metadata
    confidence: str = "low"
    clinical_note: str = ""
    
    # State management
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "manual"  # "ai_parsed" | "manual" | "edited"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for session state storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PatientContext':
        """Reconstruct from dictionary."""
        # Filter to only valid fields
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)
    
    def update(self, **kwargs) -> 'PatientContext':
        """Update fields and refresh timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.last_updated = datetime.now().isoformat()
        return self
    
    def __repr__(self) -> str:
        return (f"PatientContext(state={self.state!r}, payer={self.payer!r}, "
                f"drug_class={self.drug_class!r}, diagnosis={self.diagnosis!r}, "
                f"age={self.age}, source={self.source!r})")


# =============================================================================
# SESSION STATE MANAGER
# =============================================================================

class SessionStateManager:
    """
    Centralized session state management for The Headache Vault.
    
    This class provides a clean interface for managing all session state
    variables. It ensures consistent initialization and provides helper
    methods for common operations.
    
    Usage:
        # Initialize at app startup
        SessionStateManager.initialize()
        
        # Get patient context
        ctx = SessionStateManager.get_context()
        
        # Update from AI parser
        SessionStateManager.set_from_ai_parse(parsed_data)
        
        # Update from user input
        SessionStateManager.update_context(state='NY', payer='Aetna')
    """
    
    # Default values for all session state variables
    DEFAULTS = {
        'patient_context': None,
        'search_results': None,
        'show_pa_text': False,
        'show_moh_check': False,
        'current_page': 'Dashboard',
        'user_mode': 'pcp',
        'pa_count': 0,
        'lead_submitted': False,
        'lead_email': '',
        'show_learning_tips': True,
        'clinical_note': '',
        # Legacy compatibility
        'parsed_data': None,
        'patient_age': 35,
    }
    
    @classmethod
    def initialize(cls) -> None:
        """
        Initialize all session state variables with defaults.
        
        Call this once at app startup to ensure all variables exist.
        Safe to call multiple times - won't overwrite existing values.
        """
        for key, default in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = default
        
        # Initialize patient context as PatientContext object
        if st.session_state.patient_context is None:
            st.session_state.patient_context = PatientContext()
    
    @classmethod
    def get_context(cls) -> PatientContext:
        """
        Get current patient context, ensuring it exists.
        
        Returns:
            PatientContext object with current patient data
        """
        if 'patient_context' not in st.session_state or st.session_state.patient_context is None:
            st.session_state.patient_context = PatientContext()
        
        # Handle case where context was stored as dict
        ctx = st.session_state.patient_context
        if isinstance(ctx, dict):
            ctx = PatientContext.from_dict(ctx)
            st.session_state.patient_context = ctx
        
        return ctx
    
    @classmethod
    def update_context(cls, source: str = 'manual', **kwargs) -> PatientContext:
        """
        Update patient context with new values.
        
        Args:
            source: Origin of update ('manual', 'ai_parsed', 'edited')
            **kwargs: Fields to update (state, payer, age, etc.)
        
        Returns:
            Updated PatientContext object
        """
        ctx = cls.get_context()
        ctx.update(**kwargs)
        ctx.source = source
        st.session_state.patient_context = ctx
        
        # Sync legacy session state for backward compatibility
        cls._sync_legacy_state(ctx)
        
        return ctx
    
    @classmethod
    def set_from_ai_parse(cls, parsed_data: dict) -> PatientContext:
        """
        Update context from AI parser output.
        
        Maps the AI parser's JSON output to the PatientContext fields
        and marks the source as 'ai_parsed'.
        
        Args:
            parsed_data: Dictionary from Claude API parse response
        
        Returns:
            Updated PatientContext object
        """
        ctx = cls.get_context()
        
        # Map AI parser output to context
        mapping = {
            'state': parsed_data.get('state'),
            'payer': parsed_data.get('payer'),
            'drug_class': parsed_data.get('drug_class'),
            'diagnosis': parsed_data.get('diagnosis'),
            'age': parsed_data.get('age'),
            'prior_medications': parsed_data.get('prior_medications', []),
            'confidence': parsed_data.get('confidence', 'low'),
        }
        
        # Only update non-None values
        updates = {k: v for k, v in mapping.items() if v is not None}
        
        ctx.update(**updates)
        ctx.source = 'ai_parsed'
        
        # Sync headache_type with diagnosis
        if updates.get('diagnosis'):
            ctx.headache_type = updates['diagnosis']
        
        st.session_state.patient_context = ctx
        
        # Also store in legacy format for backward compatibility
        st.session_state.parsed_data = parsed_data
        cls._sync_legacy_state(ctx)
        
        return ctx
    
    @classmethod
    def _sync_legacy_state(cls, ctx: PatientContext) -> None:
        """
        Sync legacy session state variables for backward compatibility.
        
        This ensures components still using the old session state format
        continue to work during migration.
        """
        st.session_state.patient_age = ctx.age
        
        # Update parsed_data if it exists
        if st.session_state.parsed_data is None:
            st.session_state.parsed_data = {}
        
        st.session_state.parsed_data.update({
            'state': ctx.state,
            'payer': ctx.payer,
            'drug_class': ctx.drug_class,
            'diagnosis': ctx.diagnosis,
            'age': ctx.age,
            'prior_medications': ctx.prior_medications,
            'confidence': ctx.confidence,
        })
    
    @classmethod
    def clear_context(cls) -> None:
        """Reset patient context to defaults."""
        st.session_state.patient_context = PatientContext()
        st.session_state.parsed_data = None
        st.session_state.patient_age = 35
    
    @classmethod
    def clear_search(cls) -> None:
        """Clear search results and PA display state."""
        st.session_state.search_results = None
        st.session_state.show_pa_text = False
        st.session_state.show_moh_check = False


# =============================================================================
# SEARCH SERVICE
# =============================================================================

class SearchService:
    """
    Service for building and executing policy searches.
    
    Uses the patient context to construct database queries
    and return matching policy results.
    """
    
    @staticmethod
    def build_query(db_b: pd.DataFrame, ctx: Optional[PatientContext] = None) -> pd.DataFrame:
        """
        Build search query from patient context.
        
        Args:
            db_b: Database B (policy database)
            ctx: Optional PatientContext (uses session state if not provided)
        
        Returns:
            Filtered DataFrame of matching policies
        """
        if ctx is None:
            ctx = SessionStateManager.get_context()
        
        # Start with state filter
        query = db_b[db_b['State'] == ctx.state].copy()
        
        # Payer filter (with fuzzy matching)
        if ctx.payer and ctx.payer != 'All Payers':
            query = SearchService._filter_by_payer(query, ctx.payer)
        
        # Drug class filter
        if ctx.drug_class:
            query = query[query['Drug_Class'] == ctx.drug_class]
        
        # Diagnosis-based filtering
        query = SearchService._filter_by_diagnosis(query, ctx)
        
        return query
    
    @staticmethod
    def _filter_by_payer(query: pd.DataFrame, payer: str) -> pd.DataFrame:
        """Apply payer filter with fuzzy matching support."""
        payer_matches = query['Payer_Name'].unique()
        matched_payer = None
        
        # Exact match first
        if payer in payer_matches:
            matched_payer = payer
        else:
            # Fuzzy match
            payer_lower = payer.lower()
            for p in payer_matches:
                if payer_lower in p.lower() or p.lower() in payer_lower:
                    matched_payer = p
                    break
        
        if matched_payer:
            return query[query['Payer_Name'] == matched_payer]
        
        return query
    
    @staticmethod
    def _filter_by_diagnosis(query: pd.DataFrame, ctx: PatientContext) -> pd.DataFrame:
        """Apply diagnosis-based filtering logic."""
        if query.empty:
            return query
        
        if ctx.diagnosis == "Cluster Headache":
            # Only apply if not already filtered to a cluster drug
            if ctx.drug_class and 'Cluster' not in ctx.drug_class:
                cluster_filtered = query[query['Drug_Class'].str.contains('Cluster', case=False, na=False)]
                if not cluster_filtered.empty:
                    return cluster_filtered
        
        elif ctx.diagnosis == "Chronic Migraine":
            chronic_filtered = query[query['Medication_Category'].str.contains('Chronic|Preventive', case=False, na=False)]
            if not chronic_filtered.empty:
                return chronic_filtered
        
        # Episodic migraine - no additional filtering (too aggressive)
        return query
    
    @staticmethod
    def execute_search(db_b: pd.DataFrame) -> pd.DataFrame:
        """
        Execute search and store results in session state.
        
        Args:
            db_b: Database B (policy database)
        
        Returns:
            Search results DataFrame
        """
        results = SearchService.build_query(db_b)
        st.session_state.search_results = results
        return results


# =============================================================================
# SIDEBAR HELPER FUNCTIONS
# =============================================================================

class SidebarHelper:
    """
    Helper functions for rendering sidebar filters with context integration.
    """
    
    @staticmethod
    def get_state_index(states: List[str]) -> int:
        """Get the index for state dropdown based on patient context."""
        ctx = SessionStateManager.get_context()
        if ctx.state in states:
            return states.index(ctx.state)
        return states.index('PA') if 'PA' in states else 0
    
    @staticmethod
    def get_payer_index(payer_options: List[str]) -> int:
        """Get the index for payer dropdown with fuzzy matching."""
        ctx = SessionStateManager.get_context()
        
        if not ctx.payer:
            return 0
        
        # Try exact match
        for i, p in enumerate(payer_options):
            if ctx.payer == p:
                return i
        
        # Try fuzzy match
        payer_lower = ctx.payer.lower()
        for i, p in enumerate(payer_options):
            if payer_lower in p.lower() or p.lower() in payer_lower:
                return i
        
        return 0
    
    @staticmethod
    def get_drug_index(drug_options: List[str]) -> int:
        """Get the index for drug class dropdown."""
        ctx = SessionStateManager.get_context()
        if ctx.drug_class in drug_options:
            return drug_options.index(ctx.drug_class)
        return 0
    
    @staticmethod
    def get_headache_index(headache_options: List[str]) -> int:
        """Get the index for headache type radio."""
        ctx = SessionStateManager.get_context()
        if ctx.headache_type in headache_options:
            return headache_options.index(ctx.headache_type)
        if ctx.diagnosis in headache_options:
            return headache_options.index(ctx.diagnosis)
        return 0


# =============================================================================
# PA GENERATION HELPER
# =============================================================================

class PAGenerator:
    """
    Helper for generating prior authorization documentation.
    """
    
    @staticmethod
    def generate(row: pd.Series, db_c: pd.DataFrame, mode: str = 'pcp') -> str:
        """
        Generate PA documentation from search result and patient context.
        
        Args:
            row: Single row from search results
            db_c: Database C (denial codes)
            mode: 'pcp' for detailed, 'specialist' for compact
        
        Returns:
            Formatted PA text string
        """
        ctx = SessionStateManager.get_context()
        
        if mode == 'pcp':
            return PAGenerator._generate_detailed(row, db_c, ctx)
        else:
            return PAGenerator._generate_compact(row, db_c, ctx)
    
    @staticmethod
    def _generate_detailed(row: pd.Series, db_c: pd.DataFrame, ctx: PatientContext) -> str:
        """Generate detailed PA for PCP mode."""
        
        # Determine diagnosis code
        diag_codes = {
            "Chronic Migraine": "G43.709",
            "Episodic Migraine": "G43.909", 
            "Cluster Headache": "G44.009"
        }
        diag_code = diag_codes.get(ctx.diagnosis, "G43.909")
        
        pa_text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    PRIOR AUTHORIZATION REQUEST                    ║
╠══════════════════════════════════════════════════════════════════╣
║  Date: {datetime.now().strftime('%Y-%m-%d')}
║  Payer: {row['Payer_Name']}
║  State: {ctx.state}
╚══════════════════════════════════════════════════════════════════╝

PATIENT INFORMATION
───────────────────
  Diagnosis: {ctx.diagnosis} ({diag_code})
  Age: {ctx.age} years

REQUESTED MEDICATION
────────────────────
  Drug Class: {ctx.drug_class or row.get('Drug_Class', 'N/A')}
  Category: {row['Medication_Category']}
  Line of Business: {row['LOB']}
"""
        
        # Step therapy section
        if row.get('Step_Therapy_Required') == 'Yes':
            step_req = row.get('Step_1_Requirement', row.get('Step_Therapy_Requirements', 'Per policy'))
            step_dur = row.get('Step_1_Duration', row.get('Step_Therapy_Duration', 'Trial duration per policy'))
            
            pa_text += f"""
STEP THERAPY REQUIREMENTS
─────────────────────────
  Status: REQUIRED ⚠️
  Requirement: {step_req}
  Duration: {step_dur}
"""
            # Add prior medications if available
            if ctx.prior_medications:
                pa_text += f"  Prior Therapies: {', '.join(ctx.prior_medications)}\n"
                pa_text += "  Documentation: Completed with documented failure ✓\n"
        else:
            pa_text += """
STEP THERAPY REQUIREMENTS
─────────────────────────
  Status: NOT REQUIRED ✓
"""
        
        # Clinical rationale from denial codes
        if pd.notna(row.get('Vault_Denial_Code')):
            denial_info = db_c[db_c['Vault_Denial_Code'] == row['Vault_Denial_Code']]
            if len(denial_info) > 0:
                denial_row = denial_info.iloc[0]
                if pd.notna(denial_row.get('Winning_Clinical_Phrases_Universal')):
                    pa_text += f"""
CLINICAL RATIONALE
──────────────────
{denial_row['Winning_Clinical_Phrases_Universal']}
"""
        
        pa_text += """
REFERENCES
──────────
  • American Headache Society Guidelines 2024
  • ICHD-3 Diagnostic Criteria
  • AAN Evidence-Based Guidelines
"""
        
        return pa_text
    
    @staticmethod
    def _generate_compact(row: pd.Series, db_c: pd.DataFrame, ctx: PatientContext) -> str:
        """Generate compact PA for specialist mode."""
        
        diag_codes = {
            "Chronic Migraine": "G43.709",
            "Episodic Migraine": "G43.909",
            "Cluster Headache": "G44.009"
        }
        diag_code = diag_codes.get(ctx.diagnosis, "G43.909")
        
        pa_text = f"""{datetime.now().strftime('%Y-%m-%d')} | {row['Payer_Name']} | {ctx.state}

Dx: {ctx.diagnosis} ({diag_code})
Age: {ctx.age}y
Rx: {ctx.drug_class or row.get('Drug_Class', 'N/A')} ({row['Medication_Category']})
LOB: {row['LOB']}
"""
        
        if row.get('Step_Therapy_Required') == 'Yes':
            step_req = row.get('Step_1_Requirement', 'Prior preventive')
            step_dur = row.get('Step_1_Duration', 'Per policy')
            pa_text += f"""
Step Therapy: REQUIRED
  - {step_req}
  - Duration: {step_dur}
  - Status: Completed with documented failure
"""
        else:
            pa_text += "\nStep Therapy: Not required\n"
        
        # Add denial code rationale
        if pd.notna(row.get('Vault_Denial_Code')):
            denial_info = db_c[db_c['Vault_Denial_Code'] == row['Vault_Denial_Code']]
            if len(denial_info) > 0:
                denial_row = denial_info.iloc[0]
                if pd.notna(denial_row.get('Winning_Clinical_Phrases_Universal')):
                    pa_text += f"\nClinical Rationale:\n{denial_row['Winning_Clinical_Phrases_Universal']}\n"
        
        pa_text += "\nRefs: AHS 2024, ICHD-3, AAN Guidelines"
        
        return pa_text


# =============================================================================
# INTEGRATION SNIPPET FOR EXISTING APP
# =============================================================================

"""
INTEGRATION INSTRUCTIONS
========================

To integrate this module into your existing headache_vault_demo.py:

1. Add this import at the top of the file:
   
   from data_flow import SessionStateManager, SearchService, SidebarHelper, PAGenerator

2. Replace the session state initialization block (lines 888-910) with:
   
   SessionStateManager.initialize()

3. In the AI Parser section, after parsing succeeds, replace:
   
   st.session_state.parsed_data = parsed_data
   
   with:
   
   SessionStateManager.set_from_ai_parse(parsed_data)

4. In the sidebar filters, replace hardcoded defaults like:
   
   default_state = 'PA'
   if 'parsed_data' in st.session_state and st.session_state.parsed_data.get('state'):
       parsed_state = st.session_state.parsed_data['state'].upper()
       ...
   
   with:
   
   state_index = SidebarHelper.get_state_index(states)
   selected_state = st.sidebar.selectbox("State", options=states, index=state_index)

5. For the search button, replace the query building logic with:
   
   results = SearchService.execute_search(db_b)

6. For PA generation, use:
   
   pa_text = PAGenerator.generate(row, db_c, mode=st.session_state.user_mode)

This allows incremental migration - the module maintains backward compatibility
with the existing session state variables while introducing the new unified model.
"""


# =============================================================================
# DEBUG HELPER
# =============================================================================

def debug_session_state() -> str:
    """
    Generate a debug report of current session state.
    
    Useful for troubleshooting data flow issues.
    
    Returns:
        Formatted string with current state values
    """
    ctx = SessionStateManager.get_context()
    
    report = f"""
═══════════════════════════════════════════════════════════════
                    SESSION STATE DEBUG REPORT
═══════════════════════════════════════════════════════════════

PATIENT CONTEXT
───────────────
  State:            {ctx.state}
  Payer:            {ctx.payer or 'Not set'}
  Drug Class:       {ctx.drug_class or 'Not set'}
  Diagnosis:        {ctx.diagnosis}
  Age:              {ctx.age}
  Headache Type:    {ctx.headache_type}
  Prior Meds:       {ctx.prior_medications or 'None'}
  Confidence:       {ctx.confidence}
  Source:           {ctx.source}
  Last Updated:     {ctx.last_updated}

UI STATE
────────
  Current Page:     {st.session_state.get('current_page', 'Unknown')}
  User Mode:        {st.session_state.get('user_mode', 'Unknown')}
  Show PA Text:     {st.session_state.get('show_pa_text', False)}
  Show MOH Check:   {st.session_state.get('show_moh_check', False)}
  PA Count:         {st.session_state.get('pa_count', 0)}

SEARCH STATE
────────────
  Results:          {len(st.session_state.get('search_results') or []) if st.session_state.get('search_results') is not None else 'None'}

LEGACY STATE (for backward compatibility)
─────────────────────────────────────────
  parsed_data:      {'Present' if st.session_state.get('parsed_data') else 'None'}
  patient_age:      {st.session_state.get('patient_age', 'Not set')}
  clinical_note:    {'Present' if st.session_state.get('clinical_note') else 'None'}

═══════════════════════════════════════════════════════════════
"""
    return report


# Allow running as standalone to test
if __name__ == "__main__":
    print("Data Flow Module for The Headache Vault")
    print("=" * 50)
    print("\nThis module provides:")
    print("  - PatientContext: Unified patient data model")
    print("  - SessionStateManager: Centralized state management")
    print("  - SearchService: Query building and execution")
    print("  - SidebarHelper: UI integration helpers")
    print("  - PAGenerator: PA documentation generation")
    print("\nSee docstrings and integration instructions for usage.")
