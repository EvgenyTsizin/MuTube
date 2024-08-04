# Flow 

## Stage1: Sync youtube with mxl. 

0. Start from mxl file and youtube videos in a subfolder <composition>: 

*file_with_links.txt* - file with youtube links line by line
*<composition>.mxl* - mxl of the composition

1. Extract youtube videos to mp3 and frames 

run:
```synctoolbox/youtube_extract.py -i <file_with_links.txt>```

*output_folder* - a subfolder where the *file_with_links.txt* is located
*youtube_to_names.json* - a conversion from youtube_link to folder, json 

2. Extract *<composition>.csv* from *<composition>.mxl*

*<composition>.mxl* Downloaded from musescore 

run:
```python synctoolbox/musicxml_to_csv.py -i <composition>.mxl```

*output* - will save .csv replacing mxl 

3. Convert all mp3 extracted from youtube to wav inside the subfolder <composition>: 
run 
```synctoolbox/mp3_to_wav.py -i <composition>```

4. Sync <composition>.csv with wav files from youtube videos

run 
```python sync_dir.py -i <composition>.csv -d <youtube folder>```

*output* - in each folder with wav file added *audio_sync.json*

## Stage2: Extract images + timing from mxl. 

1. Remove tempo and generate images

run 
```save_images.py -i <composition.mxl>```

this will generate images folder under the <composition.mxl> base folder. 

/Assumptions: musescore style exports single system per image (see documentation for how to setup). 

2. ocr 

run 
```cd ocr```
```ocr_fodler.py -i <image folder>```

will be saved to <folder where>/ocr_results.json

3. Extract Measures and Crop images 

run 
```extarct_measures.py -i <composition folder>```

the utility assumes 
*images* - subfolder with images 
*ocr_results.json* - ocr result is in the folder

It will generate 
*cropped_images* - folder with croped images 
*island_locations.json* - with measure index and measure lines per image

## Stage3: Site data. 

1. Prepare all data for site and copy relevant data. 

*python copy_files_to_site.py -i <folder with composition> -o site*
 
2. Prepare *image_to_youtube_timing* in for page3.html 

run 
*python images_to_links.py -yn youtube_to_name.json -yt site/timings/<composition>/youtube_score_mappings -im site/images_metadata/<composition>.json -i site/images/<composition> -o site/timings/composition/<composition>_image_links.json*

This file unifies all data to generate youtube timings per image

## Stage4: Hand detect.

- run `detect_hands.ipynb` on server - change youtubes 
- download the Detects folder 
- run detects_to_json.py to generate json for hand detections
- run site/sort_by_hands.py