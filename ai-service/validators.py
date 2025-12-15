"""
Advanced validation utilities for AI service responses
Optimized for llama3.2 output handling
"""

import json
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def validate_interview_questions(data: Dict[str, Any], n_expected: int) -> Tuple[bool, str]:
    """
    Validate interview questions structure and content.
    
    Returns: (is_valid, error_message)
    """
    try:
        # Check required fields
        if not data.get("vacancy"):
            return False, "Missing 'vacancy' field"
        
        if not data.get("level"):
            return False, "Missing 'level' field"
        
        questions = data.get("questions")
        if not isinstance(questions, list):
            return False, "'questions' must be a list"
        
        if len(questions) < n_expected:
            return False, f"Expected {n_expected} questions, got {len(questions)}"
        
        total_weight = 0
        question_types = {"technical", "behavioral", "situational"}
        
        for i, q in enumerate(questions, 1):
            if not isinstance(q, dict):
                return False, f"Question {i} must be a dict"
            
            # Check required fields
            if not q.get("id"):
                return False, f"Question {i} missing 'id'"
            
            if not q.get("question"):
                return False, f"Question {i} missing 'question'"
            
            q_type = q.get("type", "").lower()
            if q_type not in question_types:
                return False, f"Question {i} has invalid type: {q_type}"
            
            keywords = q.get("expected_keywords", [])
            if not isinstance(keywords, list) or len(keywords) == 0:
                return False, f"Question {i} must have 'expected_keywords' list"
            
            if not q.get("rubric"):
                return False, f"Question {i} missing 'rubric'"
            
            weight = q.get("weight", 0)
            if not isinstance(weight, (int, float)) or weight <= 0 or weight > 100:
                return False, f"Question {i} has invalid weight: {weight}"
            
            total_weight += weight
        
        # Validate total weight (allow 5% tolerance for rounding)
        if abs(total_weight - 100) > 5:
            return False, f"Total weight must be ~100, got {total_weight}"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def validate_response_evaluation(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate response evaluation structure.
    
    Returns: (is_valid, error_message)
    """
    try:
        required_fields = {
            "question_id": str,
            "overall_score": (int, float),
            "relevance_score": (int, float),
            "completeness_score": (int, float),
            "clarity_score": (int, float),
            "depth_score": (int, float),
            "keywords_found": list,
            "strengths": list,
            "weaknesses": list,
            "feedback": str,
        }
        
        for field, expected_type in required_fields.items():
            if field not in data:
                return False, f"Missing required field: {field}"
            
            value = data[field]
            if not isinstance(value, expected_type):
                return False, f"Field '{field}' must be {expected_type}, got {type(value)}"
        
        # Validate scores are 0-100
        score_fields = [
            "overall_score", "relevance_score", "completeness_score",
            "clarity_score", "depth_score"
        ]
        
        for field in score_fields:
            score = data[field]
            if not (0 <= score <= 100):
                return False, f"Score '{field}' must be 0-100, got {score}"
        
        # Verify overall_score is approximately average of other scores
        other_scores = [
            data["relevance_score"],
            data["completeness_score"],
            data["clarity_score"],
            data["depth_score"]
        ]
        expected_overall = sum(other_scores) / len(other_scores)
        
        if abs(data["overall_score"] - expected_overall) > 10:
            logger.warning(
                f"overall_score {data['overall_score']} deviates from average {expected_overall}"
            )
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def validate_swot_analysis(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate SWOT analysis structure.
    
    Returns: (is_valid, error_message)
    """
    try:
        # Check basic fields
        if not data.get("vacancy"):
            return False, "Missing 'vacancy'"
        
        if not data.get("level"):
            return False, "Missing 'level'"
        
        if "swot" not in data:
            return False, "Missing 'swot' section"
        
        swot = data["swot"]
        if not isinstance(swot, dict):
            return False, "'swot' must be a dict"
        
        # Check SWOT sections
        required_sections = ["strengths", "weaknesses", "opportunities", "threats"]
        for section in required_sections:
            if section not in swot:
                return False, f"Missing '{section}' in SWOT"
            
            section_data = swot[section]
            if not isinstance(section_data, list):
                return False, f"'{section}' must be a list"
            
            # For strengths and weaknesses, check structure
            if section in ["strengths", "weaknesses"]:
                for i, item in enumerate(section_data, 1):
                    if not isinstance(item, dict):
                        return False, f"{section}[{i}] must be a dict"
                    
                    if "title" not in item or "description" not in item:
                        return False, f"{section}[{i}] missing 'title' or 'description'"
        
        # Check overall_score
        overall_score = data.get("overall_score")
        if overall_score is not None:
            if not isinstance(overall_score, (int, float)) or not (0 <= overall_score <= 100):
                return False, f"Invalid overall_score: {overall_score}"
        
        # Check recommendation
        if "recommendation" in data:
            rec = data["recommendation"]
            if rec not in ["HIRE", "INTERVIEW_AGAIN", "REJECT"]:
                return False, f"Invalid recommendation: {rec}"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def extract_json_from_text(text: str) -> Tuple[bool, Any]:
    """
    Extract and parse JSON from text, handling common llama3.2 issues.
    
    Returns: (success, parsed_data)
    """
    try:
        # Try direct parsing first
        return True, json.loads(text)
    except:
        pass
    
    # Try to extract JSON from text
    start = text.find("{")
    end = text.rfind("}") + 1
    
    if start >= 0 and end > start:
        try:
            json_str = text[start:end]
            return True, json.loads(json_str)
        except:
            pass
    
    # Try to find JSON array
    start = text.find("[")
    end = text.rfind("]") + 1
    
    if start >= 0 and end > start:
        try:
            json_str = text[start:end]
            return True, json.loads(json_str)
        except:
            pass
    
    return False, None


def sanitize_json_score(data: Dict[str, Any], fields: List[str], min_val: int = 0, max_val: int = 100) -> Dict[str, Any]:
    """
    Ensure all score fields are valid integers within range.
    """
    for field in fields:
        if field in data:
            try:
                value = data[field]
                if isinstance(value, (int, float)):
                    data[field] = max(min_val, min(max_val, int(value)))
                else:
                    data[field] = 50  # Default middle value
            except:
                data[field] = 50
    
    return data
