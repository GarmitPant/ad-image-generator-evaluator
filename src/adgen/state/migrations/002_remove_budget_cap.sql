-- Spend limits are delegated to provider accounts; the local ledger only records usage estimates.
ALTER TABLE run DROP COLUMN budget_cap_usd;
ALTER TABLE model_call DROP COLUMN reservation_usd;
INSERT INTO schema_version VALUES(2,strftime('%Y-%m-%dT%H:%M:%fZ','now'));
