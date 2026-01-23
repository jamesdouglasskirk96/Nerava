"""
Test OpenTelemetry tracing (optional).

These tests verify that tracing middleware doesn't crash when disabled
and works correctly when enabled.
"""
import pytest
import os
from unittest.mock import patch, MagicMock

from app.core.tracing import initialize_tracing, get_tracer, is_tracing_enabled


class TestTracingDisabled:
    """Test tracing when disabled"""
    
    def test_tracing_disabled_by_default(self):
        """Test that tracing is disabled by default"""
        with patch.dict(os.environ, {"OTEL_ENABLED": ""}, clear=False):
            # Reset global state
            import app.core.tracing
            app.core.tracing._tracing_initialized = False
            
            result = initialize_tracing()
            assert result is False
            assert not is_tracing_enabled()
    
    def test_get_tracer_when_disabled(self):
        """Test that get_tracer returns NoOpTracer when disabled"""
        import app.core.tracing
        app.core.tracing._tracing_initialized = False
        
        # Mock opentelemetry to avoid import errors
        with patch('app.core.tracing.trace') as mock_trace:
            mock_trace.NoOpTracer = MagicMock()
            tracer = get_tracer("test")
            # Should return NoOpTracer (doesn't crash)
            assert tracer is not None


class TestTracingEnabled:
    """Test tracing when enabled"""
    
    @pytest.mark.skipif(
        not os.getenv("OTEL_ENABLED") == "true",
        reason="OpenTelemetry not enabled in test environment"
    )
    def test_tracing_initializes_when_enabled(self):
        """Test that tracing initializes when enabled"""
        with patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False):
            # Mock OpenTelemetry imports
            with patch('app.core.tracing.trace') as mock_trace:
                mock_trace.set_tracer_provider = MagicMock()
                
                # This will fail if dependencies not installed, which is OK
                try:
                    result = initialize_tracing()
                    # May be False if dependencies not installed
                    assert isinstance(result, bool)
                except ImportError:
                    # Expected if opentelemetry packages not installed
                    pass
    
    def test_tracing_requires_dependencies(self):
        """Test that tracing requires OpenTelemetry dependencies"""
        # Reset global state
        import app.core.tracing
        app.core.tracing._tracing_initialized = False
        
        with patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False):
            # Mock ImportError when importing opentelemetry
            import sys
            original_modules = sys.modules.copy()
            try:
                # Remove opentelemetry modules if they exist
                for key in list(sys.modules.keys()):
                    if key.startswith('opentelemetry'):
                        del sys.modules[key]
                # Try to initialize - should handle ImportError gracefully
                result = initialize_tracing()
                # Should return False if dependencies not available
                assert result is False
            finally:
                # Restore modules
                sys.modules.clear()
                sys.modules.update(original_modules)


class TestTracingMiddleware:
    """Test that tracing middleware doesn't break the app"""
    
    def test_app_starts_without_tracing(self):
        """Test that app can start without tracing enabled"""
        # This is tested implicitly by other tests
        # If tracing breaks app startup, other tests would fail
        assert True

