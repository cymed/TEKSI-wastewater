CREATE SCHEMA IF NOT EXISTS tww_diff;

CREATE TABLE IF NOT EXISTS tww_diff.metadata (
    id bigserial PRIMARY KEY,
    job_id text NOT NULL UNIQUE,
    job_status text NOT NULL DEFAULT 'pending',
    import_tstamp timestamp with time zone NOT NULL DEFAULT now(),
    diff_tstamp timestamp with time zone NOT NULL DEFAULT now(),
    validation_success boolean NOT NULL DEFAULT false,
    source_model text,
    source_file text,
    import_schema text,
    live_schema text,
    metadata jsonb NOT NULL DEFAULT '{{}}'::jsonb,
    CONSTRAINT tww_diff_metadata_status_list
    CHECK (
        job_status IN (
            'pending',
            'accepted',
            'rejected',
            'applied',
            'failed',
            'archived'
        )
    )
);

CREATE INDEX IF NOT EXISTS metadata_job_status_idx
ON tww_diff.metadata (job_status);

CREATE INDEX IF NOT EXISTS metadata_diff_tstamp_idx
ON tww_diff.metadata (diff_tstamp);

DO
$DO$
DECLARE
    rec record;
BEGIN
    FOR rec IN
        SELECT tablename as table_name
        FROM tww_sys.dictionary_od_table
    LOOP
        EXECUTE FORMAT(
            'CREATE TABLE IF NOT EXISTS tww_diff.%I (
                diff_id bigserial PRIMARY KEY,
                job_id bigint NOT NULL
                    REFERENCES tww_diff.metadata (id)
                    ON DELETE CASCADE,
                obj_id text NOT NULL,
                is_created boolean NOT NULL DEFAULT false,
                is_altered boolean NOT NULL DEFAULT false,
                is_deleted boolean NOT NULL DEFAULT false,
                is_rejected boolean GENERATED ALWAYS AS (
                    jsonb_array_length(permission_findings) > 0
                    OR jsonb_array_length(validation_findings) > 0
                ) STORED,
                import_values jsonb NOT NULL DEFAULT ''{{}}''::jsonb,
                canonical_values jsonb NOT NULL DEFAULT ''{{}}''::jsonb,
                changed_attributes jsonb NOT NULL DEFAULT ''[]''::jsonb,
                unpermitted_values jsonb NOT NULL DEFAULT ''{{}}''::jsonb,
                permission_findings jsonb NOT NULL DEFAULT ''[]''::jsonb,
                validation_findings jsonb NOT NULL DEFAULT ''[]''::jsonb,
                created_at timestamp with time zone NOT NULL DEFAULT now(),
                UNIQUE (job_id, obj_id)
            );',
            rec.table_name
        );
        EXECUTE FORMAT(
            'CREATE INDEX IF NOT EXISTS %I
             ON tww_diff.%I (job_id);',
            rec.table_name || '_job_id_idx',
            rec.table_name
        );

        EXECUTE FORMAT(
            'CREATE INDEX IF NOT EXISTS %I
             ON tww_diff.%I (obj_id);',
            rec.table_name || '_obj_id_idx',
            rec.table_name
        );

        EXECUTE FORMAT(
            'CREATE INDEX IF NOT EXISTS %I
             ON tww_diff.%I (job_id, obj_id);',
            rec.table_name || '_job_obj_id_idx',
            rec.table_name
        );

        EXECUTE FORMAT(
            'CREATE INDEX IF NOT EXISTS %I
             ON tww_diff.%I (is_unpermitted);',
            rec.table_name || '_is_unpermitted_idx',
            rec.table_name
        );
    END LOOP;
END;
$DO$;  