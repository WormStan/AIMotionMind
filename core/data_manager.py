"""
数据管理模块
使用 pandas 管理和导出分析数据
"""
import pandas as pd
import json
import os
from typing import Dict, List


class DataManager:
    """数据管理器"""

    def __init__(self):
        """初始化数据管理器"""
        self.frames_df = None
        self.angles_df = None
        self.velocities_df = None
        self.keyframes_df = None

    def create_dataframes(self, analysis_results: Dict) -> Dict[str, pd.DataFrame]:
        """
        从分析结果创建数据表

        Args:
            analysis_results: 分析结果字典

        Returns:
            包含各种数据表的字典
        """
        frames = analysis_results["frames"]
        keyframes = analysis_results.get("keyframes", {})

        # 创建帧基本信息表
        frames_data = []
        for frame in frames:
            frame_info = {
                "frame_number": frame["frame_number"],
                "timestamp": frame["timestamp"],
                "pose_detected": frame["pose_detected"]
            }

            # 添加重心信息
            if frame.get("center_of_mass"):
                frame_info["com_x"] = frame["center_of_mass"]["x"]
                frame_info["com_y"] = frame["center_of_mass"]["y"]
                frame_info["com_height"] = frame.get("com_height", 0)

            # 添加投篮弧度
            if frame.get("shooting_arc") is not None:
                frame_info["shooting_arc"] = frame["shooting_arc"]

            frames_data.append(frame_info)

        self.frames_df = pd.DataFrame(frames_data)

        # 创建角度数据表
        angles_data = []
        for frame in frames:
            if frame.get("angles"):
                angle_row = {
                    "frame_number": frame["frame_number"],
                    "timestamp": frame["timestamp"]
                }
                angle_row.update(frame["angles"])
                angles_data.append(angle_row)

        self.angles_df = pd.DataFrame(
            angles_data) if angles_data else pd.DataFrame()

        # 创建速度数据表
        velocities_data = []
        for frame in frames:
            if frame.get("velocities"):
                vel_row = {
                    "frame_number": frame["frame_number"],
                    "timestamp": frame["timestamp"]
                }
                for joint, velocity in frame["velocities"].items():
                    vel_row[f"{joint}_velocity"] = velocity
                velocities_data.append(vel_row)

        self.velocities_df = pd.DataFrame(
            velocities_data) if velocities_data else pd.DataFrame()

        # 创建关键帧数据表
        keyframes_data = []
        for kf_name, kf_info in keyframes.items():
            kf_row = {
                "keyframe_name": kf_name,
                "description": kf_info.get("description", ""),
                "frame_number": kf_info["index"],
                "timestamp": kf_info["frame_data"]["timestamp"]
            }

            # 添加该关键帧的角度信息
            if kf_info["frame_data"].get("angles"):
                for angle_name, angle_value in kf_info["frame_data"]["angles"].items():
                    kf_row[angle_name] = angle_value

            keyframes_data.append(kf_row)

        self.keyframes_df = pd.DataFrame(
            keyframes_data) if keyframes_data else pd.DataFrame()

        return {
            "frames": self.frames_df,
            "angles": self.angles_df,
            "velocities": self.velocities_df,
            "keyframes": self.keyframes_df
        }

    def export_to_csv(self, output_dir: str):
        """
        导出数据到CSV文件

        Args:
            output_dir: 输出目录
        """
        os.makedirs(output_dir, exist_ok=True)

        if self.frames_df is not None:
            self.frames_df.to_csv(os.path.join(
                output_dir, "frames.csv"), index=False)

        if self.angles_df is not None and not self.angles_df.empty:
            self.angles_df.to_csv(os.path.join(
                output_dir, "angles.csv"), index=False)

        if self.velocities_df is not None and not self.velocities_df.empty:
            self.velocities_df.to_csv(os.path.join(
                output_dir, "velocities.csv"), index=False)

        if self.keyframes_df is not None and not self.keyframes_df.empty:
            self.keyframes_df.to_csv(os.path.join(
                output_dir, "keyframes.csv"), index=False)

        print(f"✓ 数据已导出到 CSV: {output_dir}")

    def export_to_json(self, analysis_results: Dict, output_path: str):
        """
        导出完整分析结果到JSON（用于HTML报表）

        Args:
            analysis_results: 分析结果字典
            output_path: 输出文件路径
        """
        # 准备JSON数据（去除图像数据）
        json_data = {
            "fps": analysis_results["fps"],
            "total_frames": analysis_results["total_frames"],
            "frames": [],
            "keyframes": {}
        }

        # 处理帧数据
        for frame in analysis_results["frames"]:
            frame_json = {
                "frame_number": frame["frame_number"],
                "timestamp": frame["timestamp"],
                "pose_detected": frame["pose_detected"],
                "angles": frame.get("angles", {}),
                "velocities": frame.get("velocities", {}),
                "accelerations": frame.get("accelerations", {}),
                "com_height": frame.get("com_height"),
                "shooting_arc": frame.get("shooting_arc")
            }

            # 添加关节位置（仅像素坐标）
            if frame.get("landmarks"):
                landmarks_simplified = {}
                for joint_name, joint_data in frame["landmarks"].items():
                    landmarks_simplified[joint_name] = {
                        "x": joint_data.get("x_pixel"),
                        "y": joint_data.get("y_pixel")
                    }
                frame_json["landmarks"] = landmarks_simplified

            json_data["frames"].append(frame_json)

        # 处理关键帧数据
        for kf_name, kf_info in analysis_results.get("keyframes", {}).items():
            json_data["keyframes"][kf_name] = {
                "index": kf_info["index"],
                "description": kf_info.get("description", ""),
                "timestamp": kf_info["frame_data"]["timestamp"],
                "angles": kf_info["frame_data"].get("angles", {}),
                "image_path": kf_info.get("image_path", "")
            }

        # 写入JSON文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 分析数据已导出到 JSON: {output_path}")

    def get_summary_statistics(self) -> Dict:
        """
        获取数据统计摘要

        Returns:
            统计摘要字典
        """
        summary = {}

        if self.angles_df is not None and not self.angles_df.empty:
            summary["angles"] = {}
            angle_columns = [col for col in self.angles_df.columns
                             if col not in ["frame_number", "timestamp"]]

            for col in angle_columns:
                summary["angles"][col] = {
                    "mean": float(self.angles_df[col].mean()),
                    "std": float(self.angles_df[col].std()),
                    "min": float(self.angles_df[col].min()),
                    "max": float(self.angles_df[col].max())
                }

        if self.velocities_df is not None and not self.velocities_df.empty:
            summary["velocities"] = {}
            vel_columns = [col for col in self.velocities_df.columns
                           if col not in ["frame_number", "timestamp"]]

            for col in vel_columns:
                summary["velocities"][col] = {
                    "mean": float(self.velocities_df[col].mean()),
                    "max": float(self.velocities_df[col].max())
                }

        return summary
