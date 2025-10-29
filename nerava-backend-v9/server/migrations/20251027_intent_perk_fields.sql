-- Add perk + station context to charge_intents for Earn page
ALTER TABLE charge_intents ADD COLUMN IF NOT EXISTS perk_id TEXT;
ALTER TABLE charge_intents ADD COLUMN IF NOT EXISTS station_name TEXT;
ALTER TABLE charge_intents ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE charge_intents ADD COLUMN IF NOT EXISTS window_text TEXT;
ALTER TABLE charge_intents ADD COLUMN IF NOT EXISTS distance_text TEXT;
ALTER TABLE charge_intents ADD COLUMN IF NOT EXISTS merchant TEXT;
ALTER TABLE charge_intents ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'saved';
-- status: saved|started|notified|verified|done
