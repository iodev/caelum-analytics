"""Distributed code analysis system for the caelum-code-analysis MCP server."""

import asyncio
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

from .cluster_protocol import cluster_node, ClusterMessage, MessageType, TaskDistribution


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
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala'
        }
    
    async def analyze_codebase(
        self,
        source_path: str,
        analysis_type: AnalysisType,
        configuration: Dict[str, Any] = None,
        target_machines: List[str] = None
    ) -> str:
        """Start distributed analysis of a codebase."""
        
        if configuration is None:
            configuration = {}
        
        # Create analysis task
        task_id = str(uuid.uuid4())
        
        logger.info(f"Starting distributed code analysis: {analysis_type.value} on {source_path}")
        
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
            created_at=datetime.now(timezone.utc)
        )
        
        # Create analysis session
        session = DistributedAnalysisSession(
            session_id=task_id,
            task=analysis_task,
            chunk_assignments={},
            results={},
            start_time=datetime.now(timezone.utc)
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
                file_metadata.append({
                    'path': str(file_path),
                    'size': stat.st_size,
                    'lines': lines,
                    'ext': file_path.suffix,
                    'complexity': self._estimate_complexity(file_path, lines)
                })
            except Exception as e:
                logger.warning(f"Could not analyze file {file_path}: {e}")
        
        # Sort by complexity (most complex first for better load balancing)
        file_metadata.sort(key=lambda x: x['complexity'], reverse=True)
        
        # Create chunks
        chunks = []
        current_chunk_files = []
        current_chunk_size = 0
        current_chunk_lines = 0
        
        for file_meta in file_metadata:
            # Check if adding this file would exceed chunk limits
            would_exceed_size = (current_chunk_size + file_meta['size']) > (self.max_chunk_size_mb * 1024 * 1024)
            would_exceed_count = len(current_chunk_files) >= self.chunk_size_target
            
            if current_chunk_files and (would_exceed_size or would_exceed_count):
                # Create chunk from current files
                chunks.append(self._create_chunk(current_chunk_files, current_chunk_size, current_chunk_lines))
                
                # Start new chunk
                current_chunk_files = []
                current_chunk_size = 0
                current_chunk_lines = 0
            
            # Add file to current chunk
            current_chunk_files.append(file_meta)
            current_chunk_size += file_meta['size']
            current_chunk_lines += file_meta['lines']
        
        # Add final chunk if it has files
        if current_chunk_files:
            chunks.append(self._create_chunk(current_chunk_files, current_chunk_size, current_chunk_lines))
        
        logger.info(f"Created {len(chunks)} chunks for analysis")
        return chunks
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a code file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    
    def _estimate_complexity(self, file_path: Path, lines: int) -> int:
        """Estimate complexity of a file (1-10 scale)."""
        # Simple heuristic based on file size and extension
        base_complexity = min(lines // 100, 5)  # 1 point per 100 lines, max 5
        
        # Adjust based on file type
        complexity_multipliers = {
            '.py': 1.2, '.js': 1.3, '.ts': 1.4, '.java': 1.1,
            '.cpp': 1.5, '.c': 1.3, '.h': 1.0, '.hpp': 1.2,
            '.cs': 1.1, '.go': 1.0, '.rs': 1.3, '.php': 1.2,
            '.rb': 1.1, '.swift': 1.2, '.kt': 1.2, '.scala': 1.4
        }
        
        multiplier = complexity_multipliers.get(file_path.suffix, 1.0)
        complexity = int(base_complexity * multiplier)
        
        return max(1, min(10, complexity))  # Ensure 1-10 range
    
    def _create_chunk(self, file_metadata: List[Dict], total_size: int, total_lines: int) -> CodeChunk:
        """Create a CodeChunk from file metadata."""
        
        file_paths = [f['path'] for f in file_metadata]
        file_types = list(set(f['ext'] for f in file_metadata))
        avg_complexity = sum(f['complexity'] for f in file_metadata) // len(file_metadata)
        
        return CodeChunk(
            chunk_id=str(uuid.uuid4()),
            file_paths=file_paths,
            total_lines=total_lines,
            size_bytes=total_size,
            file_types=file_types,
            complexity_estimate=avg_complexity
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
        sorted_chunks = sorted(chunks, key=lambda c: c.complexity_estimate, reverse=True)
        
        for chunk in sorted_chunks:
            # Find machine with least load
            assigned_machine = min(machine_loads, key=machine_loads.get)
            
            # Update load (use complexity as load factor)
            machine_loads[assigned_machine] += chunk.complexity_estimate
            
            # Record assignment
            session.chunk_assignments[chunk.chunk_id] = assigned_machine
            
            # Send analysis task to machine
            await self._send_analysis_task(chunk, assigned_machine, session.task)
        
        logger.info(f"Distributed {len(chunks)} chunks across {len(target_machines)} machines")
        for machine, load in machine_loads.items():
            logger.info(f"  {machine}: {load} complexity units")
    
    async def _send_analysis_task(self, chunk: CodeChunk, target_machine: str, task: AnalysisTask):
        """Send analysis task to a specific machine."""
        
        task_message = ClusterMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.TASK_DISTRIBUTE,
            source_machine=cluster_node.machine_id,
            target_machines=[target_machine],
            payload={
                'task_type': 'code_analysis',
                'service_name': 'caelum-code-analysis',
                'analysis_type': task.analysis_type.value,
                'chunk': asdict(chunk),
                'configuration': task.configuration,
                'session_id': task.task_id
            }
        )
        
        if target_machine == cluster_node.machine_id:
            # Process locally
            await self._process_chunk_locally(chunk, task)
        else:
            # Send to remote machine
            success = await cluster_node.send_message_to_machine(target_machine, task_message)
            if not success:
                logger.warning(f"Failed to send analysis task to {target_machine}")
                # TODO: Reassign chunk to another machine
    
    async def _process_chunk_locally(self, chunk: CodeChunk, task: AnalysisTask):
        """Process a code analysis chunk locally."""
        
        start_time = time.time()
        
        try:
            # Simulate code analysis (in real implementation, would call actual analysis tools)
            await asyncio.sleep(0.1 * chunk.complexity_estimate)  # Simulate processing time
            
            # Generate mock analysis results
            results = {
                'files_analyzed': len(chunk.file_paths),
                'total_lines': chunk.total_lines,
                'complexity_score': chunk.complexity_estimate * 10,
                'issues_found': max(0, chunk.complexity_estimate - 5),
                'analysis_type': task.analysis_type.value,
                'file_types': chunk.file_types
            }
            
            # Add specific results based on analysis type
            if task.analysis_type == AnalysisType.STATIC_ANALYSIS:
                results.update({
                    'syntax_errors': 0,
                    'warnings': chunk.complexity_estimate * 2,
                    'code_smells': max(0, chunk.complexity_estimate - 3)
                })
            elif task.analysis_type == AnalysisType.SECURITY_SCAN:
                results.update({
                    'vulnerabilities': max(0, chunk.complexity_estimate - 7),
                    'security_score': max(60, 100 - chunk.complexity_estimate * 5)
                })
            elif task.analysis_type == AnalysisType.COMPLEXITY_METRICS:
                results.update({
                    'cyclomatic_complexity': chunk.complexity_estimate * 3,
                    'maintainability_index': max(20, 100 - chunk.complexity_estimate * 8),
                    'technical_debt_hours': chunk.complexity_estimate * 0.5
                })
            
            execution_time = time.time() - start_time
            
            # Create result
            result = AnalysisResult(
                chunk_id=chunk.chunk_id,
                machine_id=cluster_node.machine_id,
                analysis_type=task.analysis_type,
                results=results,
                execution_time=execution_time,
                completed_at=datetime.now(timezone.utc)
            )
            
            # Store result
            session = self.active_sessions.get(task.task_id)
            if session:
                session.results[chunk.chunk_id] = result
                
                # Check if analysis is complete
                await self._check_analysis_completion(session)
            
            logger.info(f"Completed analysis of chunk {chunk.chunk_id[:8]} ({execution_time:.2f}s)")
            
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
                errors=[str(e)]
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
    
    async def _aggregate_results(self, session: DistributedAnalysisSession) -> Dict[str, Any]:
        """Aggregate results from all analysis chunks."""
        
        aggregated = {
            'session_id': session.session_id,
            'analysis_type': session.task.analysis_type.value,
            'total_files': 0,
            'total_lines': 0,
            'total_execution_time': session.total_execution_time,
            'machines_used': len(set(r.machine_id for r in session.results.values())),
            'chunks_processed': len(session.results),
            'errors': []
        }
        
        # Aggregate numeric results
        for result in session.results.values():
            if result.errors:
                aggregated['errors'].extend(result.errors)
            
            results = result.results
            aggregated['total_files'] += results.get('files_analyzed', 0)
            aggregated['total_lines'] += results.get('total_lines', 0)
        
        # Analysis type specific aggregation
        if session.task.analysis_type == AnalysisType.STATIC_ANALYSIS:
            aggregated.update({
                'total_warnings': sum(r.results.get('warnings', 0) for r in session.results.values()),
                'total_code_smells': sum(r.results.get('code_smells', 0) for r in session.results.values()),
                'syntax_errors': sum(r.results.get('syntax_errors', 0) for r in session.results.values())
            })
        elif session.task.analysis_type == AnalysisType.SECURITY_SCAN:
            aggregated.update({
                'total_vulnerabilities': sum(r.results.get('vulnerabilities', 0) for r in session.results.values()),
                'average_security_score': sum(r.results.get('security_score', 0) for r in session.results.values()) / len(session.results)
            })
        elif session.task.analysis_type == AnalysisType.COMPLEXITY_METRICS:
            aggregated.update({
                'average_complexity': sum(r.results.get('cyclomatic_complexity', 0) for r in session.results.values()) / len(session.results),
                'average_maintainability': sum(r.results.get('maintainability_index', 0) for r in session.results.values()) / len(session.results),
                'total_technical_debt': sum(r.results.get('technical_debt_hours', 0) for r in session.results.values())
            })
        
        # Store aggregated results
        session.task.configuration['aggregated_results'] = aggregated
        
        return aggregated
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a distributed analysis session."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            'session_id': session_id,
            'status': session.status,
            'analysis_type': session.task.analysis_type.value,
            'completion_percentage': session.completion_percentage,
            'chunks_total': len(session.chunk_assignments),
            'chunks_completed': len(session.results),
            'machines_assigned': len(set(session.chunk_assignments.values())),
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'execution_time': session.total_execution_time,
            'results_summary': session.task.configuration.get('aggregated_results')
        }
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active analysis sessions."""
        return [self.get_session_status(session_id) for session_id in self.active_sessions.keys()]


# Global distributed code analyzer instance
distributed_analyzer = DistributedCodeAnalyzer()