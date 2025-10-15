"""
文件服务API - 提供静态文件访问
"""
from flask import Blueprint, send_file, current_app, jsonify
import os

files_bp = Blueprint('files', __name__)


@files_bp.route('/files/<file_type>/<path:filename>', methods=['GET'])
def get_file(file_type, filename):
    """
    获取文件

    参数：
        file_type: 文件类型 (upload, frame, keyframe, report)
        filename: 文件路径（可能包含子目录）

    示例：
        /api/files/keyframe/basketball/analysis_20251014_110258/keyframes/keyframe_ball_at_chest.jpg
        /api/files/keyframe/basketball/curry_demo/keyframes/keyframe_release.jpg (示例)
    """
    try:
        # 特殊处理：如果是curry_demo，从frontend/public读取
        if 'curry_demo' in filename:
            frontend_public = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'frontend', 'public'
            )
            # 从filename中提取实际路径
            # 例如: basketball/curry_demo/keyframes/keyframe_xxx.jpg -> star_report/curry/keyframes/keyframe_xxx.jpg
            parts = filename.split('/')
            if len(parts) >= 3:
                # 重构路径: curry_demo/keyframes/... -> star_report/curry/keyframes/...
                curry_path = '/'.join(parts[2:])  # 跳过 basketball/curry_demo
                file_path = os.path.join(frontend_public, 'star_report', 'curry', curry_path)
            else:
                return jsonify({
                    'code': 400,
                    'message': '无效的curry_demo路径'
                }), 400
        else:
            # 根据文件类型确定基础目录
            if file_type == 'upload':
                base_dir = current_app.config['UPLOAD_FOLDER']
            elif file_type in ['frame', 'keyframe', 'report', 'analysis']:
                base_dir = current_app.config['OUTPUT_FOLDER']
            else:
                return jsonify({
                    'code': 400,
                    'message': f'不支持的文件类型: {file_type}'
                }), 400

            # 构建完整文件路径
            file_path = os.path.join(base_dir, filename)

            # 安全检查：防止目录遍历攻击
            file_path = os.path.abspath(file_path)
            base_dir = os.path.abspath(base_dir)

            if not file_path.startswith(base_dir):
                return jsonify({
                    'code': 403,
                    'message': '非法的文件路径'
                }), 403

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({
                'code': 404,
                'message': f'文件不存在: {file_path}'
            }), 404

        # 返回文件
        return send_file(file_path)

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取文件失败: {str(e)}'
        }), 500


@files_bp.route('/files/report/<path:report_path>', methods=['GET'])
def get_report(report_path):
    """
    获取HTML报告

    示例：
        /api/files/report/basketball/analysis_20251014_110258/reports/basketball_analysis_report.html
    """
    try:
        base_dir = current_app.config['OUTPUT_FOLDER']
        file_path = os.path.join(base_dir, report_path)

        # 安全检查
        file_path = os.path.abspath(file_path)
        base_dir = os.path.abspath(base_dir)

        if not file_path.startswith(base_dir):
            return jsonify({
                'code': 403,
                'message': '非法的文件路径'
            }), 403

        if not os.path.exists(file_path):
            return jsonify({
                'code': 404,
                'message': '报告文件不存在'
            }), 404

        return send_file(file_path, mimetype='text/html')

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取报告失败: {str(e)}'
        }), 500
