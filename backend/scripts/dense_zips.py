"""
Dense US ZIP code grid for near-complete NREL EV charger coverage.

Use with 10-mile radius queries. ZIPs are spaced ~15 miles apart so
circles overlap, covering virtually all populated areas plus interstate
corridors.  Roughly 1,800 ZIPs across all 50 states + DC.

Usage:
    from scripts.dense_zips import DENSE_STATE_ZIPS
"""

DENSE_STATE_ZIPS = {
    # ── Alabama (30 ZIPs) ──────────────────────────────────────────────
    "AL": [
        # Birmingham metro
        "35203", "35209", "35215", "35226", "35244", "35004", "35094",
        "35124", "35173", "35071",
        # Huntsville / Decatur
        "35801", "35758", "35601", "35630",
        # Montgomery
        "36104", "36117",
        # Mobile / Baldwin
        "36602", "36608", "36526", "36535",
        # Tuscaloosa
        "35401", "35405",
        # Auburn / Opelika, Dothan, Gadsden, Florence, Anniston
        "36830", "36301", "35901", "35632", "36201",
        # Prattville, Enterprise, Selma, Phenix City, Albertville
        "36067", "36330", "36701", "36867", "35950",
        # Corridor fill (I-65, I-20, I-59)
        "36460", "35055", "36265", "36016",
    ],

    # ── Alaska (12 ZIPs) ───────────────────────────────────────────────
    "AK": [
        "99501", "99504", "99515",  # Anchorage
        "99701", "99709",            # Fairbanks
        "99801",                     # Juneau
        "99611", "99654", "99577",   # Kenai / Wasilla / Eagle River
        "99645", "99669",            # Palmer / Soldotna
        "99901",                     # Ketchikan
    ],

    # ── Arizona (35 ZIPs) ─────────────────────────────────────────────
    "AZ": [
        # Phoenix metro grid
        "85003", "85008", "85016", "85022", "85032", "85042", "85051",
        "85083", "85201", "85210", "85224", "85233", "85248", "85251",
        "85260", "85281", "85301", "85310", "85338", "85340", "85345",
        "85374", "85382", "85392",
        # Tucson
        "85701", "85710", "85730", "85741", "85745",
        # Flagstaff, Prescott, Yuma, Lake Havasu, Sierra Vista
        "86001", "86301", "85364", "86403", "85635",
        # Kingman, Casa Grande, Globe, Nogales, Show Low
        "86401", "85122", "85501", "85621", "85901",
    ],

    # ── Arkansas (20 ZIPs) ─────────────────────────────────────────────
    "AR": [
        # Little Rock metro
        "72201", "72205", "72211", "72223", "72116", "72032",
        # Fayetteville / Springdale / Bentonville / Rogers
        "72701", "72764", "72712", "72756",
        # Fort Smith, Jonesboro, Pine Bluff, Hot Springs, Texarkana
        "72901", "72401", "71601", "71901", "71854",
        # Conway, Russellville, El Dorado, Batesville, West Memphis
        "72034", "72801", "71730", "72501", "72301",
    ],

    # ── California (85 ZIPs) ──────────────────────────────────────────
    "CA": [
        # Los Angeles basin
        "90012", "90024", "90036", "90045", "90064", "90077",
        "90210", "90245", "90274", "90291", "90401", "90501",
        "90620", "90680", "90703", "90802",
        # San Fernando / Santa Clarita / Burbank / Pasadena
        "91001", "91107", "91301", "91321", "91355", "91601", "91702",
        # Inland Empire
        "91701", "91764", "91786", "92223", "92324", "92336", "92373",
        "92501", "92571", "92590",
        # Orange County
        "92618", "92660", "92708", "92801", "92868",
        # San Diego
        "92101", "92111", "92126", "92154", "92064", "92025", "92071",
        # Central Coast
        "93001", "93101", "93301", "93401", "93454",
        # San Joaquin Valley
        "93203", "93230", "93257", "93637", "93706", "93720", "95301",
        # San Jose / Silicon Valley
        "95008", "95050", "95112", "95128", "95148",
        # East Bay / Oakland
        "94538", "94566", "94577", "94612", "94806",
        # San Francisco / Peninsula
        "94102", "94112", "94301", "94401",
        # North Bay
        "94901", "94928", "94954", "95401",
        # Sacramento metro
        "95610", "95660", "95691", "95814", "95826", "95843",
        # Stockton, Modesto, Merced
        "95207", "95355", "95340",
        # Far north / mountain / desert
        "96001", "96150", "92264", "93561", "95521",
        # Victorville / Hesperia, Palmdale / Lancaster, Temecula
        "92392", "93550", "92591",
        # Santa Cruz, San Luis Obispo fill, Eureka
        "95060", "93405",
    ],

    # ── Colorado (30 ZIPs) ─────────────────────────────────────────────
    "CO": [
        # Denver metro grid
        "80202", "80219", "80231", "80239", "80249",
        "80013", "80112", "80120", "80401", "80465",
        # Front Range corridor
        "80301", "80501", "80525", "80538",  # Boulder / Longmont / Fort Collins
        "80903", "80918", "80922",            # Colorado Springs
        "81001", "81008",                     # Pueblo
        # I-70 corridor
        "80461", "80487", "81611", "81632",
        # I-25 corridor / other cities
        "80631",                              # Greeley
        "80549",                              # Wellington
        # Western slope
        "81301", "81401", "81501", "81625",
        # Southern
        "81101", "81201",
        # Montrose, Craig, Trinidad, Sterling, Burlington, La Junta
        "81082", "80751", "80807", "81050",
    ],

    # ── Connecticut (18 ZIPs) ──────────────────────────────────────────
    "CT": [
        # Hartford metro
        "06103", "06002", "06040", "06074", "06032",
        # New Haven
        "06510", "06511",
        # Bridgeport / Stamford / Norwalk / Danbury
        "06604", "06901", "06851", "06810",
        # New London / Norwich / Waterbury / Torrington / Middletown
        "06320", "06360", "06702", "06790", "06457",
        # Corridor fill
        "06401", "06226",
    ],

    # ── Delaware (10 ZIPs) ─────────────────────────────────────────────
    "DE": [
        "19801", "19802", "19711", "19720",  # Wilmington / Newark / New Castle
        "19901", "19904",                     # Dover
        "19958", "19966", "19971",            # Sussex County beaches / Georgetown
        "19947",                              # Georgetown
    ],

    # ── Florida (55 ZIPs) ──────────────────────────────────────────────
    "FL": [
        # Miami-Dade
        "33101", "33125", "33132", "33155", "33176", "33186", "33010",
        # Broward
        "33060", "33160", "33301", "33309", "33316", "33324", "33071",
        # Palm Beach
        "33401", "33411", "33431", "33480", "33446",
        # Orlando metro
        "32801", "32819", "32835", "32746", "34747", "32703", "32765",
        "34786", "32837",
        # Tampa / St Pete
        "33601", "33609", "33647", "33701", "33760", "33572", "33510",
        # Jacksonville
        "32099", "32207", "32256", "32225",
        # Southwest FL
        "34102", "34109", "33950", "34236", "34231",
        # Space Coast / Treasure Coast
        "32901", "34950", "34952",
        # Panhandle
        "32301", "32501", "32541",
        # Central corridor
        "34601", "34482", "32605", "33801", "33870",
        # I-75 / I-95 fill
        "34201", "32136", "34691", "33570",
        # Port Charlotte, Sebring, Clewiston, Key West
        "33952", "33872", "33440", "33040",
    ],

    # ── Georgia (35 ZIPs) ──────────────────────────────────────────────
    "GA": [
        # Atlanta metro grid
        "30303", "30318", "30324", "30339", "30350",
        "30009", "30043", "30060", "30075", "30097",
        "30144", "30189", "30214", "30265", "30281",
        # Savannah
        "31401", "31404", "31419",
        # Augusta
        "30901", "30909",
        # Macon / Warner Robins
        "31201", "31008",
        # Columbus, Athens, Albany, Valdosta, Brunswick, Rome, Dalton
        "31901", "30601", "31701", "31601", "31520", "30165", "30720",
        # Gainesville, Carrollton, Milledgeville, Waycross, Tifton
        "30501", "30117", "31061", "31501", "31794",
        # Corridor fill (I-75, I-16, I-95, I-85)
        "30474", "31301", "30401", "30680", "31791",
    ],

    # ── Hawaii (10 ZIPs) ───────────────────────────────────────────────
    "HI": [
        "96813", "96817", "96822",  # Honolulu
        "96706", "96707", "96789",  # Ewa / Kapolei / Mililani
        "96734", "96786",           # Windward / Wahiawa
        "96732", "96720",           # Maui / Big Island
    ],

    # ── Idaho (20 ZIPs) ────────────────────────────────────────────────
    "ID": [
        # Boise metro
        "83702", "83709", "83616", "83646", "83686", "83651", "83605",
        # Coeur d'Alene / Moscow
        "83814", "83843", "83864",
        # Pocatello / Idaho Falls / Twin Falls
        "83201", "83210", "83401", "83440", "83301",
        # Lewiston
        "83501",
        # Corridor fill (I-84, I-15, US-93)
        "83338", "83520", "83228", "83341",
    ],

    # ── Illinois (35 ZIPs) ─────────────────────────────────────────────
    "IL": [
        # Chicago metro grid
        "60601", "60605", "60614", "60629", "60639", "60647", "60657",
        "60007", "60085", "60104", "60148", "60302", "60435", "60440",
        "60505", "60540", "60586",
        # Rockford, Champaign, Springfield, Peoria, Bloomington
        "61101", "61801", "62701", "61602", "61701",
        # Quad Cities / DeKalb / Kankakee / Carbondale
        "61265", "60115", "60901", "62901",
        # Decatur, Quincy, Effingham, Marion, Galesburg
        "62521", "62301", "62401", "62959", "61401",
        # Metro East (St. Louis)
        "62002", "62040",
        # Sterling / Dixon, Ottawa, Danville, Mt Vernon, Centralia
        "61081", "61350", "61832", "62864", "62801",
        # I-55 / I-57 corridor
        "60964", "62454",
    ],

    # ── Indiana (25 ZIPs) ──────────────────────────────────────────────
    "IN": [
        # Indianapolis metro
        "46204", "46220", "46237", "46254", "46060", "46143",
        # Fort Wayne, South Bend, Evansville, Lafayette, Terre Haute
        "46802", "46815", "46601", "47708", "47901", "47802",
        # Gary / NW Indiana, Bloomington, Columbus, New Albany
        "46312", "46383", "47401", "47201", "47130",
        # Muncie, Anderson, Kokomo, Elkhart
        "47302", "46016", "46902", "46530",
        # Marion, Vincennes, Crawfordsville, Jasper
        "46952", "47591", "47933", "47546",
        # Corridor fill (I-65, I-69, I-70)
        "47274", "46580", "46350",
    ],

    # ── Iowa (22 ZIPs) ────────────────────────────────────────────────
    "IA": [
        # Des Moines metro
        "50309", "50312", "50322", "50266",
        # Cedar Rapids / Iowa City
        "52401", "52241", "52240",
        # Davenport (Quad Cities), Dubuque, Sioux City, Council Bluffs
        "52801", "52001", "51101", "51501",
        # Waterloo / Cedar Falls, Ames, Mason City
        "50701", "50010", "50401",
        # Burlington, Ottumwa, Fort Dodge, Marshalltown
        "52601", "52501", "50501", "50158",
        # Spencer, Carroll, Clinton, Creston, Grinnell, Keokuk
        "51301", "51401", "52732", "50801", "50112", "52632",
        # Denison, Pella, Red Oak, Decorah
        "51442", "50219", "51566", "52101",
    ],

    # ── Kansas (20 ZIPs) ───────────────────────────────────────────────
    "KS": [
        # Wichita
        "67202", "67212", "67226", "67235",
        # Kansas City / Overland Park / Olathe
        "66101", "66204", "66061",
        # Topeka, Lawrence, Manhattan
        "66603", "66044", "66502",
        # Salina, Hutchinson, Emporia, Dodge City, Garden City
        "67401", "67501", "66801", "67801", "67846",
        # Hays, Liberal, Junction City, Pittsburg, Leavenworth
        "67601", "67901", "66441", "66762", "66048",
        # Great Bend, McPherson, Winfield, Coffeyville, Colby
        "67530", "67460", "67156", "67337", "67701",
    ],

    # ── Kentucky (25 ZIPs) ─────────────────────────────────────────────
    "KY": [
        # Louisville metro
        "40202", "40214", "40222", "40229", "40241",
        # Lexington
        "40502", "40509", "40517",
        # Northern KY (Cincinnati metro)
        "41011", "41075",
        # Bowling Green, Owensboro, Paducah, Ashland, Florence
        "42101", "42301", "42001", "41101", "41042",
        # Richmond, Elizabethtown, Frankfort, Hopkinsville, Somerset
        "40475", "42701", "40601", "42240", "42501",
        # Corbin, Pikeville, Madisonville, London
        "40701", "41501", "42431", "40741",
        # I-64 / I-75 fill
        "40324", "40422",
    ],

    # ── Louisiana (22 ZIPs) ────────────────────────────────────────────
    "LA": [
        # New Orleans metro
        "70112", "70119", "70130", "70001", "70056", "70072",
        # Baton Rouge
        "70801", "70808", "70816",
        # Shreveport / Bossier
        "71101", "71111",
        # Lafayette, Lake Charles, Monroe, Alexandria
        "70501", "70607", "71201", "71301",
        # Houma, Slidell, Hammond, Ruston, Natchitoches
        "70360", "70458", "70401", "71270", "71457",
        # Opelousas, Thibodaux, Minden, Bastrop, DeRidder
        "70570", "70301", "71055", "71220", "70634",
        # I-10 / I-20 fill
        "70535", "70380",
    ],

    # ── Maine (15 ZIPs) ────────────────────────────────────────────────
    "ME": [
        # Portland metro
        "04101", "04106",
        # South Portland, Scarborough, Biddeford, Saco
        "04074", "04005",
        # Lewiston / Auburn, Augusta, Bangor
        "04240", "04330", "04401",
        # Brunswick, Waterville, Sanford, Presque Isle, Ellsworth
        "04011", "04901", "04073", "04769", "04605",
        # Corridor fill (I-95, US-1)
        "04210", "04736", "04938",
        # Rockland, Skowhegan, Rumford, Houlton, Machias, Farmington
        "04841", "04976", "04276", "04730", "04654",
    ],

    # ── Maryland (25 ZIPs) ─────────────────────────────────────────────
    "MD": [
        # Baltimore metro
        "21201", "21215", "21224", "21228", "21234", "21244",
        # DC suburbs
        "20814", "20852", "20901", "20910", "20706", "20774", "20850",
        # Frederick, Hagerstown, Annapolis, Salisbury, Cumberland
        "21701", "21740", "21401", "21801", "21502",
        # Columbia, Bel Air, Waldorf, College Park
        "21044", "21014", "20601", "20740",
        # Easton, Elkton, La Plata, Westminster
        "21601", "21921", "20646", "21157",
        # Corridor fill (I-95, I-70, I-81)
        "21078",
    ],

    # ── Massachusetts (25 ZIPs) ────────────────────────────────────────
    "MA": [
        # Boston metro
        "02101", "02119", "02134", "02148", "02169",
        # Inner suburbs
        "02138", "02446", "02180", "02155", "02149",
        # Worcester, Springfield, Lowell, Brockton, New Bedford, Fall River
        "01602", "01103", "01851", "02301", "02740", "02720",
        # Cape Cod, Pittsfield, Framingham, Plymouth
        "02601", "01201", "01701", "02360",
        # North Shore / South Shore / MetroWest
        "01960", "01970", "01752", "02062",
        # Corridor fill (I-90, I-91, I-95)
        "01420", "02532", "01841", "01830",
    ],

    # ── Michigan (35 ZIPs) ─────────────────────────────────────────────
    "MI": [
        # Detroit metro grid
        "48201", "48219", "48235",
        "48075", "48084", "48152", "48167", "48170", "48187",
        "48009", "48034", "48335",
        # Ann Arbor, Lansing, Flint, Grand Rapids, Kalamazoo
        "48103", "48108", "48910", "48933", "48503", "49503", "49007",
        # Saginaw / Bay City, Traverse City, Marquette
        "48601", "48706", "49684", "49855",
        # Muskegon, Battle Creek, Jackson, Port Huron, Holland
        "49441", "49017", "49201", "48060", "49423",
        # Midland, Monroe, Cadillac, Petoskey, Alpena
        "48640", "48162", "49601", "49770", "49707",
        # Corridor fill (I-75, I-94, I-96, I-69, US-131)
        "48647", "49686", "48858", "48446", "49783",
    ],

    # ── Minnesota (25 ZIPs) ────────────────────────────────────────────
    "MN": [
        # Twin Cities metro grid
        "55401", "55408", "55416", "55420", "55428", "55437", "55447",
        "55101", "55112", "55124", "55304", "55369",
        # Rochester, Duluth, St Cloud, Mankato, Moorhead
        "55901", "55802", "56301", "56001", "56560",
        # Winona, Brainerd, Alexandria, Willmar, Bemidji, Marshall
        "55987", "56401", "56308", "56201", "56601", "56258",
        # Owatonna, Hutchinson, Fergus Falls, Worthington
        "55021", "55350", "56537", "56187",
    ],

    # ── Mississippi (18 ZIPs) ──────────────────────────────────────────
    "MS": [
        # Jackson metro
        "39201", "39206", "39212",
        # Gulfport / Biloxi, Hattiesburg, Meridian, Tupelo
        "39501", "39530", "39401", "39301", "38801",
        # Southaven / Olive Branch (Memphis metro), Oxford, Columbus
        "38671", "38654", "38655", "39701",
        # Vicksburg, Greenville, Laurel, Starkville, Natchez
        "39180", "38701", "39440", "39759", "39120",
        # Corinth, Brookhaven, McComb, Grenada, Cleveland
        "38834", "39601", "39648", "38901", "38732",
    ],

    # ── Missouri (28 ZIPs) ─────────────────────────────────────────────
    "MO": [
        # Kansas City metro
        "64101", "64110", "64118", "64131", "64155",
        "64081", "64086",
        # St. Louis metro
        "63101", "63109", "63116", "63130", "63141",
        "63011", "63031", "63043",
        # Springfield, Columbia, Jefferson City, Joplin, St. Joseph
        "65801", "65201", "65101", "64801", "64501",
        # Cape Girardeau, Branson, Sedalia, Rolla, Hannibal
        "63701", "65616", "65301", "65401", "63401",
        # Kirksville, West Plains, Poplar Bluff, Sikeston, Warrensburg
        "63501", "65775", "63901", "63801", "64093",
        # Corridor fill (I-44, I-70)
        "65560", "64735",
    ],

    # ── Montana (18 ZIPs) ──────────────────────────────────────────────
    "MT": [
        # Billings
        "59101", "59102",
        # Missoula, Great Falls, Helena, Butte, Bozeman, Kalispell
        "59801", "59401", "59601", "59701", "59715", "59901",
        # Havre, Miles City, Lewistown, Glendive, Sidney
        "59501", "59301", "59457", "59330", "59270",
        # I-90 / I-15 / I-94 fill
        "59047", "59808", "59840", "59223",
        "59405",
    ],

    # ── Nebraska (16 ZIPs) ─────────────────────────────────────────────
    "NE": [
        # Omaha metro
        "68102", "68114", "68127", "68144", "68022",
        # Lincoln
        "68502", "68510",
        # Grand Island, Kearney, North Platte, Scottsbluff, Norfolk
        "68801", "68845", "69101", "69361", "68701",
        # Hastings, Columbus, Fremont, Beatrice, McCook, Alliance, York
        "68901", "68601", "68025", "68310", "69001", "69301", "68467",
    ],

    # ── Nevada (18 ZIPs) ───────────────────────────────────────────────
    "NV": [
        # Las Vegas metro grid
        "89101", "89107", "89117", "89128", "89134", "89144",
        "89146", "89074", "89011", "89014", "89031", "89052",
        # Reno / Sparks
        "89501", "89511", "89431",
        # Carson City, Elko, Fallon, Winnemucca, Pahrump, Ely, Mesquite
        "89701", "89801", "89406", "89445", "89048", "89301", "89027",
    ],

    # ── New Hampshire (14 ZIPs) ────────────────────────────────────────
    "NH": [
        # Manchester, Nashua, Concord
        "03101", "03060", "03301",
        # Dover, Portsmouth, Keene, Laconia, Lebanon
        "03820", "03801", "03431", "03246", "03766",
        # Rochester, Berlin, Claremont, Plymouth, Littleton
        "03867", "03570", "03743", "03264", "03561",
        "03104",
    ],

    # ── New Jersey (30 ZIPs) ───────────────────────────────────────────
    "NJ": [
        # North Jersey
        "07102", "07030", "07047", "07070", "07110", "07201", "07302",
        "07410", "07470", "07601", "07652",
        # Central Jersey
        "07726", "07728", "07746", "08520", "08536", "08540", "08817",
        "08901",
        # South Jersey
        "08002", "08033", "08060", "08102", "08201", "08401", "08610",
        # Shore
        "07701", "07753", "08731", "08742",
        # Vineland, Toms River, Hackettstown, Newton
        "08360", "08753", "07840", "07860",
    ],

    # ── New Mexico (18 ZIPs) ───────────────────────────────────────────
    "NM": [
        # Albuquerque metro
        "87101", "87109", "87120", "87123",
        # Santa Fe, Las Cruces, Rio Rancho
        "87501", "88001", "87124",
        # Roswell, Farmington, Clovis, Alamogordo, Carlsbad
        "88201", "87401", "88101", "88310", "88220",
        # Las Vegas, Gallup, Silver City, Truth or Consequences, Taos
        "87701", "87301", "88061", "87901", "87571",
        # Deming, Raton, Socorro, Tucumcari, Artesia, Espanola
        "88030", "87740", "87801", "88401", "88210", "87532",
    ],

    # ── New York (45 ZIPs) ─────────────────────────────────────────────
    "NY": [
        # NYC boroughs
        "10001", "10016", "10029", "10036", "10128",  # Manhattan
        "11201", "11215", "11230",                     # Brooklyn
        "10301", "10314",                              # Staten Island
        "11101", "11354", "11375", "11432",            # Queens
        "10451", "10467",                              # Bronx
        # Long Island
        "11501", "11550", "11735", "11756", "11787", "11901",
        # Westchester / Rockland
        "10601", "10701", "10901",
        # Hudson Valley
        "12550", "12601",
        # Albany / Capital District
        "12201", "12065", "12180", "12866",
        # Syracuse, Rochester, Buffalo
        "13202", "14604", "14201", "14225",
        # Utica, Binghamton, Ithaca, Plattsburgh, Watertown
        "13501", "13901", "14850", "12901", "13601",
        # Niagara Falls, Kingston, Elmira, Glens Falls
        "14301", "12401", "14901", "12801",
        # Corridor fill (I-87, I-90, I-81)
        "12946", "13045", "14701", "13820", "14580",
    ],

    # ── North Carolina (35 ZIPs) ───────────────────────────────────────
    "NC": [
        # Charlotte metro
        "28202", "28210", "28226", "28269", "28277",
        "28025", "28078", "28105",
        # Raleigh / Durham / Chapel Hill
        "27601", "27609", "27701", "27514",
        "27560", "27587",
        # Greensboro / Winston-Salem / High Point
        "27401", "27103", "27260",
        # Fayetteville, Wilmington, Asheville, Greenville, Jacksonville
        "28301", "28401", "28801", "27834", "28540",
        # Hickory, Gastonia, Burlington, Goldsboro, New Bern
        "28601", "28052", "27215", "27530", "28560",
        # Sanford, Lumberton, Morganton, Boone, Elizabeth City
        "27330", "28358", "28655", "28607", "27909",
        # Hendersonville, Statesville, Shelby, Kinston, Roanoke Rapids
        "28792", "28677", "28150", "28501", "27870",
        # Corridor fill (I-85, I-40, I-77, I-95)
        "27253", "28327", "27707",
    ],

    # ── North Dakota (14 ZIPs) ─────────────────────────────────────────
    "ND": [
        # Fargo, Bismarck, Grand Forks, Minot
        "58102", "58103", "58501", "58201", "58701",
        # Williston, Dickinson, Jamestown, Wahpeton, Devils Lake
        "58801", "58601", "58401", "58075", "58301",
        # Corridor fill (I-94, I-29, US-2)
        "58554", "58078", "58540", "58421",
        # Grafton, Bottineau, Valley City, Watford City
        "58237", "58318", "58072", "58854",
    ],

    # ── Ohio (38 ZIPs) ─────────────────────────────────────────────────
    "OH": [
        # Columbus metro
        "43201", "43215", "43220", "43229", "43235",
        "43004", "43016", "43081", "43119",
        # Cleveland metro
        "44101", "44113", "44124", "44134", "44145",
        # Cincinnati metro
        "45202", "45211", "45236", "45241", "45255",
        # Dayton, Toledo, Akron, Canton, Youngstown
        "45402", "43601", "44313", "44703", "44505",
        # Springfield, Mansfield, Lima, Findlay, Zanesville
        "45501", "44902", "45801", "45840", "43701",
        # Sandusky, Ashtabula, Wooster, Chillicothe, Newark
        "44870", "44004", "44691", "45601", "43055",
        # Bowling Green, Tiffin, Delaware, Marion, Cambridge
        "43402", "44883", "43015", "43302", "43725",
        # Corridor fill (I-71, I-70, I-75, I-77, I-80/90)
        "44256", "44060", "44483", "44035", "43920",
    ],

    # ── Oklahoma (22 ZIPs) ─────────────────────────────────────────────
    "OK": [
        # Oklahoma City metro
        "73102", "73112", "73120", "73132", "73139", "73159",
        "73003", "73034", "73072",
        # Tulsa metro
        "74103", "74114", "74133", "74012",
        # Norman, Lawton, Enid, Muskogee, Stillwater, Shawnee
        "73069", "73501", "73701", "74401", "74074", "74801",
        # Ada, Ardmore, McAlester, Durant, Woodward, Ponca City
        "74820", "73401", "74501", "74701", "73801", "74601",
        # Corridor fill (I-35, I-40, I-44)
        "73601",
    ],

    # ── Oregon (25 ZIPs) ───────────────────────────────────────────────
    "OR": [
        # Portland metro grid
        "97201", "97214", "97220", "97229", "97233",
        "97005", "97006", "97034", "97080", "97124",
        "97301",  # Salem
        # Eugene, Medford, Bend, Corvallis, Albany
        "97401", "97501", "97701", "97330", "97321",
        # Roseburg, Grants Pass, Klamath Falls, Pendleton
        "97470", "97526", "97601", "97801",
        # Astoria, The Dalles, Coos Bay, La Grande
        "97103", "97058", "97420", "97850",
        # Hermiston, Ontario, Florence, Tillamook, Newport
        "97838", "97914", "97439", "97141", "97365",
        # I-5 fill
        "97071",
    ],

    # ── Pennsylvania (40 ZIPs) ─────────────────────────────────────────
    "PA": [
        # Philadelphia metro
        "19102", "19111", "19131", "19143", "19148",
        "19003", "19015", "19063", "19082",
        # Philadelphia suburbs
        "19401", "19446", "19002", "18940", "19355",
        # Pittsburgh metro
        "15201", "15213", "15222", "15237",
        "15108", "15146", "15090",
        # Allentown / Bethlehem / Easton, Reading, Lancaster, York
        "18101", "18015", "19601", "17601", "17401",
        # Harrisburg, Scranton / Wilkes-Barre, Erie
        "17101", "18503", "18702", "16501",
        # State College, Williamsport, Altoona, Johnstown, Chambersburg
        "16801", "17701", "16601", "15901", "17201",
        # Meadville, Indiana, DuBois, Sunbury, Pottsville
        "16335", "15701", "15801", "17801", "17901",
        # Corridor fill (I-80, I-76, I-81, I-78)
        "16001", "15501", "17057", "18360",
        # Lock Haven, Lewistown, Stroudsburg, Oil City
        "17745", "17044", "18301", "16301",
    ],

    # ── Rhode Island (10 ZIPs) ─────────────────────────────────────────
    "RI": [
        "02903", "02904", "02909",  # Providence
        "02860", "02893",            # Pawtucket / Warwick
        "02840", "02882",            # Newport / Narragansett
        "02886", "02864",            # Cranston / Cumberland
        "02891",                     # Westerly
    ],

    # ── South Carolina (22 ZIPs) ───────────────────────────────────────
    "SC": [
        # Charleston metro
        "29401", "29406", "29464", "29485",
        # Columbia metro
        "29201", "29210", "29223", "29072",
        # Greenville / Spartanburg
        "29601", "29615", "29303",
        # Myrtle Beach, Rock Hill, Florence, Hilton Head, Aiken
        "29577", "29730", "29501", "29926", "29801",
        # Anderson, Sumter, Orangeburg, Beaufort
        "29621", "29150", "29115", "29902",
        # Clemson, Greenwood, Conway, Georgetown, Walterboro
        "29631", "29646", "29526", "29440", "29488",
    ],

    # ── South Dakota (14 ZIPs) ─────────────────────────────────────────
    "SD": [
        # Sioux Falls, Rapid City
        "57104", "57106", "57701", "57702",
        # Aberdeen, Brookings, Watertown, Mitchell, Pierre
        "57401", "57006", "57201", "57301", "57501",
        # Yankton, Huron, Spearfish, Vermillion
        "57078", "57350", "57783", "57069",
        # I-90 fill, Mobridge, Winner, Chamberlain, Madison, Sturgis
        "57601", "57580", "57325", "57042", "57785",
    ],

    # ── Tennessee (28 ZIPs) ────────────────────────────────────────────
    "TN": [
        # Nashville metro
        "37203", "37211", "37214", "37221", "37027", "37064", "37075",
        "37115", "37138",
        # Memphis metro
        "38103", "38117", "38125", "38138",
        # Knoxville, Chattanooga, Clarksville, Murfreesboro
        "37902", "37421", "37040", "37129",
        # Johnson City, Jackson, Kingsport, Cookeville, Cleveland
        "37601", "38301", "37660", "38501", "37311",
        # Columbia, Dyersburg, Crossville, Morristown, Tullahoma
        "38401", "38024", "38555", "37813", "37388",
        # Corridor fill (I-40, I-65, I-24, I-81)
        "37801", "38261", "37343",
    ],

    # ── Texas (75 ZIPs) ────────────────────────────────────────────────
    "TX": [
        # Houston metro grid
        "77002", "77008", "77024", "77030", "77042", "77055", "77070",
        "77082", "77094", "77339", "77433", "77449", "77479", "77520",
        "77573",
        # Dallas / Fort Worth metro grid
        "75201", "75214", "75225", "75243", "75252",
        "75006", "75019", "75034", "75062", "75080",
        "76102", "76137", "76148", "76201", "76240",
        # San Antonio
        "78201", "78217", "78228", "78240", "78254",
        # Austin metro
        "78701", "78723", "78745", "78759",
        "78664", "78681",
        # El Paso
        "79901", "79912", "79936",
        # Corpus Christi, Lubbock, Amarillo, Midland / Odessa
        "78401", "79401", "79109", "79701", "79761",
        # Laredo, McAllen, Brownsville, Waco, Tyler
        "78040", "78501", "78520", "76701", "75701",
        # Abilene, San Angelo, Beaumont, College Station, Longview
        "79601", "76901", "77701", "77840", "75601",
        # Killeen / Temple, Texarkana, Wichita Falls, Lufkin, Victoria
        "76541", "75501", "76301", "75901", "77901",
        # Nacogdoches, Paris, Marshall, Del Rio, Eagle Pass
        "75961", "75460", "75670", "78840", "78852",
        # New Braunfels, San Marcos, Georgetown, Conroe, The Woodlands
        "78130", "78666", "78626", "77301", "77380",
        # Corridor fill (I-10, I-20, I-35, I-45, I-30)
        "76067", "79720", "77868", "78861",
        # Denton, McKinney, Sherman, Corsicana
        "76205", "75069", "75090", "75110",
    ],

    # ── Utah (20 ZIPs) ─────────────────────────────────────────────────
    "UT": [
        # Salt Lake City metro
        "84101", "84108", "84116", "84121", "84123",
        # Suburbs / exurbs
        "84003", "84020", "84043", "84065", "84095",
        # Provo / Orem, Ogden, Logan, St. George
        "84601", "84097", "84401", "84321", "84770",
        # Park City, Cedar City, Moab, Vernal, Price
        "84060", "84720", "84532", "84078", "84501",
        # Tooele, Brigham City, Richfield, Kanab, Roosevelt, Heber City
        "84074", "84302", "84701", "84741", "84066", "84032",
    ],

    # ── Vermont (12 ZIPs) ──────────────────────────────────────────────
    "VT": [
        # Burlington metro
        "05401", "05403", "05446", "05452",
        # Montpelier, Rutland, Brattleboro, Barre, Bennington
        "05602", "05701", "05301", "05641", "05201",
        # St. Johnsbury, White River Junction, Middlebury
        "05819", "05001", "05753",
    ],

    # ── Virginia (35 ZIPs) ─────────────────────────────────────────────
    "VA": [
        # Northern Virginia / DC suburbs
        "22101", "22151", "22180", "22030", "22042", "22066",
        "20109", "20110", "20170", "20175", "20191",
        # Richmond metro
        "23219", "23225", "23233", "23060",
        # Virginia Beach / Norfolk / Newport News / Hampton
        "23451", "23510", "23602", "23666",
        # Chesapeake, Suffolk
        "23320", "23434",
        # Roanoke, Lynchburg, Charlottesville, Fredericksburg
        "24011", "24502", "22901", "22401",
        # Harrisonburg, Blacksburg, Danville, Winchester, Bristol
        "22801", "24060", "24541", "22601", "24201",
        # Staunton, Radford, Martinsville, Waynesboro
        "24401", "24141", "24112", "22980",
        # Corridor fill (I-64, I-81, I-95, I-66)
        "23901", "24210", "23188", "22630",
        # Culpeper, Leesburg, Woodbridge
        "22701", "20176", "22191",
    ],

    # ── Washington (30 ZIPs) ───────────────────────────────────────────
    "WA": [
        # Seattle metro grid
        "98101", "98103", "98115", "98122", "98133", "98144", "98178",
        "98004", "98033", "98052", "98055", "98188",
        # Tacoma, Olympia, Everett, Federal Way
        "98402", "98501", "98201", "98003",
        # Spokane, Vancouver / Clark County
        "99201", "99208", "98661", "98682",
        # Bellingham, Yakima, Kennewick / Richland, Wenatchee
        "98225", "98901", "99336", "98801",
        # Bremerton, Mount Vernon, Longview, Walla Walla
        "98312", "98273", "98632", "99362",
        # Aberdeen, Centralia, Ellensburg, Moses Lake, Pullman
        "98520", "98531", "98926", "98837", "99163",
    ],

    # ── West Virginia (16 ZIPs) ────────────────────────────────────────
    "WV": [
        # Charleston
        "25301", "25304",
        # Huntington, Morgantown, Parkersburg, Wheeling, Martinsburg
        "25701", "26505", "26101", "26003", "25401",
        # Beckley, Clarksburg, Fairmont, Lewisburg, Elkins
        "25801", "26301", "26554", "24901", "26241",
        # Logan, Weston, Princeton, Point Pleasant
        "25601", "26452", "24740", "25550",
        # Corridor fill (I-64, I-77, I-79, I-81)
        "25177", "26150", "26651",
    ],

    # ── Wisconsin (25 ZIPs) ────────────────────────────────────────────
    "WI": [
        # Milwaukee metro
        "53202", "53215", "53227", "53045", "53051", "53154",
        # Madison
        "53703", "53711", "53719",
        # Green Bay, Appleton / Fox Valley, Oshkosh
        "54301", "54911", "54901",
        # Kenosha / Racine, Waukesha, Eau Claire, La Crosse
        "53140", "53186", "54701", "54601",
        # Janesville, Wausau, Sheboygan, Fond du Lac, Stevens Point
        "53545", "54401", "53081", "54935", "54481",
        # Manitowoc, Marshfield, Platteville, Baraboo, Rice Lake
        "54220", "54449", "53818", "53913", "54868",
        # Corridor fill (I-90/94, I-43, I-41)
        "54115", "53959",
    ],

    # ── Wyoming (14 ZIPs) ──────────────────────────────────────────────
    "WY": [
        # Cheyenne, Casper, Laramie, Gillette, Rock Springs
        "82001", "82601", "82070", "82716", "82901",
        # Sheridan, Jackson, Riverton, Evanston, Cody
        "82801", "83001", "82501", "82930", "82414",
        # Rawlins, Powell, Torrington, Douglas, Thermopolis, Lander
        "82301", "82435", "82240", "82633", "82443", "82520",
    ],

    # ── District of Columbia (6 ZIPs) ──────────────────────────────────
    # ── Additional coverage for sparse areas ─────────────────────────
    # These fill remaining gaps, especially in rural interstate corridors

    "DC": [
        "20001", "20009", "20015", "20019", "20024", "20036",
    ],
}
