
## Step 1: Create new database.
```
CREATE DATABASE mooringlicensing_mig_dev;
CREATE USER mooringlicensing_mig_dev WITH PASSWORD '<password>';
GRANT ALL PRIVILEGES ON DATABASE "mooringlicensing_mig_dev" to mooringlicensing_mig_dev;
\c mooringlicensing_mig_dev
create extension postgis;
GRANT ALL ON ALL TABLES IN SCHEMA public TO mooringlicensing_mig_dev;
GRANT ALL ON SCHEMA public TO mooringlicensing_mig_dev;
```


## Step 2: apply patches
```
vi venv/lib/python3.12/site-packages/django/contrib/admin/migrations/0001_initial.py (see changes in patch_for_admin_0001_initial.patch)
vi venv/lib/python3.12/site-packages/reversion/migrations/0001_squashed_0004_auto_20160611_1202.py (see changes in patch_for_reversion_0001.patch)
```

## Step 3: Run Migrations
```
./manage_ml.py migrate auth
./manage_ml.py migrate ledger_api_client
./manage_ml.py migrate admin
./manage_ml.py migrate django_cron
./manage_ml.py migrate sites
./manage_ml.py migrate sessions
./manage_ml.py migrate 
```

## Step 4 Apply Fixutures
```
./manage_ml.py loaddata mooringlicensing/fixtures/ml_fixtures.json
 ```

## Step 5 Get moorings from mooring bookings

Add environment variables

MOORING_BOOKINGS_API_KEY= Mooring booking external API key

MOORING_BOOKINGS_API_URL= Mooring booking url

MOORING_GROUP_ID=1

```
./manage_ml.py import_mooring_bookings_data
```

## Step 6 Run Migration Clean Script

Add environment variables
LOTUS_NOTES_PATH = Location of unclean migration data   
MIGRATION_DATA_PATH = Output directory for cleaned migratrion data    
![image](https://github.com/user-attachments/assets/e113c018-cf50-447f-ac87-26134adafe3f)


```
python manage_ml.py import_lotus_notes
```
## Step 7 run migrations script
```
python ./manage_ml.py ml_migration_script --path ~/datamigration/outpath04122024/ >> ~/datamigration/outpath04122024/migration_run_08012024.log 2>&1

```
