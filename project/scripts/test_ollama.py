#!/usr/bin/env python3
"""
Basic Ollama API Test Script
Tests Ollama installation and model inference functionality.
"""

import requests
import json
import time
from typing import Dict, Any


def test_ollama_api(model: str = "llama3.2") -> Dict[str, Any]:
    """
    Test Ollama API endpoint and model inference.
    
    Args:
        model: Model name to test (default: llama3.2)
        
    Returns:
        Dictionary with test results
    """
    base_url = "http://localhost:11434"
    
    results = {
        "api_endpoint": f"{base_url}/api/generate",
        "model": model,
        "tests": {}
    }
    
    # Test 1: API endpoint accessibility
    print(f"Testing API endpoint: {base_url}/api/tags")
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        results["tests"]["api_accessibility"] = {
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code
        }
        print(f"  Status: {results['tests']['api_accessibility']['status']}")
    except Exception as e:
        results["tests"]["api_accessibility"] = {
            "status": "FAIL",
            "error": str(e)
        }
        print(f"  Status: FAIL - {e}")
    
    # Test 2: Model inference
    print(f"\nTesting model inference with {model}...")
    test_prompt = "What is 2+2? Answer in one sentence."
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": test_prompt,
                "stream": False
            },
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            results["tests"]["model_inference"] = {
                "status": "PASS",
                "response_time": f"{elapsed_time:.2f}s",
                "response_length": len(data.get("response", "")),
                "response_preview": data.get("response", "")[:100] + "..."
            }
            print(f"  Status: PASS")
            print(f"  Response time: {elapsed_time:.2f}s")
            print(f"  Response preview: {results['tests']['model_inference']['response_preview']}")
        else:
            results["tests"]["model_inference"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "error": response.text
            }
            print(f"  Status: FAIL - Status code: {response.status_code}")
    except Exception as e:
        results["tests"]["model_inference"] = {
            "status": "FAIL",
            "error": str(e)
        }
        print(f"  Status: FAIL - {e}")
    
    # Overall result
    all_passed = all(
        test.get("status") == "PASS" 
        for test in results["tests"].values()
    )
    results["overall_status"] = "PASS" if all_passed else "FAIL"
    
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Ollama Installation and API Test")
    print("=" * 60)
    print()
    
    results = test_ollama_api()
    
    print()
    print("=" * 60)
    print(f"Overall Status: {results['overall_status']}")
    print("=" * 60)
    
    # Exit with appropriate code
    exit(0 if results["overall_status"] == "PASS" else 1)

