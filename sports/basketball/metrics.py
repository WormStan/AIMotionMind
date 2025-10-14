"""
篮球投篮指标计算模块
计算角度、速度、加速度等运动学指标
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import math


class BasketballMetrics:
    """篮球投篮指标计算器"""

    @staticmethod
    def calculate_angle(point1: Dict, point2: Dict, point3: Dict) -> Optional[float]:
        """
        计算三个点形成的角度（point2为顶点）

        Args:
            point1, point2, point3: 关节点信息字典

        Returns:
            角度值（度数），如果计算失败返回None
        """
        if not all([point1, point2, point3]):
            return None

        # 提取坐标
        try:
            p1 = np.array([point1["x"], point1["y"]])
            p2 = np.array([point2["x"], point2["y"]])
            p3 = np.array([point3["x"], point3["y"]])
        except (KeyError, TypeError):
            return None

        # 计算向量
        vector1 = p1 - p2
        vector2 = p3 - p2

        # 计算角度
        cos_angle = np.dot(vector1, vector2) / \
            (np.linalg.norm(vector1) * np.linalg.norm(vector2) + 1e-6)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # 防止数值误差
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)

        return float(angle_deg)

    @staticmethod
    def calculate_velocity(positions: List[Dict], fps: float, smoothing: int = 3) -> List[float]:
        """
        计算关节点的速度

        Args:
            positions: 关节点位置列表（每帧的位置）
            fps: 视频帧率
            smoothing: 平滑窗口大小

        Returns:
            速度列表（像素/秒）
        """
        if len(positions) < 2:
            return [0.0] * len(positions)

        velocities = [0.0]  # 第一帧速度为0

        for i in range(1, len(positions)):
            if positions[i] and positions[i-1]:
                try:
                    dx = positions[i]["x_pixel"] - positions[i-1]["x_pixel"]
                    dy = positions[i]["y_pixel"] - positions[i-1]["y_pixel"]
                    distance = np.sqrt(dx**2 + dy**2)
                    velocity = distance * fps  # 像素/秒
                    velocities.append(velocity)
                except (KeyError, TypeError):
                    velocities.append(0.0)
            else:
                velocities.append(0.0)

        # 平滑处理
        if smoothing > 1:
            velocities = BasketballMetrics._smooth_data(
                velocities, window_size=smoothing)

        return velocities

    @staticmethod
    def calculate_acceleration(velocities: List[float], fps: float) -> List[float]:
        """
        计算加速度

        Args:
            velocities: 速度列表
            fps: 视频帧率

        Returns:
            加速度列表（像素/秒²）
        """
        if len(velocities) < 2:
            return [0.0] * len(velocities)

        accelerations = [0.0]  # 第一帧加速度为0

        for i in range(1, len(velocities)):
            dv = velocities[i] - velocities[i-1]
            acceleration = dv * fps
            accelerations.append(acceleration)

        return accelerations

    @staticmethod
    def calculate_center_of_mass(landmarks: Dict) -> Optional[Dict]:
        """
        计算重心位置（简化版，使用髋部中点）

        Args:
            landmarks: 关节点字典

        Returns:
            重心位置 {x, y, x_pixel, y_pixel}
        """
        try:
            left_hip = landmarks.get("left_hip")
            right_hip = landmarks.get("right_hip")

            if not left_hip or not right_hip:
                return None

            com = {
                "x": (left_hip["x"] + right_hip["x"]) / 2,
                "y": (left_hip["y"] + right_hip["y"]) / 2,
                "x_pixel": (left_hip["x_pixel"] + right_hip["x_pixel"]) // 2,
                "y_pixel": (left_hip["y_pixel"] + right_hip["y_pixel"]) // 2
            }

            return com
        except (KeyError, TypeError):
            return None

    @staticmethod
    def calculate_shooting_arc(shoulder: Dict, elbow: Dict, wrist: Dict) -> Optional[float]:
        """
        计算投篮弧度（手臂与水平面的夹角）

        Args:
            shoulder, elbow, wrist: 肩、肘、腕关节点

        Returns:
            弧度角度（度数）
        """
        if not all([shoulder, elbow, wrist]):
            return None

        try:
            # 使用腕关节和肘关节计算前臂角度
            dx = wrist["x"] - elbow["x"]
            dy = wrist["y"] - elbow["y"]

            # 计算与水平线的夹角
            angle_rad = math.atan2(-dy, dx)  # y轴向下为正，所以取负
            angle_deg = math.degrees(angle_rad)

            return float(angle_deg)
        except (KeyError, TypeError, ZeroDivisionError):
            return None

    @staticmethod
    def _smooth_data(data: List[float], window_size: int = 3) -> List[float]:
        """
        移动平均平滑

        Args:
            data: 数据列表
            window_size: 窗口大小

        Returns:
            平滑后的数据
        """
        if window_size < 2 or len(data) < window_size:
            return data

        smoothed = []
        half_window = window_size // 2

        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window + 1)
            smoothed.append(np.mean(data[start:end]))

        return smoothed

    @staticmethod
    def calculate_joint_angles(landmarks: Dict, angle_configs: List[Dict]) -> Dict[str, float]:
        """
        根据配置计算多个关节角度

        Args:
            landmarks: 关节点字典
            angle_configs: 角度配置列表

        Returns:
            角度字典 {angle_name: angle_value}
        """
        angles = {}

        for config in angle_configs:
            angle_name = config["name"]
            joint_names = config["joints"]

            if len(joint_names) != 3:
                continue

            points = [landmarks.get(joint_name) for joint_name in joint_names]
            angle = BasketballMetrics.calculate_angle(*points)

            angles[angle_name] = angle if angle is not None else 0.0

        return angles

    @staticmethod
    def detect_peaks(data: List[float], threshold: float = 0.0) -> List[int]:
        """
        检测峰值点

        Args:
            data: 数据列表
            threshold: 阈值

        Returns:
            峰值点的索引列表
        """
        peaks = []

        for i in range(1, len(data) - 1):
            if data[i] > data[i-1] and data[i] > data[i+1] and data[i] > threshold:
                peaks.append(i)

        return peaks

    @staticmethod
    def detect_valleys(data: List[float], threshold: float = float('inf')) -> List[int]:
        """
        检测谷值点（最低点）

        Args:
            data: 数据列表
            threshold: 阈值

        Returns:
            谷值点的索引列表
        """
        valleys = []

        for i in range(1, len(data) - 1):
            if data[i] < data[i-1] and data[i] < data[i+1] and data[i] < threshold:
                valleys.append(i)

        return valleys

    @staticmethod
    def find_global_minimum(data: List[float]) -> int:
        """
        找到全局最小值的索引

        Args:
            data: 数据列表

        Returns:
            最小值索引
        """
        if not data:
            return -1
        return int(np.argmin(data))

    @staticmethod
    def find_global_maximum(data: List[float]) -> int:
        """
        找到全局最大值的索引

        Args:
            data: 数据列表

        Returns:
            最大值索引
        """
        if not data:
            return -1
        return int(np.argmax(data))

    @staticmethod
    def calculate_rhythm_metrics(keyframes: Dict[str, Dict], fps: float) -> Dict:
        """
        计算动作节奏指标

        分析关键帧之间的时间间隔、动作流畅度等

        Args:
            keyframes: 关键帧字典 {keyframe_name: {index, timestamp, ...}}
            fps: 视频帧率

        Returns:
            节奏分析结果字典
        """
        if not keyframes:
            return {}

        # 按时间顺序排序关键帧
        sorted_keyframes = sorted(
            keyframes.items(),
            key=lambda x: x[1].get('index', 0)
        )

        # 计算各阶段的时间间隔
        phase_durations = {}
        phase_intervals = []

        for i in range(len(sorted_keyframes) - 1):
            current_name, current_kf = sorted_keyframes[i]
            next_name, next_kf = sorted_keyframes[i + 1]

            current_frame = current_kf.get('index', 0)
            next_frame = next_kf.get('index', 0)

            duration_frames = next_frame - current_frame
            duration_seconds = duration_frames / fps if fps > 0 else 0

            phase_name = f"{current_name}_to_{next_name}"
            phase_durations[phase_name] = {
                'frames': duration_frames,
                'seconds': duration_seconds,
                'from_frame': current_frame,
                'to_frame': next_frame
            }

            phase_intervals.append(duration_seconds)

        # 计算总时长
        if sorted_keyframes:
            first_frame = sorted_keyframes[0][1].get('index', 0)
            last_frame = sorted_keyframes[-1][1].get('index', 0)
            total_duration = (last_frame - first_frame) / fps if fps > 0 else 0
        else:
            total_duration = 0

        # 计算节奏一致性（时间间隔的变异系数）
        if phase_intervals and len(phase_intervals) > 1:
            rhythm_consistency = np.std(
                phase_intervals) / (np.mean(phase_intervals) + 1e-6)
        else:
            rhythm_consistency = 0.0

        # 识别关键阶段的时长（从球最低点开始）
        key_phases = {}

        ball_lowest_kf = keyframes.get('ball_lowest')
        squat_kf = keyframes.get('squat_deepest')
        release_kf = keyframes.get('release_point')
        followthrough_kf = keyframes.get('follow_through')

        # 预备阶段：从球最低点到下蹲最深
        if ball_lowest_kf and squat_kf:
            prep_duration = (squat_kf['index'] - ball_lowest_kf['index']) / fps
            key_phases['preparation'] = prep_duration

        # 发力阶段：从下蹲最深到出手瞬间
        if squat_kf and release_kf:
            power_duration = (release_kf['index'] - squat_kf['index']) / fps
            key_phases['power_phase'] = power_duration

        # 跟随阶段：从出手瞬间到随球完成
        if release_kf and followthrough_kf:
            follow_duration = (
                followthrough_kf['index'] - release_kf['index']) / fps
            key_phases['follow_through'] = follow_duration

        # 计算从球最低点开始的总时长
        shooting_duration = 0
        if ball_lowest_kf and sorted_keyframes:
            ball_lowest_frame = ball_lowest_kf.get('index', 0)
            last_frame = sorted_keyframes[-1][1].get('index', 0)
            shooting_duration = (
                last_frame - ball_lowest_frame) / fps if fps > 0 else 0

        return {
            'phase_durations': phase_durations,
            'total_duration': total_duration,
            'shooting_duration': shooting_duration,  # 从球最低点开始的投篮时长
            'rhythm_consistency': float(rhythm_consistency),
            'key_phases': key_phases,
            'phase_count': len(phase_durations),
            'avg_phase_duration': np.mean(phase_intervals) if phase_intervals else 0.0,
            'analysis_start': 'ball_lowest' if ball_lowest_kf else 'first_keyframe'
        }

    @staticmethod
    def detect_force_sequence(frames_data: List[Dict], fps: float, keyframes: Dict = None) -> Dict:
        """
        检测关节运动启动顺序

        从球最低点开始，检测哪些关节最先开始显著运动
        不强制自下而上的严格顺序，而是分析实际的运动启动模式

        Args:
            frames_data: 帧数据列表
            fps: 视频帧率
            keyframes: 关键帧字典（用于获取球最低点）

        Returns:
            关节运动启动顺序分析结果
        """
        # 定义需要监测的关节
        monitored_joints = [
            'right_ankle',
            'right_knee',
            'right_hip',
            'right_shoulder',
            'right_elbow',
            'right_wrist'
        ]

        # 确定分析起始帧（球最低点）
        start_frame = 0
        if keyframes and 'ball_lowest' in keyframes:
            start_frame = keyframes['ball_lowest'].get('index', 0)

        # 确定分析结束帧（出手瞬间或最后一帧）
        end_frame = len(frames_data)
        if keyframes and 'release_point' in keyframes:
            end_frame = keyframes['release_point'].get(
                'index', len(frames_data))

        # 定义"显著运动"的速度阈值（像素/帧）
        # 改用加速度来检测运动启动：当加速度首次显著增加时
        movement_threshold = 20.0  # 速度阈值
        acceleration_threshold = 50.0  # 加速度阈值

        # 检测每个关节的首次显著运动时刻
        # 策略：检测速度从相对静止状态开始显著增加的时刻
        initiation_times = {}

        for joint in monitored_joints:
            velocities = []
            for i in range(start_frame, min(end_frame, len(frames_data))):
                frame = frames_data[i]
                if frame.get('pose_detected') and 'velocities' in frame:
                    vel = frame['velocities'].get(joint, 0.0)
                    velocities.append((i, vel))
                else:
                    velocities.append((i, 0.0))

            if len(velocities) < 3:
                continue

            # 方法1：寻找速度的快速上升阶段（速度导数，即加速度）
            # 计算速度变化率
            for idx in range(1, len(velocities) - 1):
                frame_idx, current_vel = velocities[idx]
                prev_frame_idx, prev_vel = velocities[idx - 1]

                # 计算速度增量（加速度的近似）
                vel_increase = current_vel - prev_vel

                # 如果速度显著增加（加速），且当前速度超过基本阈值
                if vel_increase >= acceleration_threshold and current_vel >= movement_threshold:
                    initiation_times[joint] = {
                        'frame': frame_idx,
                        'time': frame_idx / fps if fps > 0 else 0,
                        'velocity': current_vel,
                        'acceleration': vel_increase
                    }
                    break  # 找到首次显著加速，停止搜索该关节

            # 如果没有找到显著加速，使用备用方案：找速度峰值的前一段
            if joint not in initiation_times and velocities:
                # 找到速度峰值
                max_vel_idx = max(range(len(velocities)),
                                  key=lambda i: velocities[i][1])
                max_vel_frame, max_vel = velocities[max_vel_idx]

                # 从峰值往前找，找到速度开始明显上升的点
                # （速度达到峰值的30%的时刻）
                threshold_vel = max_vel * 0.3

                for idx in range(max_vel_idx):
                    frame_idx, vel = velocities[idx]
                    if vel >= threshold_vel:
                        initiation_times[joint] = {
                            'frame': frame_idx,
                            'time': frame_idx / fps if fps > 0 else 0,
                            'velocity': vel,
                            'acceleration': 0.0  # 备用方案，没有加速度数据
                        }
                        break

        # 按启动时间排序，得到实际的运动启动顺序
        if initiation_times:
            sorted_joints = sorted(
                initiation_times.items(),
                key=lambda x: x[1]['frame']
            )
            actual_sequence = [joint for joint, _ in sorted_joints]
        else:
            actual_sequence = []

        # 分析运动启动模式
        pattern_analysis = BasketballMetrics._analyze_movement_pattern(
            initiation_times, monitored_joints
        )

        # 分析关键关节对的启动顺序
        joint_pairs_analysis = BasketballMetrics._analyze_joint_pairs(
            initiation_times, fps
        )

        # 计算相邻关节的启动时间差（保留用于兼容性）
        time_intervals = []
        if len(actual_sequence) >= 2:
            for i in range(len(actual_sequence) - 1):
                current_joint = actual_sequence[i]
                next_joint = actual_sequence[i + 1]

                current_time = initiation_times[current_joint]['frame']
                next_time = initiation_times[next_joint]['frame']

                time_diff = (next_time - current_time) / fps if fps > 0 else 0
                time_intervals.append({
                    'from': current_joint,
                    'to': next_joint,
                    'time_diff_seconds': time_diff,
                    'frame_diff': next_time - current_time
                })

        return {
            'initiation_times': initiation_times,
            'actual_sequence': actual_sequence,
            'time_intervals': time_intervals,
            'pattern_analysis': pattern_analysis,
            'joint_pairs_analysis': joint_pairs_analysis,
            'movement_threshold': movement_threshold,
            'monitored_joints': monitored_joints,
            'analysis_range': {
                'start_frame': start_frame,
                'end_frame': end_frame,
                'start_keyframe': 'ball_lowest' if keyframes and 'ball_lowest' in keyframes else 'first_frame'
            }
        }

    @staticmethod
    def _analyze_joint_pairs(initiation_times: Dict, fps: float) -> Dict:
        """
        分析关键关节对的启动顺序

        关注三对关节：
        1. 手腕 vs 肘部
        2. 肘部 vs 肩部
        3. 髋部 vs 膝盖

        Args:
            initiation_times: 各关节的启动时间
            fps: 帧率

        Returns:
            关节对分析结果
        """
        pairs_result = []

        # 定义三对关键关节
        key_pairs = [
            {
                'name': '手腕-肘部',
                'joint1': 'right_wrist',
                'joint1_cn': '手腕',
                'joint2': 'right_elbow',
                'joint2_cn': '肘部',
                'category': 'upper_arm'
            },
            {
                'name': '肘部-肩部',
                'joint1': 'right_elbow',
                'joint1_cn': '肘部',
                'joint2': 'right_shoulder',
                'joint2_cn': '肩部',
                'category': 'upper_arm'
            },
            {
                'name': '髋部-膝盖',
                'joint1': 'right_hip',
                'joint1_cn': '髋部',
                'joint2': 'right_knee',
                'joint2_cn': '膝盖',
                'category': 'lower_leg'
            }
        ]

        for pair in key_pairs:
            j1 = pair['joint1']
            j2 = pair['joint2']

            if j1 in initiation_times and j2 in initiation_times:
                frame1 = initiation_times[j1]['frame']
                frame2 = initiation_times[j2]['frame']

                frame_diff = frame2 - frame1
                time_diff = frame_diff / fps if fps > 0 else 0

                # 判断谁先启动
                if frame_diff > 0:
                    first = pair['joint1_cn']
                    sequence = f"{pair['joint1_cn']} → {pair['joint2_cn']}"
                elif frame_diff < 0:
                    first = pair['joint2_cn']
                    sequence = f"{pair['joint2_cn']} → {pair['joint1_cn']}"
                else:
                    first = "同时"
                    sequence = f"{pair['joint1_cn']} ≈ {pair['joint2_cn']}"

                pairs_result.append({
                    'pair_name': pair['name'],
                    'joint1': pair['joint1'],
                    'joint1_cn': pair['joint1_cn'],
                    'joint2': pair['joint2'],
                    'joint2_cn': pair['joint2_cn'],
                    'joint1_frame': frame1,
                    'joint2_frame': frame2,
                    'frame_diff': frame_diff,
                    'time_diff_seconds': time_diff,
                    'first_to_move': first,
                    'sequence': sequence,
                    'category': pair['category']
                })
            else:
                # 数据缺失
                pairs_result.append({
                    'pair_name': pair['name'],
                    'joint1': pair['joint1'],
                    'joint1_cn': pair['joint1_cn'],
                    'joint2': pair['joint2'],
                    'joint2_cn': pair['joint2_cn'],
                    'joint1_frame': None,
                    'joint2_frame': None,
                    'frame_diff': None,
                    'time_diff_seconds': None,
                    'first_to_move': '未检测',
                    'sequence': '数据缺失',
                    'category': pair['category']
                })

        return {
            'pairs': pairs_result,
            'summary': BasketballMetrics._generate_pairs_summary(pairs_result)
        }

    @staticmethod
    def _generate_pairs_summary(pairs_result: List[Dict]) -> str:
        """生成关节对分析摘要"""
        summary_parts = []

        for pair in pairs_result:
            if pair['first_to_move'] != '未检测':
                summary_parts.append(
                    f"{pair['pair_name']}: {pair['first_to_move']}先动 "
                    f"(时间差 {abs(pair['frame_diff'])}帧)"
                )

        return '; '.join(summary_parts) if summary_parts else '数据不完整'

    @staticmethod
    def _analyze_movement_pattern(initiation_times: Dict, monitored_joints: List[str]) -> Dict:
        """
        分析关节运动启动模式

        聚焦于三个关键部位的启动顺序：
        1. 下肢（脚踝、膝盖）
        2. 髋部
        3. 上肢（肩部、肘部、手腕）

        Args:
            initiation_times: 各关节的启动时间
            monitored_joints: 监测的关节列表

        Returns:
            模式分析结果
        """
        # 定义三个关键部位
        lower_joints = ['right_ankle', 'right_knee']
        hip_joint = 'right_hip'
        upper_joints = ['right_shoulder', 'right_elbow', 'right_wrist']

        # 获取各部位的首次启动帧
        lower_frames = [
            initiation_times[j]['frame'] for j in lower_joints if j in initiation_times
        ]
        hip_frame = initiation_times.get(hip_joint, {}).get('frame', None)
        upper_frames = [
            initiation_times[j]['frame'] for j in upper_joints if j in initiation_times
        ]

        # 如果任何部位没有数据，返回不完整
        if not lower_frames or hip_frame is None or not upper_frames:
            return {
                'pattern_type': 'incomplete_data',
                'description': '数据不完整，无法判断运动模式',
                'key_parts': {
                    'lower': None,
                    'hip': None,
                    'upper': None
                }
            }

        # 计算各部位的代表性启动时间（取最早的）
        lower_start = min(lower_frames)
        hip_start = hip_frame
        upper_start = min(upper_frames)

        # 判断三者的启动顺序
        parts_timing = [
            ('lower', lower_start),
            ('hip', hip_start),
            ('upper', upper_start)
        ]
        # 按时间排序
        parts_timing.sort(key=lambda x: x[1])

        # 获取启动顺序
        initiation_order = [part[0] for part in parts_timing]

        # 计算时间差
        time_diffs = {
            'hip_vs_lower': hip_start - lower_start,
            'upper_vs_hip': upper_start - hip_start,
            'upper_vs_lower': upper_start - lower_start
        }

        # 判断模式类型
        if initiation_order == ['lower', 'hip', 'upper']:
            # 理想顺序：下肢 → 髋部 → 上肢
            pattern_type = 'lower_hip_upper'
            description = '下肢 → 髋部 → 上肢'
        elif initiation_order[0] == 'hip':
            # 髋部先启动
            if initiation_order == ['hip', 'lower', 'upper']:
                pattern_type = 'hip_lower_upper'
                description = '髋部 → 下肢 → 上肢'
            elif initiation_order == ['hip', 'upper', 'lower']:
                pattern_type = 'hip_upper_lower'
                description = '髋部 → 上肢 → 下肢'
            else:
                pattern_type = 'hip_first'
                description = '髋部主导发力'
        elif initiation_order[0] == 'lower':
            # 下肢先启动
            if abs(time_diffs['upper_vs_lower']) <= 2:
                # 如果上下肢时间差很小（≤2帧）
                pattern_type = 'lower_synchronized'
                description = '下肢启动，上下肢协同发力'
            else:
                pattern_type = 'lower_first'
                description = '下肢主导发力'
        elif initiation_order[0] == 'upper':
            # 上肢先启动
            pattern_type = 'upper_first'
            description = '上肢先启动'
        else:
            pattern_type = 'unknown'
            description = '运动模式无法分类'

        return {
            'pattern_type': pattern_type,
            'description': description,
            'initiation_order': initiation_order,
            'key_parts': {
                'lower': lower_start,
                'hip': hip_start,
                'upper': upper_start
            },
            'time_differences': time_diffs,
            'summary': f"{initiation_order[0]} → {initiation_order[1]} → {initiation_order[2]}"
        }

    @staticmethod
    def calculate_energy_transfer_efficiency(frames_data: List[Dict], keyframes: Dict) -> Dict:
        """
        计算能量传递效率

        分析：
        1. 下肢是否产生了初始动能
        2. 上肢是否获得了加速（力量传递的证据）
        3. 整体协调性（速度峰值的时间顺序）

        Args:
            frames_data: 帧数据列表
            keyframes: 关键帧字典

        Returns:
            能量传递分析结果
        """
        # 定义下肢关节和上肢关节
        lower_body_joints = ['right_ankle', 'right_knee', 'right_hip']
        upper_body_joints = ['right_shoulder', 'right_elbow', 'right_wrist']

        # 获取分析阶段的帧范围（从球最低点到出手）
        ball_lowest_kf = keyframes.get('ball_lowest', {})
        release_kf = keyframes.get('release_point', {})

        # 优先使用球最低点作为起始帧
        start_frame = ball_lowest_kf.get('index', 0)
        end_frame = release_kf.get('index', len(frames_data) - 1)

        if start_frame >= end_frame:
            return {
                'lower_body_peak_velocity': 0.0,
                'upper_body_peak_velocity': 0.0,
                'velocity_ratio': 0.0,
                'transfer_timing': 'unknown',
                'lower_peak_frame': 0,
                'upper_peak_frame': 0,
                'timing_difference': 0,
                'analysis_range': {
                    'start_frame': start_frame,
                    'end_frame': end_frame,
                    'start_keyframe': 'ball_lowest'
                }
            }

        # 收集下肢和上肢的速度数据
        lower_body_velocities = []
        upper_body_velocities = []

        for i in range(start_frame, min(end_frame + 1, len(frames_data))):
            frame = frames_data[i]
            if frame.get('pose_detected') and 'velocities' in frame:
                # 下肢平均速度
                lower_vels = [frame['velocities'].get(
                    joint, 0.0) for joint in lower_body_joints]
                valid_lower = [v for v in lower_vels if v > 0]
                lower_body_velocities.append(
                    np.mean(valid_lower) if valid_lower else 0.0)

                # 上肢平均速度
                upper_vels = [frame['velocities'].get(
                    joint, 0.0) for joint in upper_body_joints]
                valid_upper = [v for v in upper_vels if v > 0]
                upper_body_velocities.append(
                    np.mean(valid_upper) if valid_upper else 0.0)

        if not lower_body_velocities or not upper_body_velocities:
            return {
                'lower_body_peak_velocity': 0.0,
                'upper_body_peak_velocity': 0.0,
                'velocity_ratio': 0.0,
                'transfer_timing': 'unknown',
                'lower_peak_frame': 0,
                'upper_peak_frame': 0,
                'timing_difference': 0,
                'analysis_range': {
                    'start_frame': start_frame,
                    'end_frame': end_frame,
                    'start_keyframe': 'ball_lowest'
                }
            }

        # 找到速度峰值
        lower_peak_velocity = max(lower_body_velocities)
        upper_peak_velocity = max(upper_body_velocities)

        lower_peak_idx = np.argmax(lower_body_velocities)
        upper_peak_idx = np.argmax(upper_body_velocities)

        lower_peak_frame = start_frame + lower_peak_idx
        upper_peak_frame = start_frame + upper_peak_idx

        timing_difference = upper_peak_frame - lower_peak_frame

        # 分析传递时序
        if timing_difference > 3:
            # 上肢峰值明显晚于下肢（正常的力量传递链）
            transfer_timing = 'sequential'
        elif timing_difference >= 0:
            # 上肢峰值稍晚或同时
            transfer_timing = 'synchronized'
        else:
            # 上肢峰值早于下肢
            transfer_timing = 'reversed'

        # 计算速度放大比（上肢相对于下肢的加速效果）
        velocity_ratio = upper_peak_velocity / \
            lower_peak_velocity if lower_peak_velocity > 0 else 0.0

        return {
            'lower_body_peak_velocity': float(lower_peak_velocity),
            'upper_body_peak_velocity': float(upper_peak_velocity),
            'velocity_ratio': float(velocity_ratio),
            'transfer_timing': transfer_timing,
            'lower_peak_frame': int(lower_peak_frame),
            'upper_peak_frame': int(upper_peak_frame),
            'timing_difference': int(timing_difference),
            'lower_body_joints': lower_body_joints,
            'upper_body_joints': upper_body_joints,
            'analysis_range': {
                'start_frame': start_frame,
                'end_frame': end_frame,
                'start_keyframe': 'ball_lowest'
            }
        }
