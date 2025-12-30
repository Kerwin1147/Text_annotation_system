# app/utils.py
import jieba.posseg as pseg
from snownlp import SnowNLP
from flask import current_app
from app import db
from app.models import KnowledgeEntity
import re

# ========== 词性映射 ==========
POS_12 = {
    'n': '名词', 'v': '动词', 'a': '形容词', 'd': '副词',
    'm': '数词', 'q': '量词', 'r': '代词', 't': '时间词',
    'p': '介词', 'c': '连词', 'u': '助词', 'w': '标点'
}

# 标点符号集合
PUNCTUATION_SET = set('，。！？、；：""''【】（）《》〈〉「」『』〔〕…—～·.,!?;:\'\"()[]{}<>@#$%^&*+-=_|\\`~')

# 常见姓氏（扩充）
SURNAMES = '王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾萧田董袁潘蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫雷侯龙段郝孔邵史毛常万顾赖武康贺严钱施牛洪龚聂路古毕于阎柳华邢莫袁汤殷罗倪严傅章丛鲁韦俞翟葛姬费卞管向欧施柴覃辛'

# 常见名字用字（用于识别普通人名）
NAME_CHARS = '伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发武新利清飞彬富顺信子杰涛昌成康星光天达安岩中茂进林有坚和彪博诚先敬震振壮会思群豪心邦承乐绍功松善厚庆磊民友裕河哲江超浩亮政谦亨奇固之轮翰朗伯宏言若鸣朋斌梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德行时泰盛雄琛钧冠策腾楠榕风航弘秀娟英华慧巧美娜静淑惠珠翠雅芝玉萍红娥玲芬芳燕彩春菊兰凤洁梅琳素云莲真环雪荣爱妹霞香月莺媛艳瑞凡佳嘉琼勤珍贞莉桂娣叶璧璐娅琦晶妍茜秋珊莎锦黛青倩婷姣婉娴瑾颖露瑶怡婵雁蓓纨仪荷丹蓉眉君琴蕊薇菁梦岚苑婕馨瑗琰韵融园艺咏卿聪澜纯毓悦昭冰爽琬茗羽希宁欣飘育滢馥筠柔竹霭凝晓欢霄枫芸菲寒伊亚宜可姬舒影荔枝思丽'

# 排除词（这些不是人名）
EXCLUDE_NAMES = {
    '我们', '他们', '她们', '你们', '自己', '本人', '对方', '双方', '各方',
    '有关', '相关', '上述', '所有', '其他', '部分', '全部', '本案', '该案',
    '原因', '结果', '事实', '证据', '法律', '法规', '规定', '条款', '合同',
    '时间', '地点', '方式', '方法', '情况', '问题', '意见', '建议', '要求',
    '银行', '公司', '法院', '政府', '学校', '医院', '单位', '部门', '机构',
    '东西', '南北', '上下', '左右', '前后', '大小', '多少', '高低', '长短',
}


# ========== 文本分类关键词库 ==========
CATEGORY_KEYWORDS = {
    '新闻时事': {
        'keywords': [
            '报道', '消息', '记者', '新华社', '央视', '本报讯', '据悉', '获悉', '采访',
            '发布会', '新闻', '通讯员', '特约记者', '本台', '本网', '本报', '编辑',
            '头条', '快讯', '要闻', '时政', '国际', '国内', '社会', '民生', '舆论',
            '官方', '政府', '声明', '公告', '通报', '发言人', '外交部', '国防部',
            '中央', '国务院', '人大', '政协', '两会', '领导人', '主席', '总理',
            '峰会', '会议', '论坛', '访问', '出访', '会见', '会谈', '签署', '协议',
        ],
        'weight': 1.5
    },
    '科技数码': {
        'keywords': [
            '技术', '科学', '研究', '算法', '人工智能', 'AI', '机器学习', '深度学习',
            '互联网', '软件', '硬件', '芯片', '处理器', 'CPU', 'GPU', '内存', '存储',
            '手机', '电脑', '笔记本', '平板', '智能', '数码', '电子', '设备', '产品',
            '苹果', '华为', '小米', '三星', 'iPhone', '安卓', 'Android', 'iOS',
            '5G', '4G', '网络', '通信', '信号', '基站', '宽带', 'WiFi', '蓝牙',
            '云计算', '大数据', '区块链', '物联网', 'IoT', '虚拟现实', 'VR', 'AR',
            '程序', '代码', '开发', '编程', '工程师', '程序员', '架构', '系统',
            '创新', '发明', '专利', '科研', '实验', '实验室', '研发', '研究院',
        ],
        'weight': 1.3
    },
    '财经金融': {
        'keywords': [
            '公司', '企业', '市场', '投资', '融资', '上市', 'IPO', '股票', '股市',
            '基金', '债券', '证券', '期货', '期权', '外汇', '汇率', '利率',
            '银行', '保险', '信托', '券商', '金融', '资本', '资产', '负债',
            '收入', '利润', '营收', '净利', '毛利', '成本', '费用', '支出',
            '增长', '下跌', '涨幅', '跌幅', '波动', '行情', '走势', '趋势',
            '经济', 'GDP', 'CPI', 'PPI', '通胀', '通货膨胀', '紧缩', '宽松',
            '央行', '货币', '政策', '降息', '加息', '降准', '存款', '贷款',
            '万元', '亿元', '美元', '人民币', '港币', '欧元',
        ],
        'weight': 1.4
    },
    '体育运动': {
        'keywords': [
            '比赛', '球队', '运动员', '冠军', '亚军', '季军', '金牌', '银牌', '铜牌',
            '足球', '篮球', 'NBA', 'CBA', '排球', '乒乓球', '羽毛球', '网球',
            '游泳', '田径', '体操', '跳水', '举重', '射击', '击剑', '拳击',
            '奥运会', '世界杯', '亚运会', '全运会', '锦标赛', '联赛', '杯赛',
            '教练', '主帅', '裁判', '球迷', '观众', '看台', '球场', '赛场',
        ],
        'weight': 1.3
    },
    '娱乐影视': {
        'keywords': [
            '电影', '电视剧', '综艺', '演员', '导演', '票房', '收视率', '播出',
            '明星', '艺人', '歌手', '演唱会', '专辑', '单曲', 'MV', '音乐',
            '颁奖', '奖项', '提名', '获奖', '影帝', '影后', '视帝', '视后',
            '拍摄', '杀青', '上映', '首映', '定档', '预告', '海报', '剧照',
        ],
        'weight': 1.2
    },
    '教育学术': {
        'keywords': [
            '学生', '教师', '老师', '课程', '学校', '大学', '中学', '小学',
            '高考', '中考', '考试', '成绩', '分数', '录取', '招生', '报名',
            '学习', '教育', '培训', '辅导', '补习', '家教', '网课', '在线',
            '论文', '研究', '课题', '项目', '基金', '学术', '学者', '教授',
            '博士', '硕士', '本科', '专科', '学位', '学历', '毕业', '就业',
        ],
        'weight': 1.3
    },
    '法律法规': {
        'keywords': [
            '法院', '判决', '法律', '诉讼', '原告', '被告', '律师', '法官',
            '案件', '案例', '审判', '庭审', '开庭', '上诉', '申诉', '裁定',
            '刑事', '民事', '行政', '犯罪', '违法', '违规', '处罚', '罚款',
            '合同', '协议', '条款', '权利', '义务', '责任', '赔偿', '损失',
            '借款', '欠款', '债务', '债权', '本金', '利息', '借条', '欠条',
            '起诉', '答辩', '证据', '质证', '举证', '判令', '驳回', '支持',
        ],
        'weight': 1.4
    },
    '医疗健康': {
        'keywords': [
            '患者', '医生', '治疗', '医院', '疾病', '症状', '诊断', '检查',
            '手术', '住院', '门诊', '急诊', 'ICU', '护士', '护理', '康复',
            '药物', '药品', '处方', '用药', '服药', '副作用', '不良反应',
            '疫情', '病毒', '细菌', '感染', '传染', '防控', '隔离', '疫苗',
        ],
        'weight': 1.4
    },
    '生活服务': {
        'keywords': [
            '服务', '用户', '体验', '推荐', '评价', '评分', '好评', '差评',
            '购物', '消费', '价格', '优惠', '折扣', '促销', '特价', '秒杀',
            '外卖', '快递', '物流', '配送', '到货', '签收', '退货', '退款',
        ],
        'weight': 1.1
    },
    '其他': {
        'keywords': [],
        'weight': 0.5
    }
}


def is_punctuation_or_whitespace(word):
    """判断是否为标点符号或空白字符"""
    if not word or not word.strip():
        return True, 'whitespace'
    if all(c in PUNCTUATION_SET or c.isspace() for c in word):
        return True, 'punctuation'
    return False, None


def map_pos_to_12(flag, word=None):
    """将jieba词性映射到12种基本词性"""
    if word:
        is_special, special_type = is_punctuation_or_whitespace(word)
        if is_special:
            return 'w', '标点'
    
    if not flag:
        if word and is_punctuation_or_whitespace(word)[0]:
            return 'w', '标点'
        return 'n', '名词'
    
    flag_lower = flag.lower()
    first = flag_lower[0] if flag_lower else 'n'
    
    if first in POS_12:
        return first, POS_12[first]
    
    mapping = {
        'n': 'n', 'v': 'v', 'a': 'a', 'd': 'd',
        'm': 'm', 'q': 'q', 'r': 'r', 't': 't',
        'p': 'p', 'c': 'c', 'u': 'u', 'w': 'w',
        'x': 'w', 'e': 'u', 'y': 'u', 'o': 'u',
        'h': 'u', 'k': 'u', 'f': 'n', 's': 'n',
        'i': 'n', 'l': 'n', 'j': 'n', 'b': 'a',
        'g': 'u', 'z': 'a'
    }
    
    pos = mapping.get(first, 'n')
    return pos, POS_12[pos]


def get_text_category(content):
    """智能文本分类"""
    if not content:
        return '其他'
    
    content_lower = content.lower()
    scores = {}
    
    for category, config in CATEGORY_KEYWORDS.items():
        if category == '其他':
            continue
            
        keywords = config['keywords']
        weight = config.get('weight', 1.0)
        score = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = content_lower.count(keyword_lower)
            if count > 0:
                score += min(count, 5) * weight
                if keyword_lower in content_lower[:100]:
                    score += 2 * weight
        
        scores[category] = score
    
    if not scores or max(scores.values()) == 0:
        return '其他'
    
    best_category = max(scores, key=scores.get)
    
    if scores[best_category] < 3:
        return '其他'
    
    return best_category


def get_sentiment(content):
    """情感分析"""
    try:
        if not content or len(content.strip()) == 0:
            return '中性', 0.5
        score = SnowNLP(content).sentiments
        if score > 0.65:
            return '积极', score
        elif score < 0.35:
            return '消极', score
        return '中性', score
    except:
        return '中性', 0.5


def segment_text(content):
    """分词和词性标注，返回包含位置信息的结果"""
    words = list(pseg.cut(content))
    results = []
    
    current_pos = 0  # 当前字符位置
    
    for word, flag in words:
        if not word.strip():
            # 跳过空白但更新位置
            current_pos += len(word)
            continue
        
        # 查找词语在原文中的实际位置
        actual_pos = content.find(word, current_pos)
        if actual_pos == -1:
            # 如果找不到，使用当前位置
            actual_pos = current_pos
        
        pos, pos_cn = map_pos_to_12(flag, word)
        
        results.append({
            'word': word,
            'pos': pos,
            'pos_cn': pos_cn,
            'start_pos': actual_pos,
            'end_pos': actual_pos + len(word)
        })
        
        # 更新当前位置
        current_pos = actual_pos + len(word)
    
    return results


# ========== 辅助函数 ==========

def check_overlap(new_entity, existing_entities):
    """检查新实体是否与已有实体重叠"""
    for e in existing_entities:
        if not (new_entity['end_pos'] <= e['start_pos'] or new_entity['start_pos'] >= e['end_pos']):
            return True, e
    return False, None


def add_entity_if_no_overlap(entity, entities):
    """如果不重叠则添加实体"""
    overlap, _ = check_overlap(entity, entities)
    if not overlap:
        entities.append(entity)
        return True
    return False


# ========== 实体识别核心算法 ==========

def recognize_time_entities(content):
    """识别时间日期实体"""
    entities = []
    
    time_patterns = [
        r'\d{4}年\d{1,2}月\d{1,2}[日号]',
        r'\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}',
        r'\d{1,2}月\d{1,2}[日号]?[至到\-－]\d{1,2}[日号]',
        r'\d{4}年\d{1,2}月[至到\-－]\d{1,2}月',
        r'\d{4}年\d{1,2}月',
        r'\d{1,2}月\d{1,2}[日号]',
        r'当地时间\d{1,2}[日号]',
        r'当地时间\d{1,2}月\d{1,2}[日号]',
        r'北京时间\d{1,2}[日号]',
        r'北京时间\d{1,2}月\d{1,2}[日号]',
        r'\d{4}年(?:代|初|末|底|中期)?',
        r'公元前?\d{1,4}年',
        r'(?:今|明|昨|前|后|大前|大后)天',
        r'(?:今|明|去|前|后)年',
        r'(?:这|那|本|上|下)个?月',
        r'(?:周|星期)[一二三四五六日天]',
        r'(?:过去|近|未来|今后)\d{1,2}年',
        r'["""]?十[一二三四五六七八九]五["""]?',
    ]
    
    for pattern in time_patterns:
        try:
            for match in re.finditer(pattern, content):
                text = match.group().strip()
                start = match.start()
                end = match.end()
                
                overlap = False
                to_remove = None
                for e in entities:
                    if not (end <= e['start_pos'] or start >= e['end_pos']):
                        if len(text) > len(e['text']):
                            to_remove = e
                        else:
                            overlap = True
                        break
                
                if to_remove:
                    entities.remove(to_remove)
                
                if not overlap and len(text) >= 2:
                    entities.append({
                        'text': text,
                        'label': '时间日期',
                        'start_pos': start,
                        'end_pos': end
                    })
        except re.error:
            continue
    
    return sorted(entities, key=lambda x: x['start_pos'])


def recognize_amount_entities(content):
    """识别数值金额实体"""
    entities = []
    CN_NUM = '[零一二三四五六七八九十百千万亿两]+'
    
    amount_patterns = [
        (r'[¥￥$€£]\s*\d+(?:[,，]\d{3})*(?:\.\d+)?(?:万|亿)?元?', 'money'),
        (r'\d+(?:[,，]\d{3})*(?:\.\d+)?(?:万亿|千亿|百亿|十亿|亿|千万|百万|十万|万|千)?(?:多|余|来|左右)?\s*(?:元|美元|美金|欧元|英镑|日元|港币|人民币)', 'money'),
        (rf'{CN_NUM}(?:多|余|来|左右)?\s*(?:元|块钱|块|美元|欧元|英镑|日元|港币|人民币)', 'money'),
        (r'\d+(?:\.\d+)?[%％]', 'percent'),
        (r'百分之' + CN_NUM, 'percent'),
        (r'\d{2,}(?:\.\d+)?(?:万|千|百)?(?:多|余|来)?\s*(?:亩|公顷|平方米|平方公里|平米|㎡)', 'area'),
        (rf'{CN_NUM}(?:多|余|来)?\s*(?:亩|公顷|平方米|平方公里|平米)', 'area'),
        (r'\d+(?:\.\d+)?(?:万亿|亿|万|千|百)?(?:多|余)?\s*(?:桶|升|毫升|立方米|加仑|吨)', 'volume'),
        (rf'{CN_NUM}(?:多|余)?\s*(?:桶|升|毫升|立方米|加仑|吨)', 'volume'),
        (r'\d+(?:\.\d+)?(?:万|千|百)?(?:多|余)?\s*(?:吨|千克|公斤|斤|克|kg|g)', 'weight'),
        (r'\d+(?:\.\d+)?(?:万|千|百)?(?:多|余)?\s*(?:千米|公里|米|厘米|毫米|km|m)', 'length'),
        (r'\d{2,}(?:\.\d+)?(?:多|余|来|几)?\s*(?:人|位|名|个|只|条|头|支|把|件|套|台|辆|架|艘|座|栋|家|户|所|处|项|笔|批|次|届|倍|股)', 'quantity'),
        (r'\d+(?:万|千|百)(?:多|余|来|几)?\s*(?:人|位|名|个|只|条|头|支|把|件|套|台|辆|架|艘|座|栋|家|户|所|处|项|笔|批|次|届|倍|股)', 'quantity'),
        (rf'{CN_NUM}(?:多|余|来|几)?\s*(?:人|位|名|个|件|套|台|辆|架|艘|座|栋|家|户|所|处|项|笔|批|次|届|倍|股)', 'quantity'),
    ]
    
    for pattern, amt_type in amount_patterns:
        try:
            for match in re.finditer(pattern, content):
                text = match.group().strip()
                start = match.start()
                end = match.end()
                
                if amt_type == 'quantity':
                    if re.match(r'^[1-9]\s*[人位名个只条头支把件套台辆架艘座栋家户所处项笔批次届倍股]$', text):
                        continue
                
                overlap = False
                to_remove = None
                for e in entities:
                    if not (end <= e['start_pos'] or start >= e['end_pos']):
                        if len(text) > len(e['text']):
                            to_remove = e
                        else:
                            overlap = True
                        break
                
                if to_remove:
                    entities.remove(to_remove)
                
                if not overlap and len(text) >= 2:
                    entities.append({
                        'text': text,
                        'label': '数值金额',
                        'start_pos': start,
                        'end_pos': end
                    })
        except re.error:
            continue
    
    return sorted(entities, key=lambda x: x['start_pos'])


def recognize_person_entities(content):
    """识别人名实体"""
    entities = []
    
    # 1. 法律文书中的"某"字人名
    pattern_mou = r'[' + SURNAMES + r']某\d*'
    for match in re.finditer(pattern_mou, content):
        text = match.group()
        start = match.start()
        end = match.end()
        entities.append({
            'text': text,
            'label': '人名',
            'start_pos': start,
            'end_pos': end
        })
    
    # 2. 已知公众人物
    known_persons = [
        '习近平', '李强', '赵乐际', '王沪宁', '蔡奇', '丁薛祥', '李希',
        '卢拉', '特朗普', '拜登', '普京', '马克龙', '岸田文雄', '莫迪',
        '马斯克', '比尔盖茨', '扎克伯格', '贝索斯', '马云', '马化腾',
        '任正非', '雷军', '刘强东', '李彦宏', '张一鸣',
    ]
    for person in known_persons:
        for match in re.finditer(re.escape(person), content):
            overlap, _ = check_overlap({
                'start_pos': match.start(),
                'end_pos': match.end()
            }, entities)
            if not overlap:
                entities.append({
                    'text': person,
                    'label': '人名',
                    'start_pos': match.start(),
                    'end_pos': match.end()
                })
    
    # 3. 姓+两个字的名
    pattern_3char = r'[' + SURNAMES + r'][' + NAME_CHARS + r']{2}'
    for match in re.finditer(pattern_3char, content):
        text = match.group()
        start = match.start()
        end = match.end()
        
        if text in EXCLUDE_NAMES:
            continue
        
        overlap, _ = check_overlap({'start_pos': start, 'end_pos': end}, entities)
        
        if not overlap:
            if start > 0 and content[start-1] in NAME_CHARS:
                continue
            if end < len(content) and content[end] in NAME_CHARS:
                continue
            
            entities.append({
                'text': text,
                'label': '人名',
                'start_pos': start,
                'end_pos': end
            })
    
    # 4. 姓+单字名（需要更严格的上下文判断）
    pattern_2char = r'[' + SURNAMES + r'][' + NAME_CHARS + r']'
    name_indicators_before = [
        '原告', '被告', '证人', '当事人', '代理人', '委托人',
        '被害人', '嫌疑人', '犯罪嫌疑人', '被申请人', '申请人',
        '先生', '女士', '同志', '老师', '教授', '医生', '律师',
        '经理', '总裁', '董事', '主任', '部长', '局长', '处长',
        '向', '给', '找', '问', '叫', '是', '为', '即', '系', '名叫',
    ]
    
    for match in re.finditer(pattern_2char, content):
        text = match.group()
        start = match.start()
        end = match.end()
        
        if text in EXCLUDE_NAMES:
            continue
        
        overlap, _ = check_overlap({'start_pos': start, 'end_pos': end}, entities)
        
        if overlap:
            continue
        
        if start > 0 and content[start-1] in NAME_CHARS + SURNAMES:
            continue
        if end < len(content) and content[end] in NAME_CHARS:
            continue
        
        has_indicator = False
        prefix = content[max(0, start-5):start]
        for indicator in name_indicators_before:
            if indicator in prefix:
                has_indicator = True
                break
        
        suffix = content[end:min(len(content), end+3)]
        name_indicators_after = ['说', '称', '表示', '认为', '指出', '强调', '介绍', '告诉', '回忆']
        for indicator in name_indicators_after:
            if suffix.startswith(indicator):
                has_indicator = True
                break
        
        if has_indicator:
            entities.append({
                'text': text,
                'label': '人名',
                'start_pos': start,
                'end_pos': end
            })
    
    return sorted(entities, key=lambda x: x['start_pos'])


def recognize_location_entities(content):
    """识别地名实体"""
    entities = []
    
    # 中国省级行政区
    provinces = [
        '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
        '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
        '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
        '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门',
    ]
    
    # 主要城市
    cities = [
        '石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德',
        '太原', '大同', '沈阳', '大连', '鞍山', '长春', '吉林市', '哈尔滨',
        '南京', '苏州', '无锡', '常州', '徐州', '杭州', '宁波', '温州', '嘉兴',
        '合肥', '芜湖', '福州', '厦门', '泉州', '南昌', '济南', '青岛', '烟台',
        '郑州', '洛阳', '武汉', '宜昌', '长沙', '株洲', '广州', '深圳', '珠海',
        '东莞', '佛山', '中山', '惠州', '海口', '三亚', '成都', '绵阳', '贵阳',
        '昆明', '西安', '咸阳', '兰州', '西宁', '银川', '乌鲁木齐', '拉萨',
        '呼和浩特', '包头', '南宁', '桂林', '柳州',
    ]
    
    # 国际地名
    international = [
        '美国', '英国', '法国', '德国', '日本', '韩国', '俄罗斯', '加拿大',
        '澳大利亚', '新西兰', '印度', '巴西', '墨西哥', '阿根廷', '南非',
        '埃及', '沙特', '伊朗', '伊拉克', '以色列', '土耳其', '泰国', '越南',
        '新加坡', '马来西亚', '印尼', '菲律宾', '意大利', '西班牙', '葡萄牙',
        '荷兰', '比利时', '瑞士', '瑞典', '挪威', '丹麦', '芬兰', '波兰',
        '乌克兰', '希腊', '奥地利', '捷克', '匈牙利', '罗马尼亚',
        '纽约', '华盛顿', '洛杉矶', '旧金山', '芝加哥', '波士顿', '西雅图',
        '伦敦', '巴黎', '柏林', '罗马', '马德里', '阿姆斯特丹', '布鲁塞尔',
        '东京', '大阪', '京都', '首尔', '釜山', '莫斯科', '悉尼', '墨尔本',
        '多伦多', '温哥华', '迪拜', '新德里', '孟买', '曼谷', '河内', '雅加达',
    ]
    
    all_locations = provinces + cities + international
    
    for loc in all_locations:
        for match in re.finditer(re.escape(loc), content):
            overlap, _ = check_overlap({
                'start_pos': match.start(),
                'end_pos': match.end()
            }, entities)
            if not overlap:
                entities.append({
                    'text': loc,
                    'label': '地名',
                    'start_pos': match.start(),
                    'end_pos': match.end()
                })
    
    # 地名模式匹配
    location_patterns = [
        r'[^\s，。！？、；：""'']{2,6}(?:省|市|县|区|镇|乡|村|街道|路|街|巷|弄|号|大道|广场|公园|医院|学校|大学|学院|中学|小学|幼儿园)',
        r'[^\s，。！？、；：""'']{2,4}(?:机场|火车站|汽车站|地铁站|港口|码头|高速|国道|省道)',
    ]
    
    for pattern in location_patterns:
        try:
            for match in re.finditer(pattern, content):
                text = match.group().strip()
                start = match.start()
                end = match.end()
                
                # 过滤无效结果
                if len(text) < 3 or len(text) > 15:
                    continue
                
                overlap, existing = check_overlap({
                    'start_pos': start,
                    'end_pos': end
                }, entities)
                
                if overlap:
                    if existing and len(text) > len(existing['text']):
                        entities.remove(existing)
                        entities.append({
                            'text': text,
                            'label': '地名',
                            'start_pos': start,
                            'end_pos': end
                        })
                else:
                    entities.append({
                        'text': text,
                        'label': '地名',
                        'start_pos': start,
                        'end_pos': end
                    })
        except re.error:
            continue
    
    return sorted(entities, key=lambda x: x['start_pos'])


def recognize_organization_entities(content):
    """识别组织机构实体"""
    entities = []
    
    # 知名组织机构
    known_orgs = [
        '中国共产党', '国务院', '全国人大', '全国政协', '中央军委',
        '最高人民法院', '最高人民检察院', '中国人民银行', '外交部', '国防部',
        '发改委', '教育部', '科技部', '工信部', '公安部', '财政部', '商务部',
        '联合国', '世界卫生组织', '世贸组织', '国际货币基金组织', '世界银行',
        '欧盟', '东盟', '北约', '亚投行', '金砖国家',
        '阿里巴巴', '腾讯', '百度', '京东', '华为', '小米', '字节跳动', '美团',
        '苹果公司', '谷歌', '微软', '亚马逊', '特斯拉', '脸书', '推特',
        '清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学',
        '中国科学院', '中国工程院', '中国社会科学院',
        '新华社', '人民日报', '中央电视台', 'CCTV', '央视',
    ]
    
    for org in known_orgs:
        for match in re.finditer(re.escape(org), content):
            overlap, _ = check_overlap({
                'start_pos': match.start(),
                'end_pos': match.end()
            }, entities)
            if not overlap:
                entities.append({
                    'text': org,
                    'label': '组织机构',
                    'start_pos': match.start(),
                    'end_pos': match.end()
                })
    
    # 组织机构模式
    org_patterns = [
        r'[^\s，。！？、；：""'']{2,10}(?:公司|集团|企业|银行|保险|证券|基金|信托)',
        r'[^\s，。！？、；：""'']{2,8}(?:大学|学院|中学|小学|学校|研究院|研究所|实验室)',
        r'[^\s，。！？、；：""'']{2,8}(?:医院|诊所|卫生院|疾控中心)',
        r'[^\s，。！？、；：""'']{2,8}(?:法院|检察院|公安局|派出所|司法局)',
        r'[^\s，。！？、；：""'']{2,8}(?:政府|党委|人大|政协|纪委|组织部|宣传部)',
        r'[^\s，。！？、；：""'']{2,8}(?:局|厅|部|委|办|处|科|股|室)',
        r'[^\s，。！？、；：""'']{2,8}(?:协会|学会|联合会|商会|基金会|促进会)',
        r'[^\s，。！？、；：""'']{2,6}(?:有限公司|股份有限公司|责任公司)',
    ]
    
    for pattern in org_patterns:
        try:
            for match in re.finditer(pattern, content):
                text = match.group().strip()
                start = match.start()
                end = match.end()
                
                if len(text) < 4 or len(text) > 20:
                    continue
                
                overlap, existing = check_overlap({
                    'start_pos': start,
                    'end_pos': end
                }, entities)
                
                if overlap:
                    if existing and len(text) > len(existing['text']):
                        entities.remove(existing)
                        entities.append({
                            'text': text,
                            'label': '组织机构',
                            'start_pos': start,
                            'end_pos': end
                        })
                else:
                    entities.append({
                        'text': text,
                        'label': '组织机构',
                        'start_pos': start,
                        'end_pos': end
                    })
        except re.error:
            continue
    
    return sorted(entities, key=lambda x: x['start_pos'])


def recognize_entities_from_knowledge(content):
    """从知识库匹配实体"""
    entities = []
    
    try:
        knowledge_entities = KnowledgeEntity.query.all()
        
        for ke in knowledge_entities:
            for match in re.finditer(re.escape(ke.text), content):
                entities.append({
                    'text': ke.text,
                    'label': ke.label,
                    'start_pos': match.start(),
                    'end_pos': match.end(),
                    'from_knowledge': True
                })
    except Exception as e:
        pass
    
    return entities


def recognize_entities(content):
    """综合实体识别"""
    if not content:
        return []
    
    all_entities = []
    
    # 1. 知识库匹配（最高优先级）
    knowledge_entities = recognize_entities_from_knowledge(content)
    for e in knowledge_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 2. 时间日期
    time_entities = recognize_time_entities(content)
    for e in time_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 3. 数值金额
    amount_entities = recognize_amount_entities(content)
    for e in amount_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 4. 人名
    person_entities = recognize_person_entities(content)
    for e in person_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 5. 地名
    location_entities = recognize_location_entities(content)
    for e in location_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 6. 组织机构
    org_entities = recognize_organization_entities(content)
    for e in org_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    return sorted(all_entities, key=lambda x: x['start_pos'])