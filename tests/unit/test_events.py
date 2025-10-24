import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

import asyncio
from unittest.mock import patch, MagicMock
from app.events.domain import ChargeStartedEvent, ChargeStoppedEvent, WalletCreditedEvent
from app.events.bus import EventBus
from app.workers.outbox_relay import OutboxRelay

class TestEventBus:
    
    @pytest.fixture
    def event_bus(self):
        return EventBus()
    
    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_bus):
        """Test publishing and subscribing to events"""
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        # Subscribe to events
        event_bus.subscribe("charge_started", handler)
        
        # Create and publish event
        event = ChargeStartedEvent(
            session_id="test-123",
            user_id="user-456",
            hub_id="hub-789",
            started_at="2024-01-01T12:00:00Z"
        )
        
        await event_bus.publish(event)
        
        # Wait for async processing
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0].session_id == "test-123"
        assert received_events[0].user_id == "user-456"
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus):
        """Test multiple subscribers for the same event"""
        received_events_1 = []
        received_events_2 = []
        
        async def handler1(event):
            received_events_1.append(event)
        
        async def handler2(event):
            received_events_2.append(event)
        
        # Subscribe multiple handlers
        event_bus.subscribe("charge_started", handler1)
        event_bus.subscribe("charge_started", handler2)
        
        # Create and publish event
        event = ChargeStartedEvent(
            session_id="test-123",
            user_id="user-456",
            hub_id="hub-789",
            started_at="2024-01-01T12:00:00Z"
        )
        
        await event_bus.publish(event)
        
        # Wait for async processing
        await asyncio.sleep(0.1)
        
        assert len(received_events_1) == 1
        assert len(received_events_2) == 1
    
    @pytest.mark.asyncio
    async def test_event_history(self, event_bus):
        """Test that events are stored in history"""
        event = ChargeStartedEvent(
            session_id="test-123",
            user_id="user-456",
            hub_id="hub-789",
            started_at="2024-01-01T12:00:00Z"
        )
        
        await event_bus.publish(event)
        
        # Check history
        events = event_bus.get_events()
        assert len(events) == 1
        assert events[0].session_id == "test-123"
    
    @pytest.mark.asyncio
    async def test_event_filtering(self, event_bus):
        """Test filtering events by type and aggregate ID"""
        # Publish different types of events
        charge_event = ChargeStartedEvent(
            session_id="test-123",
            user_id="user-456",
            hub_id="hub-789",
            started_at="2024-01-01T12:00:00Z"
        )
        
        wallet_event = WalletCreditedEvent(
            user_id="user-456",
            amount_cents=100,
            session_id="test-123",
            new_balance_cents=500,
            credited_at="2024-01-01T12:00:00Z"
        )
        
        await event_bus.publish(charge_event)
        await event_bus.publish(wallet_event)
        
        # Filter by event type
        charge_events = event_bus.get_events(event_type="charge_started")
        assert len(charge_events) == 1
        assert charge_events[0].session_id == "test-123"
        
        # Filter by aggregate ID
        user_events = event_bus.get_events(aggregate_id="user-456")
        assert len(user_events) == 2  # Both events have user-456 as aggregate_id

class TestOutboxRelay:
    
    @pytest.fixture
    def outbox_relay(self):
        return OutboxRelay(poll_interval=1)
    
    @pytest.mark.asyncio
    async def test_outbox_relay_lifecycle(self, outbox_relay):
        """Test starting and stopping the outbox relay"""
        # Start relay
        await outbox_relay.start()
        assert outbox_relay.running is True
        
        # Stop relay
        await outbox_relay.stop()
        assert outbox_relay.running is False
    
    @pytest.mark.asyncio
    async def test_get_outbox_stats(self, outbox_relay):
        """Test getting outbox statistics"""
        with patch('app.workers.outbox_relay.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock database results
            mock_db.execute.return_value.scalar.return_value = 10
            mock_db.execute.return_value.__iter__.return_value = [
                MagicMock(event_type="charge_started", count=5),
                MagicMock(event_type="charge_stopped", count=3),
                MagicMock(event_type="wallet_credited", count=2)
            ]
            
            stats = await outbox_relay.get_outbox_stats()
            
            assert stats["total_events"] == 10
            assert stats["unprocessed_events"] == 10
            assert stats["processed_events"] == 0
            assert "charge_started" in stats["events_by_type"]
    
    @pytest.mark.asyncio
    async def test_process_outbox_events(self, outbox_relay):
        """Test processing outbox events"""
        with patch('app.workers.outbox_relay.get_db') as mock_get_db, \
             patch('app.workers.outbox_relay.event_bus') as mock_event_bus:
            
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock unprocessed events
            mock_event = {
                "id": 1,
                "event_type": "charge_started",
                "payload_json": '{"session_id": "test-123", "user_id": "user-456"}',
                "created_at": "2024-01-01T12:00:00Z"
            }
            
            mock_db.execute.return_value = [mock_event]
            
            # Mock event bus
            mock_event_bus.publish = MagicMock()
            
            # Process events
            await outbox_relay._process_outbox_events()
            
            # Verify event was published
            mock_event_bus.publish.assert_called_once()
            
            # Verify event was marked as processed
            mock_db.execute.assert_called()
            mock_db.commit.assert_called_once()
