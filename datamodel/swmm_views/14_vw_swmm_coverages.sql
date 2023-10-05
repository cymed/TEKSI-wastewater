-----------------------------------------
-- creates coverages
-- - Depends on tww_swmm.subcatchments
-----------------------------------------
CREATE OR REPLACE VIEW tww_swmm.vw_coverages AS
SELECT
  sub.Name  as Subcatchment,
  pzk.value_en as landUse,
  round((st_area(st_intersection(sub.geom, pz.perimeter_geometry))/st_area(sub.geom))::numeric,2)*100 as percent,
  sub.obj_id
FROM tww_swmm.vw_subcatchments sub, tww_od._planning_zone pz
LEFT JOIN tww_vl._planning_zone_kind pzk on pz.kind = pzk.code
WHERE st_intersects(sub.geom, pz.perimeter_geometry)
AND st_isvalid(sub.geom) AND st_isvalid(pz.perimeter_geometry)
ORDER BY sub.Name, percent DESC;
