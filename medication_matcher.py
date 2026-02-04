#!/usr/bin/env python3
"""
Medication Name Matcher - Headache Vault
Handles brand names, generic names, misspellings, and variations
"""

from typing import Optional, List, Tuple
from difflib import SequenceMatcher
import re


class MedicationMatcher:
    """
    Robust medication name matching with fuzzy logic
    Handles: brand names, generics, misspellings, common variations
    """
    
    def __init__(self):
        # Comprehensive medication alias database
        self.medication_db = {
            # CGRP Monoclonal Antibodies
            "aimovig": {
                "generic": "erenumab",
                "brand": "Aimovig",
                "drug_class": "CGRP mAbs",
                "aliases": ["erenumab", "aimovig", "erenumab-aooe"],
                "common_misspellings": ["aimovag", "aimovig", "erenomab", "erenumob"]
            },
            "emgality": {
                "generic": "galcanezumab",
                "brand": "Emgality",
                "drug_class": "CGRP mAbs",
                "aliases": ["galcanezumab", "emgality", "galcanezumab-gnlm"],
                "common_misspellings": ["emgalaty", "galcanezumob", "galcanezemab"]
            },
            "ajovy": {
                "generic": "fremanezumab",
                "brand": "Ajovy",
                "drug_class": "CGRP mAbs",
                "aliases": ["fremanezumab", "ajovy", "fremanezumab-vfrm"],
                "common_misspellings": ["ajovey", "fremanezemab", "fremanezumob"]
            },
            "vyepti": {
                "generic": "eptinezumab",
                "brand": "Vyepti",
                "drug_class": "CGRP mAbs",
                "aliases": ["eptinezumab", "vyepti", "eptinezumab-jjmr"],
                "common_misspellings": ["viepti", "eptinezemab", "eptinezumob"]
            },
            
            # Gepants (Acute)
            "nurtec": {
                "generic": "rimegepant",
                "brand": "Nurtec ODT",
                "drug_class": "Gepants",
                "aliases": ["rimegepant", "nurtec", "nurtec odt", "nurtec-odt"],
                "common_misspellings": ["nurtac", "rimegapent", "rimegepent"]
            },
            "ubrelvy": {
                "generic": "ubrogepant",
                "brand": "Ubrelvy",
                "drug_class": "Gepants",
                "aliases": ["ubrogepant", "ubrelvy"],
                "common_misspellings": ["ubrelvey", "ubrogapent", "ubrogepent"]
            },
            
            # Gepants (Preventive)
            "qulipta": {
                "generic": "atogepant",
                "brand": "Qulipta",
                "drug_class": "Gepants (Preventive)",
                "aliases": ["atogepant", "qulipta"],
                "common_misspellings": ["qualipta", "atogapent", "atogepent"]
            },
            
            # Ditans
            "reyvow": {
                "generic": "lasmiditan",
                "brand": "Reyvow",
                "drug_class": "Ditans",
                "aliases": ["lasmiditan", "reyvow"],
                "common_misspellings": ["rayvow", "lasmidatan", "lasmiditant"]
            },
            
            # Botox
            "botox": {
                "generic": "onabotulinumtoxinA",
                "brand": "Botox",
                "drug_class": "Botox",
                "aliases": ["onabotulinumtoxina", "botox", "onabotulinum", "onabotulinumtoxin a"],
                "common_misspellings": ["botulinum", "onabotulinum"]
            },
            
            # Triptans
            "sumatriptan": {
                "generic": "sumatriptan",
                "brand": "Imitrex",
                "drug_class": "Triptan",
                "aliases": ["sumatriptan", "imitrex", "sumavel", "zecuity"],
                "common_misspellings": ["sumatripptan", "sumatriptin", "imitrix"]
            },
            "rizatriptan": {
                "generic": "rizatriptan",
                "brand": "Maxalt",
                "drug_class": "Triptan",
                "aliases": ["rizatriptan", "maxalt", "maxalt-mlt"],
                "common_misspellings": ["rizatripptan", "rizatriptin"]
            },
            "zolmitriptan": {
                "generic": "zolmitriptan",
                "brand": "Zomig",
                "drug_class": "Triptan",
                "aliases": ["zolmitriptan", "zomig", "zomig-zmt"],
                "common_misspellings": ["zolmitripptan", "zolmitriptin"]
            },
            "eletriptan": {
                "generic": "eletriptan",
                "brand": "Relpax",
                "drug_class": "Triptan",
                "aliases": ["eletriptan", "relpax"],
                "common_misspellings": ["eletripptan", "eletriptin"]
            },
            "naratriptan": {
                "generic": "naratriptan",
                "brand": "Amerge",
                "drug_class": "Triptan",
                "aliases": ["naratriptan", "amerge"],
                "common_misspellings": ["naratripptan", "naratriptin"]
            },
            "almotriptan": {
                "generic": "almotriptan",
                "brand": "Axert",
                "drug_class": "Triptan",
                "aliases": ["almotriptan", "axert"],
                "common_misspellings": ["almotripptan", "almotriptin"]
            },
            "frovatriptan": {
                "generic": "frovatriptan",
                "brand": "Frova",
                "drug_class": "Triptan",
                "aliases": ["frovatriptan", "frova"],
                "common_misspellings": ["frovatripptan", "frovatriptin"]
            },
            
            # Oral Preventives - Beta Blockers
            "propranolol": {
                "generic": "propranolol",
                "brand": "Inderal",
                "drug_class": "Beta-blocker",
                "aliases": ["propranolol", "inderal", "inderal la", "innopran xl"],
                "common_misspellings": ["propanolol", "propranolal", "propanalol", "indral"]
            },
            "metoprolol": {
                "generic": "metoprolol",
                "brand": "Toprol-XL",
                "drug_class": "Beta-blocker",
                "aliases": ["metoprolol", "toprol", "toprol-xl", "lopressor"],
                "common_misspellings": ["metropolol", "metaprolol", "topral"]
            },
            "timolol": {
                "generic": "timolol",
                "brand": "Blocadren",
                "drug_class": "Beta-blocker",
                "aliases": ["timolol", "blocadren"],
                "common_misspellings": ["timelol", "timolal"]
            },
            "atenolol": {
                "generic": "atenolol",
                "brand": "Tenormin",
                "drug_class": "Beta-blocker",
                "aliases": ["atenolol", "tenormin"],
                "common_misspellings": ["atenalol", "atenolal"]
            },
            
            # Anticonvulsants
            "topiramate": {
                "generic": "topiramate",
                "brand": "Topamax",
                "drug_class": "Anticonvulsant",
                "aliases": ["topiramate", "topamax", "trokendi xr", "qudexy xr"],
                "common_misspellings": ["topimax", "topomax", "topiramat", "topirimate", "topamax"]
            },
            "valproate": {
                "generic": "valproate",
                "brand": "Depakote",
                "drug_class": "Anticonvulsant",
                "aliases": ["valproate", "valproic acid", "divalproex", "depakote", "depakene"],
                "common_misspellings": ["valproat", "divalproax", "depakot"]
            },
            "gabapentin": {
                "generic": "gabapentin",
                "brand": "Neurontin",
                "drug_class": "Anticonvulsant",
                "aliases": ["gabapentin", "neurontin", "gralise"],
                "common_misspellings": ["gabapentin", "neurontin", "gabapantin"]
            },
            "levetiracetam": {
                "generic": "levetiracetam",
                "brand": "Keppra",
                "drug_class": "Anticonvulsant",
                "aliases": ["levetiracetam", "keppra"],
                "common_misspellings": ["levitiracetam", "keppra"]
            },
            "zonisamide": {
                "generic": "zonisamide",
                "brand": "Zonegran",
                "drug_class": "Anticonvulsant",
                "aliases": ["zonisamide", "zonegran"],
                "common_misspellings": ["zonisamid", "zonagran"]
            },
            
            # Tricyclic Antidepressants (TCAs)
            "amitriptyline": {
                "generic": "amitriptyline",
                "brand": "Elavil",
                "drug_class": "TCA",
                "aliases": ["amitriptyline", "elavil"],
                "common_misspellings": ["amitryptiline", "amitriptylin", "elivil"]
            },
            "nortriptyline": {
                "generic": "nortriptyline",
                "brand": "Pamelor",
                "drug_class": "TCA",
                "aliases": ["nortriptyline", "pamelor", "aventyl"],
                "common_misspellings": ["nortryptiline", "nortriptylin"]
            },
            "doxepin": {
                "generic": "doxepin",
                "brand": "Silenor",
                "drug_class": "TCA",
                "aliases": ["doxepin", "silenor", "sinequan"],
                "common_misspellings": ["doxapine", "doxipin"]
            },
            "protriptyline": {
                "generic": "protriptyline",
                "brand": "Vivactil",
                "drug_class": "TCA",
                "aliases": ["protriptyline", "vivactil"],
                "common_misspellings": ["protryptiline", "protriptylin"]
            },
            
            # SNRIs
            "venlafaxine": {
                "generic": "venlafaxine",
                "brand": "Effexor",
                "drug_class": "SNRI",
                "aliases": ["venlafaxine", "effexor", "effexor xr"],
                "common_misspellings": ["venlafaxin", "venlefaxine", "effexer"]
            },
            "duloxetine": {
                "generic": "duloxetine",
                "brand": "Cymbalta",
                "drug_class": "SNRI",
                "aliases": ["duloxetine", "cymbalta"],
                "common_misspellings": ["duloxetin", "duloxatine", "cymbalta"]
            },
            
            # Calcium Channel Blockers (Cluster)
            "verapamil": {
                "generic": "verapamil",
                "brand": "Calan",
                "drug_class": "Cluster Verapamil",
                "aliases": ["verapamil", "calan", "verelan", "covera-hs"],
                "common_misspellings": ["verapamel", "verapamil", "calan"]
            },
            
            # Other
            "lithium": {
                "generic": "lithium",
                "brand": "Lithobid",
                "drug_class": "Cluster Lithium",
                "aliases": ["lithium", "lithobid", "lithium carbonate"],
                "common_misspellings": ["litheum", "litium"]
            },
            "oxygen": {
                "generic": "oxygen",
                "brand": "Oxygen",
                "drug_class": "Cluster Oxygen",
                "aliases": ["oxygen", "o2", "high-flow oxygen"],
                "common_misspellings": []
            },
            
            # ACE Inhibitors
            "lisinopril": {
                "generic": "lisinopril",
                "brand": "Zestril",
                "drug_class": "ACE Inhibitor",
                "aliases": ["lisinopril", "zestril", "prinivil"],
                "common_misspellings": ["lisinopril", "lisinopral", "zestrel"]
            },
            
            # ARBs
            "candesartan": {
                "generic": "candesartan",
                "brand": "Atacand",
                "drug_class": "ARB",
                "aliases": ["candesartan", "atacand"],
                "common_misspellings": ["candesarten", "atacand"]
            },
        }
        
        # Build reverse lookup indices
        self._build_lookup_indices()
        
    def _build_lookup_indices(self):
        """Build reverse lookup dictionaries for fast matching"""
        self.generic_to_key = {}
        self.brand_to_key = {}
        self.alias_to_key = {}
        
        for key, med_data in self.medication_db.items():
            # Generic lookup
            generic = med_data["generic"].lower()
            self.generic_to_key[generic] = key
            
            # Brand lookup
            brand = med_data["brand"].lower()
            self.brand_to_key[brand] = key
            
            # Alias lookup
            for alias in med_data["aliases"]:
                self.alias_to_key[alias.lower()] = key
                
    def normalize_input(self, text: str) -> str:
        """Normalize medication name input"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove dosage information (more comprehensive)
        # Matches: "70mg", "100 mg", "75mg daily", etc.
        text = re.sub(r'\d+\.?\d*\s*(mg|mcg|ml|g|units?)\b.*$', '', text, flags=re.IGNORECASE)
        
        # Remove common suffixes
        text = re.sub(r'\s+(tablets?|capsules?|injection|subcutaneous|oral|daily|bid|tid|qd|prn)\b.*$', '', text, flags=re.IGNORECASE)
        
        # Remove parenthetical content
        text = re.sub(r'\([^)]*\)', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove hyphens between words (but keep "odt" together)
        # Special handling for "nurtec-odt" → "nurtec odt"
        text = text.replace('-', ' ')
        text = ' '.join(text.split())
        
        return text.strip()
        
    def fuzzy_match(self, input_text: str, candidate: str, threshold: float = 0.85) -> float:
        """Calculate similarity ratio between input and candidate"""
        return SequenceMatcher(None, input_text.lower(), candidate.lower()).ratio()
        
    def find_medication(self, input_text: str, threshold: float = 0.85) -> Optional[dict]:
        """
        Find medication using multi-strategy matching
        
        Strategy priority:
        1. Exact match (aliases, generic, brand)
        2. Fuzzy match against aliases
        3. Fuzzy match against common misspellings
        4. Fuzzy match against all medication names
        
        Args:
            input_text: User input medication name
            threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            dict with medication data or None
        """
        normalized = self.normalize_input(input_text)
        
        # Strategy 1: Exact match
        if normalized in self.alias_to_key:
            key = self.alias_to_key[normalized]
            return self._build_result(key, 1.0, "exact_alias")
            
        if normalized in self.generic_to_key:
            key = self.generic_to_key[normalized]
            return self._build_result(key, 1.0, "exact_generic")
            
        if normalized in self.brand_to_key:
            key = self.brand_to_key[normalized]
            return self._build_result(key, 1.0, "exact_brand")
        
        # Strategy 2: Fuzzy match against aliases
        best_match = None
        best_score = 0.0
        
        for alias, key in self.alias_to_key.items():
            score = self.fuzzy_match(normalized, alias)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = key
                
        if best_match:
            return self._build_result(best_match, best_score, "fuzzy_alias")
            
        # Strategy 3: Fuzzy match against common misspellings
        for key, med_data in self.medication_db.items():
            for misspelling in med_data.get("common_misspellings", []):
                score = self.fuzzy_match(normalized, misspelling)
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = key
                    
        if best_match:
            return self._build_result(best_match, best_score, "fuzzy_misspelling")
            
        # Strategy 4: Fuzzy match against all medication keys
        for key in self.medication_db.keys():
            score = self.fuzzy_match(normalized, key)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = key
                
        if best_match:
            return self._build_result(best_match, best_score, "fuzzy_key")
            
        return None
        
    def _build_result(self, key: str, confidence: float, match_type: str) -> dict:
        """Build result dictionary with medication data"""
        med_data = self.medication_db[key]
        return {
            "key": key,
            "generic": med_data["generic"],
            "brand": med_data["brand"],
            "drug_class": med_data["drug_class"],
            "confidence": confidence,
            "match_type": match_type,
            "all_aliases": med_data["aliases"]
        }
        
    def get_drug_class(self, medication_name: str) -> Optional[str]:
        """Get drug class for a medication name"""
        result = self.find_medication(medication_name)
        return result["drug_class"] if result else None
        
    def search_multiple(self, medication_list: List[str], threshold: float = 0.85) -> List[dict]:
        """Search for multiple medications and return results"""
        results = []
        for med in medication_list:
            match = self.find_medication(med, threshold)
            if match:
                results.append(match)
        return results


def test_medication_matcher():
    """Test the medication matcher with various inputs"""
    matcher = MedicationMatcher()
    
    print("\n" + "="*80)
    print("MEDICATION MATCHER TESTING")
    print("="*80 + "\n")
    
    test_cases = [
        # Exact matches
        ("Aimovig", "Should match exactly"),
        ("erenumab", "Should match generic"),
        ("Topamax", "Should match brand"),
        
        # Common misspellings
        ("topimax", "Common misspelling of Topamax"),
        ("propanolol", "Common misspelling of propranolol"),
        ("imitrix", "Common misspelling of Imitrex"),
        
        # With dosage info
        ("Aimovig 70mg", "With dosage"),
        ("topiramate 100mg daily", "With dosage and frequency"),
        ("Nurtec ODT 75mg", "Brand with strength"),
        
        # Generic variations
        ("rimegepant", "Generic for Nurtec"),
        ("ubrogepant", "Generic for Ubrelvy"),
        ("galcanezumab", "Generic for Emgality"),
        
        # Edge cases
        ("botox", "All lowercase"),
        ("AIMOVIG", "All uppercase"),
        ("sumatriptan (Imitrex)", "With parenthetical"),
        
        # Should fail
        ("aspirin", "Not in database"),
        ("tylenol", "Not in database"),
    ]
    
    for input_text, description in test_cases:
        result = matcher.find_medication(input_text)
        
        print(f"Input: '{input_text}'")
        print(f"Description: {description}")
        
        if result:
            print(f"✓ MATCH FOUND")
            print(f"  Generic: {result['generic']}")
            print(f"  Brand: {result['brand']}")
            print(f"  Drug Class: {result['drug_class']}")
            print(f"  Confidence: {result['confidence']:.2%}")
            print(f"  Match Type: {result['match_type']}")
        else:
            print(f"✗ NO MATCH")
            
        print("-" * 80)
        
    # Test multiple medication search
    print("\n" + "="*80)
    print("TESTING MULTIPLE MEDICATION SEARCH")
    print("="*80 + "\n")
    
    failed_meds = ["propanolol", "topimax", "amitriptyline"]
    print(f"Input list: {failed_meds}")
    print()
    
    results = matcher.search_multiple(failed_meds)
    print(f"Found {len(results)} matches:")
    for r in results:
        print(f"  • {r['brand']} ({r['generic']}) - {r['drug_class']} - {r['confidence']:.0%} match")
        
    # Show what drug classes were identified
    drug_classes = set([r['drug_class'] for r in results])
    print(f"\nDrug classes identified: {', '.join(drug_classes)}")


if __name__ == "__main__":
    test_medication_matcher()
