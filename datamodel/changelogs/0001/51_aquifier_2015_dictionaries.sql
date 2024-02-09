 ------ this file generates the tww is_dictionary (Table _aquifier dss 2015) in en on TEKSI
------ For questions etc. please contact Stefan Burckhardt stefan.burckhardt@sjib.ch
------ version 9.2.2024 09:18:00
------ // skip-keyword-check based on version 04.07.2017 23:28:49 09_qgep_dictionaries.sql
------ with 3D coordinates

--- CREATE TABLE tww_sys.dictionary_od_table already exists

 INSERT INTO tww_sys.dictionary_od_table (id, tablename, name_en, shortcut_en, name_de, shortcut_de, name_fr, shortcut_fr, name_it, shortcut_it, name_ro, shortcut_ro) VALUES (30,'_aquifier','aquifier','AQ','Grundwasserleiter','GL','Aquifère','AQ','NULL','NULL','NULL','NULL');

 --- CREATE TABLE tww_sys.dictionary_od_field already exists

 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,283,'_aquifier','average_groundwater_level','average_groundwater_level','MittlererGWSpiegel','NIVEAU_NAPPE_MOY','zzz_MittlererGWSpiegel','nivelul_mediu_al_apelor_subterane','Average level of groundwater table','Höhe des mittleren Grundwasserspiegels','[m.s.m.]','[m s.l.m.]','rrr_[M.ü.M.]',ARRAY['kein_Plantyp_definiert']::tww_od.plantype[],'true','decimal(7,3)','[m.a.sl.]','meters above sea level [m.a.sl.]','[M.ü.M.]','Meter über Meer [M.ü.M.]','','','','','','',-200,5000);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,2519,'_aquifier','identifier','identifier','Bezeichnung','DESIGNATION','denominazione','identificator','NULL','NULL','NULL','NULL','rrr_[M.ü.M.]',ARRAY['kein_Plantyp_definiert']::tww_od.plantype[],'true','varchar(20)','','','','','','','','','','',NULL,NULL);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,284,'_aquifier','maximal_groundwater_level','maximal_groundwater_level','MaxGWSpiegel','NIVEAU_NAPPE_MAX','zzz_MaxGWSpiegel','nivelul_maxim_al_apelor_subterane','Maximal level of ground water table','Maximale Lage des Grundwasserspiegels','[m.s.m.]','[m s.l.m.]','rrr_[M.ü.M.]',ARRAY['kein_Plantyp_definiert']::tww_od.plantype[],'true','decimal(7,3)','[m.a.sl.]','meters above sea level [m.a.sl.]','[M.ü.M.]','Meter über Meer [M.ü.M.]','','','','','','',-200,5000);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,285,'_aquifier','minimal_groundwater_level','minimal_groundwater_level','MinGWSpiegel','NIVEAU_NAPPE_MIN','zzz_MinGWSpiegel','nivelul_minim_al_apelor_subterane','Minimal level of groundwater table','Minimale Lage des Grundwasserspiegels','[m.s.m.]','[m s.l.m.]','rrr_[M.ü.M.]',ARRAY['kein_Plantyp_definiert']::tww_od.plantype[],'true','decimal(7,3)','[m.a.sl.]','meters above sea level [m.a.sl.]','[M.ü.M.]','Meter über Meer [M.ü.M.]','','','','','','',-200,5000);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,2246,'_aquifier','perimeter','perimeter','Perimeter','PERIMETRE','perimetro','perimetru','Boundary points of the perimeter','Begrenzungspunkte der Fläche','[CoordNat]','[LKoord]','[LKoord]',ARRAY['kein_Plantyp_definiert']::tww_od.plantype[],'true','geometry','[LKoord]','points with coordinates in the swiss national grid','[LKoord]','Punkte mit Schweizer Landeskoordinaten','','','','','','',NULL,NULL);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,2577,'_aquifier','remark','remark','Bemerkung','REMARQUE','osservazione','observa?ii','General remarks','Allgemeine Bemerkungen','Remarques générales','NULL','[LKoord]',ARRAY['kein_Plantyp_definiert']::tww_od.plantype[],'true','varchar(80)','','','','','','','','','','',NULL,NULL);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,999999,'_aquifier','OBJ_ID','OBJ_ID','OBJ_ID','OBJ_ID','OBJ_ID','OBJ_ID','OBJ_ID - Unique ID','OBJ_ID - eindeutige Kennung','OBJ_ID - ID unique','OBJ_ID - identificatore univoco','rrr_OBJ_ID - eindeutige Kennung',ARRAY['Werkinformation','Leitungskataster', 'GEP_Verband','GEP_Traegerschaft','SAA', 'PAA']::tww_od.plantype[],'true','varchar(16)','','','','','','','','','','',NULL,NULL);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,999998,'_aquifier','dataowner','dataowner','Datenherr','MAITRE_DES_DONNEES','proprietario_dati','rrr_Datenherr','dataowner - this is the person or body who is allowed to delete, change or maintain this object','Metaattribut Datenherr ist diejenige Person oder Stelle, die berechtigt ist, diesen Datensatz zu löschen, zu ändern bzw. zu verwalten','Maître des données gestionnaire de données, qui est la personne ou l''organisation autorisée pour gérer, modifier ou supprimer les données de cette table/classe','zzz_Metaattribut L''attributo proprietario dati si riferisce alla persona o ente che è autorizzato a eliminare, modificare o gestire i dati','rrr_Metaattribut Datenherr ist diejenige Person oder Stelle, die berechtigt ist, diesen Datensatz zu löschen, zu ändern bzw. zu verwalten',ARRAY['Werkinformation','Leitungskataster', 'GEP_Verband','GEP_Traegerschaft','SAA', 'PAA']::tww_od.plantype[],'true','varchar(80)','','','','','','','','','','',NULL,NULL);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,999997,'_aquifier','provider','provider','Datenlieferant','FOURNISSEUR_DES_DONNEES','fornitore_dati','rrr_Datenlieferant','Metaattribute provider - this is the person or body who delivered the data','Metaattribut Datenlieferant ist diejenige Person oder Stelle, die die Daten geliefert hat','FOURNISSEUR DES DONNEES Organisation qui crée l’enregistrement de ces données','zzz_Metaattribut L''attributo fornitore dati si riferisce alla persona o ente che ha fornito i dati','rrr_Metaattribut Datenlieferant ist diejenige Person oder Stelle, die die Daten geliefert hat',ARRAY['Werkinformation','Leitungskataster', 'GEP_Verband','GEP_Traegerschaft','SAA', 'PAA']::tww_od.plantype[],'true','varchar(80)','','','','','','','','','','',NULL,NULL);
 INSERT INTO tww_sys.dictionary_od_field (class_id, attribute_id, table_name, field_name, field_name_en, field_name_de, field_name_fr, field_name_it, field_name_ro, field_description_en, field_description_de, field_description_fr, field_description_it, field_description_ro, field_mandatory, field_visible, field_datatype, field_unit_en, field_unit_description_en, field_unit_de, field_unit_description_de, field_unit_fr, field_unit_description_fr, field_unit_it, field_unit_description_it, field_unit_ro, field_unit_description_ro, field_max, field_min) VALUES (30,999996,'_aquifier','last_modification','last_modification','Letzte_Aenderung','DERNIERE_MODIFICATION','ultima_modifica','rrr_Letze_Aenderung','Last modification: INTERLIS_1_DATE','Letzte Änderung: INTERLIS_1_DATE','Dernière modification: INTERLIS_1_DATE','ultima_modifica: INTERLIS_1_DATE','rrr_Letzte Änderung: INTERLIS_1_DATE',ARRAY['Werkinformation','Leitungskataster', 'GEP_Verband','GEP_Traegerschaft','SAA', 'PAA']::tww_od.plantype[],'true','TIMESTAMP','','','','','','','','','','',NULL,NULL);

 -- CREATE TABLE tww_sys.dictionary_od_values already exists


