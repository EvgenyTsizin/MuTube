import os
import numpy as np
import json
import argparse
import librosa
import scipy.interpolate
from synctoolbox.dtw.mrmsdtw import sync_via_mrmsdtw
from synctoolbox.dtw.utils import compute_optimal_chroma_shift, shift_chroma_vectors, make_path_strictly_monotonic
from synctoolbox.feature.chroma import pitch_to_chroma, quantize_chroma, quantized_chroma_to_CENS
from synctoolbox.feature.dlnco import pitch_onset_features_to_DLNCO
from synctoolbox.feature.pitch import audio_to_pitch_features
from synctoolbox.feature.utils import estimate_tuning

def get_features_from_audio(audio, tuning_offset, Fs, feature_rate, visualize=True):
    f_pitch = audio_to_pitch_features(f_audio=audio, Fs=Fs, tuning_offset=tuning_offset, feature_rate=feature_rate, verbose=visualize)
    f_chroma = pitch_to_chroma(f_pitch=f_pitch)
    f_chroma_quantized = quantize_chroma(f_chroma=f_chroma)

    # Compute DLNCO features
    f_DLNCO = pitch_onset_features_to_DLNCO(f_peaks=f_pitch, feature_rate=feature_rate, feature_sequence_length=f_chroma_quantized.shape[1], visualize=visualize)
    
    return f_chroma_quantized, f_DLNCO

def process_wav_file(wav_file, ref_wav_file, output_file, feature_rate=50, step_weights=np.array([1.5, 1.5, 2.0]), threshold_rec=10**6):
    Fs = 22050
    
    audio, _ = librosa.load(wav_file, sr=Fs)
    ref_audio, _ = librosa.load(ref_wav_file, sr=Fs)
    
    tuning_offset = estimate_tuning(audio, Fs)
    ref_tuning_offset = estimate_tuning(ref_audio, Fs)
    
    print(f'Estimated tuning deviation for {os.path.basename(wav_file)}: {tuning_offset} cents')
    print(f'Estimated tuning deviation for reference recording: {ref_tuning_offset} cents')
    
    f_chroma_quantized, f_DLNCO = get_features_from_audio(audio, tuning_offset, Fs, feature_rate, visualize=False)
    f_chroma_quantized_ref, f_DLNCO_ref = get_features_from_audio(ref_audio, ref_tuning_offset, Fs, feature_rate, visualize=False)
    
    f_cens_1hz = quantized_chroma_to_CENS(f_chroma_quantized, 201, 50, feature_rate)[0]
    f_cens_1hz_ref = quantized_chroma_to_CENS(f_chroma_quantized_ref, 201, 50, feature_rate)[0]
    
    opt_chroma_shift = compute_optimal_chroma_shift(f_cens_1hz, f_cens_1hz_ref)
    print(f'Pitch shift between {os.path.basename(wav_file)} and reference recording, determined by DTW: {opt_chroma_shift} bins')
    
    f_chroma_quantized_ref = shift_chroma_vectors(f_chroma_quantized_ref, opt_chroma_shift)
    f_DLNCO_ref = shift_chroma_vectors(f_DLNCO_ref, opt_chroma_shift)
    
    wp = sync_via_mrmsdtw(f_chroma1=f_chroma_quantized, 
                          f_onset1=f_DLNCO, 
                          f_chroma2=f_chroma_quantized_ref, 
                          f_onset2=f_DLNCO_ref, 
                          input_feature_rate=feature_rate, 
                          step_weights=step_weights, 
                          threshold_rec=threshold_rec, 
                          verbose=False)
    
    print(f'Length of warping path obtained from MrMsDTW: {wp.shape[1]}')
    wp = make_path_strictly_monotonic(wp)
    
    # Correct mapping every 0.5 seconds in the reference audio
    time_intervals = np.arange(0, len(ref_audio) / Fs, 0.05)
    wp_time_ref = wp[1] / feature_rate
    wp_time_current = wp[0] / feature_rate
    
    interpolated_times = scipy.interpolate.interp1d(wp_time_ref, wp_time_current, 
                                                    kind='linear', fill_value="extrapolate")(time_intervals)

    audio_to_ref_time_map = {f"{t:.1f}": float(f"{mapped_t:.3f}") for t, mapped_t in zip(time_intervals, interpolated_times)}
    
    with open(output_file, 'w') as json_file:
        json.dump(audio_to_ref_time_map, json_file)
    print(f"Mapping dictionary saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Synchronize a wav file with a reference wav file and save the mapping.')
    parser.add_argument('-r', '--ref', required=True, help='Path to the reference wav file.')
    parser.add_argument('-s', '--sync', required=True, help='Path to the wav file to be synchronized.')
    parser.add_argument('-o', '--output', required=True, help='Path to the output JSON file.')
    
    args = parser.parse_args()

    if not os.path.exists(args.ref):
        print(f"The reference file {args.ref} does not exist.")
        return

    if not os.path.exists(args.sync):
        print(f"The sync file {args.sync} does not exist.")
        return

    process_wav_file(args.sync, args.ref, args.output)

if __name__ == '__main__':
    main()

