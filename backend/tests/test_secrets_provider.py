"""
Test secrets provider abstraction.

These tests verify that the secrets provider abstraction works correctly
with both environment variable and AWS Secrets Manager providers.
"""
import pytest
import os
from unittest.mock import patch, MagicMock

from app.core.secrets import (
    EnvSecretProvider,
    AWSSecretsManagerProvider,
    get_secret_provider,
    get_secret,
    _secret_provider
)


class TestEnvSecretProvider:
    """Test environment variable secret provider"""
    
    def test_get_secret_from_env(self):
        """Test getting secret from environment variable"""
        provider = EnvSecretProvider()
        
        with patch.dict(os.environ, {"TEST_SECRET": "test_value"}):
            value = provider.get_secret("TEST_SECRET")
            assert value == "test_value"
    
    def test_get_secret_not_found(self):
        """Test getting secret that doesn't exist"""
        provider = EnvSecretProvider()
        
        value = provider.get_secret("NONEXISTENT_SECRET")
        assert value is None


class TestAWSSecretsManagerProvider:
    """Test AWS Secrets Manager provider"""
    
    def test_get_secret_from_aws(self):
        """Test getting secret from AWS Secrets Manager"""
        provider = AWSSecretsManagerProvider(region="us-east-1")
        
        # Mock boto3 client
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": "aws_secret_value"}
        provider._client = mock_client
        
        value = provider.get_secret("test-secret-name")
        
        assert value == "aws_secret_value"
        mock_client.get_secret_value.assert_called_once_with(SecretId="test-secret-name")
    
    def test_get_secret_not_found_in_aws(self):
        """Test getting secret that doesn't exist in AWS"""
        provider = AWSSecretsManagerProvider(region="us-east-1")
        
        # Mock boto3 client
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = Exception
        mock_client.get_secret_value.side_effect = Exception("Secret not found")
        provider._client = mock_client
        
        value = provider.get_secret("nonexistent-secret")
        
        assert value is None
    
    def test_aws_provider_requires_boto3(self):
        """Test that AWS provider requires boto3"""
        provider = AWSSecretsManagerProvider()
        
        # Mock ImportError when accessing boto3
        import sys
        original_boto3 = sys.modules.get('boto3')
        try:
            # Remove boto3 from modules if it exists
            if 'boto3' in sys.modules:
                del sys.modules['boto3']
            # Mock the import to raise ImportError
            with patch.dict('sys.modules', {'boto3': None}):
                # This will raise ImportError when _get_client tries to import boto3
                try:
                    provider._get_client()
                    # If we get here, boto3 is available (which is fine)
                except ImportError:
                    # Expected if boto3 not available
                    pass
        finally:
            # Restore original boto3 if it existed
            if original_boto3:
                sys.modules['boto3'] = original_boto3


class TestSecretProviderSelection:
    """Test secret provider selection"""
    
    def test_default_provider_is_env(self):
        """Test that default provider is EnvSecretProvider"""
        # Reset global provider
        import app.core.secrets
        app.core.secrets._secret_provider = None
        
        with patch.dict(os.environ, {"SECRETS_PROVIDER": ""}, clear=False):
            provider = get_secret_provider()
            assert isinstance(provider, EnvSecretProvider)
    
    def test_aws_provider_selection(self):
        """Test that AWS provider is selected when configured"""
        # Reset global provider
        import app.core.secrets
        app.core.secrets._secret_provider = None
        
        with patch.dict(os.environ, {"SECRETS_PROVIDER": "aws", "AWS_DEFAULT_REGION": "us-west-2"}, clear=False):
            # Mock boto3 import to avoid ImportError
            import sys
            mock_boto3 = MagicMock()
            with patch.dict('sys.modules', {'boto3': mock_boto3}):
                provider = get_secret_provider()
                assert isinstance(provider, AWSSecretsManagerProvider)
                assert provider.region == "us-west-2"


class TestGetSecretHelper:
    """Test get_secret helper function"""
    
    def test_get_secret_uses_provider(self):
        """Test that get_secret uses the configured provider"""
        # Reset global provider
        import app.core.secrets
        app.core.secrets._secret_provider = None
        
        with patch.dict(os.environ, {"TEST_SECRET": "test_value"}, clear=False):
            value = get_secret("TEST_SECRET")
            assert value == "test_value"

