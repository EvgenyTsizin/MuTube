import os
import numpy as np
import pandas as pd
import scipy.interpolate
import librosa
import json
import argparse
from libfmp.b import list_to_pitch_activations, plot_chromagram, plot_signal, plot_matrix, sonify_pitch_activations_with_signal
from synctoolbox.dtw.mrmsdtw import sync_via_mrmsdtw
from synctoolbox.dtw.utils import compute_optimal_chroma_shift, shift_chroma_vectors, make_path_strictly_monotonic
from synctoolbox.feature.csv_tools import read_csv_to_df, df_to_pitch_features, df_to_pitch_onset_features
from synctoolbox.feature.chroma import pitch_to_chroma, quantize_chroma, quantized_chroma_to_CENS
from synctoolbox.feature.dlnco import pitch_onset_features_to_DLNCO
from synctoolbox.feature.pitch import audio_to_pitch_features
from synctoolbox.feature.pitch_onset import audio_to_pitch_onset_features
from synctoolbox.feature.utils import estimate_tuning

def get_features_from_audio(audio, tuning_offset, Fs, feature_rate, visualize=True):
    f_pitch = audio_to_pitch_features(f_audio=audio, Fs=Fs, tuning_offset=tuning_offset, feature_rate=feature_rate, verbose=visualize)
    f_chroma = pitch_to_chroma(f_pitch=f_pitch)
    f_chroma_quantized = quantize_chroma(f_chroma=f_chroma)
    if visualize:
        plot_chromagram(f_chroma_quantized, title='Quantized chroma features - Audio', Fs=feature_rate, figsize=(9, 3))
    f_pitch_onset = audio_to_pitch_onset_features(f_audio=audio, Fs=Fs, tuning_offset=tuning_offset, verbose=visualize)
    f_DLNCO = pitch_onset_features_to_DLNCO(f_peaks=f_pitch_onset, feature_rate=feature_rate, feature_sequence_length=f_chroma_quantized.shape[1], visualize=visualize)
    return f_chroma_quantized, f_DLNCO

def get_features_from_annotation(df_annotation, feature_rate, visualize=True):
    f_pitch = df_to_pitch_features(df_annotation, feature_rate=feature_rate)
    f_chroma = pitch_to_chroma(f_pitch=f_pitch)
    f_chroma_quantized = quantize_chroma(f_chroma=f_chroma)
    if visualize:
        plot_chromagram(f_chroma_quantized, title='Quantized chroma features - Annotation', Fs=feature_rate, figsize=(9, 3))
    f_pitch_onset = df_to_pitch_onset_features(df_annotation)
    f_DLNCO = pitch_onset_features_to_DLNCO(f_peaks=f_pitch_onset, feature_rate=feature_rate, feature_sequence_length=f_chroma_quantized.shape[1], visualize=visualize)
    return f_chroma_quantized, f_DLNCO

def process_wav_file(wav_file, csv_file, feature_rate=50, step_weights=np.array([1.5, 1.5, 2.0]), threshold_rec=10**6):
    Fs = 22050
    output_dir = os.path.dirname(wav_file)
    audio, _ = librosa.load(wav_file, sr=Fs)
    df_annotation = read_csv_to_df(csv_file, csv_delimiter=';')
    tuning_offset = estimate_tuning(audio, Fs)
    print('Estimated tuning deviation for recording: %d cents' % (tuning_offset))

    f_chroma_quantized_audio, f_DLNCO_audio = get_features_from_audio(audio, tuning_offset, Fs, feature_rate, visualize=False)
    f_chroma_quantized_annotation, f_DLNCO_annotation = get_features_from_annotation(df_annotation, feature_rate, visualize=False)

    f_cens_1hz_audio = quantized_chroma_to_CENS(f_chroma_quantized_audio, 201, 50, feature_rate)[0]
    f_cens_1hz_annotation = quantized_chroma_to_CENS(f_chroma_quantized_annotation, 201, 50, feature_rate)[0]

    opt_chroma_shift = compute_optimal_chroma_shift(f_cens_1hz_audio, f_cens_1hz_annotation)
    print('Pitch shift between the audio recording and score, determined by DTW:', opt_chroma_shift, 'bins')

    f_chroma_quantized_annotation = shift_chroma_vectors(f_chroma_quantized_annotation, opt_chroma_shift)
    f_DLNCO_annotation = shift_chroma_vectors(f_DLNCO_annotation, opt_chroma_shift)

    wp = sync_via_mrmsdtw(f_chroma1=f_chroma_quantized_audio, 
                          f_onset1=f_DLNCO_audio, 
                          f_chroma2=f_chroma_quantized_annotation, 
                          f_onset2=f_DLNCO_annotation, 
                          input_feature_rate=feature_rate, 
                          step_weights=step_weights, 
                          threshold_rec=threshold_rec, 
                          verbose=False)
    print('Length of warping path obtained from MrMsDTW:', wp.shape[1])
    wp = make_path_strictly_monotonic(wp)

    annotation_to_audio_time_map = {}
    interpolated_starts = scipy.interpolate.interp1d(wp[1] / feature_rate, wp[0] / feature_rate, 
                                                     kind='linear', fill_value="extrapolate")(df_annotation['start'])

    for original_start, mapped_start in zip(df_annotation['start'], interpolated_starts):
        annotation_to_audio_time_map[original_start] = mapped_start

    output_path = os.path.join(output_dir, os.path.splitext(os.path.basename(wav_file))[0] + '_sync.json')
    with open(output_path, 'w') as json_file:
        json.dump(annotation_to_audio_time_map, json_file)
    print(f"Mapping dictionary saved to {output_path}")

def scan_wav_files(directory):
    wav_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.wav'):
                wav_files.append(os.path.join(root, file))
    return wav_files
    
def main():
    parser = argparse.ArgumentParser(description='Process wav files and generate sync json files.')
    parser.add_argument('-i', '--input', required=True, help='CSV file')
    parser.add_argument('-d', '--directory', required=True, help='Directory with wav files')
    
    args = parser.parse_args()
    csv_file = args.input
    wav_dir = args.directory

    if not os.path.exists(wav_dir):
        print(f"The directory {wav_dir} does not exist.")
        return
    
    wav_files = scan_wav_files(wav_dir)
    
    for wav_file in wav_files:
        print(wav_file)
        wav_file_path = os.path.join(wav_dir, wav_file)
        process_wav_file(wav_file_path, csv_file)
    
if __name__ == '__main__':
    main()
