-- Numbers for one built region. Run through stats.sh.
.print == places in
select (select count(*) from ovt) as overture, (select count(*) from atp) as alltheplaces,
       (select count(*) from osm) as osm, (select count(*) from osm where lifecycle is not null) as osm_closed_features;

.print == merged (rows that joined an existing place, by rule)
select 'overture duplicates' as step, rule, count(*) as "rows" from core_member where source = 'overture' and rule <> 'self' group by all
union all
select 'alltheplaces -> overture' as step, rule, count(*) as "rows" from atp_match group by all
union all
select 'osm -> core', rule, count(*) from osm_match group by all
order by 1, 2;

.print == places out
select (select count(*) from out_core) as core, (select count(*) from out_full) as "full",
       (select count(*) from osm_only) as osm_only,
       (select count(*) from core_place where id like 'atp:%') as atp_only,
       (select count(*) from born) as from_registers;

.print == places minted from a register
select source, count(*) as places from born group by 1 order by 1;

.print == status, full layer
select status, count(*) as places from out_full group by 1 order by 1;

.print == status, core layer (no OSM)
select status, count(*) as places from out_core group by 1 order by 1;

.print == register records in the box and how many found a place
select r.source, r.state, count(*) as records,
       count(*) filter (where exists (select 1 from full_evidence e
                                      where e.source = r.source and e.source_id = r.source_id)) as matched
from register r group by all order by 1, 2;

.print == evidence by source and rule (places is distinct places)
select source, state, rule, count(*) as "rows", count(distinct place_id) as places
from full_evidence group by all order by 1, 2, 3;

.print == what decided the status
select status, status_source, count(*) as places from out_full where status <> 'unknown' group by all order by 1, 2;

.print == closing signals against independent evidence
.print == (says_open_after: a different source saw the place open after the closing date)
with c as (
  select place_id, source, max(date) as d from full_evidence where state = 'closed' group by all
)
select c.source, count(*) as places,
       count(*) filter (where exists (
         select 1 from full_evidence e where e.place_id = c.place_id and e.state = 'open' and e.date > c.d
           and split_part(e.source, '_', 1) <> split_part(c.source, '_', 1))) as says_open_after,
       count(*) filter (where exists (
         select 1 from full_evidence e where e.place_id = c.place_id and e.state = 'closed'
           and split_part(e.source, '_', 1) <> split_part(c.source, '_', 1))) as says_closed_too
from c group by 1 order by 1;

.print == Overture operating_status against our status
select coalesce(overture_status, '(none)') as overture_status, status, count(*) as places
from out_full where id like 'ovt:%' group by all order by 1, 2;
