-- SaaS tiering: track each business's subscription plan (free | pro | multi).
-- Entitlements/limits live in code (app/core/plans.py); this is the stored selection.

ALTER TABLE business_profiles
    ADD COLUMN IF NOT EXISTS plan TEXT NOT NULL DEFAULT 'free';
