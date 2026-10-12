-- Full layer: the core layer plus OpenStreetMap. Everything made here is
-- derived from OSM and falls under the ODbL. Inputs: osm, p576, and the
-- tables core.sql made.

create or replace table osm_n as
  select 'osm:' || osm_id as id, * exclude (osm_id),
         norm_name(name) as nn, house_number(housenumber) as hn,
         nullif(concat_ws(' ', housenumber, street), '') as address
  from osm;

-- Each OSM feature joins the one core place it matches best.
create or replace table osm_match as
  select a_id as place_id, b_id as osm_id, rule, dist, sim
  from match_pairs('core_names', 'osm_n')
  qualify row_number() over (
    partition by b_id
    order by case rule when 'number' then 1 when 'near' then 2 else 3 end, sim desc, dist) = 1;

create or replace table osm_member as
  select coalesce(m.place_id, o.id) as place_id, 'osm' as source, substr(o.id, 5) as source_id,
         coalesce(m.rule, 'self') as rule, coalesce(m.dist, 0.0) as dist, coalesce(m.sim, 1.0) as sim
  from osm_n o left join osm_match m on m.osm_id = o.id;

create or replace table osm_only as
  select o.id, o.name, o.category, o.brand, o.brand_wikidata, o.address, o.city, o.region, o.postcode,
         o.phone, o.website, o.lat, o.lng, null::varchar as overture_status, o.nn, o.hn, false as has_fsq,
         zip5(o.postcode) as zip, street_key(o.address) as sk
  from osm_n o
  where o.id not in (select osm_id from osm_match);

create or replace table osm_fill as
  select m.place_id, o.*
  from osm_match m join osm_n o on o.id = m.osm_id
  where o.lifecycle is null
  qualify row_number() over (partition by m.place_id order by m.dist) = 1;

create or replace table osm_evidence as
  -- lifecycle prefix: closed. The date is the end_date tag when it parses,
  -- otherwise the day the feature was last edited, an upper bound.
  select m.place_id, 'osm_lifecycle' as source, o.id as source_id, 'closed' as state,
         coalesce(try_cast(o.end_date as date), o.edited) as date,
         m.rule, m.dist, o.name as ev_name, o.address as ev_address
  from osm_member m join osm_n o on o.id = 'osm:' || m.source_id
  where o.lifecycle is not null
  union all
  -- check_date: a mapper confirmed the feature on that day
  select m.place_id, 'osm_check_date', o.id, 'open', try_cast(o.check_date as date),
         m.rule, m.dist, o.name, o.address
  from osm_member m join osm_n o on o.id = 'osm:' || m.source_id
  where o.lifecycle is null and try_cast(o.check_date as date) is not null
  union all
  -- Wikidata P576 (dissolved, abolished or demolished date) on the item the feature links to.
  -- Not for offices: there the item is the company, and a merger date says
  -- nothing about the building (2 of the 4 hits in the test boxes were that).
  select m.place_id, 'wikidata_p576', o.wikidata, 'closed', w.date, m.rule, m.dist, o.name, o.address
  from osm_member m join osm_n o on o.id = 'osm:' || m.source_id
  join p576 w on w.qid = o.wikidata
  where o.category not like 'office=%'
  union all
  -- OSM edit history, by way of OpenPOIs: the OSM feature matched to this
  -- Overture place was deleted, lost its main tag, or was renamed to
  -- something else on that day. (A lifecycle prefix being added is left to
  -- the osm_lifecycle rows above.)
  select k.place_id, 'osm_history', h.overture_id, 'closed', h.event_date, 'id', 0.0, h.event, null
  from openpois h join ovt_canon k on k.id = 'ovt:' || h.overture_id
  join ovt_all o on o.id = 'ovt:' || h.overture_id
  join ovt_n p on p.id = k.place_id
  where same_name(o.name, p.name) and h.event in ('hard_delete', 'primary_tag_deleted', 'substantial_rename') and h.event_date is not null
    -- the place must still carry the name OpenPOIs matched the event to,
    -- and must not already be the business the OSM feature was renamed to
    and same_name(h.overture_name, o.name)
    and not (h.event = 'substantial_rename' and h.osm_name is not null and same_name(h.osm_name, o.name))
  union all
  -- France: an OSM feature tagged with its SIRET takes that establishment's
  -- record directly, no matching needed
  select m.place_id, r.source, r.source_id, r.state, r.date, 'id', 0.0, r.name, r.address
  from osm_member m join osm_n o on o.id = 'osm:' || m.source_id
  join register_n r on r.source = 'sirene' and r.source_id = replace(o.siret, ' ', '')
  union all
  -- registers against the places only OSM has
  select * from matched_evidence('osm_only');

delete from osm_evidence
  where source in (select source from independents_only)
    and place_id in (select id from osm_only where brand is not null);

create or replace table full_evidence as
  select * from core_evidence union all select * from osm_evidence;

create or replace table full_status as
  select * from status_of('full_evidence', (select build_date from params), (select recent_days from params));

-- OpenPOIs' confidence per place, for the open score of places with no evidence.
create or replace table full_conf as
  select k.place_id, max(h.conf_mean) as conf
  from openpois h join ovt_canon k on k.id = 'ovt:' || h.overture_id
  where h.conf_mean is not null group by 1;
create or replace table core_conf as select * from full_conf where false;
