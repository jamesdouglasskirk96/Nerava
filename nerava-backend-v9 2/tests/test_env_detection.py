"""
Test environment detection utilities.

Verifies that:
1. Environment detection uses ENV only, never REGION
2. REGION spoofing doesn't work (security)
3. Functions return correct values for different ENV values
"""
import os
import pytest
from app.core.env import get_env_name, is_local_env, is_production_env, is_staging_env


class TestEnvDetection:
    """Test environment detection functions"""
    
    def test_get_env_name_defaults_to_dev(self):
        """Test that get_env_name() defaults to 'dev' when ENV not set"""
        # Save original ENV
        original_env = os.environ.get("ENV")
        
        try:
            # Remove ENV if set
            if "ENV" in os.environ:
                del os.environ["ENV"]
            
            # Clear cache
            get_env_name.cache_clear()
            
            # Should default to 'dev'
            assert get_env_name() == "dev"
        finally:
            # Restore original ENV
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            get_env_name.cache_clear()
    
    def test_get_env_name_returns_lowercase(self):
        """Test that get_env_name() returns lowercase"""
        original_env = os.environ.get("ENV")
        
        try:
            os.environ["ENV"] = "PROD"
            get_env_name.cache_clear()
            
            assert get_env_name() == "prod"
        finally:
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            get_env_name.cache_clear()
    
    def test_is_local_env_checks_env_only(self):
        """Test that is_local_env() only checks ENV, not REGION"""
        original_env = os.environ.get("ENV")
        original_region = os.environ.get("REGION")
        
        try:
            # Set ENV=prod but REGION=local - should return False (not fooled by REGION)
            os.environ["ENV"] = "prod"
            os.environ["REGION"] = "local"
            is_local_env.cache_clear()
            
            assert is_local_env() is False, (
                "is_local_env() should return False when ENV=prod, "
                "even if REGION=local (REGION can be spoofed)"
            )
        finally:
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            if original_region is not None:
                os.environ["REGION"] = original_region
            else:
                if "REGION" in os.environ:
                    del os.environ["REGION"]
            is_local_env.cache_clear()
    
    def test_is_local_env_returns_true_for_local_dev(self):
        """Test that is_local_env() returns True for local/dev environments"""
        original_env = os.environ.get("ENV")
        
        try:
            for env_value in ["local", "dev"]:
                os.environ["ENV"] = env_value
                is_local_env.cache_clear()
                
                assert is_local_env() is True, f"is_local_env() should return True for ENV={env_value}"
        finally:
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            is_local_env.cache_clear()
    
    def test_is_production_env_checks_env_only(self):
        """Test that is_production_env() only checks ENV, not REGION"""
        original_env = os.environ.get("ENV")
        original_region = os.environ.get("REGION")
        
        try:
            # Set ENV=prod but REGION=local - should return True (not fooled by REGION)
            os.environ["ENV"] = "prod"
            os.environ["REGION"] = "local"
            is_production_env.cache_clear()
            
            assert is_production_env() is True, (
                "is_production_env() should return True when ENV=prod, "
                "even if REGION=local (REGION can be spoofed)"
            )
        finally:
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            if original_region is not None:
                os.environ["REGION"] = original_region
            else:
                if "REGION" in os.environ:
                    del os.environ["REGION"]
            is_production_env.cache_clear()
    
    def test_is_production_env_returns_true_for_prod(self):
        """Test that is_production_env() returns True for prod/production"""
        original_env = os.environ.get("ENV")
        
        try:
            for env_value in ["prod", "production"]:
                os.environ["ENV"] = env_value
                is_production_env.cache_clear()
                
                assert is_production_env() is True, f"is_production_env() should return True for ENV={env_value}"
        finally:
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            is_production_env.cache_clear()
    
    def test_is_production_env_returns_false_for_local(self):
        """Test that is_production_env() returns False for local/dev"""
        original_env = os.environ.get("ENV")
        
        try:
            for env_value in ["local", "dev"]:
                os.environ["ENV"] = env_value
                is_production_env.cache_clear()
                
                assert is_production_env() is False, f"is_production_env() should return False for ENV={env_value}"
        finally:
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            is_production_env.cache_clear()
    
    def test_is_staging_env_returns_true_for_staging(self):
        """Test that is_staging_env() returns True for staging/stage"""
        original_env = os.environ.get("ENV")
        
        try:
            for env_value in ["staging", "stage"]:
                os.environ["ENV"] = env_value
                is_staging_env.cache_clear()
                
                assert is_staging_env() is True, f"is_staging_env() should return True for ENV={env_value}"
        finally:
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            is_staging_env.cache_clear()
    
    def test_region_spoofing_prevention(self):
        """Test that REGION spoofing doesn't bypass security checks"""
        original_env = os.environ.get("ENV")
        original_region = os.environ.get("REGION")
        
        try:
            # Attempt to spoof: ENV=prod but REGION=local
            # All security checks should still treat this as production
            os.environ["ENV"] = "prod"
            os.environ["REGION"] = "local"
            
            # Clear all caches
            get_env_name.cache_clear()
            is_local_env.cache_clear()
            is_production_env.cache_clear()
            
            # Should detect as production, not local
            assert get_env_name() == "prod"
            assert is_local_env() is False, "Should not be fooled by REGION=local"
            assert is_production_env() is True, "Should detect production despite REGION=local"
        finally:
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                if "ENV" in os.environ:
                    del os.environ["ENV"]
            if original_region is not None:
                os.environ["REGION"] = original_region
            else:
                if "REGION" in os.environ:
                    del os.environ["REGION"]
            get_env_name.cache_clear()
            is_local_env.cache_clear()
            is_production_env.cache_clear()







