"""
分析服务 - 封装核心分析逻辑供API调用
"""
import sys
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from sports.basketball.shot_analyzer import BasketballShotAnalyzer
from core.report_generator import ReportGenerator
from core.data_manager import DataManager
from core.video_processor import VideoProcessor
from config import BASKETBALL_SHOT_CONFIG, OUTPUT_DIR



class AnalysisService:
    """分析服务：封装视频分析逻辑"""

    def __init__(self):
        self.config = BASKETBALL_SHOT_CONFIG
        self.output_dir = OUTPUT_DIR

    def analyze_video(self, video_path: str, options: dict, progress_callback=None):
        """
        分析视频

        Args:
            video_path: 视频文件路径
            options: 分析选项
                - frame_interval: 帧间隔（默认5）
                - sport_type: 运动类型（默认basketball）
                - device_id: 设备ID（用于确定输出目录）
                - analysis_name: 自定义分析名称（可选）
                - analysis_id: 自定义分析ID（可选）
            progress_callback: 进度回调函数 callback(progress: int, message: str)

        Returns:
            dict: 分析结果
                - analysis_id: 分析ID
                - output_dir: 输出目录
                - video_info: 视频信息
                - keyframes: 关键帧信息
                - report_path: 报告路径
        """
        try:
            # 更新进度：0%
            if progress_callback:
                progress_callback(0, '开始处理视频...')

            # 1. 初始化视频处理器
            processor = VideoProcessor(video_path)
            video_info = processor.get_video_info()

            # 更新进度：5%
            if progress_callback:
                progress_callback(5, f'视频信息获取完成: {video_info["frame_count"]}帧')

            # 2. 创建输出目录（支持用户隔离和自定义名称）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 如果提供了自定义分析ID，使用它；否则生成默认ID
            if options.get('analysis_id'):
                analysis_id = options.get('analysis_id')
            elif options.get('analysis_name'):
                # 清理分析名称，确保文件系统安全
                clean_name = options.get('analysis_name', '').strip()
                clean_name = ''.join(c for c in clean_name if c.isalnum() or c in ('_', '-', ' '))
                clean_name = clean_name.replace(' ', '_')[:50]  # 限制长度
                analysis_id = f"{clean_name}_{timestamp}" if clean_name else f"analysis_{timestamp}"
            else:
                analysis_id = f"analysis_{timestamp}"
            
            sport_type = options.get('sport_type', 'basketball')
            device_id = options.get('device_id', '')
            
            # 如果有device_id，输出到用户文件夹
            if device_id:
                output_dir = os.path.join(self.output_dir, device_id, sport_type, analysis_id)
            else:
                output_dir = os.path.join(self.output_dir, sport_type, analysis_id)

            # 更新进度：10%
            if progress_callback:
                progress_callback(10, '创建输出目录...')

            # 3. 提取视频帧
            frame_interval = options.get(
                'frame_interval', self.config.get('frame_interval', 5))

            if progress_callback:
                progress_callback(15, f'开始提取视频帧（间隔{frame_interval}帧）...')

            frames_data = processor.extract_frames(
                frame_interval=frame_interval,
                output_dir=os.path.join(output_dir, 'frames')
            )

            # 更新进度：30%
            if progress_callback:
                progress_callback(30, f'视频帧提取完成: {len(frames_data)}帧')

            # 4. 姿态分析
            if progress_callback:
                progress_callback(35, '开始姿态检测和指标计算...')

            analyzer = BasketballShotAnalyzer(self.config)
            analysis_results = analyzer.analyze_frames(
                frames_data, processor.fps)

            # 更新进度：60%
            if progress_callback:
                progress_callback(60, '姿态分析完成，开始检测关键帧...')

            # 5. 获取关键帧（已在analyzer中检测）
            keyframes = analysis_results.get('keyframes', {})

            # 保存关键帧图片
            keyframes_dir = os.path.join(output_dir, 'keyframes')
            os.makedirs(keyframes_dir, exist_ok=True)

            import cv2
            for kf_name, kf_data in keyframes.items():
                if 'frame_data' in kf_data and 'image' in kf_data['frame_data']:
                    kf_filename = f"keyframe_{kf_name}.jpg"
                    kf_path = os.path.join(keyframes_dir, kf_filename)
                    cv2.imwrite(kf_path, kf_data['frame_data']['image'])
                    kf_data['filename'] = kf_filename

            # 更新进度：75%
            if progress_callback:
                progress_callback(75, f'关键帧检测完成: {len(keyframes)}个关键帧')

            # 6. 保存数据
            if progress_callback:
                progress_callback(80, '保存分析数据...')

            data_manager = DataManager()
            data_manager.create_dataframes(analysis_results)

            # 导出 CSV 数据
            csv_dir = os.path.join(output_dir, 'data')
            data_manager.export_to_csv(csv_dir)

            # 导出分析结果 JSON（仅 analysis_results）
            json_path = os.path.join(output_dir, 'data', 'analysis_data.json')
            data_manager.export_to_json(analysis_results, json_path)

            # 导出完整数据 JSON（包含 video_info、keyframes 等）
            complete_json_path = os.path.join(output_dir, 'data', 'complete_data.json')
            complete_data = {
                'video_info': video_info,
                'analysis_results': analysis_results,
                'keyframes': keyframes,
                'timestamp': timestamp,
                'device_id': device_id,
                'sport_type': sport_type,
                'analysis_name': options.get('analysis_name', '')
            }
            os.makedirs(os.path.dirname(complete_json_path), exist_ok=True)
            with open(complete_json_path, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, ensure_ascii=False, indent=2, default=str)
            
            # 保存元数据到单独的文件
            metadata_path = os.path.join(output_dir, 'metadata.json')
            metadata = {
                'analysis_id': analysis_id,
                'analysis_name': options.get('analysis_name', ''),
                'analysis_time': datetime.now().isoformat(),
                'video_file': os.path.basename(video_path),
                'sport_type': sport_type,
                'device_id': device_id,
                'output_dir': output_dir,
                'frame_interval': options.get('frame_interval', 5)
            }
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 更新进度：90%
            if progress_callback:
                progress_callback(90, '生成分析报告...')

            # 7. 生成报告
            report_generator = ReportGenerator()
            reports_dir = os.path.join(output_dir, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            report_path = report_generator.generate_report(
                analysis_results=analysis_results,
                video_path=video_path,
                output_dir=reports_dir
            )

            # 更新进度：95%
            if progress_callback:
                progress_callback(95, '清理资源...')

            # 8. 清理
            if hasattr(processor, 'cap') and processor.cap is not None:
                processor.cap.release()

            # 更新进度：100%
            if progress_callback:
                progress_callback(100, '分析完成！')

            # 返回结果
            return {
                'analysis_id': analysis_id,
                'output_dir': output_dir,
                'video_info': video_info,
                'analysis_results': analysis_results,
                'keyframes': keyframes,
                'report_path': report_path,
                'timestamp': timestamp
            }

        except Exception as e:
            if progress_callback:
                progress_callback(-1, f'分析失败: {str(e)}')
            raise

    def get_analysis_result(self, analysis_id: str, sport_type: str = 'basketball', device_id: str = None):
        """
        获取分析结果

        Args:
            analysis_id: 分析ID
            sport_type: 运动类型
            device_id: 设备ID（用于定位用户文件夹）

        Returns:
            dict: 分析结果
        """
        try:
            # 如果有device_id，从用户文件夹读取
            if device_id:
                output_dir = os.path.join(self.output_dir, device_id, sport_type, analysis_id)
            else:
                output_dir = os.path.join(self.output_dir, sport_type, analysis_id)

            if not os.path.exists(output_dir):
                raise FileNotFoundError(f"分析结果不存在: {analysis_id}")

            # 优先读取完整数据文件
            complete_data_file = os.path.join(output_dir, 'data', 'complete_data.json')
            data_file = os.path.join(output_dir, 'data', 'analysis_data.json')

            data = {}
            if os.path.exists(complete_data_file):
                # 读取完整数据（包含 video_info）
                with open(complete_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif os.path.exists(data_file):
                # 降级读取旧格式数据（仅 analysis_results）
                with open(data_file, 'r', encoding='utf-8') as f:
                    analysis_results = json.load(f)
                    data = {'analysis_results': analysis_results}
            else:
                raise FileNotFoundError(f"分析数据文件不存在")

            # 获取关键帧列表
            keyframes_dir = os.path.join(output_dir, 'keyframes')
            keyframe_files = []
            if os.path.exists(keyframes_dir):
                keyframe_files = [f for f in os.listdir(
                    keyframes_dir) if f.endswith('.jpg')]
                keyframe_files.sort()

            # 获取报告路径
            reports_dir = os.path.join(output_dir, 'reports')
            report_file = None
            if os.path.exists(reports_dir):
                reports = [f for f in os.listdir(
                    reports_dir) if f.endswith('.html')]
                if reports:
                    report_file = reports[0]

            return {
                'analysis_id': analysis_id,
                'output_dir': output_dir,
                'video_info': data.get('video_info'),
                'analysis_results': data.get('analysis_results'),
                'keyframes': data.get('keyframes'),
                'keyframe_files': keyframe_files,
                'report_file': report_file
            }

        except Exception as e:
            raise Exception(f"获取分析结果失败: {str(e)}")

    def list_analyses(self, sport_type: str = 'basketball'):
        """
        列出所有分析结果

        Args:
            sport_type: 运动类型

        Returns:
            list: 分析结果列表
        """
        try:
            sport_dir = os.path.join(self.output_dir, sport_type)

            if not os.path.exists(sport_dir):
                return []

            analyses = []
            for analysis_id in os.listdir(sport_dir):
                analysis_path = os.path.join(sport_dir, analysis_id)

                # 跳过comparison_reports目录
                if not os.path.isdir(analysis_path) or 'comparison' in analysis_id:
                    continue

                # 读取分析数据
                data_file = os.path.join(
                    analysis_path, 'data', 'analysis_data.json')
                if os.path.exists(data_file):
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    analyses.append({
                        'analysis_id': analysis_id,
                        'timestamp': analysis_id.replace('analysis_', ''),
                        'video_info': data.get('video_info'),
                        'keyframe_count': len(data.get('keyframes', []))
                    })

            # 按时间倒序排序
            analyses.sort(key=lambda x: x['timestamp'], reverse=True)

            return analyses

        except Exception as e:
            raise Exception(f"列出分析结果失败: {str(e)}")


# 全局分析服务实例
analysis_service = AnalysisService()
