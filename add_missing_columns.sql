-- Add the missing columns to the bets table
-- This will fix the admin dashboard not showing bets

-- Step 1: Add market column
ALTER TABLE bets ADD COLUMN market VARCHAR(50) DEFAULT '2';

-- Step 2: Add sport_name column  
ALTER TABLE bets ADD COLUMN sport_name VARCHAR(50) DEFAULT 'soccer';

-- Step 3: Update all existing bets to have the correct values
UPDATE bets SET market = '2', sport_name = 'soccer' WHERE market IS NULL OR market = '' OR sport_name IS NULL OR sport_name = '';

-- Step 4: Verify the changes
SELECT id, user_id, match_id, market, sport_name FROM bets LIMIT 10;
