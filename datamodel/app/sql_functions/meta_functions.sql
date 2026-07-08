CREATE OR REPLACE FUNCTION tww_app.check_all_nulls(
	jason jsonb,
	prefix_ character varying,
	ignored_postfix text[] DEFAULT ARRAY['obj_id'::text,
	'identifier'::text])
    RETURNS boolean
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
    BEGIN
	  SELECT array_agg(prefix_||'_'||t.val)
	  FROM  unnest(ignored_postfix) as t(val)
	  INTO ignored_postfix;

	  SELECT ignored_postfix||( SELECT array_agg(key)
	  FROM jsonb_object_keys(jason) key
          WHERE LEFT(key, char_length(prefix_)) != prefix_)
		INTO ignored_postfix;

	  jason := jason - ignored_postfix;
      -- Check if all remaining values are NULL
      RETURN jsonb_strip_nulls(jason)::text = '{{}}' OR jsonb_strip_nulls(jason)::text IS NULL;
	  END;
$BODY$;


CREATE OR REPLACE FUNCTION tww_app.refresh_materialized_views(_schema_name text, _matview_name text, _all bool DEFAULT False)
RETURNS void AS $$
DECLARE
    mv_record record;
    _error_message text;
    cnt int;
BEGIN
    FOR mv_record IN
        SELECT schemaname, matviewname
        FROM pg_matviews
        WHERE schemaname = _schema_name
		AND (_all OR matviewname = _matview_name)
    LOOP
        BEGIN
            EXECUTE format('SELECT COUNT(*) FROM %I.%I', mv_record.schemaname, mv_record.matviewname) INTO cnt;
            IF cnt > 0 THEN
                EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I.%I WITH DATA',
                    mv_record.schemaname,
                    mv_record.matviewname);
            ELSE
                EXECUTE format('REFRESH MATERIALIZED VIEW %I.%I WITH DATA',
                    mv_record.schemaname,
                    mv_record.matviewname);
            END IF;
            RAISE NOTICE '%',format('Refreshed materialized view: %s.%s', mv_record.schemaname, mv_record.matviewname);
        EXCEPTION
            WHEN OTHERS THEN
                _error_message := format('Error refreshing materialized view %s.%s: %s',
                                       mv_record.schemaname, mv_record.matviewname, SQLERRM);
                RAISE EXCEPTION '%', _error_message;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tww_app.apply_refresh() RETURNS VOID AS $body$
BEGIN
    IF NOT pg_try_advisory_lock(4711) THEN
        RETURN;
    END IF;
    BEGIN
        -- Don't refresh while users are editing
        IF EXISTS (
            SELECT 1
            FROM tww_app.active_editors
        ) THEN
            RETURN;
        END IF;
        SELECT tww_app.network_refresh_network_simple();
        TRUNCATE tww_od.refresh_state;
        PERFORM pg_advisory_unlock(4711);
        RETURN;
    EXCEPTION
        WHEN OTHERS THEN
            PERFORM pg_advisory_unlock(4711);
            RAISE;
    END;
END;

$body$
LANGUAGE plpgsql;
