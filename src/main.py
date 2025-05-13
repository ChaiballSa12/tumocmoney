import tkinter as tk
from tkinter import filedialog, messagebox
from services.transcription import generate_audio_from_transcript
from services.audio_video_merger import merge_audio_video, add_subtitle_with_ffmpeg
import os
import whisper
import pysubs2
import subprocess


def normalize_ass_file(input_ass, output_ass):
    """
    Chuẩn hóa file ASS để đảm bảo định dạng hợp lệ và áp dụng style mặc định.
    """
    try:
        # Load file ASS
        subs = pysubs2.load(input_ass, encoding="utf-8")
        
        # Áp dụng style mặc định cho tất cả các dòng phụ đề
        default_style = pysubs2.SSAStyle(
            fontname="Arial",  # Font chữ Arial
            fontsize=12,  # Kích thước chữ
            primarycolor=pysubs2.Color(255, 255, 255, 0),  # Màu trắng
            outlinecolor=pysubs2.Color(0, 0, 0, 255),  # Viền đen
            shadow=0.2,  # Không có bóng
            outline=1,  # Độ dày viền (2 là mức vừa phải)
            alignment=pysubs2.Alignment.TOP_CENTER,  # Căn giữa phía dưới
            marginv=20,  # Khoảng cách từ dưới lên
        )

        # Ghi đè style mặc định cho tất cả các style
        subs.styles["Default"] = default_style

        # Đảm bảo tất cả các dòng phụ đề sử dụng style "Default"
        for line in subs:
            line.style = "Default"

        # Lưu file ASS đã chỉnh sửa
        subs.save(output_ass)
        print(f"✅ File ASS đã được chuẩn hóa và lưu tại: {output_ass}")
    except Exception as e:
        print(f"❌ Lỗi khi chuẩn hóa file ASS: {e}")

def convert_srt_to_ass(srt_file, ass_file):
    """
    Chuyển đổi phụ đề từ SRT sang ASS, giữ nguyên thời gian hiển thị từ file SRT.
    """
    try:
        # Load file SRT
        subs = pysubs2.load(srt_file, encoding="utf-8")

        # Áp dụng style mặc định cho file ASS
        default_style = pysubs2.SSAStyle(
            fontname="Arial",  # Font chữ Arial
            fontsize=24,  # Kích thước chữ
            primarycolor=pysubs2.Color(255, 255, 255, 0),  # Màu trắng
            outlinecolor=pysubs2.Color(0, 0, 0, 255),  # Viền đen
            shadow=0,  # Không có bóng
            outline=2,  # Độ dày viền
            alignment=pysubs2.Alignment.BOTTOM_CENTER,  # Căn giữa phía dưới
            marginv=20,  # Khoảng cách từ dưới lên
        )

        # Ghi đè style mặc định
        subs.styles["Default"] = default_style

        # Đảm bảo tất cả các dòng phụ đề sử dụng style "Default"
        for line in subs:
            line.style = "Default"

        # Lưu file dưới định dạng ASS
        subs.save(ass_file)
        messagebox.showinfo("Thành công", f"File ASS đã được lưu tại: {ass_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi chuyển đổi: {e}")
def generate_srt_from_audio_or_video():
    """
    Hàm xử lý tạo file SRT từ file audio hoặc video bằng Whisper.
    """
    # Chọn file audio hoặc video
    input_file = filedialog.askopenfilename(
        title="Chọn file audio hoặc video",
        filetypes=[("Audio/Video files", "*.mp3;*.mp4;*.wav;*.mkv;*.avi")]
    )
    if not input_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn file audio hoặc video!")
        return

    # Chọn nơi lưu file SRT
    output_file = filedialog.asksaveasfilename(
        title="Lưu file SRT",
        defaultextension=".srt",
        filetypes=[("SRT Subtitle files", "*.srt")]
    )
    if not output_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn nơi lưu file SRT!")
        return

    # Gọi Whisper để tạo phụ đề
    try:
        model = whisper.load_model("base")  # Tải mô hình Whisper
        result = model.transcribe(input_file)
        with open(output_file, "w", encoding="utf-8") as srt_file:
            subtitle_id = 1
            for segment in result["segments"]:
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"].strip()

                # Tách câu dựa trên dấu chấm
                sentences = text.split(". ")
                sentence_start = start_time
                sentence_duration = (end_time - start_time) / len(sentences)

                for sentence in sentences:
                    if sentence.strip():  # Bỏ qua câu rỗng
                        sentence_end = sentence_start + sentence_duration
                        srt_file.write(f"{subtitle_id}\n")
                        srt_file.write(f"{format_time(sentence_start)} --> {format_time(sentence_end)}\n")
                        srt_file.write(f"{sentence.strip()}.\n\n")
                        subtitle_id += 1
                        sentence_start = sentence_end  # Cập nhật thời gian bắt đầu cho câu tiếp theo

        messagebox.showinfo("Thành công", f"File SRT đã được lưu tại: {output_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi tạo file SRT: {e}")
def format_time(seconds):
    """
    Chuyển đổi thời gian từ giây sang định dạng SRT (hh:mm:ss,ms).
    """
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
def process_transcript_to_audio():
    """
    Hàm xử lý chuyển đổi file TXT thành audio và lưu file audio.
    """
    # Lấy API Key
    api_key = api_key_entry.get().strip()
    if not api_key:
        messagebox.showwarning("Cảnh báo", "API Key không được để trống!")
        return

    # Chọn file TXT
    txt_file = filedialog.askopenfilename(
        title="Chọn file TXT",
        filetypes=[("Text files", "*.txt")]
    )
    if not txt_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn file TXT!")
        return

    # Đọc nội dung file TXT
    try:
        with open(txt_file, "r", encoding="utf-8") as file:
            transcript = file.read()
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc file TXT: {e}")
        return

    # Chọn nơi lưu file audio
    output_file = filedialog.asksaveasfilename(
        title="Lưu file audio",
        defaultextension=".mp3",
        filetypes=[("MP3 files", "*.mp3")]
    )
    if not output_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn nơi lưu file audio!")
        return

    # Gọi hàm chuyển đổi
    try:
        generate_audio_from_transcript(transcript, api_key, output_file)
        messagebox.showinfo("Thành công", f"File audio đã được lưu tại: {output_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi chuyển đổi: {e}")

def process_videos_and_audios():
    """
    Hàm xử lý ghép nối nhiều video trong thư mục, cắt video đã ghép theo độ dài audio,
    tắt tiếng video đã ghép, và ghép audio vào video đã tắt tiếng.
    """
    # Chọn thư mục chứa video
    video_folder = filedialog.askdirectory(
        title="Chọn thư mục chứa các file video"
    )
    if not video_folder:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn thư mục chứa video!")
        return

    # Chọn file audio
    audio_file = filedialog.askopenfilename(
        title="Chọn file audio",
        filetypes=[("Audio files", "*.mp3;*.wav")]
    )
    if not audio_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn file audio!")
        return

    # Chọn nơi lưu video đầu ra
    output_file = filedialog.asksaveasfilename(
        title="Lưu video đầu ra",
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if not output_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn nơi lưu video!")
        return

    try:
        # Bước 1: Ghép video
        merged_video = os.path.join(video_folder, "merged_video.mp4")
        merge_videos(video_folder, merged_video)

        # Bước 2: Lấy độ dài audio
        audio_duration_cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file
        ]
        audio_duration = float(subprocess.check_output(audio_duration_cmd).strip())

        # Bước 3: Cắt video đã ghép theo độ dài audio
        trimmed_video = os.path.join(video_folder, "trimmed_video.mp4")
        trim_cmd = [
            "ffmpeg", "-y", "-i", merged_video,
            "-t", str(audio_duration), "-c", "copy", trimmed_video
        ]
        subprocess.run(trim_cmd, check=True)

        # Bước 4: Tắt tiếng video đã cắt
        muted_video = os.path.join(video_folder, "muted_video.mp4")
        mute_video(trimmed_video, muted_video)

        # Bước 5: Ghép audio vào video đã tắt tiếng
        merge_audio_with_video(muted_video, audio_file, output_file)

        # Xóa file tạm
        for temp_file in [merged_video, trimmed_video, muted_video]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        messagebox.showinfo("Thành công", f"Video đã được xử lý và lưu tại: {output_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")
def add_subtitle_to_video():
    """
    Hàm xử lý chèn phụ đề vào video đã ghép, đồng thời tách phụ đề thành từng câu ngắn.
    """
    # Chọn video đã ghép
    video_file = filedialog.askopenfilename(
        title="Chọn video đã ghép",
        filetypes=[("Video files", "*.mp4;*.mkv;*.avi")]
    )
    if not video_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn video!")
        return

    # Chọn nơi lưu video đầu ra
    output_file = filedialog.asksaveasfilename(
        title="Lưu video đầu ra",
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if not output_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn nơi lưu video!")
        return

    # Tạo file SRT từ video bằng Whisper
    temp_srt_file = video_file.replace(".mp4", ".srt")
    MIN_SUBTITLE_DURATION = 0.1  # Thời gian tối thiểu cho mỗi phụ đề (giây)
    try:
        model = whisper.load_model("base")  # Tải mô hình Whisper
        result = model.transcribe(video_file)
        with open(temp_srt_file, "w", encoding="utf-8") as srt_file:
            subtitle_id = 1
            for segment in result["segments"]:
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"].strip()

                # Tách câu thành từng đoạn ngắn
                sentences = text.split(". ")  # Tách câu dựa trên dấu chấm
                sentence_start = start_time
                sentence_duration = max((end_time - start_time) / len(sentences), MIN_SUBTITLE_DURATION)

                for sentence in sentences:
                    if sentence.strip():  # Bỏ qua câu rỗng
                        sentence_end = sentence_start + sentence_duration
                        srt_file.write(f"{subtitle_id}\n")
                        srt_file.write(f"{format_time(sentence_start)} --> {format_time(sentence_end)}\n")
                        srt_file.write(f"{sentence.strip()}.\n\n")
                        subtitle_id += 1
                        sentence_start = sentence_end
        print(f"✅ File SRT đã được tạo tại: {temp_srt_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi tạo file SRT: {e}")
        return
    # Chuyển đổi SRT sang ASS
    temp_ass_file = video_file.replace(".mp4", ".ass")
    try:
        convert_srt_to_ass(temp_srt_file, temp_ass_file)  # Chuyển đổi SRT sang ASS
        print(f"✅ File ASS đã được lưu tại: {temp_ass_file}")

        # Chuẩn hóa file ASS
        normalize_ass_file(temp_ass_file, temp_ass_file)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi chuyển đổi SRT sang ASS: {e}")
        return
    finally:
        # Xóa file SRT tạm thời
        if os.path.exists(temp_srt_file):
            os.remove(temp_srt_file)

    # Chèn phụ đề vào video
    try:
        add_subtitle_with_ffmpeg(video_file, temp_ass_file, output_file)
        messagebox.showinfo("Thành công", f"Video đã được lưu tại: {output_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi chèn phụ đề: {e}")
def generate_ass_from_audio_or_video():
    """
    Tự động tạo file ASS từ file audio hoặc video.
    """
    # Chọn file audio hoặc video
    input_file = filedialog.askopenfilename(
        title="Chọn file audio hoặc video",
        filetypes=[("Audio/Video files", "*.mp3;*.mp4;*.wav;*.mkv;*.avi")]
    )
    if not input_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn file audio hoặc video!")
        return

    # Chọn nơi lưu file ASS
    output_file = filedialog.asksaveasfilename(
        title="Lưu file ASS",
        defaultextension=".ass",
        filetypes=[("ASS Subtitle files", "*.ass")]
    )
    if not output_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn nơi lưu file ASS!")
        return

    # Tạo file SRT tạm thời
    temp_srt_file = output_file.replace(".ass", ".srt")

    # Gọi Whisper để tạo phụ đề SRT
    try:
        model = whisper.load_model("base")  # Tải mô hình Whisper
        result = model.transcribe(input_file)
        with open(temp_srt_file, "w", encoding="utf-8") as srt_file:
            for segment in result["segments"]:
                start = format_time(segment["start"])
                end = format_time(segment["end"])
                text = segment["text"].strip()
                srt_file.write(f"{segment['id'] + 1}\n{start} --> {end}\n{text}\n\n")
        print(f"File SRT đã được tạo tại: {temp_srt_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi tạo file SRT: {e}")
        return

    # Chuyển đổi SRT sang ASS
    try:
        subs = pysubs2.load(temp_srt_file, encoding="utf-8")  # Load file SRT
        subs.save(output_file)  # Lưu file dưới định dạng ASS
        messagebox.showinfo("Thành công", f"File ASS đã được lưu tại: {output_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi chuyển đổi SRT sang ASS: {e}")
        return
    finally:
        # Xóa file SRT tạm thời
        if os.path.exists(temp_srt_file):
            os.remove(temp_srt_file)

def merge_videos(video_folder: str, output_path: str):
    """
    Cắt tất cả các video trong thư mục thành 5 giây (nếu cần) và ghép nối chúng thành một video duy nhất.
    """
    try:
        # Lấy danh sách các file video trong thư mục
        video_files = [os.path.join(video_folder, f) for f in os.listdir(video_folder) if f.endswith((".mp4", ".mkv", ".avi"))]
        if not video_files:
            raise Exception("Thư mục không chứa file video hợp lệ!")

        # Tạo thư mục tạm để lưu các video đã cắt
        temp_folder = os.path.join(video_folder, "temp_videos")
        os.makedirs(temp_folder, exist_ok=True)

        # Cắt từng video thành 5 giây nếu cần
        trimmed_videos = []
        for video_file in video_files:
            # Lấy độ dài video
            video_duration_cmd = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_file
            ]
            video_duration = float(subprocess.check_output(video_duration_cmd).strip())

            # Đường dẫn video đã cắt
            trimmed_video = os.path.join(temp_folder, os.path.basename(video_file))

            if video_duration > 5:
                # Cắt video thành 5 giây
                trim_cmd = [
                    "ffmpeg", "-y", "-i", video_file,
                    "-t", "5", "-c", "copy", trimmed_video
                ]
                subprocess.run(trim_cmd, check=True)
                print(f"✅ Video {video_file} đã được cắt thành 5 giây.")
            else:
                # Nếu video nhỏ hơn hoặc bằng 5 giây, sao chép video gốc
                trimmed_video = video_file
                print(f"✅ Video {video_file} nhỏ hơn hoặc bằng 5 giây, giữ nguyên.")

            trimmed_videos.append(trimmed_video)

        # Tạo danh sách file để ghép
        concat_list_file = os.path.join(temp_folder, "concat_list.txt")
        with open(concat_list_file, "w") as f:
            for trimmed_video in trimmed_videos:
                f.write(f"file '{trimmed_video.replace('\\', '/')}'\n")

        # Ghép video
        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_file,
            "-c", "copy", output_path
        ]
        subprocess.run(concat_cmd, check=True)

        print(f"✅ Video đã được ghép và lưu tại: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi xử lý video: {e}")
        raise Exception(f"Lỗi khi xử lý video: {e}")
    finally:
        # Xóa thư mục tạm
        if os.path.exists(temp_folder):
            for temp_file in os.listdir(temp_folder):
                os.remove(os.path.join(temp_folder, temp_file))
            os.rmdir(temp_folder)
def mute_video(input_path: str, output_path: str):
    """
    Tắt tiếng video.
    """
    try:
        mute_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-c:v", "copy", "-an", output_path
        ]
        subprocess.run(mute_cmd, check=True)
        print(f"✅ Video đã được tắt tiếng và lưu tại: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi tắt tiếng video: {e}")
        raise Exception(f"Lỗi khi tắt tiếng video: {e}")
def merge_audio_with_video(video_path: str, audio_path: str, output_path: str):
    """
    Ghép âm thanh từ file audio vào video đã tắt tiếng.
    """
    try:
        merge_cmd = [
            "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", output_path
        ]
        subprocess.run(merge_cmd, check=True)
        print(f"✅ Video đã được ghép audio và lưu tại: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi ghép audio vào video: {e}")
        raise Exception(f"Lỗi khi ghép audio vào video: {e}")
def merge_audio_with_videos(video_folder: str, audio_path: str, output_path: str):
    """
    Ghép nối các video trong thư mục cho đến khi tổng thời lượng lớn hơn thời lượng audio + 1 video,
    sau đó cắt video đã ghép theo thời lượng audio và ghép âm thanh vào video.
    """
    try:
        # Lấy danh sách các file video trong thư mục
        video_files = [os.path.join(video_folder, f) for f in os.listdir(video_folder) if f.endswith((".mp4", ".mkv", ".avi"))]
        if not video_files:
            raise Exception("Thư mục không chứa file video hợp lệ!")

        # Lấy độ dài audio
        audio_duration_cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ]
        audio_duration = float(subprocess.check_output(audio_duration_cmd).strip())

        # Ghép nối các video
        concat_list_file = os.path.join(video_folder, "concat_list.txt")
        total_video_duration = 0
        with open(concat_list_file, "w") as f:
            for video_file in video_files:
                # Lấy độ dài video
                video_duration_cmd = [
                    "ffprobe", "-v", "error", "-show_entries",
                    "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_file
                ]
                video_duration = float(subprocess.check_output(video_duration_cmd).strip())
                total_video_duration += video_duration

                # Thêm video vào danh sách ghép
                f.write(f"file '{video_file.replace('\\', '/')}'\n")

                # Nếu tổng thời lượng video lớn hơn thời lượng audio + 1 video, dừng thêm video
                if total_video_duration > audio_duration + video_duration:
                    break

        # Tạo video ghép nối
        concatenated_video = os.path.join(video_folder, "concatenated_video.mp4")
        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_file,
            "-c", "copy", concatenated_video
        ]
        subprocess.run(concat_cmd, check=True)

        # Cắt video ghép nối theo thời lượng audio
        trimmed_video = os.path.join(video_folder, "trimmed_video.mp4")
        trim_cmd = [
            "ffmpeg", "-y", "-i", concatenated_video,
            "-t", str(audio_duration), "-c", "copy", trimmed_video
        ]
        subprocess.run(trim_cmd, check=True)

        # Tắt tiếng video đã cắt
        muted_video = os.path.join(video_folder, "muted_video.mp4")
        mute_cmd = [
            "ffmpeg", "-y", "-i", trimmed_video,
            "-c:v", "copy", "-an", muted_video
        ]
        subprocess.run(mute_cmd, check=True)

        # Ghép audio vào video đã tắt tiếng
        merge_cmd = [
            "ffmpeg", "-y", "-i", muted_video, "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", output_path
        ]
        subprocess.run(merge_cmd, check=True)

        print(f"✅ Video đã được ghép audio và lưu tại: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi xử lý video hoặc audio: {e}")
        raise Exception(f"Lỗi khi xử lý video hoặc audio: {e}")
    finally:
        # Xóa các file tạm
        for temp_file in [concat_list_file, concatenated_video, trimmed_video, muted_video]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

def process_videos_and_audio():
    """
    Hàm xử lý ghép nối nhiều video trong thư mục và ghép audio vào video.
    """
    # Chọn thư mục chứa video
    video_folder = filedialog.askdirectory(
        title="Chọn thư mục chứa các file video"
    )
    if not video_folder:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn thư mục chứa video!")
        return

    # Chọn file audio
    audio_file = filedialog.askopenfilename(
        title="Chọn file audio",
        filetypes=[("Audio files", "*.mp3;*.wav")]
    )
    if not audio_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn file audio!")
        return

    # Chọn nơi lưu video đầu ra
    output_file = filedialog.asksaveasfilename(
        title="Lưu video đầu ra",
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if not output_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn nơi lưu video!")
        return

    # Gọi hàm xử lý
    try:
        merge_audio_with_videos(video_folder, audio_file, output_file)
        messagebox.showinfo("Thành công", f"Video đã được lưu tại: {output_file}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")
def main():
    """
    Hàm khởi chạy giao diện GUI.
    """
    root = tk.Tk()
    root.title("Bố Tú - Text to audio và chèn sub")

    # Nhãn và ô nhập API Key
    tk.Label(root, text="Nhập API Key (Evenlabs):").pack(pady=5)
    global api_key_entry
    api_key_entry = tk.Entry(root, width=50, show="*")
    api_key_entry.pack(pady=5)

    # Nút 1: Chuyển file TXT thành audio
    tk.Button(root, text="Chuyển file TXT thành audio", command=process_transcript_to_audio).pack(pady=10)

    # Nút 2: Ghép video với audio
    tk.Button(root, text="Ghép video với audio", command=process_videos_and_audios).pack(pady=10)

    # Nút 3: Chèn phụ đề vào video đã ghép
    tk.Button(root, text="Chèn phụ đề vào video đã ghép", command=add_subtitle_to_video).pack(pady=10)

    # Chạy giao diện
    root.mainloop()
def convert_srt_to_ass_gui():
    """
    Hàm xử lý chuyển đổi file SRT sang ASS thông qua giao diện.
    """
    # Chọn file SRT
    srt_file = filedialog.askopenfilename(
        title="Chọn file SRT",
        filetypes=[("SRT Subtitle files", "*.srt")]
    )
    if not srt_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn file SRT!")
        return

    # Chọn nơi lưu file ASS
    ass_file = filedialog.asksaveasfilename(
        title="Lưu file ASS",
        defaultextension=".ass",
        filetypes=[("ASS Subtitle files", "*.ass")]
    )
    if not ass_file:
        messagebox.showwarning("Cảnh báo", "Bạn chưa chọn nơi lưu file ASS!")
        return

    # Gọi hàm chuyển đổi
    convert_srt_to_ass(srt_file, ass_file)

if __name__ == "__main__":
    main()