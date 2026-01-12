# app/utils.py
import jieba.posseg as pseg
from snownlp import SnowNLP
import re

# ========== 词性映射 ==========
POS_12 = {
    'n': '名词', 'v': '动词', 'a': '形容词', 'd': '副词',
    'm': '数词', 'q': '量词', 'r': '代词', 't': '时间词',
    'p': '介词', 'c': '连词', 'u': '助词', 'w': '标点'
}

# 标点符号集合
PUNCTUATION_SET = set('，。！？、；：""''【】（）《》〈〉「」『』〔〕…—～·.,!?;:\'\"()[]{}<>@#$%^&*+-=_|\\`~')

# 常见姓氏
SURNAMES = '王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾萧田董袁潘蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫雷侯龙段郝孔邵史毛常万顾赖武康贺严钱施牛洪龚聂路古毕于阎柳华邢莫袁汤殷罗倪严傅章丛鲁韦俞翟葛姬费卞管向欧施柴覃辛'

# 常见名字用字
NAME_CHARS = '伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发武新利清飞彬富顺信子杰涛昌成康星光天达安岩中茂进林有坚和彪博诚先敬震振壮会思群豪心邦承乐绍功松善厚庆磊民友裕河哲江超浩亮政谦亨奇固之轮翰朗伯宏言若鸣朋斌梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德行时泰盛雄琛钧冠策腾楠榕风航弘秀娟英华慧巧美娜静淑惠珠翠雅芝玉萍红娥玲芬芳燕彩春菊兰凤洁梅琳素云莲真环雪荣爱妹霞香月莺媛艳瑞凡佳嘉琼勤珍贞莉桂娣叶璧璐娅琦晶妍茜秋珊莎锦黛青倩婷姣婉娴瑾颖露瑶怡婵雁蓓纨仪荷丹蓉眉君琴蕊薇菁梦岚苑婕馨瑗琰韵融园艺咏卿聪澜纯毓悦昭冰爽琬茗羽希宁欣飘育滢馥筠柔竹霭凝晓欢霄枫芸菲寒伊亚宜可姬舒影荔枝思丽'

# 人名排除词
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
    
    current_pos = 0
    
    for word, flag in words:
        if not word.strip():
            current_pos += len(word)
            continue
        
        actual_pos = content.find(word, current_pos)
        if actual_pos == -1:
            actual_pos = current_pos
        
        pos, pos_cn = map_pos_to_12(flag, word)
        
        results.append({
            'word': word,
            'pos': pos,
            'pos_cn': pos_cn,
            'start_pos': actual_pos,
            'end_pos': actual_pos + len(word)
        })
        
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


def get_char_before(content, pos, count=1):
    """获取指定位置前的字符"""
    start = max(0, pos - count)
    return content[start:pos]


def get_char_after(content, pos, count=1):
    """获取指定位置后的字符"""
    end = min(len(content), pos + count)
    return content[pos:end]


def is_valid_entity_boundary(content, start, end):
    """检查实体边界是否合理（不在词语中间）"""
    # 检查前一个字符是否是中文（可能是词语的一部分）
    if start > 0:
        char_before = content[start - 1]
        # 如果前一个字符是中文且不是标点，可能边界不对
        if '\u4e00' <= char_before <= '\u9fff' and char_before not in PUNCTUATION_SET:
            # 进一步检查是否是常见的前缀词
            prefix_2 = content[max(0, start-2):start]
            prefix_3 = content[max(0, start-3):start]
            bad_prefixes = {'这个', '那个', '某个', '一个', '每个', '各个', '哪个', 
                           '这家', '那家', '某家', '一家', '每家', '各家',
                           '这所', '那所', '某所', '一所', '每所', '各所',
                           '这座', '那座', '某座', '一座', '每座', '各座',
                           '该', '本', '某', '各', '每', '此'}
            if prefix_2 in bad_prefixes or prefix_3 in bad_prefixes:
                return False
            if content[start-1] in bad_prefixes:
                return False
    
    return True


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
    
    # 2. 已知公众人物（高置信度）
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
    
    # 3. 姓+两个字的名（需要上下文验证）
    pattern_3char = r'[' + SURNAMES + r'][' + NAME_CHARS + r']{2}'
    for match in re.finditer(pattern_3char, content):
        text = match.group()
        start = match.start()
        end = match.end()
        
        if text in EXCLUDE_NAMES:
            continue
        
        overlap, _ = check_overlap({'start_pos': start, 'end_pos': end}, entities)
        
        if not overlap:
            # 检查边界
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


# ========== 地名识别（严格模式）==========

# 确定的地名白名单（只有这些才会被识别）
KNOWN_LOCATIONS = {
    # 中国省级行政区
    '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
    '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
    '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
    '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门',
    # 主要城市
    '石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德',
    '太原', '大同', '沈阳', '大连', '鞍山', '长春', '哈尔滨',
    '南京', '苏州', '无锡', '常州', '徐州', '杭州', '宁波', '温州', '嘉兴',
    '合肥', '芜湖', '福州', '厦门', '泉州', '南昌', '济南', '青岛', '烟台',
    '郑州', '洛阳', '武汉', '宜昌', '长沙', '株洲', '广州', '深圳', '珠海',
    '东莞', '佛山', '中山', '惠州', '海口', '三亚', '成都', '绵阳', '贵阳',
    '昆明', '西安', '咸阳', '兰州', '西宁', '银川', '乌鲁木齐', '拉萨',
    '呼和浩特', '包头', '南宁', '桂林', '柳州',
    # 国家
    '美国', '英国', '法国', '德国', '日本', '韩国', '俄罗斯', '加拿大',
    '澳大利亚', '新西兰', '印度', '巴西', '墨西哥', '阿根廷', '南非',
    '埃及', '沙特', '伊朗', '伊拉克', '以色列', '土耳其', '泰国', '越南',
    '新加坡', '马来西亚', '印尼', '菲律宾', '意大利', '西班牙', '葡萄牙',
    '荷兰', '比利时', '瑞士', '瑞典', '挪威', '丹麦', '芬兰', '波兰',
    '乌克兰', '希腊', '奥地利', '捷克', '匈牙利', '罗马尼亚', '朝鲜',
    # 国际城市
    '纽约', '华盛顿', '洛杉矶', '旧金山', '芝加哥', '波士顿', '西雅图',
    '伦敦', '巴黎', '柏林', '罗马', '马德里', '阿姆斯特丹', '布鲁塞尔',
    '东京', '大阪', '京都', '首尔', '釜山', '莫斯科', '悉尼', '墨尔本',
    '多伦多', '温哥华', '迪拜', '新德里', '孟买', '曼谷', '河内', '雅加达',
}

# 地名相关的排除词（这些不是地名）
LOCATION_EXCLUDE = {
    '这里', '那里', '哪里', '这儿', '那儿', '哪儿', '何处', '何地',
    '本地', '当地', '外地', '异地', '原地', '此地', '彼地',
    '东方', '西方', '南方', '北方', '前方', '后方', '上方', '下方',
    '东边', '西边', '南边', '北边', '左边', '右边', '前边', '后边',
    '东面', '西面', '南面', '北面', '前面', '后面', '上面', '下面',
    '东部', '西部', '南部', '北部', '中部', '内部', '外部',
    '附近', '周围', '旁边', '身边', '眼前', '面前', '背后', '身后',
    '远方', '远处', '近处', '高处', '低处', '深处',
    '国内', '国外', '海内', '海外', '境内', '境外', '省内', '省外',
    '城内', '城外', '市内', '市外', '县内', '县外', '区内', '区外',
    '室内', '室外', '门内', '门外', '院内', '院外', '校内', '校外',
    '家里', '家中', '家外', '屋里', '屋内', '屋外', '房内', '房外',
    '地方', '地点', '地区', '地带', '地域', '地段', '地块',
    '位置', '方位', '方向', '去向', '走向', '朝向', '取向',
    '场所', '场地', '场合', '处所', '住所', '居所',
    '途中', '路上', '路边', '路旁', '路口', '街上', '街头', '街边',
    '山上', '山下', '山中', '山里', '山顶', '山脚', '山腰',
    '水中', '水下', '水上', '水边', '水面', '河边', '河中', '河上',
    '天上', '天下', '天空', '空中', '地上', '地下', '地面', '地底',
    '世界', '全球', '全国', '各地', '各处', '处处', '到处', '四处',
    '农村', '城市', '城镇', '乡村', '乡下', '郊区', '郊外', '市区',
}

# 地名后缀（用于模式匹配验证）
LOCATION_SUFFIXES = {'省', '市', '县', '区', '镇', '乡', '村', '街道'}


def recognize_location_entities(content):
    """识别地名实体（严格模式）"""
    entities = []
    
    # 1. 只匹配已知地名白名单
    for loc in KNOWN_LOCATIONS:
        if loc in LOCATION_EXCLUDE:
            continue
        for match in re.finditer(re.escape(loc), content):
            start = match.start()
            end = match.end()
            
            # 检查是否已被更长的实体覆盖
            overlap, existing = check_overlap({
                'start_pos': start,
                'end_pos': end
            }, entities)
            
            if not overlap:
                # 检查边界：确保不是更长词语的一部分
                if start > 0:
                    char_before = content[start - 1]
                    # 如果前面是中文字符，检查是否构成其他词
                    if '\u4e00' <= char_before <= '\u9fff':
                        # 允许的前缀
                        allowed_prefix = {'在', '到', '去', '来', '从', '经', '由', '往', '赴', '回', '离'}
                        if char_before not in allowed_prefix:
                            # 检查前两个字是否构成排除词
                            prefix_word = content[max(0, start-2):end]
                            if prefix_word in LOCATION_EXCLUDE:
                                continue
                
                if end < len(content):
                    char_after = content[end]
                    # 如果后面紧跟地名后缀，说明当前匹配不完整
                    if char_after in LOCATION_SUFFIXES:
                        continue
                
                entities.append({
                    'text': loc,
                    'label': '地名',
                    'start_pos': start,
                    'end_pos': end
                })
    
    # 2. 匹配带有明确后缀的完整地名（如 XX省、XX市）
    # 只匹配那些前面有明确边界的
    strict_location_patterns = [
        # 使用字符类中的字面引号，不需要转义
        (r'(?<=[，。！？、；："\'（）\s在到去来从经由往赴回离])([^\s，。！？、；："\'（）]{2,4}(?:省|自治区))', 'province'),
        (r'(?<=[，。！？、；："\'（）\s在到去来从经由往赴回离])([^\s，。！？、；："\'（）]{2,4}(?:市|自治州))', 'city'),
        (r'(?<=[，。！？、；："\'（）\s在到去来从经由往赴回离])([^\s，。！？、；："\'（）]{2,4}(?:县|自治县))', 'county'),
    ]
    
    for pattern, loc_type in strict_location_patterns:
        try:
            for match in re.finditer(pattern, content):
                text = match.group(1) if match.lastindex else match.group()
                start = match.start(1) if match.lastindex else match.start()
                end = match.end(1) if match.lastindex else match.end()
                
                # 长度验证
                if len(text) < 3 or len(text) > 8:
                    continue
                
                # 排除词检查
                if text in LOCATION_EXCLUDE:
                    continue
                
                # 检查是否包含不应该的字符
                invalid_chars = {'的', '了', '着', '过', '和', '与', '或', '及', '等', '很', '太', '更', '最'}
                if any(c in text for c in invalid_chars):
                    continue
                
                overlap, existing = check_overlap({
                    'start_pos': start,
                    'end_pos': end
                }, entities)
                
                if overlap:
                    # 如果新实体更长，替换旧的
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


# ========== 组织机构识别（严格模式）==========

# 确定的机构白名单
KNOWN_ORGANIZATIONS = {
    # 国家机构
    '中国共产党', '国务院', '全国人大', '全国政协', '中央军委',
    '最高人民法院', '最高人民检察院', '中国人民银行', '外交部', '国防部',
    '发改委', '教育部', '科技部', '工信部', '公安部', '财政部', '商务部',
    '中央纪委', '中央组织部', '中央宣传部', '中央统战部',
    # 国际组织
    '联合国', '世界卫生组织', '世贸组织', '国际货币基金组织', '世界银行',
    '欧盟', '东盟', '北约', '亚投行', '金砖国家', '上合组织',
    # 知名企业
    '阿里巴巴', '腾讯', '百度', '京东', '华为', '小米', '字节跳动', '美团',
    '苹果公司', '谷歌', '微软', '亚马逊', '特斯拉', '脸书', '推特',
    '中国移动', '中国联通', '中国电信', '中国石油', '中国石化',
    '工商银行', '建设银行', '农业银行', '中国银行', '招商银行',
    # 知名高校
    '清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学',
    '南京大学', '中国科技大学', '武汉大学', '中山大学', '华中科技大学',
    '哈尔滨工业大学', '西安交通大学', '同济大学', '北京师范大学',
    # 科研机构
    '中国科学院', '中国工程院', '中国社会科学院',
    # 媒体
    '新华社', '人民日报', '中央电视台', 'CCTV', '央视', '中新社',
}

# 组织机构排除词（这些不是机构名）
ORG_EXCLUDE = {
    # 代词性质
    '这家公司', '那家公司', '某家公司', '一家公司', '该公司', '本公司',
    '这所学校', '那所学校', '某所学校', '一所学校', '该学校', '本学校',
    '这家医院', '那家医院', '某家医院', '一家医院', '该医院', '本医院',
    '这个机构', '那个机构', '某个机构', '一个机构', '该机构', '本机构',
    '这家银行', '那家银行', '某家银行', '一家银行', '该银行', '本银行',
    # 泛指
    '有关部门', '相关部门', '主管部门', '上级部门', '下级部门',
    '有关单位', '相关单位', '有关机构', '相关机构',
    '有限公司', '股份公司', '责任公司',  # 单独出现时不是完整机构名
    '公司', '企业', '单位', '机构', '组织', '部门', '学校', '医院', '银行',
    '大学', '学院', '中学', '小学', '幼儿园', '研究院', '研究所',
    '法院', '检察院', '公安局', '派出所',
    '政府', '党委', '人大', '政协', '纪委',
    '协会', '学会', '联合会', '商会', '基金会',
    # 常见误识别
    '的公司', '了公司', '和公司', '或公司',
    '的学校', '了学校', '和学校', '或学校',
    '的医院', '了医院', '和医院', '或医院',
    '个公司', '家公司', '些公司',
    '个学校', '所学校', '些学校',
    '个医院', '家医院', '些医院',
}

# 机构名中不应该包含的字符
ORG_INVALID_CHARS = {
    '的', '了', '着', '过', '和', '与', '或', '及', '等',
    '很', '太', '更', '最', '就', '才', '又', '也', '都',
    '这', '那', '哪', '某', '每', '各', '任何',
    '我', '你', '他', '她', '它', '们',
    '什么', '怎么', '为什么', '如何',
}

# 有效的机构前缀词（必须以这些开头或前面是标点/空格）
ORG_VALID_PREFIXES = {
    # 地名（作为机构前缀）
    '中国', '中华', '全国', '国家', '国际',
    '北京', '上海', '广州', '深圳', '天津', '重庆',
    '江苏', '浙江', '广东', '山东', '河南', '四川', '湖北', '湖南',
    '省', '市', '县', '区',
}


def is_valid_org_name(text, content, start):
    """验证是否是有效的机构名"""
    # 长度检查
    if len(text) < 4 or len(text) > 20:
        return False
    
    # 排除词检查
    if text in ORG_EXCLUDE:
        return False
    
    # 检查是否包含无效字符
    for char in ORG_INVALID_CHARS:
        if char in text:
            return False
    
    # 检查前缀是否合理
    if start > 0:
        # 获取前面的字符
        prefix_1 = content[start - 1] if start >= 1 else ''
        prefix_2 = content[start - 2:start] if start >= 2 else ''
        prefix_3 = content[start - 3:start] if start >= 3 else ''
        
        # 如果前面是中文字符，需要特别验证
        if prefix_1 and '\u4e00' <= prefix_1 <= '\u9fff':
            # 不允许的前缀
            bad_single = {'这', '那', '哪', '某', '该', '本', '个', '家', '所', '些', '的', '了', '和', '或', '是', '有'}
            if prefix_1 in bad_single:
                return False
            
            bad_double = {'这个', '那个', '某个', '一个', '这家', '那家', '某家', '一家', 
                         '这所', '那所', '某所', '一所', '每个', '各个', '哪个'}
            if prefix_2 in bad_double:
                return False
            
            bad_triple = {'这一家', '那一家', '某一家'}
            if prefix_3 in bad_triple:
                return False
            
            # 允许的前缀（介词等）
            allowed_prefix = {'在', '到', '去', '来', '从', '经', '由', '往', '赴', '向', '为', '与', '和', '被', '把', '对'}
            # 如果前面不是允许的前缀，也不是标点，则拒绝
            if prefix_1 not in allowed_prefix and prefix_1 not in PUNCTUATION_SET:
                # 检查是否是地名前缀的一部分
                is_location_prefix = False
                for loc in KNOWN_LOCATIONS:
                    if text.startswith(loc):
                        is_location_prefix = True
                        break
                if not is_location_prefix:
                    # 再检查前两个字是否构成有效前缀
                    if prefix_2 not in ORG_VALID_PREFIXES:
                        return False
    
    return True


def recognize_organization_entities(content):
    """识别组织机构实体（严格模式）"""
    entities = []
    
    # 1. 只匹配已知机构白名单
    for org in KNOWN_ORGANIZATIONS:
        for match in re.finditer(re.escape(org), content):
            start = match.start()
            end = match.end()
            
            overlap, _ = check_overlap({
                'start_pos': start,
                'end_pos': end
            }, entities)
            
            if not overlap:
                entities.append({
                    'text': org,
                    'label': '组织机构',
                    'start_pos': start,
                    'end_pos': end
                })
    
    # 2. 严格的模式匹配（只匹配高置信度的）
    # 要求前面必须是标点、空格或特定动词
    boundary_prefix = r'(?<=[，。！？、；："\'（）【】\s]|^)'
    
    strict_org_patterns = [
        # XX大学、XX学院（前面必须是边界）
        (boundary_prefix + r'((?:北京|清华|北大|复旦|上海|浙江|南京|武汉|中山|华中|哈尔滨|西安|同济|厦门|天津|南开|吉林|山东|四川|中国|中央)[^\s，。！？、；：""''（）]{0,6}(?:大学|学院))', 'university'),
        # XX公司（必须有具体名称）
        (boundary_prefix + r'((?:阿里|腾讯|百度|华为|小米|京东|美团|字节|网易|新浪|搜狐|滴滴)[^\s，。！？、；：""''（）]{0,8}(?:公司|集团|科技)?)', 'company'),
        # XX银行（前面必须是边界）
        (boundary_prefix + r'((?:中国|工商|建设|农业|交通|招商|浦发|民生|光大|中信|兴业|平安)[^\s，。！？、；：""''（）]{0,4}银行)', 'bank'),
        # XX医院（必须有具体地名或专有名词）
        (boundary_prefix + r'((?:北京|上海|广州|深圳|协和|同仁|华山|瑞金|湘雅|华西|中山)[^\s，。！？、；：""''（）]{0,6}医院)', 'hospital'),
    ]
    
    for pattern, org_type in strict_org_patterns:
        try:
            for match in re.finditer(pattern, content):
                text = match.group(1) if match.lastindex else match.group()
                # 计算实际位置
                full_match = match.group(0)
                offset = len(full_match) - len(text)
                start = match.start() + offset
                end = start + len(text)
                
                # 验证机构名
                if not is_valid_org_name(text, content, start):
                    continue
                
                # 排除词检查
                if text in ORG_EXCLUDE:
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
    
    # 3. 带有完整后缀的机构名（非常严格）
    # 只匹配 "XX有限公司"、"XX股份有限公司" 等完整形式
    # 要求前面必须是明确的边界
    full_company_pattern = r'(?<=[，。！？、；："\'（）【】\s在到去来从经由往赴向为与和被把对])([^\s，。！？、；："\'（）【】的了着过]{2,10}(?:有限公司|股份有限公司|责任有限公司|集团有限公司|集团公司))'
    try:
        for match in re.finditer(full_company_pattern, content):
            text = match.group(1)
            start = match.start(1)
            end = match.end(1)
            
            # 验证
            if not is_valid_org_name(text, content, start):
                continue
            
            # 额外检查：确保不是泛指
            if text.startswith(('这', '那', '某', '该', '本', '一家', '一个')):
                continue
            
            overlap, existing = check_overlap({
                'start_pos': start,
                'end_pos': end
            }, entities)
            
            if not overlap:
                entities.append({
                    'text': text,
                    'label': '组织机构',
                    'start_pos': start,
                    'end_pos': end
                })
    except re.error:
        pass
    
    return sorted(entities, key=lambda x: x['start_pos'])


def recognize_entities_from_knowledge(content):
    """从知识库匹配实体（高优先级）"""
    entities = []
    
    try:
        from app.models import KnowledgeEntity
        knowledge_entities = KnowledgeEntity.query.all()
        
        for ke in knowledge_entities:
            # 知识库中的实体是可信的，直接匹配
            for match in re.finditer(re.escape(ke.text), content):
                start = match.start()
                end = match.end()
                
                # 简单的边界检查
                # 检查前面是否是中文字符（可能是词语的一部分）
                if start > 0:
                    char_before = content[start - 1]
                    if '\u4e00' <= char_before <= '\u9fff':
                        # 如果知识库实体较短（2-3字），需要更严格的边界检查
                        if len(ke.text) <= 3:
                            # 检查是否有不良前缀
                            bad_prefixes = {'这', '那', '某', '该', '本', '个', '家', '所'}
                            if char_before in bad_prefixes:
                                continue
                
                # 检查后面
                if end < len(content):
                    char_after = content[end]
                    # 如果后面还是中文，可能不是完整的实体
                    if '\u4e00' <= char_after <= '\u9fff':
                        # 对于人名，检查是否后面跟着名字常用字
                        if ke.label == '人名' and char_after in NAME_CHARS:
                            continue
                
                entities.append({
                    'text': ke.text,
                    'label': ke.label,
                    'start_pos': start,
                    'end_pos': end,
                    'from_knowledge': True
                })
    except Exception:
        # 知识库不可用时静默失败
        pass
    
    return entities


def merge_overlapping_entities(entities):
    """合并重叠的实体，保留更长或更优先的"""
    if not entities:
        return []
    
    # 按起始位置排序
    sorted_entities = sorted(entities, key=lambda x: (x['start_pos'], -len(x['text'])))
    
    merged = []
    for entity in sorted_entities:
        if not merged:
            merged.append(entity)
            continue
        
        last = merged[-1]
        # 检查是否重叠
        if entity['start_pos'] < last['end_pos']:
            # 重叠了，保留更长的那个
            if len(entity['text']) > len(last['text']):
                merged[-1] = entity
            # 如果长度相同，保留知识库来源的
            elif len(entity['text']) == len(last['text']):
                if entity.get('from_knowledge') and not last.get('from_knowledge'):
                    merged[-1] = entity
            # 否则保留原来的
        else:
            merged.append(entity)
    
    return merged


def recognize_entities(content):
    """
    综合实体识别（严格模式）
    
    策略：
    1. 知识库匹配优先（用户标注过的实体）
    2. 时间日期识别（模式明确，误识别率低）
    3. 数值金额识别（模式明确，误识别率低）
    4. 人名识别（需要上下文验证）
    5. 地名识别（严格白名单模式）
    6. 组织机构识别（严格白名单+模式验证）
    """
    if not content:
        return []
    
    all_entities = []
    
    # 1. 知识库匹配（最高优先级，用户验证过的实体）
    knowledge_entities = recognize_entities_from_knowledge(content)
    for e in knowledge_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 2. 时间日期识别（误识别率低）
    time_entities = recognize_time_entities(content)
    for e in time_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 3. 数值金额识别（误识别率低）
    amount_entities = recognize_amount_entities(content)
    for e in amount_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 4. 人名识别
    person_entities = recognize_person_entities(content)
    for e in person_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 5. 地名识别（严格白名单模式）
    location_entities = recognize_location_entities(content)
    for e in location_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 6. 组织机构识别（严格模式）
    org_entities = recognize_organization_entities(content)
    for e in org_entities:
        add_entity_if_no_overlap(e, all_entities)
    
    # 最终合并和排序
    all_entities = merge_overlapping_entities(all_entities)
    
    # 清理结果，移除 from_knowledge 标记（前端不需要）
    for e in all_entities:
        if 'from_knowledge' in e:
            del e['from_knowledge']
    
    return sorted(all_entities, key=lambda x: x['start_pos'])