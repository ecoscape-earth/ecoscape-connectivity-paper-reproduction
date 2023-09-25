import hashlib
import numpy as np
import os
import pandas as pd
import sqlite3
from sqlite3 import Error

from collections import defaultdict
from pyproj import Transformer
from pyproj.crs import CRS

from scgt import GeoTiff

"""
A module for interaction with a sqlite database. Contains functions for query execution, 
and some common functionality we need to run on the DB
"""
class Connection:
    def __init__(self, db_file):
        """Initializes the connection to the SQLite database
        @param db_file: The file path to the database file
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
            print("Error in create_connection: ", e)
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.conn:
            self.conn.close()

    def get_cursor(self):
        try:
            cur = self.conn.cursor()
        except:
            print("error connecting to db")
            cur = None
        return cur

    def execute_query(self, query, verbose=False):
        """
        executes the given query in the database
        :param query (str): a sqlite query to the database
        :param verbose (boolean): flag to print out result of the query
        :returns: result of the query as a list of rows
        """
        try:
            cur = self.get_cursor()
            if isinstance(query, str):
                cur.execute(query)
            else:
                cur.execute(query[0], query[1])
            self.conn.commit()
            rows = cur.fetchall()
            if verbose:
                for row in rows:
                    print(row)
            return rows
        except Exception as e:
            print("Error executing query:\n\t", query, ".\n Error: ", e)


class EbirdObservations(Connection):
    """Class for eBird-specific connections, includes functionality particular to the eBird database"""

    def __init__(self, db_file):
        super().__init__(db_file)

    def get_all_squares(self, state=None,
                        breeding=True, date_range=None,
                        lat_range=None, lng_range=None, max_dist=2,
                        verbose=False):
        """
        Gets all squares with bird (any bird) observations, for a certain state,
        and withing certain lat, lng, and date ranges.
        :param state (str): state code
        :param breeding (boolean): whether to filter observations by breeding months (getting only apr-june)
        :param date_range: tuple of 2 date-strings in format "YYYY-MM-DD" to get only observations in this date range
        :param lat_range: tuple of 2 floats for the lower and upper bounds for latitude
        :param lng_range: tuple of 2 floats for the lower and upper bounds for longitude
        :param max_dist (int): max kilometers traveled for the checklist for any observation we consider
            (any of further distance will be too noisy, and should be disreguarded)
        :returns: list of squares which fall within the query parameters
        """
        query_string=['select DISTINCT SQUARE from checklist where "ALL SPECIES REPORTED" = 1']
        query_string.append('and "PROTOCOL TYPE" != "Incidental"')
        query_string.append('and "EFFORT DISTANCE KM" <= :dist')
        d = {"dist": max_dist}
        if state is not None:
            query_string.append('and "STATE CODE" = :state')
            d['state'] = state
        # Adds breeding portion
        if breeding:
            query_string.extend([
                'and (substr("OBSERVATION DATE", 6, 2) = "04"',
                'OR substr("OBSERVATION DATE", 6, 2) = "05"',
                'OR substr("OBSERVATION DATE", 6, 2) = "06")'
                ])
        if date_range is not None:
            query_string.append('and "OBSERVATION DATE" >= :min_date')
            query_string.append('and "OBSERVATION DATE" <= :max_date')
            d["min_date"], d["max_date"] = date_range
        if lat_range is not None:
            query_string.append('and "LATITUDE" >= :min_lat')
            query_string.append('and "LATITUDE" <= :max_lat')
            d["min_lat"], d["max_lat"] = lat_range
        if lng_range is not None:
            query_string.append('and "LONGITUDE" >= :min_lng')
            query_string.append('and "LONGITUDE" <= :max_lng')
            d["min_lng"], d["max_lng"] = lng_range
        query_string = " ".join(query_string)
        if verbose:
            print("Query:", query_string)
        squares_list = self.execute_query((query_string, d))
        return [sq[0] for sq in squares_list]

    def get_square_observations(self, square, bird,
                          breeding=True, date_range=None,
                          lat_range=None, lng_range=None, max_dist=2,
                          verbose=False):
        """
        Get the number of checklists, number of checklists with a bird,
        and total bird sightings, for a square.
        :param square: tuple of 2 floats, representing (lat, lng) of the square
        :param bird (str): name of bird
        :param breeding (boolean): whether to filter observations by breeding months (getting only apr-june)
        :param date_range: tuple of 2 date-strings in format "YYYY-MM-DD" to get only observations in this date range
        :param lat_range: tuple of 2 floats for the lower and upper bounds for latitude
        :param lng_range: tuple of 2 floats for the lower and upper bounds for longitude
        :param max_dist (int): max kilometers traveled for the checklist for any observation we consider
            (any of further distance will be too noisy, and should be disreguarded)
        :returns: num_checklists, num_bird_checklists, num_birds for the given square.
        """
        # First the number of checklists, with or without the bird.
        query_string=['select COUNT(*) FROM checklist where SQUARE = :square']
        d = {'square': square}
        query_string.append('and "ALL SPECIES REPORTED" = 1')
        query_string.append('and "PROTOCOL TYPE" != "Incidental"')
        query_string.append('and "EFFORT DISTANCE KM" <= :dist')
        d["dist"] = max_dist
        # Adds breeding portion
        if breeding:
            query_string.extend([
                'and (substr("OBSERVATION DATE", 6, 2) = "04"',
                'OR substr("OBSERVATION DATE", 6, 2) = "05"',
                'OR substr("OBSERVATION DATE", 6, 2) = "06")'
                ])
        if date_range is not None:
            query_string.append('and "OBSERVATION DATE" >= :min_date')
            query_string.append('and "OBSERVATION DATE" <= :max_date')
            d["min_date"], d["max_date"] = date_range
        if lat_range is not None:
            query_string.append('and "LATITUDE" >= :min_lat')
            query_string.append('and "LATITUDE" <= :max_lat')
            d["min_lat"], d["max_lat"] = lat_range
        if lng_range is not None:
            query_string.append('and "LONGITUDE" >= :min_lng')
            query_string.append('and "LONGITUDE" <= :max_lng')
            d["min_lng"], d["max_lng"] = lng_range
        query_string = " ".join(query_string)
        if verbose:
            print("Query:", query_string)
        num_checklists = float(self.execute_query((query_string, d))[0][0])

        # Then, the number of checklists with the bird, and the total number of birds.
        query_string = ['select COUNT(DISTINCT checklist."SAMPLING EVENT IDENTIFIER"),',
                        'SUM(observation."OBSERVATION COUNT")',
                        'from checklist join observation',
                        'on checklist."SAMPLING EVENT IDENTIFIER" = observation."SAMPLING EVENT IDENTIFIER"',
                        ]
        query_string.append('where checklist.SQUARE = :square')
        query_string.append('and checklist."ALL SPECIES REPORTED" = 1')
        query_string.append('and checklist."PROTOCOL TYPE" != "Incidental"')
        query_string.append('and checklist."EFFORT DISTANCE KM" <= :dist')
        d["dist"] = max_dist
        # Adds breeding portion
        if breeding:
            query_string.extend([
                'and (substr(checklist."OBSERVATION DATE", 6, 2) = "04"',
                'OR substr(checklist."OBSERVATION DATE", 6, 2) = "05"',
                'OR substr(checklist."OBSERVATION DATE", 6, 2) = "06")'
                ])
        if date_range is not None:
            query_string.append('and checklist."OBSERVATION DATE" >= :min_date')
            query_string.append('and checklist."OBSERVATION DATE" <= :max_date')
            d["min_date"], d["max_date"] = date_range
        if lat_range is not None:
            query_string.append('and checklist."LATITUDE" >= :min_lat')
            query_string.append('and checklist."LATITUDE" <= :max_lat')
            d["min_lat"], d["max_lat"] = lat_range
        if lng_range is not None:
            query_string.append('and checklist."LONGITUDE" >= :min_lng')
            query_string.append('and checklist."LONGITUDE" <= :max_lng')
            d["min_lng"], d["max_lng"] = lng_range
        # Ask about the bird.
        query_string.append('and observation."COMMON NAME" = :bird')
        d["bird"] = bird.name
        # Runs the query.
        query_string = " ".join(query_string)
        if verbose:
            print("Query:", query_string)
        r = self.execute_query((query_string, d))
        if r is None:
            return 0, 0, 0
        r = r[0]
        num_bird_checklists = float(r[0])
        num_birds = 0 if r[1] is None else float(r[1])
        return num_checklists, num_bird_checklists, num_birds


    def get_square_individual_checklists(self, square, bird,
                          breeding=True, date_range=None,
                          lat_range=None, lng_range=None, max_dist=2,
                          verbose=False):
        """
        Get the checklists for a square, so that statistics can be computed.
        The result is returned as a dataframe.

        and total bird sightings, for a square.
        :param square: tuple of 2 floats, representing (lat, lng) of the square
        :param bird (str): name of bird
        :param breeding (boolean): whether to filter observations by breeding months (getting only apr-june)
        :param date_range: tuple of 2 date-strings in format "YYYY-MM-DD" to get only observations in this date range
        :param lat_range: tuple of 2 floats for the lower and upper bounds for latitude
        :param lng_range: tuple of 2 floats for the lower and upper bounds for longitude
        :param max_dist (int): max kilometers traveled for the checklist for any observation we consider
            (any of further distance will be too noisy, and should be disreguarded)
        :returns: list of squares which fall within the query parameters
        """
        # First the checklists, with or without the bird.
        query_string=['select DISTINCT("SAMPLING EVENT IDENTIFIER")',
                      'FROM checklist where SQUARE = :square']
        d = {'square': square}
        query_string.append('and "ALL SPECIES REPORTED" = 1')
        query_string.append('and "PROTOCOL TYPE" != "Incidental"')
        query_string.append('and "EFFORT DISTANCE KM" <= :dist')
        d["dist"] = max_dist
        # Adds breeding portion
        if breeding:
            query_string.extend([
                'and (substr("OBSERVATION DATE", 6, 2) = "04"',
                'OR substr("OBSERVATION DATE", 6, 2) = "05"',
                'OR substr("OBSERVATION DATE", 6, 2) = "06")'
                ])
        if date_range is not None:
            query_string.append('and "OBSERVATION DATE" >= :min_date')
            query_string.append('and "OBSERVATION DATE" <= :max_date')
            d["min_date"], d["max_date"] = date_range
        if lat_range is not None:
            query_string.append('and "LATITUDE" >= :min_lat')
            query_string.append('and "LATITUDE" <= :max_lat')
            d["min_lat"], d["max_lat"] = lat_range
        if lng_range is not None:
            query_string.append('and "LONGITUDE" >= :min_lng')
            query_string.append('and "LONGITUDE" <= :max_lng')
            d["min_lng"], d["max_lng"] = lng_range
        query_string = " ".join(query_string)
        if verbose:
            print("Query:", query_string)
        checklists_df = pd.read_sql_query(query_string, self.conn, params=d)

        # Then, the number of checklists with the bird, and the total number of birds.
        query_string = ['select checklist."SAMPLING EVENT IDENTIFIER", ',
                        'observation."OBSERVATION COUNT"',
                        'from checklist join observation',
                        'on checklist."SAMPLING EVENT IDENTIFIER" = observation."SAMPLING EVENT IDENTIFIER"',
                        ]
        query_string.append('where checklist.SQUARE = :square')
        query_string.append('and checklist."ALL SPECIES REPORTED" = 1')
        query_string.append('and checklist."PROTOCOL TYPE" != "Incidental"')
        query_string.append('and checklist."EFFORT DISTANCE KM" <= :dist')
        d["dist"] = max_dist
        # Adds breeding portion
        if breeding:
            query_string.extend([
                'and (substr(checklist."OBSERVATION DATE", 6, 2) = "04"',
                'OR substr(checklist."OBSERVATION DATE", 6, 2) = "05"',
                'OR substr(checklist."OBSERVATION DATE", 6, 2) = "06")'
                ])
        if date_range is not None:
            query_string.append('and checklist."OBSERVATION DATE" >= :min_date')
            query_string.append('and checklist."OBSERVATION DATE" <= :max_date')
            d["min_date"], d["max_date"] = date_range
        if lat_range is not None:
            query_string.append('and checklist."LATITUDE" >= :min_lat')
            query_string.append('and checklist."LATITUDE" <= :max_lat')
            d["min_lat"], d["max_lat"] = lat_range
        if lng_range is not None:
            query_string.append('and checklist."LONGITUDE" >= :min_lng')
            query_string.append('and checklist."LONGITUDE" <= :max_lng')
            d["min_lng"], d["max_lng"] = lng_range
        # Ask about the bird.
        query_string.append('and observation."COMMON NAME" = :bird')
        d["bird"] = bird.name
        # Runs the query.
        query_string = " ".join(query_string)
        if verbose:
            print("Query:", query_string)
        rows = self.execute_query((query_string, d))
        counts = defaultdict(int)
        for r in rows:
            counts[r[0]] = r[1]
        checklists_df["Count"] = checklists_df.apply(lambda row : counts[row["SAMPLING EVENT IDENTIFIER"]], axis=1)
        return checklists_df

    def get_squares_with_bird(self, bird, max_dist=1, breeding=False,
                              date_range=None, lat_range=None, lng_range=None,
                              state=None, verbose=False):
        """Gets all the squares where a bird has been sighted.  This is used
        primarily to refine the terrain resistance.
        :param bird: Common name of the bird
        :param max_dist: max length of the checklist in Km
        :param breeding: whether to consider only the breeding period or not
        :param date_range: date range in years, as a string tuple of yyyy-mm-dd dates
        :param lat_range: range of latitudes to consider, as number tuple, optional.
        :param lng_range: range of longitudes to consider, as number tuple, optional.
        :param state: state, to limit the query.  Example: "US-CA"
        :param verbose: if True, more debugging information is printed.
        :return: List of squares with the bird.
        """
        query_string = [
            'select DISTINCT checklist.SQUARE',
            'from checklist join observation on',
            'checklist."SAMPLING EVENT IDENTIFIER" = observation."SAMPLING EVENT IDENTIFIER"',
            'where observation."COMMON NAME" = :bird',
            'and checklist."ALL SPECIES REPORTED" = 1',
        ]
        d = {'dist': max_dist ,'bird': bird}
        query_string.append('and checklist."PROTOCOL TYPE" != "Incidental"')
        query_string.append('and checklist."EFFORT DISTANCE KM" <= :dist')
         # Adds breeding portion
        if breeding:
            query_string.extend([
                'and (substr(checklist."OBSERVATION DATE", 6, 2) = "04"',
                'OR substr(checklist."OBSERVATION DATE", 6, 2) = "05"',
                'OR substr(checklist."OBSERVATION DATE", 6, 2) = "06")'
                ])
        if date_range is not None:
            query_string.append('and checklist."OBSERVATION DATE" >= :min_date')
            query_string.append('and checklist."OBSERVATION DATE" <= :max_date')
            d["min_date"], d["max_date"] = date_range
        if lat_range is not None:
            query_string.append('and checklist."LATITUDE" >= :min_lat')
            query_string.append('and checklist."LATITUDE" <= :max_lat')
            d["min_lat"], d["max_lat"] = lat_range
        if lng_range is not None:
            query_string.append('and checklist."LONGITUDE" >= :min_lng')
            query_string.append('and checklist."LONGITUDE" <= :max_lng')
            d["min_lng"], d["max_lng"] = lng_range
         # Runs the query.
        query_string = " ".join(query_string)
        if verbose:
            print("Query:", query_string)
        r = self.execute_query((query_string, d))
        return [row[0] for row in r]


    def get_observation_ratios(self, bird, min_checklists, bigsquare=False,
                               max_dist=1, verbose=False,
                               state=None, breeding=True):
        """This function is not used now.  It was the old, deprecated way of
        doing validation, and we are keeping the code for reference only."""
        # First, I create a dictionary of squares to checklist counts.
        query_string = [
            'select "SAMPLING EVENT IDENTIFIER",',
            'BIGSQUARE' if bigsquare else 'SQUARE',
            'from checklist where',
            '"ALL SPECIES REPORTED" = 1',
        ]
        d = {'dist': max_dist}
        query_string.append('and "PROTOCOL TYPE" != "Incidental"')
        query_string.append('and "EFFORT DISTANCE KM" <= :dist')
        if state is not None:
            query_string.append('and "STATE CODE" = :state')
            d['state'] = state
        # Adds breeding portion
        if breeding:
            query_string.extend([
                'and (substr("OBSERVATION DATE", 6, 2) = "04"',
                'OR substr("OBSERVATION DATE", 6, 2) = "05"',
                'OR substr("OBSERVATION DATE", 6, 2) = "06")'
                ])
        query_string = " ".join(query_string)
        if verbose:
            print("Query:", query_string)
        observations = self.execute_query((query_string, d))
        checklists_per_square = defaultdict(int)
        for _, sq in observations:
            checklists_per_square[sq] += 1
        # Now I keep only the squares with a minimum of checklists.
        checklists_per_square = {sq: c for sq, c in checklists_per_square.items() if c >= min_checklists}
        # Ok, I care only about these squares.
        # Now I want to know, for each of these squares, how many checklists there are that
        # contain the bird.
        query_string = [
            'select DISTINCT checklist."SAMPLING EVENT IDENTIFIER",',
            'checklist.BIGSQUARE' if bigsquare else 'checklist.SQUARE',
            'from checklist join observation on',
            'checklist."SAMPLING EVENT IDENTIFIER" = observation."SAMPLING EVENT IDENTIFIER"',
            'where observation."COMMON NAME" = :bird',
            'and checklist."ALL SPECIES REPORTED" = 1',
        ]
        d = {'dist': max_dist ,'bird': bird}
        query_string.append('and checklist."PROTOCOL TYPE" != "Incidental"')
        query_string.append('and checklist."EFFORT DISTANCE KM" <= :dist')
        if state is not None:
            query_string.append('and checklist."STATE CODE" = :state')
            d['state'] = state
        if breeding:
            query_string.extend([
                'and (substr(checklist."OBSERVATION DATE", 6, 2) = "04"',
                'OR substr(checklist."OBSERVATION DATE", 6, 2) = "05"',
                'OR substr(checklist."OBSERVATION DATE", 6, 2) = "06")',
                ])
        query_string = " ".join(query_string)
        if verbose:
            print("Query:", query_string)
        observations = self.execute_query((query_string, d))
        good_checklists_per_square = defaultdict(int)
        for _, sq in observations:
            if sq in checklists_per_square: # Otherwise, too few observations.
                good_checklists_per_square[sq] += 1
        for sq in checklists_per_square:
            if good_checklists_per_square[sq] > checklists_per_square[sq]:
                print("Too many checklists at", sq, good_checklists_per_square[sq], checklists_per_square[sq])
        return {sq: (good_checklists_per_square[sq] / checklists_per_square[sq])
                for sq in checklists_per_square}


def format_coords(coords, bigsquare=False):
    """
    formats coords from the eBird database format '4406;-12131' to
    tuple (44.06, -121.31) for (lat, lng) in WGS84 format
    :param coords (str): coordinates in eBird database format (ie '4406;-12131')
    :param bigsquare (bool): option is used in case these are big squares (one less decimal).
    :returns: tuple (lat, long)
    """
    lat, long = coords.split(';')
    if bigsquare:
        lat = float(lat[:-1] + '.' + lat[-1:]) + 0.05
        long = float(long[:-1] + '.' + long[-1:]) + 0.05
    else:
        lat = float(lat[:-2] + '.' + lat[-2:]) + 0.005
        long = float(long[:-2] + '.' + long[-2:]) + 0.005
    return (lat, long)


def transform_coords(geotiff, coord):
    """
    transforms WGS84 coordinates to the same projection as the given geotiff
    :param geotiff (scgt.GeoTiff): geotiff which we want our coordinates to map to
    :param coords: tuple of 2 floats (lat, lng), representing coordinates in WGS84 format
    :returns: tuple (lat, long) in the CRS of geotiff
    """
    lat, long = coord
    transformer = Transformer.from_crs("WGS84", CRS.from_user_input(geotiff.crs), always_xy=True)
    xx, yy = transformer.transform(long, lat)
    return (xx, yy)


"""
A module for common functionality in the validaiton process using ebird data
"""
class Validation(object):

    def __init__(self, obs_fn, geotiff_fn):
        """
        Generates a class for validation.
        It first tries to read the cached version of obs_fn for the specified geotiff_fn.
        If the cached version is not found, it is created.
        The cached version contains pre-translated coordinates to pixel values.
        :param obs_fn: Observations filename.
        :param geotiff_fn: name of a geotiff (habitat is preferred) used
            for translating coordinates to pixel coordinates.
        """
        self.obs_fn = obs_fn
        self.geotiff_fn = geotiff_fn
        h = hashlib.sha1(obs_fn.encode('utf-8'))
        h.update(geotiff_fn.encode('utf-8'))
        cached_fn = obs_fn + "." + h.hexdigest() + ".csv"
        if not os.path.exists(cached_fn):
            self._create_cached_observations(cached_fn)
        self.observations = pd.read_csv(cached_fn)


    def _create_cached_observations(self, cached_fn):
        """Creates a cached version of the observations that also contains
        pixel coordinates."""
        geotiff = GeoTiff.from_file(self.geotiff_fn)
        def f(row):
            square = row["Square"]
            if (isinstance(square, str)):
                coords = format_coords(square)
            else:
                coords = square
            lat, lng = coords
            pix_x, pix_y = transform_coords(geotiff, coords)
            return lat, lng, pix_x, pix_y
        df = pd.read_csv(self.obs_fn)
        df["lat"], df["lng"], df["pix_x"], df["pix_y"] = zip(*df.apply(f, axis=1))
        df.to_csv(cached_fn)


    def filter_CA_rectangle(self, observation_ratios, bigsquare=False):
        """
        Filters observation ratios, keeping only the ones in California.
        :param observation_ratios: list of tuples (square, observation_ratio)
        :returns: list of tuples (square, observation_ratio) with only squares in CA
        """
        # California rectangle
        ca_lng_max = -113
        ca_lng_min = -125
        ca_lat_max = 43
        ca_lat_min = 32
        result = {}
        for square, ratio in observation_ratios.items():
            lat, lng = format_coords(square, bigsquare=bigsquare)
            if ca_lat_min <= lat <= ca_lat_max and ca_lng_min <= lng <= ca_lng_max:
                result[square] = ratio
        return result

    def plot_observations(self, observation_ratios, hab_fn, output_path,
                          bigsquare=False, obs_multiplier=1):
        """
        Creates a Geotiff with the observation ratios plotted
        :param observation_ratios: list of tuples (square, observation_ratio)
        :param hab_fn: file path to the habitat geotiff to clone
        :param output_path: file path to create our new geotiff
        :param obs_multiplier: scalar to multiply the observation_ratios by
        """
        tile_scale = 30 if bigsquare else 3
        with GeoTiff.from_file(hab_fn) as hab_f:
            with hab_f.clone_shape(output_path, no_data_value=-1, dtype='float32') as obsTiff:
                for (square, observed) in observation_ratios:
                    if (isinstance(square, str)):
                        square = format_coords(square, bigsquare=bigsquare)
                    coord = transform_coords(obsTiff, square)
                    obsTiff.set_tile_from_coord(coord, observed * obs_multiplier, tile_scale)

    ### Correlation Functions ###
    def get_df_correlation(self, df):
        return df.corr()

    # Weighted correlation coefficent
    def weighted_correlation(self, df):
        '''
        :param df: dataframe with 3 columns: 'repop', 'obs_ratio', and 'weight'
        :returns: the weighted correlation coefficent of the df
        '''
        # Weighted Mean
        def m(x, w):
            return np.sum(x * w) / np.sum(w)

        # Weighted Covariance
        def cov(x, y, w):
            return np.sum(w * (x - m(x, w)) * (y - m(y, w))) / np.sum(w)

        # Weighted Correlation
        return cov(df['repop'], df['obs_ratio'], df['weight']) / np.sqrt(cov(df['repop'], df['repop'], df['weight']) * cov(df['obs_ratio'], df['obs_ratio'], df['weight']))


    def weighted_repop_to_observation_ratio_df(
        self, repop_tif, hab, observation_ratios, bigsquare=False,
        tile_scale=4, weighted_tile_size=100):
        '''
        :param repop_tif: repopulation geotiff
        :param hab: habitat geotiff used to compute repop
        :param observation_ratios: list of pairs (square, observation ratio) from ebird.
        :param tile_scale: percentage of habitat the tile must contain to be considered "in habitat" if being refined by hab
        :param tile_scale: size of the tile around square
        :param weighted_tile_size: size of the tile to attribute grouped weights to
        :returns: a dataframe with columns repopulation, observation ratio, and weights
        '''
        df = pd.DataFrame(columns=['repop', 'hab', 'max_repop', 'max_hab', 'obs_ratio', 'lat', 'lng', 'x', 'y', ])
        count = defaultdict(int)
        for (square, ratio) in observation_ratios:
            if (isinstance(square, str)):
                coords = format_coords(square, bigsquare=bigsquare)
            else:
                coords = square
            lat, lng = coords
            coords = transform_coords(repop_tif, coords)
            repop_tile = repop_tif.get_tile_from_coord(coords, tile_scale=tile_scale)
            hab_tile = hab.get_tile_from_coord(hab, coords, tile_scale=tile_scale)
            if repop_tile is None or hab_tile is None:
                continue
            x, y = repop_tif.get_pixel_from_coord(coords)
            x_floor = x // weighted_tile_size
            y_floor = y // weighted_tile_size
            count[(x_floor,  y_floor)] += 1
            # df = df.append(
            df = pd.concat([df, pd.DataFrame.from_records([
                {'repop': np.average(repop_tile.m),
                 'hab': np.average(hab_tile.m),
                 'max_repop': np.max(repop_tile.m),
                 'max_hab': np.max(hab_tile.m),
                 'obs_ratio': ratio,
                 'lat': lat,
                 'lng': lng,
                 'x': x,
                 'y': y,
                 }])])
        # Now adds the weight column.
        df['weight'] = df.apply(lambda row:
            1 / count[(row.x // weighted_tile_size, row.y // weighted_tile_size)], axis=1)
        return df

    def get_repop_ratios(self, repop_tif, hab_tif, tile_scale=3):
        """
        Takes as input a dataframe containing columns Square (and possibly other columns), and
        adds to it columns for the total repopulation and amount of habitat.
        :param repop_tif: repopulation geotiff
        :param hab_tif: habitat geotiff used to compute repop
        :param tile_scale: size of the tile around square
        """
        df = self.observations.copy()
        def f(row):
            coords = (row["pix_x"], row["pix_y"])
            repop_tile = repop_tif.get_tile_from_coord(coords, tile_scale=tile_scale)
            hab_tile = hab_tif.get_tile_from_coord(coords, tile_scale=tile_scale)
            if repop_tile is None or hab_tile is None:
                return pd.NA, pd.NA
            avg_repop = np.average(repop_tile.m) / 255.
            avg_hab = np.average(hab_tile.m)
            max_repop = np.max(repop_tile.m) / 255.
            max_hab = np.max(hab_tile.m)
            return avg_repop, avg_hab, max_repop, max_hab
        df["avg_repop"], df["avg_hab"], df["max_repop"], df["max_hab"] = zip(*df.apply(f, axis=1))
        return df

