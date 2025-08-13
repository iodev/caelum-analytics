"""WebSocket cluster communication protocol for distributed Caelum MCP servers."""

import asyncio
import json
import uuid
import websockets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .machine_registry import machine_registry, MachineNode
from .port_registry import port_registry


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of cluster communication messages."""

    # Machine Discovery
    MACHINE_REGISTER = "machine_register"
    MACHINE_HEARTBEAT = "machine_heartbeat"
    MACHINE_DISCOVER = "machine_discover"
    MACHINE_UPDATE = "machine_update"

    # Task Coordination
    TASK_DISTRIBUTE = "task_distribute"
    TASK_ASSIGN = "task_assign"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"

    # Resource Management
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_AVAILABLE = "resource_available"
    RESOURCE_RESERVED = "resource_reserved"
    RESOURCE_RELEASED = "resource_released"

    # Service Discovery
    SERVICE_ANNOUNCE = "service_announce"
    SERVICE_QUERY = "service_query"
    SERVICE_RESPONSE = "service_response"

    # System Status
    STATUS_BROADCAST = "status_broadcast"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


@dataclass
class ClusterMessage:
    """Standard message format for cluster communication."""

    message_id: str
    message_type: MessageType
    source_machine: str
    target_machines: Optional[List[str]] = None  # None = broadcast to all
    timestamp: datetime = None
    payload: Dict[str, Any] = None
    correlation_id: Optional[str] = None  # For request/response pairing

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.payload is None:
            self.payload = {}

    def to_json(self) -> str:
        """Convert message to JSON string."""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "ClusterMessage":
        """Create message from JSON string."""
        data = json.loads(json_str)
        data["message_type"] = MessageType(data["message_type"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class TaskDistribution:
    """Information about a distributed task."""

    task_id: str
    task_type: str
    service_name: str  # Which MCP server handles this
    source_machine: str
    assigned_machines: List[str]
    payload: Dict[str, Any]
    priority: int = 5  # 1-10, higher = more priority
    estimated_duration: int = 60  # seconds
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class ResourceReservation:
    """Resource reservation for distributed tasks."""

    reservation_id: str
    machine_id: str
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    gpu_count: Optional[int] = None
    duration_seconds: int = 3600
    task_id: Optional[str] = None
    reserved_at: datetime = None

    def __post_init__(self):
        if self.reserved_at is None:
            self.reserved_at = datetime.now(timezone.utc)


class ClusterNode:
    """Represents a node in the Caelum cluster with WebSocket communication."""

    def __init__(self, port: int = 8080):
        self.port = port
        self.machine_id = None
        self.is_server = False
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.pending_tasks: Dict[str, TaskDistribution] = {}
        self.resource_reservations: Dict[str, ResourceReservation] = {}
        self.discovered_machines: Dict[str, MachineNode] = {}

        # Register default message handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default message handlers."""
        self.message_handlers.update(
            {
                MessageType.MACHINE_REGISTER: self._handle_machine_register,
                MessageType.MACHINE_HEARTBEAT: self._handle_machine_heartbeat,
                MessageType.MACHINE_DISCOVER: self._handle_machine_discover,
                MessageType.TASK_DISTRIBUTE: self._handle_task_distribute,
                MessageType.RESOURCE_REQUEST: self._handle_resource_request,
                MessageType.SERVICE_QUERY: self._handle_service_query,
                MessageType.PING: self._handle_ping,
            }
        )

    async def start_server(self, host: str = "0.0.0.0"):
        """Start the cluster communication server."""
        self.is_server = True

        # Get local machine info
        if machine_registry.local_machine_id is None:
            local_machine = machine_registry.get_local_machine_info()
            machine_registry.register_machine(local_machine)

        self.machine_id = machine_registry.local_machine_id

        logger.info(f"Starting cluster node server on {host}:{self.port}")

        async def handle_client(websocket):
            await self._handle_connection(websocket)

        # Start WebSocket server
        server = await websockets.serve(handle_client, host, self.port)
        logger.info(f"Cluster communication server started on ws://{host}:{self.port}")

        # Announce our presence to the network
        await self._announce_machine()

        return server

    async def connect_to_machine(self, host: str, port: int = None) -> bool:
        """Connect to another machine in the cluster."""
        if port is None:
            port = self.port

        try:
            uri = f"ws://{host}:{port}"
            websocket = await websockets.connect(uri)

            # Register this connection
            machine_id = f"remote-{host}-{port}"
            self.connections[machine_id] = websocket

            # Start listening for messages
            asyncio.create_task(self._listen_to_connection(websocket, machine_id))

            # Send machine registration
            await self._send_machine_register(websocket)

            logger.info(f"Connected to cluster node at {uri}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {host}:{port} - {e}")
            return False

    async def _handle_connection(self, websocket):
        """Handle incoming WebSocket connection."""
        machine_id = None
        try:
            async for message in websocket:
                try:
                    cluster_msg = ClusterMessage.from_json(message)

                    # Register the machine if this is a registration message
                    if cluster_msg.message_type == MessageType.MACHINE_REGISTER:
                        machine_id = cluster_msg.source_machine
                        self.connections[machine_id] = websocket

                    # Handle the message
                    await self._process_message(cluster_msg, websocket)

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for machine {machine_id}")
        finally:
            if machine_id and machine_id in self.connections:
                del self.connections[machine_id]

    async def _listen_to_connection(self, websocket, machine_id: str):
        """Listen for messages from a specific connection."""
        try:
            async for message in websocket:
                cluster_msg = ClusterMessage.from_json(message)
                await self._process_message(cluster_msg, websocket)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection to {machine_id} closed")
            if machine_id in self.connections:
                del self.connections[machine_id]

    async def _process_message(self, message: ClusterMessage, websocket):
        """Process incoming cluster message."""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            await handler(message, websocket)
        else:
            logger.warning(f"No handler for message type: {message.message_type}")

    async def broadcast_message(self, message: ClusterMessage):
        """Broadcast message to all connected machines."""
        message_json = message.to_json()

        # Send to all connections
        for machine_id, websocket in self.connections.items():
            try:
                await websocket.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Connection to {machine_id} closed during broadcast")
                # Remove closed connection
                del self.connections[machine_id]

    async def send_message_to_machine(
        self, machine_id: str, message: ClusterMessage
    ) -> bool:
        """Send message to a specific machine."""
        if machine_id not in self.connections:
            logger.warning(f"No connection to machine {machine_id}")
            return False

        try:
            await self.connections[machine_id].send(message.to_json())
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Connection to {machine_id} closed during send")
            del self.connections[machine_id]
            return False

    # Message Handlers

    async def _handle_machine_register(self, message: ClusterMessage, websocket):
        """Handle machine registration."""
        machine_data = message.payload.get("machine_info")
        if machine_data:
            try:
                machine = MachineNode.from_dict(machine_data)
                machine_registry.register_machine(machine)
                self.discovered_machines[machine.machine_id] = machine

                logger.info(
                    f"Registered machine: {machine.hostname} ({machine.machine_id})"
                )

                # Send our machine info back
                response = ClusterMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.MACHINE_UPDATE,
                    source_machine=self.machine_id,
                    target_machines=[message.source_machine],
                    payload={
                        "machine_info": machine_registry.machines[
                            self.machine_id
                        ].to_dict()
                    },
                )
                await websocket.send(response.to_json())

            except Exception as e:
                logger.error(f"Failed to register machine: {e}")

    async def _handle_machine_heartbeat(self, message: ClusterMessage, websocket):
        """Handle machine heartbeat."""
        machine_registry.update_machine_heartbeat(message.source_machine)

        # Update machine info if provided
        machine_data = message.payload.get("machine_info")
        if machine_data:
            try:
                machine = MachineNode.from_dict(machine_data)
                machine_registry.register_machine(machine)
                self.discovered_machines[machine.machine_id] = machine
            except Exception as e:
                logger.error(f"Failed to update machine info: {e}")

    async def _handle_machine_discover(self, message: ClusterMessage, websocket):
        """Handle machine discovery request."""
        # Send our machine info
        response = ClusterMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.MACHINE_UPDATE,
            source_machine=self.machine_id,
            target_machines=[message.source_machine],
            correlation_id=message.message_id,
            payload={
                "machine_info": machine_registry.machines[self.machine_id].to_dict(),
                "discovered_machines": [
                    m.to_dict() for m in self.discovered_machines.values()
                ],
            },
        )
        await websocket.send(response.to_json())

    async def _handle_task_distribute(self, message: ClusterMessage, websocket):
        """Handle task distribution request."""
        task_data = message.payload.get("task")
        if task_data:
            task = TaskDistribution(**task_data)
            self.pending_tasks[task.task_id] = task

            logger.info(f"Received distributed task: {task.task_type} ({task.task_id})")

            # Check if we can handle this task
            if await self._can_handle_task(task):
                # Accept the task
                response = ClusterMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.TASK_ASSIGN,
                    source_machine=self.machine_id,
                    target_machines=[message.source_machine],
                    correlation_id=message.message_id,
                    payload={
                        "task_id": task.task_id,
                        "status": "accepted",
                        "estimated_completion": (
                            datetime.now(timezone.utc)
                            + timedelta(seconds=task.estimated_duration)
                        ).isoformat(),
                    },
                )
                await websocket.send(response.to_json())

                # Start processing the task
                asyncio.create_task(self._process_distributed_task(task))

    async def _handle_resource_request(self, message: ClusterMessage, websocket):
        """Handle resource reservation request."""
        resource_req = message.payload.get("resource_request")
        if resource_req:
            # Check if we have the requested resources
            machine = machine_registry.machines.get(self.machine_id)
            if machine and await self._can_provide_resources(resource_req, machine):
                # Reserve the resources
                reservation = ResourceReservation(
                    reservation_id=str(uuid.uuid4()),
                    machine_id=self.machine_id,
                    **resource_req,
                )
                self.resource_reservations[reservation.reservation_id] = reservation

                response = ClusterMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.RESOURCE_RESERVED,
                    source_machine=self.machine_id,
                    target_machines=[message.source_machine],
                    correlation_id=message.message_id,
                    payload={
                        "reservation_id": reservation.reservation_id,
                        "machine_id": self.machine_id,
                        "resources": asdict(reservation),
                    },
                )
                await websocket.send(response.to_json())

    async def _handle_service_query(self, message: ClusterMessage, websocket):
        """Handle service location query."""
        service_name = message.payload.get("service_name")
        if service_name:
            location = port_registry.get_service_location(service_name)
            response = ClusterMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.SERVICE_RESPONSE,
                source_machine=self.machine_id,
                target_machines=[message.source_machine],
                correlation_id=message.message_id,
                payload={
                    "service_name": service_name,
                    "location": asdict(location) if location else None,
                },
            )
            await websocket.send(response.to_json())

    async def _handle_ping(self, message: ClusterMessage, websocket):
        """Handle ping message."""
        response = ClusterMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.PONG,
            source_machine=self.machine_id,
            target_machines=[message.source_machine],
            correlation_id=message.message_id,
            payload={"timestamp": datetime.now(timezone.utc).isoformat()},
        )
        await websocket.send(response.to_json())

    # Utility Methods

    async def _announce_machine(self):
        """Announce this machine to the cluster."""
        if self.machine_id:
            machine = machine_registry.machines[self.machine_id]
            message = ClusterMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.MACHINE_REGISTER,
                source_machine=self.machine_id,
                payload={"machine_info": machine.to_dict()},
            )
            await self.broadcast_message(message)

    async def _send_machine_register(self, websocket):
        """Send machine registration to a specific connection."""
        if self.machine_id:
            machine = machine_registry.machines[self.machine_id]
            message = ClusterMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.MACHINE_REGISTER,
                source_machine=self.machine_id,
                payload={"machine_info": machine.to_dict()},
            )
            await websocket.send(message.to_json())

    async def _can_handle_task(self, task: TaskDistribution) -> bool:
        """Check if this machine can handle the given task."""
        # Check if we have the required service
        machine = machine_registry.machines.get(self.machine_id)
        if not machine:
            return False

        # Check if the service is running on this machine
        for service in machine.running_services:
            if service["service_name"] == task.service_name:
                return True

        return False

    async def _can_provide_resources(
        self, resource_req: Dict, machine: MachineNode
    ) -> bool:
        """Check if this machine can provide the requested resources."""
        required_cpu = resource_req.get("cpu_cores", 0)
        required_memory = resource_req.get("memory_gb", 0)
        required_gpu = resource_req.get("gpu_count", 0)

        # Simple availability check (in production, would be more sophisticated)
        available_cpu = machine.resources.cpu_cores * (
            1 - machine.resources.cpu_usage_percent / 100
        )
        available_memory = machine.resources.memory_available_gb
        available_gpu = (
            len(machine.resources.gpu_info) if machine.resources.gpu_info else 0
        )

        return (
            available_cpu >= required_cpu
            and available_memory >= required_memory
            and available_gpu >= required_gpu
        )

    async def _process_distributed_task(self, task: TaskDistribution):
        """Process a distributed task based on its type."""
        logger.info(f"Processing distributed task: {task.task_type}")

        try:
            # Route task to appropriate handler based on task type
            if task.task_type == "code_analysis":
                result = await self._process_code_analysis_task(task)
            elif task.task_type == "integration_testing":
                result = await self._process_integration_testing_task(task)
            elif task.task_type == "ai_inference":
                result = await self._process_ai_inference_task(task)
            elif task.task_type == "data_processing":
                result = await self._process_data_processing_task(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            # Send completion message
            completion_message = ClusterMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.TASK_COMPLETE,
                source_machine=self.machine_id,
                payload={
                    "task_id": task.task_id,
                    "status": "completed",
                    "result": result,
                },
            )
            await self.broadcast_message(completion_message)

        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")

            # Send failure message
            failure_message = ClusterMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.TASK_FAILED,
                source_machine=self.machine_id,
                payload={"task_id": task.task_id, "status": "failed", "error": str(e)},
            )
            await self.broadcast_message(failure_message)

        finally:
            # Remove from pending tasks
            if task.task_id in self.pending_tasks:
                del self.pending_tasks[task.task_id]

    async def _process_code_analysis_task(
        self, task: TaskDistribution
    ) -> Dict[str, Any]:
        """Process a code analysis task."""
        from .distributed_code_analysis import distributed_analyzer, AnalysisType

        payload = task.payload
        chunk_data = payload.get("chunk", {})
        analysis_type = AnalysisType(payload.get("analysis_type", "static_analysis"))
        configuration = payload.get("configuration", {})

        # Import and reconstruct chunk
        from .distributed_code_analysis import CodeChunk

        chunk = CodeChunk(
            chunk_id=chunk_data.get("chunk_id"),
            file_paths=chunk_data.get("file_paths", []),
            total_lines=chunk_data.get("total_lines", 0),
            size_bytes=chunk_data.get("size_bytes", 0),
            file_types=chunk_data.get("file_types", []),
            complexity_estimate=chunk_data.get("complexity_estimate", 1),
        )

        # Process the chunk
        results = await distributed_analyzer._analyze_code_chunk(
            chunk, analysis_type, configuration
        )

        return {
            "task_type": "code_analysis",
            "chunk_id": chunk.chunk_id,
            "analysis_results": results,
            "processing_time": results.get("processing_time", 0),
        }

    async def _process_integration_testing_task(
        self, task: TaskDistribution
    ) -> Dict[str, Any]:
        """Process an integration testing task using Caelum Integration Testing MCP server."""
        import httpx
        import time
        from ..port_registry import port_registry

        payload = task.payload
        test_suite = payload.get("test_suite", [])
        test_config = payload.get("configuration", {})

        start_time = time.time()

        # Find Caelum Integration Testing MCP server
        testing_allocation = port_registry.get_service_location(
            "caelum-integration-testing"
        )
        if not testing_allocation:
            raise ValueError(
                "Caelum Integration Testing MCP server not found in port registry"
            )

        testing_url = f"http://{testing_allocation.ip_address or 'localhost'}:{testing_allocation.port}"

        try:
            # Prepare test execution request for Integration Testing MCP server
            testing_request = {
                "test_suite": test_suite,
                "configuration": test_config,
                "distributed_task_id": task.task_id,
                "parallel_execution": True,
                "timeout": test_config.get("timeout", 300),
            }

            async with httpx.AsyncClient(
                timeout=600.0
            ) as client:  # Longer timeout for tests
                # Send request to Integration Testing MCP server
                response = await client.post(
                    f"{testing_url}/mcp/execute-tests",
                    json=testing_request,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result_data = response.json()
                    execution_time = time.time() - start_time

                    return {
                        "task_type": "integration_testing",
                        "tests_run": result_data.get("tests_run", 0),
                        "tests_passed": result_data.get("tests_passed", 0),
                        "tests_failed": result_data.get("tests_failed", 0),
                        "test_results": result_data.get("test_results", []),
                        "execution_time": execution_time,
                        "status": "completed",
                        "mcp_server": "caelum-integration-testing",
                        "mcp_response": result_data,
                    }
                else:
                    raise ValueError(
                        f"Integration Testing MCP server error: {response.status_code} - {response.text}"
                    )

        except httpx.ConnectError:
            # Fallback: try to start or connect to the MCP server
            raise ValueError(
                f"Could not connect to Caelum Integration Testing MCP server at {testing_url}"
            )
        except Exception as e:
            return {
                "task_type": "integration_testing",
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "test_results": [],
                "execution_time": time.time() - start_time,
                "status": "failed",
                "error": f"MCP server communication failed: {str(e)}",
                "mcp_server": "caelum-integration-testing",
            }

    async def _process_ai_inference_task(
        self, task: TaskDistribution
    ) -> Dict[str, Any]:
        """Process an AI inference task using local Ollama pool."""
        import httpx
        from ..port_registry import port_registry

        payload = task.payload
        model_name = payload.get("model_name", "default")
        input_data = payload.get("input_data", {})
        inference_config = payload.get("configuration", {})

        # Find Ollama pool MCP server
        ollama_allocation = port_registry.get_service_location("caelum-ollama-pool")
        if not ollama_allocation:
            raise ValueError("Ollama pool MCP server not found in port registry")

        ollama_url = f"http://{ollama_allocation.ip_address or 'localhost'}:{ollama_allocation.port}"

        start_time = time.time()

        try:
            # Prepare inference request for Ollama
            inference_request = {
                "model": model_name,
                "prompt": input_data.get("prompt", ""),
                "system": input_data.get("system", ""),
                "context": input_data.get("context", []),
                "options": inference_config,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Send request to Ollama pool
                response = await client.post(
                    f"{ollama_url}/api/generate", json=inference_request
                )

                if response.status_code == 200:
                    result_data = response.json()
                    inference_time = time.time() - start_time

                    return {
                        "task_type": "ai_inference",
                        "model_name": model_name,
                        "input_processed": True,
                        "inference_time": inference_time,
                        "result": {
                            "status": "completed",
                            "output": result_data.get("response", ""),
                            "context": result_data.get("context", []),
                            "total_duration": result_data.get("total_duration", 0),
                            "load_duration": result_data.get("load_duration", 0),
                            "prompt_eval_count": result_data.get(
                                "prompt_eval_count", 0
                            ),
                            "eval_count": result_data.get("eval_count", 0),
                        },
                    }
                else:
                    raise ValueError(
                        f"Ollama API error: {response.status_code} - {response.text}"
                    )

        except Exception as e:
            return {
                "task_type": "ai_inference",
                "model_name": model_name,
                "input_processed": False,
                "inference_time": time.time() - start_time,
                "result": {"status": "failed", "error": str(e)},
            }

    async def _process_data_processing_task(
        self, task: TaskDistribution
    ) -> Dict[str, Any]:
        """Process a data processing task using Caelum Analytics MCP server."""
        import httpx
        import time
        from ..port_registry import port_registry

        payload = task.payload
        data_source = payload.get("data_source", "")
        processing_type = payload.get("processing_type", "transform")
        config = payload.get("configuration", {})

        start_time = time.time()

        # Find Caelum Analytics Metrics MCP server
        analytics_allocation = port_registry.get_service_location(
            "caelum-analytics-metrics"
        )
        if not analytics_allocation:
            raise ValueError(
                "Caelum Analytics Metrics MCP server not found in port registry"
            )

        analytics_url = f"http://{analytics_allocation.ip_address or 'localhost'}:{analytics_allocation.port}"

        try:
            # Prepare data processing request for Analytics MCP server
            processing_request = {
                "data_source": data_source,
                "processing_type": processing_type,
                "configuration": config,
                "distributed_task_id": task.task_id,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Send request to Analytics MCP server
                response = await client.post(
                    f"{analytics_url}/mcp/data-processing",
                    json=processing_request,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result_data = response.json()
                    processing_time = time.time() - start_time

                    return {
                        "task_type": "data_processing",
                        "processing_type": processing_type,
                        "data_source": data_source,
                        "records_processed": result_data.get("records_processed", 0),
                        "records_output": result_data.get("records_output", 0),
                        "processing_time": processing_time,
                        "status": "completed",
                        "output_path": result_data.get("output_path"),
                        "mcp_server": "caelum-analytics-metrics",
                        "mcp_response": result_data,
                    }
                else:
                    raise ValueError(
                        f"Analytics MCP server error: {response.status_code} - {response.text}"
                    )

        except httpx.ConnectError:
            # Fallback: try to start or connect to the MCP server
            raise ValueError(
                f"Could not connect to Caelum Analytics MCP server at {analytics_url}"
            )
        except Exception as e:
            return {
                "task_type": "data_processing",
                "processing_type": processing_type,
                "data_source": data_source,
                "records_processed": 0,
                "processing_time": time.time() - start_time,
                "status": "failed",
                "error": f"MCP server communication failed: {str(e)}",
                "mcp_server": "caelum-analytics-metrics",
            }


# Global cluster node instance
cluster_node = ClusterNode(port=8080)
