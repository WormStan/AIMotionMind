"""
任务管理器 - 管理异步分析任务
"""
import threading
import uuid
import sys
import os
from datetime import datetime
from typing import Dict, Optional
import traceback

# 导入自定义异常
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))
from exceptions import VideoAnalysisError


class TaskManager:
    """任务管理器：管理异步视频分析任务"""

    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        self.lock = threading.Lock()

    def create_task(self, video_path: str, options: dict, callback) -> str:
        """
        创建新任务

        Args:
            video_path: 视频文件路径
            options: 分析选项
            callback: 分析函数回调

        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid.uuid4())

        with self.lock:
            self.tasks[task_id] = {
                'task_id': task_id,
                'status': 'pending',  # pending, processing, completed, failed
                'progress': 0,
                'message': '任务创建成功，等待开始...',
                'video_path': video_path,
                'options': options,
                'created_at': datetime.now().isoformat(),
                'started_at': None,
                'completed_at': None,
                'result': None,
                'error': None
            }

        # 启动后台线程执行分析
        thread = threading.Thread(
            target=self._run_task,
            args=(task_id, callback),
            daemon=True
        )
        thread.start()

        return task_id

    def _run_task(self, task_id: str, callback):
        """
        后台执行任务

        Args:
            task_id: 任务ID
            callback: 分析函数
        """
        try:
            # 更新任务状态为进行中
            self.update_task(task_id, {
                'status': 'processing',
                'started_at': datetime.now().isoformat(),
                'message': '开始分析视频...'
            })

            # 获取任务信息
            task = self.get_task(task_id)
            video_path = task['video_path']
            options = task['options']

            # 执行分析（传入进度更新回调）
            def progress_callback(progress: int, message: str):
                self.update_task(task_id, {
                    'progress': progress,
                    'message': message
                })

            result = callback(video_path, options, progress_callback)

            # 任务完成
            self.update_task(task_id, {
                'status': 'completed',
                'progress': 100,
                'message': '分析完成',
                'completed_at': datetime.now().isoformat(),
                'result': result
            })

        except VideoAnalysisError as e:
            # 捕获自定义的视频分析错误，使用用户友好的错误信息
            error_msg = e.user_message if hasattr(e, 'user_message') else str(e)
            error_trace = traceback.format_exc()

            self.update_task(task_id, {
                'status': 'failed',
                'message': error_msg,
                'completed_at': datetime.now().isoformat(),
                'error': {
                    'message': error_msg,
                    'trace': error_trace,
                    'type': 'VideoAnalysisError'
                }
            })
        except Exception as e:
            # 任务失败 - 其他未预期的错误
            error_msg = f'分析过程发生错误: {str(e)}'
            user_msg = '视频分析失败，请检查视频是否完整、格式是否正确.'
            error_trace = traceback.format_exc()

            self.update_task(task_id, {
                'status': 'failed',
                'message': user_msg,
                'completed_at': datetime.now().isoformat(),
                'error': {
                    'message': error_msg,
                    'user_message': user_msg,
                    'trace': error_trace,
                    'type': 'UnexpectedError'
                }
            })

            print(f"任务 {task_id} 失败:")
            print(error_trace)

    def update_task(self, task_id: str, updates: dict):
        """
        更新任务信息

        Args:
            task_id: 任务ID
            updates: 更新的字段
        """
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].update(updates)

    def get_task(self, task_id: str) -> Optional[dict]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，如果不存在返回None
        """
        with self.lock:
            return self.tasks.get(task_id)

    def get_all_tasks(self) -> list:
        """
        获取所有任务列表

        Returns:
            任务列表
        """
        with self.lock:
            return list(self.tasks.values())

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
            return False

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        清理旧任务

        Args:
            max_age_hours: 最大保留时间（小时）
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with self.lock:
            tasks_to_delete = []
            for task_id, task in self.tasks.items():
                created_at = datetime.fromisoformat(task['created_at'])
                if created_at < cutoff_time and task['status'] in ['completed', 'failed']:
                    tasks_to_delete.append(task_id)

            for task_id in tasks_to_delete:
                del self.tasks[task_id]

            return len(tasks_to_delete)


# 全局任务管理器实例
task_manager = TaskManager()
