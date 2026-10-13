-- Core layer: Overture + AllThePlaces + evidence that does not come from OSM.
-- Nothing in this file may read an OSM-derived table; that is what keeps the
-- core layer free of ODbL terms. Inputs (made by build.sh): ovt, atp,
-- fsq_closed, register (evidence rows inside the region), params.

create or replace table ovt_all as
  select 'ovt:' || id as id, * exclude (id), norm_name(name) as nn, house_number(address) as hn
  from ovt;

-- Duplicate listings inside Overture. Two cases merge.
-- 1. Same house number, within 250 m, identical normalized name. Looser
--    name pairs were read and are mostly a part and its whole (a gift shop
--    and its hospital), see SPEC.md section 9.
-- 2. Two fuel stations with the same house number within 60 m, whatever
--    they are called. A forecourt is one per lot, and Overture keeps a row
--    for every brand the lot has had ("Shell", "BP", "Bladensburg Amoco").
-- Groups are closed over chains of pairs by passing the smallest id along
-- the pairs three times; the smallest id is kept as the place id.
create or replace macro is_fuel(category) as category in ('gas_station', 'fueling_station');
create or replace table ovt_fuel_pair as
  select a.id as a_id, b.id as b_id
  from (select *, cell_y(lat) as cy, cell_x(lng) as cx from ovt_all where is_fuel(category) and hn is not null) a
  join (select t.*, cell_y(t.lat) + dy.d as cy, cell_x(t.lng) + dx.d as cx
        from ovt_all t, (values (-1), (0), (1)) dy(d), (values (-1), (0), (1)) dx(d)
        where is_fuel(t.category) and t.hn is not null) b
    on a.cy = b.cy and a.cx = b.cx and a.hn = b.hn
  where a.id <> b.id and a.nn <> b.nn and dist_m(a.lat, a.lng, b.lat, b.lng) <= 60;

create or replace table ovt_pair as
  select a_id, b_id from match_pairs('ovt_all', 'ovt_all')
  where a_id <> b_id and rule = 'number' and sim = 1.0
  union
  select a_id, b_id from ovt_fuel_pair;

create or replace table ovt_canon as
  with l0 as (select id, id as c from ovt_all),
  l1 as (select l.id, least(l.c, coalesce(min(n.c), l.c)) as c
         from l0 l left join ovt_pair p on p.a_id = l.id left join l0 n on n.id = p.b_id group by l.id, l.c),
  l2 as (select l.id, least(l.c, coalesce(min(n.c), l.c)) as c
         from l1 l left join ovt_pair p on p.a_id = l.id left join l1 n on n.id = p.b_id group by l.id, l.c),
  l3 as (select l.id, least(l.c, coalesce(min(n.c), l.c)) as c
         from l2 l left join ovt_pair p on p.a_id = l.id left join l2 n on n.id = p.b_id group by l.id, l.c)
  select id, c as place_id from l3;

-- Which listing of a fuel lot names the place: one with a real name before
-- one named by its street address ("2917 MLK AVE SE"), then the one the
-- brand's own locator still lists there, then the one Overture is surest of. Every
-- other group keeps the listing whose id it carries (the names are equal).
create or replace table ovt_lead as
  with fuel as (
    select k.place_id, o.id, o.nn, o.confidence,
           exists (select 1 from atp a
                   where a.category = 'amenity=fuel' and abs(a.lat - o.lat) < 0.001 and abs(a.lng - o.lng) < 0.0013
                     and (name_sim(norm_name(a.name), o.nn) >= 0.9 or name_sim(norm_name(a.brand), o.nn) >= 0.9)) as listed
    from ovt_canon k join ovt_all o on o.id = k.id
    where k.place_id in (select place_id from ovt_canon
                         where id in (select a_id from ovt_fuel_pair))
  )
  select k.place_id, coalesce(f.id, k.place_id) as lead_id
  from (select distinct place_id from ovt_canon) k
  left join (select place_id, id from fuel
             qualify row_number() over (partition by place_id order by regexp_matches(nn, '^[0-9]+ ') or regexp_matches(nn, ' (st|street|ave|avenue|rd|road|blvd|hwy|pike)( [nsew]{1,2})?$'), listed desc, confidence desc nulls last, id) = 1) f
    using (place_id);

-- One row per Overture place: the leading listing under the place id, gaps
-- filled from its duplicates.
create or replace table ovt_n as
  with fill as (
    select k.place_id,
           any_value(o.category) as category, any_value(o.brand) as brand,
           any_value(o.brand_wikidata) as brand_wikidata, any_value(o.postcode) as postcode,
           any_value(o.phone) as phone, any_value(o.website) as website,
           bool_or(list_contains(o.datasets, 'Foursquare')) as has_fsq,
           -- closed only if every listing says so
           case when bool_and(o.operating_status = 'permanently_closed') then 'permanently_closed'
                else any_value(nullif(o.operating_status, 'permanently_closed')) end as operating_status
    from ovt_canon k join ovt_all o on o.id = k.id group by k.place_id
  )
  select o.* replace (
           l.place_id as id,
           coalesce(o.category, f.category) as category, coalesce(o.brand, f.brand) as brand,
           coalesce(o.brand_wikidata, f.brand_wikidata) as brand_wikidata,
           coalesce(o.postcode, f.postcode) as postcode, coalesce(o.phone, f.phone) as phone,
           coalesce(o.website, f.website) as website, f.operating_status as operating_status),
         f.has_fsq
  from ovt_lead l join ovt_all o on o.id = l.lead_id join fill f on f.place_id = l.place_id;

-- The other names a merged fuel lot goes by. A register or a locator that
-- still uses one of them must find the place, not mint a second one.
create or replace table ovt_alias as
  select distinct k.place_id as id, o.nn, o.hn, o.lat, o.lng, zip5(o.postcode) as zip, street_key(o.address) as sk
  from ovt_canon k join ovt_lead l using (place_id) join ovt_all o on o.id = k.id
  join ovt_all lead on lead.id = l.lead_id
  where k.id <> l.lead_id and o.nn <> lead.nn;
create or replace table ovt_names as
  select id, nn, hn, lat, lng from ovt_n union all select id, nn, hn, lat, lng from ovt_alias;

create or replace table atp_n as
  select 'atp:' || atp_id as id, * exclude (atp_id, housenumber),
         norm_name(name) as nn,
         coalesce(house_number(housenumber), house_number(address)) as hn
  from atp;

-- Each AllThePlaces row joins the one Overture place it matches best.
create or replace table atp_match as
  select a_id as place_id, b_id as atp_id, rule, dist, sim
  from match_pairs('ovt_names', 'atp_n')
  qualify row_number() over (
    partition by b_id
    order by case rule when 'number' then 1 when 'near' then 2 else 3 end, sim desc, dist) = 1;

create or replace table core_member as
  select place_id, 'overture' as source, substr(id, 5) as source_id,
         case when id = place_id then 'self'
              when id in (select a_id from ovt_fuel_pair) then 'fuel lot' else 'duplicate' end as rule,
         0.0 as dist, 1.0 as sim
  from ovt_canon
  union all
  select coalesce(m.place_id, a.id), 'atp', substr(a.id, 5),
         coalesce(m.rule, 'self'), coalesce(m.dist, 0.0), coalesce(m.sim, 1.0)
  from atp_n a left join atp_match m on m.atp_id = a.id;

-- One AllThePlaces row per Overture place fills attribute gaps.
create or replace table atp_fill as
  select m.place_id, a.*
  from atp_match m join atp_n a on a.id = m.atp_id
  qualify row_number() over (partition by m.place_id order by m.dist) = 1;

create or replace table core_place as
  select *, zip5(postcode) as zip, street_key(address) as sk from (
  select o.id, o.name, o.category,
         coalesce(o.brand, nullif(f.brand, '')) as brand,
         coalesce(o.brand_wikidata, nullif(f.brand_wikidata, '')) as brand_wikidata,
         coalesce(o.address, nullif(f.address, '')) as address,
         coalesce(o.city, nullif(f.city, '')) as city,
         coalesce(o.region, nullif(f.region, '')) as region,
         coalesce(o.postcode, nullif(f.postcode, '')) as postcode,
         coalesce(o.phone, nullif(f.phone, '')) as phone,
         coalesce(o.website, nullif(f.website, '')) as website,
         o.lat, o.lng, o.operating_status as overture_status,
         o.nn, coalesce(o.hn, f.hn) as hn,
         o.has_fsq
  from ovt_n o left join atp_fill f on f.place_id = o.id
  union all
  select a.id, a.name, nullif(a.category, ''), nullif(a.brand, ''), nullif(a.brand_wikidata, ''),
         nullif(a.address, ''), nullif(a.city, ''), nullif(a.region, ''), nullif(a.postcode, ''),
         nullif(a.phone, ''), nullif(a.website, ''), a.lat, a.lng, null, a.nn, a.hn, false
  from atp_n a
  where a.id not in (select atp_id from atp_match)
  );

-- Places with every name they are matched under.
create or replace table core_names as
  select id, nn, hn, lat, lng, zip, sk from core_place
  union all select id, nn, hn, lat, lng, zip, sk from ovt_alias;

-- Evidence. Every row: place_id, source, source_id, state, date, rule, dist,
-- plus the name and address the source used, kept for review.

-- Registers and other located records, through the matcher.
create or replace table register_n as
  select source || ':' || source_id as id, *, norm_name(name) as nn, house_number(address) as hn,
         zip5(address) as zip, street_key(address) as sk
  from register;
create or replace table register_pos as select * from register_n where lat is not null;
create or replace table register_addr as select * from register_n where lat is null;

create or replace macro matched_evidence(places) as table (
  select m.a_id as place_id, r.source, r.source_id, r.state, r.date, m.rule, m.dist,
         r.name as ev_name, r.address as ev_address
  from (
    select * from (
      -- a place listed under two names can pass twice; keep its best pass
      select * from match_pairs(places, 'register_pos')
      qualify row_number() over (partition by a_id, b_id order by sim desc, dist) = 1)
    -- a shared house number may hit every listing of the place; without one, only the nearest
    qualify rule = 'number'
         or (max(rule = 'number') over (partition by b_id) = false
             and row_number() over (partition by b_id order by sim desc, dist) = 1)
    union all
    select * from (select * from match_address(places, 'register_addr'))
    qualify row_number() over (partition by a_id, b_id order by sim desc) = 1
  ) m join register_n r on r.id = m.b_id
);

create or replace table core_evidence as
  -- Foursquare's own closing date, joined on the Foursquare id Overture carries
  select k.place_id, 'fsq_closed' as source, f.fsq_place_id as source_id, 'closed' as state,
         f.date_closed as date, 'id' as rule, 0.0 as dist, f.name as ev_name, f.address as ev_address
  from ovt_all o join ovt_canon k on k.id = o.id join fsq_closed f on f.fsq_place_id = o.fsq_id
  join ovt_n p on p.id = k.place_id
  -- An id outlives the business: Overture can keep the row and rename it for
  -- the next tenant. The closure applies only while the names still agree,
  -- and on a merged fuel lot only to the name the place now carries.
  where f.date_closed is not null and same_name(f.name, o.name) and same_name(f.name, p.name)
  union all
  -- present in the chain's own store locator on the day it was collected
  select m.place_id, 'atp', a.id, 'open', a.collected, m.rule, m.dist, a.name, a.address
  from core_member m join atp_n a on a.id = 'atp:' || m.source_id
  where m.source = 'atp' and a.end_date is null and a.collected is not null
  union all
  select * from matched_evidence('core_names');

-- Closures that only hold for independents. When a chain outlet's license or
-- permit ends, the outlet usually carries on under a new franchisee, so
-- these sources do not close a place that carries a brand.
create or replace table independents_only as
  select * from (values ('cdph_chicago_oob'), ('abca_dc_cancelled'), ('bacp_chicago_cancelled')) t(source);
delete from core_evidence
  where source in (select source from independents_only)
    and place_id in (select id from core_place where brand is not null);

-- Places minted from a register. Some registers list the storefront itself:
-- a bank branch, a store authorized for SNAP, a licensed premises. A row
-- from one of those becomes a new place when it is open, has a position,
-- matched nothing, and no listed place within 80 m has a name anywhere near
-- its own (the matcher's near misses are mostly the same place under a
-- longer name, and must not be added twice).
create or replace table storefront_source as
  select * from (values
    ('fdic_locations', 'bank', false, false),
    ('snap_current', 'grocery_or_convenience_store', false, false),
    ('abca_dc_active', 'licensed_premises', false, false),
    ('sla_ny', 'licensed_premises', false, false),
    ('dohmh_nyc', 'restaurant', false, false),
    ('cdph_chicago', 'food_service', false, false),
    ('agm_ny', 'food_store', false, false),
    ('dph_de', 'restaurant', false, false),
    ('emd_sac', 'food_service', false, false),
    ('abc_ky_jefferson', 'licensed_premises', false, false),
    ('lottery_ny', 'grocery_or_convenience_store', false, false),
    ('lottery_fl', 'grocery_or_convenience_store', false, true),
    ('co_tobacco', 'grocery_or_convenience_store', false, true),
    ('childcare_tx', 'amenity=childcare', true, true),
    ('bop_tx', 'amenity=pharmacy', true, true),
    ('dbpr_fl_lodging', 'tourism=hotel', true, true),
    ('cpa_tx_tobacco', 'grocery_or_convenience_store', true, true),
    -- registers that give only an address; see "pinned" below
    ('tabc_tx', 'licensed_premises', true, true),
    ('abc_nc', 'licensed_premises', true, true),
    ('lcb_wa', 'licensed_premises', true, true),
    ('abc_ks', 'licensed_premises', true, true),
    ('abc_nj', 'licensed_premises', true, true),
    ('bablo_me', 'licensed_premises', true, true),
    ('abc_ky', 'licensed_premises', true, true),
    ('led_co', 'licensed_premises', true, true),
    ('lottery_tx', 'grocery_or_convenience_store', true, true),
    ('olcc_or', 'licensed_premises', true, true),
    ('isp_id_liquor', 'licensed_premises', true, true),
    ('lcc_ne', 'licensed_premises', true, true),
    ('phx_liquor', 'licensed_premises', false, true),
    ('anc_liquor', 'licensed_premises', false, true),
    ('nash_beer', 'licensed_premises', false, true),
    ('det_liquor', 'licensed_premises', false, true),
    ('moco_md_alcohol', 'licensed_premises', false, true),
    ('llb_baltimore', 'licensed_premises', false, true),
    ('mpls_liquor', 'licensed_premises', false, true),
    ('fw_co', 'commercial_premises', false, true),
    ('miami_dade_biz', 'commercial_premises', false, true),
    ('longbeach_biz', 'commercial_premises', false, true),
    ('biz_denver', 'commercial_premises', false, true),
    ('biz_lasvegas', 'commercial_premises', false, true),
    ('bacp_chicago', 'commercial_premises', false, true),
    ('bbl_dc', 'commercial_premises', false, true),
    ('dcwp_nyc', 'commercial_premises', false, true),
    ('det_biz', 'commercial_premises', false, true),
    ('cpa_tx', 'commercial_roll', true, true),
    ('osdh_ok_food', 'food_roll', true, true),
    ('lac_food', 'food_roll', false, true),
    ('alameda_food', 'food_roll', false, true),
    ('kc_wa_food', 'food_roll', false, true),
    ('riverside_food', 'food_roll', false, true),
    ('det_food', 'food_roll', false, true),
    ('achd_pa_food', 'food_roll', false, true),
    ('cph_columbus_food', 'food_roll', false, true),
    ('sd_county_food', 'food_roll', true, true),
    ('dph_sc_food', 'food_roll', false, true),
    ('mke_food', 'food_roll', false, true),
    ('mpls_food', 'food_roll', false, true),
    ('mdard_mi_food', 'food_roll', false, true),
    ('dca_ca_salon', 'commercial_roll', true, true),
    ('dca_ca_auto', 'commercial_roll', true, true),
    ('dmv_ny', 'commercial_roll', true, true),
    ('tdlr_tx', 'commercial_roll', true, true),
    ('dos_ny_salons', 'commercial_roll', true, true),
    ('dbpr_fl_salon', 'commercial_roll', true, true),
    ('biz_seattle', 'commercial_roll', false, true),
    ('vb_biz', 'commercial_roll', false, true),
    ('bot_sac', 'commercial_roll', false, true),
    ('saccounty_biz', 'commercial_roll', false, true),
    ('anaheim_biz', 'commercial_roll', false, true),
    ('brla_biz', 'commercial_roll', false, true),
    ('biz_de', 'commercial_roll', false, true),
    ('lac_biz', 'commercial_roll', false, true),
    ('glendale_az_biz', 'commercial_roll', false, true),
    ('broward_biz', 'commercial_roll', false, true),
    ('tucson_biz', 'commercial_roll', false, true),
    ('biz_nola', 'commercial_roll', false, true),
    ('tceq_tx_cleaners', 'shop=dry_cleaning', true, true),
    ('abc_ca', 'licensed_premises', true, true),
    ('abt_fl', 'licensed_premises', true, true)) t(source, category, pinned, strict);
-- pinned: the register gives only an address, and a row is placed on its address point.
-- strict: the row is held to the harder duplicate tests below (every pinned register, and
-- registers whose rows often sit at a fuel station already listed under its brand).

-- Address points, one per house number, street and ZIP. Where a street
-- name repeats inside a ZIP ("N Main" and "S Main") the points lie far
-- apart and the address is left out.
create or replace table addr_pt as
  select zip, hn, sk, avg(lat) as lat, avg(lng) as lng
  from (select zip5(postcode) as zip, house_number(number) as hn, street_key(number || ' ' || street) as sk, lat, lng
        from addr)
  where zip is not null and hn is not null and sk is not null
  group by zip, hn, sk
  having max(lat) - min(lat) < 0.001 and max(lng) - min(lng) < 0.0013;

-- A register row may add a place from the position the register gives, or,
-- for a register that gives only addresses (pinned), from the address
-- point of its house number, street and ZIP. A geocoder's guess along the
-- street is good enough to match a place and not good enough to make one.
create or replace table born as
  with unmatched as materialized (
    select r.* replace (case when s.pinned then coalesce(n.lat, a.lat) else r.lat end as lat,
                        case when s.pinned then coalesce(n.lng, a.lng) else r.lng end as lng),
           s.category, s.pinned, s.strict
    from register_n r join storefront_source s using (source)
    -- (joined for every row and used only for pinned ones: a test on the register's side
    -- of this join makes it crawl on a state the size of California)
    left join addr_pt a on a.zip = r.zip and a.hn = r.hn and a.sk = r.sk
    -- or the point a second public layer gives this very record
    left join (select source, source_id, any_value(lat) as lat, any_value(lng) as lng from pins group by all) n
      on n.source = r.source and n.source_id = r.source_id
    where r.state = 'open'
      and case when s.pinned then coalesce(n.lat, a.lat) else r.lat end is not null
      -- a pin can lie outside the region when only the row's ZIP brought it in
      and case when s.pinned then coalesce(n.lat, a.lat) else r.lat end between (select s from params) and (select n from params)
      and case when s.pinned then coalesce(n.lng, a.lng) else r.lng end between (select w from params) and (select e from params)
      and not exists (select 1 from core_evidence e where e.source = r.source and e.source_id = r.source_id)
      -- a license held for a premises that has no name yet
      and r.name not ilike 'tbd%' and lower(trim(r.name)) not in ('none', 'na', 'n/a', 'not available', 'unknown', 'vacant')
      -- a mailing line or an estate is not a sign on a door
      and not regexp_matches(r.name, '^attn\b|\bc/o\b|estate of', 'i')
      -- a name that ends in a legal form is the company, not the sign on the door
      and not regexp_matches(lower(trade_name(r.name)), '\b(inc|incorporated|corp|corporation|llc|lp|llp|ltd)\.?\s*#?\s*[0-9]*$')
      -- An address-only register is held to more. A counter inside a store
      -- ("Publix #1638 (Deli)", "AFC Sushi @ Publix") is not a place of its
      -- own, and a kitchen in a school, church or hospital is that
      -- institution, which a food register cannot name or classify.
      -- A lottery agent is often licensed in the owner's own name. Only a
      -- name that reads as a shop becomes a place; a person's name never does.
      -- A certificate of occupancy or a city's business license roll (the
      -- commercial_premises registers) names whatever the applicant typed, at
      -- whatever address: only a name that reads as a shop, at an address
      -- that is not an apartment, becomes a place.
      and (s.category not in ('commercial_premises', 'commercial_roll', 'food_roll')
           or reads_as_shop(r.name) and not regexp_matches(r.address, '\b(apt|bsmt|basement|lot|trlr)\b', 'i'))
      -- A roll that fails that reading is held to more (commercial_roll): no
      -- unit or suite in the address, no name of a person's trade ("Nails by
      -- Roni", pet sitting, detailing, rentals), and, below, a listed
      -- business next door.
      and (s.category not in ('commercial_roll', 'food_roll')
           or not regexp_matches(r.name, '\bby\b|\b(pet (sitting|care|services)|sitting|walking|pool|consult\w*|detailing|rentals?|wholesale|distribut\w*|home|design)\b', 'i')
              and not regexp_matches(r.address, '#|\b(unit|ste|suite)\b', 'i'))
      -- a row with no house number sits wherever its register put it
      and (s.category not in ('commercial_premises', 'commercial_roll', 'food_roll') or r.hn is not null)
      -- A food permit names kitchens, counters and outlets as well as shops:
      -- "Pittsburgh Zoo / Jambo Grill", "Safeway #2968 - Grocery", a hotel's
      -- "Main Kitchen", and in King County a food truck by its plate ("KC112").
      and (s.category <> 'food_roll'
           or not regexp_matches(r.name, '/| - |\b(snack bar|main kitchen|banquet|prep|pantry|service bar|kitchen [0-9]|warehouse|storage|bakery dept|deli dept|cafeteria|cart|micro market)\b|\bkc ?#? ?[0-9]+', 'i'))
      and (r.source <> 'lottery_ny'
           -- a sidewalk newsstand carries its holder's name
           or not regexp_matches(r.name, 'news', 'i') and regexp_matches(r.name, '\b(deli|grocery|groc|pharmacy|drugs?|mart|market|convenien\w*|store|liquors?|wine|check cashing|supermarket|food|shop|discount|cafe|coffee|smoke|vape|tobacco|station|gas|cards?|gifts?|stationery|candy|bodega|cents)\b|#\s*[0-9]', 'i'))
      -- a food service contractor's license sits in someone else's building, and a
      -- license at an apartment or a basement is a business run from home
      and not (s.pinned and (regexp_matches(r.name, '\b(eurest|chartwells|aramark|sodexo|compass group|levy|delaware north|dining services|food services?|concessions?|hospitality group|distribut\w*|imports?|wholesale)\b', 'i')
                             or regexp_matches(r.address, '\b(apt|bsmt|basement|lot|trlr)\b', 'i')))
      and not ((s.pinned and s.category in ('licensed_premises', 'grocery_or_convenience_store', 'food_service') or s.category = 'food_roll')
               and (regexp_matches(r.name, '[(@]| at | - (deli|bakery|meat|produce|seafood|starbucks|kitchen|cafe|cafeteria|concession)', 'i')
                             or regexp_matches(r.name, '\b(school|elementary|academy|university|college|church|ministr|baptist|methodist|hospital|medical|nursing|rehab|senior|child|daycare|day care|preschool|learning|head start|ymca|club|lodge|vfw|concession|stand|catering|commissary|truck|mobile)', 'i')))
  ),
  -- every listed name within 200 m of a candidate, found once; the name
  -- tests below are slow and run on these pairs only
  near as materialized (
    select u.id, u.nn, u.hn, u.strict, p.nn as pnn, p.hn as phn, dist_m(u.lat, u.lng, p.lat, p.lng) as d
    from (select *, cell_y(lat) as cy, cell_x(lng) as cx from unmatched) u
    join (select p.nn, p.hn, p.lat, p.lng, cell_y(p.lat) + dy.d as cy, cell_x(p.lng) + dx.d as cx
          from core_names p, (values (-1), (0), (1)) dy(d), (values (-1), (0), (1)) dx(d)) p
      on p.cy = u.cy and p.cx = u.cx
    where dist_m(u.lat, u.lng, p.lat, p.lng) <= 200
  ),
  lookalike as materialized (
    select distinct id from near n,
         lateral (select n.nn as nn, n.hn as hn, n.strict as strict) u, lateral (select n.pnn as nn, n.phn as hn) p
    where (n.d <= 200 and name_sim(u.nn, p.nn) >= 0.9)
       or (n.d <= 80
      and (jaro_winkler_similarity(u.nn, p.nn) >= 0.7
           -- same door and same first word: "Silk Lounge" and "Silk Restaurant and Lounge"
           or (u.hn = p.hn and split_part(u.nn, ' ', 1) = split_part(p.nn, ' ', 1))
           -- an address-only register: any neighbor sharing a real word ("Airport Rd
           -- Chevron" beside "Chevron") is taken to be the same place
           or (u.strict and (list_has_any(name_words(u.nn), name_words(p.nn))
                             -- "la rosas florence" beside "larosas pizza": the same name with the spaces moved
                             or (length(replace(p.nn, ' ', '')) >= 5 and length(replace(u.nn, ' ', '')) >= 5
                                 and left(replace(u.nn, ' ', ''), 6) = left(replace(p.nn, ' ', ''), 6))
                             or (length(p.nn) >= 3 and initials(u.nn) = p.nn)
                             -- "kentucky fried chicken h730213" beside "kfc"
                             or (length(p.nn) between 3 and 5 and length(initials(u.nn)) = length(p.nn) + 1
                                 and left(initials(u.nn), length(p.nn)) = p.nn)
                             or (length(u.nn) >= 3 and initials(p.nn) = u.nn)))))
    union
    -- An address-only register row at the door of a fuel station, a
    -- supermarket, a stadium, a campus or a hospital is nearly always the
    -- shop, counter or stand inside it, which the map already has under
    -- the host's name.
    select distinct u.id
    from (select *, cell_y(lat) as cy, cell_x(lng) as cx from unmatched
          where strict and category in ('licensed_premises', 'grocery_or_convenience_store', 'food_service', 'food_roll')) u
    join (select p.hn, p.lat, p.lng, cell_y(p.lat) + dy.d as cy, cell_x(p.lng) + dx.d as cx
          from core_place p, (values (-1), (0), (1)) dy(d), (values (-1), (0), (1)) dx(d)
          where regexp_matches(coalesce(p.category, ''), 'gas_station|fueling|supermarket|grocery|stadium|arena|college|university|hospital|department_store|warehouse_club|school|airport|convention|casino')) p
      on p.cy = u.cy and p.cx = u.cx
    where dist_m(u.lat, u.lng, p.lat, p.lng) <= 80 and (p.hn = u.hn or dist_m(u.lat, u.lng, p.lat, p.lng) <= 30)
    union
    -- A dry cleaner registered at the door of a listed dry cleaner is that
    -- shop under its new or its legal name ("Q&T Cleaner" at "119 Quick Cleaners").
    select distinct u.id
    from (select *, cell_y(lat) as cy, cell_x(lng) as cx from unmatched where category = 'shop=dry_cleaning') u
    join (select p.hn, p.lat, p.lng, cell_y(p.lat) + dy.d as cy, cell_x(p.lng) + dx.d as cx
          from core_place p, (values (-1), (0), (1)) dy(d), (values (-1), (0), (1)) dx(d)
          where regexp_matches(coalesce(p.category, ''), 'dry_clean|laundr')) p
      on p.cy = u.cy and p.cx = u.cx
    where dist_m(u.lat, u.lng, p.lat, p.lng) <= 80 and (p.hn = u.hn or dist_m(u.lat, u.lng, p.lat, p.lng) <= 30)
  )
  -- A house has no shop beside it. A row of a commercial_roll register
  -- becomes a place only within 40 m of a listed business that is not a
  -- home trade itself.
  , anchored as (
    select distinct u.id
    from (select *, cell_y(lat) as cy, cell_x(lng) as cx from unmatched where category in ('commercial_roll', 'food_roll')) u
    join (select p.lat, p.lng, cell_y(p.lat) + dy.d as cy, cell_x(p.lng) + dx.d as cx
          from core_place p, (values (-1), (0), (1)) dy(d), (values (-1), (0), (1)) dx(d)
          where not regexp_matches(coalesce(p.category, ''), 'apartment|residential|condo|housing|real_estate|property_manag|home_|contractor|landscap|cleaning_serv|pet_sitting|atm|parcel|locker|bitcoin')) p
      on p.cy = u.cy and p.cx = u.cx
    where dist_m(u.lat, u.lng, p.lat, p.lng) <= 40
  )
  -- Two or more new food permits at one door are trucks at their
  -- commissary, stalls in a market hall or the departments of one store.
  , crowded as (
    select source, hn, round(lat, 3) as la, round(lng, 3) as lo
    from unmatched
    where category = 'food_roll' and id not in (select id from lookalike)
    group by all having count(*) > 1
  )
  select 'alm:' || u.source || '/' || u.source_id as place_id, u.*
  from unmatched u
  where u.id not in (select id from lookalike)
    and (u.category not in ('commercial_roll', 'food_roll') or u.id in (select id from anchored))
    and (u.category <> 'food_roll'
         or not exists (select 1 from crowded c where c.source = u.source and c.hn = u.hn
                        and c.la = round(u.lat, 3) and c.lo = round(u.lng, 3)))
  -- one register can list a premises twice, and two registers can list the same shop
  -- (the same name and house number within a few kilometers: a register that lists one
  -- premises under two ZIPs puts its rows on two address points)
  qualify row_number() over (partition by u.nn, u.hn, round(u.lat, 1), round(u.lng, 1) order by u.source, u.source_id) = 1;

insert into core_place
  select place_id, display_name(name), named_category(trade_name(name), case category when 'commercial_roll' then 'commercial_premises' when 'food_roll' then 'food_service' else category end), null, null,
         title_case(split_part(address, ', ', 1)), nullif(title_case(split_part(address, ', ', 2)), ''),
         nullif(regexp_extract(address, ', ([A-Z]{2}) [0-9]{5}', 1), ''), zip, null, null,
         lat, lng, null, nn, hn, false, zip, sk
  from born;
insert into core_names
  select place_id, nn, hn, lat, lng, zip, sk from born;
insert into core_member
  select place_id, source, source_id, 'self', 0.0, 1.0 from born;
insert into core_evidence
  select place_id, source, source_id, state, date, 'self', 0.0, name, address from born;

create or replace table core_status as
  select * from status_of('core_evidence', (select build_date from params), (select recent_days from params));
