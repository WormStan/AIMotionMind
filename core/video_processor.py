"""
视频处理模块
负责视频读取、帧提取、保存等操作
"""
import cv2
import os
from typing import List, Tuple, Optional
import numpy as np
from tqdm import tqdm


class VideoProcessor:
    """视频处理器"""

    def __init__(self, video_path: str):
        """
        初始化视频处理器

        Args:
            video_path: 视频文件路径
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        # 获取视频信息
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.frame_count / self.fps if self.fps > 0 else 0

    def get_video_info(self) -> dict:
        """
        获取视频信息

        Returns:
            包含视频信息的字典
        """
        return {
            "path": self.video_path,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "duration_formatted": f"{int(self.duration // 60)}:{int(self.duration % 60):02d}"
        }

    def extract_frames(self, frame_interval: int = 5, output_dir: Optional[str] = None) -> List[dict]:
        """
        按指定间隔提取视频帧

        Args:
            frame_interval: 帧间隔（每N帧提取一次）
            output_dir: 输出目录（如果提供，则保存帧图片）

        Returns:
            帧信息列表，每个元素包含帧号、时间戳、图像数据等
        """
        frames_data = []
        frame_idx = 0

        # 重置视频到开头
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # 创建输出目录
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        print(f"开始提取视频帧... (总帧数: {self.frame_count}, 间隔: {frame_interval})")

        with tqdm(total=self.frame_count, desc="提取帧") as pbar:
            while True:
                ret, frame = self.cap.read()

                if not ret:
                    break

                # 按间隔提取帧
                if frame_idx % frame_interval == 0:
                    timestamp = frame_idx / self.fps

                    frame_info = {
                        "frame_number": frame_idx,
                        "timestamp": timestamp,
                        "timestamp_formatted": f"{int(timestamp // 60):02d}:{timestamp % 60:06.3f}",
                        "image": frame.copy()
                    }

                    # 保存帧图片
                    if output_dir:
                        frame_filename = f"frame_{frame_idx:06d}.jpg"
                        frame_path = os.path.join(output_dir, frame_filename)
                        cv2.imwrite(frame_path, frame)
                        frame_info["image_path"] = frame_path

                    frames_data.append(frame_info)

                frame_idx += 1
                pbar.update(1)

        print(f"✓ 提取完成! 共提取 {len(frames_data)} 帧")
        return frames_data

    def get_frame_at_time(self, timestamp: float) -> Optional[np.ndarray]:
        """
        获取指定时间点的帧

        Args:
            timestamp: 时间戳（秒）

        Returns:
            帧图像数据，如果失败返回None
        """
        frame_number = int(timestamp * self.fps)
        return self.get_frame_at_index(frame_number)

    def get_frame_at_index(self, frame_number: int) -> Optional[np.ndarray]:
        """
        获取指定索引的帧

        Args:
            frame_number: 帧号

        Returns:
            帧图像数据，如果失败返回None
        """
        if frame_number < 0 or frame_number >= self.frame_count:
            return None

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        return frame if ret else None

    def save_frame(self, frame: np.ndarray, output_path: str):
        """
        保存帧图片

        Args:
            frame: 帧图像数据
            output_path: 输出路径
        """
        cv2.imwrite(output_path, frame)

    def resize_frame(self, frame: np.ndarray, width: Optional[int] = None,
                     height: Optional[int] = None) -> np.ndarray:
        """
        调整帧大小

        Args:
            frame: 帧图像数据
            width: 目标宽度
            height: 目标高度

        Returns:
            调整大小后的帧
        """
        if width is None and height is None:
            return frame

        if width is None:
            aspect_ratio = frame.shape[1] / frame.shape[0]
            width = int(height * aspect_ratio)
        elif height is None:
            aspect_ratio = frame.shape[0] / frame.shape[1]
            height = int(width * aspect_ratio)

        return cv2.resize(frame, (width, height))

    def copy_video_to_output(self, output_path: str):
        """
        复制视频文件到输出目录（用于HTML报表）

        Args:
            output_path: 输出路径
        """
        import shutil
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy2(self.video_path, output_path)
        print(f"✓ 视频已复制到: {output_path}")

    def __del__(self):
        """释放资源"""
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
