"""Tests for ReviewerAgent."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, 'src')

from reviewer_agent import ReviewerAgent, ReviewDecision, ReviewFeedback


def test_basic_diff_analysis():
    """Test basic diff analysis functionality."""
    agent = ReviewerAgent()
    
    # Simple test diff
    diff_text = """diff --git a/test.py b/test.py
index 1234567..89abcdef 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("old")
+    print("new")
     return "world"
"""
    
    result = agent.analyze_diff(diff_text)
    
    assert result.decision == ReviewDecision.APPROVE
    assert result.confidence_score > 0.5
    assert len(result.feedback) == 0
    
    print("✓ Basic diff analysis test passed")


def test_problematic_patterns():
    """Test detection of problematic patterns."""
    agent = ReviewerAgent()
    
    # Diff with problematic patterns
    diff_text = """diff --git a/bad.py b/bad.py
index 1234567..89abcdef 100644
--- a/bad.py
+++ b/bad.py
@@ -1,3 +1,4 @@
 def bad_func():
-    return "ok"
+    print("DEBUG: here")
+    TODO: fix this
+    import os
     return "bad"
"""
    
    result = agent.analyze_diff(diff_text)
    
    # Should be rejected due to problematic patterns
    assert result.decision == ReviewDecision.REJECT
    assert len(result.feedback) > 0
    
    # Check that specific patterns were detected
    feedback_messages = [f.message for f in result.feedback]
    assert any("TODO" in msg for msg in feedback_messages)
    assert any("print" in msg for msg in feedback_messages)
    
    print("✓ Problematic patterns test passed")


def test_python_specific_checks():
    """Test Python-specific code checks."""
    agent = ReviewerAgent()
    
    # Diff with Python issues
    diff_text = """diff --git a/python_issues.py b/python_issues.py
index 1234567..89abcdef 100644
--- a/python_issues.py
+++ b/python_issues.py
@@ -1,3 +1,4 @@
 def risky():
-    return safe()
+    import os
+    try:
+        pass
+    except:
+        return dangerous()
"""
    
    result = agent.analyze_diff(diff_text)
    
    # Should detect Python issues
    assert len(result.feedback) > 0
    
    # Check for Python-specific issues
    feedback_messages = [f.message for f in result.feedback]
    assert any("os" in msg for msg in feedback_messages)
    assert any("except" in msg for msg in feedback_messages)
    
    print("✓ Python-specific checks test passed")


def test_format_review_result():
    """Test formatting of review results."""
    agent = ReviewerAgent()
    
    # Create a sample result
    from reviewer_agent import ReviewResult
    result = ReviewResult(
        decision=ReviewDecision.APPROVE,
        feedback=[
            ReviewFeedback("Test feedback", "info", "test.py", 1)
        ],
        confidence_score=0.9,
        metadata={"files_reviewed": 1, "total_feedback": 1}
    )
    
    formatted = agent.format_review_result(result)
    
    assert "APPROVE" in formatted
    assert "0.90" in formatted
    assert "Test feedback" in formatted
    assert "test.py:1" in formatted
    
    print("✓ Format review result test passed")


def run_all_tests():
    """Run all tests."""
    print("Running ReviewerAgent tests...")
    print("=" * 40)
    
    test_basic_diff_analysis()
    test_problematic_patterns()
    test_python_specific_checks()
    test_format_review_result()
    
    print("=" * 40)
    print("All tests passed! ✅")


if __name__ == "__main__":
    run_all_tests()