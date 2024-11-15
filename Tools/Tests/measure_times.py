import os
import json
import music21
import bisect

def get_measure_times(mxl_path):
    score = None
    try:
        score = music21.converter.parse(mxl_path)
    except:
        # If not found, search for another file ending with .mxl
        mxl_path = next((os.path.join(os.path.dirname(mxl_path), f) for f in os.listdir(os.path.dirname(mxl_path)) if
                         f.endswith('.mxl')), None)

    if mxl_path is None:
        return None

    if score is None:
        try:
            score = music21.converter.parse(mxl_path)
        except:
            return None

    if score is None:
        return None

    measure_times = {}
    current_time = 0.0  # To track the total time considering repeats
    repeat_start_time = 0

    measure_index = -1

    for _ in score.parts[0].getElementsByClass('Measure'):
        measure_index += 1

    last_measure = measure_index

    measure_index = -1

    for measure in score.parts[0].getElementsByClass('Measure'):
        measure_index += 1

        measure_times[measure_index + 1] = current_time

        # Handle the repeats
        if measure.leftBarline and (
                    getattr(measure.leftBarline, 'style', None) == 'heavy-light' or getattr(measure.leftBarline, 'type',
                                                                                            None) == 'heavy-light'):

            # Repeat start - mark the time for the first repeat
            repeat_start_time = current_time
            print("repeat start time", repeat_start_time)

        # Increment the time by the duration of the current measure
        current_time += measure.duration.quarterLength

        if measure.rightBarline and (
                getattr(measure.rightBarline, 'style', None) == 'final' or getattr(measure.rightBarline, 'type',
                                                                                   None) == 'final'):

            if (repeat_start_time >= 0 and measure_index != last_measure) or repeat_start_time > 0:
                # Repeat end - add the duration of the repeated section
                repeat_duration = current_time - repeat_start_time

                print("repeat duration", repeat_duration)
                current_time += repeat_duration
                repeat_start_time = -1

    print("Successfully extracted", len(measure_times), "measures")
    return measure_times, current_time

def get_score_scale(score_data, first_audio_sync):
    json_last_timing = float(list(first_audio_sync.keys())[-1])
    score_last_timing = score_data[1]

    scale_factor = json_last_timing / score_last_timing
    if abs(scale_factor - 1) < 0.05:
        scale_factor = 1

    if abs(scale_factor - 0.5) < 0.05:
        scale_factor = 0.5

    return scale_factor


def find_youtube_time_for_measure(score_index, score_data, scale_factor, youtube_timings):
    score_time = score_data.get(score_index)

    if score_time is None:
        raise ValueError(f"Score index {score_index} not found in the score JSON data")

    # Scale the score time by the scale_factor
    scaled_time = float(score_time) * scale_factor

    # Convert youtube_timings to a list of floats for comparison
    youtube_timings_float = [(float(k), v) for k, v in youtube_timings.items()]

    # Find the insertion point for the scaled_time
    youtube_timings_float.sort()
    idx = bisect.bisect_left([yt[0] for yt in youtube_timings_float], scaled_time)

    # If the scaled_time is exactly one of the points
    if idx < len(youtube_timings_float) and youtube_timings_float[idx][0] == scaled_time:
        return youtube_timings_float[idx][1]

    # Get the timings just before and just after the scaled_time
    lower_timing, lower_value = youtube_timings_float[idx - 1] if idx > 0 else youtube_timings_float[0]
    higher_timing, higher_value = youtube_timings_float[idx] if idx < len(youtube_timings_float) else \
        youtube_timings_float[-1]

    # Linear interpolation
    if lower_timing == higher_timing:
        return lower_value
    else:
        proportion = (scaled_time - lower_timing) / (higher_timing - lower_timing)
        interpolated_time = lower_value + proportion * (higher_value - lower_value)
        return interpolated_time


def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


if __name__ == "__main__":
    # Hardcoded path for debugging
    mxl_path = '/media/simsim314/DATA/Github/music21/Pieces/youtubes/Franz Schubert - Impromptu in G-flat major, Op. 90, No. 3/Franz_Schubert_-_Impromptu_Op._90_No._3_in_G_Major_modified.musicxml'
    first_audio_sync_path = '/media/simsim314/DATA/Github/music21/Pieces/youtubes/Franz Schubert - Impromptu in G-flat major, Op. 90, No. 3/SCHUBERT - Impromptu n3 Horowitz/audio_sync.json'

    # Load first_audio_sync and calculate initial measure times without scaling
    measure_times = get_measure_times(mxl_path)
    score_data, total_time = measure_times

    if measure_times is not None:
        first_audio_sync = load_json_file(first_audio_sync_path)
        youtube_data = first_audio_sync
        scale_factor = get_score_scale(measure_times, first_audio_sync)
        print(f"Calculated scale factor: {scale_factor}")

        # Update measure times with the calculated scale factor
        print(f"Updated measure times with scale factor: {measure_times}")

        # Load YouTube timings and create mapping
        score_to_youtube = {}
        for idx in score_data.keys():
            youtube_time = find_youtube_time_for_measure(idx, score_data, scale_factor, youtube_data)
            score_to_youtube[int(idx)] = youtube_time

        for idx in list(score_data.keys())[:-1]:
            score_duration = scale_factor * (score_data[idx + 1] - score_data[idx])
            youtube_duration = score_to_youtube[idx + 1] - score_to_youtube[idx]

            print(idx, score_duration / youtube_duration)

        print(f"Score to YouTube mapping: {score_to_youtube}")
    else:
        print("Failed to extract measure times.")