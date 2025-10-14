"""
篮球投篮关键帧检测器

检测投篮动作中的关键帧（最多可达15个，具体数量取决于视频内容）：

重要：球最低点是投篮动作的起点，所有其他关键帧必须在球最低点之后

主要关键帧：
- 身体重心：squat_deepest (下蹲最深)
- 球位置：ball_lowest (球最低点 - 必定是第一个), lift_start (开始抬球), 
          ball_at_chest (球到胸部), ball_at_shoulder (球到肩部)
- 上肢动作：elbow_max_bend (肘最大弯曲), elbow_extension_max (肘伸展最快),
           wrist_snap (手腕下压), arm_full_extension (手臂伸直)
- 下肢动作：leg_power_start (腿部发力)
- 出手相关：release (出手瞬间), follow_through (随球完成)

辅助关键帧（中点）：
- ball_rising_mid (球上升中点)
- power_transfer (力量传递中点)  
- release_prepare (出手准备中点)

使用方法：
    from sports.basketball.keyframe_detector import KeyframeDetector
    keyframes = KeyframeDetector.detect_keyframes(frames_data)
"""
import numpy as np
from typing import Dict, List, Optional
from collections import OrderedDict


class KeyframeDetector:
    """篮球投篮关键帧检测器"""

    @staticmethod
    def detect_keyframes(frames_data: List[Dict]) -> Dict[str, Dict]:
        """
        检测所有关键帧并按时间排序

        重要：球最低点是投篮动作的起点，所有其他关键帧必须在球最低点之后

        Args:
            frames_data: 帧数据列表

        Returns:
            按时间排序的关键帧字典（球最低点永远是第一个）
        """
        keyframes = {}

        print("\n开始检测关键帧...")
        print("=" * 70)

        # 第一步：先在完整视频中检测球最低点（这是投篮动作的起点）
        ball_lowest_kf = KeyframeDetector._detect_ball_lowest(frames_data)
        if ball_lowest_kf:
            keyframes['ball_lowest'] = ball_lowest_kf
            ball_lowest_idx = ball_lowest_kf['index']
            print(f"✓ ball_lowest (球最低点 - 投篮起点): 帧 {ball_lowest_idx}")
        else:
            print("⚠️  警告: 未检测到球最低点，将使用第0帧作为起点")
            ball_lowest_idx = 0
            keyframes['ball_lowest'] = {
                'index': 0,
                'timestamp': 0.0,
                'frame_data': frames_data[0] if frames_data else {},
                'description': '默认起点（未检测到球最低点）'
            }

        # 第二步：创建裁剪后的帧列表（只包含球最低点及之后的帧）
        # 这样所有后续检测都只会在有效范围内进行
        clipped_frames = frames_data[ball_lowest_idx:]
        total_frames = len(frames_data)
        valid_frames = len(clipped_frames)

        print(
            f"\n📍 投篮分析范围: 从第{ball_lowest_idx}帧开始，共{valid_frames}帧（总共{total_frames}帧）")
        print(f"   忽略前{ball_lowest_idx}帧（球最低点之前）")
        print("=" * 70)

        # 第三步：在裁剪后的帧列表中检测其他关键帧
        # 注意：检测结果的索引是相对于裁剪列表的，需要加上 ball_lowest_idx 才是原始索引

        # 重心最低点（可能在裁剪范围内，也可能被过滤掉）
        squat_deepest_kf = KeyframeDetector._detect_squat_deepest(
            clipped_frames)
        if squat_deepest_kf:
            squat_deepest_kf['index'] += ball_lowest_idx  # 映射回原始索引
            keyframes['squat_deepest'] = squat_deepest_kf
            print(f"✓ squat_deepest (重心最低点): 帧 {squat_deepest_kf['index']}")

        # 球位置相关（从球最低点开始检测，start_idx相对于裁剪列表是0）
        kf = KeyframeDetector._detect_lift_start(clipped_frames, 0)
        if kf:
            kf['index'] += ball_lowest_idx
            keyframes['lift_start'] = kf
            print(f"✓ lift_start (开始抬球): 帧 {kf['index']}")

        # 球高度检测：从抬球开始之后搜索
        lift_start_idx = keyframes.get('lift_start', {}).get(
            'index', ball_lowest_idx) - ball_lowest_idx

        kf = KeyframeDetector._detect_ball_at_height(
            clipped_frames, 'chest', lift_start_idx)
        if kf:
            kf['index'] += ball_lowest_idx
            keyframes['ball_at_chest'] = kf
            print(f"✓ ball_at_chest (球到胸部): 帧 {kf['index']}")

        # 球上升中点
        if 'lift_start' in keyframes and 'ball_at_chest' in keyframes:
            kf = KeyframeDetector._detect_midpoint(
                keyframes['lift_start'], keyframes['ball_at_chest'],
                frames_data, "球上升中点")
            if kf:
                keyframes['ball_rising_mid'] = kf
                print(f"✓ ball_rising_mid (球上升中点): 帧 {kf['index']}")

        ball_at_chest_idx = keyframes.get('ball_at_chest', {}).get(
            'index', ball_lowest_idx) - ball_lowest_idx

        kf = KeyframeDetector._detect_ball_at_height(
            clipped_frames, 'shoulder', ball_at_chest_idx)
        if kf:
            kf['index'] += ball_lowest_idx
            keyframes['ball_at_shoulder'] = kf
            print(f"✓ ball_at_shoulder (球到肩部): 帧 {kf['index']}")

        # 上肢动作相关（在裁剪列表中检测）
        elbow_max_bend_kf = KeyframeDetector._detect_elbow_max_bend(
            clipped_frames)
        if elbow_max_bend_kf:
            elbow_max_bend_kf['index'] += ball_lowest_idx
            keyframes['elbow_max_bend'] = elbow_max_bend_kf
            print(f"✓ elbow_max_bend (肘最大弯曲): 帧 {elbow_max_bend_kf['index']}")

        elbow_ext_kf = KeyframeDetector._detect_elbow_extension_max(
            clipped_frames)
        if elbow_ext_kf:
            elbow_ext_kf['index'] += ball_lowest_idx
            keyframes['elbow_extension_max'] = elbow_ext_kf
            print(f"✓ elbow_extension_max (肘伸展最快): 帧 {elbow_ext_kf['index']}")

        wrist_snap_kf = KeyframeDetector._detect_wrist_snap(clipped_frames)
        if wrist_snap_kf:
            wrist_snap_kf['index'] += ball_lowest_idx
            keyframes['wrist_snap'] = wrist_snap_kf
            print(f"✓ wrist_snap (手腕下压): 帧 {wrist_snap_kf['index']}")

        arm_ext_kf = KeyframeDetector._detect_arm_full_extension(
            clipped_frames)
        if arm_ext_kf:
            arm_ext_kf['index'] += ball_lowest_idx
            keyframes['arm_full_extension'] = arm_ext_kf
            print(f"✓ arm_full_extension (手臂伸直): 帧 {arm_ext_kf['index']}")

        # 下肢动作相关
        leg_power_kf = KeyframeDetector._detect_leg_power_start(clipped_frames)
        if leg_power_kf:
            leg_power_kf['index'] += ball_lowest_idx
            keyframes['leg_power_start'] = leg_power_kf
            print(f"✓ leg_power_start (腿部发力): 帧 {leg_power_kf['index']}")

        # 力量传递（在已有关键帧之间计算）
        if 'leg_power_start' in keyframes and 'elbow_max_bend' in keyframes:
            kf = KeyframeDetector._detect_midpoint(
                keyframes['leg_power_start'], keyframes['elbow_max_bend'],
                frames_data, "力量传递")
            if kf:
                keyframes['power_transfer'] = kf
                print(f"✓ power_transfer (力量传递): 帧 {kf['index']}")

        # 出手相关（start_idx相对于裁剪列表是0）
        release_kf = KeyframeDetector._detect_release(clipped_frames, 0)
        if release_kf:
            release_kf['index'] += ball_lowest_idx
            keyframes['release'] = release_kf
            print(f"✓ release (出手瞬间): 帧 {release_kf['index']}")

        # 出手准备（在已有关键帧之间计算）
        if 'wrist_snap' in keyframes and 'release' in keyframes:
            kf = KeyframeDetector._detect_midpoint(
                keyframes['wrist_snap'], keyframes['release'],
                frames_data, "出手准备")
            if kf:
                keyframes['release_prepare'] = kf
                print(f"✓ release_prepare (出手准备): 帧 {kf['index']}")

        # 跟随动作
        follow_kf = KeyframeDetector._detect_follow_through(clipped_frames)
        if follow_kf:
            follow_kf['index'] += ball_lowest_idx
            keyframes['follow_through'] = follow_kf
            print(f"✓ follow_through (随球完成): 帧 {follow_kf['index']}")

        print(f"\n检测到 {len(keyframes)} 个有效关键帧（全部在球最低点之后）")

        # 按时间排序（球最低点永远是第一个）
        sorted_keyframes = KeyframeDetector._sort_by_time(keyframes)

        # 验证球最低点是第一个
        first_kf = next(iter(sorted_keyframes.keys()))
        if first_kf != 'ball_lowest':
            print(f"\n⚠️  警告: 第一个关键帧不是ball_lowest，而是{first_kf}，需要调整")

        # 验证合理性
        warnings = KeyframeDetector._validate_order(sorted_keyframes)
        if warnings:
            print("\n⚠️  合理性警告：")
            for warning in warnings:
                print(f"  {warning}")
        else:
            print("\n✓ 所有关键帧时间顺序合理")

        print("=" * 70)

        return sorted_keyframes

    @staticmethod
    def _sort_by_time(keyframes: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        按实际发生时间（帧索引）排序

        由于所有关键帧都在球最低点之后检测，排序后球最低点自然是第一个
        """
        sorted_items = sorted(keyframes.items(), key=lambda x: x[1]['index'])
        sorted_dict = OrderedDict(sorted_items)

        # 验证：确保球最低点是第一个关键帧
        if sorted_dict and 'ball_lowest' in sorted_dict:
            first_key = next(iter(sorted_dict))
            if first_key != 'ball_lowest':
                print(f"⚠️  排序异常: 第一个关键帧是 {first_key}，而不是 ball_lowest")

        return sorted_dict

    @staticmethod
    def _validate_order(keyframes: Dict[str, Dict]) -> List[str]:
        """验证关键帧顺序的合理性"""
        warnings = []
        kf_dict = {name: data['index'] for name, data in keyframes.items()}

        # 最重要的验证：球最低点必须是第一个关键帧
        if 'ball_lowest' in kf_dict:
            ball_lowest_frame = kf_dict['ball_lowest']
            for name, frame_idx in kf_dict.items():
                if name != 'ball_lowest' and frame_idx < ball_lowest_frame:
                    warnings.append(
                        f"❌ 严重错误: {name} (帧{frame_idx}) 在 ball_lowest (帧{ball_lowest_frame}) 之前！")

        if 'ball_lowest' in kf_dict and 'lift_start' in kf_dict:
            if kf_dict['ball_lowest'] > kf_dict['lift_start']:
                warnings.append(
                    f"ball_lowest ({kf_dict['ball_lowest']}) 晚于 lift_start ({kf_dict['lift_start']})")

        if 'set_point' in kf_dict and 'release' in kf_dict:
            if kf_dict['set_point'] > kf_dict['release']:
                warnings.append(
                    f"set_point ({kf_dict['set_point']}) 晚于 release ({kf_dict['release']})")

        if 'release' in kf_dict and 'follow_through' in kf_dict:
            if kf_dict['release'] > kf_dict['follow_through']:
                warnings.append(
                    f"release ({kf_dict['release']}) 晚于 follow_through ({kf_dict['follow_through']})")

        if 'leg_power_start' in kf_dict and 'release' in kf_dict:
            if kf_dict['leg_power_start'] > kf_dict['release']:
                warnings.append(
                    f"leg_power_start ({kf_dict['leg_power_start']}) 晚于 release ({kf_dict['release']})")

        if 'ball_at_chest' in kf_dict and 'ball_at_shoulder' in kf_dict:
            if kf_dict['ball_at_chest'] > kf_dict['ball_at_shoulder']:
                warnings.append(
                    f"ball_at_chest ({kf_dict['ball_at_chest']}) 晚于 ball_at_shoulder ({kf_dict['ball_at_shoulder']})")

        return warnings

    @staticmethod
    def _detect_midpoint(kf1: Dict, kf2: Dict, frames_data: List[Dict], description: str) -> Optional[Dict]:
        """检测两个关键帧之间的中点帧"""
        idx1 = kf1['index']
        idx2 = kf2['index']

        if idx1 >= idx2:
            return None

        # 计算中点帧索引
        mid_idx = (idx1 + idx2) // 2

        return {
            "index": mid_idx,
            "frame_data": frames_data[mid_idx],
            "description": description
        }

    @staticmethod
    def _detect_squat_deepest(frames_data: List[Dict]) -> Optional[Dict]:
        """检测重心最低点（下蹲最深）"""
        com_heights = [f.get("com_height", 0) for f in frames_data]
        if not com_heights or max(com_heights) == 0:
            return None

        idx = int(np.argmax(com_heights))

        return {
            "index": idx,
            "frame_data": frames_data[idx],
            "description": "重心最低点（下蹲最深）"
        }

    @staticmethod
    def _detect_ball_lowest(frames_data: List[Dict]) -> Optional[Dict]:
        """检测球的最低点（使用右手腕Y坐标）"""
        ball_heights = []
        for f in frames_data:
            landmarks = f.get("landmarks", {})
            right_wrist = landmarks.get("right_wrist")

            if right_wrist:
                # 球的位置 = 右手腕Y坐标
                ball_y = right_wrist['y']
                ball_heights.append(ball_y)
            else:
                ball_heights.append(0.0)

        if not ball_heights or max(ball_heights) == 0:
            return None

        idx = int(np.argmax(ball_heights))

        return {
            "index": idx,
            "frame_data": frames_data[idx],
            "description": "球的最低点"
        }

    @staticmethod
    def _detect_lift_start(frames_data: List[Dict], search_after: int = 0) -> Optional[Dict]:
        """检测开始持续抬球的时刻"""
        ball_heights = []
        for f in frames_data:
            landmarks = f.get("landmarks", {})
            right_wrist = landmarks.get("right_wrist")

            if right_wrist:
                ball_y = right_wrist['y']
                ball_heights.append(ball_y)
            else:
                ball_heights.append(1.0)

        for i in range(search_after, len(ball_heights) - 3):
            if (ball_heights[i] > ball_heights[i+1] > ball_heights[i+2] > ball_heights[i+3]):
                total_rise = ball_heights[i] - ball_heights[i+3]
                if total_rise > 0.01:
                    return {
                        "index": i,
                        "frame_data": frames_data[i],
                        "description": "开始持续抬球"
                    }

        return None

    @staticmethod
    def _detect_ball_at_height(frames_data: List[Dict], height_type: str, search_after: int = 0) -> Optional[Dict]:
        """检测手腕到达特定高度的时刻（上升过程中最接近目标的位置）"""
        distances = []  # 存储手腕与目标高度的距离

        for f in frames_data:
            landmarks = f.get("landmarks", {})
            right_wrist = landmarks.get("right_wrist")
            left_shoulder = landmarks.get("left_shoulder")
            right_shoulder = landmarks.get("right_shoulder")
            left_hip = landmarks.get("left_hip")
            right_hip = landmarks.get("right_hip")

            if all([right_wrist, left_shoulder, right_shoulder, left_hip, right_hip]):
                # 手腕Y坐标
                wrist_y = right_wrist['y']

                shoulder_y = (left_shoulder['y'] + right_shoulder['y']) / 2
                hip_y = (left_hip['y'] + right_hip['y']) / 2

                if height_type == 'chest':
                    # 胸部高度：肩部下方约 1/3 的位置
                    target_y = shoulder_y + (hip_y - shoulder_y) * 0.33
                elif height_type == 'shoulder':
                    # 使用右肩的Y坐标
                    target_y = right_shoulder['y']
                else:
                    target_y = 1.0

                # 计算距离（绝对值）
                distance = abs(wrist_y - target_y)
                distances.append(distance)
            else:
                distances.append(float('inf'))  # 无效帧使用无穷大

        # 在上升区间内找到距离目标最近的帧
        # 首先确定上升区间（从 search_after 开始，手腕持续上升）
        min_distance = float('inf')
        best_idx = None

        for i in range(search_after, len(frames_data)):
            # 确保在上升过程中（Y值减小）
            if i > 0 and frames_data[i].get("landmarks", {}).get("right_wrist"):
                current_wrist_y = frames_data[i]["landmarks"]["right_wrist"]['y']

                # 找到距离最小的帧
                if distances[i] < min_distance:
                    min_distance = distances[i]
                    best_idx = i

        if best_idx is not None:
            description = "球到胸部高度" if height_type == 'chest' else "球到肩部高度"
            return {
                "index": best_idx,
                "frame_data": frames_data[best_idx],
                "description": description
            }

        return None

    @staticmethod
    def _detect_elbow_max_bend(frames_data: List[Dict]) -> Optional[Dict]:
        """检测肘关节最大弯曲点"""
        elbow_angles = [f.get("angles", {}).get(
            "elbow_angle", 180) for f in frames_data]

        if not elbow_angles or min(elbow_angles) >= 180:
            return None

        idx = int(np.argmin(elbow_angles))

        return {
            "index": idx,
            "frame_data": frames_data[idx],
            "description": f"肘关节最大弯曲（{elbow_angles[idx]:.1f}°）"
        }

    @staticmethod
    def _detect_set_point(frames_data: List[Dict], search_after: int = 0) -> Optional[Dict]:
        """检测出手定点（多因素评分）"""
        scores = []

        wrist_heights = []
        elbow_angles = []
        velocities = []

        for f in frames_data:
            landmarks = f.get("landmarks", {})
            wrist = landmarks.get("right_wrist")
            wrist_heights.append(wrist['y'] if wrist else 1.0)
            elbow_angles.append(f.get("angles", {}).get("elbow_angle", 180))
            velocities.append(f.get("velocities", {}).get("right_wrist", 0))

        angle_changes = [0] + [abs(elbow_angles[i] - elbow_angles[i-1])
                               for i in range(1, len(elbow_angles))]

        for i in range(search_after, len(frames_data)):
            score = 0

            # 手腕高度
            score += (1 - wrist_heights[i]) * 30

            # 肘角度适中（60-120度）
            angle = elbow_angles[i]
            if 60 <= angle <= 120:
                score += 30
            else:
                score += max(0, 30 - abs(angle - 90) * 0.5)

            # 运动减速
            score += max(0, 20 - abs(velocities[i]) * 100)

            # 角度变化小
            score += max(0, 20 - angle_changes[i] * 2)

            scores.append(score)

        scores = [0] * search_after + scores

        if not scores or max(scores) == 0:
            return None

        idx = int(np.argmax(scores))

        return {
            "index": idx,
            "frame_data": frames_data[idx],
            "description": "出手定点"
        }

    @staticmethod
    def _detect_elbow_extension_max(frames_data: List[Dict]) -> Optional[Dict]:
        """检测肘关节伸展最快的时刻"""
        elbow_angles = [f.get("angles", {}).get(
            "elbow_angle", 180) for f in frames_data]

        angular_velocities = [0] + [elbow_angles[i] - elbow_angles[i-1]
                                    for i in range(1, len(elbow_angles))]
        positive_velocities = [max(0, v) for v in angular_velocities]

        if not positive_velocities or max(positive_velocities) == 0:
            return None

        idx = int(np.argmax(positive_velocities))

        return {
            "index": idx,
            "frame_data": frames_data[idx],
            "description": f"肘关节伸展最快（{positive_velocities[idx]:.1f}°/帧）"
        }

    @staticmethod
    def _detect_wrist_snap(frames_data: List[Dict]) -> Optional[Dict]:
        """检测手腕下压（snap）的时刻"""
        wrist_elbow_diffs = []

        for f in frames_data:
            landmarks = f.get("landmarks", {})
            wrist = landmarks.get("right_wrist")
            elbow = landmarks.get("right_elbow")

            if wrist and elbow:
                diff = wrist['y'] - elbow['y']
                wrist_elbow_diffs.append(diff)
            else:
                wrist_elbow_diffs.append(-1.0)

        if not wrist_elbow_diffs or max(wrist_elbow_diffs) <= 0:
            return None

        # 从后半段开始搜索
        search_start = len(frames_data) // 2
        max_idx = search_start + \
            int(np.argmax(wrist_elbow_diffs[search_start:]))

        return {
            "index": max_idx,
            "frame_data": frames_data[max_idx],
            "description": "手腕下压（snap）"
        }

    @staticmethod
    def _detect_arm_full_extension(frames_data: List[Dict]) -> Optional[Dict]:
        """检测手臂完全伸直的时刻"""
        elbow_angles = [f.get("angles", {}).get(
            "elbow_angle", 180) for f in frames_data]

        for i, angle in enumerate(elbow_angles):
            if angle >= 170:
                return {
                    "index": i,
                    "frame_data": frames_data[i],
                    "description": f"手臂完全伸直（{angle:.1f}°）"
                }

        idx = int(np.argmax(elbow_angles))
        if elbow_angles[idx] > 155:
            return {
                "index": idx,
                "frame_data": frames_data[idx],
                "description": f"手臂接近伸直（{elbow_angles[idx]:.1f}°）"
            }

        return None

    @staticmethod
    def _detect_leg_power_start(frames_data: List[Dict]) -> Optional[Dict]:
        """检测腿部开始发力的时刻"""
        knee_angles = [f.get("angles", {}).get("knee_angle", 180)
                       for f in frames_data]

        angle_velocities = [0] + [knee_angles[i] - knee_angles[i-1]
                                  for i in range(1, len(knee_angles))]

        # 找到从负到正的转折点
        for i in range(1, len(angle_velocities) - 1):
            if angle_velocities[i-1] < 0 and angle_velocities[i] >= 0:
                if i+1 < len(angle_velocities) and angle_velocities[i+1] >= 0:
                    return {
                        "index": i,
                        "frame_data": frames_data[i],
                        "description": "腿部开始发力（蹬伸）"
                    }

        # 备选：角速度最大的伸展点
        positive_velocities = [max(0, v) for v in angle_velocities]
        if max(positive_velocities) > 0:
            idx = int(np.argmax(positive_velocities))
            return {
                "index": idx,
                "frame_data": frames_data[idx],
                "description": f"腿部伸展最快（{positive_velocities[idx]:.1f}°/帧）"
            }

        return None

    @staticmethod
    def _detect_release(frames_data: List[Dict], search_after: int = 0) -> Optional[Dict]:
        """检测出手瞬间（多因素评分）"""
        scores = []

        wrist_heights = []
        elbow_angles = []
        wrist_velocities = []

        for f in frames_data:
            landmarks = f.get("landmarks", {})
            wrist = landmarks.get("right_wrist")
            wrist_heights.append(wrist['y'] if wrist else 1.0)
            elbow_angles.append(f.get("angles", {}).get("elbow_angle", 180))
            wrist_velocities.append(
                f.get("velocities", {}).get("right_wrist", 0))

        elbow_velocities = [0] + [elbow_angles[i] - elbow_angles[i-1]
                                  for i in range(1, len(elbow_angles))]

        for i in range(search_after, len(frames_data)):
            score = 0

            # 手腕高度
            score += (1 - wrist_heights[i]) * 40

            # 肘关节快速伸展
            elbow_extension_score = max(0, elbow_velocities[i] * 3.5)
            score += min(elbow_extension_score, 35)

            # 手腕仍在上升
            if wrist_velocities[i] < 0:
                score += min(abs(wrist_velocities[i]) * 250, 25)

            scores.append(score)

        scores = [0] * search_after + scores

        if not scores or max(scores) == 0:
            return None

        idx = int(np.argmax(scores))

        return {
            "index": idx,
            "frame_data": frames_data[idx],
            "description": "出手瞬间"
        }

    @staticmethod
    def _detect_follow_through(frames_data: List[Dict]) -> Optional[Dict]:
        """检测随球动作完成的时刻"""
        wrist_heights = []

        for f in frames_data:
            landmarks = f.get("landmarks", {})
            wrist = landmarks.get("right_wrist")
            if wrist:
                wrist_heights.append(wrist['y'])
            else:
                wrist_heights.append(1.0)

        if not wrist_heights or min(wrist_heights) >= 1.0:
            return None

        idx = int(np.argmin(wrist_heights))

        return {
            "index": idx,
            "frame_data": frames_data[idx],
            "description": "随球动作完成（手腕最高点）"
        }
