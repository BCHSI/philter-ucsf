# Adds variables in to regex to create complex regex

import os
import json

# Define regex variables

day_name = "(S|s)un(day)?(s)?|SUN(DAY)?(S)?|(M|m)on(day)?(s)?|MON(DAY)?(S)?|(T|t)ues(day)?(s)?|Tue|TUES(DAY)?(S)?|(W|w)ed(nesday)?(s)?|WED(NESDAY)?(S)?|(T|t)hurs(day)?(s)?|Thu|THURS(DAY)?(S)?|(F|f)ri(day)?(s)?|FRI(DAY)?(S)?|(S|s)at(urday)?(s)?|SAT(URDAY)?(S)?"

month_name = "(J|j)an(uary)?|JAN(UARY)?|(F|f)eb(ruary)?|FEB(RUARY)?|(M|m)ar(ch)?|MAR(CH)?|(A|a)pr(il)?|APR(IL)?|May|MAY|(J|j)un(e)?|JUN(E)?|(J|j)ul(y)?|JUL(Y)?|(A|a)ug(ust)?|AUG(UST)?|(S|s)ep(tember)?|SEP(TEMBER)?|SEPT|Sept|(O|o)ct(ober)?|OCT(OBER)?|(N|n)ov(ember)?|NOV(EMBER)?|(D|d)ec(ember)?|DEC(EMBER)?"

day_numbering = "1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|13th|14th|15th|16th|17th|18th|19th|20th|21st|22nd|23rd|24th|25th|26th|27th|28th|29th|30th|31st|32nd|33rd|34th|35th|36th|37th|38th|39th|40th|41st|42nd|43rd|44th|45th|46th|47th|48th|49th|50th"

seasons = "(S|s)pring|SPRING|(F|f)all|FALL|(A|a)utumn|AUTUMN|(W|w)inter|WINTER|(S|s)ummer|SUMMER|(C|c)hristmas|(N|n)ew (Y|y)ear's (E|e)ve"

#old_address_indicator = "alley|alley|ally|aly|anex|annex|annx|anx|apartment|apt|arcade|arcade|avenue|ave|aven|avenu|avenue|avn|avnue|bayou|bayou|beach|beach|bend|bnd|bluff|bluf|bluff|bluffs|bottom|btm|bottm|bottom|boulevard|boul|boulevard|blvd|boulv|box|branch|brnch|branch|bridge|brg|bridge|brook|brook|brooks|burg|burgs|bypass|bypa|bypas|bypass|byps|camp|cp|cmp|canyon|canyon|cnyn|cape|cpe|causeway|causwa|cswy|center|cent|center|centr|centre|cnter|cntr|ctr|centers|circle|circ|circl|circle|crcl|crcle|circles|cliff|cliff|cliffs|cliffs|club|club|common|commons|corner|corner|corners|cors|crse|court|ct|courts|cts|cove|cv|coves|creek|crk|crescent|cres|crsent|crsnt|crest|crossing|crssng|xing|crossroad|crossroads|curve|dale|dl|dam|dm|divide|divide|dv|dvd|drive|driv|dr|drv|drives|east|estate|estate|estates|ests|expressway|expr|express|expressway|expw|expy|extension|extension|extn|extnsn|extensions|fall|falls|fls|ferry|frry|fry|field|fld|fields|flds|flat|flt|flats|flts|ford|frd|fords|forest|forests|frst|forge|forge|frg|forges|fork|frk|forks|frks|fort|frt|ft|freeway|freewy|frway|frwy|fwy|garden|gardn|grden|grdn|gardens|gdns|grdns|gateway|gatewy|gatway|gtway|gtwy|glen|gln|glens|green|grn|greens|grove|grove|grv|groves|harbor|harbor|harbr|hbr|hrbor|harbors|haven|hvn|heights|hts|highway|highwy|hiway|hiwy|hway|hwy|hill|hl|hills|hls|hollow|hollow|hollows|holw|holws|inlet|island|island|islnd|islands|islnds|iss|isle|isles|junction|jction|jctn|junction|junctn|juncton|junctions|jcts|junctions|key|ky|keys|kys|knoll|knol|knoll|knolls|knolls|lake|lake|lakes|lakes|land|landing|lndg|lndng|lane|ln|light|light|lights|loaf|loaf|lock|lock|locks|locks|lodge|ldge|lodg|lodge|loop|loops|mall|manor|manor|manors|mnrs|meadow|meadows|mdws|meadows|medows|mews|mill|mills|mission|mssn|motorway|mount|mt|mount|mountain|mntn|mountain|mountin|mtin|mtn|mountains|mountains|neck|neck|north|orchard|orchard|orchrd|oval|ovl|overpass|park|prk|parks|parkway|parkwy|pkway|pkwy|pky|parkways|pkwys|pass|passage|path|paths|pike|pikes|pine|pines|pnes|place|plain|pln|plains|plns|plaza|plz|plza|point|pt|points|pts|port|prt|ports|prts|prairie|prairie|prr|radial|radial|radiel|radl|ramp|ranch|ranches|rnch|rnchs|rapid|rpd|rapids|rpds|rest|rst|ridge|rdge|ridge|ridges|ridges|river|river|rvr|rivr|road|road|rd|roads|rds|route|row|rue|run|shoal|shoal|shoals|shoals|shore|shore|shr|shores|shores|shrs|skyway|south|spring|spng|spring|sprng|springs|spngs|springs|sprngs|spur|spurs|square|sqr|sqre|squ|square|squares|squares|station|station|statn|stn|stravenue|strav|straven|stravenue|stravn|strvn|strvnue|stream|streme|strm|street|strt|st|str|streets|suite|ste|summit|sumit|sumitt|summit|terrace|terr|terrace|throughway|trace|traces|trce|track|tracks|trak|trk|trks|trafficway|trail|trails|trl|trls|trailer|trlr|trlrs|tunnel|tunl|tunls|tunnel|tunnels|tunnl|turnpike|turnpike|turnpk|underpass|union|union|unions|valley|vally|vlly|vly|valleys|vlys|viaduct|via|viadct|viaduct|view|vw|views|vws|village|villag|village|villg|villiage|vlg|villages|vlgs|ville|vl|vista|vist|vista|vst|vsta|walk|walks|wall|way|way|ways|well|wells|west|wls"

# Modified address_indicator on 08/24/18
address_indicator = "alley|alley|ally|aly|anex|annex|annx|anx|apartment|apt|avenue|ave|aven|avenu|avenue|avn|avnue|bayou|bayou|beach|beach|bnd|bluff|bluf|bluff|bluffs|boulevard|boul|boulevard|blvd|boulv|box|branch|brnch|branch|bridge|brg|bridge|brook|brook|brooks|burg|burgs|byps|canyon|canyon|cnyn|cape|cpe|causeway|causwa|cswy|cent|centr|centre|cnter|cntr|ctr|circle|circ|circl|circle|crcl|crcle|circles|cliff|cliff|cliffs|cliffs|club|club|commons|corner|corner|corners|cors|crse|court|ct|courts|cts|cove|cv|coves|creek|crk|crescent|cres|crsent|crsnt|crest|crossing|crssng|xing|crossroad|crossroads|dale|dl|dam|divide|divide|dv|dvd|drive|driv|dr|drv|drives|east|estate|estate|estates|ests|expressway|expr|express|expressway|expw|expy|extn|extnsn|fls|ferry|frry|fry|flat|flt|flats|flts|ford|frd|fords|forest|forests|frst|forge|forge|frg|forges|fork|frk|forks|frks|fort|frt|ft|freeway|freewy|frway|frwy|fwy|garden|gardn|grden|grdn|gardens|gdns|grdns|gateway|gatewy|gatway|gtway|gtwy|glen|gln|glens|green|grn|greens|grove|grove|grv|groves|harbor|harbor|harbr|hbr|hrbor|harbors|haven|hvn|heights|hts|highway|highwy|hiway|hiwy|hway|hwy|hill|hl|hills|hls|hollow|hollow|hollows|holw|holws|iss|isle|isles|knoll|knol|knoll|knolls|knolls|lake|lake|lakes|lakes|land|landing|lndg|lndng|lane|ln|loaf|loaf|lock|lock|locks|locks|ldge|lodg|lodge|loop|loops|mall|manor|manor|manors|mnrs|meadow|meadows|mdws|meadows|medows|mews|mill|mills|mission|mssn|motorway|north|orchard|orchard|orchrd|oval|ovl|overpass|park|prk|parks|parkway|parkwy|pkway|pkwy|pky|parkways|pkwys|pass|passage|pike|pikes|pine|pines|pnes|place|plain|pln|plains|plns|plaza|plz|plza|port|prt|ports|prts|prairie|prairie|prr|ramp|ranch|ranches|rnch|rnchs|rapids|rpds|rst|ridge|rdge|ridge|ridges|ridges|river|river|rvr|rivr|road|road|rd|roads|rds|route|row|run|shoal|shoal|shoals|shoals|shore|shore|shr|shores|shores|shrs|skyway|south|spring|spng|spring|sprng|springs|spngs|springs|sprngs|spur|spurs|square|sqr|sqre|squ|square|squares|squares|station|station|statn|stn|stravenue|strav|straven|stravenue|stravn|strvn|strvnue|stream|streme|strm|street|strt|st|str|streets|suite|summit|sumit|sumitt|summit|terrace|terr|terrace|throughway|trce|track|tracks|trak|trk|trks|trafficway|trail|trails|trl|trls|trailer|trlr|trlrs|tunnel|tunl|tunls|tunnel|tunnels|tunnl|turnpike|turnpike|turnpk|underpass|union|union|unions|valley|vally|vlly|vly|valleys|vlys|viaduct|viadct|viaduct|village|villag|village|villg|villiage|vlg|villages|vlgs|ville|vl|vista|vist|vista|vst|vsta|way|way|ways|west|wls"

state_names = "(A|a)rizona|AZ|(V|v)irginia|VA|(M|m)innesota|MN|(A|a)laska|AK|(N|n)ew (Y|y)ork|NY|(T|t)exas|TX|(V|v)ermont|VT|(U|u)tah|UT|(N|n)ew (J|j)ersey|NJ|(N|n)orth (D|d)akota|ND|(S|s)outh (D|d)akota|SD|(M|m)issouri|MO|(W|w)ashington (D|d).(C|c).|(G|g)eorgia|GA|(M|m)assachusetts|MA|(P|p)uerto (R|r)ico|(M|m)ichigan|MI|(I|i)owa|IA|(N|n)orth (C|c)arolina|NC|(S|s)outh (C|c)arolina|SC|(N|n)evada|NV|(C|c)olorado|CO|(O|o)hio|OH|(H|h)awaii|HI|(N|n)ebraska|NE|(N|n)ew (H|h)ampshire|NH|(W|w)ashington|WA|(T|t)ennessee|TN|(A|a)rkansas|AR|(L|l)ouisiana|LA|(M|m)ississippi|MS|(O|o)regon|OR|(A|a)labama|AL|(W|w)yoming|WY|(W|w)isconsin|WI|(O|o)klahoma|OK|(F|f)lorida|FL|(R|r)hode (I|i)sland|RI|(I|i)ndiana|IN|(C|c)alifornia|CA|(K|k)ansas|KS|(D|d)elaware|DE|(M|m)aryland|(I|i)daho|ID|(P|p)ennsylvania|PA|(K|k)entucky|KY|(C|c)onnecticut|CT|(M|m)ontana|MT|(I|i)llinois|IL|(M|m)aine|ME"

full_numbering = "First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth|Thirteenth|Fourteenth|Fifteenth|Sixteenth|Seventeenth|Eighteenth|Nineteenth|Twentieth"

# Get blacklisted names
# names_blacklist = json.loads(open("../../filters/blacklists/names_blacklist_ssfirst.json").read())
# person_names = ''
# for key in names_blacklist:
# 	person_names += key + '|'
# # Get rid of last pipe
# person_names = person_names[:-1]

# Do folder walk and transform each file
rootdir = '.'
for subdir, dirs, files in os.walk(rootdir):
	for file in files:
		if ".txt" in file and "_transformed.txt" not in file and "catchall" not in file:
			filepath = os.path.join(subdir, file)
			# Get currnet file name and create transformed name
			file_root = file.split(".")[0]
			new_file_name = file_root + "_transformed.txt"
			new_filepath = os.path.join(subdir, new_file_name)
			# Open file
			regex = open(filepath,"r").read().strip()
			# Replace variables
			regex = regex.replace('"""+month_name+r"""', month_name).replace('"""+day_numbering+r"""', day_numbering).replace('"""+day_name+r"""', day_name).replace('"""+seasons+r"""', seasons).replace('"""+address_indicator+r"""',address_indicator).replace('"""+state_name+r"""', state_names).replace('"""+full_numbering+r"""', full_numbering)	
			# Write new file
			with open(new_filepath, "w") as fin:
				fin.write(regex)







