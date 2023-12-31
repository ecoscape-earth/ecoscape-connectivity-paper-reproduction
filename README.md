# Bird Mapping Project

The code in this repository enables the reproduction of the results of the EcoScape paper. 

## Contributors (alphabetically)

* Coen Adler
* Luca de Alfaro
* Artie Nazarov
* Natalia Ocampo-Peñuela
* Jasmine Tai
* Natalie Valett

## Code archives

The code used comprises 4 packages, which are available in archival form:

* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8395862.svg)](https://doi.org/10.5281/zenodo.8395862) ecoscape-connectivity
* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8395867.svg)](https://doi.org/10.5281/zenodo.8395867)
 ecoscape-layers
* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8395869.svg)](https://doi.org/10.5281/zenodo.8395869) ecoscape-utils
* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8395864.svg)](https://doi.org/10.5281/zenodo.8395864) scgt

For general use, these packages can be installed from the Python package repository pypi via `pip install`. 
For reproducibility, we recommend using the archived versions, since the packages on pypi may have been updated since the paper was written.

## Repository Organization

* `birdmaps` contains some code that is used specifically for the paper, and that is imported in the notebooks. 
* `ebird_data` contains information and scripts for generating a database of bird observations.  The database is optional; it is needed to reproduce the initial step of our validation. 
* `data` contains data that will make it easier for you to reproduce the results.  In essence, in `data` you will put a copy of the entire data generated, so that you can decide whether to verify all results, or only a part. 
* The notebooks cited in this README are all at top level in this repository. 

## Data

You will need two datasets. 

* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8395850.svg)](https://doi.org/10.5281/zenodo.8395850)
 [`CA-Final.zip`](https://zenodo.org/doi/10.5281/zenodo.8395850) : this provides the habitat and terrain info for the birds, as well as the terrain permeabilities.  You can regenerate this data with the appropriate packages, but it's very convenient to have.  Download the file, put it into the `data` folder, and unzip it. 
* `bird-data-uswest.db` : An Sqlite database containing all eBird observations in the Western part of the US. As we are not allowed to redistribute eBird data, you will have to build this database yourself. You can find [detailed instructions](ebird_data/README.md) in the `ebird_data` folder.  It is a process that may take a few days.  

The above database of eBird data is not strictly necessary.  It is used to generate, in California, the list of locations where people birded, along with the average sightings of a bird per checklist in those locations.  We provide these location lists; the database is only necessary if you wish to recreate them. 

Additionally, the database is needed to analyze the nature of noise in bird observations, and precisely, the amounts of _location noise_ (difference between bird frequency at similar locations) vs. _checklist noise_ (difference between bird frequency in different checklists at the same location).  This is a point that is rather tangential to the paper, and only mentioned in the supplementary material. 

## Where to put Data and Computation

You can compute either on Google Colab, or locally, or both. 

You need GPUs for the ecoscape-connectivity package.  You can use Colab for this, or you can run locally if you have a local GPU.  We used A100 GPUs for many runs.  You should be able to use also T4 GPUs, but they will be somewhat slower, and they might run out of memory with the chosen parameters when flow layers are desired (this could be obviated by changing some parameters such as tile sizes). 

The code, either local or on Colab, needs access to the `CA-Final` data. 
You can have this data available both on Colab, and locally, by placing it on Google Drive, and by using Drive for Desktop to keep in synch the data on Google Drive with the data on the local file system. 
This approach is the one we followed for the paper. 

## Notebooks

Many notebooks at the beginning define these constants; you may need to change them according to where you want to run the code. 

* `IS_LOCAL` : indicates whether you are running the code locally or on Google Colab. 
* `REMOTE_PATH` : Path on Google Drive to the folder where you put the CA-EcoScape-Paper data. 
* `LOCAL_PATH`: Path in the local file system where a copy of CA-EcoScape-Paper can be found. 

### EcoScape

Before one starts, it is useful to take a look at `ecoscape_utilities.BirdRun`.
That file describes the location of input and output files. 
There: 

* A bird name is its English name, such as "Acorn Woodpecker". 
* A bird nickname is its eBird API nickname, such as "acowoo". The birds we have are: 
  * `acowoo`: Acorn Woodpecker
  * `stejay`: This is the Steller Jay. 
* `run_name` is the name of one of the runs we did for the paper.  You can find the results in <bird_nickname>`/Output/`<run_name> . We did the following runs: 
  * `Paper`: This run produced all the data used for the sensitivity analysis. We run 400 simulations for every gap_crossing and num_spreads parameters. 
  * `Gradient`: These were the runs for generating connectivity and flow used in the main figure for California; the simulations were run 2000 times to guarantee superior accuracy. 
  * `Paper10000`: These were the runs done for generating the sightings to connectivity graphs in the paper.  We performed 10000 simulations to have as accurate as possible results for the paper figures. 
  * `Timing`: This is the run we used to analyze the runtime of the method. 
  * `Precision`: This is the run we did to analyze the standard deviation of the connectivity and flow.  

The input files are the following, where `{bird}` is the bird nickname. All of these file names are relative to a root directory, which can be specified in the code: 

* `Terrain/iucn_habclass_lvl2_us_300_near_cropped.tif` is the terrain description for California, at 300m resolution. 
* `{bird}/habitat.tif` is the habitat raster for each bird (this can be regenerated with the Generating Habitats step below). 
* `{bird}/transmission_refined_1.csv` is the landscape permeability dictionary.  This is in fact the same for all runs. 

In addition to these, there are files that are generated by our code.  These contain parameter values in the filenames, often; these are: 

* `num_spreads` is the number of gap-crossings a bird can do during dispersal. 
* `hop_distance` is the gap-crossing distance for the bird, measured in pixels. Each square has an edge of 300m, so a hop distance of 2 corresponds to 600m. 
* `num_simulations` is the number of simulations performed for the spread process; a typical value is 400. 

The main files generated are:   

* `{bird}/Output/{run_name}/repopulation_spreads_{num_spreads}_hop_{hop_distance}_sims_{num_simulations}_texp_1.tif` contains the output connectivity layer. 
* `{bird}/Output/{run_name}/gradient_spreads_{num_spreads}_hop_{hop_distance}_sims_{num_simulations}_texp_1.tif` contains the output flow layer.
* `Data/CA/{bird}/Observations/CA_all_len_{l}_2012-01-01-2018-12-31_20000.csv` contain data on all bird observations in checklists of length at least `l` in a given date range, limited to 20,000 observation locations if necessary.  Generally, for the given date range, there were a few more than 18,000 observation locations (technically, squares; see `ebird_data/README.md`).  We used value 2 for `l`. 
* `Data/CA/{bird}/Output/{run_name}/obs_{num_spreads}_hop_{hop_distance}_sims_{num_simulations}.csv` is a Pandas dataframe containing data with the repopulation value, and sightings, of a bird at the various locations.  These dataframes are read by the code that generates the validation graphs. 

### Omniscape

There is a `CA-Final/Omniscape` folder with what is needed to reproduce the Omniscape run results; see later for instructions. 

## Simulated Landscape

These are produced by the [`SimulatedLandscapes.ipynb`](SimulatedLandscapes.ipynb) notebook. 

## Reproducing The EcoScape / Omniscape / Patch Size Results

### Generating Terrain and Habitats 

> Step (habitat), depends(). 

This uses the `GenerateLayers.ipynb` notebook to create the habitat layers, landcover matrix layer, and resistance dictionaries for a list of bird species. 
We provide already the results for this step, so it can be skipped if desired. 

**Note:** eBird no longer provides the layers we used, as of Fall 2023.  
Thus, the notebook can no longer be run. 
We provide its result, namely, the terrain and habitat layers for all species. 
The new `ecoscape_layers` package works with 2022 eBird layers, which differ slightly from the ones we used for the paper; thus, small differences in output can be expected if one runs the updated package. 

### Prepare the observation data for the validation

Step (prepare_validation), depends(habitat). 

Note: This step is optional.  It required the database that contains all ebird observations, mentioned above.  If you do not have the database, you can skip this step, as we already include the output. 

Run the notebook [`GenerateValidationData.ipynb`](GenerateValidationData.ipynb)

You need to decide which birds to process, and which combination of ebird walked distance, min checklists per square, whether to use small (1Km) or big (10Km) squares, etc. 

For the paper, we run it with the following parameters:

```
max_distances = [2]
date_range = ("2012-01-01", "2018-12-31")
breeding = True
state = "US-CA"
num_sample_squares = 20000 # Sampling number for the squares. 
```

### Generating the terrain permeability

> Step (transmission), depends(habitat). 

This step is not strictly necessary, as we provide the output already. 
If you wish to recompute the terrain permeability, there are two steps. 

The first step consists in running the notebook [`TerrainHistograms.ipynb`](TerrainHistograms.ipynb).  This notebook generates a histogram of bird sightings according to landcover type, considering all seasons (and not only breeding season).
It leaves the output in the files `data/CA-Final/{bird}/terrain_hist.*`. 

The second steps consists in merging the file `{bird}/resistance.csv`, derived from IUCN data, with the above histograms.  To do so, run the notebook [`RefineResistanceWithEbirdData.ipynb`](RefineResistanceWithEbirdData.ipynb). 
This will generate the `data/CA-Final/{bird}/transmission_refined_1.csv` files that are used.  Note that a copy of these files is also present in the Omniscape folders. 
These files are csv files that map landcover type to landcover permeability. 

The notebook [`GeneratePermeabilityTables.ipynb`](GeneratePermeabilityTables.ipynb) generates the tables of landcover type permeability included, with minor esthetical edits, in the paper. 

### Compute the connectivity and flow layers. 

> Step (repopulation), depends(transmission). 

There are three substeps, for EcoScape, Omniscape, and patch size analysis. 

#### EcoScape

Upload to Google Colab the notebook [`ConnectivityAndFlow.ipynb`](ConnectivityAndFlow.ipynb) and run it. 

We recommend running this on A100 GPUs; the T4 also may work (except it might go out of memory for the flow layer; you can reduce the tile size to 1024 x 1024). 
There are three cells at the end that do the runs: 

* `run_birds` does the sensitivity analysis, with 400 simulations, generating the `Paper` output.  This takes about two hours. 
* `run_birds_details` generates the `Paper10000` output, used for the graphs relating observations to connectivity. This takes less than one hour. 
* `run_birds_gradient` generates the `Gradient` output, used for the initial figure for the Acorn Woodpecker, connectivity and flow layers. This takes about 3-5 minutes. 

To obtain a clean estimation of EcoScape running time, we used the [`EstimateRunningTime.ipynb`](EstimateRunningTime.ipynb) on Google Colab, run on September 21, 2023, on A100 GPUs; the notebook above is the one we used to obtain the running times.
***Note:*** The cells that contain GPU computation need to be run _more than once_ in order to yield accurate results.  This is because the first time a GPU-accelereated computation is run, the GPU is initialized, and this takes a few seconds.  The second time, the initialization is not needed.

#### Omniscape

First, you need to run the notebook [`PrepareOmniscapeLayers.ipynb`](data/Omniscape/PrepareOmniscapeLayers.ipynb) to generate the conductance layers needed by Omniscape.

Then, you need to run Omniscape.
To do so, you need to install Julia, and then run the following commands: 

```
cd data/CA-Final/Omniscape
julia
```

Then, in the Julia prompt: 

```
using Pkg; Pkg.add("Omniscape")
using Omniscape;
run_omniscape("OmniscapeRunAcowooCA.ini")
run_omniscape("OmniscapeRunStejayCA_h2_S3.ini")
```

This step is also used to generate the Omniscape running time. 

#### Patch Size Analysis

To compute the patch sizes, you can use the [`ComputePatchSizes.ipynb`](ComputePatchSizes.ipynb) notebook.  
We ran it on Google Colab, using A100 GPUs; the time is about 30s for both bird species. 
This step is also used to obtain the running times for the patch size analysis.

### Computing FCH

> Step (fch), depends(repopulation).

The FCH (Functionally Connected Habitat) is the sum of the connectivity over the area of habitat, and gives an estimate of the amount of habitat that is functionally connected.
The FCH is computed in [`ComputingFCH.ipynb`](ComputingFCH.ipynb); the notebook also computes the percentage error for Acorn Woodpecker in using 400 vs 10000 simulations. 

### Generates the validation dataframes

> Step (validation) depends(prepare_validation, repopulation).

In this step, we read the output connectivity layers for the birds, and we correlate the connectivity with the ebird sightings (the information produced in Step (prepare_validation)). 
The process takes a long time, because for each geographical location computed in Step (prepare_validation), we need to sample the connectivity and habitat layers at the correct pixels, and this is not immediate. For the complete set of runs, this may take some hours.   
This takes a while to run, as it needs to read all the various terrains, and write all the results. 

You need to run these notebooks: 

* [`Validation.ipynb`](Validation.ipynb) generates the validation data for the EcoScape output.  
* [`ValidationOmniscape.ipynb`](ValidationOmniscape.ipynb) generates the validation data for the Omniscape output. 
* [`ValidationConnectivityAsPatches.ipynb`](ValidationConnectivityAsPatches.ipynb) generates the validation data for the patch size analysis.

### Display the validation results.

> Step (validation_results) depends(validation). 

The following three notebooks display the validation results, and in particular, the graphs of sightings vs. connectivity.
The notebooks also compute the coefficients R^2 of determination that are given in the paper. 

* [`DisplayValidationResults-Graphs.ipynb`](DisplayValidationResults-Graphs.ipynb) for Ecoscape; 
* [`DisplayValidationResults-Omniscape.ipynb`](DisplayValidationResultsOmniscape.ipynb) for Omniscape; 
* [`DisplayValidationResults-PatchSize.ipynb`](DisplayValidationResults-PatchSize.ipynb) for the patch size analysis.

This loads the dataframes generated by the previous step, and produces all the figures related to the correlation between habitat connectivity and ebird sightings. 

***Sensitivity Analysis.***
In addition, you can also run the sensitivity analysis for the EcoScape results, which explores the effect of gap-crossing and dispersal distance on the coefficient of determination between sightings and connectivity. 
Use the notebook [`DisplayValidationResults-Sensitivity.ipynb`](DisplayValidationResults-Sensitivity.ipynb). 
This generates the sensitivity analysis figure in the supplementary material. 

### Estimate EcoScape Accuracy

> Step (estimate_accuracy) depends(transmission).

The notebook [`EstimateAccuracy.ipynb`](EstimateAccuracy.ipynb) is the one we used to estimate the accuracy (standard deviation) with which the connectivity is computed. 
It is here reproduces as-is, with the original outputs.  
To compute the standard deviation, the notebook performs a number of simulations, and then computes the standard deviation of the connectivity. 
The process is computation-itensive; the notebook needs to be run on Colab, or on a machine with fast GPUs; we used A100 GPUs on Colab. 

### Analyze eBird Checklist Noise

> Step (checklist_noise) depends(validation).

This is a step that requires the database. 
The notebook [`AnalyzeEbirdNoise.ipynb`](AnalyzeEbirdNoise.ipynb) analyzes the noise in checklists, determining whether location noise or checklist noise is predominant. 
We provide it as run, with the results used for the paper. 
