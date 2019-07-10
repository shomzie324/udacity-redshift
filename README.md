# Udacity Data Engineering Project 3: Data Warehouse With AWS

## Datasets
There are two datasets being used in this project. The first is song metadata stored in data/song_data. This includes information about a song including who its artist is, how long the song is and information about the artist who created it including their name and location. These files are stored as JSON. An example is below:
```json
{"num_songs": 1, "artist_id": "ARJIE2Y1187B994AB7", "artist_latitude": null, "artist_longitude": null, "artist_location": "", "artist_name": "Line Renaud", "song_id": "SOUPIRU12A6D4FA1E1", "title": "Der Kleine Dompfaff", "duration": 152.92036, "year": 0}
```

The other dataset is log data stored in data/log_data. These files are stored as JSON and include information about user activity for every session within the app. This includes information such as the userAgent used to access the app, the user's name, location, and what songs they have listened to. Each log file represents 1 day of user activity within the app.


## Setup
The files in this repo are as follows:
* create_tables.py: python script to create the sparkify database or reset it
* etl.py: python script to run the queries that extract the JSON data into staging tables in redshift and insert it into the dimensional tables which are also stored in redshift.
* sql_queries.py: utilities file containing the PostgreSQL/Redshift queries that will be used to interact with the sparkify database.
* dwh.cfg: configuration file that contains the settings required to connect to the redshift datawarehouse and run queries against it

### How to run this project:
0.  Before starting: Add your own redshift and AWS settings to dwh.cfg. Once your settings are included, be sure not to push your config file to any public repos on platforms like github or gitlabs.
1. Run the create_tables.py script to reset the database or create it if it does not exist:
```bash
python create_tables.py
```
2. Run the etl.py script to extra the data from data/song_data & data/log_data, transform it and load it into the postgreSQL database set up in step 1:
```bash
python etl.py
```
3. Run quries against datawarehouse inside Amazon Redshift Query Editor to ensure everything worked


## Song Plays Datawarehouse
The purpose of this data mart is to extract the various sources of data Sparkify collects on songs and user activity to provide useful and fast insights into how the streaming application is currently being used. This document will outline the datawarehouse design and processing pipeline.

## Schema Design
The entire schema is stored in Amazon redshift and in this project is being accessed with a PostgreSQL driver.

There are two staging tables that serve as a landing zone or back office for the song and log data that is stored in Amazon S3. The COPY command is used to parallelize the data extraction resulting in faster ingest speeds. 

**NOTE: A 4 node cluster was used for ingestion. This is a recommended minimum. Though less could be used, it would not take advantage of the parallelism that the redshift COPY command provides**

The datawarehouse is organized as a  having a back office that contains 2 staging tables which is where data from longs and song data will initially land. There is also a star schema dtaa mart as the front office with user activity related to song plays as the fact table. This is because the primary goal was to optimize queries related to song plays as that is what the analytics team is primarily interested in. Right now, the analytics team is finding they are wasting a lot of time sorting through the user activity logs when they are just stored as JSON and need a more efficient way to gather business intelligence from the data regarding both the users activity and information about the songs themselves. 

This star schema design minimizes the amount of joins needed to query the front office data. This will make gathering useful insights from the data, and by extension acting on it, much faster.

There is 1 fact table (song_plays) and 4 dimension tables(users,artists,songs,time). The song_plays table is connected to the dimension tables for quick analytics that require more detailed information along a given dimension. The table descriptions are as follows:

**songplays:** songplay_id, start_time, user_id, level, song_id, artist_id, session_id, location, user_agent
* activity events from the log data that tracks whenever a user plays a song
* start_time is used as a sortkey since the table is event based and when those events occurred is a logical ordering and connection that. Since analytics would likely be focused on what songs to offer, song_id is used as a distribution key 
**users:** user_id, first_name, last_name, gender, level
* detailed user information including what membership they have
* Since the table is small, this data is broadcasted to all nodes to make joins faster. user_id is used as a sorting field.
**songs:** song_id, title, artist_id, year, duration
* detailed song information
* This table is large, so song_id is used as both a sorting key and a distribution key
**artists:** artist_id, name, location, lattitude, longitude
* detailed artist information
* This table is large, so artist_id is used as both a sorting key and a distribution key
**time:** start_time, hour, day, week, month, year, weekday
* detailed temporal breakdown regarding song_play time stamps
* This table is large, so start_time is used as both a sorting key and a distribution key

## ETL Pipeline
The ETL pipeline I built extracts the JSON song metadata and user activity logs and constructs the star schema described above. The process is as follows:
1. Set up a minimum 4 node Amazon redshift cluster
2. Set up staging tables and star schema tables in redshift
3. Set up a connection to the sparkify datawarehouse
4. Execute COPY command to populate staging tables
5. Execute INSERT queries to populate required data from stagin tables into star schema front office tables

This was done so that the only thing the analytics team needs to do to ensure the ETL script works is ensure the Software Engineering Team is sending logs and song metadata to Amazon S3. Since that is the existing structure, no changes are needed.


