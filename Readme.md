# What is MuTube?

The project is enspired by [YouGlish](https://youglish.com/) just for musical notes (currently focused on piano). 

The idea is that the user can choose/photograph notes from some musical piece played by different performers,
and watch how different maestros played the selected notes. 

The site curently allows to chose notes - and the site provides youtube links to performing the notes, at times corresponding to the notes.

-----
# What is currently working?

This demo [site](https://evgenytsizin.github.io/MuTube/site/index.html) currently contains 3 musical pieces, it has notes for each: 

1. F.Liszt Dante Sonata S.161 No.7
2. Nocturne No. 20 in C Minor
3. Sonate No. 14 Moonlight 3rd Movement

# What the site about?

Each of the musical piece has its notes, upon clicking on the notes a window with several piano performers is linked to youtube at the specific time. 

# How it works? 

A special sync algorithm is used to synchronize the notes and the music.

===========================
# Technical 

# Batch Flow 

1. Batch flow starts from list of html pages with youtube embeds per query. 

You need to prepare file with queries (music pieces)
You will also need youtube api key 

run: 
```Tools/music_piece_searcher.py -f <search file> -k <youtube_api_key>```

*search file* - this is the file with search terms, each line is a search
*youtube_api_key* - youtube api key will need to work with google cloud services 
https://developers.google.com/youtube/registering_an_application

The run will create an array of html files *youtube_report_<index>.html* with 100 youtube, each html per search term. It will also create *youtube_report_<index>.json* with all youtube keys.

2. In this step the user chooses the youtubes he want to be present in the site.

2.1 Run local server in the htmls folder:
*python -m http.server 8000*

2.2 Open local link like this:
*http://localhost:8000/youtube_report_<index>.html*

This will allow to save json locally after you finish your work. 

2.3 Start your hand pick selection. Open each html file and select your youtubes marking them as *Good* using radio button. After you finish select in the end of the page *save ratings*.

3. Utility will run over all jsons created in step 1 and generate new json with all selected youtubes. 

The expected *youtubes.json* file will contain a list of tuples: 
(<search term (piece name>, [<list youtube keys>])

** TODO ** make this utility. There is no utility yet - because I didn't knew I need to use localhost. 

4. Download each musical piece .mxl format from https://musescore.com/ into same folder.

5. Now you will need to associete *youtube search* with *score sheet name*.

place the *youtubes.json* and all *name.mxl* files into same folder.  
run
```python Tools/attach_musicfile_to_name.py <folder>```

*folder* - pass the folder with all the mentioned data. 

The script will generate *youtube_with_notes.json* this file will have all the data for the next step.

6. Download all data needed from youtubes.

run
```python Tools/youtube_download_extract.py -i <youtube_with_notes.json>```

This script will download youtubes into the same folder as the input json 


# Old Flow 

## Stage1: Sync youtube with mxl. 

0. Start from mxl file and youtube videos in a subfolder <composition>: 

*file_with_links.txt* - file with youtube links line by line
*<composition>.mxl* - mxl of the composition

1. Extract youtube videos to mp3 and frames 

run:
```python synctoolbox/youtube_extract.py -i <file_with_links.txt>```

*output_folder* - a subfolder where the *file_with_links.txt* is located
*youtube_to_names.json* - a conversion from youtube_link to folder, json 

2. Extract *<composition>.mp3* from *<composition>.mxl*

*<composition>.mxl* Downloaded from musescore 

run:
```python synctoolbox/mxl_to_mp3.py -i <composition>.mxl```

*output* - will save .mp3 replacing mxl 

3. Convert all mp3 extracted from youtube to wav inside the subfolder <composition>: 
run 
```python synctoolbox/mp3_to_wav.py -i <composition>```

4. Sync <composition>.wav with wav files from youtube videos

run 
```python synctoolbox/sync_dir_wav.py -r <composition>.wav -d <youtube folder>```

*output* - in each folder with wav file added *audio_sync.json*

## Stage2: Extract images + timing from mxl. 

1. Remove tempo and generate images

run 
```python save_images.py -i <composition.mxl>```

this will generate images folder under the <composition.mxl> base folder. 

/Assumptions: musescore style exports single system per image (see documentation for how to setup). 

2. ocr 

run 
```cd ocr```
```python ocr_fodler.py -i <image folder>```

will be saved to <folder where>/ocr_results.json

3. Extract Measures and Crop images 

run 
```python extract_measures.py -i <composition folder>```

the utility assumes 
*images* - subfolder with images 
*ocr_results.json* - ocr result is in the folder

It will generate 
*cropped_images* - folder with croped images 
*island_locations.json* - with measure index and measure lines per image

## Stage3: Site data. 

1. Prepare all data for site and copy relevant data. 

*python copy_files_to_site.py -i <folder with composition> [-o site]*
 
2. Prepare *image_to_youtube_timing* in for page3.html 

run 
*python images_to_links.py -c <composition> [-o site]

This file unifies all data to generate youtube timings per image

## Stage4: Hand detect.

- run `detect_hands.ipynb` on server - change youtubes 
- download the Detects folder 
- run detects_to_json.py to generate json for hand detections
- run site/sort_by_hands.py
