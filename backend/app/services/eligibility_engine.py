"""
AidFlow AI - Eligibility Engine Service
Evaluates user profiles against scheme rules.
"""

from typing import List, Dict, Any

def evaluate_eligibility(user_profile: Dict[str, Any], scheme_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Evaluate a user profile against a list of scheme rules.
    Returns a list of results with match percentages and matched/failed rules.
    """
    results = []
    
    for rule_record in scheme_rules:
        scheme_id = rule_record.get("scheme_id")
        scheme_name = rule_record.get("schemes", {}).get("name", "Unknown")
        rule_def = rule_record.get("rule_definition", {})
        
        # If no rules defined, assume 100% match (or could assume 0, depends on policy)
        if not rule_def or "conditions" not in rule_def:
            results.append({
                "scheme_id": scheme_id,
                "scheme_name": scheme_name,
                "match_percentage": 100.0,
                "matched_rules": ["No specific rules defined"],
                "failed_rules": []
            })
            continue
            
        matched = []
        failed = []
        
        # Evaluate root rule definition
        _eval_node(rule_def, user_profile, matched, failed)
        
        total_conditions = len(matched) + len(failed)
        match_pct = (len(matched) / total_conditions * 100) if total_conditions > 0 else 0
        
        results.append({
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "match_percentage": round(match_pct, 1),
            "matched_rules": matched,
            "failed_rules": failed
        })
        
    # Sort by highest match percentage first
    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return results


def _eval_node(node: Dict[str, Any], profile: Dict[str, Any], matched: List[str], failed: List[str]) -> bool:
    """Recursively evaluate a rule node."""
    
    # Base condition node
    if "field" in node and "op" in node:
        field = node["field"]
        op = node["op"]
        target = node.get("value")
        
        # Get actual value from profile
        actual = profile.get(field)
        
        # Evaluation logic
        is_match = False
        desc = f"{field} {op} {target}"
        
        if actual is None:
            is_match = False
            desc += f" (Missing in profile)"
        else:
            try:
                if op == "eq":
                    is_match = str(actual).lower() == str(target).lower()
                elif op == "neq":
                    is_match = str(actual).lower() != str(target).lower()
                elif op in ["gt", "gte", "lt", "lte"]:
                    actual_num = float(actual)
                    target_num = float(target)
                    if op == "gt": is_match = actual_num > target_num
                    elif op == "gte": is_match = actual_num >= target_num
                    elif op == "lt": is_match = actual_num < target_num
                    elif op == "lte": is_match = actual_num <= target_num
                elif op == "in" and isinstance(target, list):
                    is_match = actual in target
                elif op == "contains" and isinstance(actual, list):
                    is_match = target in actual
            except (ValueError, TypeError):
                is_match = False
                desc += " (Type mismatch)"
                
        if is_match:
            matched.append(desc)
        else:
            failed.append(desc)
            
        return is_match
        
    # Logical operator node (and/or)
    if "operator" in node and "conditions" in node:
        op = node["operator"].lower()
        conditions = node["conditions"]
        
        if op == "and":
            # For 'and', we evaluate all to populate matched/failed lists properly
            results = [_eval_node(c, profile, matched, failed) for c in conditions]
            return all(results)
            
        elif op == "or":
            # For 'or', if any is true, we consider it a success.
            # However, to avoid spamming failed list for OR branches that naturally fail,
            # we isolate their matched/failed tracking.
            sub_matched = []
            sub_failed = []
            results = []
            
            for c in conditions:
                temp_matched = []
                temp_failed = []
                res = _eval_node(c, profile, temp_matched, temp_failed)
                results.append(res)
                if res:
                    sub_matched.extend(temp_matched)
                else:
                    sub_failed.extend(temp_failed)
                    
            is_any_true = any(results)
            if is_any_true:
                matched.extend(sub_matched)
            else:
                failed.extend(sub_failed)
                
            return is_any_true
            
    return False
