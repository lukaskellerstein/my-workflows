"""
Example 4: Dynamic Signal and Query Handlers
This demonstrates how to register signal and query handlers dynamically at runtime,
allowing workflows to adapt their message handling based on configuration.
"""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, List, Optional

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


# Activities for processing signals
@activity.defn
async def process_signal_data(signal_type: str, data: Dict[str, Any]) -> str:
    activity.logger.info(f"Processing signal {signal_type}: {data}")
    return f"Processed {signal_type}"


@dataclass
class SignalConfig:
    """Configuration for dynamic signal handlers"""

    signal_name: str
    handler_type: str  # "store", "process", "trigger"
    process_immediately: bool = False


@dataclass
class WorkflowState:
    """Internal workflow state"""

    active: bool = True
    signals_received: List[Dict[str, Any]] = field(default_factory=list)
    queries_count: Dict[str, int] = field(default_factory=dict)
    data_store: Dict[str, Any] = field(default_factory=dict)


# Workflow with dynamic signal and query handlers
@workflow.defn
class DynamicSignalQueryWorkflow:
    def __init__(self):
        self.state = WorkflowState()
        self.registered_signals: Dict[str, SignalConfig] = {}
        self.registered_queries: List[str] = []

    @workflow.run
    async def run(
        self,
        signal_configs: List[SignalConfig],
        query_configs: List[str],
        duration_seconds: int = 60,
    ) -> Dict[str, Any]:
        """
        Run a workflow with dynamically configured signals and queries.

        Args:
            signal_configs: List of signal configurations to register
            query_configs: List of query names to register
            duration_seconds: How long the workflow should run
        """
        workflow.logger.info(
            f"Starting dynamic workflow with {len(signal_configs)} signals "
            f"and {len(query_configs)} queries"
        )

        # Dynamically register signal handlers
        for config in signal_configs:
            self._register_signal_handler(config)

        # Dynamically register query handlers
        for query_name in query_configs:
            self._register_query_handler(query_name)

        workflow.logger.info("All handlers registered")

        # Wait for the specified duration or until workflow is stopped
        try:
            await workflow.wait_condition(
                lambda: not self.state.active,
                timeout=timedelta(seconds=duration_seconds),
            )
        except asyncio.TimeoutError:
            workflow.logger.info(f"Workflow completed after {duration_seconds}s")

        return {
            "signals_received": len(self.state.signals_received),
            "signals_detail": self.state.signals_received,
            "queries_executed": self.state.queries_count,
            "data_store": self.state.data_store,
            "registered_signals": list(self.registered_signals.keys()),
            "registered_queries": self.registered_queries,
        }

    def _register_signal_handler(self, config: SignalConfig):
        """Register signal configuration (handlers are defined at class level)"""
        workflow.logger.info(f"Registering signal handler: {config.signal_name}")
        self.registered_signals[config.signal_name] = config

    # Static signal handlers that dispatch dynamically
    @workflow.signal
    async def update_data(self, data: Dict[str, Any]):
        """Signal handler for update_data"""
        self._handle_signal("update_data", data)

    @workflow.signal
    async def add_item(self, data: Dict[str, Any]):
        """Signal handler for add_item"""
        self._handle_signal("add_item", data)

    @workflow.signal
    async def complete(self, data: Dict[str, Any]):
        """Signal handler for complete"""
        self._handle_signal("complete", data)

    def _handle_signal(self, signal_name: str, data: Dict[str, Any]):
        """Handle signal based on registered configuration"""
        workflow.logger.info(f"Signal received [{signal_name}]: {data}")

        config = self.registered_signals.get(signal_name)
        if not config:
            workflow.logger.warning(f"No configuration for signal: {signal_name}")
            return

        self.state.signals_received.append(
            {"signal": signal_name, "data": data}
        )

        if config.handler_type == "store":
            self.state.data_store[signal_name] = data
        elif config.handler_type == "trigger":
            self.state.active = False

    def _register_query_handler(self, query_name: str):
        """Register query configuration (handlers are defined at class level)"""
        workflow.logger.info(f"Registering query handler: {query_name}")
        self.registered_queries.append(query_name)

    # Static query handlers
    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Query handler for get_status"""
        self.state.queries_count["get_status"] = (
            self.state.queries_count.get("get_status", 0) + 1
        )
        return {
            "active": self.state.active,
            "signals_received": len(self.state.signals_received),
        }

    @workflow.query
    def get_data(self) -> Dict[str, Any]:
        """Query handler for get_data"""
        self.state.queries_count["get_data"] = (
            self.state.queries_count.get("get_data", 0) + 1
        )
        return self.state.data_store

    @workflow.query
    def get_signals(self) -> List[Dict[str, Any]]:
        """Query handler for get_signals"""
        self.state.queries_count["get_signals"] = (
            self.state.queries_count.get("get_signals", 0) + 1
        )
        return self.state.signals_received


# Advanced example: Plugin-based workflow
@dataclass
class PluginConfig:
    """Configuration for workflow plugins"""

    name: str
    signals: List[str]
    queries: List[str]
    handlers: Dict[str, str]  # signal/query name -> handler type


@workflow.defn
class PluginBasedWorkflow:
    def __init__(self):
        self.state = WorkflowState()
        self.plugins: Dict[str, PluginConfig] = {}
        self.plugin_data: Dict[str, Dict[str, Any]] = {}

    @workflow.run
    async def run(
        self,
        plugin_configs: List[PluginConfig],
        duration_seconds: int = 60,
    ) -> Dict[str, Any]:
        """
        Run a workflow with plugin-based dynamic handlers.

        Args:
            plugin_configs: List of plugin configurations
            duration_seconds: How long the workflow should run
        """
        workflow.logger.info(f"Starting plugin-based workflow with {len(plugin_configs)} plugins")

        # Load plugins dynamically
        for plugin_config in plugin_configs:
            self._load_plugin(plugin_config)

        workflow.logger.info("All plugins loaded")

        # Wait for the specified duration or until workflow is stopped
        try:
            await workflow.wait_condition(
                lambda: not self.state.active,
                timeout=timedelta(seconds=duration_seconds),
            )
        except asyncio.TimeoutError:
            workflow.logger.info(f"Workflow completed after {duration_seconds}s")

        return {
            "plugins_loaded": list(self.plugins.keys()),
            "signals_received": len(self.state.signals_received),
            "plugin_data": self.plugin_data,
            "queries_executed": self.state.queries_count,
        }

    def _load_plugin(self, config: PluginConfig):
        """Dynamically load a plugin with its handlers"""

        workflow.logger.info(f"Loading plugin: {config.name}")
        self.plugins[config.name] = config
        self.plugin_data[config.name] = {}

        # Register plugin signals
        for signal_name in config.signals:
            handler_type = config.handlers.get(signal_name, "store")
            self._register_plugin_signal(config.name, signal_name, handler_type)

        # Register plugin queries
        for query_name in config.queries:
            self._register_plugin_query(config.name, query_name)

    def _register_plugin_signal(
        self, plugin_name: str, signal_name: str, handler_type: str
    ):
        """Register plugin signal configuration"""
        workflow.logger.info(
            f"Plugin {plugin_name}: Registering signal {signal_name}"
        )
        # Store the configuration for runtime dispatching
        if not hasattr(self, "_plugin_signal_configs"):
            self._plugin_signal_configs = {}
        self._plugin_signal_configs[f"{plugin_name}_{signal_name}"] = {
            "plugin_name": plugin_name,
            "signal_name": signal_name,
            "handler_type": handler_type,
        }

    # Predefined signal handlers for plugins
    @workflow.signal
    async def analytics_track_event(self, data: Dict[str, Any]):
        """Signal handler for analytics_track_event"""
        self._handle_plugin_signal("analytics", "track_event", data, "store")

    @workflow.signal
    async def analytics_update_metrics(self, data: Dict[str, Any]):
        """Signal handler for analytics_update_metrics"""
        self._handle_plugin_signal("analytics", "update_metrics", data, "store")

    @workflow.signal
    async def notifications_send_email(self, data: Dict[str, Any]):
        """Signal handler for notifications_send_email"""
        self._handle_plugin_signal("notifications", "send_email", data, "store")

    @workflow.signal
    async def notifications_send_sms(self, data: Dict[str, Any]):
        """Signal handler for notifications_send_sms"""
        self._handle_plugin_signal("notifications", "send_sms", data, "store")

    @workflow.signal
    async def control_shutdown(self, data: Dict[str, Any]):
        """Signal handler for control_shutdown"""
        self._handle_plugin_signal("control", "shutdown", data, "trigger")

    def _handle_plugin_signal(
        self, plugin_name: str, signal_name: str, data: Dict[str, Any], handler_type: str
    ):
        """Handle plugin signal"""
        workflow.logger.info(
            f"Plugin {plugin_name} signal [{signal_name}]: {data}"
        )
        self.state.signals_received.append(
            {
                "plugin": plugin_name,
                "signal": signal_name,
                "data": data,
            }
        )
        # Store data in plugin-specific namespace
        if plugin_name not in self.plugin_data:
            self.plugin_data[plugin_name] = {}
        self.plugin_data[plugin_name][signal_name] = data

        if handler_type == "trigger":
            self.state.active = False

    def _register_plugin_query(self, plugin_name: str, query_name: str):
        """Register plugin query configuration"""
        workflow.logger.info(
            f"Plugin {plugin_name}: Registering query {query_name}"
        )

    # Predefined query handlers for plugins
    @workflow.query
    def analytics_get_data(self) -> Dict[str, Any]:
        """Query handler for analytics_get_data"""
        query_key = "analytics_get_data"
        self.state.queries_count[query_key] = (
            self.state.queries_count.get(query_key, 0) + 1
        )
        return self.plugin_data.get("analytics", {})

    @workflow.query
    def notifications_get_data(self) -> Dict[str, Any]:
        """Query handler for notifications_get_data"""
        query_key = "notifications_get_data"
        self.state.queries_count[query_key] = (
            self.state.queries_count.get(query_key, 0) + 1
        )
        return self.plugin_data.get("notifications", {})

    @workflow.query
    def control_get_data(self) -> Dict[str, Any]:
        """Query handler for control_get_data"""
        query_key = "control_get_data"
        self.state.queries_count[query_key] = (
            self.state.queries_count.get(query_key, 0) + 1
        )
        return self.plugin_data.get("control", {})


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker
    async with Worker(
        client,
        task_queue="3-advanced-dynamic-signals-task-queue",
        workflows=[DynamicSignalQueryWorkflow, PluginBasedWorkflow],
        activities=[process_signal_data],
        activity_executor=ThreadPoolExecutor(5),
    ):
        # Example 1: Dynamic signal and query handlers
        print("\n" + "=" * 60)
        print("Example 1: Dynamic Signal and Query Handlers")
        print("=" * 60)

        signal_configs = [
            SignalConfig(
                signal_name="update_data",
                handler_type="store",
                process_immediately=False,
            ),
            SignalConfig(
                signal_name="add_item",
                handler_type="store",
                process_immediately=False,
            ),
            SignalConfig(
                signal_name="complete",
                handler_type="trigger",
                process_immediately=True,
            ),
        ]

        query_configs = ["get_status", "get_data", "get_signals"]

        # Start workflow
        handle = await client.start_workflow(
            DynamicSignalQueryWorkflow.run,
            args=[signal_configs, query_configs, 30],
            id=f"3-advanced-dynamic-signals-example-1-{uuid.uuid4()}",
            task_queue="3-advanced-dynamic-signals-task-queue",
        )

        # Send signals dynamically
        await asyncio.sleep(1)
        await handle.signal("update_data", {"key": "value1", "timestamp": "2024-01-01"})

        await asyncio.sleep(1)
        await handle.signal("add_item", {"item": "item1", "quantity": 5})

        # Query workflow state
        await asyncio.sleep(1)
        status = await handle.query("get_status")
        print(f"\nWorkflow status: {status}")

        data = await handle.query("get_data")
        print(f"Workflow data: {data}")

        # Send completion signal
        await handle.signal("complete", {"reason": "manual_completion"})

        # Wait for workflow to complete
        result = await handle.result()

        print(f"\nResult 1:")
        print(f"  Signals received: {result['signals_received']}")
        print(f"  Registered signals: {result['registered_signals']}")
        print(f"  Registered queries: {result['registered_queries']}")
        print(f"  Queries executed: {result['queries_executed']}")
        print(f"  Signal details:")
        for signal in result["signals_detail"]:
            print(f"    - {signal['signal']}: {signal['data']}")

        # Example 2: Plugin-based workflow
        print("\n" + "=" * 60)
        print("Example 2: Plugin-Based Dynamic Workflow")
        print("=" * 60)

        plugin_configs = [
            PluginConfig(
                name="analytics",
                signals=["track_event", "update_metrics"],
                queries=["get_data"],
                handlers={"track_event": "store", "update_metrics": "store"},
            ),
            PluginConfig(
                name="notifications",
                signals=["send_email", "send_sms"],
                queries=["get_data"],
                handlers={"send_email": "store", "send_sms": "store"},
            ),
            PluginConfig(
                name="control",
                signals=["shutdown"],
                queries=["get_data"],
                handlers={"shutdown": "trigger"},
            ),
        ]

        # Start workflow
        handle2 = await client.start_workflow(
            PluginBasedWorkflow.run,
            args=[plugin_configs, 30],
            id=f"3-advanced-dynamic-signals-example-2-{uuid.uuid4()}",
            task_queue="3-advanced-dynamic-signals-task-queue",
        )

        # Send signals to different plugins
        await asyncio.sleep(1)
        await handle2.signal("analytics_track_event", {"event": "user_login", "user_id": 123})

        await asyncio.sleep(1)
        await handle2.signal("notifications_send_email", {"to": "user@example.com", "subject": "Welcome"})

        await asyncio.sleep(1)
        await handle2.signal("analytics_update_metrics", {"metric": "active_users", "value": 1500})

        # Query plugin data
        await asyncio.sleep(1)
        analytics_data = await handle2.query("analytics_get_data")
        print(f"\nAnalytics plugin data: {analytics_data}")

        notifications_data = await handle2.query("notifications_get_data")
        print(f"Notifications plugin data: {notifications_data}")

        # Shutdown workflow via control plugin
        await handle2.signal("control_shutdown", {"reason": "graceful_shutdown"})

        # Wait for workflow to complete
        result2 = await handle2.result()

        print(f"\nResult 2:")
        print(f"  Plugins loaded: {result2['plugins_loaded']}")
        print(f"  Signals received: {result2['signals_received']}")
        print(f"  Queries executed: {result2['queries_executed']}")
        print(f"  Plugin data:")
        for plugin_name, data in result2["plugin_data"].items():
            print(f"    - {plugin_name}: {data}")


if __name__ == "__main__":
    asyncio.run(main())
