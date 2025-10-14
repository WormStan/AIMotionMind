"""
关键帧对比模块
用于两次篮球投篮分析报告之间的关键帧对比
"""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import shutil


class KeyframeComparison:
    """关键帧对比分析类"""

    # 角度名称中文映射
    ANGLE_NAME_MAP = {
        'knee_angle': '膝关节角度',
        'hip_angle': '髋关节角度',
        'elbow_angle': '肘关节角度',
        'shoulder_angle': '肩关节角度',
        'wrist_angle': '手腕角度',
        'trunk_lean': '躯干倾斜'
    }

    # 关键帧类型中文映射
    KEYFRAME_TYPE_MAP = {
        'ball_lowest': '球的最低点',
        'lift_start': '开始持续抬球',
        'ball_rising_mid': '球上升中点',
        'ball_at_chest': '球到胸部高度',
        'squat_deepest': '重心最低点（下蹲最深）',
        'ball_at_shoulder': '球到肩部高度',
        'leg_power_start': '腿部开始发力（蹬伸）',
        'power_transfer': '力量传递',
        'elbow_max_bend': '肘关节最大弯曲',
        'wrist_snap': '手腕下压（snap）',
        'release_prepare': '出手准备',
        'elbow_extension_max': '肘关节伸展最快',
        'release': '出手瞬间',
        'follow_through': '随球动作'
    }

    @staticmethod
    def list_available_analyses(output_dir: str, sport: str = "basketball") -> List[Dict[str, Any]]:
        """
        列出所有可用的分析数据

        Args:
            output_dir: 输出根目录
            sport: 运动类型

        Returns:
            分析数据列表，每个包含 folder, timestamp, video_name, path, analysis_path
        """
        sport_dir = Path(output_dir) / sport
        if not sport_dir.exists():
            return []

        analyses = []
        for analysis_folder in sport_dir.iterdir():
            if not analysis_folder.is_dir():
                continue

            # 跳过报告文件夹
            if 'report' in analysis_folder.name.lower() or 'comparison' in analysis_folder.name.lower():
                continue

            # 检查是否有 data 目录和 analysis_data.json
            data_file = analysis_folder / "data" / "analysis_data.json"
            if not data_file.exists():
                continue

            # 提取时间戳
            folder_name = analysis_folder.name
            if "_" in folder_name:
                timestamp = folder_name.split("_", 1)[1]
            else:
                timestamp = folder_name

            analyses.append({
                'folder': folder_name,
                'timestamp': timestamp,
                'video_name': folder_name,
                'path': str(data_file),
                'analysis_path': str(analysis_folder)
            })

        # 按时间戳倒序排列
        analyses.sort(key=lambda x: x['timestamp'], reverse=True)
        return analyses

    @staticmethod
    def load_analysis_data(json_path: str) -> Optional[Dict[str, Any]]:
        """
        加载分析数据

        Args:
            json_path: JSON文件路径

        Returns:
            分析数据字典，失败返回None
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载数据失败: {e}")
            return None

    @staticmethod
    def compare_two_keyframes(
        data1: Dict[str, Any],
        data2: Dict[str, Any],
        analysis_path1: str,
        analysis_path2: str,
        label1: str = "投篮A",
        label2: str = "投篮B"
    ) -> Dict[str, Any]:
        """
        对比两组关键帧数据

        Args:
            data1: 第一组分析数据
            data2: 第二组分析数据
            analysis_path1: 第一组分析路径
            analysis_path2: 第二组分析路径
            label1: 第一组标签
            label2: 第二组标签

        Returns:
            对比结果字典
        """
        keyframes1 = data1.get('keyframes', {})
        keyframes2 = data2.get('keyframes', {})

        comparison = {
            'label1': label1,
            'label2': label2,
            'analysis_path1': analysis_path1,
            'analysis_path2': analysis_path2,
            'keyframes': {},
            'summary': {
                'total_keyframes_1': len(keyframes1),
                'total_keyframes_2': len(keyframes2),
                'common_keyframes': [],
                'only_in_1': [],
                'only_in_2': []
            }
        }

        # 找出所有关键帧类型
        all_keyframe_types = set(keyframes1.keys()) | set(keyframes2.keys())
        common_types = set(keyframes1.keys()) & set(keyframes2.keys())

        comparison['summary']['common_keyframes'] = list(common_types)
        comparison['summary']['only_in_1'] = list(
            set(keyframes1.keys()) - set(keyframes2.keys()))
        comparison['summary']['only_in_2'] = list(
            set(keyframes2.keys()) - set(keyframes1.keys()))

        # 对比每个关键帧类型
        for kf_type in all_keyframe_types:
            kf_comparison = {
                'type': kf_type,
                'exists_in_1': kf_type in keyframes1,
                'exists_in_2': kf_type in keyframes2,
            }

            if kf_type in keyframes1:
                kf1 = keyframes1[kf_type]
                kf_comparison['data1'] = {
                    'timestamp': kf1.get('timestamp', 0),
                    'frame_index': kf1.get('index', 0),
                    'description': kf1.get('description', ''),
                    'angles': kf1.get('angles', {}),
                    'image_path': kf1.get('image_path', '')
                }

            if kf_type in keyframes2:
                kf2 = keyframes2[kf_type]
                kf_comparison['data2'] = {
                    'timestamp': kf2.get('timestamp', 0),
                    'frame_index': kf2.get('index', 0),
                    'description': kf2.get('description', ''),
                    'angles': kf2.get('angles', {}),
                    'image_path': kf2.get('image_path', '')
                }

            # 如果两个都存在，计算差异
            if kf_type in keyframes1 and kf_type in keyframes2:
                angles1 = keyframes1[kf_type].get('angles', {})
                angles2 = keyframes2[kf_type].get('angles', {})

                angle_diffs = {}
                for angle_name in set(angles1.keys()) | set(angles2.keys()):
                    if angle_name in angles1 and angle_name in angles2:
                        diff = angles2[angle_name] - angles1[angle_name]
                        angle_diffs[angle_name] = {
                            'value1': angles1[angle_name],
                            'value2': angles2[angle_name],
                            'difference': diff,
                            'percentage': (diff / angles1[angle_name] * 100) if angles1[angle_name] != 0 else 0
                        }

                kf_comparison['angle_differences'] = angle_diffs

                # 时间差异
                time1 = keyframes1[kf_type].get('timestamp', 0)
                time2 = keyframes2[kf_type].get('timestamp', 0)
                kf_comparison['time_difference'] = time2 - time1

            comparison['keyframes'][kf_type] = kf_comparison

        return comparison

    @staticmethod
    def generate_text_summary(comparison: Dict[str, Any]) -> str:
        """
        生成文本摘要

        Args:
            comparison: 对比结果

        Returns:
            文本摘要
        """
        lines = []
        lines.append("关键帧对比分析摘要")
        lines.append("=" * 70)
        lines.append(f"投篮A: {comparison['label1']}")
        lines.append(f"投篮B: {comparison['label2']}")
        lines.append("-" * 70)

        summary = comparison['summary']
        lines.append(
            f"关键帧数量: {summary['total_keyframes_1']} vs {summary['total_keyframes_2']}")
        lines.append(f"共同关键帧: {len(summary['common_keyframes'])} 个")

        if summary['only_in_1']:
            lines.append(f"仅在投篮A中: {', '.join(summary['only_in_1'])}")
        if summary['only_in_2']:
            lines.append(f"仅在投篮B中: {', '.join(summary['only_in_2'])}")

        lines.append("-" * 70)
        lines.append("关键差异:")

        for kf_type, kf_comp in comparison['keyframes'].items():
            if kf_comp['exists_in_1'] and kf_comp['exists_in_2']:
                # 使用中文关键帧名称
                kf_name_cn = KeyframeComparison.KEYFRAME_TYPE_MAP.get(
                    kf_type, kf_type)
                lines.append(f"\n  {kf_name_cn}:")
                if 'angle_differences' in kf_comp:
                    for angle_name, diff_data in kf_comp['angle_differences'].items():
                        # 使用中文角度名称
                        angle_name_cn = KeyframeComparison.ANGLE_NAME_MAP.get(
                            angle_name, angle_name)
                        diff_val = diff_data['difference']
                        lines.append(f"    {angle_name_cn}: {diff_val:+.1f}° "
                                     f"({diff_data['value1']:.1f}° → {diff_data['value2']:.1f}°)")

                if 'time_difference' in kf_comp:
                    time_diff = kf_comp['time_difference']
                    lines.append(f"    时间差: {time_diff:+.2f}秒")

        return "\n".join(lines)

    @staticmethod
    def prepare_comparison_images(
        comparison: Dict[str, Any],
        output_dir: str
    ) -> Dict[str, Any]:
        """
        准备对比图片（复制到输出目录）

        Args:
            comparison: 对比结果
            output_dir: 输出目录

        Returns:
            更新后的对比结果（包含新的图片路径）
        """
        images_dir = Path(output_dir) / "keyframe_images"
        images_dir.mkdir(parents=True, exist_ok=True)

        for kf_type, kf_comp in comparison['keyframes'].items():
            # 复制图片1
            if kf_comp['exists_in_1'] and 'data1' in kf_comp:
                old_path = kf_comp['data1'].get('image_path', '')
                if old_path and Path(old_path).exists():
                    new_filename = f"{kf_type}_shot1.jpg"
                    new_path = images_dir / new_filename
                    shutil.copy2(old_path, new_path)
                    kf_comp['data1']['comparison_image_path'] = str(new_path)
                    kf_comp['data1']['comparison_image_rel'] = f"keyframe_images/{new_filename}"

            # 复制图片2
            if kf_comp['exists_in_2'] and 'data2' in kf_comp:
                old_path = kf_comp['data2'].get('image_path', '')
                if old_path and Path(old_path).exists():
                    new_filename = f"{kf_type}_shot2.jpg"
                    new_path = images_dir / new_filename
                    shutil.copy2(old_path, new_path)
                    kf_comp['data2']['comparison_image_path'] = str(new_path)
                    kf_comp['data2']['comparison_image_rel'] = f"keyframe_images/{new_filename}"

        return comparison

    @staticmethod
    def save_comparison_data(comparison: Dict[str, Any], output_dir: str) -> str:
        """
        保存对比数据为JSON

        Args:
            comparison: 对比结果
            output_dir: 输出目录

        Returns:
            保存的文件路径
        """
        output_path = Path(output_dir) / "comparison_data.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)

        return str(output_path)
