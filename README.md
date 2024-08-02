# MuTube

# Flow 

## Stage1: Sync youtube with mxl. 

0. Start from mxl file and youtube videos in a subfolder <composition>: 

*file_with_links.txt* - file with youtube links line by line
*<composition>.mxl* - mxl of the composition

1. Extract youtube videos to mp3 and frames 

run:
```synctoolbox/youtube_extract.py -i <file_with_links.txt>```

*output_folder* - a subfolder where the *file_with_links.txt* is located

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

**After you have run ocr you can continue to this code**

3. Run **mxl_to_svg.py** now with *report_measures* and extract measures location and indeces in each image.

output_directory = "output_directory2"
output_json = "island_locations.json"

report_measures(output_directory, output_json)

*It uses hardcoded inside a function:*

**r'output_directory2\ocr\all_results.json'**

## Stage3: Site data. 

1. Copy images generated previouslt to images folder. 

*crop_copy_dir.py*

-i <image folder> 
-o <output folder>
 
It will crop them. 

2. Extract measure score timing per index of measure. 

*mxl_timing.py*

-i <mxl file>
-o <json with index to time>
 
3. Now we need start time of each system image. 
Copy the 
*synctoolbox/F.Liszt_Dante_Sonata_S.161_No.7* into  *site/timing/F.Liszt_Dante_Sonata_S.161_No.7*

run *score_to_youtube_timing.py*

The flow: 

Measure index -> Measure timing -> CSV + timing -> Youtube Timing 
Image index -> Measure index -> Youtube Time in sec

4. Prepare image to youtube timing in for page3.html 

run 
**python images_to_links.py -yn F.Liszt_Dante_Sonata_S.161_No.7_youtube_to_name.json -yt site\timings\F.Liszt_Dante_Sonata_S.161_No.7\youtube_score_mappings -im site\images_metadata\F.Liszt_Dante_Sonata_S.161_No.7.json -i site\images\F.Liszt_Dante_Sonata_S.161_No.7 -o F.Liszt_Dante_Sonata_S.161_No.7_image_links.json**

This file unifies all data to generate youtube timings per image

## Stage4: Hand detect.

- run `detect_hands.ipynb` on server - change youtubes 
- download the Detects folder 
- run detects_to_json.py to generate json for hand detections
- run site/sort_by_hands.py