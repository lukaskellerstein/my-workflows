"""Report Generator Agent - Generates comprehensive review reports with historical context."""

import logging
from datetime import datetime
from typing import Dict

from shared.sdk_wrapper import Agent
from models import CodeSubmission

logger = logging.getLogger(__name__)


class ReportGeneratorAgent:
    """Agent specialized in generating comprehensive code review reports with Mem0 historical context."""

    def __init__(self):
        self.logger = logging.getLogger("agent.report_generator")

    async def generate_report(
        self, submission: CodeSubmission, review_report: Dict, test_results: Dict
    ) -> Dict:
        """
        Generate comprehensive review report with LLM and historical context.

        Args:
            submission: Code submission details
            review_report: Review findings from multi-agent team
            test_results: Test execution results

        Returns:
            Dict with comprehensive final report including LLM analysis
        """
        self.logger.info(f"Generating report with LLM and Mem0 for: {submission.submission_id}")

        # Create agent with Mem0 for historical context
        async with Agent(
            name="report-generator",
            description="Code review report generator with memory of past reviews",
            system_prompt="""You are an expert code review report generator with access to memory of past reviews.
Analyze the provided review data and test results to create a comprehensive, actionable report.
Use past review patterns to provide better context and recommendations.
Focus on actionable insights and prioritize critical issues.""",
            mcp_servers=["openmemory"],  # Mem0 for historical context
        ) as agent:

            # Prepare comprehensive review data
            task = self._build_review_task(submission, review_report, test_results)

            try:
                # Get LLM-generated analysis with historical context
                llm_response = await agent.query(task)

                return self._build_final_report(
                    submission, review_report, test_results, llm_response
                )

            except Exception as e:
                self.logger.error(f"Error generating report with LLM: {e}")
                return self._build_fallback_report(
                    submission, review_report, test_results, e
                )

    def _build_review_task(
        self, submission: CodeSubmission, review_report: Dict, test_results: Dict
    ) -> str:
        """Build the task prompt for the LLM."""
        return f"""Generate a comprehensive code review report for the following submission:

**Submission Details:**
- ID: {submission.submission_id}
- Language: {submission.language}
- Description: {submission.description}

**Review Summary:**
{review_report.get('summary', 'No summary available')}

**Overall Score:** {review_report.get('overall_score', 'N/A')}/100

**Security Findings:** {len(review_report.get('security_findings', []))} issues found
Priority Issues: {review_report.get('priority_issues', [])}

**Test Results:**
- Total Tests: {test_results.get('total_tests', 0)}
- Passed: {test_results.get('passed', 0)}
- Failed: {test_results.get('failed', 0)}
- Coverage: {test_results.get('coverage_percentage', 0)}%

**Recommendations from Review:**
{chr(10).join(f"- {rec}" for rec in review_report.get('recommendations', [])[:5])}

Please:
1. Check memory for similar past code reviews
2. Synthesize a concise executive summary
3. Highlight the top 5 most critical issues
4. Provide 5 concrete, actionable recommendations
5. Compare this review to past reviews if relevant patterns exist
6. Store key insights from this review for future reference

Format your response with clear sections."""

    def _build_final_report(
        self,
        submission: CodeSubmission,
        review_report: Dict,
        test_results: Dict,
        llm_response: str,
    ) -> Dict:
        """Build the final comprehensive report with LLM analysis."""
        # Extract structured data from review_report
        security_findings = review_report.get("security_findings", [])
        performance_analysis = review_report.get("performance_analysis", {})
        style_issues = review_report.get("style_issues", [])
        test_suite = review_report.get("test_suite", {})

        # Count critical issues
        critical_security_issues = sum(
            1
            for f in security_findings
            if isinstance(f, dict) and f.get("severity") == "critical"
        )

        # Build final comprehensive report
        final_report = {
            "submission_id": submission.submission_id,
            "language": submission.language,
            "description": submission.description,
            "review_date": datetime.now().isoformat(),
            "overall_score": review_report.get("overall_score", 70),
            "security_findings_count": len(security_findings),
            "critical_security_issues": critical_security_issues,
            "performance_bottlenecks": len(performance_analysis.get("bottlenecks", [])),
            "style_issues_count": len(style_issues),
            "test_coverage": test_suite.get(
                "coverage_percentage", test_results.get("coverage_percentage", 0)
            ),
            "test_results": test_results,
            "priority_issues": review_report.get("priority_issues", []),
            "recommendations": review_report.get("recommendations", []),
            "summary": review_report.get("summary", ""),
            "llm_analysis": llm_response[:1000],  # First 1000 chars of LLM analysis
            "historical_context": self._detect_historical_context(llm_response),
        }

        self.logger.info(
            f"Final report with LLM analysis generated for: {submission.submission_id}"
        )
        return final_report

    def _build_fallback_report(
        self,
        submission: CodeSubmission,
        review_report: Dict,
        test_results: Dict,
        error: Exception,
    ) -> Dict:
        """Build fallback report without LLM enhancement."""
        security_findings = review_report.get("security_findings", [])
        performance_analysis = review_report.get("performance_analysis", {})
        style_issues = review_report.get("style_issues", [])
        test_suite = review_report.get("test_suite", {})

        critical_security_issues = sum(
            1
            for f in security_findings
            if isinstance(f, dict) and f.get("severity") == "critical"
        )

        return {
            "submission_id": submission.submission_id,
            "language": submission.language,
            "description": submission.description,
            "review_date": datetime.now().isoformat(),
            "overall_score": review_report.get("overall_score", 70),
            "security_findings_count": len(security_findings),
            "critical_security_issues": critical_security_issues,
            "performance_bottlenecks": len(performance_analysis.get("bottlenecks", [])),
            "style_issues_count": len(style_issues),
            "test_coverage": test_suite.get(
                "coverage_percentage", test_results.get("coverage_percentage", 0)
            ),
            "test_results": test_results,
            "priority_issues": review_report.get("priority_issues", []),
            "recommendations": review_report.get("recommendations", []),
            "summary": review_report.get("summary", ""),
            "llm_analysis": f"Error generating LLM analysis: {str(error)[:200]}",
            "historical_context": "Error accessing historical context",
        }

    def _detect_historical_context(self, llm_response: str) -> str:
        """Detect if historical context was used in the response."""
        response_lower = llm_response.lower()
        if "past" in response_lower or "previous" in response_lower or "similar" in response_lower:
            return "Mem0 context included - patterns from past reviews applied"
        return "No historical patterns found - first review of this type"
