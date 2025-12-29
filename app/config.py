# config.py
import os


class Config:
    """应用配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///annotation.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt'}
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    
    # 词性标注映射（jieba词性 -> 中文名称和颜色）
    POS_MAPPING = {
        # 名词类
        'n': ('名词', 'primary'),
        'nr': ('人名', 'primary'),
        'ns': ('地名', 'primary'),
        'nt': ('机构名', 'primary'),
        'nz': ('其他专名', 'primary'),
        'nl': ('名词性惯用语', 'primary'),
        'ng': ('名词性语素', 'primary'),
        
        # 动词类
        'v': ('动词', 'success'),
        'vd': ('副动词', 'success'),
        'vn': ('名动词', 'success'),
        'vg': ('动词性语素', 'success'),
        
        # 形容词类
        'a': ('形容词', 'warning'),
        'ad': ('副形词', 'warning'),
        'an': ('名形词', 'warning'),
        'ag': ('形容词性语素', 'warning'),
        
        # 副词类
        'd': ('副词', 'info'),
        'df': ('副词', 'info'),
        'dg': ('副词性语素', 'info'),
        
        # 数词和量词
        'm': ('数词', 'danger'),
        'mq': ('数量词', 'danger'),
        'q': ('量词', 'secondary'),
        'qv': ('动量词', 'secondary'),
        'qt': ('时量词', 'secondary'),
        
        # 代词
        'r': ('代词', 'dark'),
        'rr': ('人称代词', 'dark'),
        'rz': ('指示代词', 'dark'),
        'rzt': ('时间指示代词', 'dark'),
        'rzs': ('处所指示代词', 'dark'),
        'rzv': ('谓词性指示代词', 'dark'),
        
        # 时间词
        't': ('时间词', 'primary'),
        'tg': ('时间词性语素', 'primary'),
        
        # 介词、连词、助词
        'p': ('介词', 'secondary'),
        'c': ('连词', 'secondary'),
        'cc': ('并列连词', 'secondary'),
        'u': ('助词', 'secondary'),
        'uzhe': ('着', 'secondary'),
        'ule': ('了', 'secondary'),
        'uguo': ('过', 'secondary'),
        'ude1': ('的', 'secondary'),
        'ude2': ('地', 'secondary'),
        'ude3': ('得', 'secondary'),
        'usuo': ('所', 'secondary'),
        'udeng': ('等', 'secondary'),
        'uyy': ('一样', 'secondary'),
        'udh': ('的话', 'secondary'),
        'uls': ('来说', 'secondary'),
        'uzhi': ('之', 'secondary'),
        'ulian': ('连', 'secondary'),
        
        # 标点符号
        'w': ('标点', 'light'),
        'wkz': ('左括号', 'light'),
        'wky': ('右括号', 'light'),
        'wyz': ('左引号', 'light'),
        'wyy': ('右引号', 'light'),
        'wj': ('句号', 'light'),
        'ww': ('问号', 'light'),
        'wt': ('叹号', 'light'),
        'wd': ('逗号', 'light'),
        'wf': ('分号', 'light'),
        'wn': ('顿号', 'light'),
        'wm': ('冒号', 'light'),
        'ws': ('省略号', 'light'),
        'wp': ('破折号', 'light'),
        'wb': ('百分号千分号', 'light'),
        'wh': ('单位符号', 'light'),
        
        # 其他
        'x': ('字符串', 'secondary'),
        'xx': ('非语素字', 'secondary'),
        'xu': ('网址URL', 'secondary'),
        'e': ('叹词', 'secondary'),
        'y': ('语气词', 'secondary'),
        'o': ('拟声词', 'secondary'),
        'h': ('前缀', 'secondary'),
        'k': ('后缀', 'secondary'),
        'f': ('方位词', 'info'),
        's': ('处所词', 'info'),
        'i': ('成语', 'warning'),
        'l': ('习用语', 'warning'),
        'j': ('简称', 'primary'),
        'b': ('区别词', 'secondary'),
        'g': ('语素', 'secondary'),
        'z': ('状态词', 'info'),
        'eng': ('英文', 'secondary'),
    }
    
    # 文本分类关键词（用于智能分类）
    CATEGORY_KEYWORDS = {
        '新闻报道': ['报道', '消息', '记者', '采访', '发布', '通讯', '新华社', '本报讯'],
        '科技文章': ['技术', '科学', '研究', '实验', '数据', '算法', '系统', '开发', '创新'],
        '商业文档': ['公司', '企业', '市场', '销售', '业务', '合同', '协议', '投资', '股份'],
        '学术论文': ['摘要', '关键词', '引言', '方法', '结果', '讨论', '参考文献', '研究'],
        '法律文书': ['法院', '判决', '原告', '被告', '法律', '条款', '诉讼', '裁定'],
        '医疗健康': ['患者', '医生', '治疗', '诊断', '症状', '药物', '医院', '疾病'],
        '教育培训': ['学生', '教师', '课程', '学习', '教育', '培训', '考试', '学校'],
        '文学作品': ['小说', '诗歌', '散文', '故事', '人物', '情节', '描写'],
        '社交媒体': ['转发', '评论', '点赞', '分享', '话题', '@', '#'],
        '产品评论': ['购买', '使用', '质量', '价格', '推荐', '好评', '差评', '体验'],
    }
    
    # 命名实体类型配置（只保留5种）
    ENTITY_TYPES = [
        {'value': '人名', 'label': '👤 人名', 'color': '#3B82F6'},
        {'value': '地名', 'label': '📍 地名', 'color': '#10B981'},
        {'value': '组织机构', 'label': '🏢 组织机构', 'color': '#F59E0B'},
        {'value': '时间日期', 'label': '📅 时间日期', 'color': '#8B5CF6'},
        {'value': '数值金额', 'label': '💲 数值金额', 'color': '#EF4444'},
    ]
    
    # 情感分析阈值
    SENTIMENT_THRESHOLDS = {
        'positive': 0.65,  # 大于此值为积极
        'negative': 0.35,  # 小于此值为消极
    }
    
    # 文本分类选项
    TEXT_CATEGORIES = [
        '新闻报道', '科技文章', '商业文档', '学术论文', 
        '法律文书', '医疗健康', '教育培训', '文学作品', 
        '社交媒体', '产品评论', '其他'
    ]
    
    # 情感分析选项
    SENTIMENT_OPTIONS = ['积极', '中性', '消极']
    
    # 知识库配置
    KNOWLEDGE_BASE_AUTO_LEARN = True  # 是否自动学习到知识库
    KNOWLEDGE_BASE_MIN_FREQUENCY = 2  # 最小出现频率才加入知识库
    
    # 导出配置
    EXPORT_FORMATS = ['json', 'csv', 'txt']
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # 是否打印SQL语句


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # 生产环境应该使用环境变量设置这些值
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """获取配置对象"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, DevelopmentConfig)