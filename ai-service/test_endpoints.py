#!/usr/bin/env python3
"""
Test script for AI Service endpoints
Verifies the improved interview question generation, response evaluation, and SWOT analysis
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
AI_SERVICE_URL = "http://localhost:8001"  # Change if running on different host

def test_health_check():
    """Test basic health endpoints"""
    print("\n" + "="*60)
    print("TEST 1: Health Check Endpoints")
    print("="*60)
    
    endpoints = ["/healthz", "/ping", "/ollama/status"]
    
    for endpoint in endpoints:
        try:
            resp = requests.get(f"{AI_SERVICE_URL}{endpoint}", timeout=5)
            print(f"✅ {endpoint}: {resp.status_code}")
            print(f"   Response: {resp.json()}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")


def test_generate_interview():
    """Test interview generation with strict validation"""
    print("\n" + "="*60)
    print("TEST 2: Generate Interview Questions")
    print("="*60)
    
    payload = {
        "vacancy_title": "Backend Engineer (Node.js)",
        "requirements": [
            "Node.js y Express.js",
            "PostgreSQL y SQL",
            "REST APIs",
            "Git y versionamiento"
        ],
        "level": "intermedio",
        "n_questions": 4,
        "model": "llama3.2"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        resp = requests.post(
            f"{AI_SERVICE_URL}/generate_interview",
            json=payload,
            timeout=120
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n✅ Status: {resp.status_code}")
            
            if data.get("ok"):
                interview = data.get("interview", {})
                questions = interview.get("questions", [])
                
                print(f"\n📋 Interview Generated:")
                print(f"   Vacancy: {interview.get('vacancy')}")
                print(f"   Level: {interview.get('level')}")
                print(f"   Number of questions: {len(questions)}")
                
                # Validate questions
                total_weight = 0
                for i, q in enumerate(questions, 1):
                    weight = q.get("weight", 0)
                    total_weight += weight
                    print(f"\n   Q{i}: {q.get('question')[:60]}...")
                    print(f"       Type: {q.get('type')}")
                    print(f"       Weight: {weight}%")
                    print(f"       Keywords: {', '.join(q.get('expected_keywords', [])[:2])}")
                
                print(f"\n   Total Weight: {total_weight}%")
                print(f"   {'✅ Valid (100±5%)' if abs(total_weight - 100) <= 5 else '❌ Invalid weight'}")
                
                return interview
            else:
                print(f"❌ Response OK but validation failed: {data.get('validation')}")
        else:
            print(f"❌ Status: {resp.status_code}")
            print(f"   Error: {resp.text}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return None


def test_evaluate_response(interview: Dict[str, Any]):
    """Test response evaluation"""
    print("\n" + "="*60)
    print("TEST 3: Evaluate Candidate Response")
    print("="*60)
    
    if not interview or not interview.get("questions"):
        print("❌ No interview data available")
        return None
    
    question = interview["questions"][0]
    
    payload = {
        "question": question,
        "candidate_response": """He trabajado con Node.js durante 4 años en diferentes proyectos. 
He usado Express.js para crear APIs RESTful escalables, siempre
considerando async/await y el event loop. También he trabajado 
con PostgreSQL optimizando queries y usando ORMs como Sequelize. 
Estoy familiarizado con Git y versionamiento de código.""",
        "model": "llama3.2"
    }
    
    print(f"Question: {question.get('question')}")
    print(f"Candidate response: {payload['candidate_response'][:100]}...")
    
    try:
        resp = requests.post(
            f"{AI_SERVICE_URL}/evaluate_response",
            json=payload,
            timeout=120
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n✅ Status: {resp.status_code}")
            
            if data.get("ok"):
                evaluation = data.get("evaluation", {})
                
                print(f"\n📊 Response Evaluation:")
                print(f"   Overall Score: {evaluation.get('overall_score')}/100")
                print(f"   Relevance: {evaluation.get('relevance_score')}/100")
                print(f"   Completeness: {evaluation.get('completeness_score')}/100")
                print(f"   Clarity: {evaluation.get('clarity_score')}/100")
                print(f"   Depth: {evaluation.get('depth_score')}/100")
                print(f"\n   Keywords Found: {', '.join(evaluation.get('keywords_found', []))}")
                print(f"   Keywords Missing: {', '.join(evaluation.get('keywords_missing', []))}")
                print(f"\n   Strengths: {', '.join(evaluation.get('strengths', []))}")
                print(f"   Weaknesses: {', '.join(evaluation.get('weaknesses', []))}")
                print(f"\n   Feedback: {evaluation.get('feedback')}")
                
                return evaluation
            else:
                print(f"❌ Evaluation failed")
        else:
            print(f"❌ Status: {resp.status_code}")
            print(f"   Error: {resp.text}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return None


def test_generate_swot_analysis(interview: Dict[str, Any], evaluations: list):
    """Test SWOT analysis generation"""
    print("\n" + "="*60)
    print("TEST 4: Generate SWOT Analysis")
    print("="*60)
    
    # Create mock evaluations for all questions
    candidate_responses = []
    for i, question in enumerate(interview.get("questions", []), 1):
        candidate_responses.append({
            "question_id": question.get("id", f"Q{i}"),
            "overall_score": 70 + (i * 5),  # Incrementing scores
            "feedback": f"Buena respuesta para pregunta {i}",
            "strengths": ["Conocimiento técnico", "Claridad"],
            "weaknesses": ["Falta de ejemplos", "Poco detalle"]
        })
    
    payload = {
        "vacancy_title": interview.get("vacancy", "Backend Engineer"),
        "level": interview.get("level", "intermedio"),
        "interview_data": interview,
        "candidate_responses": candidate_responses,
        "model": "llama3.2"
    }
    
    print(f"SWOT Analysis for: {payload['vacancy_title']}")
    print(f"Candidate Scores: {[r['overall_score'] for r in candidate_responses]}")
    
    try:
        resp = requests.post(
            f"{AI_SERVICE_URL}/generate_swot_analysis",
            json=payload,
            timeout=120
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n✅ Status: {resp.status_code}")
            
            if data.get("ok"):
                analysis = data.get("analysis", {})
                swot = analysis.get("swot", {})
                
                print(f"\n📈 SWOT Analysis:")
                print(f"   Overall Score: {analysis.get('overall_score')}/100")
                print(f"   Candidate Level: {analysis.get('candidate_level')}")
                print(f"   Recommendation: {analysis.get('recommendation')}")
                
                print(f"\n   ✅ STRENGTHS ({len(swot.get('strengths', []))})")
                for s in swot.get('strengths', []):
                    print(f"      - {s.get('title')}: {s.get('description')[:50]}...")
                
                print(f"\n   ❌ WEAKNESSES ({len(swot.get('weaknesses', []))})")
                for w in swot.get('weaknesses', []):
                    print(f"      - {w.get('title')}: {w.get('description')[:50]}...")
                
                print(f"\n   📈 OPPORTUNITIES ({len(swot.get('opportunities', []))})")
                for o in swot.get('opportunities', []):
                    print(f"      - {o[:50]}...")
                
                print(f"\n   ⚠️ THREATS ({len(swot.get('threats', []))})")
                for t in swot.get('threats', []):
                    print(f"      - {t[:50]}...")
                
                print(f"\n   Rationale: {analysis.get('rationale')}")
                print(f"   Next Steps: {analysis.get('next_steps')}")
            else:
                print(f"❌ Analysis generation failed")
        else:
            print(f"❌ Status: {resp.status_code}")
            print(f"   Error: {resp.text}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")


def main():
    """Run all tests"""
    print("\n" + "🚀 "*30)
    print("AI SERVICE - COMPREHENSIVE TEST SUITE")
    print("🚀 "*30)
    
    # Test 1: Health checks
    test_health_check()
    
    # Test 2: Generate interview
    interview = test_generate_interview()
    
    if not interview:
        print("\n⚠️ Cannot proceed with further tests without interview data")
        return
    
    # Wait a bit to avoid overwhelming Ollama
    time.sleep(2)
    
    # Test 3: Evaluate response
    evaluation = test_evaluate_response(interview)
    
    # Wait before next test
    time.sleep(2)
    
    # Test 4: Generate SWOT
    if evaluation:
        test_generate_swot_analysis(interview, [evaluation])
    
    print("\n" + "="*60)
    print("✅ TEST SUITE COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
