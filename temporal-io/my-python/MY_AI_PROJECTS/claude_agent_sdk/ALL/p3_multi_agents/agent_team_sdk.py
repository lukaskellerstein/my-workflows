"""Multi-agent team for code review using SDK SupervisorTeam pattern."""

import json
import logging
import re
from typing import Any, Dict, List

from claude_agent_sdk import AgentDefinition
from shared.sdk_wrapper import SupervisorTeam
from shared.models import CodeSubmission

logger = logging.getLogger(__name__)


class CodeReviewTeam:
    """Orchestrates multi-agent code review using SDK SupervisorTeam."""

    def __init__(self):
        self.logger = logging.getLogger("team.code_review")

    async def review(self, submission: CodeSubmission) -> Dict[str, Any]:
        """
        Execute multi-agent code review using SDK SupervisorTeam.

        Agents work under supervisor coordination.
        """
        self.logger.info(f"Starting SDK team review for: {submission.submission_id}")

        # Define specialist agents using SDK AgentDefinition
        # Note: Tools list should contain MCP tool names that will be available from mcp_servers
        team = SupervisorTeam(
            supervisor_name="tech-lead",
            supervisor_description="Coordinates code review team and synthesizes findings from security, performance, style, and test specialists",
            team_agents={
                "security-expert": AgentDefinition(
                    description="Security vulnerability analyst with E2B sandbox - scans for injection attacks, authentication issues, and vulnerabilities",
                    prompt="You are a security expert with access to E2B sandbox for safe code execution. Analyze code for security vulnerabilities including SQL injection, XSS, authentication issues, and insecure dependencies. Use E2B MCP tools to safely test potential exploits.",
                    tools=[],  # Tools will be available from E2B MCP server
                    model="sonnet",
                ),
                "performance-expert": AgentDefinition(
                    description="Performance optimization specialist with E2B sandbox - analyzes complexity and benchmarks code",
                    prompt="You are a performance expert with access to E2B sandbox. Analyze algorithmic complexity, identify bottlenecks, and run performance benchmarks. Use E2B MCP tools to execute code and measure actual performance.",
                    tools=[],  # Tools will be available from E2B MCP server
                    model="sonnet",
                ),
                "style-expert": AgentDefinition(
                    description="Code style and best practices reviewer with Academia MCP - checks naming, documentation, and conventions",
                    prompt="You are a code style expert with access to Academia MCP for coding standards research. Review code for naming conventions, documentation quality, and adherence to best practices. Use Academia MCP tools to reference authoritative style guides.",
                    tools=[],  # Tools will be available from Academia MCP server
                    model="sonnet",
                ),
                "test-expert": AgentDefinition(
                    description="Test generation specialist with E2B sandbox - creates and executes unit and integration tests",
                    prompt="You are a testing expert with access to E2B sandbox. Generate comprehensive unit and integration tests with good edge case coverage. Use E2B MCP tools to execute tests and verify they work correctly.",
                    tools=[],  # Tools will be available from E2B MCP server
                    model="sonnet",
                ),
            },
            supervisor_tools=[],  # Supervisor coordinates, doesn't need tools
            mcp_servers=["e2b", "academia"],  # Enable E2B and Academia MCP servers for all agents
        )

        # Execute team review
        task = f"""Review this code submission comprehensively:

Language: {submission.language}
Description: {submission.description}

Code:
```{submission.language}
{submission.code}
```

Coordinate your team to provide:
1. Security analysis (vulnerabilities, risks)
2. Performance analysis (complexity, bottlenecks, optimizations)
3. Style review (naming, documentation, best practices)
4. Test coverage (unit tests, integration tests, coverage percentage)

Provide a comprehensive final report with:
- Overall code quality score (0-100)
- Priority issues to address
- Specific recommendations
- Summary of findings
"""

        result = await team.execute(task=task, max_iterations=15)

        # Parse the result into structured format
        report = {
            "submission_id": submission.submission_id,
            "review": result,
            "overall_score": self._extract_score(result),
            "priority_issues": self._extract_priority_issues(result),
            "recommendations": self._extract_recommendations(result),
            "summary": result[:500] + "..." if len(result) > 500 else result,
        }

        self.logger.info(f"SDK team review complete: score={report.get('overall_score', 'N/A')}")
        return report

    def _extract_score(self, text: str) -> int:
        """Extract overall score from review text."""
        # Look for "score: 85" or "85/100" patterns
        score_match = re.search(r"(?:score|rating)[\s:]+(\d+)", text, re.IGNORECASE)
        if score_match:
            return int(score_match.group(1))

        score_match = re.search(r"(\d+)\s*/\s*100", text)
        if score_match:
            return int(score_match.group(1))

        return 70  # Default score

    def _extract_priority_issues(self, text: str) -> List[str]:
        """Extract priority issues from review text."""
        issues = []

        # Look for sections with issues/problems
        if "priority" in text.lower() or "critical" in text.lower():
            lines = text.split("\n")
            in_issues_section = False

            for line in lines:
                if "priority" in line.lower() or "critical" in line.lower():
                    in_issues_section = True
                    continue

                if in_issues_section and line.strip().startswith(("-", "*", "•", "1.", "2.", "3.")):
                    issues.append(line.strip().lstrip("-*•0123456789. "))

                if in_issues_section and len(issues) >= 5:
                    break

        return issues[:5] if issues else ["See full review for details"]

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from review text."""
        recommendations = []

        # Look for recommendation sections
        if "recommend" in text.lower() or "suggest" in text.lower():
            lines = text.split("\n")
            in_rec_section = False

            for line in lines:
                if "recommend" in line.lower() or "suggest" in line.lower():
                    in_rec_section = True
                    continue

                if in_rec_section and line.strip().startswith(("-", "*", "•", "1.", "2.", "3.")):
                    recommendations.append(line.strip().lstrip("-*•0123456789. "))

                if in_rec_section and len(recommendations) >= 5:
                    break

        return recommendations[:5] if recommendations else ["See full review for details"]
