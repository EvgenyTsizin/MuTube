import csv
from music21 import converter, midi
import argparse
import os

def convert_musicxml_to_csv(musicxml_path, csv_path):
    # Load the MusicXML file
    score = converter.parse(musicxml_path)
    
    # Convert the score to a MIDI file in memory
    mf = midi.translate.music21ObjectToMidiFile(score)
    
    # Get TPQN (ticks per quarter note)
    tpqn = mf.ticksPerQuarterNote
    
    # Prepare to track notes and events
    events = []
    ongoing_notes = {}  # Dictionary to track ongoing notes (keyed by pitch)
    current_tempo = 500000  # Default MIDI tempo (500,000 microseconds per quarter note)
    microseconds_per_tick = current_tempo / tpqn
    time_elapsed_ticks = 0  # Time elapsed in ticks since the start of the track

    # Process each track in the MIDI file
    for track in mf.tracks:
        for event in track.events:
            # Update elapsed time for all events
            if isinstance(event, midi.DeltaTime):
                time_elapsed_ticks += event.time

            if isinstance(event, midi.MidiEvent):
                # Handle tempo changes
                if event.type == "SET_TEMPO":
                    current_tempo = midi.translate.tempoEventToNumber(event)  # Extract microseconds per beat from the event
                    microseconds_per_tick = current_tempo / tpqn

                # Handle note-on events
                if event.isNoteOn() and event.velocity > 0:
                    # Note on: start tracking this note
                    pitch = event.pitch
                    ongoing_notes[pitch] = (time_elapsed_ticks, event.velocity)

                # Handle note-off events
                elif event.isNoteOff() or (event.isNoteOn() and event.velocity == 0):
                    # Note off: stop tracking this note and record its event
                    pitch = event.pitch
                    if pitch in ongoing_notes:
                        start_time_ticks, velocity = ongoing_notes[pitch]
                        duration_ticks = time_elapsed_ticks - start_time_ticks
                        # Convert ticks to seconds
                        start_time_seconds = (start_time_ticks * microseconds_per_tick) / 1_000_000
                        duration_seconds = (duration_ticks * microseconds_per_tick) / 1_000_000
                        events.append([start_time_seconds, duration_seconds, pitch, velocity, "piano"])
                        del ongoing_notes[pitch]

    # Write to CSV
    with open(csv_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Start', 'Duration', 'Pitch', 'Velocity', 'Instrument'])
        for event in sorted(events, key=lambda x: x[0]):  # Sort events by start time
            writer.writerow(event)
            
def main():

    parser = argparse.ArgumentParser(description="Convert MusicXML to CSV.")
    parser.add_argument('-i', '--input', required=True, help='Path to the input MusicXML file.')
    
    args = parser.parse_args()
    
    input_file = args.input
    
    # Compute the output file path
    if input_file.lower().endswith('.mxl'):
        output_file = input_file[:-4] + '.csv'
    elif input_file.lower().endswith('.musicxml'):
        output_file = input_file[:-9] + '.csv'
    else:
        raise ValueError("Input file must have a .mxl or .musicxml extension")

    convert_musicxml_to_csv(input_file, output_file)
    print(f"Conversion completed. CSV file saved at '{output_file}'.")

if __name__ == "__main__":
    main()
