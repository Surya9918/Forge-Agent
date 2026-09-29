"""
Central Event Bus for ForgeAgent decoupling agents, UI, logging, and notifications.
"""

from typing import Callable, List, Dict
from collections import defaultdict
from forgeagent.events.events import ForgeEvent, EventType
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.events")


class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[ForgeEvent], None]]] = defaultdict(list)
        self._global_subscribers: List[Callable[[ForgeEvent], None]] = []
        self._event_history: List[ForgeEvent] = []

    def subscribe(self, event_type: EventType, callback: Callable[[ForgeEvent], None]) -> None:
        self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[ForgeEvent], None]) -> None:
        self._global_subscribers.append(callback)

    def emit(self, event: ForgeEvent) -> None:
        self._event_history.append(event)
        logger.info(
            f"Event [{event.event_type.value}] {event.message}",
            extra={"extra_data": event.payload, "task_id": event.task_id}
        )

        for callback in self._global_subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Global subscriber failed on event {event.event_type}: {e}")

        for callback in self._subscribers.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Subscriber failed on event {event.event_type}: {e}")

    def get_history(self) -> List[ForgeEvent]:
        return list(self._event_history)

    def clear(self) -> None:
        self._event_history.clear()


# Global shared bus instance
bus = EventBus()
