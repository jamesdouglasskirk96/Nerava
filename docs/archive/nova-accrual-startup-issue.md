# Nova Accrual Service Startup Issue

## Problem Identified

The `nova_accrual_service` starts on application startup (line 869 in `main_simple.py`), and while it has protection to only run in demo mode, the service's background task (`_run`) immediately starts polling the database every 5 seconds.

## Code Flow

1. **Startup Event Handler** (`main_simple.py:866-876`):
   ```python
   @app.on_event("startup")
   async def start_nova_accrual():
       await nova_accrual_service.start()
   ```

2. **Service Start Method** (`nova_accrual.py:40-52`):
   ```python
   async def start(self):
       if not self.is_enabled():
           logger.info("Nova accrual service disabled (demo mode not enabled)")
           return  # ✅ Returns early if not enabled
       
       self.running = True
       self.task = asyncio.create_task(self._run())  # Starts background task
   ```

3. **Background Task** (`nova_accrual.py:68-84`):
   ```python
   async def _run(self):
       while self.running:
           try:
               await self._accrue_nova_for_charging_wallets()  # Queries database
               await asyncio.sleep(self.accrual_interval)
           except Exception as e:
               logger.error(f"Error in Nova accrual service: {e}", exc_info=True)
               await asyncio.sleep(self.accrual_interval)
   ```

4. **Database Query** (`nova_accrual.py:86-96`):
   ```python
   async def _accrue_nova_for_charging_wallets(self):
       db = SessionLocal()
       try:
           charging_wallets = db.query(DriverWallet).filter(
               DriverWallet.charging_detected == True
           ).all()  # ❌ Fails if tables don't exist
   ```

## The Issue

**In Production:**
- If `DEMO_MODE` or `DEMO_QR_ENABLED` is `false`, the service should not start ✅
- However, if these env vars are `true` (or accidentally set), the service will start
- The background task immediately queries the database
- If migrations haven't run or tables don't exist, it will fail with:
  ```
  sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: driver_wallets
  ```

**But wait:** The service catches exceptions and logs them, so it shouldn't crash the application. However, the error logs are very noisy and could mask other issues.

## Potential Real Issue

If the service is enabled in production, and the database query fails, it should just log an error and continue. But let me check if there's a different problem - maybe the startup is failing for a different reason.

Let me check the actual App Runner logs to see what's happening.


