CREATE OR REPLACE FUNCTION tww_app.update_catchment_area_totals(_obj_id text, _all boolean default false)
  RETURNS VOID 
  SECURITY DEFINER
  AS
  $BODY$
BEGIN
 
 UPDATE tww_od.catchment_area_totals cat
 SET
      population=subquery.population
	, surface_area=subquery.surface_area
    , surface_imp=subquery.surface_imp
    , surface_red=subquery.surface_red
    , sewer_infiltration_water=subquery.sewer_infiltration_water
    , waste_water_production=subquery.waste_water_production
    , surface_dim=subquery.surface_dim
	, population_dim=subquery.population_dim
    , surface_imp_dim=subquery.surface_imp_dim
    , surface_red_dim=subquery.surface_red_dim
    -- , sewer_infiltration_water_dim=subquery.sewer_infiltration_water_dim
    -- , waste_water_production_dim=subquery.waste_water_production_dim
   FROM 
	( SELECT 
		  ca_tot.obj_id
		, ca_agg.population
		, ca_agg.surface_area
		, ca_agg.surface_imp
		, ca_agg.surface_red
		, ca_agg.sewer_infiltration_water
		, ca_agg.waste_water_production
		, ca_agg.population_dim
		, ca_agg.surface_dim
		, ca_agg.surface_imp_dim
		, ca_agg.surface_red_dim
		-- , ca_agg.sewer_infiltration_water_dim
		-- , ca_agg.waste_water_production_dim
	 FROM tww_od.catchment_area_totals ca_tot
     LEFT JOIN tww_od.hydraulic_char_data hcd ON hcd.obj_id::text = ca_tot.fk_hydraulic_char_data::text
     LEFT JOIN tww_od.wastewater_node wn ON hcd.fk_wastewater_node::text = wn.obj_id::text
     LEFT JOIN ( WITH ca AS 
					(
                 SELECT 
		 			obj_id,
		 			fk_special_building_ww_current AS fk_log_card,
		 			population_density_current*surface_area AS population,
		 			surface_area,
		 			surface_area*seal_factor_ww_current/100 AS surface_imp,
		 			surface_area*discharge_coefficient_ww_current/100 AS surface_red,
		 			sewer_infiltration_water_production_current AS sewer_infiltration_water,
		 			waste_water_production_current AS waste_water_production,
		 			0 AS population_dim,
		 			0 AS surface_dim,
		 			0 AS surface_imp_dim,
					0 AS surface_red_dim
		 			-- ,0 AS sewer_infiltration_water_dim,  -- Not in datamodel (yet) 
		 			-- 0 AS waste_water_production_dim,    -- Not in datamodel (yet)
                   FROM tww_od.catchment_area
                  WHERE catchment_area.fk_special_building_ww_current IS NOT NULL
                UNION ALL
                 SELECT 
		 			obj_id,
		 			fk_special_building_rw_current AS fk_log_card,
		 			population_density_current*surface_area AS population,
		 			-- do not count double
		 			CASE WHEN fk_special_building_rw_current=fk_special_building_ww_current THEN 0 else surface_area END AS surface_area,
		 			surface_area*seal_factor_rw_current/100 AS surface_imp,
		 			surface_area*discharge_coefficient_rw_current/100 AS surface_red,
		 			0 AS sewer_infiltration_water,
		 			0 AS waste_water_production,
		 			0 AS population_dim,
		 			0 AS surface_dim,
		 			0 AS surface_imp_dim,
					0 AS surface_red_dim
		 			-- ,0 AS sewer_infiltration_water_dim,  -- Not in datamodel (yet) 
		 			-- 0 AS waste_water_production_dim,    -- Not in datamodel (yet)
                  FROM tww_od.catchment_area
				  WHERE catchment_area.fk_special_building_rw_current IS NOT NULL
		 		UNION ALL
                 SELECT 
		 			obj_id,
		 			fk_special_building_ww_planned AS fk_log_card,
		 			0 AS population,
		 			0 AS surface_area,
		 			0 AS surface_imp,
		 			0 AS surface_red,
		 			0 AS sewer_infiltration_water,
		 			0 AS waste_water_production,
		 			population_density_planned*surface_area AS population_dim,
		 			surface_area AS surface_dim,
		 			surface_area*seal_factor_ww_planned/100 AS surface_imp_dim,
		 			surface_area*discharge_coefficient_ww_planned/100 AS surface_red_dim
		 			-- ,0 AS sewer_infiltration_water_dim,  -- Not in datamodel (yet) 
		 			-- 0 AS waste_water_production_dim,    -- Not in datamodel (yet)
                  FROM tww_od.catchment_area
				  WHERE catchment_area.fk_special_building_ww_planned IS NOT NULL
		 		UNION ALL
                 SELECT 
		 			obj_id,
		 			fk_special_building_rw_planned AS fk_log_card,
		 			0 AS population,
		 			0 AS surface_area,
		 			0 AS surface_imp,
		 			0 AS surface_red,
		 			0 AS sewer_infiltration_water,
		 			0 AS waste_water_production,
		 			0 AS population_dim,
		 			-- do not count double
		 			CASE WHEN fk_special_building_rw_planned=fk_special_building_ww_planned THEN 0 else surface_area END AS surface_dim,
		 			surface_area*seal_factor_rw_planned/100 AS surface_imp_dim,
		 			surface_area*discharge_coefficient_rw_planned/100 AS surface_red_dim
		 			-- ,0 AS sewer_infiltration_water_dim,  -- Not in datamodel (yet) 
		 			-- 0 AS waste_water_production_dim,    -- Not in datamodel (yet)
                  FROM tww_od.catchment_area
				  WHERE catchment_area.fk_special_building_ww_planned IS NOT NULL
                )
                 SELECT main_lc.obj_id,
                    main_lc.fk_pwwf_wastewater_node,
                    sum(ca.population) AS population,
					sum(ca.surface_area) AS surface_area,
					sum(ca.surface_imp) AS surface_imp,
					sum(ca.surface_red) AS surface_red,
					sum(ca.sewer_infiltration_water) AS sewer_infiltration_water,
					sum(ca.waste_water_production) AS waste_water_production,
					sum(ca.population_dim) AS population_dim,
					sum(ca.surface_dim) AS surface_dim,
					sum(ca.surface_imp_dim) AS surface_imp_dim,
					sum(ca.surface_red_dim) AS surface_red_dim
					-- ,sum(ca.sewer_infiltration_water_dim) AS sewer_infiltration_water_dim,    -- Not in datamodel (yet)
					-- sum(ca.waste_water_production_dim) AS waste_water_production_dim,    -- Not in datamodel (yet)
                   FROM ca
                     LEFT JOIN tww_od.log_card lc ON ca.fk_log_card::text = lc.obj_id::text
                     LEFT JOIN tww_od.log_card main_lc ON main_lc.obj_id::text = lc.fk_main_structure::text
				   GROUP BY main_lc.obj_id,
                    main_lc.fk_pwwf_wastewater_node
                )ca_agg 
				ON ca_agg.fk_pwwf_wastewater_node::text = wn.obj_id::text
	  WHERE (_all OR ca_tot.obj_id = _obj_id)
   ) subquery
WHERE subquery.obj_id = cat.obj_id;
	
END
$BODY$
LANGUAGE plpgsql
VOLATILE;