"""
用户认证API - 游客模式
基于设备ID的简单用户识别系统
"""
from flask import Blueprint, request, jsonify, current_app
import os
import json
from datetime import datetime
import glob

auth_bp = Blueprint('auth', __name__)


def get_device_id():
    """从请求头或参数中获取设备ID"""
    # 优先从请求头获取
    device_id = request.headers.get('X-Device-ID')
    
    # 如果请求头没有，尝试从查询参数获取
    if not device_id:
        device_id = request.args.get('device_id')
    
    # 如果是POST请求，尝试从body获取
    if not device_id and request.is_json:
        device_id = request.json.get('device_id')
    
    return device_id


def get_user_folder(device_id, folder_type='upload'):
    """
    获取用户文件夹路径
    
    Args:
        device_id: 设备ID
        folder_type: 文件夹类型 ('upload' 或 'output')
    
    Returns:
        用户文件夹的绝对路径
    """
    if folder_type == 'upload':
        base_folder = current_app.config['UPLOAD_FOLDER']
    else:
        base_folder = current_app.config['OUTPUT_FOLDER']
    
    user_folder = os.path.join(base_folder, device_id)
    return user_folder


def ensure_user_folder(device_id):
    """确保用户文件夹存在"""
    upload_folder = get_user_folder(device_id, 'upload')
    output_folder = get_user_folder(device_id, 'output')
    
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    return upload_folder, output_folder


@auth_bp.route('/auth/verify', methods=['POST'])
def verify_device():
    """
    验证设备ID
    
    请求体：
        {
            "device_id": "guest_xxx"
        }
    
    响应：
        {
            "code": 200,
            "message": "设备验证成功",
            "data": {
                "device_id": "guest_xxx",
                "is_new": false,
                "upload_count": 5,
                "analysis_count": 3
            }
        }
    """
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({
                'code': 400,
                'message': '缺少设备ID'
            }), 400
        
        # 检查是否是新用户
        upload_folder = get_user_folder(device_id, 'upload')
        is_new = not os.path.exists(upload_folder)
        
        # 创建用户文件夹
        ensure_user_folder(device_id)
        
        # 统计用户数据
        upload_count = 0
        analysis_count = 0
        
        if not is_new:
            # 统计上传的视频数量
            upload_folder = get_user_folder(device_id, 'upload')
            if os.path.exists(upload_folder):
                upload_count = len([f for f in os.listdir(upload_folder) 
                                   if f.endswith(('.mp4', '.avi', '.mov'))])
            
            # 统计分析报告数量
            output_folder = get_user_folder(device_id, 'output')
            basketball_folder = os.path.join(output_folder, 'basketball')
            if os.path.exists(basketball_folder):
                analysis_count = len([d for d in os.listdir(basketball_folder) 
                                     if os.path.isdir(os.path.join(basketball_folder, d)) 
                                     and d.startswith('analysis_')])
        
        return jsonify({
            'code': 200,
            'message': '设备验证成功' if not is_new else '欢迎新用户',
            'data': {
                'device_id': device_id,
                'is_new': is_new,
                'upload_count': upload_count,
                'analysis_count': analysis_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'验证失败: {str(e)}'
        }), 500


@auth_bp.route('/auth/history', methods=['GET'])
def get_user_history():
    """
    获取用户历史记录
    
    查询参数：
        device_id: 设备ID
    
    响应：
        {
            "code": 200,
            "data": {
                "uploads": [...],
                "analyses": [...]
            }
        }
    """
    try:
        device_id = get_device_id()
        
        if not device_id:
            return jsonify({
                'code': 400,
                'message': '缺少设备ID'
            }), 400
        
        # 获取上传记录
        uploads = []
        upload_folder = get_user_folder(device_id, 'upload')
        
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.endswith(('.mp4', '.avi', '.mov')):
                    file_path = os.path.join(upload_folder, filename)
                    file_stat = os.stat(file_path)
                    
                    uploads.append({
                        'filename': filename,
                        'size': file_stat.st_size,
                        'upload_time': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        'file_path': file_path
                    })
        
        # 按上传时间倒序排列
        uploads.sort(key=lambda x: x['upload_time'], reverse=True)
        
        # 获取分析记录
        analyses = []
        output_folder = get_user_folder(device_id, 'output')
        basketball_folder = os.path.join(output_folder, 'basketball')
        
        if os.path.exists(basketball_folder):
            for analysis_dir in os.listdir(basketball_folder):
                # 支持所有分析目录（包括自定义名称的）
                analysis_path = os.path.join(basketball_folder, analysis_dir)
                
                if os.path.isdir(analysis_path) and not analysis_dir.startswith('comparison'):
                    # 读取分析元数据
                    metadata_file = os.path.join(analysis_path, 'metadata.json')
                    metadata = {}
                    
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        except:
                            pass
                    
                    # 查找报告文件
                    reports_dir = os.path.join(analysis_path, 'reports')
                    report_file = None
                    comparison_file = None
                    
                    if os.path.exists(reports_dir):
                        report_files = glob.glob(os.path.join(reports_dir, 'basketball_*_report.html'))
                        report_file = report_files[0] if report_files else None
                        
                        comparison_files = glob.glob(os.path.join(reports_dir, 'keyframe_comparison_*.html'))
                        comparison_file = comparison_files[0] if comparison_files else None
                    
                    analyses.append({
                        'analysis_id': analysis_dir,
                        'analysis_name': metadata.get('analysis_name', ''),
                        'analysis_time': metadata.get('analysis_time', 
                                       datetime.fromtimestamp(os.path.getctime(analysis_path)).isoformat()),
                        'video_file': metadata.get('video_file', ''),
                        'sport_type': metadata.get('sport_type', 'basketball'),
                        'report_file': report_file,
                        'comparison_file': comparison_file,
                        'metadata': metadata
                    })
        
        # 按分析时间倒序排列
        analyses.sort(key=lambda x: x['analysis_time'], reverse=True)
        
        return jsonify({
            'code': 200,
            'message': '获取历史记录成功',
            'data': {
                'device_id': device_id,
                'uploads': uploads,
                'analyses': analyses,
                'total_uploads': len(uploads),
                'total_analyses': len(analyses)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取历史记录失败: {str(e)}'
        }), 500


@auth_bp.route('/auth/stats', methods=['GET'])
def get_user_stats():
    """
    获取用户统计信息
    
    查询参数：
        device_id: 设备ID
    
    响应：
        {
            "code": 200,
            "data": {
                "total_uploads": 10,
                "total_analyses": 8,
                "storage_used": "125.5 MB",
                "first_use": "2025-10-15",
                "last_use": "2025-10-15"
            }
        }
    """
    try:
        device_id = get_device_id()
        
        if not device_id:
            return jsonify({
                'code': 400,
                'message': '缺少设备ID'
            }), 400
        
        upload_folder = get_user_folder(device_id, 'upload')
        output_folder = get_user_folder(device_id, 'output')
        
        # 统计存储空间
        total_size = 0
        first_time = None
        last_time = None
        
        for folder in [upload_folder, output_folder]:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_stat = os.stat(file_path)
                        total_size += file_stat.st_size
                        
                        file_time = datetime.fromtimestamp(file_stat.st_ctime)
                        if first_time is None or file_time < first_time:
                            first_time = file_time
                        if last_time is None or file_time > last_time:
                            last_time = file_time
        
        # 格式化存储空间
        if total_size < 1024:
            storage_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            storage_str = f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            storage_str = f"{total_size / (1024 * 1024):.1f} MB"
        else:
            storage_str = f"{total_size / (1024 * 1024 * 1024):.1f} GB"
        
        # 统计数量
        upload_count = len([f for f in os.listdir(upload_folder) 
                           if f.endswith(('.mp4', '.avi', '.mov'))]) if os.path.exists(upload_folder) else 0
        
        basketball_folder = os.path.join(output_folder, 'basketball')
        analysis_count = len([d for d in os.listdir(basketball_folder) 
                             if os.path.isdir(os.path.join(basketball_folder, d)) 
                             and d.startswith('analysis_')]) if os.path.exists(basketball_folder) else 0
        
        return jsonify({
            'code': 200,
            'message': '获取统计信息成功',
            'data': {
                'device_id': device_id,
                'total_uploads': upload_count,
                'total_analyses': analysis_count,
                'storage_used': storage_str,
                'storage_bytes': total_size,
                'first_use': first_time.isoformat() if first_time else None,
                'last_use': last_time.isoformat() if last_time else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500
