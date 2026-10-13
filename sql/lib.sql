-- Shared macros: name and house number normalization, distance, and the one
-- matcher used for both the base merge and the evidence match.
-- Thresholds are stated in SPEC.md and exercised by tests/match_test.sql.

-- lowercase, no accents, no punctuation
create or replace macro clean_name(s) as
  trim(regexp_replace(
    regexp_replace(regexp_replace(lower(strip_accents(s)), '[''’`.]', '', 'g'), '&', ' and ', 'g'),
    '[^a-z0-9]+', ' ', 'g'));

-- "Vanguard Restaurant Group LLC dba Fuego" trades as "Fuego"
create or replace macro trade_name(s) as
  regexp_replace(s, '^.+\s(dba|d/b/a|d\.b\.a\.?)[: ][\s>:-]*', '', 'i');

-- clean_name minus bracketed asides, legal suffixes, articles and trailing
-- store numbers: "Hillside Heights (UIP Properties)" and "Outten & Golden
-- LLP" are "hillside heights" and "outten and golden". "PC" and "APC" count
-- as a legal form only at the end of a name. Falls back to clean_name when
-- nothing would be left.
create or replace macro norm_name(s) as
  coalesce(
    nullif(trim(regexp_replace(
      regexp_replace(
        -- every way of writing "credit union" becomes one word, so that
        -- "Justice FCU" and "Justice Federal Credit Union" are the same name
        regexp_replace(regexp_replace(regexp_replace(
                         clean_name(regexp_replace(trade_name(s), '\([^)]*\)', ' ', 'g')), '( [0-9]+)+$', ''),
                         ' (pc|apc)$', ''),
                       '\b(federal credit union|credit union|fcu)\b', 'cu', 'g'),
        '\b(the|inc|incorporated|llc|llp|pllc|ltd|corp|corporation|company|co|national association|na|branch|sarl|sas|sasu|eurl|sa|sci|snc|societe|ste|ets|etablissements)\b', ' ', 'g'),
      ' +', ' ', 'g')), ''),
    clean_name(s));

-- The words of a normalized name that can identify a business: three
-- letters or more and not a word half the street shares.
create or replace macro name_words(nn) as
  list_filter(string_split(nn, ' '), lambda w: length(w) >= 3
    and w not in ('restaurant', 'food', 'foods', 'store', 'shop', 'grill', 'cafe', 'pizza', 'market', 'house', 'kitchen',
                  'express', 'center', 'street', 'avenue', 'north', 'south', 'east', 'west', 'and', 'bar', 'inn', 'new',
                  'old', 'big', 'usa', 'los', 'las', 'del', 'mart', 'deli', 'mini', 'stop', 'one', 'two'));
-- "kentucky fried chicken" -> "kfc"
create or replace macro initials(nn) as
  array_to_string(list_transform(string_split(nn, ' '), lambda w: w[1]), '');

-- A certificate of occupancy names its occupant in the applicant's own
-- words: a business, a landlord, a person, a building, a street address.
-- A name becomes a place only when it carries a word a shop puts on its
-- sign and something besides: "Cowser Tire", not "Restaurant Taqueria",
-- "Tobias Place Bldg 7" or "Saul Mendoza".
create or replace macro shop_words() as
  '\b(restaurante?|taqueria|cantina|cafe|coffee|grill|kitchen|pizza|pizzeria|burgers?|tacos?|bbq|barbecue|bakery|panaderia|donuts?|bar|pub|tavern|brewery|lounge|salon|barber|barbershop|spa|nails?|lashes|beauty|tattoo|smoke|vape|tobacco|liquor|wine|market|mart|grocery|carniceria|store|shop|boutique|outlet|tires?|autos?|motors|cleaners|laundry|pharmacy|dental|dentistry|clinic|chiropractic|fitness|gym|daycare|montessori|bonds|insurance|jewelry|furniture|florist|flowers|pets?|veterinary|bank|hotel|motel|dulceria|fruteria|paleteria|supermercado|creamery|bistro|diner|sushi|pho|wings|chicken|seafood|steakhouse)\b';
create or replace macro reads_as_shop(name) as
  -- a store number has three digits or more; "#1" and "#9" are a landlord's units
  regexp_matches(name, shop_words() || '|#\s*[0-9]{3,}', 'i')
  -- a machine or a counter inside someone else's store
  and not regexp_matches(name, '@| at | atm\b|cardtronics|coinstar|redbox', 'i')
  and not regexp_matches(name, '\b(bldg|building|phase|remodel|suite|ste|shell|addition|finish.?out|tenant|properties|property|apartments|residences|holdings|investments|realty|mobile|floor|unit|transport|transportation|trucking|logistics|towing|catering|events?|towers?|vending|decal|on wheels)\b|tag ?#', 'i')
  -- something is left once the trade words and small words are taken out
  and length(regexp_replace(regexp_replace(regexp_replace(lower(name), shop_words(), ' ', 'g'),
                                           '\b(the|and|of|de|la|el|los|las|del|y|no|inc|llc|co)\b', ' ', 'g'), '[^a-z0-9]', '', 'g')) >= 2;

-- A register gives an added place a coarse kind ("licensed premises"). Its
-- name often says more. Only plain words are read, and a name that says
-- nothing keeps the register's kind. Values are the tags OSM uses, which
-- the category groups already know.
create or replace macro named_category(name, fallback) as
  case
    when fallback not in ('licensed_premises', 'grocery_or_convenience_store', 'food_service', 'restaurant', 'commercial_premises') then fallback
    when regexp_matches(name, '\b(liquors?|spirits|bottle shop|package store|beverage (depot|warehouse|house)|wine (and|&) spirits|wines?( shop| store| cellar| merchants?)?$)', 'i') then 'shop=alcohol'
    when regexp_matches(name, '\b(smoke|smokes|vape|vapor|tobacco|cigars?|hookah)\b', 'i') then 'shop=tobacco'
    when regexp_matches(name, '\b(pharmacy|drugs?|rx)\b', 'i') then 'amenity=pharmacy'
    when regexp_matches(name, '\b(fuels?|gas|petroleum|exxon|shell|chevron|mobil|valero|texaco|citgo|conoco|sunoco|marathon|phillips 66|sinclair|speedway|arco|bp)\b', 'i') then 'amenity=fuel'
    when regexp_matches(name, '\b(juice|smoothies?|salad|acai|coffee|espresso|yogurt|dessert)\b.*\bbar\b', 'i') then 'amenity=cafe'
    -- a nail bar or a brow bar pours nothing
    when regexp_matches(name, '\b(nails?|lash|lashes|brows?|hair|blow ?dry|beauty|wax)\b.*\bbar\b', 'i') then (case when fallback = 'commercial_premises' then 'shop=beauty' else fallback end)
    when regexp_matches(name, '\b(bar|pub|tavern|saloon|lounge|taproom|tap room|brewery|brewing|cantina|nightclub|night club|icehouse|ice house|sports bar)\b', 'i') then 'amenity=bar'
    -- "Florida Kitchen Cabinets" is not a kitchen
    when regexp_matches(name, '\b(cabinets?|countertops?|granite|flooring|remodeling)\b', 'i') then fallback
    when regexp_matches(name, '\b(coffee|cafe|café|espresso|tea house|bakery|donuts?)\b', 'i') then 'amenity=cafe'
    when regexp_matches(name, '\b(restaurant|grill|grille|kitchen|pizza|pizzeria|taqueria|tacos?|sushi|bbq|barbecue|barbeque|diner|bistro|steakhouse|noodles?|ramen|pho|burgers?|wings|seafood|cuisine|eatery|buffet|deli|tortas|mariscos|hibachi|trattoria|cocina)\b', 'i') then 'amenity=restaurant'
    when regexp_matches(name, '\b(supermarket|super market|supermercado|carniceria|meat market|market place|marketplace)\b', 'i') then 'shop=supermarket'
    when regexp_matches(name, '\b(mart|foodmart|market|mini|convenience|c-store|food store|grocery|groceries|quick|kwik|stop|corner store|express|tienda|bodega|7-eleven|circle k)\b', 'i') then 'shop=convenience'
    -- a certificate of occupancy says nothing of the trade, so the name is read for more
    when fallback <> 'commercial_premises' then fallback
    when regexp_matches(name, '\b(salon|barber|barbershop|hair|braids?)\b', 'i') then 'shop=hairdresser'
    when regexp_matches(name, '\b(nails?|lashes|beauty|spa|brows?|waxing)\b', 'i') then 'shop=beauty'
    when regexp_matches(name, '\b(tattoo|ink)\b', 'i') then 'shop=tattoo'
    when regexp_matches(name, '\b(tires?|llantas)\b', 'i') then 'shop=tyres'
    when regexp_matches(name, '\b(auto sales?|autos|motors|car sales)\b', 'i') then 'shop=car'
    when regexp_matches(name, '\b(auto repair|automotive|collision|body shop|mechanic)\b', 'i') then 'shop=car_repair'
    when regexp_matches(name, '\b(dental|dentistry|orthodontics)\b', 'i') then 'amenity=dentist'
    when regexp_matches(name, '\b(veterinary|animal hospital)\b', 'i') then 'amenity=veterinary'
    when regexp_matches(name, '\b(clinic|chiropractic|urgent care)\b', 'i') then 'amenity=clinic'
    when regexp_matches(name, '\b(fitness|gym|pilates|yoga|crossfit)\b', 'i') then 'leisure=fitness_centre'
    when regexp_matches(name, '\b(cleaners|laundry|lavanderia|laundromat)\b', 'i') then 'shop=laundry'
    when regexp_matches(name, '\b(boutique|clothing|apparel)\b', 'i') then 'shop=clothes'
    when regexp_matches(name, '\b(jewelry|jewelers)\b', 'i') then 'shop=jewelry'
    when regexp_matches(name, '\b(furniture|mattress)\b', 'i') then 'shop=furniture'
    when regexp_matches(name, '\b(florist|flowers|floreria)\b', 'i') then 'shop=florist'
    when regexp_matches(name, '\b(insurance|seguros)\b', 'i') then 'office=insurance'
    when regexp_matches(name, '\b(hotel|motel|inn|suites)\b', 'i') then 'tourism=hotel'
    when regexp_matches(name, '\b(daycare|day care|child care|montessori|preschool)\b', 'i') then 'amenity=childcare'
    else fallback
  end;

-- leading street number of an address, digits only
create or replace macro house_number(addr) as
  nullif(regexp_extract(addr, '^\s*#?\s*([0-9]+)', 1), '');

-- meters between two points, flat approximation (fine under a kilometer)
create or replace macro dist_m(lat1, lng1, lat2, lng2) as
  111320.0 * sqrt(pow(lat1 - lat2, 2) + pow((lng1 - lng2) * cos(radians((lat1 + lat2) / 2)), 2));

-- similarity of two normalized names, 0 to 1
--   1.0  identical
--   0.9  the shorter name (at least 4 letters) is the leading words of the
--        longer one: "giant" and "giant food", "pnc bank" and "pnc bank mlk".
--        Leading only: "fashion centre" inside "timberland fashion centre" is
--        a shop named after the mall it sits in, not the mall.
--   else Jaro-Winkler on the strings with spaces removed, which catches
--        spelling variants; the rules only trust it from 0.95
--   0    one name is a cash machine and the other is not: a branch closing
--        says nothing about the ATM left behind, and the reverse
create or replace macro name_sim(a, b) as
  case
    when a = b then 1.0
    when (a = 'atm' or a like '% atm' or a like '% atm %') <> (b = 'atm' or b like '% atm' or b like '% atm %') then 0.0
    when length(a) >= 4 and starts_with(b, a || ' ') then 0.9
    when length(b) >= 4 and starts_with(a, b || ' ') then 0.9
    else least(jaro_winkler_similarity(replace(a, ' ', ''), replace(b, ' ', '')), 0.99)
  end;

-- Grid cell for the hash join. Cells are about 440 m tall and at least 370 m
-- wide anywhere in the contiguous states, so every pair within 250 m sits in
-- the same or a neighboring cell.
create or replace macro cell_y(lat) as cast(floor(lat / 0.004) as integer);
create or replace macro cell_x(lng) as cast(floor(lng / 0.008) as integer);

-- match_pairs('a', 'b'): every pair of rows that passes a rule.
-- Both tables need: id, nn (norm_name), hn (house_number), lat, lng.
--   number  same house number, within 250 m, name_sim >= 0.9
--   near    house number missing on a side, within 60 m, name_sim >= 0.9
--   spot    house numbers differ, within 30 m, identical normalized names
-- Jaro-Winkler scores count only from 0.95.
create or replace macro match_pairs(ta, tb) as table (
  with a as (
    select id, nn, hn, lat, lng, cell_y(lat) as cy, cell_x(lng) as cx from query_table(ta)
  ),
  b as (
    select t.id, t.nn, t.hn, t.lat, t.lng, cell_y(t.lat) + dy.d as cy, cell_x(t.lng) + dx.d as cx
    from query_table(tb) t, (values (-1), (0), (1)) dy(d), (values (-1), (0), (1)) dx(d)
  ),
  c as (
    select a.id as a_id, b.id as b_id, a.hn as a_hn, b.hn as b_hn,
           dist_m(a.lat, a.lng, b.lat, b.lng) as dist,
           name_sim(a.nn, b.nn) as sim
    from a join b on a.cy = b.cy and a.cx = b.cx
  )
  select a_id, b_id, round(dist, 1) as dist, round(sim, 3) as sim,
         case
           when a_hn = b_hn and dist <= 250 and (sim in (1.0, 0.9) or sim >= 0.95) then 'number'
           when (a_hn is null or b_hn is null) and dist <= 60 and (sim in (1.0, 0.9) or sim >= 0.95) then 'near'
           when a_hn <> b_hn and dist <= 30 and sim = 1.0 then 'spot'
         end as rule
  from c
  where rule is not null
);

-- For records that come with an address but no position.
create or replace macro zip5(s) as nullif(regexp_extract(s, '([0-9]{5})(-[0-9]{4})?\s*$', 1), '');

-- First distinctive word of the street name, after the number and any
-- compass word, French street type or article: "1108 N Ross Clark Cir" ->
-- "ross", "12 bis Rue de la Paix" -> "paix". Enough to tell two streets in
-- one postal code apart.
create or replace macro street_key(addr) as
  nullif(regexp_extract(lower(strip_accents(addr)),
    '^\s*#?\s*[0-9]+[a-z]?\s+(?:(?:bis|ter|n|s|e|w|ne|nw|se|sw|north|south|east|west|rue|avenue|av|boulevard|bd|place|pl|quai|impasse|allee|chemin|cours|passage|square|villa|cite|faubourg|fg|route|rte|de|du|des|la|le|les|l|d|saint|st)[. '']+)*([a-z0-9]+)', 1), '');

-- match_address('a', 'b'): pairs with the same ZIP, house number and street
-- word, and a name that passes the same test as the other rules.
-- Both tables need: id, nn, hn, zip, sk.
create or replace macro match_address(ta, tb) as table (
  select a.id as a_id, b.id as b_id, null::double as dist, round(name_sim(a.nn, b.nn), 3) as sim,
         'address' as rule
  from query_table(ta) a join query_table(tb) b
    on a.zip = b.zip and a.hn = b.hn and a.sk = b.sk
  where name_sim(a.nn, b.nn) in (1.0, 0.9) or name_sim(a.nn, b.nn) >= 0.95
);

-- Kinds of place that cannot trade without an alcohol license.
create or replace macro needs_alcohol_license(category) as
  category in ('bar', 'pub', 'sports_bar', 'cocktail_bar', 'wine_bar', 'dive_bar', 'lounge', 'beer_bar',
               'irish_pub', 'gay_bar', 'night_club', 'dance_club', 'hookah_bar', 'gastropub', 'brewery',
               'amenity=bar', 'amenity=pub', 'amenity=nightclub');

-- Do two names pass the matcher's name test? Used to check that a closure
-- joined by id still belongs to the business the place is named for today.
create or replace macro same_name(a, b) as
  name_sim(norm_name(a), norm_name(b)) in (1.0, 0.9) or name_sim(norm_name(a), norm_name(b)) >= 0.95;

-- Registers write names and streets in capitals. For a place that exists
-- only because a register lists it, show the text the way a sign would:
-- "MARCO POLO BAR & GRILL #2" becomes "Marco Polo Bar & Grill". Words with
-- no vowel (BBQ, CVS), compass points and roman numerals stay in capitals.
-- Text that already has lowercase letters is left alone.
create or replace macro title_case(s) as
  case when s is null or s <> upper(s) or not regexp_matches(s, '[A-Z]') then s
  else replace(array_to_string(list_transform(
         string_split(regexp_replace(trim(s), '([-&/.(])', '\1' || chr(1) || ' ', 'g'), ' '),
         lambda w: case
           when regexp_matches(w, '^(NE|NW|SE|SW|II|III|IV|VI|VII|USA|US|PO)$') or regexp_matches(w, '^[0-9]+[A-Z]$') then w
           when regexp_matches(w, '^(ST|RD|DR|LN|CT|PL|PLZ|HWY|PKY|TRL|SQ|FL|MR|MRS|JR|SR|LTD|STE|BLDG)[-&/.]?' || chr(1) || '?$')
             then upper(w[1]) || lower(w[2:])
           when length(replace(w, chr(1), '')) between 2 and 4 and regexp_matches(w, '^[B-DF-HJ-NP-TV-XZ]+[-&/.]?' || chr(1) || '?$') then w
           else upper(w[1]) || lower(w[2:]) end), ' '), chr(1) || ' ', '') end;
create or replace macro display_name(s) as
  title_case(trim(regexp_replace(trade_name(s), '\s*(#\s*[0-9]+[A-Z]?|\bSTORE\s+#?[0-9]+)\s*$', '')));
