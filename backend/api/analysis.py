"""
视频分析API
"""
from flask import Blueprint, request, jsonify, current_app, send_from_directory
import os
import json

from services.task_manager import task_manager
from services.analysis_service import analysis_service
from .auth import get_device_id

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/analysis/start', methods=['POST'])
def start_analysis():
    """
    开始分析任务

    请求体：
        {
            "file_id": "uuid",
            "file_path": "/path/to/video.mp4",
            "device_id": "guest_xxx",
            "options": {
                "frame_interval": 5,
                "sport_type": "basketball"
            }
        }

    响应：
        {
            "code": 200,
            "message": "分析任务已创建",
            "data": {
                "task_id": "task-uuid",
                "status": "pending"
            }
        }
    """
    try:
        data = request.get_json()
        
        # 获取设备ID
        device_id = get_device_id()
        if not device_id:
            return jsonify({
                'code': 401,
                'message': '缺少设备ID，请先验证设备'
            }), 401

        # 验证参数
        file_path = data.get('file_path')
        if not file_path:
            return jsonify({
                'code': 400,
                'message': '缺少参数: file_path'
            }), 400

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({
                'code': 404,
                'message': '视频文件不存在'
            }), 404

        # 获取分析选项，并添加device_id
        options = data.get('options', {})
        options['device_id'] = device_id

        # 创建分析任务
        def analysis_callback(video_path, opts, progress_cb):
            return analysis_service.analyze_video(video_path, opts, progress_cb)

        task_id = task_manager.create_task(
            video_path=file_path,
            options=options,
            callback=analysis_callback
        )

        return jsonify({
            'code': 200,
            'message': '分析任务已创建',
            'data': {
                'task_id': task_id,
                'status': 'pending',
                'device_id': device_id
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'创建分析任务失败: {str(e)}'
        }), 500


@analysis_bp.route('/analysis/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    查询任务状态

    响应：
        {
            "code": 200,
            "data": {
                "task_id": "task-uuid",
                "status": "processing",
                "progress": 45,
                "message": "正在分析第 23/50 帧",
                "result": null  // 完成后包含结果
            }
        }
    """
    try:
        task = task_manager.get_task(task_id)

        if not task:
            return jsonify({
                'code': 404,
                'message': '任务不存在'
            }), 404

        # 返回任务信息（不包含完整结果，避免数据量过大）
        response_data = {
            'task_id': task['task_id'],
            'status': task['status'],
            'progress': task['progress'],
            'message': task['message'],
            'created_at': task['created_at'],
            'started_at': task['started_at'],
            'completed_at': task['completed_at']
        }

        # 如果任务完成，返回analysis_id
        if task['status'] == 'completed' and task['result']:
            response_data['analysis_id'] = task['result'].get('analysis_id')

        # 如果任务失败，返回错误信息
        if task['status'] == 'failed' and task['error']:
            response_data['error'] = task['error']['message']

        return jsonify({
            'code': 200,
            'data': response_data
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'查询任务状态失败: {str(e)}'
        }), 500


@analysis_bp.route('/analysis/result/<analysis_id>', methods=['GET'])
def get_analysis_result(analysis_id):
    """
    获取分析结果

    查询参数：
        sport_type: 运动类型（默认basketball）
        device_id: 设备ID

    响应：
        {
            "code": 200,
            "data": {
                "analysis_id": "analysis_20251014_110258",
                "video_info": {...},
                "keyframes": [...],
                "analysis_results": {...}
            }
        }
    """
    try:
        # 获取设备ID
        device_id = get_device_id()
        if not device_id:
            return jsonify({
                'code': 401,
                'message': '缺少设备ID，请先验证设备'
            }), 401
        
        sport_type = request.args.get('sport_type', 'basketball')

        result = analysis_service.get_analysis_result(analysis_id, sport_type, device_id)

        return jsonify({
            'code': 200,
            'data': result
        })

    except FileNotFoundError as e:
        return jsonify({
            'code': 404,
            'message': str(e)
        }), 404

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取分析结果失败: {str(e)}'
        }), 500


@analysis_bp.route('/analysis/list', methods=['GET'])
def list_analyses():
    """
    获取分析历史列表

    响应：
        {
            "code": 200,
            "data": [
                {
                    "analysis_id": "analysis_20251014_110258",
                    "timestamp": "20251014_110258",
                    "video_info": {...},
                    "keyframe_count": 10
                }
            ]
        }
    """
    try:
        sport_type = request.args.get('sport_type', 'basketball')

        analyses = analysis_service.list_analyses(sport_type)

        return jsonify({
            'code': 200,
            'data': analyses
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取分析列表失败: {str(e)}'
        }), 500


@analysis_bp.route('/analysis/tasks', methods=['GET'])
def list_tasks():
    """
    获取所有任务列表

    响应：
        {
            "code": 200,
            "data": [...]
        }
    """
    try:
        tasks = task_manager.get_all_tasks()

        # 简化任务信息
        simplified_tasks = []
        for task in tasks:
            simplified_tasks.append({
                'task_id': task['task_id'],
                'status': task['status'],
                'progress': task['progress'],
                'message': task['message'],
                'created_at': task['created_at']
            })

        return jsonify({
            'code': 200,
            'data': simplified_tasks
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取任务列表失败: {str(e)}'
        }), 500


@analysis_bp.route('/analysis/demo/curry', methods=['GET'])
def get_curry_demo():
    """
    获取库里投篮示例分析数据
    
    响应：
        {
            "code": 200,
            "data": {
                "analysis_id": "curry_demo",
                "video_path": "/star_report/curry/reports/79ffbe93-c341-457a-b9df-c621824ad7e2.mp4",
                "keyframes": [...],
                "frames": [...],
                ...
            }
        }
    """
    try:
        # 从public/star_report/curry读取分析数据
        frontend_public = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'public')
        curry_data_path = os.path.join(frontend_public, 'star_report', 'curry', 'data', 'complete_data.json')
        
        if not os.path.exists(curry_data_path):
            return jsonify({
                'code': 404,
                'message': '示例数据不存在'
            }), 404
        
        # 读取数据
        with open(curry_data_path, 'r', encoding='utf-8') as f:
            demo_data = json.load(f)
        
        # 添加特殊标识
        demo_data['analysis_id'] = 'curry_demo'
        demo_data['is_demo'] = True
        demo_data['title'] = '斯蒂芬·库里 投篮动作分析'
        demo_data['description'] = 'NBA历史最伟大射手之一的投篮动作分析示例'
        
        # 修改路径为前端可访问的路径
        if 'video_info' in demo_data and 'path' in demo_data['video_info']:
            demo_data['video_info']['path'] = '/star_report/curry/reports/79ffbe93-c341-457a-b9df-c621824ad7e2.mp4'
        
        return jsonify({
            'code': 200,
            'data': demo_data
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取示例数据失败: {str(e)}'
        }), 500

