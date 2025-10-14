"""
自定义配置示例
复制此文件并根据需要修改参数
"""

# 篮球投篮分析 - 高精度配置
HIGH_PRECISION_CONFIG = {
    "sport_type": "basketball_shot",
    "frame_interval": 2,  # 每2帧提取一次，提高精度

    "joints_of_interest": [
        "right_hip", "right_knee", "right_ankle",
        "right_shoulder", "right_elbow", "right_wrist", "right_index",
        "nose", "left_shoulder", "left_hip"
    ],

    "angle_metrics": [
        {"name": "knee_angle", "joints": [
            "right_hip", "right_knee", "right_ankle"], "description": "膝关节角度"},
        {"name": "hip_angle", "joints": [
            "right_shoulder", "right_hip", "right_knee"], "description": "髋关节角度"},
        {"name": "elbow_angle", "joints": [
            "right_shoulder", "right_elbow", "right_wrist"], "description": "肘关节角度"},
        {"name": "shoulder_angle", "joints": [
            "right_hip", "right_shoulder", "right_elbow"], "description": "肩关节角度"},
        {"name": "wrist_angle", "joints": [
            "right_elbow", "right_wrist", "right_index"], "description": "手腕角度"},
        {"name": "trunk_lean", "joints": [
            "nose", "right_hip", "right_knee"], "description": "躯干倾斜角度"}
    ],

    "keyframes": [
        {"name": "preparation", "display_name": "准备姿态（最低点）",
            "detection_method": "lowest_center_of_mass"},
        {"name": "ball_lift", "display_name": "抬球点",
            "detection_method": "wrist_acceleration_peak"},
        {"name": "set_point", "display_name": "定点（出手前）",
            "detection_method": "elbow_angle_max"},
        {"name": "release", "display_name": "出手点",
            "detection_method": "elbow_extension_max_velocity"},
        {"name": "follow_through", "display_name": "随球动作",
            "detection_method": "wrist_highest_point"}
    ],

    "mediapipe": {
        "model_complexity": 2,  # 最高精度
        "min_detection_confidence": 0.7,  # 更严格的检测
        "min_tracking_confidence": 0.7,
        "smooth_landmarks": True
    },

    "visualization": {
        "draw_skeleton": True,
        "skeleton_color": (0, 255, 0),
        "joint_color": (255, 0, 0),
        "line_thickness": 2,
        "joint_radius": 5
    }
}


# 篮球投篮分析 - 快速预览配置
FAST_PREVIEW_CONFIG = {
    "sport_type": "basketball_shot",
    "frame_interval": 10,  # 每10帧提取一次，快速处理

    "joints_of_interest": [
        "right_hip", "right_knee", "right_ankle",
        "right_shoulder", "right_elbow", "right_wrist"
    ],

    "angle_metrics": [
        {"name": "knee_angle", "joints": [
            "right_hip", "right_knee", "right_ankle"], "description": "膝关节角度"},
        {"name": "elbow_angle", "joints": [
            "right_shoulder", "right_elbow", "right_wrist"], "description": "肘关节角度"}
    ],

    "keyframes": [
        {"name": "preparation", "display_name": "准备姿态",
            "detection_method": "lowest_center_of_mass"},
        {"name": "release", "display_name": "出手点",
            "detection_method": "elbow_extension_max_velocity"}
    ],

    "mediapipe": {
        "model_complexity": 1,  # 中等精度
        "min_detection_confidence": 0.5,
        "min_tracking_confidence": 0.5,
        "smooth_landmarks": True
    },

    "visualization": {
        "draw_skeleton": True,
        "skeleton_color": (0, 255, 0),
        "joint_color": (255, 0, 0),
        "line_thickness": 2,
        "joint_radius": 5
    }
}


# 左侧投篮配置（镜像版本）
LEFT_SIDE_SHOT_CONFIG = {
    "sport_type": "basketball_shot",
    "frame_interval": 5,

    # 使用左侧关节点
    "joints_of_interest": [
        "left_hip", "left_knee", "left_ankle",
        "left_shoulder", "left_elbow", "left_wrist", "left_index",
        "nose", "right_shoulder", "right_hip"
    ],

    "angle_metrics": [
        {"name": "knee_angle", "joints": [
            "left_hip", "left_knee", "left_ankle"], "description": "膝关节角度"},
        {"name": "hip_angle", "joints": [
            "left_shoulder", "left_hip", "left_knee"], "description": "髋关节角度"},
        {"name": "elbow_angle", "joints": [
            "left_shoulder", "left_elbow", "left_wrist"], "description": "肘关节角度"},
        {"name": "shoulder_angle", "joints": [
            "left_hip", "left_shoulder", "left_elbow"], "description": "肩关节角度"},
        {"name": "wrist_angle", "joints": [
            "left_elbow", "left_wrist", "left_index"], "description": "手腕角度"},
        {"name": "trunk_lean", "joints": [
            "nose", "left_hip", "left_knee"], "description": "躯干倾斜角度"}
    ],

    "keyframes": [
        {"name": "preparation", "display_name": "准备姿态（最低点）",
            "detection_method": "lowest_center_of_mass"},
        {"name": "ball_lift", "display_name": "抬球点",
            "detection_method": "wrist_acceleration_peak"},
        {"name": "set_point", "display_name": "定点（出手前）",
            "detection_method": "elbow_angle_max"},
        {"name": "release", "display_name": "出手点",
            "detection_method": "elbow_extension_max_velocity"},
        {"name": "follow_through", "display_name": "随球动作",
            "detection_method": "wrist_highest_point"}
    ],

    "mediapipe": {
        "model_complexity": 2,
        "min_detection_confidence": 0.5,
        "min_tracking_confidence": 0.5,
        "smooth_landmarks": True
    },

    "visualization": {
        "draw_skeleton": True,
        "skeleton_color": (0, 255, 0),
        "joint_color": (255, 0, 0),
        "line_thickness": 2,
        "joint_radius": 5
    }
}


# 使用自定义配置的示例
def use_custom_config():
    """使用自定义配置进行分析"""
    from sports.basketball.shot_analyzer import BasketballShotAnalyzer

    # 选择配置
    config = HIGH_PRECISION_CONFIG  # 或 FAST_PREVIEW_CONFIG 或 LEFT_SIDE_SHOT_CONFIG

    # 创建分析器
    analyzer = BasketballShotAnalyzer(config=config)

    # 后续使用与默认配置相同
    # ...

    return analyzer


if __name__ == "__main__":
    print("配置示例文件")
    print("\n可用配置:")
    print("1. HIGH_PRECISION_CONFIG - 高精度配置（处理较慢）")
    print("2. FAST_PREVIEW_CONFIG - 快速预览配置（快速处理）")
    print("3. LEFT_SIDE_SHOT_CONFIG - 左侧投篮配置")
    print("\n在代码中导入并使用:")
    print("from config_examples import HIGH_PRECISION_CONFIG")
    print("analyzer = BasketballShotAnalyzer(config=HIGH_PRECISION_CONFIG)")
