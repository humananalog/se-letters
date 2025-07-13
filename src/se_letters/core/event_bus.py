"""Event bus for loose coupling between pipeline components."""

from typing import Dict, List, Callable, Any
import asyncio
from collections import defaultdict

from .interfaces import IEventBus


class EventBus(IEventBus):
    """Simple event bus for component communication."""
    
    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._async_subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event synchronously.
        
        Args:
            event_type: Type of event to publish
            data: Event data
        """
        # Call synchronous subscribers
        for handler in self._subscribers[event_type]:
            try:
                handler(data)
            except Exception as e:
                print(f"Error in event handler for {event_type}: {e}")
    
    async def publish_async(
        self, event_type: str, data: Dict[str, Any]
    ) -> None:
        """Publish an event asynchronously.
        
        Args:
            event_type: Type of event to publish
            data: Event data
        """
        # Call synchronous subscribers
        self.publish(event_type, data)
        
        # Call asynchronous subscribers
        tasks = []
        for handler in self._async_subscribers[event_type]:
            try:
                task = asyncio.create_task(handler(data))
                tasks.append(task)
            except Exception as e:
                print(f"Error creating async task for {event_type}: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Handler function to call
        """
        if asyncio.iscoroutinefunction(handler):
            self._async_subscribers[event_type].append(handler)
        else:
            self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
        
        if handler in self._async_subscribers[event_type]:
            self._async_subscribers[event_type].remove(handler)
    
    def clear_subscribers(self, event_type: str = None) -> None:
        """Clear subscribers for an event type or all events.
        
        Args:
            event_type: Event type to clear, or None for all
        """
        if event_type:
            self._subscribers[event_type].clear()
            self._async_subscribers[event_type].clear()
        else:
            self._subscribers.clear()
            self._async_subscribers.clear()
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get the number of subscribers for an event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            Number of subscribers
        """
        return (
            len(self._subscribers[event_type]) +
            len(self._async_subscribers[event_type])
        )
    
    def get_event_types(self) -> List[str]:
        """Get all registered event types.
        
        Returns:
            List of event types
        """
        all_types = set()
        all_types.update(self._subscribers.keys())
        all_types.update(self._async_subscribers.keys())
        return list(all_types)


# Common event types
class EventTypes:
    """Common event types for the pipeline."""
    
    # Document processing events
    DOCUMENT_LOADED = "document.loaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_ERROR = "document.error"
    
    # Metadata extraction events
    METADATA_EXTRACTED = "metadata.extracted"
    METADATA_ERROR = "metadata.error"
    
    # Product matching events
    PRODUCTS_MATCHED = "products.matched"
    MATCHING_ERROR = "matching.error"
    
    # Pipeline events
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_STAGE_COMPLETED = "pipeline.stage.completed"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_ERROR = "pipeline.error"
    
    # Report generation events
    REPORT_GENERATED = "report.generated"
    REPORT_ERROR = "report.error" 