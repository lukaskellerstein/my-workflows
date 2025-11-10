"""Code Review Models for Project 3."""

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ProgrammingLanguage(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"


class ReviewSeverity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CodeSubmission(BaseModel):
    """Code submission for review."""

    submission_id: str
    code: str
    language: ProgrammingLanguage
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityFinding(BaseModel):
    """Security vulnerability finding."""

    severity: ReviewSeverity
    category: str
    description: str
    location: str
    recommendation: str


class PerformanceAnalysis(BaseModel):
    """Performance analysis results."""

    complexity_analysis: Dict[str, str]
    bottlenecks: List[str]
    optimization_suggestions: List[str]
    benchmark_results: Dict[str, float] = Field(default_factory=dict)


class StyleIssue(BaseModel):
    """Code style issue."""

    severity: ReviewSeverity
    description: str
    location: str
    suggestion: str


class TestSuite(BaseModel):
    """Generated test suite."""

    unit_tests: List[str]
    integration_tests: List[str]
    coverage_percentage: float


class CodeReviewReport(BaseModel):
    """Comprehensive code review report."""

    submission_id: str
    security_findings: List[SecurityFinding]
    performance_analysis: PerformanceAnalysis
    style_issues: List[StyleIssue]
    test_results: TestSuite
    overall_score: float
    recommendations: List[str]
