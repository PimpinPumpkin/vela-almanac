-- Final tables in the published shape. See SPEC.md for the columns.

create or replace macro license_of(source) as
  case
    when source = 'overture' then 'CDLA-Permissive-2.0'
    when source in ('fsq', 'fsq_closed') then 'Apache-2.0'
    when source in ('atp', 'wikidata_p576', 'biz_nola', 'childcare_tx', 'la_biz', 'achd_pa_food') then 'CC0-1.0'
    when source like 'osm%' or source in ('dol_wa', 'marin_food') then 'ODbL-1.0'
    when source like 'abca_dc%' or source in ('bbl_dc', 'childcare_ca', 'mke_food', 'mke_liquor') then 'CC-BY-4.0'
    when source in ('abc_ca', 'tabc_tx', 'dbpr_fl_food', 'abt_fl', 'atc_mo', 'olcc_or', 'tdlr_tx',
                    'bot_sac', 'emd_sac', 'lou_food', 'abc_ky_jefferson', 'li_phl', 'biz_seattle', 'biz_denver', 'childcare_wa',
                    'dor_wi_liquor', 'isp_id_liquor', 'lcb_wa', 'abc_nj', 'lcc_ne', 'bablo_me', 'abc_ar', 'able_ok',
                    'biz_lasvegas', 'dchd_omaha_food', 'mpls_food', 'mpls_liquor', 'llb_baltimore', 'cph_columbus_food',
                    'mdard_mi_food', 'dph_sc_food', 'mda_mn_food', 'dpor_va', 'bop_tx', 'bop_oh',
                    'phx_liquor', 'nash_beer', 'anc_liquor', 'sux_food', 'hsv_liquor', 'det_biz', 'det_liquor',
                    'det_food', 'miami_dade_biz', 'longbeach_biz', 'broward_biz', 'tucson_biz', 'bellevue_biz',
                    'saccounty_biz', 'chesapeake_biz', 'alameda_food',
                    'riverside_food', 'cdph_ca_facilities', 'co_tobacco', 'lac_biz',
                    'abc_nc', 'abc_ky', 'abc_ks', 'plcb_pa', 'tda_tn_food', 'dhhs_nc_inspections',
                    'dph_ga_inspections', 'msdh_ms_food', 'adph_al_food', 'osdh_ok_food',
                    'norfolk_biz', 'berkeley_biz', 'nj_inspection')
         or source like 'foodsafety_%'
         or source like 'dca_ca_%' or (source like 'childcare_%' and source not in ('childcare_ca', 'childcare_co', 'childcare_ny', 'childcare_nyc', 'childcare_pa', 'childcare_tx'))
         or source like 'dbpr_fl_%' then 'none-stated'
    when source in ('sla_ny', 'dmv_ny', 'dos_ny_salons', 'agm_ny', 'tax_ny_tobacco', 'ocm_ny', 'doh_ny_food',
                    'childcare_ny', 'lottery_ny') then 'OPEN-NY-terms'
    when source in ('dohmh_nyc', 'dcwp_nyc', 'childcare_nyc', 'wm_nyc') then 'NYC-Open-Data-terms'
    when source like 'cdph_chicago%' or source like 'bacp_chicago%' then 'Chicago-Data-Portal-terms'
    when source in ('isd_boston_food', 'isd_boston_inspection', 'lb_boston', 'childcare_co', 'cambridge_food', 'sf_biz',
                    'biz_sandiego') then 'PDDL-1.0'
    when source = 'lottery_tx' then 'Texas-Lottery-terms'
    when source = 'sirene' then 'etalab-2.0'
    -- everything else is a US federal register or a table its publisher marks public domain
    else 'US-public-domain'
  end;

-- open_score: a rough chance, 0 to 1, that the place is open on the build date.
-- It is a rule of thumb, not a fitted model. The parts:
--   closed                        0.10  (a closing record is wrong about 1 time in 8
--                                        where a second source can check it)
--   newest evidence is open       0.97 * 0.90 ^ years since that date
--                                        (about 1 business in 10 closes each year)
--   same, but it overrode an
--   older closing record          0.80 * 0.90 ^ years
--   no evidence                   0.30 when Overture says permanently_closed or when
--                                 missing_license is true; OpenPOIs' confidence
--                                 when that is 0.80 or more; otherwise the
--                                 listing's own standing (unvouched_score below)
-- A stale open record never scores below 0.75.
--
-- unvouched_score: what a place with no evidence is worth, from who lists it.
-- A place that OSM or AllThePlaces also has, or that does not come from
-- Overture at all, keeps 0.75. A place only Overture has is scored by the
-- source Overture took it from, because that predicts whether a register
-- will ever find it (SPEC.md section 7, "Listings nobody vouches for"):
--   Meta, or more than one source   0.60
--   BrightQuery or Microsoft alone  0.40
--   Foursquare alone                0.25
create or replace macro overture_sources_of(datasets) as
  list_sort(list_filter(list_transform(datasets, lambda d: lower(d)), lambda d: d not in ('overture', 'overture-signals')));
create or replace macro unvouched_score(id, in_map, datasets) as
  case when in_map or id not like 'ovt:%' or datasets is null then 0.75
       when len(overture_sources_of(datasets)) <> 1 then 0.60
       when overture_sources_of(datasets)[1] = 'foursquare' then 0.25
       when overture_sources_of(datasets)[1] in ('brightquery', 'microsoft') then 0.40
       else 0.60 end;
create or replace macro open_score(status, status_date, conflict, overture_status, missing_license, conf, build_date, base) as
  round(case
    when status = 'closed' then 0.10
    when status_date is not null then greatest(
      case when conflict then 0.80 else 0.97 end * pow(0.90, greatest(build_date - status_date, 0) / 365.25),
      case when conflict then 0.50 else 0.75 end)
    when overture_status = 'permanently_closed' or missing_license then 0.30
    when conf >= 0.80 then conf
    else base
  end, 2);

-- States whose active alcohol license list is complete and carries positions,
-- so that finding no license for a bar means something. See SPEC.md section 7.
create or replace table license_list as
  select * from (values ('DC', 'abca_dc_active'), ('NY', 'sla_ny')) t(region, source);

-- Opening hours, in OpenStreetMap's opening_hours syntax. AllThePlaces reads
-- them off each brand's own store pages; OSM mappers write them by hand. A
-- place takes the newest one among its members. The core layer only has the
-- AllThePlaces ones.
create or replace table hours_core as
  select m.place_id, arg_max(a.opening_hours, a.collected) as opening_hours,
         'atp' as hours_source, max(a.collected) as hours_date
  from core_member m join atp a on a.atp_id = m.source_id
  where m.source = 'atp' and nullif(trim(a.opening_hours), '') is not null
  group by m.place_id;
create or replace table hours_full as
  select place_id, arg_max(opening_hours, hours_date) as opening_hours,
         arg_max(hours_source, hours_date) as hours_source, max(hours_date) as hours_date
  from (select * from hours_core
        union all
        select m.place_id, o.opening_hours, 'osm', o.edited
        from osm_member m join osm o on o.osm_id = m.source_id
        where m.source = 'osm' and o.lifecycle is null and nullif(trim(o.opening_hours), '') is not null)
  group by place_id;

create or replace macro published(place, member, status, conf, hours) as table (
  with m as (
    select place_id,
           list(struct_pack(source, id := source_id) order by source, source_id) as sources,
           list(distinct license_of(source)) as member_licenses,
           bool_or(source in ('osm', 'atp')) as in_map
    from query_table(member) group by place_id
  )
  select p.id, p.name, p.category,
         coalesce(og.category_group, group_of(p.category)) as category_group,
         coalesce(og.category_subgroup, subgroup_of(p.category)) as category_subgroup,
         p.brand, p.brand_wikidata,
         p.address, p.city, p.region, p.postcode, p.phone, p.website,
         h.opening_hours, h.hours_source, h.hours_date,
         coalesce(s.status, 'unknown') as status, s.status_date, s.status_source,
         open_score(coalesce(s.status, 'unknown'), s.status_date, coalesce(s.conflict, false),
                    p.overture_status, coalesce(ml.missing, false), cf.conf, (select build_date from params),
                    unvouched_score(p.id, m.in_map, og.datasets)) as open_score,
         round(cf.conf, 2) as openpois_conf,
         ml.missing as missing_license,
         p.overture_status,
         overture_sources_of(og.datasets) as overture_sources,
         m.sources,
         list_sort(list_distinct(
           m.member_licenses
           || case when p.has_fsq then ['Apache-2.0'] else [] end
           || coalesce(list_transform(s.evidence, lambda e: license_of(e.source)), []))) as licenses,
         coalesce(s.evidence, []) as evidence,
         p.lat, p.lng,
         st_point(p.lng, p.lat) as geometry
  from query_table(place) p
  join m on m.place_id = p.id
  left join query_table(status) s on s.place_id = p.id
  left join query_table(conf) cf on cf.place_id = p.id
  left join query_table(hours) h on h.place_id = p.id
  left join ovt_all og on og.id = p.id
  -- true: a bar in a state with a license list, and no active license matched it.
  -- null: the question does not apply to this place.
  left join (
    select p2.id, not exists (
             select 1 from query_table(status) s2, unnest(s2.evidence) as u(e)
             where s2.place_id = p2.id and u.e.source = l.source) as missing
    from query_table(place) p2 join license_list l on l.region = p2.region
    where needs_alcohol_license(p2.category)
  ) ml on ml.id = p.id
);

create or replace table out_core as
  select * from published('core_place', 'core_member', 'core_status', 'core_conf', 'hours_core');

-- The full layer: core places with OSM folded in, then the places only OSM has.
create or replace table full_place as
  select c.* replace (
           coalesce(r.name, c.name) as name,
           coalesce(c.phone, f.phone) as phone,
           coalesce(c.website, f.website) as website,
           -- a renamed fuel lot takes OSM's brand too, or none: the old brand must not stay
           case when r.place_id is not null then r.brand else coalesce(c.brand, f.brand) end as brand,
           case when r.place_id is not null then r.brand_wikidata else coalesce(c.brand_wikidata, f.brand_wikidata) end as brand_wikidata,
           coalesce(c.address, f.address) as address)
  from core_place c left join osm_fill f on f.place_id = c.id
  left join fuel_rename r on r.place_id = c.id
  union all
  select * from osm_only;

create or replace table full_member as
  select * from core_member union all select * from osm_member;

create or replace table out_full as
  select * from published('full_place', 'full_member', 'full_status', 'full_conf', 'hours_full');
