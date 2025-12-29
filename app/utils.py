# app/utils.py
import jieba.posseg as pseg
from snownlp import SnowNLP
from flask import current_app
from app import db
from app.models import KnowledgeEntity

# 统一的12种词性
POS_12 = {
    'n': '名词', 'v': '动词', 'a': '形容词', 'd': '副词',
    'm': '数词', 'q': '量词', 'r': '代词', 't': '时间词',
    'p': '介词', 'c': '连词', 'u': '助词', 'w': '标点'
}

def map_pos_to_12(flag):
    """将jieba词性映射到12种标准词性"""
    if not flag:
        return 'n', '名词'
    
    first = flag[0].lower()
    if first in POS_12:
        return first, POS_12[first]
    
    # 映射规则
    mapping = {
        'n': 'n', 'v': 'v', 'a': 'a', 'd': 'd',
        'm': 'm', 'q': 'q', 'r': 'r', 't': 't',
        'p': 'p', 'c': 'c', 'u': 'u', 'w': 'w',
        'x': 'n', 'e': 'u', 'y': 'u', 'o': 'u',
        'h': 'u', 'k': 'u', 'f': 'n', 's': 'n',
        'i': 'n', 'l': 'n', 'j': 'n', 'b': 'a',
        'g': 'u', 'z': 'a'
    }
    
    pos = mapping.get(first, 'n')
    return pos, POS_12[pos]


def get_text_category(content):
    """文本分类"""
    keywords = {
        '新闻时事': ['报道', '消息', '记者', '新华社'],
        '科技数码': ['技术', '科学', '研究', '算法'],
        '财经金融': ['公司', '企业', '市场', '投资'],
        '体育运动': ['比赛', '球队', '运动员', '冠军'],
        '娱乐影视': ['电影', '演员', '导演', '票房'],
        '教育学术': ['学生', '教师', '课程', '学校'],
        '法律法规': ['法院', '判决', '法律', '诉讼'],
        '医疗健康': ['患者', '医生', '治疗', '医院'],
        '生活服务': ['服务', '用户', '体验', '推荐']
    }
    
    scores = {}
    for cat, kws in keywords.items():
        scores[cat] = sum(content.count(kw) for kw in kws)
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else '其他'


def get_sentiment(content):
    """情感分析"""
    try:
        score = SnowNLP(content).sentiments
        if score > 0.65:
            return '积极', score
        elif score < 0.35:
            return '消极', score
        return '中性', score
    except:
        return '中性', 0.5


def segment_text(content):
    """分词（不包含实体识别）"""
    words = list(pseg.cut(content))
    results = []
    
    for word, flag in words:
        pos, pos_cn = map_pos_to_12(flag)
        results.append({
            'word': word,
            'pos': pos,
            'pos_cn': pos_cn
        })
    
    return results


def recognize_entities(content):
    """命名实体识别（独立于分词）"""
    knowledge_dict = get_knowledge_dict()
    entities = []
    
    # 1. 从知识库匹配
    for text, label in knowledge_dict.items():
        start = 0
        while True:
            pos = content.find(text, start)
            if pos == -1:
                break
            entities.append({
                'text': text,
                'label': label,
                'start_pos': pos,
                'end_pos': pos + len(text)
            })
            start = pos + 1
    
    # 2. 基于规则识别
    words = list(pseg.cut(content))
    char_pos = 0
    
    for word, flag in words:
        label = None
        
        if flag.startswith('nr'):
            label = '人名'
        elif flag.startswith('ns'):
            label = '地名'
        elif flag.startswith('nt'):
            label = '组织机构'
        elif flag.startswith('t'):
            label = '时间日期'
        elif flag.startswith('m') and any(c in word for c in ['元', '￥', '$', '万', '亿']):
            label = '数值金额'
        
        if label:
            # 检查是否已存在
            exists = any(e['start_pos'] == char_pos and e['end_pos'] == char_pos + len(word) 
                        for e in entities)
            if not exists:
                entities.append({
                    'text': word,
                    'label': label,
                    'start_pos': char_pos,
                    'end_pos': char_pos + len(word)
                })
        
        char_pos += len(word)
    
    # 去重并排序
    entities = sorted(entities, key=lambda x: x['start_pos'])
    return entities


def get_knowledge_dict():
    """获取知识库"""
    entities = KnowledgeEntity.query.all()
    return {e.text: e.label for e in entities}


def add_to_knowledge_base(text, label, source='manual'):
    """添加到知识库"""
    if not text or label not in ['人名', '地名', '组织机构', '时间日期', '数值金额']:
        return False
    
    existing = KnowledgeEntity.query.filter_by(text=text).first()
    if not existing:
        entity = KnowledgeEntity(text=text, label=label, source=source)
        db.session.add(entity)
        db.session.commit()
        return True
    return False