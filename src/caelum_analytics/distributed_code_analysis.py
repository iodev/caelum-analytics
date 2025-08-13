"""Distributed code analysis system for the caelum-code-analysis MCP server."""

import asyncio
import ast
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .cluster_protocol import (
    cluster_node,
    ClusterMessage,
    MessageType,
    TaskDistribution,
)


logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of code analysis that can be distributed."""

    STATIC_ANALYSIS = "static_analysis"
    COMPLEXITY_METRICS = "complexity_metrics"
    SECURITY_SCAN = "security_scan"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    CODE_QUALITY = "code_quality"
    PERFORMANCE_PROFILING = "performance_profiling"


@dataclass
class CodeChunk:
    """Represents a chunk of code to be analyzed."""

    chunk_id: str
    file_paths: List[str]
    total_lines: int
    size_bytes: int
    file_types: List[str]
    complexity_estimate: int  # 1-10 scale

    def __post_init__(self):
        if self.chunk_id is None:
            self.chunk_id = str(uuid.uuid4())


@dataclass
class AnalysisTask:
    """Distributed code analysis task."""

    task_id: str
    analysis_type: AnalysisType
    source_path: str
    chunks: List[CodeChunk]
    target_machines: List[str]
    configuration: Dict[str, Any]
    created_at: datetime
    estimated_duration: int = 300  # seconds
    priority: int = 5

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class AnalysisResult:
    """Result from analyzing a code chunk."""

    chunk_id: str
    machine_id: str
    analysis_type: AnalysisType
    results: Dict[str, Any]
    execution_time: float
    completed_at: datetime
    errors: List[str] = None

    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now(timezone.utc)
        if self.errors is None:
            self.errors = []


@dataclass
class DistributedAnalysisSession:
    """Tracks a complete distributed analysis session."""

    session_id: str
    task: AnalysisTask
    chunk_assignments: Dict[str, str]  # chunk_id -> machine_id
    results: Dict[str, AnalysisResult]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now(timezone.utc)

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if not self.chunk_assignments:
            return 0.0
        completed = len([r for r in self.results.values() if r.completed_at])
        return (completed / len(self.chunk_assignments)) * 100

    @property
    def total_execution_time(self) -> Optional[float]:
        """Calculate total execution time."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class DistributedCodeAnalyzer:
    """Main distributed code analysis coordinator."""

    def __init__(self):
        self.active_sessions: Dict[str, DistributedAnalysisSession] = {}
        self.chunk_size_target = 50  # Target number of files per chunk
        self.max_chunk_size_mb = 10  # Maximum chunk size in MB
        self.supported_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".swift",
            ".kt",
            ".scala",
        }

    async def analyze_codebase(
        self,
        source_path: str,
        analysis_type: AnalysisType,
        configuration: Dict[str, Any] = None,
        target_machines: List[str] = None,
    ) -> str:
        """Start distributed analysis of a codebase."""

        if configuration is None:
            configuration = {}

        # Create analysis task
        task_id = str(uuid.uuid4())

        logger.info(
            f"Starting distributed code analysis: {analysis_type.value} on {source_path}"
        )

        # Discover and partition the codebase
        chunks = await self._partition_codebase(source_path)

        if not chunks:
            raise ValueError(f"No analyzable code files found in {source_path}")

        # Get available machines if not specified
        if not target_machines:
            target_machines = list(cluster_node.connections.keys())

        if not target_machines:
            logger.warning("No remote machines available, running locally")
            target_machines = [cluster_node.machine_id]

        # Create analysis task
        analysis_task = AnalysisTask(
            task_id=task_id,
            analysis_type=analysis_type,
            source_path=source_path,
            chunks=chunks,
            target_machines=target_machines,
            configuration=configuration,
            created_at=datetime.now(timezone.utc),
        )

        # Create analysis session
        session = DistributedAnalysisSession(
            session_id=task_id,
            task=analysis_task,
            chunk_assignments={},
            results={},
            start_time=datetime.now(timezone.utc),
        )

        self.active_sessions[task_id] = session

        # Distribute chunks across machines
        await self._distribute_analysis_chunks(session)

        return task_id

    async def _partition_codebase(self, source_path: str) -> List[CodeChunk]:
        """Partition codebase into chunks for distributed analysis."""

        source_path = Path(source_path)
        if not source_path.exists():
            raise ValueError(f"Source path does not exist: {source_path}")

        # Collect all analyzable files
        all_files = []

        if source_path.is_file():
            if source_path.suffix in self.supported_extensions:
                all_files = [source_path]
        else:
            # Recursively find code files
            for ext in self.supported_extensions:
                all_files.extend(source_path.rglob(f"*{ext}"))

        if not all_files:
            return []

        logger.info(f"Found {len(all_files)} code files to analyze")

        # Calculate file metadata
        file_metadata = []
        for file_path in all_files:
            try:
                stat = file_path.stat()
                lines = self._count_lines(file_path)
                file_metadata.append(
                    {
                        "path": str(file_path),
                        "size": stat.st_size,
                        "lines": lines,
                        "ext": file_path.suffix,
                        "complexity": self._estimate_complexity(file_path, lines),
                    }
                )
            except Exception as e:
                logger.warning(f"Could not analyze file {file_path}: {e}")

        # Sort by complexity (most complex first for better load balancing)
        file_metadata.sort(key=lambda x: x["complexity"], reverse=True)

        # Create chunks
        chunks = []
        current_chunk_files = []
        current_chunk_size = 0
        current_chunk_lines = 0

        for file_meta in file_metadata:
            # Check if adding this file would exceed chunk limits
            would_exceed_size = (current_chunk_size + file_meta["size"]) > (
                self.max_chunk_size_mb * 1024 * 1024
            )
            would_exceed_count = len(current_chunk_files) >= self.chunk_size_target

            if current_chunk_files and (would_exceed_size or would_exceed_count):
                # Create chunk from current files
                chunks.append(
                    self._create_chunk(
                        current_chunk_files, current_chunk_size, current_chunk_lines
                    )
                )

                # Start new chunk
                current_chunk_files = []
                current_chunk_size = 0
                current_chunk_lines = 0

            # Add file to current chunk
            current_chunk_files.append(file_meta)
            current_chunk_size += file_meta["size"]
            current_chunk_lines += file_meta["lines"]

        # Add final chunk if it has files
        if current_chunk_files:
            chunks.append(
                self._create_chunk(
                    current_chunk_files, current_chunk_size, current_chunk_lines
                )
            )

        logger.info(f"Created {len(chunks)} chunks for analysis")
        return chunks

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a code file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _estimate_complexity(self, file_path: Path, lines: int) -> int:
        """Estimate complexity of a file (1-10 scale)."""
        # Simple heuristic based on file size and extension
        base_complexity = min(lines // 100, 5)  # 1 point per 100 lines, max 5

        # Adjust based on file type
        complexity_multipliers = {
            ".py": 1.2,
            ".js": 1.3,
            ".ts": 1.4,
            ".java": 1.1,
            ".cpp": 1.5,
            ".c": 1.3,
            ".h": 1.0,
            ".hpp": 1.2,
            ".cs": 1.1,
            ".go": 1.0,
            ".rs": 1.3,
            ".php": 1.2,
            ".rb": 1.1,
            ".swift": 1.2,
            ".kt": 1.2,
            ".scala": 1.4,
        }

        multiplier = complexity_multipliers.get(file_path.suffix, 1.0)
        complexity = int(base_complexity * multiplier)

        return max(1, min(10, complexity))  # Ensure 1-10 range

    def _create_chunk(
        self, file_metadata: List[Dict], total_size: int, total_lines: int
    ) -> CodeChunk:
        """Create a CodeChunk from file metadata."""

        file_paths = [f["path"] for f in file_metadata]
        file_types = list(set(f["ext"] for f in file_metadata))
        avg_complexity = sum(f["complexity"] for f in file_metadata) // len(
            file_metadata
        )

        return CodeChunk(
            chunk_id=str(uuid.uuid4()),
            file_paths=file_paths,
            total_lines=total_lines,
            size_bytes=total_size,
            file_types=file_types,
            complexity_estimate=avg_complexity,
        )

    async def _distribute_analysis_chunks(self, session: DistributedAnalysisSession):
        """Distribute analysis chunks across available machines."""

        chunks = session.task.chunks
        target_machines = session.task.target_machines

        if not target_machines:
            logger.error("No target machines available for analysis")
            session.status = "failed"
            return

        # Assign chunks to machines using round-robin with load balancing
        machine_loads = {machine: 0 for machine in target_machines}

        # Sort chunks by complexity (distribute complex chunks first)
        sorted_chunks = sorted(
            chunks, key=lambda c: c.complexity_estimate, reverse=True
        )

        for chunk in sorted_chunks:
            # Find machine with least load
            assigned_machine = min(machine_loads, key=machine_loads.get)

            # Update load (use complexity as load factor)
            machine_loads[assigned_machine] += chunk.complexity_estimate

            # Record assignment
            session.chunk_assignments[chunk.chunk_id] = assigned_machine

            # Send analysis task to machine
            await self._send_analysis_task(chunk, assigned_machine, session.task)

        logger.info(
            f"Distributed {len(chunks)} chunks across {len(target_machines)} machines"
        )
        for machine, load in machine_loads.items():
            logger.info(f"  {machine}: {load} complexity units")

    async def _send_analysis_task(
        self, chunk: CodeChunk, target_machine: str, task: AnalysisTask
    ):
        """Send analysis task to a specific machine."""

        task_message = ClusterMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.TASK_DISTRIBUTE,
            source_machine=cluster_node.machine_id,
            target_machines=[target_machine],
            payload={
                "task_type": "code_analysis",
                "service_name": "caelum-code-analysis",
                "analysis_type": task.analysis_type.value,
                "chunk": asdict(chunk),
                "configuration": task.configuration,
                "session_id": task.task_id,
            },
        )

        if target_machine == cluster_node.machine_id:
            # Process locally
            await self._process_chunk_locally(chunk, task)
        else:
            # Send to remote machine
            success = await cluster_node.send_message_to_machine(
                target_machine, task_message
            )
            if not success:
                logger.warning(f"Failed to send analysis task to {target_machine}")
                # Reassign chunk to another available machine
                await self._reassign_failed_chunk(chunk, task, target_machine)

    async def _process_chunk_locally(self, chunk: CodeChunk, task: AnalysisTask):
        """Process a code analysis chunk locally."""

        start_time = time.time()

        try:
            # Perform real code analysis on the chunk files
            results = await self._analyze_code_chunk(
                chunk, task.analysis_type, task.configuration
            )

            execution_time = time.time() - start_time

            # Create result
            result = AnalysisResult(
                chunk_id=chunk.chunk_id,
                machine_id=cluster_node.machine_id,
                analysis_type=task.analysis_type,
                results=results,
                execution_time=execution_time,
                completed_at=datetime.now(timezone.utc),
            )

            # Store result
            session = self.active_sessions.get(task.task_id)
            if session:
                session.results[chunk.chunk_id] = result

                # Check if analysis is complete
                await self._check_analysis_completion(session)

            logger.info(
                f"Completed analysis of chunk {chunk.chunk_id[:8]} ({execution_time:.2f}s)"
            )

        except Exception as e:
            logger.error(f"Error processing chunk {chunk.chunk_id}: {e}")

            # Record error result
            result = AnalysisResult(
                chunk_id=chunk.chunk_id,
                machine_id=cluster_node.machine_id,
                analysis_type=task.analysis_type,
                results={},
                execution_time=time.time() - start_time,
                completed_at=datetime.now(timezone.utc),
                errors=[str(e)],
            )

            session = self.active_sessions.get(task.task_id)
            if session:
                session.results[chunk.chunk_id] = result

    async def _check_analysis_completion(self, session: DistributedAnalysisSession):
        """Check if distributed analysis is complete and aggregate results."""

        total_chunks = len(session.chunk_assignments)
        completed_chunks = len(session.results)

        if completed_chunks >= total_chunks:
            # Analysis complete - aggregate results
            session.status = "completed"
            session.end_time = datetime.now(timezone.utc)

            aggregated = await self._aggregate_results(session)

            logger.info(f"Distributed analysis completed: {session.session_id}")
            logger.info(f"  Total time: {session.total_execution_time:.2f}s")
            logger.info(f"  Chunks processed: {completed_chunks}")
            logger.info(f"  Files analyzed: {aggregated.get('total_files', 0)}")
            logger.info(f"  Total lines: {aggregated.get('total_lines', 0)}")

    async def _aggregate_results(
        self, session: DistributedAnalysisSession
    ) -> Dict[str, Any]:
        """Aggregate results from all analysis chunks."""

        aggregated = {
            "session_id": session.session_id,
            "analysis_type": session.task.analysis_type.value,
            "total_files": 0,
            "total_lines": 0,
            "total_execution_time": session.total_execution_time,
            "machines_used": len(set(r.machine_id for r in session.results.values())),
            "chunks_processed": len(session.results),
            "errors": [],
        }

        # Aggregate numeric results
        for result in session.results.values():
            if result.errors:
                aggregated["errors"].extend(result.errors)

            results = result.results
            aggregated["total_files"] += results.get("files_analyzed", 0)
            aggregated["total_lines"] += results.get("total_lines", 0)

        # Analysis type specific aggregation
        if session.task.analysis_type == AnalysisType.STATIC_ANALYSIS:
            aggregated.update(
                {
                    "total_warnings": sum(
                        r.results.get("warnings", 0) for r in session.results.values()
                    ),
                    "total_code_smells": sum(
                        r.results.get("code_smells", 0)
                        for r in session.results.values()
                    ),
                    "syntax_errors": sum(
                        r.results.get("syntax_errors", 0)
                        for r in session.results.values()
                    ),
                }
            )
        elif session.task.analysis_type == AnalysisType.SECURITY_SCAN:
            aggregated.update(
                {
                    "total_vulnerabilities": sum(
                        r.results.get("vulnerabilities", 0)
                        for r in session.results.values()
                    ),
                    "average_security_score": sum(
                        r.results.get("security_score", 0)
                        for r in session.results.values()
                    )
                    / len(session.results),
                }
            )
        elif session.task.analysis_type == AnalysisType.COMPLEXITY_METRICS:
            aggregated.update(
                {
                    "average_complexity": sum(
                        r.results.get("cyclomatic_complexity", 0)
                        for r in session.results.values()
                    )
                    / len(session.results),
                    "average_maintainability": sum(
                        r.results.get("maintainability_index", 0)
                        for r in session.results.values()
                    )
                    / len(session.results),
                    "total_technical_debt": sum(
                        r.results.get("technical_debt_hours", 0)
                        for r in session.results.values()
                    ),
                }
            )

        # Store aggregated results
        session.task.configuration["aggregated_results"] = aggregated

        return aggregated

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a distributed analysis session."""

        session = self.active_sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session_id,
            "status": session.status,
            "analysis_type": session.task.analysis_type.value,
            "completion_percentage": session.completion_percentage,
            "chunks_total": len(session.chunk_assignments),
            "chunks_completed": len(session.results),
            "machines_assigned": len(set(session.chunk_assignments.values())),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "execution_time": session.total_execution_time,
            "results_summary": session.task.configuration.get("aggregated_results"),
        }

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active analysis sessions."""
        return [
            self.get_session_status(session_id)
            for session_id in self.active_sessions.keys()
        ]

    async def _analyze_code_chunk(
        self,
        chunk: CodeChunk,
        analysis_type: AnalysisType,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Perform real code analysis on a chunk of files."""
        import ast
        import re
        import subprocess
        from pathlib import Path

        results = {
            "files_analyzed": len(chunk.file_paths),
            "total_lines": chunk.total_lines,
            "analysis_type": analysis_type.value,
            "file_types": chunk.file_types,
            "files_details": [],
        }

        total_complexity = 0
        total_functions = 0
        total_classes = 0
        total_imports = 0
        security_issues = []
        syntax_errors = []
        warnings = []

        for file_path in chunk.file_paths:
            try:
                file_results = await self._analyze_single_file(file_path, analysis_type)
                results["files_details"].append(file_results)

                # Aggregate metrics
                total_complexity += file_results.get("cyclomatic_complexity", 0)
                total_functions += file_results.get("function_count", 0)
                total_classes += file_results.get("class_count", 0)
                total_imports += file_results.get("import_count", 0)

                # Collect issues
                security_issues.extend(file_results.get("security_issues", []))
                syntax_errors.extend(file_results.get("syntax_errors", []))
                warnings.extend(file_results.get("warnings", []))

            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")
                results["files_details"].append(
                    {"file_path": file_path, "error": str(e), "analyzed": False}
                )

        # Calculate aggregate metrics based on analysis type
        if analysis_type == AnalysisType.STATIC_ANALYSIS:
            results.update(
                {
                    "syntax_errors": len(syntax_errors),
                    "warnings": len(warnings),
                    "code_smells": len([w for w in warnings if "smell" in w.lower()]),
                    "function_count": total_functions,
                    "class_count": total_classes,
                    "import_count": total_imports,
                    "error_details": syntax_errors[:10],  # Limit to first 10
                    "warning_details": warnings[:20],  # Limit to first 20
                }
            )
        elif analysis_type == AnalysisType.SECURITY_SCAN:
            critical_issues = [
                i for i in security_issues if i.get("severity") == "critical"
            ]
            high_issues = [i for i in security_issues if i.get("severity") == "high"]
            results.update(
                {
                    "vulnerabilities": len(security_issues),
                    "critical_vulnerabilities": len(critical_issues),
                    "high_vulnerabilities": len(high_issues),
                    "security_score": max(
                        0, 100 - len(critical_issues) * 20 - len(high_issues) * 10
                    ),
                    "security_issues": security_issues[:10],  # Limit details
                }
            )
        elif analysis_type == AnalysisType.COMPLEXITY_METRICS:
            avg_complexity = (
                total_complexity / max(1, total_functions) if total_functions > 0 else 0
            )
            maintainability = max(0, 100 - avg_complexity * 2)
            results.update(
                {
                    "cyclomatic_complexity": total_complexity,
                    "average_complexity": round(avg_complexity, 2),
                    "maintainability_index": round(maintainability, 2),
                    "technical_debt_hours": round(total_complexity * 0.1, 2),
                    "function_count": total_functions,
                    "class_count": total_classes,
                }
            )
        elif analysis_type == AnalysisType.DEPENDENCY_ANALYSIS:
            results.update(
                {
                    "total_imports": total_imports,
                    "unique_dependencies": len(set(results.get("all_imports", []))),
                    "external_dependencies": len(
                        [
                            i
                            for i in results.get("all_imports", [])
                            if not i.startswith(".")
                        ]
                    ),
                    "circular_dependencies": [],  # Would need more sophisticated analysis
                }
            )
        elif analysis_type == AnalysisType.CODE_QUALITY:
            quality_score = self._calculate_quality_score(results["files_details"])
            results.update(
                {
                    "quality_score": quality_score,
                    "code_coverage": 0,  # Would need test runner integration
                    "documentation_coverage": self._calculate_doc_coverage(
                        results["files_details"]
                    ),
                    "style_violations": len(warnings),
                }
            )

        return results

    async def _analyze_single_file(
        self, file_path: str, analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """Analyze a single file and return metrics."""
        import ast
        import re
        from pathlib import Path

        file_path = Path(file_path)
        results = {
            "file_path": str(file_path),
            "analyzed": True,
            "size_bytes": 0,
            "line_count": 0,
        }

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                results["size_bytes"] = len(content.encode("utf-8"))
                results["line_count"] = len(content.splitlines())

            # File extension specific analysis
            if file_path.suffix == ".py":
                results.update(
                    await self._analyze_python_file(file_path, content, analysis_type)
                )
            elif file_path.suffix in [".js", ".ts"]:
                results.update(
                    await self._analyze_javascript_file(
                        file_path, content, analysis_type
                    )
                )
            elif file_path.suffix in [".java"]:
                results.update(
                    await self._analyze_java_file(file_path, content, analysis_type)
                )
            else:
                results.update(
                    await self._analyze_generic_file(file_path, content, analysis_type)
                )

        except Exception as e:
            results.update(
                {"analyzed": False, "error": str(e), "syntax_errors": [str(e)]}
            )

        return results

    async def _analyze_python_file(
        self, file_path: Path, content: str, analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """Analyze Python file using AST."""
        import ast
        import re

        results = {
            "language": "python",
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "cyclomatic_complexity": 0,
            "syntax_errors": [],
            "warnings": [],
            "security_issues": [],
        }

        try:
            # Parse AST
            tree = ast.parse(content)

            # Count elements
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    results["function_count"] += 1
                    results[
                        "cyclomatic_complexity"
                    ] += self._calculate_cyclomatic_complexity_python(node)
                elif isinstance(node, ast.ClassDef):
                    results["class_count"] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    results["import_count"] += 1

            # Security analysis
            if analysis_type == AnalysisType.SECURITY_SCAN:
                results["security_issues"] = self._find_python_security_issues(
                    tree, content
                )

            # Code quality checks
            if analysis_type in [
                AnalysisType.STATIC_ANALYSIS,
                AnalysisType.CODE_QUALITY,
            ]:
                results["warnings"] = self._find_python_quality_issues(tree, content)

        except SyntaxError as e:
            results["syntax_errors"].append(f"Line {e.lineno}: {e.msg}")
        except Exception as e:
            results["syntax_errors"].append(f"Parse error: {str(e)}")

        return results

    async def _analyze_javascript_file(
        self, file_path: Path, content: str, analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript file."""
        import re

        results = {
            "language": "javascript",
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "cyclomatic_complexity": 0,
            "syntax_errors": [],
            "warnings": [],
            "security_issues": [],
        }

        # Simple regex-based analysis (could be enhanced with proper JS parser)
        functions = re.findall(
            r"function\s+\w+|const\s+\w+\s*=\s*\([^)]*\)\s*=>", content
        )
        classes = re.findall(r"class\s+\w+", content)
        imports = re.findall(r"import\s+.*?from|require\s*\(", content)

        results["function_count"] = len(functions)
        results["class_count"] = len(classes)
        results["import_count"] = len(imports)

        # Simple complexity estimation
        complexity_patterns = ["if", "for", "while", "switch", "catch", "&&", "||", "?"]
        for pattern in complexity_patterns:
            results["cyclomatic_complexity"] += len(re.findall(pattern, content))

        # Security issues
        if analysis_type == AnalysisType.SECURITY_SCAN:
            security_patterns = [
                (r"eval\s*\(", "Use of eval() function", "high"),
                (r"innerHTML\s*=", "Potential XSS vulnerability", "medium"),
                (r"document\.write\s*\(", "Use of document.write", "medium"),
                (r"\.html\s*\(", "Dynamic HTML injection", "medium"),
            ]

            for pattern, message, severity in security_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    results["security_issues"].append(
                        {"message": message, "severity": severity, "line": line_num}
                    )

        return results

    async def _analyze_java_file(
        self, file_path: Path, content: str, analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """Analyze Java file."""
        import re

        results = {
            "language": "java",
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "cyclomatic_complexity": 0,
            "syntax_errors": [],
            "warnings": [],
            "security_issues": [],
        }

        # Java-specific patterns
        methods = re.findall(
            r"(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\([^)]*\)\s*\{",
            content,
        )
        classes = re.findall(r"(public|private)?\s*class\s+\w+", content)
        imports = re.findall(r"import\s+[\w\.]+;", content)

        results["function_count"] = len(methods)
        results["class_count"] = len(classes)
        results["import_count"] = len(imports)

        # Complexity calculation
        complexity_patterns = ["if", "for", "while", "switch", "catch", "&&", "||", "?"]
        for pattern in complexity_patterns:
            results["cyclomatic_complexity"] += len(re.findall(pattern, content))

        return results

    async def _analyze_generic_file(
        self, file_path: Path, content: str, analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """Generic analysis for unsupported file types."""
        import re

        results = {
            "language": "generic",
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "cyclomatic_complexity": 1,  # Base complexity
            "syntax_errors": [],
            "warnings": [],
            "security_issues": [],
        }

        # Basic pattern matching
        if_statements = len(re.findall(r"\bif\b", content))
        for_loops = len(re.findall(r"\bfor\b", content))
        while_loops = len(re.findall(r"\bwhile\b", content))

        results["cyclomatic_complexity"] = 1 + if_statements + for_loops + while_loops

        return results

    def _calculate_cyclomatic_complexity_python(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a Python function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(
                child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
            ):
                complexity += 1

        return complexity

    def _find_python_security_issues(
        self, tree: ast.AST, content: str
    ) -> List[Dict[str, Any]]:
        """Find security issues in Python code."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node.func, "id"):
                    # Check for dangerous functions
                    if node.func.id in ["eval", "exec", "compile"]:
                        issues.append(
                            {
                                "message": f"Use of dangerous function: {node.func.id}",
                                "severity": "critical",
                                "line": node.lineno,
                            }
                        )
                    elif node.func.id in ["input", "raw_input"]:
                        issues.append(
                            {
                                "message": "User input without validation",
                                "severity": "medium",
                                "line": node.lineno,
                            }
                        )
                elif hasattr(node.func, "attr"):
                    if node.func.attr in ["system", "popen", "spawn"]:
                        issues.append(
                            {
                                "message": f"System command execution: {node.func.attr}",
                                "severity": "high",
                                "line": node.lineno,
                            }
                        )

        return issues

    def _find_python_quality_issues(self, tree: ast.AST, content: str) -> List[str]:
        """Find code quality issues in Python code."""
        warnings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function length
                if hasattr(node, "end_lineno") and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                    if func_length > 50:
                        warnings.append(
                            f"Long function '{node.name}' ({func_length} lines)"
                        )

                # Check for missing docstring
                if not ast.get_docstring(node):
                    warnings.append(f"Function '{node.name}' missing docstring")

            elif isinstance(node, ast.ClassDef):
                # Check for missing docstring
                if not ast.get_docstring(node):
                    warnings.append(f"Class '{node.name}' missing docstring")

        return warnings

    def _calculate_quality_score(self, file_details: List[Dict]) -> float:
        """Calculate overall code quality score."""
        if not file_details:
            return 0.0

        total_score = 0
        analyzed_files = 0

        for file_detail in file_details:
            if not file_detail.get("analyzed", False):
                continue

            analyzed_files += 1
            file_score = 100

            # Deduct for issues
            file_score -= len(file_detail.get("syntax_errors", [])) * 20
            file_score -= len(file_detail.get("warnings", [])) * 2
            file_score -= len(file_detail.get("security_issues", [])) * 10

            # Complexity penalty
            complexity = file_detail.get("cyclomatic_complexity", 0)
            functions = file_detail.get("function_count", 1)
            avg_complexity = complexity / max(1, functions)
            if avg_complexity > 10:
                file_score -= (avg_complexity - 10) * 5

            total_score += max(0, file_score)

        return round(total_score / max(1, analyzed_files), 2)

    def _calculate_doc_coverage(self, file_details: List[Dict]) -> float:
        """Calculate documentation coverage percentage."""
        total_functions = 0
        documented_functions = 0

        for file_detail in file_details:
            if not file_detail.get("analyzed", False):
                continue

            functions = file_detail.get("function_count", 0)
            total_functions += functions

            # Estimate documented functions (would need more sophisticated analysis)
            warnings = file_detail.get("warnings", [])
            missing_docs = len([w for w in warnings if "docstring" in w])
            documented_functions += max(0, functions - missing_docs)

        if total_functions == 0:
            return 100.0

        return round((documented_functions / total_functions) * 100, 2)

    async def _reassign_failed_chunk(
        self, chunk: CodeChunk, task: AnalysisTask, failed_machine: str
    ):
        """Reassign a failed chunk to another available machine."""
        # Get list of available machines excluding the failed one
        available_machines = [m for m in task.target_machines if m != failed_machine]

        if not available_machines:
            logger.warning(
                f"No alternative machines available for chunk {chunk.chunk_id[:8]}, processing locally"
            )
            await self._process_chunk_locally(chunk, task)
            return

        # Find the machine with the least current load
        machine_loads = {}
        for machine in available_machines:
            # Count current chunk assignments for this machine
            session = self.active_sessions.get(task.task_id)
            if session:
                machine_loads[machine] = len(
                    [m for m in session.chunk_assignments.values() if m == machine]
                )
            else:
                machine_loads[machine] = 0

        # Select machine with least load
        target_machine = min(machine_loads, key=machine_loads.get)

        # Update assignment
        session = self.active_sessions.get(task.task_id)
        if session:
            session.chunk_assignments[chunk.chunk_id] = target_machine

        logger.info(
            f"Reassigning chunk {chunk.chunk_id[:8]} from {failed_machine} to {target_machine}"
        )

        # Send to new machine
        await self._send_analysis_task(chunk, target_machine, task)


# Global distributed code analyzer instance
distributed_analyzer = DistributedCodeAnalyzer()
