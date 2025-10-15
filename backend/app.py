"""
AIMotionMind Web API
Flask 后端应用入口
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# 导入API蓝图
from api.upload import upload_bp
from api.analysis import analysis_bp
from api.files import files_bp

# 导入配置
from config_backend import Config


def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 启用CORS（跨域资源共享）
    CORS(app, resources={
        r"/api/*": {
            # Vite默认端口
            "origins": ["http://localhost:5173", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 创建必要的目录
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    # 注册蓝图
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(analysis_bp, url_prefix='/api')
    app.register_blueprint(files_bp, url_prefix='/api')

    # 健康检查接口
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查"""
        return jsonify({
            'status': 'ok',
            'message': 'AIMotionMind API is running',
            'timestamp': datetime.now().isoformat()
        })

    # 统一错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'code': 404, 'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'code': 500, 'message': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("🏀 AIMotionMind Web API Server")
    print("=" * 60)
    print(f"🚀 Running on: http://localhost:5000")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📁 Output folder: {app.config['OUTPUT_FOLDER']}")
    print("=" * 60)
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
