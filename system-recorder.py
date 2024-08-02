import soundcard as sc
import soundfile as sf
import numpy as np

OUTPUT_FILE_NAME = "out.wav"
SAMPLE_RATE = 48000
RECORD_SEC = 5

def list_speakers():
    speakers = sc.all_speakers()
    print("Available speakers:")
    for i, speaker in enumerate(speakers):
        print(f"{i}: {speaker.name}")
    return speakers

def select_speaker(speakers):
    default_speaker = sc.default_speaker()
    default_index = next((i for i, s in enumerate(speakers) if s.name == default_speaker.name), None)
    
    if default_index is not None:
        print(f"Default speaker is: {default_speaker.name} (index {default_index})")
    else:
        print(f"Default speaker ({default_speaker.name}) is not in the list. It will be added.")
        speakers.append(default_speaker)
        default_index = len(speakers) - 1
        print(f"{default_index}: {default_speaker.name} (Default)")
    
    choice = input(f"Enter the number of the speaker you want to use (default is {default_index}): ")
    if choice.strip() == "":
        return speakers[default_index]
    try:
        choice = int(choice)
        if 0 <= choice < len(speakers):
            return speakers[choice]
        else:
            print("Invalid choice. Using default speaker.")
            return speakers[default_index]
    except ValueError:
        print("Invalid input. Using default speaker.")
        return speakers[default_index]

def record_audio(speaker):
    print(f"Recording from: {speaker.name}")
    print(f"Sample rate: {SAMPLE_RATE} Hz")
    print(f"Recording duration: {RECORD_SEC} seconds")
    
    mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
    with mic.recorder(samplerate=SAMPLE_RATE) as rec:
        print("Recording...")
        data = rec.record(numframes=SAMPLE_RATE * RECORD_SEC)
        print("Recording complete.")
    
    # Normalize audio data
    max_value = np.max(np.abs(data))
    if max_value > 0:
        data = data / max_value
    
    # Write to file
    sf.write(file=OUTPUT_FILE_NAME, data=data[:, 0], samplerate=SAMPLE_RATE)
    print(f"Audio saved as {OUTPUT_FILE_NAME}")

if __name__ == "__main__":
    speakers = list_speakers()
    selected_speaker = select_speaker(speakers)
    record_audio(selected_speaker)