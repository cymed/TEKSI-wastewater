-- this file generates a new SQL function to create INTERLIS STANDARDOID's for all the tww_od.* tables.
-- you need to add entries for your organizations into the table tww_sys.oid_prefixes
-- questions regarding this function should be directed to Arnaud Poncet, Pully
-- Adapted for TEKSI VSA-DSS 2020 Stefan Burckhardt

CREATE TABLE tww_sys.oid_prefixes
(
  id serial NOT NULL,
  prefix character(8),
  organization text,
  active boolean,
  CONSTRAINT pkey_tww_is_oid_prefixes_id PRIMARY KEY (id )
)
WITH (
  OIDS=FALSE
);
COMMENT ON TABLE tww_sys.oid_prefixes
  IS 'This table contains OID prefixes for different communities or organizations. The application or administrator changing this table has to make sure that only one record is set to active.';

-- sample entry for Invalid - you need to adapt this entry later for your own organization
INSERT INTO tww_sys.oid_prefixes (prefix,organization,active) VALUES ('ch000000','Invalid',TRUE);


CREATE INDEX in_tww_is_oid_prefixes_active
  ON tww_sys.oid_prefixes
  USING btree
  (active );

CREATE UNIQUE INDEX in_tww_is_oid_prefixes_id
  ON tww_sys.oid_prefixes
  USING btree
  (id );

-- function for generating StandardOIDs

CREATE OR REPLACE FUNCTION tww_sys.generate_oid(schema_name text, table_name text)
  RETURNS text AS
$BODY$
DECLARE
  myrec_prefix record;
  myrec_shortcut record;
  myrec_seq record;
BEGIN
  -- first we have to get the OID prefix
  BEGIN
    SELECT prefix::text INTO myrec_prefix FROM tww_sys.oid_prefixes WHERE active = TRUE;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
           RAISE EXCEPTION 'no active record found in table tww_sys.oid_prefixes';
        WHEN TOO_MANY_ROWS THEN
	   RAISE EXCEPTION 'more than one active records found in table tww_sys.oid_prefixes';
  END;
  -- test if prefix is of correct length
  IF char_length(myrec_prefix.prefix) != 8 THEN
    RAISE EXCEPTION 'character length of prefix must be 8';
  END IF;
  --get table 2char shortcut
  BEGIN
    SELECT shortcut_en INTO STRICT myrec_shortcut FROM tww_sys.dictionary_od_table WHERE tablename = table_name;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE EXCEPTION 'dictionary entry for table % not found', table_name;
        WHEN TOO_MANY_ROWS THEN
            RAISE EXCEPTION 'dictonary entry for table % not unique', table_name;
  END;
  --get sequence for table
  EXECUTE format('SELECT nextval(''%1$I.seq_%2$I_oid'') AS seqval', schema_name, table_name) INTO myrec_seq;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'sequence for table % not found', table_name;
  END IF;
  RETURN myrec_prefix.prefix || myrec_shortcut.shortcut_en || to_char(myrec_seq.seqval,'FM000000');
END;
$BODY$
  LANGUAGE plpgsql STABLE
  COST 100;
