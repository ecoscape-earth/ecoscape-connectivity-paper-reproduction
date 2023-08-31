import argparse
import csv
import datetime
import gzip
import os
from pathlib import Path
from pydal import Field, DAL
import sys
import traceback


# We only keep these observations, and strip out this prefix.
OBS_PREFIX = "URN:CornellLabOfOrnithology:EBIRD:"
OBS_PREFIX_LEN = len(OBS_PREFIX)

def open_db(args):
    print("db path:", args.db)
    Path(args.db).mkdir(parents=True, exist_ok=True)
    db = DAL("sqlite://ebd.sqlite", folder=args.db, migrate=True)
    return db

def create_tables(db):
    
    db.define_table('locality',
                    Field('locality_ebird_id'), ##
                    Field('country_code'),
                    Field('state'),
                    Field('state_code'),
                    Field('county'),
                    Field('county_code'),
                    Field('locality_name'),
                    Field('locality_type'),
                    Field('lat', 'double'),
                    Field('lng', 'double'),
                    Field('lat_square', 'integer'),
                    Field('lng_square', 'integer'),
                    )
    
    db.define_table('checklist',
                    Field('checklist_id'), ## ID on eBird
                    Field('observer_id'), # as per eBird
                    Field('last_edited', 'datetime'),
                    Field('locality_id', 'reference locality'),
                    Field('observation_date', 'date'),
                    Field('observation_time', 'time'),
                    Field('protocol_type'),
                    Field('protocol_code'),
                    Field('duration_minutes', 'double'),
                    Field('length_km', 'double'),
                    Field('area_ha', 'double'),
                    Field('num_observers', 'integer'),
                    Field('complete', 'boolean'),
                    Field('group_id'), # As per eBird
                    Field('approved', 'boolean'),
                    Field('reviewed', 'boolean'),
                    Field('reason', 'text'),
                    Field('comments', 'text'),
                    )
    
    db.define_table('bird',
                    Field('taxonomy', 'integer'), ##
                    Field('name_en'), 
                    Field('name_sci'),
                    Field('category'),
                    Field('subspecies_sci'),
                    Field('subspecies_en'),
                    )

    db.define_table('obs',
                    Field('obs_id'), ##
                    Field('bird_id', 'reference bird'),
                    Field('checklist_id', 'reference checklist'),
                    Field('count', 'integer'),
                    Field('present', 'boolean'),
                    Field('breeding_code'),
                    Field('breeding_cat'),
                    Field('behavior_code'),
                    Field('age_sex'),
                    Field('comments', 'text'),
                    )
    
    db.commit()
    
def create_basic_indices(db):
    """Creates the indices necessary for insertion.""" 
    db.executesql('CREATE UNIQUE INDEX IF NOT EXISTS bird_taxonomy_idx on bird(taxonomy)')
    db.executesql('CREATE UNIQUE INDEX IF NOT EXISTS locality_ebird_id_idx on locality(locality_ebird_id)')
    db.executesql('CREATE UNIQUE INDEX IF NOT EXISTS checklist_id_idx on checklist(checklist_id)')
    db.executesql('CREATE UNIQUE INDEX IF NOT EXISTS obs_id_idx on obs(obs_id)')
    db.commit()
    
def create_aux_indices(db):
    
    db.executesql('CREATE INDEX IF NOT EXISTS bird_name_sci_idx on bird(name_sci)')
    db.executesql('CREATE INDEX IF NOT EXISTS locality_lat_idx on locality(lat)')
    db.executesql('CREATE INDEX IF NOT EXISTS locality_lat_square_idx on locality(lat_square)')    
    db.executesql('CREATE INDEX IF NOT EXISTS locality_lng_idx on locality(lng)')
    db.executesql('CREATE INDEX IF NOT EXISTS locality_lng_square_idx on locality(lng_square)')    
    db.executesql('CREATE INDEX IF NOT EXISTS locality_state_code_idx on locality(state_code)')
    db.executesql('CREATE INDEX IF NOT EXISTS locality_county_idx on locality(county)')
    db.commit()
    
def round_coord(c):
    """Rounds a coordinate into a square"""
    return round(c * 10)

def safefloat(x):
    return float(x) if x else None

def safeint(x):
    return int(x) if x is not None and x.isnumeric() else None

def is_present(x):
    return x == "X" or x is not None and x.isnumeric() and int(x) > 0

def safebool(x):
    return bool(int(x)) if x else None

def safedatetime(x):
    """Deals with rounded numbers of decimals."""
    try:
        return datetime.datetime.fromisoformat(x)
    except ValueError as e:
        if "." not in x:
            if x is None or len(x) == 0:
                return None
            return datetime.datetime.fromisoformat(x + ".000000")
        rest, millis = x.split(".")
        return datetime.datetime.fromisoformat(x + "0" * (6 - len(millis)))

def safetime(x):
    """Deals with rounded numbers of decimals."""
    try:
        return datetime.time.fromisoformat(x)
    except ValueError as e:
        if "." not in x:
            if x is None or len(x) == 0:
                return None
            return datetime.time.fromisoformat(x + ".000000")
        rest, millis = x.split(".")
        return datetime.time.fromisoformat(x + "0" * (6 - len(millis)))

def ensure(table, cond, **values):
    row = table(cond)
    if row:
        row.update(**values)
        return row.id
    else:
        return table.insert(**values)

def insert_bird(db, row):
    """Adds a bird to the db, if missing."""
    id = ensure(
        db.bird, 
        (db.bird.taxonomy == safeint(row['TAXONOMIC ORDER'])),
        taxonomy = safeint(row['TAXONOMIC ORDER']),
        name_sci = row['SCIENTIFIC NAME'],
        name_en = row['COMMON NAME'],
        category = row['CATEGORY'],
        subspecies_sci = row['SUBSPECIES SCIENTIFIC NAME'],
        subspecies_en = row['SUBSPECIES COMMON NAME'],
    )
    return id

def insert_locality(db, row):
    """Inserts a unique locality in the db."""
    id = ensure(
        db.locality,
        (db.locality.locality_ebird_id == row['LOCALITY ID']),
        locality_ebird_id = row['LOCALITY ID'],
        country_code = row['COUNTRY CODE'],
        state = row['STATE'],
        state_code = row['STATE CODE'],
        county = row['COUNTY'],
        county_code = row['COUNTY CODE'],
        locality_name = row['LOCALITY'],
        locality_type = row['LOCALITY TYPE'],
        lat = safefloat(row['LATITUDE']),
        lng = safefloat(row['LONGITUDE']),
        lat_square = round_coord(safefloat(row['LATITUDE'])),
        lng_square = round_coord(safefloat(row['LONGITUDE'])),        
    )
    return id

def insert_checklist(db, row):
    """Inserts the checklist, returning the id"""
    locality_id = insert_locality(db, row)
    assert locality_id is not None
    observation_date = datetime.date.fromisoformat(row['OBSERVATION DATE'])
    observation_time = safetime(row['TIME OBSERVATIONS STARTED'])
    
    id = ensure(
        db.checklist,
        (db.checklist.checklist_id == row['SAMPLING EVENT IDENTIFIER']),
        checklist_id = row['SAMPLING EVENT IDENTIFIER'],
        observer_id = row['OBSERVER ID'],
        last_edited = safedatetime(row['LAST EDITED DATE']),
        locality_id = locality_id,
        observation_date = observation_date,
        observation_time = observation_time,
        protocol_type = row['PROTOCOL TYPE'],
        protocol_code = row['PROTOCOL CODE'],
        duration_minutes = safefloat(row['DURATION MINUTES']),
        length_km = safefloat(row['EFFORT DISTANCE KM']),
        area_ha = safefloat(row['EFFORT AREA HA']),
        num_observers = safeint(row['NUMBER OBSERVERS']),
        complete = safebool(row['ALL SPECIES REPORTED']),
        group_id = row['GROUP IDENTIFIER'],
        approved = safebool(row['APPROVED']),
        reviewed = safebool(row['REVIEWED']),
        reason = row['REASON'],
        comments = row['TRIP COMMENTS'],
    )
    return id

def get_ebird_id(row):
    ebird_id = row['GLOBAL UNIQUE IDENTIFIER']
    if ebird_id.startswith(OBS_PREFIX):
        return ebird_id[OBS_PREFIX_LEN:]
    else:
        return None
    
def insert_observation(db, row, obs_ebird_id=None, bird_id=None, checklist_id=None):
    """Inserts the observation of a bird"""
    assert obs_ebird_id is not None
    assert bird_id is not None
    assert checklist_id is not None
    id = ensure(
        db.obs,
        (db.obs.obs_id == obs_ebird_id),
        obs_id = obs_ebird_id,
        bird_id = bird_id,
        checklist_id = checklist_id, 
        count = safeint(row['OBSERVATION COUNT']),
        present = is_present(row['OBSERVATION COUNT']),
        breeding_code = row['BREEDING CODE'],
        breeding_cat = row['BREEDING CATEGORY'],
        behavior_code = row['BEHAVIOR CODE'],
        age_sex = row['AGE/SEX'],
        comments = row['SPECIES COMMENTS'],
    )
    return id

def insert_row(db, row):
    if args.print_lines:
        print("Row:", row)
    obs_ebird_id = get_ebird_id(row)
    if obs_ebird_id is not None:
        # Inserts bird. 
        bird_id = insert_bird(db, row)
        # Inserts checklist.
        checklist_id = insert_checklist(db, row)
        # Inserts observation.
        observation_id = insert_observation(db, row, obs_ebird_id=obs_ebird_id,
                                            bird_id=bird_id, checklist_id=checklist_id)    
    
def main(args):
    if args.clean_ebd_file.split(".")[-1] == 'gz':
        fp = gzip.open(args.clean_ebd_file, mode='rt', encoding='utf-8', newline='')
    else:
        fp = open(args.clean_ebd_file, newline='')
    reader = csv.DictReader(fp, delimiter="\t")
    if args.show_format:
        for row in reader:
            for i, k in enumerate(row.keys()):
                print(i + 1, k)
            break
        sys.exit(0)
    db = open_db(args)
    create_tables(db)
    create_basic_indices(db)
    
    # Sanity check on rows.
    max_obs = db(db.obs).select(orderby=~db.obs.id).first()
    if max_obs is not None and max_obs.id != args.skip_lines and not args.ignore_repeated:
        raise Exception("Starting from {} but db has {} rows".format(
            args.skip_lines, max_obs.id))
    
    error_file = open(args.error_file, 'w')
    row_idx = 0
    for row in reader:
        row_idx += 1
        if row_idx <= args.skip_lines:
            continue # Skip the line
        if args.num_lines is not None and row_idx > args.skip_lines + args.num_lines:
            break
        if row_idx % 10000 == 0:
            print("Inserted {} lines".format(row_idx))
            db.commit()
        try:
            insert_row(db, row)
        except Exception as e:
            traceback.print_exc()
            traceback.print_exc(file=error_file)
            print("Row:", row)
            error_file.write("Row_idx: {} Row: {}\n".format(row_idx, row))
            if not args.ignore_errors:
                error_file.close()
                fp.close()
                raise e
    db.commit()
    fp.close()
    error_file.close()
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ebd_file', type=str, default=None,
                        help="Edb dump file")
    parser.add_argument('--show_format', default=False, action='store_true',
                        help="Show the format of the csv file only")
    parser.add_argument('--db', type=str, default=None, 
                        help='db file to produce')
    parser.add_argument('--overwrite', default=False, 
                        action="store_true")
    parser.add_argument('--skip_lines', type=int, default=0,
                        help="How many lines to skip from the csv")
    parser.add_argument('--num_lines', type=int, default=None,
                        help="Number of lines to read")
    parser.add_argument('--ignore_repeated', default=False, action="store_true",
                        help="Ignore processing of repeated records")
    parser.add_argument('--print_lines', default=False, action="store_true",
                        help="print input csv lines, for debug")
    parser.add_argument('--ignore_errors', default=False, action='store_true', 
                        help="Carry over if errors occur.")
    args = parser.parse_args()
    args.db = os.path.abspath(os.path.expanduser(args.db)) if args.db is not None else None
    args.clean_ebd_file = os.path.abspath(os.path.expanduser(args.ebd_file))
    args.error_file = os.path.join(args.db, "error.log") if args.db is not None else None
    main(args)