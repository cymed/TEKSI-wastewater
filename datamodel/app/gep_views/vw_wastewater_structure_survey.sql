CREATE VIEW tww_app.vw_tww_wastewater_structure_survey
 AS 
 SELECT ws.obj_id,
   ws.identifier,
        CASE
            WHEN ma.obj_id IS NOT NULL THEN 'manhole'::text
            WHEN ss.obj_id IS NOT NULL THEN 'special_structure'::text
            WHEN dp.obj_id IS NOT NULL THEN 'discharge_point'::text
            WHEN ii.obj_id IS NOT NULL THEN 'infiltration_installation'::text
            ELSE 'unknown'::text
        END AS ws_type,
    ma.function AS ma_function,
    ss.function AS ss_function,
    COALESCE(wn.situation3d_geometry, main_co.situation3d_geometry) AS situation3d_geometry,
    wn._usage_current AS _channel_usage_current,
    wn._function_hierarchic AS _channel_function_hierarchic,
    me.status,
	ms.obj_id as ms_obj_id
   FROM tww_od.wastewater_structure ws
     LEFT JOIN tww_od.cover main_co ON main_co.obj_id::text = ws.fk_main_cover::text
     LEFT JOIN tww_od.structure_part main_co_sp ON main_co_sp.obj_id::text = ws.fk_main_cover::text
     LEFT JOIN tww_od.manhole ma ON ma.obj_id::text = ws.obj_id::text
     LEFT JOIN tww_od.special_structure ss ON ss.obj_id::text = ws.obj_id::text
     LEFT JOIN tww_od.discharge_point dp ON dp.obj_id::text = ws.obj_id::text
     LEFT JOIN tww_od.infiltration_installation ii ON ii.obj_id::text = ws.obj_id::text
     LEFT JOIN tww_od.wastewater_networkelement ne ON ne.obj_id::text = ws.fk_main_wastewater_node::text
     LEFT JOIN tww_od.wastewater_node wn ON wn.obj_id::text = ws.fk_main_wastewater_node::text
     RIGHT JOIN tww_od.re_maintenance_event_wastewater_structure mw ON mw.fk_wastewater_structure = ws.obj_id::text	 
	 LEFT JOIN tww_od.maintenance_event me ON mw.fk_maintenance_event = me.obj_id::text	
     RIGHT JOIN tww_od.measure ms ON me.fk_measure = ms.obj_id::text
  WHERE NOT (EXISTS ( SELECT 1
           FROM tww_od.channel ch
          WHERE ch.obj_id::text = ws.obj_id::text));
		  
 
CREATE VIEW tww_app.vw_tww_wastewater_channel_survey
 AS 
 SELECT re.obj_id,
    ws.identifier,
    ch.usage_current AS ch_usage_current,
    ch.function_hierarchic AS ch_function_hierarchic,
    re.progression3d_geometry,
    me.status,
	ms.obj_id as ms_obj_id
   FROM tww_od.reach re
     INNER JOIN tww_od.wastewater_networkelement ne ON ne.obj_id::text = re.obj_id::text 
     LEFT JOIN tww_od.channel ch ON ch.obj_id::text = ne.fk_wastewater_structure::text
     LEFT JOIN tww_od.wastewater_structure ws ON ch.obj_id::text = ws.obj_id::text
     RIGHT JOIN tww_od.re_maintenance_event_wastewater_structure mw ON mw.fk_wastewater_structure = ws.obj_id::text	 
	 LEFT JOIN tww_od.maintenance_event me ON mw.fk_maintenance_event = me.obj_id::text	
     RIGHT JOIN tww_od.measure ms ON me.fk_measure = ms.obj_id::text
;