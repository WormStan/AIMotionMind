"""
篮球投篮分析器
整合姿态检测和指标计算，进行投篮动作分析
"""
import numpy as np
from typing import List, Dict, Optional
import os
import cv2
from tqdm import tqdm

from core.pose_detector import PoseDetector
from sports.basketball.metrics import BasketballMetrics
from config import BASKETBALL_SHOT_CONFIG


class BasketballShotAnalyzer:
    """篮球投篮分析器"""

    def __init__(self, config: Dict = None):
        """
        初始化分析器

        Args:
            config: 配置字典，默认使用全局配置
        """
        self.config = config or BASKETBALL_SHOT_CONFIG

        # 初始化姿态检测器
        mp_config = self.config.get("mediapipe", {})
        self.pose_detector = PoseDetector(**mp_config)

        # 指标计算器
        self.metrics = BasketballMetrics()

        # 分析结果
        self.frames_data = []
        self.analysis_results = {}

    def analyze_frames(self, frames_data: List[Dict], fps: float) -> Dict:
        """
        分析提取的视频帧

        Args:
            frames_data: 帧数据列表（来自VideoProcessor）
            fps: 视频帧率

        Returns:
            分析结果字典
        """
        print(f"\n开始姿态分析... (共 {len(frames_data)} 帧)")

        analyzed_frames = []

        # 逐帧分析
        for frame_info in tqdm(frames_data, desc="姿态检测"):
            image = frame_info["image"]

            # 姿态检测
            pose_result = self.pose_detector.detect(image)

            if pose_result:
                # 计算关节角度
                landmarks = pose_result["landmarks"]
                angles = self.metrics.calculate_joint_angles(
                    landmarks,
                    self.config["angle_metrics"]
                )

                # 计算重心
                center_of_mass = self.metrics.calculate_center_of_mass(
                    landmarks)

                # 计算投篮弧度
                shooting_arc = self.metrics.calculate_shooting_arc(
                    landmarks.get("right_shoulder"),
                    landmarks.get("right_elbow"),
                    landmarks.get("right_wrist")
                )

                # 保存分析结果
                analyzed_frame = {
                    **frame_info,
                    "pose_detected": True,
                    "landmarks": landmarks,
                    "angles": angles,
                    "center_of_mass": center_of_mass,
                    "shooting_arc": shooting_arc,
                    "pose_result": pose_result
                }
            else:
                # 姿态检测失败
                analyzed_frame = {
                    **frame_info,
                    "pose_detected": False,
                    "landmarks": None,
                    "angles": {},
                    "center_of_mass": None,
                    "shooting_arc": None
                }

            analyzed_frames.append(analyzed_frame)

        self.frames_data = analyzed_frames

        # 计算时序数据（速度、加速度等）
        print("计算运动学指标...")
        self._calculate_temporal_metrics(fps)

        # 识别关键帧
        print("识别关键帧...")
        keyframes = self._detect_keyframes()

        # 计算动作节奏分析（从球最低点开始）
        print("计算动作节奏...")
        rhythm_analysis = self.metrics.calculate_rhythm_metrics(keyframes, fps)

        # 检测发力顺序（从球最低点开始）
        print("检测发力顺序...")
        force_sequence = self.metrics.detect_force_sequence(
            self.frames_data, fps, keyframes)

        # 计算能量传递效率（从球最低点到出手）
        print("计算能量传递效率...")
        energy_transfer = self.metrics.calculate_energy_transfer_efficiency(
            self.frames_data, keyframes)

        # 确定有效分析范围（从球最低点开始）
        ball_lowest_frame = keyframes.get('ball_lowest', {}).get('index', 0)
        release_frame = keyframes.get('release_point', {}).get(
            'index', len(self.frames_data) - 1)

        print(f"✓ 有效分析范围: 第{ball_lowest_frame}帧(球最低点) 到 第{release_frame}帧(出手)")

        # 保存标注图片
        print("生成标注图片...")
        self._generate_annotated_images()

        # 汇总分析结果
        self.analysis_results = {
            "frames": self.frames_data,
            "keyframes": keyframes,
            "rhythm_analysis": rhythm_analysis,
            "force_sequence": force_sequence,
            "energy_transfer": energy_transfer,
            "fps": fps,
            "total_frames": len(self.frames_data),
            "config": self.config,
            "analysis_range": {
                "start_frame": ball_lowest_frame,
                "end_frame": release_frame,
                "start_keyframe": "ball_lowest",
                "end_keyframe": "release_point",
                "valid_frames": release_frame - ball_lowest_frame + 1,
                "description": f"从球最低点(第{ball_lowest_frame}帧)到出手(第{release_frame}帧)"
            }
        }

        print("✓ 分析完成!")
        return self.analysis_results

    def _calculate_temporal_metrics(self, fps: float):
        """计算时序相关的指标（速度、加速度）"""
        # 提取各关节点的位置序列
        joints_of_interest = self.config["joints_of_interest"]

        for joint_name in joints_of_interest:
            positions = []
            for frame in self.frames_data:
                if frame["pose_detected"] and frame["landmarks"]:
                    positions.append(frame["landmarks"].get(joint_name))
                else:
                    positions.append(None)

            # 计算速度
            velocities = self.metrics.calculate_velocity(positions, fps)

            # 计算加速度
            accelerations = self.metrics.calculate_acceleration(
                velocities, fps)

            # 保存到各帧
            for i, frame in enumerate(self.frames_data):
                if "velocities" not in frame:
                    frame["velocities"] = {}
                if "accelerations" not in frame:
                    frame["accelerations"] = {}

                frame["velocities"][joint_name] = velocities[i]
                frame["accelerations"][joint_name] = accelerations[i]

        # 计算重心高度序列（用于检测最低点）
        com_heights = []
        for frame in self.frames_data:
            if frame.get("center_of_mass"):
                com_heights.append(frame["center_of_mass"]["y"])
            else:
                com_heights.append(0.0)

        # 保存重心高度
        for i, frame in enumerate(self.frames_data):
            frame["com_height"] = com_heights[i]

    def _detect_keyframes(self) -> Dict[str, Dict]:
        """检测关键帧"""
        from sports.basketball.keyframe_detector import KeyframeDetector

        keyframes = KeyframeDetector.detect_keyframes(self.frames_data)

        return keyframes

    def _generate_annotated_images(self):
        """为所有帧生成带标注的图片"""
        joints_to_draw = self.config["joints_of_interest"]

        for frame in self.frames_data:
            if frame["pose_detected"] and "pose_result" in frame:
                # 绘制骨架
                annotated_image = self.pose_detector.draw_custom_landmarks(
                    frame["image"],
                    frame["pose_result"],
                    joints_to_draw,
                    color=(0, 255, 0),
                    thickness=2,
                    radius=5
                )

                # 添加角度信息
                if frame.get("angles"):
                    y_offset = 30
                    for angle_name, angle_value in frame["angles"].items():
                        text = f"{angle_name}: {angle_value:.1f}°"
                        cv2.putText(
                            annotated_image,
                            text,
                            (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 0),
                            2
                        )
                        y_offset += 25

                frame["annotated_image"] = annotated_image

    def save_keyframe_images(self, output_dir: str, keyframes: Dict):
        """
        保存关键帧图片

        Args:
            output_dir: 输出目录
            keyframes: 关键帧字典
        """
        os.makedirs(output_dir, exist_ok=True)

        for keyframe_name, keyframe_info in keyframes.items():
            frame_data = keyframe_info["frame_data"]

            if "annotated_image" in frame_data:
                output_path = os.path.join(
                    output_dir, f"keyframe_{keyframe_name}.jpg")
                cv2.imwrite(output_path, frame_data["annotated_image"])
                keyframe_info["image_path"] = output_path

        print(f"✓ 关键帧图片已保存到: {output_dir}")
