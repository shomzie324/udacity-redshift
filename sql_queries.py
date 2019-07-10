import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES
staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

# staging table cols need to match json props, no constraints to ensure all data is received as it stored
# data can be explored after loaded
staging_events_table_create= ("""
CREATE TABLE IF NOT EXISTS staging_events (
artist varchar,
auth varchar,
firstName varchar,
gender varchar,
itemInSession int,
lastName varchar,
length numeric,
level varchar,
location varchar,
method varchar,
page varchar, 
registration bigint,
sessionId int,
song varchar,
status int,
ts bigint,
userAgent varchar,
userId int
)
""")

staging_songs_table_create = ("""
CREATE TABLE IF NOT EXISTS staging_songs(
id bigint identity(0, 1),
num_songs int,
artist_id varchar,
artist_latitude numeric,
artist_longitude numeric,
artist_location varchar,
artist_name varchar,
song_id varchar,
title varchar,
duration numeric,
year int
)
""")

songplay_table_create = ("""
CREATE TABLE IF NOT EXISTS songplays
(songplay_id bigint identity(0, 1) PRIMARY KEY, start_time timestamp NOT NULL sortkey, user_id int NOT NULL, level varchar NOT NULL, song_id varchar distkey, artist_id varchar, session_id int NOT NULL, location varchar, user_agent varchar,
FOREIGN KEY (start_time) REFERENCES time(start_time),
FOREIGN KEY(user_id) REFERENCES users(user_id),
FOREIGN KEY(song_id) REFERENCES songs(song_id),
FOREIGN KEY(artist_id) REFERENCES artists(artist_id));
""")

user_table_create = ("""
CREATE TABLE IF NOT EXISTS users
(user_id int PRIMARY KEY sortkey, first_name varchar, last_name varchar, gender char NOT NULL, level varchar NOT NULL) diststyle all;
""")

song_table_create = ("""
CREATE TABLE IF NOT EXISTS songs
(song_id varchar PRIMARY KEY sortkey distkey, title varchar NOT NULL, artist_id varchar NOT NULL, year int, duration numeric NOT NULL);
""")

artist_table_create = ("""
CREATE TABLE IF NOT EXISTS artists
(artist_id varchar PRIMARY KEY sortkey distkey, name varchar NOT NULL, location varchar, lattitude numeric, longitude numeric);
""")

time_table_create = ("""
CREATE TABLE IF NOT EXISTS time
(start_time timestamp PRIMARY KEY sortkey distkey, hour int, day int, week int, month int, year int, weekday int);
""")


# STAGING TABLES INSERTS
# json path for log file maps specific json props to columns in table
staging_events_copy = ("""
COPY staging_events FROM '{}' 
CREDENTIALS 'aws_iam_role={}'
REGION 'us-west-2'
JSON '{}';
""").format(config.get("S3", "LOG_DATA"), config.get("IAM_ROLE", "ARN"), config.get("S3", "LOG_JSONPATH"))

# auto assumes all json props matches columns in table
staging_songs_copy = ("""
COPY staging_songs from '{}' 
CREDENTIALS 'aws_iam_role={}'
REGION 'us-west-2'
JSON 'auto' truncatecolumns
""").format(config.get("S3", "SONG_DATA"), config.get("IAM_ROLE", "ARN"))



# FINAL TABLE INSERTS

# use select queries for the insert statements
user_table_insert = ("""
INSERT INTO users
(
SELECT distinct userId, firstName, lastName, gender, level
FROM staging_events
WHERE page = 'NextSong'
);
""")

song_table_insert = ("""
INSERT INTO songs
(
SELECT distinct song_id, title, artist_id, year, duration
FROM staging_songs
WHERE SONG_ID IS NOT NULL
);
""")

artist_table_insert = ("""
INSERT INTO artists
(
SELECT distinct artist_id, artist_name,artist_location, artist_latitude, artist_longitude
FROM staging_songs
WHERE artist_id IS NOT NULL
);
""")

time_table_insert = ("""
INSERT INTO time
(
SELECT 
distinct TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second', 
EXTRACT(HOUR FROM TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second'), 
EXTRACT(DAY FROM TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second'),
EXTRACT(WEEK FROM TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second'),
EXTRACT(MONTH FROM TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second'),
EXTRACT(YEAR FROM TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second'),
EXTRACT(DOW FROM TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second')
FROM staging_events
WHERE page = 'NextSong'
);
""")

# join the staging tables on song title, artist name and song length since the logs have no song id
songplay_table_insert = ("""
INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
    SELECT events.start_time, events.userId, events.level, songs.song_id, songs.artist_id, events.sessionId, events.location, events.userAgent
    FROM (SELECT TIMESTAMP 'epoch' + ts/1000 * interval '1 second' AS start_time, *
          FROM staging_events
          WHERE page='NextSong') events
    LEFT JOIN staging_songs songs
    ON events.song = songs.title
    AND events.artist = songs.artist_name
    AND events.length = songs.duration
""")

# QUERY LISTS
# dimension tables need to be created before fact table
create_table_queries = [staging_events_table_create, staging_songs_table_create,user_table_create, song_table_create, artist_table_create, time_table_create, songplay_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
