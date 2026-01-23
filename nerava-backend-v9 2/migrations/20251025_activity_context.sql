-- Adds a free-text context for the earning row, e.g. "charged and chilled at Starbucks".
ALTER TABLE follow_earnings_monthly
  ADD COLUMN IF NOT EXISTS context TEXT;
