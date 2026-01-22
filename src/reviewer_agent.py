"""Reviewer Agent - Analyzes diffs and provides approval/rejection decisions."""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ReviewDecision(Enum):
    """Review decision types."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


@dataclass
class ReviewFeedback:
    """Feedback for a review decision."""
    message: str
    severity: str  # "info", "warning", "error"
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class ReviewResult:
    """Result of a code review."""
    decision: ReviewDecision
    feedback: List[ReviewFeedback]
    confidence_score: float  # 0.0 to 1.0
    metadata: Dict[str, Any]


class ReviewerAgent:
    """Agent that reviews code changes and makes approval/rejection decisions."""
    
    def __init__(self):
        """Initialize the reviewer agent."""
        self.approval_patterns = [
            r"test\s*:\s*add",  # Adding tests
            r"fix\s*:\s*",      # Bug fixes
            r"docs?\s*:\s*",    # Documentation
            r"refactor\s*:\s*",  # Refactoring
        ]
        
        self.rejection_patterns = [
            r"TODO|FIXME|XXX",  # Incomplete work
            r"print\s*\(\s*['\"]DEBUG",  # Debug print statements
            r"debugger",        # Debug statements
            r"password|secret", # Potential secrets
            r"import.*os",     # Potentially dangerous imports
        ]
        
        self.warning_patterns = [
            r"except\s*:",      # Bare except
            r"global\s+",       # Global variables
            r"eval\s*\(",       # Eval usage
            r"exec\s*\(",       # Exec usage
        ]
    
    def analyze_diff(self, diff_text: str) -> ReviewResult:
        """Analyze a git diff and provide review decision.
        
        Args:
            diff_text: Git diff output
            
        Returns:
            ReviewResult with decision and feedback
        """
        feedback = []
        confidence_score = 0.8  # Base confidence
        
        # Parse diff into file changes
        file_changes = self._parse_diff(diff_text)
        
        for file_path, changes in file_changes.items():
            file_feedback = self._analyze_file_changes(file_path, changes)
            feedback.extend(file_feedback)
        
        # Make decision based on feedback
        decision, confidence = self._make_decision(feedback)
        
        # Add metadata
        metadata = {
            "files_reviewed": len(file_changes),
            "total_feedback": len(feedback),
            "file_paths": list(file_changes.keys())
        }
        
        return ReviewResult(
            decision=decision,
            feedback=feedback,
            confidence_score=confidence,
            metadata=metadata
        )
    
    def _parse_diff(self, diff_text: str) -> Dict[str, List[str]]:
        """Parse git diff into file changes.
        
        Args:
            diff_text: Git diff output
            
        Returns:
            Dictionary mapping file paths to lists of changed lines
        """
        file_changes = {}
        current_file = None
        current_changes = []
        
        for line in diff_text.split('\n'):
            if line.startswith('diff --git'):
                # Save previous file changes
                if current_file:
                    file_changes[current_file] = current_changes
                
                # Start new file
                current_file = line.split(' b/')[1].strip()
                current_changes = []
                
            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                current_changes.append(line[1:])  # Remove '+' prefix
            elif line.startswith('-') and not line.startswith('---'):
                # Removed line
                current_changes.append(f"REMOVED:{line[1:]}")
        
        # Save last file
        if current_file:
            file_changes[current_file] = current_changes
            
        return file_changes
    
    def _analyze_file_changes(self, file_path: str, changes: List[str]) -> List[ReviewFeedback]:
        """Analyze changes for a single file.
        
        Args:
            file_path: Path to the file being changed
            changes: List of changed lines
            
        Returns:
            List of ReviewFeedback items
        """
        feedback = []
        
        # Check file extension for context
        file_ext = file_path.split('.')[-1] if '.' in file_path else ''
        
        for i, change in enumerate(changes):
            # Check for problematic patterns
            for pattern in self.rejection_patterns:
                if re.search(pattern, change, re.IGNORECASE):
                    feedback.append(ReviewFeedback(
                        message=f"Potentially problematic pattern found: {pattern}",
                        severity="error",
                        file_path=file_path,
                        line_number=i + 1
                    ))
            
            # Check for warning patterns
            for pattern in self.warning_patterns:
                if re.search(pattern, change, re.IGNORECASE):
                    feedback.append(ReviewFeedback(
                        message=f"Warning: {pattern} detected",
                        severity="warning",
                        file_path=file_path,
                        line_number=i + 1
                    ))
            
            # Language-specific checks
            if file_ext in ['py', 'python']:
                feedback.extend(self._check_python_code(change, file_path, i + 1))
            elif file_ext in ['js', 'ts', 'javascript', 'typescript']:
                feedback.extend(self._check_javascript_code(change, file_path, i + 1))
        
        # Check for test additions
        if 'test' in file_path.lower() and any('def test_' in change for change in changes):
            feedback.append(ReviewFeedback(
                message="Test code detected - this is generally positive",
                severity="info",
                file_path=file_path
            ))
        
        return feedback
    
    def _check_python_code(self, code: str, file_path: str, line_number: int) -> List[ReviewFeedback]:
        """Check Python-specific code issues.
        
        Args:
            code: Python code to check
            file_path: File path
            line_number: Line number
            
        Returns:
            List of ReviewFeedback items
        """
        feedback = []
        
        # Check for dangerous imports
        dangerous_imports = ['os', 'sys', 'subprocess', 'pickle']
        for imp in dangerous_imports:
            if f"import {imp}" in code:
                feedback.append(ReviewFeedback(
                    message=f"Potentially dangerous import: {imp}",
                    severity="warning",
                    file_path=file_path,
                    line_number=line_number
                ))
        
        # Check for bare except
        if "except:" in code:
            feedback.append(ReviewFeedback(
                message="Bare except clause - should specify exception type",
                severity="warning",
                file_path=file_path,
                line_number=line_number
            ))
        
        return feedback
    
    def _check_javascript_code(self, code: str, file_path: str, line_number: int) -> List[ReviewFeedback]:
        """Check JavaScript-specific code issues.
        
        Args:
            code: JavaScript code to check
            file_path: File path
            line_number: Line number
            
        Returns:
            List of ReviewFeedback items
        """
        feedback = []
        
        # Check for eval usage
        if "eval(" in code:
            feedback.append(ReviewFeedback(
                message="eval() usage detected - security concern",
                severity="error",
                file_path=file_path,
                line_number=line_number
            ))
        
        # Check for innerHTML
        if "innerHTML" in code:
            feedback.append(ReviewFeedback(
                message="innerHTML usage - potential XSS vulnerability",
                severity="warning",
                file_path=file_path,
                line_number=line_number
            ))
        
        return feedback
    
    def _make_decision(self, feedback: List[ReviewFeedback]) -> Tuple[ReviewDecision, float]:
        """Make approval/rejection decision based on feedback.
        
        Args:
            feedback: List of feedback items
            
        Returns:
            Tuple of (decision, confidence_score)
        """
        if not feedback:
            return ReviewDecision.APPROVE, 0.9
        
        # Count feedback by severity
        error_count = sum(1 for f in feedback if f.severity == "error")
        warning_count = sum(1 for f in feedback if f.severity == "warning")
        info_count = sum(1 for f in feedback if f.severity == "info")
        
        # Decision logic
        if error_count > 0:
            return ReviewDecision.REJECT, 0.9
        elif warning_count > 3:
            return ReviewDecision.REQUEST_CHANGES, 0.8
        elif warning_count > 0:
            return ReviewDecision.REQUEST_CHANGES, 0.7
        else:
            return ReviewDecision.APPROVE, 0.8
    
    def format_review_result(self, result: ReviewResult) -> str:
        """Format review result for display.
        
        Args:
            result: ReviewResult to format
            
        Returns:
            Formatted string representation
        """
        output = []
        output.append(f"Review Decision: {result.decision.value.upper()}")
        output.append(f"Confidence Score: {result.confidence_score:.2f}")
        output.append("")
        
        if result.feedback:
            output.append("Feedback:")
            for feedback in result.feedback:
                severity_icon = {
                    "error": "❌",
                    "warning": "⚠️", 
                    "info": "ℹ️"
                }.get(feedback.severity, "•")
                
                location = f" ({feedback.file_path}:{feedback.line_number})" if feedback.file_path else ""
                output.append(f"  {severity_icon} {feedback.severity.upper()}: {feedback.message}{location}")
        else:
            output.append("No feedback - changes look good!")
        
        output.append("")
        output.append(f"Files reviewed: {result.metadata.get('files_reviewed', 0)}")
        output.append(f"Total feedback items: {result.metadata.get('total_feedback', 0)}")
        
        return "\n".join(output)