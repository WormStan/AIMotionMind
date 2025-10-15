"""
后端配置文件
"""
import os
from datetime import timedelta

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """基础配置"""

    # Flask配置
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'backend', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB 最大上传大小
    ALLOWED_EXTENSIONS = {'mp4', 'webm'}

    # 输出目录（复用项目原有的output目录）
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

    # 任务配置
    TASK_TIMEOUT = 600  # 任务超时时间（秒）
    TASK_CHECK_INTERVAL = 1  # 任务状态检查间隔（秒）

    # 分析配置（从原config.py导入）
    FRAME_INTERVAL = 5  # 帧提取间隔

    # CORS配置
    CORS_ORIGINS = [
        'http://localhost:5173',  # Vite开发服务器
        'http://localhost:3000',  # 备用端口
    ]

    @staticmethod
    def allowed_file(filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
