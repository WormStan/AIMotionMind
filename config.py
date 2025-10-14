"""
全局配置文件
"""
import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# 篮球投篮分析配置
BASKETBALL_SHOT_CONFIG = {
    "sport_type": "basketball_shot",
    "frame_interval": 5,  # 每5帧提取一次（可根据视频帧率调整）

    # 关注的关节点（右侧）
    "joints_of_interest": [
        "right_hip",
        "right_knee",
        "right_ankle",
        "right_shoulder",
        "right_elbow",
        "right_wrist",
        "right_index",  # 右手食指
        "nose",  # 鼻子（用于头部位置）
        "left_shoulder",  # 左肩（用于躯干计算）
        "left_hip"  # 左髋（用于躯干计算）
    ],

    # 需要计算的角度指标
    "angle_metrics": [
        {
            "name": "knee_angle",
            "joints": ["right_hip", "right_knee", "right_ankle"],
            "description": "膝关节角度"
        },
        {
            "name": "hip_angle",
            "joints": ["right_shoulder", "right_hip", "right_knee"],
            "description": "髋关节角度"
        },
        {
            "name": "elbow_angle",
            "joints": ["right_shoulder", "right_elbow", "right_wrist"],
            "description": "肘关节角度"
        },
        {
            "name": "shoulder_angle",
            "joints": ["right_hip", "right_shoulder", "right_elbow"],
            "description": "肩关节角度"
        },
        {
            "name": "wrist_angle",
            "joints": ["right_elbow", "right_wrist", "right_index"],
            "description": "手腕角度"
        },
        {
            "name": "trunk_lean",
            "joints": ["nose", "right_hip", "right_knee"],
            "description": "躯干倾斜角度"
        }
    ],

    # 关键帧检测配置
    "keyframes": [
        {
            "name": "squat_deepest",
            "display_name": "重心最低点（下蹲最深）",
            "detection_method": "lowest_center_of_mass"
        },
        {
            "name": "ball_lowest",
            "display_name": "球的最低点",
            "detection_method": "ball_position_lowest"
        },
        {
            "name": "lift_start",
            "display_name": "开始持续抬球",
            "detection_method": "ball_continuous_rise"
        },
        {
            "name": "ball_rising_mid",
            "display_name": "球上升中点",
            "detection_method": "midpoint_between_frames"
        },
        {
            "name": "ball_at_chest",
            "display_name": "球到胸部高度",
            "detection_method": "ball_at_chest_level"
        },
        {
            "name": "ball_at_shoulder",
            "display_name": "球到肩部高度",
            "detection_method": "ball_at_shoulder_level"
        },
        {
            "name": "elbow_max_bend",
            "display_name": "肘关节最大弯曲",
            "detection_method": "elbow_angle_minimum"
        },
        {
            "name": "elbow_extension_max",
            "display_name": "肘伸展最快",
            "detection_method": "elbow_angular_velocity_max"
        },
        {
            "name": "wrist_snap",
            "display_name": "手腕下压（snap）",
            "detection_method": "wrist_below_elbow_max"
        },
        {
            "name": "release_prepare",
            "display_name": "出手准备",
            "detection_method": "midpoint_between_frames"
        },
        {
            "name": "arm_full_extension",
            "display_name": "手臂完全伸直",
            "detection_method": "elbow_angle_near_180"
        },
        {
            "name": "leg_power_start",
            "display_name": "腿部开始发力",
            "detection_method": "knee_angle_inflection"
        },
        {
            "name": "power_transfer",
            "display_name": "力量传递",
            "detection_method": "midpoint_between_frames"
        },
        {
            "name": "release",
            "display_name": "出手瞬间",
            "detection_method": "multi_factor_scoring"
        },
        {
            "name": "follow_through",
            "display_name": "随球动作完成",
            "detection_method": "wrist_highest_point"
        }
    ],

    # MediaPipe 配置
    "mediapipe": {
        "model_complexity": 2,
        "min_detection_confidence": 0.5,
        "min_tracking_confidence": 0.5,
        "smooth_landmarks": True
    },

    # 可视化配置
    "visualization": {
        "draw_skeleton": True,
        "skeleton_color": (0, 255, 0),  # 绿色
        "joint_color": (255, 0, 0),  # 红色
        "line_thickness": 2,
        "joint_radius": 5
    }
}

# MediaPipe 关节点索引映射
MEDIAPIPE_POSE_LANDMARKS = {
    "nose": 0,
    "left_eye_inner": 1,
    "left_eye": 2,
    "left_eye_outer": 3,
    "right_eye_inner": 4,
    "right_eye": 5,
    "right_eye_outer": 6,
    "left_ear": 7,
    "right_ear": 8,
    "mouth_left": 9,
    "mouth_right": 10,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_pinky": 17,
    "right_pinky": 18,
    "left_index": 19,
    "right_index": 20,
    "left_thumb": 21,
    "right_thumb": 22,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_foot_index": 31,
    "right_foot_index": 32
}
