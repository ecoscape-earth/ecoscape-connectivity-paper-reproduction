# Producing SQLite databases from eBird Data

In order to reproduce the results, you need to have eBird observation data in a sqlite database format.  Here, we explain how to produce such sqlite databases. 

> Note: We do not have the permission to redistribute eBird data, and so we cannot provide you with the sqlite database files directly.  If you had a letter of permission / support from eBird, we would be happy to share our database files with you; this would likely save you a few days of downloading and processing data.  If you have permission from eBird, please contact Luca de Alfaro, luca@ucsc.edu for obtaining the database files. 

The sqlite databases, compressed with gzip, have the following sizes: 

* Full eBird database: 52 GB 
* eBird database for US West, which suffices to reproduce the results: 11.6 GB
* Observations database: 18 GB
* Observation database for US West: 3.9 GB

To use the databases, you need to uncompress them of course.  To reproduce the resuls of the paper, you just need the US West data.  If you need to re-create the data, you can proceed as follows. 

## Download the data

The first step is to [download the eBird Basic Dataset (EBD)](https://science.ebird.org/en/use-ebird-data/download-ebird-data-products).  You may need to apply for permission. 

You should download two files, the full eBird data, and also the smaller effort dataset. 
These are .tar files (as of April 2023), and if you expand them, there will be .txt.gz files in them.   The following files are what we used (but later files will be fine; we specify in the code which date range to use for the experiments):

* The full eBird data, such as `ebd_relApr-2022.txt.gz`
* The "effort" dataset, such as `ebd_sampling_relApr-2022.txt.gz`

## Produce the .csv files to create the database

To produce the csv files that will be loaded into the database, do: 

```
gunzip -c ebd_sampling_relApr-2022.txt.gz | awk -f checklists.awk > checklists.csv
gunzip -c ebd_relApr-2022.txt.gz | awk -f observations.awk - > observations.csv
```

You can replace the awk scripts with their `_uswest` version if all you want is information on the US West (US, west of -95). 

> Explanation: The EBD is a single flat csv file, in which each row contains information about both a bird sighting, and the checklist in which the bird was seen.  This format makes the EBD data easy to use, but is not the most efficient way to organize the data. 
We store the data in two database tables; please see `create_tables.sql` for the details. 
Essentially, one table contains information about checklists (information about a single checklist: location, time, user, etc, but not which birds were seen in the checklist), and another table stores bird observations (the bird name, and a reference to the checklist in which the bird was seen). 
To populate the two tables, we need to produce two csv files, which are then read by sqlite in the `create_tables.sql` script.  

> Squares: to faciliate the spacial indexing of the checklists, we associate with each checklist a _square_, obtained by rounding the checklist coordinates.  For instance, if a checklist is at latitude and longitude (36.995575,-122.091983), we assign the square "36.99;-122.09" to it.  A square is roughly one square Kilometer in size. Indexing checklists by squares enables us to quickly find all the checklists that occur in a square-Kilometer area. 

## Produce the database

    sqlite3 my_new_database.db
    .read create_tables.sql

The above creates the database with the correct format, reads the data into the tables, and creates the indices.  You can use `create_tables_uswest.sql` to create a smaller database that only contains the data for US West, and that suffices to reproduce the results of the paper. 

***This is all you need to do to reproduce the results of the paper.***

# Example queries

We give here a few sample queries, purely as documentation.  You do not need to run any of these queries. 

The following query gives you the squares with the most sightings of white-headed woodpeckers, sorted in decreasing order of total sightings: 

    select SQUARE, SUM(NUM_SEEN) from observation where  NAME = "White-headed Woodpecker" group by SQUARE order by 2 desc limit 10;

Note that I have renamed some columns in my version of the db to make it easier, but the logic is the same (Use "..." if the column name includes a space)
If you also want to access fields that talk about the checklist, such as the distance in Km for the checklist, you would need to make a join with the other "checklist" table.

Another idea would be: take the places with at least (say) 50 checklists, that are in the habitat of the w-h wp.  Then measure the fraction of checklists that contain w-h wp.
Here is how to do a simple join w/o any conditions (note that I have renamed the fields):

    select * from checklist JOIN observation on checklist.SEI = observation.SEI limit 10;

    select * from checklist JOIN observation on checklist.SEI = observation.SEI where observation.NAME = "White-headed Woodpecker" limit 10;

To exclude old ones:

    select * from checklist JOIN observation on checklist.SEI = observation.SEI where observation.NAME = "White-headed Woodpecker" and checklist.OBSERVATION_DATE > "2000-00-00" limit 10;

This gives you the squares where some whwp has been seen:

    select DISTINCT(SQUARE) from observation where NAME = "White-headed Woodpecker" and NUM_SEEN > 0 limit 10;

This gives you the number of checklists in every square where at least one whwp has been seen:

    select SQUARE, COUNT(*) FROM checklist where SQUARE in (select DISTINCT(SQUARE) from observation where NAME = "White-headed Woodpecker" and NUM_SEEN > 0) group by SQUARE limit 10;

    select SQUARE, COUNT(*) AS CNT FROM checklist where SQUARE in (select DISTINCT(SQUARE) from observation where NAME = "White-headed Woodpecker" and NUM_SEEN > 0) group by SQUARE order by CNT DESC limit 10;

And this, the grand finale, gives you all the squares where a white-headed woodpecker has been seen, and there are at least 50 checklists.  Takes a fraction of a second.  SQL rules.

    select SQUARE, CNT from (select SQUARE, COUNT(*) AS CNT FROM checklist where SQUARE in (select DISTINCT(SQUARE) from observation where NAME = "White-headed Woodpecker" and NUM_SEEN > 0) group by SQUARE) where CNT > 49;
    
But wait, there's more! This gets the number of of total checklists AND number of checklists containing white-headed woodpeckers for every square in which white-headed woodpecker's have been observed and having 50 or more checklists
```
select SQUARE, COUNT(checklist."SAMPLING EVENT IDENTIFIER") as CNT, SEEN, round(SEEN * 1.0 / COUNT(checklist."SAMPLING EVENT IDENTIFIER"), 5) from (checklist join (select SQUARE, COUNT(DISTINCT("SAMPLING EVENT IDENTIFIER")) as SEEN from observation where "COMMON NAME" = "White-headed Woodpecker" and "OBSERVATION COUNT" > 0 group by SQUARE) using(SQUARE)) group by SQUARE having CNT > 49 order by 4 desc limit 10;
```
