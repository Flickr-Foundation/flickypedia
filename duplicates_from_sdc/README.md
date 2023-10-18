# Finding duplicates in the structured data

When somebody uses Flickypedia, we want to check for duplicate Flickr pictures which already exist on Wikimedia Commons, and prevent the same file being uploaded twice.

It's unlikely that we can prevent all duplicates, but we can make some best-effort attempts to prevent unnecessary duplication.

One approach to spotting duplicates is to look for the Flickr photo URL in the structured data on existing Wikimedia Commons files ([example](https://commons.wikimedia.org/wiki/File:Gelnhausen,_Kaiserpfalz,_Ruine_des_Palas_%28http---www.flickr.com-photos-poly-image-6318576132-in-set-72157628058920966-%29_%288342633974%29.jpg)):

<img src="flickr_source_in_sdc.png" alt="Screenshot of a structured data statement on Wikimedia Commons. This is a 'source of file' statement for a file which is available on the Internet, with 'operator' Flickr and 'described at URL' a link back to the original Flickr image.">

Unfortunately knowing exactly what value to query for is tricky, because there are a number of forms that a Flickr URL could take in the structured data (e.g. with/without trailing slash, with user slug or numeric ID).

So instead, we use the [snapshots of Wikimedia Commons structured data](https://dumps.wikimedia.org/other/wikibase/commonswiki/).
We download a snapshot, then run a script which looks for instances of this structured data field -- and knows how to parse the many forms of Flickr URL.

It produces a mapping Flickr ID ↔ Wikimedia Commons file.

1.  Download the latest JSON snapshot from Wikimedia Commons.
    
    This file is large and will take several hours to download.
    This command will download the file, and can resume where you left off if the download is interrupted:
    
    ```
    curl \
      --location \
      --remote-name \
      --continue-at - \
      https://dumps.wikimedia.org/other/wikibase/commonswiki/20231009/commons-20231009-mediainfo.json.bz2    
    ```

2.  Run the script that finds the Flickr IDs in the snapshot:

    ```
    python3 find_flickr_ids_in_sdc_snapshot.py commons-20231009-mediainfo.json.bz2
    ```
    
    This will create a spreadsheet of IDs (e.g. `flickr_ids_from_sdc.20231009.csv`).
    
    ```csv
    flickr_photo_id,wikimedia_title,wikimedia_page_id
    3176098,File:Crocodile grin-scubadive67.jpg,M63606
    7267164,File:Rfid implant after.jpg,M87190
    9494179,File:Madrid Metro Sign.jpg,M137548
    ```
    
    Even on a fast computer, this may take several hours to complete.

    If there are any anomalous URLs in the snapshot, these will be logged in two separate files:
    
    -   `sdc_errors.txt` – any URLs in the structured data which couldn't be recognised as Flickr URLs
    -   `sdc_warnings.txt` – any Flickr URLs in the structured data which weren't a URL that points to a single photo

3.  Run the script that creates a SQLite database from the CSV:

    ```
    python3 csv_to_sqlite.py flickr_ids_from_sdc.20231009.csv
    ```
    
    This will create a SQLite database (e.g. `flickr_ids_from_sdc.20231009.sqlite`).
    You should copy this database into the environment where Flickypedia will be running.
    
    You can query this database to find where a particular Flickr photo has been used in Wikimedia Commons:
    
    ```console
    $ sqlite3 flickr_ids_from_sdc.20231009.sqlite
    SQLite version 3.39.5 2022-10-14 20:58:05
    Enter ".help" for usage hints.
    53230629852|File:2023.10.03 Womens Soccer Game -093.jpg|M138669374
    sqlite> SELECT * FROM flickr_photos_on_wikimedia
       ...> WHERE flickr_photo_id = 53230629852;
    53230629852|File:2023.10.03 Womens Soccer Game -093.jpg|M138669374
    ```
