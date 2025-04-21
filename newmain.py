import os
import sys
import warnings
from datetime import timedelta
from faster_whisper import WhisperModel
import ffmpeg

warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

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

            if len(current_group) >= length:
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

    def gen_srt(self, path, grouped, words_to_color=0, color=None, font_size=None):
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

                # Only color if both are set
                if words_to_color > 0 and color:
                    word_entries = [{"word": seg["text"], "index": idx} for idx, seg in enumerate(group)]
                    word_entries.sort(key=lambda x: len(x["word"]), reverse=True)
                    colored_indices = set(entry["index"] for entry in word_entries[:words_to_color])
                else:
                    colored_indices = set()

                # Rebuild text with color and font
                words = []
                for idx, seg in enumerate(group):
                    word = seg["text"]
                    if idx in colored_indices:
                        word = f'<font color="{color}">{word}</font>'
                    words.append(word)

                line = " ".join(words).strip()
                if font_size:
                    line = f'<font size="{font_size}">{line}</font>'

                f.write(f"{i + 1}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{line}\n\n")

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
    if len(sys.argv) < 4:
        print("Usage: python newmain.py <file> <delay> <max_words> [words_to_color] [color] [font_size]")
        sys.exit(1)

    audio_file = sys.argv[1]
    delay = float(sys.argv[2])
    max_words = int(sys.argv[3])
    words_to_color = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    color = sys.argv[5] if len(sys.argv) > 5 else None
    font_size = int(sys.argv[6]) if len(sys.argv) > 6 else None

    if not audio_file.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
        audio_path = "temp_audio.wav"
        ffmpeg.input(audio_file).output(audio_path, ac=1, ar='16k').run(overwrite_output=True, quiet=True)
    else:
        audio_path = audio_file

    sub_gen = Subtitles()
    sub_gen.delay = delay

    with HiddenPrints():
        words = transcribe(audio_path)

    grouped = sub_gen.group_text(words, max_words)

    sub_gen.gen_srt(
        os.path.splitext(audio_file)[0],
        grouped,
        words_to_color=words_to_color,
        color=color,
        font_size=font_size
    )

    if audio_path == "temp_audio.wav":
        os.remove(audio_path)
