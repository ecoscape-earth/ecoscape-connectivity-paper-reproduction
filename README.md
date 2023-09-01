# Bird Mapping Project

The code in this repository enables the reproduction of the results of the EcoScape paper. 

## Contributors (alphabetically)

* Coen Adler
* Luca de Alfaro
* Artie Nazarov
* Natalia Ocampo-Peñuela
* Jasmine Tai
* Natalie Valett

## Repository Organization

* `birdmaps` contains some code that is used specifically for the paper, and that is imported in the notebooks. 
* `ebird_data` contains information and scripts for generating a database of bird observations.  The database is optional; it is needed to reproduce the initial step of our validation. 
* `data` contains data that will make it easier for you to reproduce the results.  In essence, in `data` you will put a copy of the entire data generated, so that you can decide whether to verify all results, or only a part. 
* The notebooks cited in this README are all at top level in this repository. 

## Data

You will need two datasets. 

* [`CA-EcoScape-Paper.zip`](https://drive.google.com/file/d/1szR8edvTmrNWXJYmruavPI7mPNgsUPbs/view?usp=sharing) : this provides the habitat and terrain info for the birds, as well as the terrain permeabilities.  You can regenerate this data with the appropriate packages, but it's very convenient to have.  Download the file, put it into the `data` folder, and unzip it. 
* `bird-data-uswest.db` : An Sqlite database containing all eBird observations in the Western part of the US. As we are not allowed to redistribute eBird data, you will have to build this database yourself. You can find [detailed instructions](ebird_data/README.md) in the `ebird_data` folder.  It is a process that may take a few days.  

The above database is not strictly necessary.  It is used to generate, in California, the list of locations where people birded, along with the average sightings of a bird per checklist in those locations.  We provide these location lists; the database is only necessary if you wish to recreate them. 

Additionally, the database is needed to analyze the nature of noise in bird observations, and precisely, the amounts of _location noise_ (difference between bird frequency at similar locations) vs. _checklist noise_ (difference between bird frequency in different checklists at the same location).  This is a point that is rather tangential to the paper, and only mentioned in the methods. 

## Where to put Data and Computation

You can compute either on Google Colab, or locally, or both. 

You need GPUs for the ecoscape-connectivity package.  You can use Colab for this, or you can run locally if you have a local GPU. 

You need to run locally the `GenerateValidationData.ipynb` notebook.  This because you need to access a large Sqlite database, and on Colab this does not work well.  Also, this step takes a long time, and requires no GPU, so it is more suited to be run locally. 

The code, either local or on Colab, needs access to the `CA-EcoScape-Paper` data. 
You can have this data available both on Colab, and locally, by placing it on Google Drive, and by using Drive for Desktop to keep in synch the data on Google Drive with the data on the local file system. 
This approach is the one we followed for the paper. 

## Notebooks

Many notebooks at the beginning define these constants; you may need to change them according to where you want to run the code. 

* `IS_LOCAL` : indicates whether you are running the code locally or on Google Colab. 
* `REMOTE_PATH` : Path on Google Drive to the folder where you put the CA-EcoScape-Paper data. 
* `LOCAL_PATH`: Path in the local file system where a copy of CA-EcoScape-Paper can be found. 

## File locations. 

Before one starts, it is useful to take a look at `ecoscape_utilities.BirdRun`.
That class defined the local   
That file describes the location of every input and output. 
There: 

* A bird name is its English name, such as "Acorn Woodpecker". 
* A bird nickname is its eBird API nickname, such as "acowoo". The birds we have are: 
  * `acowoo`: Acorn Woodpecker
  * `oaktit308`: Oak Titmouse (the `308` is there for historical reasons; it is a variation where terrain type 308, which in California is sparse Oak woodland, is considered as possible habitat for the Oak Titmouse).
  * `stejay`: This is the Steller Jay. 
* `run_name` is the name of one of the runs we did for the paper.  We did three main runs: 
  * `Jun8`: This run produced all the data used for validation.  The run computed connectivity layers for many combinations of gap crossing and dispersal distances.  To save time, no flow layer was produced. 
  * `Jun9-gradient`: This run produced flow layers.  We used the flow layer for Acorn Woodpecker for the figure in the paper. 
  * `Aug24-timing`: This run was used simply to obtain accurate measurements of running time and result variance. 

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

## Reproducing The Results

### Generating Terrain and Habitats 

> Step (habitat), depends(). 

This uses the `Jasmine_complete_here.ipynb` notebook. 
We provide already the results for this step, so it can be skipped if desired. 

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
If you have used IUCN data to obtain `{bird}/resistance.csv`, then you  can run [`RefineResistanceWithForestTerrain.ipynb`](RefineResistanceWithForestTerrain.ipynb) to generate the values of terrain permeability we use. 

### Compute the connectivity and flow layers. 

Step (repopulation), depends(transmission). 

Upload to colab the notebook [`ConnectivityAndFlow.ipynb`](ConnectivityAndFlow.ipynb) and run it. 

You need to choose which birds to process, and with what parameters. 
This is done in the cell "Bird Run Definition". 
The notebook we give does the most complete runs; these will take several hours even with a fast GPU, as we run the process for a large combination of parameters. 
You can speed up the process by selecting only some gap lengths, number of gaps, or by turning off the 
production of the gradient. 
If you have a GPU you can also run this step locally.   
We recommend running this on A100 GPUs. 

### Generates the validation dataframes

Step (validation) depends(prepare_validation, repopulation).

In this step, we prepare some data that will facilitate the visualization of the correlation between habitat connectivity, and bird sightings. 

Use the notebook [`Validation.ipynb`](Validation.ipynb).
In this step, we read the output connectivity layers for the birds, and we correlate the connectivity with the ebird sightings (the information produced in Step (prepare_validation)). 
The process takes a long time, because for each geographical location computed in Step (prepare_validation), we need to sample the connectivity and habitat layers at the correct pixels, and this is not immediate. For the complete set of runs, this may take some hours.   
This takes a while to run, as it needs to read all the various terrains, and write all the results. 

### Display the validation results.

Step (validation_results) depends(validation). 

Use the notebook [`DisplayValidationResults.ipynb`](DisplayValidationResults.ipynb).  This loads the dataframes generated by the previous step, and produces all the figures related to the correlation between habitat connectivity and ebird sightings. 

### Estimate Running Time

The notebook [`EstimateRunningTime.ipynb`](EstimateRunningTime.ipynb) was run on Colab, and yielded the running times.  It is given as is.  It should work; if it complains that the run Aug24-timing is missing, you can do: 

    cd data/CA-EcoScape-Paper
    cp -r acowoo/Output/Jun8 acowoo/Output/Aug24-timing
    cp -r oaktit308/Output/Jun8 oaktit308/Output/Aug24-timing
    cp -r stejay/Output/Jun8 stejay/Output/Aug24-timing

before running the notebook.

We give here the notebook that produced the timing results, with its original output. 
If the type of GPUs or CPUs available on Colab changes, these numbers might change. 
The numbers were obtained on August 24, 2023, on A100 GPUs. 

### Estimate Accuracy

The notebook [`EstimateAccuracy.ipynb`](EstimateAccuracy.ipynb) is the one we used to estimate the accuracy (standard deviation) with which the connectivity of the flow layer is computed.  It is here reproduces as-is, with the original outputs.  
This notebook needs to be run on Colab, or on a machine with fast GPUs; we used A100 GPUs on Colab. 

