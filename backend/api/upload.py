"""
视频上传API
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import cv2
import json

from config_backend import Config
from .auth import get_device_id, ensure_user_folder, get_user_folder

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/upload', methods=['POST'])
def upload_video():
    """
    上传视频文件

    请求：
        - multipart/form-data
        - file: 视频文件
        - sport_type: 运动类型（可选，默认basketball）
        - device_id: 设备ID（必需）

    响应：
        {
            "code": 200,
            "message": "上传成功",
            "data": {
                "file_id": "uuid",
                "filename": "original_name.mp4",
                "file_path": "/path/to/file",
                "size": 1024000,
                "duration": 5.2,
                "fps": 30,
                "resolution": "1920x1080"
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
        
        # 确保用户文件夹存在
        upload_folder, _ = ensure_user_folder(device_id)
        
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': '没有上传文件'
            }), 400

        file = request.files['file']

        # 检查文件名
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': '文件名为空'
            }), 400

        # 检查文件类型
        if not Config.allowed_file(file.filename):
            return jsonify({
                'code': 400,
                'message': f'不支持的文件类型，仅支持: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400

        # 生成唯一文件ID和文件名
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        filename = f"{file_id}.{file_extension}"

        # 保存文件到用户文件夹
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # 获取视频信息
        video_info = get_video_info(file_path)
        
        # 保存元数据
        metadata = {
            'file_id': file_id,
            'original_filename': original_filename,
            'upload_time': datetime.now().isoformat(),
            'device_id': device_id,
            'sport_type': request.form.get('sport_type', 'basketball'),
            'video_info': video_info
        }
        
        metadata_path = os.path.join(upload_folder, f"{file_id}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 返回结果
        return jsonify({
            'code': 200,
            'message': '上传成功',
            'data': {
                'file_id': file_id,
                'filename': original_filename,
                'file_path': file_path,
                'size': os.path.getsize(file_path),
                'duration': video_info.get('duration', 0),
                'fps': video_info.get('fps', 0),
                'resolution': f"{video_info.get('width', 0)}x{video_info.get('height', 0)}",
                'frame_count': video_info.get('frame_count', 0),
                'device_id': device_id
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'上传失败: {str(e)}'
        }), 500


def get_video_info(video_path):
    """
    获取视频信息

    Args:
        video_path: 视频文件路径

    Returns:
        dict: 视频信息
    """
    try:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return {}

        info = {
            'fps': int(cap.get(cv2.CAP_PROP_FPS)),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }

        # 计算时长
        if info['fps'] > 0:
            info['duration'] = round(info['frame_count'] / info['fps'], 2)
        else:
            info['duration'] = 0

        cap.release()
        return info

    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return {}


@upload_bp.route('/upload/list', methods=['GET'])
def list_uploads():
    """
    获取已上传的文件列表（仅返回当前用户的文件）

    查询参数：
        device_id: 设备ID

    响应：
        {
            "code": 200,
            "data": [
                {
                    "filename": "xxx.mp4",
                    "size": 1024000,
                    "upload_time": "2025-10-14 10:30:00"
                }
            ]
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
        
        # 获取用户上传文件夹
        upload_folder = get_user_folder(device_id, 'upload')
        files = []

        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                # 跳过元数据文件
                if filename.endswith('.json'):
                    continue
                    
                file_path = os.path.join(upload_folder, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    
                    # 尝试读取元数据
                    file_id = filename.rsplit('.', 1)[0]
                    metadata_path = os.path.join(upload_folder, f"{file_id}.json")
                    original_filename = filename
                    
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                original_filename = metadata.get('original_filename', filename)
                        except:
                            pass
                    
                    files.append({
                        'file_id': file_id,
                        'filename': filename,
                        'original_filename': original_filename,
                        'size': stat.st_size,
                        'upload_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'file_path': file_path
                    })

        # 按上传时间倒序排序
        files.sort(key=lambda x: x['upload_time'], reverse=True)

        return jsonify({
            'code': 200,
            'message': '获取文件列表成功',
            'data': {
                'device_id': device_id,
                'files': files,
                'total': len(files)
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取文件列表失败: {str(e)}'
        }), 500
