import os
import sys
from datetime import timedelta
from faster_whisper import WhisperModel
import ffmpeg

class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

class Subtitles:
    delay = 0.3

    def group_text(self, segments, length):
        grouped = []
        weak_words = {
            "a", "an", "as", "at", "am", "be", "by", "do", "go", "he", "if", "in", "is", "it", "me", "my", "no", "of",
            "on", "or", "so", "the", "to", "up", "us", "we", "you", "and", "but", "are", "has", "had", "not", "was",
            "yet", "can", "may", "she", "his", "her", "did", "out", "too", "get", "got", "off", "our", "own", "let",
            "any", "all", "few"
        }

        current_group = []
        for i, segment in enumerate(segments):
            current_group.append(segment)

            # Check if we reached the desired length
            if len(current_group) >= length:
                # Check last word is weak (and not the only one)
                last_word = current_group[-1]['text'].strip(".,?!").lower()
                if last_word in weak_words and len(current_group) > 1:
                    carry = current_group.pop()
                    grouped.append(current_group)
                    current_group = [carry]
                else:
                    grouped.append(current_group)
                    current_group = []

        if current_group:
            grouped.append(current_group)

        return grouped


    def gen_srt(self, path, grouped):
        try:
            os.remove(path + ".srt")
        except OSError:
            pass

        with open(path + ".srt", "a", encoding="utf-8") as f:
            for i, group in enumerate(grouped):
                start = group[0]['start']
                end = group[-1]['end']
                start_td = timedelta(seconds=start)
                end_td = timedelta(seconds=end)

                start_str = f"{str(start_td).split('.')[0]},{int(start % 1 * 1000):03d}"
                end_str = f"{str(end_td).split('.')[0]},{int(end % 1 * 1000):03d}"
                text = " ".join([seg['text'] for seg in group]).strip()

                f.write(f"{i + 1}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{text}\n\n")

def transcribe(audio_path, model_size="small", device="cpu"):
    model = WhisperModel(model_size, device=device, compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)

    words = []
    for segment in segments:
        for word in segment.words:
            words.append({
                "text": word.word.strip(),
                "start": word.start,
                "end": word.end
            })
    return words

if __name__ == "__main__":
    audio_file = input("File path (audio or video): ")

    if not audio_file.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
        # extract audio from video
        print("Extracting audio...")
        audio_path = "temp_audio.wav"
        ffmpeg.input(audio_file).output(audio_path, ac=1, ar='16k').run(overwrite_output=True, quiet=True)
    else:
        audio_path = audio_file

    try:
        delay = float(input("No-sound delay (e.g., 0.3): "))
        max_words = int(input("Max words per subtitle (e.g., 10): "))
    except:
        print("Invalid input.")
        sys.exit(1)

    sub_gen = Subtitles()
    sub_gen.delay = delay

    print("Transcribing...")
    with HiddenPrints():
        words = transcribe(audio_path)

    print("Grouping...")
    grouped = sub_gen.group_text(words, max_words)

    print("Generating SRT...")
    sub_gen.gen_srt(os.path.splitext(audio_file)[0], grouped)

    if audio_path == "temp_audio.wav":
        os.remove(audio_path)

    print("✅ Done! SRT file created.")
