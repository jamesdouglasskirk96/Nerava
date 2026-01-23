from fastapi import APIRouter, Depends, HTTPException, Path, Request
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.tenant import list_modules
from app.security.scopes import require_scopes
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/tenant", tags=["utility-platform"])

# Required scopes: utility:read for tenant modules
@router.get("/{tenant_id}/modules")
async def get_tenant_modules(
    request: Request,
    tenant_id: str = Path(..., description="Tenant ID"),
    current_user: Dict[str, Any] = Depends(require_scopes(["utility:read"]))
) -> Dict[str, Any]:
    """
    Get utility-as-a-platform tenant modules.
    
    Requires scope: utility:read
    """
    
    # Check feature flag
    if not flag_enabled("feature_uap_partnerships"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "tenant_modules",
        "tenant_id": tenant_id,
        "actor_id": current_user.get("user_id")
    })
    
    try:
        result = list_modules(tenant_id)
        
        log_info({
            "trace_id": trace_id,
            "route": "tenant_modules",
            "tenant_id": tenant_id,
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "tenant_modules",
            "tenant_id": tenant_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
