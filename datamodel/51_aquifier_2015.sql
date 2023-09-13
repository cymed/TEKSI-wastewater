------ This file generates the VSA-DSS database (Modul VSA-DSS 2015) table _aquifier (as it does not exist anymore in VSA-DSS 2020)  in en on QQIS
------ For questions etc. please contact Stefan Burckhardt stefan.burckhardt@sjib.ch
------ version 03.07.2017 21:26:28
BEGIN;
------ CREATE SCHEMA qgep;

-------
CREATE TABLE qgep_od._aquifier
(
   obj_id varchar(16) NOT NULL,
   CONSTRAINT pkey_qgep_od_aquifier_obj_id PRIMARY KEY (obj_id)
)
WITH (
   OIDS = False
);
CREATE SEQUENCE qgep_od.seq_aquifier_oid INCREMENT 1 MINVALUE 0 MAXVALUE 999999 START 0;
 ALTER TABLE qgep_od._aquifier ALTER COLUMN obj_id SET DEFAULT qgep_sys.generate_oid('qgep_od','aquifier');
COMMENT ON COLUMN qgep_od._aquifier.obj_id IS '[primary_key] INTERLIS STANDARD OID (with Postfix/Präfix) or UUOID, see www.interlis.ch';
ALTER TABLE qgep_od._aquifier ADD COLUMN average_groundwater_level  decimal(7,3) ;
COMMENT ON COLUMN qgep_od._aquifier.average_groundwater_level IS 'Average level of groundwater table / Höhe des mittleren Grundwasserspiegels / Niveau moyen de la nappe';
ALTER TABLE qgep_od._aquifier ADD COLUMN identifier  varchar(20) ;
COMMENT ON COLUMN qgep_od._aquifier.identifier IS '';
ALTER TABLE qgep_od._aquifier ADD COLUMN maximal_groundwater_level  decimal(7,3) ;
COMMENT ON COLUMN qgep_od._aquifier.maximal_groundwater_level IS 'Maximal level of ground water table / Maximale Lage des Grundwasserspiegels / Niveau maximal de la nappe';
ALTER TABLE qgep_od._aquifier ADD COLUMN minimal_groundwater_level  decimal(7,3) ;
COMMENT ON COLUMN qgep_od._aquifier.minimal_groundwater_level IS 'Minimal level of groundwater table / Minimale Lage des Grundwasserspiegels / Niveau minimal de la nappe';
ALTER TABLE qgep_od._aquifier ADD COLUMN perimeter_geometry geometry('CURVEPOLYGON', :SRID);
CREATE INDEX in_qgep_od_aquifier_perimeter_geometry ON qgep_od._aquifier USING gist (perimeter_geometry );
COMMENT ON COLUMN qgep_od._aquifier.perimeter_geometry IS 'Boundary points of the perimeter / Begrenzungspunkte der Fläche / Points de délimitation de la surface';
ALTER TABLE qgep_od._aquifier ADD COLUMN remark  varchar(80) ;
COMMENT ON COLUMN qgep_od._aquifier.remark IS 'General remarks / Allgemeine Bemerkungen / Remarques générales';
ALTER TABLE qgep_od._aquifier ADD COLUMN last_modification TIMESTAMP without time zone DEFAULT now();
COMMENT ON COLUMN qgep_od._aquifier.last_modification IS 'Last modification / Letzte_Aenderung / Derniere_modification: INTERLIS_1_DATE';
ALTER TABLE qgep_od._aquifier ADD COLUMN fk_dataowner varchar(16);
COMMENT ON COLUMN qgep_od._aquifier.fk_dataowner IS 'Foreignkey to Metaattribute dataowner (as an organisation) - this is the person or body who is allowed to delete, change or maintain this object / Metaattribut Datenherr ist diejenige Person oder Stelle, die berechtigt ist, diesen Datensatz zu löschen, zu ändern bzw. zu verwalten / Maître des données gestionnaire de données, qui est la personne ou l''organisation autorisée pour gérer, modifier ou supprimer les données de cette table/classe';
ALTER TABLE qgep_od._aquifier ADD COLUMN fk_provider varchar (16);
COMMENT ON COLUMN qgep_od._aquifier.fk_provider IS 'Foreignkey to Metaattribute provider (as an organisation) - this is the person or body who delivered the data / Metaattribut Datenlieferant ist diejenige Person oder Stelle, die die Daten geliefert hat / FOURNISSEUR DES DONNEES Organisation qui crée l’enregistrement de ces données ';
-------
CREATE TRIGGER
update_last_modified_aquifier
BEFORE UPDATE OR INSERT ON
 qgep_od._aquifier
FOR EACH ROW EXECUTE PROCEDURE
 qgep_sys.update_last_modified();

-------

/* ALTER TABLE qgep_od.water_catchment ADD COLUMN fk_aquifier varchar (16);
ALTER TABLE qgep_od.water_catchment ADD CONSTRAINT rel_water_catchment_aquifier FOREIGN KEY (fk_aquifier) REFERENCES qgep_od._aquifier(obj_id) ON UPDATE CASCADE ON DELETE set null; */


/* ALTER TABLE qgep_od.infiltration_installation ADD COLUMN fk_aquifier varchar (16);
ALTER TABLE qgep_od.infiltration_installation ADD CONSTRAINT rel_infiltration_installation_aquifier FOREIGN KEY (fk_aquifier) REFERENCES qgep_od._aquifier(obj_id) ON UPDATE CASCADE ON DELETE set null; */


ALTER TABLE qgep_od._aquifier ADD CONSTRAINT rel_od_aquifier_fk_dataowner FOREIGN KEY (fk_dataowner) REFERENCES qgep_od.organisation(obj_id);
ALTER TABLE qgep_od._aquifier ADD CONSTRAINT rel_od_aquifier_fk_dataprovider FOREIGN KEY (fk_provider) REFERENCES qgep_od.organisation(obj_id);


------ Indexes on identifiers

CREATE UNIQUE INDEX in_od_aquifier_identifier ON qgep_od._aquifier USING btree (identifier ASC NULLS LAST, fk_dataowner ASC NULLS LAST);
 
 
COMMIT;
