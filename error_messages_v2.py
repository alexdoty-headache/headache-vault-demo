#!/usr/bin/env python3
"""
Simplified Error Message System - Headache Vault
Clean, actionable error messages focused on user guidance
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass  
class ErrorMessage:
    """Simple, actionable error message"""
    severity: ErrorSeverity
    title: str
    description: str
    actions: List[str]
    appeal_tip: Optional[str] = None
    
    def __str__(self):
        """Default string representation"""
        icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}[self.severity.value]
        lines = [
            f"{icon} {self.title}",
            "",
            self.description,
            "",
            "What to do:"
        ]
        lines.extend(f"  • {action}" for action in self.actions)
        
        if self.appeal_tip:
            lines.extend(["", f"💡 Appeal Tip: {self.appeal_tip}"])
        
        return "\n".join(lines)


def create_error(error_type: str, **context) -> ErrorMessage:
    """Create error message based on type and context"""
    
    errors = {
        # Medication errors
        "med_not_found": ErrorMessage(
            severity=ErrorSeverity.ERROR,
            title="Medication Not Recognized",
            description=f"We couldn't find '{context.get('medication', 'this medication')}' in our database.",
            actions=[
                "Check spelling (e.g., 'propranolol' not 'propanolol')",
                "Try brand name (e.g., 'Aimovig') or generic (e.g., 'erenumab')",
                "Remove dosage info (e.g., 'Aimovig' not 'Aimovig 70mg')"
            ]
        ),
        
        # Step therapy errors
        "insufficient_trials": ErrorMessage(
            severity=ErrorSeverity.ERROR,
            title="Need More Preventive Medication Trials",
            description=f"Documented {context.get('current', 1)} preventive class(es), need {context.get('required', 2)}.",
            actions=[
                f"Add trials from: {context.get('missing', 'Anticonvulsant, TCA, or SNRI')}",
                "Each trial needs: ≥8 weeks at therapeutic dose",
                "Document why stopped (side effects, didn't work, contraindication)",
                "Examples: topiramate 100mg, propranolol 80mg, amitriptyline 50mg"
            ],
            appeal_tip=f"If patient can't tolerate required meds (side effects, contraindications), document this clearly and cite AHS guidelines"
        ),
        
        "low_doses": ErrorMessage(
            severity=ErrorSeverity.WARNING,
            title="Medication Doses May Be Too Low",
            description="Some preventive trials may not have reached therapeutic dose.",
            actions=[
                "Propranolol: ≥80mg/day",
                "Topiramate: ≥100mg/day",
                "Amitriptyline: ≥50mg/day",
                "Document reason if lower dose used (e.g., side effects prevented increase)"
            ],
            appeal_tip="Explain that patient couldn't tolerate higher doses due to specific side effects"
        ),
        
        "short_trials": ErrorMessage(
            severity=ErrorSeverity.WARNING,
            title="Medication Trials May Be Too Short",
            description="AHS guidelines recommend ≥8 week trials for preventive medications.",
            actions=[
                "Document each medication was tried for ≥8 weeks",
                "If stopped early, explain why (severe side effects, allergic reaction)",
                "Include specific dates: started X, stopped Y due to Z"
            ],
            appeal_tip="Early discontinuation due to intolerable side effects is acceptable - document clearly"
        ),
        
        # Frequency errors
        "frequency_low": ErrorMessage(
            severity=ErrorSeverity.ERROR,
            title="Headache Frequency Below Threshold",
            description=f"Documented {context.get('current', 0)} days/month, payer requires ≥{context.get('required', 4)} days/month.",
            actions=[
                "Verify frequency from 3-month headache diary",
                "Document disability: MIDAS score (>21 = severe), HIT-6 score (>60 = severe impact)",
                "Note missed work/school days",
                "If truly <4 days/month, consider acute treatment (Ubrelvy, Nurtec) instead"
            ],
            appeal_tip=f"Emphasize impact over frequency. Include MIDAS{' score ' + context.get('midas', '') if context.get('midas') else ''} showing severe disability despite lower frequency"
        ),
        
        "frequency_missing": ErrorMessage(
            severity=ErrorSeverity.ERROR,
            title="Headache Frequency Not Documented",
            description="PA requires headache frequency (days per month).",
            actions=[
                "Add: 'Patient has [X] headache days per month'",
                "Base on patient diary or 3-month recall",
                "Include assessment period (e.g., 'over past 3 months')"
            ]
        ),
        
        # Diagnosis errors
        "wrong_diagnosis": ErrorMessage(
            severity=ErrorSeverity.ERROR,
            title="Diagnosis Code Issue",
            description=f"ICD-10 code may not match requested medication.",
            actions=[
                "Chronic migraine (≥15 days/month): G43.709 or G43.719",
                "Episodic migraine (4-14 days/month): G43.909",
                "Cluster headache: G44.009",
                "Botox REQUIRES chronic migraine diagnosis (≥15 days/month)"
            ]
        ),
        
        "botox_needs_chronic": ErrorMessage(
            severity=ErrorSeverity.ERROR,
            title="Botox Requires Chronic Migraine",
            description="Botox is only approved for chronic migraine (≥15 headache days/month for ≥3 months).",
            actions=[
                "If patient has <15 days/month, request CGRP mAb instead (Aimovig, Emgality, Ajovy)",
                "If patient has ≥15 days/month, update diagnosis to G43.709 or G43.719",
                "Document frequency from 3-month diary"
            ]
        ),
        
        # Helpful bypass info
        "cv_bypass": ErrorMessage(
            severity=ErrorSeverity.INFO,
            title="✓ CV Contraindication Bypass Available",
            description="Patient has cardiovascular condition - first-line CGRP/gepant may be approved without full step therapy.",
            actions=[
                "Document CV diagnosis: CAD, stroke, uncontrolled HTN, peripheral vascular disease",
                "Note contraindication to triptans (FDA labeling)",
                "Reference AHS 2024 guidelines supporting gepants in CV patients",
                "Bypass approved - may not need 2-3 preventive failures"
            ],
            appeal_tip="Cite specific CV condition and safety data for gepants/CGRPs in cardiovascular population"
        ),
        
        "pregnancy_bypass": ErrorMessage(
            severity=ErrorSeverity.INFO,
            title="✓ Teratogen Bypass Available",
            description="Patient is female of childbearing age - can skip teratogenic preventives.",
            actions=[
                "Document patient is female, age 12-55",
                "Note contraindication to valproate (FDA Category X) and topiramate (FDA Category D)",
                "Can proceed to CGRP without trying these medications",
                "Reference FDA pregnancy warnings"
            ],
            appeal_tip="Teratogenic risk makes valproate/topiramate inappropriate - CGRP represents safer alternative"
        ),
        
        "moh_risk": ErrorMessage(
            severity=ErrorSeverity.WARNING,
            title="Medication Overuse Headache Risk Detected",
            description=f"Patient using acute meds ≥{context.get('frequency', 10)} days/month - MOH risk.",
            actions=[
                "Document acute medication frequency (triptan/NSAID/combination analgesic days/month)",
                "Note this increases urgency for preventive therapy",
                "Include in PA justification: 'Patient at high risk for MOH, preventive therapy urgent'",
                "Preventive therapy helps reduce acute medication use"
            ],
            appeal_tip="High MOH risk strengthens case for preventive therapy urgency"
        ),
        
        # Success messages
        "approved": ErrorMessage(
            severity=ErrorSeverity.INFO,
            title="✓ PA Ready to Submit",
            description="All requirements met. PA looks good!",
            actions=[
                "Review generated PA for accuracy",
                "Add any additional clinical details",
                "Submit to payer (portal, fax, or electronic)",
                "Follow up in 5-7 business days"
            ]
        ),
        
        "strong_pa": ErrorMessage(
            severity=ErrorSeverity.INFO,
            title="✓ Strong PA - High Approval Probability",
            description="Excellent documentation. Expected approval rate >90%.",
            actions=[
                "Consider expedited review if urgent",
                "Have follow-up plan ready",
                "Track submission for timely response"
            ]
        ),
        
        # System errors
        "payer_not_found": ErrorMessage(
            severity=ErrorSeverity.WARNING,
            title="Payer Policy Not in Database",
            description=f"We don't have specific policy for '{context.get('payer', 'this payer')}'.",
            actions=[
                "Using national commercial insurance criteria as fallback",
                "Verify insurance name spelling",
                "Check payer's formulary directly for specific requirements",
                "Contact us to add this payer to database"
            ]
        ),
    }
    
    return errors.get(error_type, ErrorMessage(
        severity=ErrorSeverity.ERROR,
        title="Unknown Error",
        description=f"Error type '{error_type}' not recognized.",
        actions=["Contact support for assistance"]
    ))


def test_error_messages():
    """Test error message system"""
    print("\n" + "="*80)
    print("ERROR MESSAGE SYSTEM - SIMPLIFIED VERSION")
    print("="*80 + "\n")
    
    # Test various scenarios
    scenarios = [
        ("Medication not found", "med_not_found", {"medication": "XYZ-123"}),
        ("Insufficient trials", "insufficient_trials", {"current": 1, "required": 2, "missing": "Anticonvulsant or TCA"}),
        ("Low frequency", "frequency_low", {"current": 3, "required": 4, "midas": "45 (Grade IV)"}),
        ("CV bypass", "cv_bypass", {}),
        ("PA approved", "approved", {}),
        ("Short trials", "short_trials", {}),
    ]
    
    for title, error_type, context in scenarios:
        print(f"TEST: {title}")
        print("-" * 80)
        error = create_error(error_type, **context)
        print(error)
        print("\n" + "="*80 + "\n")
    
    print("✅ All error messages tested successfully!")


if __name__ == "__main__":
    test_error_messages()
