import os
from collections import namedtuple

BirdRunDef = namedtuple('BirdRun', [
    'nickname', # 6-letter ebird name.
    'name', # official name.
    'terrain_fn', # File for the terrain
    'habitat_fn', # File for the habitat.
    'transmission_fn', # Terrain transmission.
    'resistance_original_fn', # Original terrain resistance, unrefined.
    'terrain_histogram_json_fn', # File name for terrain histogram.
    'terrain_histogram_csv_fn', # File name for terrain histogram.
    'repopulation_fn', 'gradient_fn', 'log_fn',
    'validation_fn',
    'obs_path',
    'obs_csv_path',
    'do_gradient', 'do_validation',
    'hop_distance', 'num_spreads', 'num_simulations'])


class BirdRun(object):

    def __init__(self, data_path):
        """Initializes a bird run, given a data path"""
        self.files_path = data_path

    def get_bird_run(self, nickname, bird_name, run_name=None, do_gradient=False, do_validation=False,
                     hop_distance=4, num_spreads=5, num_simulations=2, transmission_exponent=0.5):
        """Given a bird name in 6-letter ebird format, returns the BirdRun object for the bird."""
        d = {"bird": nickname,
             "run_name": run_name or "Standard",
             "num_spreads": num_spreads,
             "hop_distance": hop_distance,
             "num_simulations": num_simulations,
             "transmission_exponent": transmission_exponent}
        self.createdir(os.path.join(self.files_path, "{bird}/Output/{run_name}".format(**d)))
        return BirdRunDef(
            nickname = nickname,
            name = bird_name,
            # Input ,
            terrain_fn = os.path.join(self.files_path, "Terrain/iucn_habclass_lvl2_us_300_near_cropped.tif"),
            habitat_fn = os.path.join(self.files_path, "{bird}/habitat.tif".format(**d)),
            transmission_fn = os.path.join(self.files_path, "{bird}/transmission_refined_{transmission_exponent}.csv".format(**d)),
            resistance_original_fn = os.path.join(self.files_path, "{bird}/resistance.csv".format(**d)),
            terrain_histogram_json_fn = os.path.join(self.files_path, "{bird}/terrain_hist.json".format(**d)),
            terrain_histogram_csv_fn = os.path.join(self.files_path, "{bird}/terrain_hist.csv".format(**d)),
            # Validation files.
            validation_fn = os.path.join(self.files_path, "{bird}/Ratios".format(**d)),
            # Output files
            repopulation_fn = os.path.join(self.files_path, "{bird}/Output/{run_name}/repopulation_spreads_{num_spreads}_hop_{hop_distance}_sims_{num_simulations}_texp_{transmission_exponent}.tif".format(**d)),
            gradient_fn = os.path.join(self.files_path, "{bird}/Output/{run_name}/gradient_spreads_{num_spreads}_hop_{hop_distance}_sims_{num_simulations}_texp_{transmission_exponent}.tif".format(**d)),
            log_fn = os.path.join(self.files_path, "{bird}/Output/{run_name}/log_spreads_{num_spreads}_hop_{hop_distance}_sims_{num_simulations}_texp_{transmission_exponent}.json".format(**d)),
            obs_path = os.path.join(self.files_path, "{bird}/Observations".format(**d)),
            obs_csv_path = os.path.join(self.files_path, "{bird}/Output/{run_name}/obs_{num_spreads}_hop_{hop_distance}_sims_{num_simulations}_texp_{transmission_exponent}.csv".format(**d)),
            # Run parameters
            do_gradient=do_gradient,
            do_validation = do_validation,
            hop_distance = hop_distance,
            num_spreads = num_spreads,
            num_simulations = num_simulations
        )

    def get_observations_fn(self, obs_path, bigsquare=False, **kwargs):
        """Completes the name of an observation ratio file, adding the information on minimum number of observations,
        and maximum length walked.
        """
        d = dict(**kwargs)
        d["isbig"] = "_big" if bigsquare else ""
        return os.path.join(obs_path, "CA_min_{min_checklists}_len_{max_distance}{isbig}.json".format(**d))

    def get_observations_display_fn(self, obs_path, bigsquare=False, **kwargs):
        """Completes the name of an observation ratio tif file, adding the information on minimum number of observations,
        and maximum length walked.
        """
        d = dict(**kwargs)
        d["isbig"] = "_big" if bigsquare else ""
        return os.path.join(obs_path, "CA_min_{min_checklists}_len_{max_distance}{isbig}.tif".format(**d))

    def get_observations_all_fn(self, obs_path, **kwargs):
        """Completes the name of an observation ratio file, adding the information on minimum number of observations,
        and maximum length walked.
        """
        d = dict(**kwargs)
        return os.path.join(obs_path, "CA_all_len_{max_distance}_{date_range}_{num_squares}.csv".format(**d))

    def get_observations_all_display_fn(self, obs_path, **kwargs):
        """Completes the name of an observation ratio tif file, adding the information on minimum number of observations,
        and maximum length walked.
        """
        d = dict(**kwargs)
        return os.path.join(obs_path, "CA_all_len_{max_distance}_{date_range}_{num_squares}.tif".format(**d))

    def createdir_for_file(self, fn):
        """Ensures that the path to a file exists."""
        dirs, ffn = os.path.split(fn)
        # print("Creating", dirs)
        os.makedirs(dirs, exist_ok=True)

    def createdir(self, dir_path):
        """Ensures that a folder exists."""
        # print("Creating", dir_path)
        os.makedirs(dir_path, exist_ok=True)
