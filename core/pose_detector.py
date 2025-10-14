"""
姿态检测模块
使用 MediaPipe Pose 进行人体姿态检测
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List, Dict
from config import MEDIAPIPE_POSE_LANDMARKS


class PoseDetector:
    """姿态检测器"""

    def __init__(self, model_complexity: int = 2,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 smooth_landmarks: bool = True):
        """
        初始化姿态检测器

        Args:
            model_complexity: 模型复杂度 (0, 1, 2)，2为最高精度
            min_detection_confidence: 最小检测置信度
            min_tracking_confidence: 最小跟踪置信度
            smooth_landmarks: 是否平滑关节点
        """
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            smooth_landmarks=smooth_landmarks
        )

        self.landmark_names = MEDIAPIPE_POSE_LANDMARKS

    def detect(self, image: np.ndarray) -> Optional[Dict]:
        """
        检测图像中的人体姿态

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            检测结果字典，包含关节点信息；如果检测失败返回None
        """
        # 转换为RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 处理图像
        results = self.pose.process(image_rgb)

        if not results.pose_landmarks:
            return None

        # 提取关节点信息
        landmarks_dict = {}
        image_height, image_width = image.shape[:2]

        for name, idx in self.landmark_names.items():
            landmark = results.pose_landmarks.landmark[idx]
            landmarks_dict[name] = {
                "x": landmark.x,  # 归一化坐标 [0, 1]
                "y": landmark.y,
                "z": landmark.z,  # 深度（相对值）
                "visibility": landmark.visibility,  # 可见度 [0, 1]
                "x_pixel": int(landmark.x * image_width),  # 像素坐标
                "y_pixel": int(landmark.y * image_height)
            }

        return {
            "landmarks": landmarks_dict,
            "raw_landmarks": results.pose_landmarks,
            "image_width": image_width,
            "image_height": image_height
        }

    def draw_landmarks(self, image: np.ndarray, pose_results: Dict,
                       draw_connections: bool = True) -> np.ndarray:
        """
        在图像上绘制关节点和连接

        Args:
            image: 输入图像
            pose_results: 姿态检测结果
            draw_connections: 是否绘制骨架连接

        Returns:
            绘制后的图像
        """
        annotated_image = image.copy()

        if pose_results and "raw_landmarks" in pose_results:
            if draw_connections:
                # 绘制完整骨架
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    pose_results["raw_landmarks"],
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )
            else:
                # 只绘制关节点
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    pose_results["raw_landmarks"],
                    None,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )

        return annotated_image

    def draw_custom_landmarks(self, image: np.ndarray, pose_results: Dict,
                              joints_to_draw: List[str],
                              color: tuple = (0, 255, 0),
                              thickness: int = 2,
                              radius: int = 5) -> np.ndarray:
        """
        自定义绘制指定关节点

        Args:
            image: 输入图像
            pose_results: 姿态检测结果
            joints_to_draw: 要绘制的关节点名称列表
            color: 颜色 (B, G, R)
            thickness: 线条粗细
            radius: 关节点半径

        Returns:
            绘制后的图像
        """
        annotated_image = image.copy()

        if not pose_results or "landmarks" not in pose_results:
            return annotated_image

        landmarks = pose_results["landmarks"]

        # 绘制关节点
        for joint_name in joints_to_draw:
            if joint_name in landmarks:
                joint = landmarks[joint_name]
                if joint["visibility"] > 0.5:  # 只绘制可见度高的关节点
                    cv2.circle(
                        annotated_image,
                        (joint["x_pixel"], joint["y_pixel"]),
                        radius,
                        color,
                        -1
                    )
                    # 添加标签
                    cv2.putText(
                        annotated_image,
                        joint_name.replace("_", " ").title(),
                        (joint["x_pixel"] + 10, joint["y_pixel"] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        color,
                        1
                    )

        # 绘制连接线
        connections = [
            ("right_shoulder", "right_elbow"),
            ("right_elbow", "right_wrist"),
            ("right_wrist", "right_index"),
            ("right_shoulder", "right_hip"),
            ("right_hip", "right_knee"),
            ("right_knee", "right_ankle"),
            ("left_shoulder", "right_shoulder"),
            ("left_hip", "right_hip")
        ]

        for start_joint, end_joint in connections:
            if start_joint in landmarks and end_joint in landmarks:
                if (landmarks[start_joint]["visibility"] > 0.5 and
                        landmarks[end_joint]["visibility"] > 0.5):
                    start_point = (landmarks[start_joint]["x_pixel"],
                                   landmarks[start_joint]["y_pixel"])
                    end_point = (landmarks[end_joint]["x_pixel"],
                                 landmarks[end_joint]["y_pixel"])
                    cv2.line(annotated_image, start_point,
                             end_point, color, thickness)

        return annotated_image

    def get_joint_position(self, pose_results: Dict, joint_name: str) -> Optional[Dict]:
        """
        获取指定关节点的位置

        Args:
            pose_results: 姿态检测结果
            joint_name: 关节点名称

        Returns:
            关节点位置信息，如果不存在返回None
        """
        if not pose_results or "landmarks" not in pose_results:
            return None

        return pose_results["landmarks"].get(joint_name)

    def batch_detect(self, images: List[np.ndarray]) -> List[Optional[Dict]]:
        """
        批量检测多张图像

        Args:
            images: 图像列表

        Returns:
            检测结果列表
        """
        results = []
        for image in images:
            result = self.detect(image)
            results.append(result)
        return results

    def __del__(self):
        """释放资源"""
        if hasattr(self, 'pose'):
            self.pose.close()
