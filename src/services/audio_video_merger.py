import os
import subprocess
import shlex

def normalize_path(path):
    """
    Chuẩn hóa đường dẫn để đảm bảo định dạng đúng.
    """
    return os.path.normpath(path)


def merge_audio_video(video_path, audio_path, output_path):
    """
    Ghép audio vào video bằng FFmpeg, tắt âm thanh gốc của video.
    """
    command = [
        "ffmpeg",
        "-y",  # Ghi đè file đầu ra nếu đã tồn tại
        "-i", video_path,  # Đầu vào video
        "-i", audio_path,  # Đầu vào audio
        "-c:v", "copy",  # Giữ nguyên codec video
        "-c:a", "aac",  # Sử dụng codec âm thanh AAC
        "-map", "0:v:0",  # Chỉ lấy video từ file gốc
        "-map", "1:a:0",  # Chỉ lấy audio từ file audio
        "-shortest",  # Dừng khi video hoặc audio kết thúc
        output_path
    ]
    try:
        result = subprocess.run(command, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print("FFmpeg Output:", result.stdout.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print("FFmpeg Error:", e.stderr.decode("utf-8"))
        raise Exception(f"Lỗi FFmpeg: {e.stderr.decode('utf-8')}")
# filepath: d:\python du an\2\text-to-audio\src\services\audio_video_merger.py
def escape_path_for_ffmpeg(path):
    """
    Escape đường dẫn để sử dụng trong FFmpeg.
    - Thay dấu `\` bằng `/` để đảm bảo tính nhất quán.
    - Bao bọc đường dẫn trong dấu nháy kép `"`.
    """
    path = os.path.normpath(path).replace("\\", "/")  # Thay \ bằng /
    return f'"{path}"'  # Bao bọc trong dấu nháy kép
def normalize_path(path):
    """
    Chuẩn hóa đường dẫn để loại bỏ khoảng trắng và ký tự đặc biệt.
    """
    # Thay thế khoảng trắng bằng dấu gạch dưới
    normalized_path = os.path.normpath(path).replace(" ", "_")
    # Đổi tên file nếu cần
    if path != normalized_path:
        os.rename(path, normalized_path)
    return normalized_path
def quote_path(path: str) -> str:
    """
    Escape đường dẫn cho phù hợp với FFmpeg trên Windows.
    """
    # FFmpeg yêu cầu escape dấu `\` trong filter như -vf "ass='C\\:\\\\path\\\\to\\\\file.ass'"
    path = path.replace('\\', '\\\\')        # Escape dấu \
    path = path.replace(':', '\\:')          # Escape dấu :
    return f"'{path}'"                       # Bọc trong dấu nháy đơn
def escape_path_for_ffmpeg_filter(path: str) -> str:
    """
    Escape đường dẫn để sử dụng trong filter -vf của FFmpeg.
    - Thay dấu `\` bằng `/` để đảm bảo tính nhất quán.
    - Escape dấu `:` thành `\\:`.
    - Bọc đường dẫn trong dấu nháy đơn `'`.
    """
    path = os.path.abspath(path).replace("\\", "/")  # Chuyển sang đường dẫn tuyệt đối và thay \ bằng /
    path = path.replace(":", "\\:")  # Escape dấu `:`
    return f"'{path}'"  # Bọc trong dấu nháy đơn
def escape_path_for_ffmpeg(path: str) -> str:
    """
    Escape đường dẫn để sử dụng trong FFmpeg.
    - Bọc đường dẫn trong dấu nháy kép `"`.
    """
    path = os.path.abspath(path).replace("\\", "/")  # Chuyển sang đường dẫn tuyệt đối và thay \ bằng /
    return f'"{path}"'  # Bọc trong dấu nháy kép



def escape_path_for_ffmpeg_filter(path: str) -> str:
    """
    Escape đường dẫn để sử dụng trong filter -vf của FFmpeg.
    - Thay dấu `\` bằng `/` để đảm bảo tính nhất quán.
    - Escape dấu `:` thành `\\:`.
    - Bọc đường dẫn trong dấu nháy đơn `'`.
    """
    path = os.path.abspath(path).replace("\\", "/")  # Chuyển sang đường dẫn tuyệt đối và thay \ bằng /
    path = path.replace(":", "\\:")  # Escape dấu `:`
    return f"'{path}'"  # Bọc trong dấu nháy đơn


def add_subtitle_with_ffmpeg(video_path: str, subtitle_path: str, output_path: str):
    """
    Chèn phụ đề ASS vào video bằng FFmpeg.
    """
    try:
        # Chuẩn hóa đường dẫn để tránh lỗi
        video_path = os.path.abspath(video_path).replace("\\", "/")
        subtitle_path = os.path.abspath(subtitle_path).replace("\\", "/").replace(":", "\\:")
        output_path = os.path.abspath(output_path).replace("\\", "/")

        # In đường dẫn để kiểm tra
        print(f"Video path: {video_path}")
        print(f"Subtitle path: {subtitle_path}")
        print(f"Output path: {output_path}")

        # Lệnh FFmpeg để chèn phụ đề
        command = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"ass='{subtitle_path}'",  # Escape dấu `:` và dùng nháy đơn
            "-c:v", "libx264",  # Mã hóa lại video bằng codec H.264
            "-preset", "fast",  # Tùy chọn preset để tối ưu tốc độ
            "-crf", "23",  # Chất lượng video (CRF 23 là mức cân bằng giữa chất lượng và kích thước file)
            "-c:a", "copy",  # Giữ nguyên codec audio
            output_path
        ]

        # Chạy lệnh FFmpeg
        subprocess.run(command, check=True)
        print(f"✅ Phụ đề đã được chèn vào video và lưu tại: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi chèn phụ đề vào video: {e}")
        raise Exception(f"Lỗi khi chèn phụ đề vào video: {e}")