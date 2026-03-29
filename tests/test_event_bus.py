"""Tests for Event Bus"""

import pytest

from orchestration.event_bus import (
    CacheEvents,
    Event,
    EventBus,
    EventPriority,
    PipelineEvents,
    Subscriber,
)


class TestEvent:
    """Test Event"""

    def test_creation(self):
        """Test creation"""
        event = Event(
            event_type="test.event",
            data={"key": "value"},
            source="test",
        )
        assert event.event_type == "test.event"
        assert event.data["key"] == "value"
        assert event.timestamp != ""


class TestSubscriber:
    """Test Subscriber"""

    def test_creation(self):
        """Test creation"""
        def handler(e):
            return "handled"

        sub = Subscriber(handler, ["event1", "event2"], EventPriority.HIGH)
        assert sub.handler is not None
        assert "event1" in sub.event_types
        assert sub.priority == EventPriority.HIGH

    def test_matches(self):
        """Test matches"""
        def handler(e):
            return "handled"

        sub = Subscriber(handler, ["event1", "event2"])
        assert sub.matches("event1") is True
        assert sub.matches("event2") is True
        assert sub.matches("event3") is False

    def test_matches_all(self):
        """Test matches all"""
        def handler(e):
            return "handled"

        sub = Subscriber(handler)  # No event types = all
        assert sub.matches("any_event") is True


class TestEventBus:
    """Test EventBus"""

    @pytest.fixture
    def bus(self):
        """Create event bus"""
        return EventBus()

    def test_bus_init(self, bus):
        """Test init"""
        assert bus._running is False
        assert len(bus._subscribers) == 0

    def test_subscribe(self, bus):
        """Test subscribe"""
        def handler(e):
            return "handled"

        sub = bus.subscribe(handler, ["test.event"])
        assert sub is not None
        assert len(bus._subscribers) == 1

    def test_subscribe_priority(self, bus):
        """Test subscribe with priority"""
        def handler1(e):
            return "low"

        def handler2(e):
            return "high"

        bus.subscribe(handler1, ["test"], EventPriority.LOW)
        sub2 = bus.subscribe(handler2, ["test"], EventPriority.HIGH)

        # High priority should be first
        assert bus._subscribers[0] is sub2

    def test_unsubscribe(self, bus):
        """Test unsubscribe"""
        def handler(e):
            return "handled"

        sub = bus.subscribe(handler, ["test.event"])
        assert len(bus._subscribers) == 1

        bus.unsubscribe(sub)
        assert len(bus._subscribers) == 0

    @pytest.mark.asyncio
    async def test_publish(self, bus):
        """Test publish"""
        results = []

        async def handler(event):
            results.append(event.data)

        bus.subscribe(handler, ["test.event"])

        event = Event(event_type="test.event", data={"value": 1})
        await bus.publish(event)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_publish_multiple_subscribers(self, bus):
        """Test multiple subscribers"""
        results = []

        async def handler1(event):
            results.append(f"handler1:{event.data}")

        async def handler2(event):
            results.append(f"handler2:{event.data}")

        bus.subscribe(handler1, ["test.event"])
        bus.subscribe(handler2, ["test.event"])

        event = Event(event_type="test.event", data={"value": 1})
        await bus.publish(event)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_start_stop(self, bus):
        """Test start and stop"""
        await bus.start()
        assert bus._running is True

        await bus.stop()
        assert bus._running is False

    def test_get_subscriber_count(self, bus):
        """Test get subscriber count"""
        def handler(e):
            return "handled"

        bus.subscribe(handler, ["e1"])
        bus.subscribe(handler, ["e2"])
        bus.subscribe(handler, ["e3"])

        assert bus.get_subscriber_count() == 3


class TestEventTypes:
    """Test event types"""

    def test_pipeline_events(self):
        """Test pipeline events"""
        assert PipelineEvents.PHASE_STARTED == "pipeline.phase.started"
        assert PipelineEvents.PIPELINE_STARTED == "pipeline.started"

    def test_cache_events(self):
        """Test cache events"""
        assert CacheEvents.CACHE_HIT == "cache.hit"
        assert CacheEvents.CACHE_MISS == "cache.miss"
