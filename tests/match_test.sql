-- Matcher checks. Run: duckdb < tests/match_test.sql
-- Every row is one pair with the rule it should get (or null for no match).
-- Places are invented; coordinates sit in the District of Columbia test box.
.read sql/lib.sql
.bail on

create table cases (n int, a_name text, a_addr text, a_lat double, a_lng double,
                    b_name text, b_addr text, b_lat double, b_lng double, want text);
insert into cases values
  -- same number, name variants a register and a map would use
  (1, 'Bank of America, National Association', '1800 K St NW', 38.9022, -77.0421, 'Bank of America Financial Center', '1800 K Street Northwest', 38.9024, -77.0419, 'number'),
  (2, 'Chase Bank', '700 13th St NW', 38.8990, -77.0296, 'Chase', '700 13th St NW', 38.8991, -77.0297, 'number'),
  (3, 'SAFEWAY 1283', '1855 Wisconsin Ave NW', 38.9150, -77.0672, 'Safeway', '1855 Wisconsin Avenue Northwest', 38.9153, -77.0675, 'number'),
  (4, '7-ELEVEN 34567A', '912 New Hampshire Ave NW', 38.9015, -77.0530, '7-Eleven', '912 New Hampshire Ave NW', 38.9015, -77.0531, 'number'),
  (5, 'Whole Foods Market', '2201 I St NW', 38.9007, -77.0500, 'Wholefoods Market', '2201 I St NW', 38.9008, -77.0501, 'number'),
  -- same number but 250 m is the limit: a geocode a block off still matches, half a mile does not
  (6, 'Giant Food', '1400 7th St NW', 38.9090, -77.0220, 'Giant Food', '1400 7th St NW', 38.9108, -77.0220, 'number'),
  (7, 'Giant Food', '1400 7th St NW', 38.9090, -77.0220, 'Giant Food', '1400 7th St NE', 38.9090, -77.0120, null),
  -- same number, different business: a successor at the address must not match
  (8, 'Bank of Georgetown', '1054 31st St NW', 38.9040, -77.0610, 'Bank of America', '1054 31st St NW', 38.9040, -77.0610, null),
  (9, 'Capital Deli', '500 H St NE', 38.9000, -76.9990, 'Capitol Hill Market', '500 H St NE', 38.9000, -76.9990, null),
  -- chain twins across the street: different numbers, 40 m apart
  (10, 'Starbucks', '1801 K St NW', 38.9026, -77.0421, 'Starbucks', '1800 K St NW', 38.9022, -77.0421, null),
  -- no number on one side: close and same name matches, 100 m does not
  (11, 'Starbucks', null, 38.9022, -77.0421, 'Starbucks', '1800 K St NW', 38.9024, -77.0422, 'near'),
  (12, 'Starbucks', null, 38.9022, -77.0421, 'Starbucks', '1800 K St NW', 38.9031, -77.0421, null),
  (13, 'Chase Bank', null, 38.8990, -77.0296, 'Chase', '700 13th St NW', 38.8991, -77.0297, 'near'),
  -- numbers differ but the two points are on top of each other and the name is identical
  (14, 'Lincoln Theatre', '1215 U St NW', 38.9170, -77.0290, 'The Lincoln Theatre', '1213 U St NW', 38.9171, -77.0290, 'spot'),
  (15, 'Lincoln Theatre', '1215 U St NW', 38.9170, -77.0290, 'Lincoln Theater', '1213 U St NW', 38.9171, -77.0290, null),
  -- only leading words count: a shop named after its mall is not the mall
  (16, 'Fashion Centre at Pentagon City', '1100 S Hayes St', 38.8630, -77.0600, 'Timberland - Fashion Centre at Pentagon City', '1100 S Hayes St', 38.8632, -77.0601, null),
  (18, 'Deli', '10 Main St', 38.9000, -77.0000, 'Corner Deli and Market', '10 Main St', 38.9000, -77.0000, null),
  (19, 'George Town', '1077 Wisconsin Ave NW', 38.9050, -77.0630, 'Georgetown', '3150 M St NW', 38.9051, -77.0631, null),
  -- string similarity under 0.95 is not enough: two embassies, one street
  (20, 'Embassy of Albania', null, 38.9140, -77.0470, 'Embassy of Mali', null, 38.9141, -77.0471, null),
  (21, 'Royal Tobacco', '2604 Connecticut Ave NW', 38.9240, -77.0520, 'Royal Tobaco', '2604 Connecticut Avenue Northwest', 38.9240, -77.0521, 'number'),
  -- bracketed asides and legal forms are not part of the name
  (40, 'Hillside Heights (UIP Properties)', '5237 Marlboro Pike', 38.8700, -76.9200, 'Hillside Heights', '5237 Marlboro Pike #201', 38.8701, -76.9200, 'number'),
  (41, 'Outten & Golden LLP', '1225 New York Ave NW Ste 1200', 38.9003, -77.0290, 'Outten & Golden', '1225 New York Ave NW Suite 1200', 38.9004, -77.0291, 'number'),
  (42, 'Washington Eye Doctors, Pc', '900 17th St NW Ste 400', 38.9010, -77.0390, 'Washington Eye Doctors', '900 17th St NW #400', 38.9011, -77.0391, 'number'),
  (43, 'PC Repair Shop', '10 Main St', 38.9000, -77.0000, 'Repair Shop', '10 Main St', 38.9000, -77.0000, null),
  -- a branch is not the cash machine at the same address
  (22, 'Bank of America', '4301 49th St NW', 38.9450, -77.0960, 'Bank of America ATM', '4301 49th St NW', 38.9450, -77.0960, null),
  -- a credit union is not the agency it is named after
  (23, 'Library of Congress Credit Union', '101 Independence Ave SE', 38.8870, -77.0050, 'Library of Congress Federal Credit Union', '101 Independence Ave SE', 38.8870, -77.0050, 'number'),
  (24, 'Library of Congress Credit Union', '101 Independence Ave SE', 38.8870, -77.0050, 'Library of Congress, Law Library', '101 Independence Ave SE', 38.8870, -77.0050, null),
  (25, 'Justice Credit Union', '601 4th St NW', 38.8970, -77.0160, 'Justice FCU', '601 4th St NW', 38.8970, -77.0160, 'number'),
  (17, 'Inn', '10 Main St', 38.9000, -77.0000, 'Capitol Inn', '10 Main St', 38.9000, -77.0000, null);

create table a as select n as id, norm_name(a_name) nn, house_number(a_addr) hn, a_lat lat, a_lng lng from cases;
create table b as select n as id, norm_name(b_name) nn, house_number(b_addr) hn, b_lat lat, b_lng lng from cases;

create table got as
  select c.n, c.a_name, c.b_name, c.want, m.rule, m.dist, m.sim
  from cases c left join (select * from match_pairs('a', 'b') where a_id = b_id) m on m.a_id = c.n;

.print failures (none is a pass):
select * from got where want is distinct from rule order by n;
select case when (select count(*) from got where want is distinct from rule) = 0
            then 'ok ' || (select count(*) from got) || ' cases'
            else error('matcher test failed') end as result;

-- The address rule, for records with no position.
create table ac (n int, a_name text, a_addr text, a_zip text, b_name text, b_addr text, want boolean);
insert into ac values
  (1, 'Sibley Memorial Hospital', '5255 Loughboro Rd NW', '20016', 'SIBLEY MEMORIAL HOSPITAL', '5255 LOUGHBORO RD NW, WASHINGTON, DC 20016', true),
  (2, 'Elite Dental', '1025 N Fillmore St', '22201', 'ELITE DENTAL', '1025 N FILLMORE ST, ARLINGTON, VA 22201', true),
  -- same number and name, another street in the ZIP
  (3, 'Elite Dental', '1025 N Fillmore St', '22201', 'ELITE DENTAL', '1025 N GLEBE RD, ARLINGTON, VA 22201', false),
  -- same address, another ZIP
  (4, 'Elite Dental', '1025 N Fillmore St', '22201', 'ELITE DENTAL', '1025 N FILLMORE ST, ARLINGTON, VA 22203', false),
  -- same address, another tenant
  (5, 'Elite Dental', '1025 N Fillmore St', '22201', 'FILLMORE EYE CARE', '1025 N FILLMORE ST, ARLINGTON, VA 22201', false);
create table aa as select n as id, norm_name(a_name) nn, house_number(a_addr) hn, a_zip as zip, street_key(a_addr) sk from ac;
create table ab as select n as id, norm_name(b_name) nn, house_number(b_addr) hn, zip5(b_addr) as zip, street_key(b_addr) sk from ac;
select case when (select count(*) from ac c
                  left join (select * from match_address('aa', 'ab') where a_id = b_id) m on m.a_id = c.n
                  where c.want <> (m.rule is not null)) = 0
            then 'ok 5 address cases' else error('address test failed') end as result;

-- A closure joined by id only applies while the names still agree.
select case when same_name('Sunoco', 'SUNOCO #1234') and same_name('Bar Pilar', 'Bar Pilar')
                 and not same_name('Sunoco', 'Shell') and not same_name('Mirabelle', 'Le Diplomate')
            then 'ok 4 name check cases' else error('name check test failed') end as result;

-- Names and streets for places that come from a register.
select case when display_name('MARCO POLO BAR & GRILL #2') = 'Marco Polo Bar & Grill'
                 and display_name('BOB''S BBQ') = 'Bob''s BBQ'
                 and display_name('T-MOBILE') = 'T-Mobile'
                 and display_name('7-ELEVEN STORE 22358A') = '7-Eleven Store 22358A'
                 and display_name('FAMILY DOLLAR STORE #31487') = 'Family Dollar'
                 and display_name('Café Loup') = 'Café Loup'
                 and title_case('1312 NE 43RD ST') = '1312 NE 43rd St'
                 and title_case('100 A&P PLZ') = '100 A&P Plz'
            then 'ok 8 display name cases' else error('display name test failed') end as result;

-- Trade names, and the words that tell one shop from its neighbor.
select case when norm_name('Vanguard Restaurant Group LLC dba Fuego') = 'fuego'
                 and display_name('SC HUNTSVILLE INC DBA SUPER CHIX #12') = 'Super Chix'
                 and norm_name('DBA Coffee') = 'dba coffee'
                 and list_has_any(name_words('airport rd chevron'), name_words('chevron'))
                 and not list_has_any(name_words('hibachi express'), name_words('garden room restaurant'))
                 and initials('kentucky fried chicken') = 'kfc'
            then 'ok 6 trade name cases' else error('trade name test failed') end as result;

-- The kind of an added place, read from its name.
select case when named_category('Richards Liquors', 'licensed_premises') = 'shop=alcohol'
                 and named_category('Supreme Smoke & Vape 3', 'grocery_or_convenience_store') = 'shop=tobacco'
                 and named_category('Murphy Chevron', 'grocery_or_convenience_store') = 'amenity=fuel'
                 and named_category('Last Call Sports Bar', 'licensed_premises') = 'amenity=bar'
                 and named_category('Fu Shu Restaurant', 'licensed_premises') = 'amenity=restaurant'
                 and named_category('Tipsy Chango', 'licensed_premises') = 'licensed_premises'
                 and named_category('First National Bank', 'bank') = 'bank'
            then 'ok 7 named category cases' else error('named category test failed') end as result;
