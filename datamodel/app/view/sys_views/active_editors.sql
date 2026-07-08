CREATE VIEW tww_app.active_editors AS
SELECT
    usename,
    application_name,
    state,
    xact_start,
    now() - xact_start AS transaction_age
FROM pg_stat_activity
WHERE datname = current_database()
  AND state IN ('idle in transaction')
  AND xact_start IS NOT NULL;
