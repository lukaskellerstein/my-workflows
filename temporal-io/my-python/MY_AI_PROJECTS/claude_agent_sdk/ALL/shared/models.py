"""Shared data models across all projects."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Project 1: Content Publishing Pipeline Models
# ============================================================================


class ContentFormat(str, Enum):
    """Supported content formats."""

    MARKDOWN = "markdown"
    HTML = "html"


class ValidationStatus(str, Enum):
    """Content validation status."""

    VALID = "valid"
    INVALID = "invalid"


class ArticleInput(BaseModel):
    """Input article for publishing pipeline."""

    title: str
    content: str
    format: ContentFormat
    author: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of content validation."""

    status: ValidationStatus
    errors: List[str] = Field(default_factory=list)
    word_count: int


class ContentAnalysis(BaseModel):
    """LLM-powered content analysis."""

    tone: str
    readability_score: float
    key_topics: List[str]
    summary: str
    sensitive_topics: List[str] = Field(default_factory=list)


class SEOOptimization(BaseModel):
    """SEO optimization suggestions."""

    title_alternatives: List[str]
    meta_description: str
    keywords: List[str]
    internal_linking_suggestions: List[str] = Field(default_factory=list)


class PublishedArticle(BaseModel):
    """Final published article."""

    article_id: str
    publication_url: str
    published_at: datetime
    metadata: Dict[str, Any]


# ============================================================================
# Project 3: Code Review Models
# ============================================================================


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


# ============================================================================
# Project 4: Product Launch Models
# ============================================================================


class LaunchPhase(str, Enum):
    """Product launch phases."""

    PLANNING = "planning"
    RESEARCH = "research"
    CONTENT_CREATION = "content_creation"
    DEPLOYMENT = "deployment"
    LAUNCH = "launch"
    MONITORING = "monitoring"
    POST_LAUNCH = "post_launch"


class ProductSpecification(BaseModel):
    """Product specification for launch."""

    product_id: str
    name: str
    description: str
    target_audience: List[str]
    key_features: List[str]
    launch_date: datetime
    budget: float


class MarketResearch(BaseModel):
    """Market research findings."""

    competitor_analysis: List[Dict[str, Any]]
    market_gaps: List[str]
    customer_sentiment: Dict[str, Any]
    opportunities: List[str]


class MarketingContent(BaseModel):
    """Generated marketing content."""

    product_descriptions: Dict[str, str]  # audience -> description
    marketing_copy: List[str]
    technical_documentation: str
    faq_content: List[Dict[str, str]]


class DeploymentConfig(BaseModel):
    """Technical deployment configuration."""

    deployment_scripts: List[str]
    monitoring_config: Dict[str, Any]
    ab_testing_params: Dict[str, Any]
    production_ready: bool


class LaunchMetrics(BaseModel):
    """Launch monitoring metrics."""

    timestamp: datetime
    active_users: int
    conversion_rate: float
    error_rate: float
    customer_feedback_score: float
    anomalies: List[str] = Field(default_factory=list)


class LaunchReport(BaseModel):
    """Post-launch analysis report."""

    product_id: str
    launch_success: bool
    key_metrics: Dict[str, float]
    customer_feedback_summary: str
    improvement_suggestions: List[str]
    lessons_learned: List[str]
