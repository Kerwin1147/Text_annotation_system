# app/api.py
from flask import Blueprint, request, jsonify, Response, make_response
from app import db
from app.models import TextFile, TextAnnotation, WordAnnotation, EntityAnnotation, KnowledgeEntity, FileStatus
from app.utils import segment_text, get_text_category, get_sentiment, recognize_entities, POS_12
import json
from urllib.parse import quote

api_bp = Blueprint('api', __name__)


# ==================== 文件管理 ====================

@api_bp.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除文件"""
    text_file = TextFile.query.get_or_404(file_id)
    db.session.delete(text_file)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '删除成功'})


@api_bp.route('/mark_complete/<int:file_id>', methods=['POST'])
def mark_complete(file_id):
    """标记任务为已完成"""
    text_file = TextFile.query.get_or_404(file_id)
    text_file.status = FileStatus.COMPLETED
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '已标记为完成'})


@api_bp.route('/export_annotations/<int:file_id>', methods=['GET'])
def export_annotations(file_id):
    """导出标注结果"""
    text_file = TextFile.query.get_or_404(file_id)
    
    # 获取所有标注数据
    text_ann = TextAnnotation.query.filter_by(file_id=file_id).first()
    word_anns = WordAnnotation.query.filter_by(file_id=file_id).order_by(WordAnnotation.word_index).all()
    entity_anns = EntityAnnotation.query.filter_by(file_id=file_id).order_by(EntityAnnotation.start_pos).all()
    
    export_data = {
        'file': {
            'id': text_file.id,
            'filename': text_file.filename,
            'content': text_file.content
        },
        'text_annotation': text_ann.to_dict() if text_ann else None,
        'word_annotations': [w.to_dict() for w in word_anns],
        'entity_annotations': [e.to_dict() for e in entity_anns]
    }
    
    # 处理中文文件名
    filename = text_file.filename.replace('.txt', '').replace('.csv', '')
    # 使用 RFC 5987 编码处理中文文件名
    encoded_filename = quote(f'{filename}_标注结果.json')
    
    response = make_response(json.dumps(export_data, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
    
    return response


# ==================== 智能标注（只分析，不入库）====================

@api_bp.route('/smart_annotate/<int:file_id>', methods=['POST'])
def smart_annotate(file_id):
    """
    智能标注 - 只进行分析，不写入数据库
    数据保存在前端，用户点击"保存标注"后才入库
    """
    text_file = TextFile.query.get_or_404(file_id)
    content = text_file.content
    
    try:
        # 1. 文本分类和情感分析
        category = get_text_category(content)
        sentiment, sentiment_score = get_sentiment(content)
        
        text_annotation = {
            'text_category': category,
            'text_sentiment': sentiment,
            'sentiment_score': sentiment_score
        }
        
        # 2. 分词和词性标注（只返回结果，不入库）
        segments = segment_text(content)
        word_annotations = []
        for idx, seg in enumerate(segments):
            word_annotations.append({
                'id': idx + 1,  # 临时ID，前端使用
                'word_index': idx,
                'word': seg['word'],
                'pos': seg['pos'],
                'pos_cn': seg['pos_cn'],
                'start_pos': seg['start_pos'],
                'end_pos': seg['end_pos']
            })
        
        # 3. 实体识别（只返回结果，不入库）
        entities = recognize_entities(content)
        entity_annotations = []
        for idx, entity in enumerate(entities):
            entity_annotations.append({
                'id': idx + 1,  # 临时ID，前端使用
                'text': entity['text'],
                'label': entity['label'],
                'start_pos': entity['start_pos'],
                'end_pos': entity['end_pos']
            })
        
        return jsonify({
            'status': 'success',
            'message': '智能标注完成（未保存，请点击保存按钮）',
            'text_annotation': text_annotation,
            'word_annotations': word_annotations,
            'entity_annotations': entity_annotations
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== 保存标注（真正写入数据库）====================

@api_bp.route('/save_all_annotations', methods=['POST'])
def save_all_annotations():
    """
    保存所有标注 - 将前端数据写入数据库
    这是唯一写入数据库的接口
    """
    data = request.get_json()
    file_id = data.get('file_id')
    text_category = data.get('text_category', '')
    text_sentiment = data.get('text_sentiment', '')
    word_annotations = data.get('word_annotations', [])
    entity_annotations = data.get('entity_annotations', [])
    
    if not file_id:
        return jsonify({'status': 'error', 'message': '缺少文件ID'}), 400
    
    text_file = TextFile.query.get_or_404(file_id)
    
    try:
        # 1. 清除旧的标注数据
        TextAnnotation.query.filter_by(file_id=file_id).delete()
        WordAnnotation.query.filter_by(file_id=file_id).delete()
        EntityAnnotation.query.filter_by(file_id=file_id).delete()
        
        # 2. 保存文本标注（分类和情感）
        if text_category or text_sentiment:
            text_ann = TextAnnotation(
                file_id=file_id,
                text_category=text_category,
                text_sentiment=text_sentiment
            )
            db.session.add(text_ann)
        
        # 3. 保存词语标注
        for idx, word_data in enumerate(word_annotations):
            word_ann = WordAnnotation(
                file_id=file_id,
                word_index=idx,
                word=word_data.get('word', ''),
                pos=word_data.get('pos', 'n'),
                pos_cn=word_data.get('pos_cn', '名词'),
                start_pos=word_data.get('start_pos', 0),
                end_pos=word_data.get('end_pos', 0)
            )
            db.session.add(word_ann)
        
        # 4. 保存实体标注并更新知识库
        for entity_data in entity_annotations:
            entity_text = entity_data.get('text', '')
            entity_label = entity_data.get('label', '')
            
            if not entity_text or not entity_label:
                continue
            
            entity_ann = EntityAnnotation(
                file_id=file_id,
                text=entity_text,
                label=entity_label,
                start_pos=entity_data.get('start_pos', 0),
                end_pos=entity_data.get('end_pos', 0)
            )
            db.session.add(entity_ann)
            
            # 更新知识库
            existing = KnowledgeEntity.query.filter_by(text=entity_text).first()
            if existing:
                existing.frequency += 1
            else:
                ke = KnowledgeEntity(
                    text=entity_text,
                    label=entity_label,
                    source='auto'
                )
                db.session.add(ke)
        
        # 5. 更新文件状态
        text_file.status = FileStatus.PROCESSING
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '标注已保存到数据库',
            'saved_words': len(word_annotations),
            'saved_entities': len(entity_annotations)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== 清空标注 ====================

@api_bp.route('/clear_annotations/<int:file_id>', methods=['POST'])
def clear_annotations(file_id):
    """清空所有标注（从数据库删除）"""
    text_file = TextFile.query.get_or_404(file_id)
    
    # 删除所有相关标注
    TextAnnotation.query.filter_by(file_id=file_id).delete()
    WordAnnotation.query.filter_by(file_id=file_id).delete()
    EntityAnnotation.query.filter_by(file_id=file_id).delete()
    
    # 重置状态
    text_file.status = FileStatus.PENDING
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '已清空所有标注'})


# ==================== 词语标注管理（前端临时操作）====================

@api_bp.route('/update_word_pos', methods=['POST'])
def update_word_pos():
    """更新词性标注（返回确认，实际保存在前端）"""
    data = request.get_json()
    word_id = data.get('id')
    new_pos = data.get('pos')
    new_pos_cn = data.get('pos_cn')
    
    if not new_pos:
        return jsonify({'status': 'error', 'message': '缺少词性参数'}), 400
    
    # 只返回确认，不写数据库（数据在前端维护）
    return jsonify({
        'status': 'success',
        'message': '词性已更新（请保存以持久化）',
        'pos': new_pos,
        'pos_cn': new_pos_cn or POS_12.get(new_pos, '未知')
    })


@api_bp.route('/merge_words', methods=['POST'])
def merge_words():
    """合并词语（在前端处理，返回新的词语列表）"""
    data = request.get_json()
    word_ids = data.get('word_ids', [])
    words_data = data.get('words_data', [])  # 前端传来的词语数据
    
    if len(word_ids) < 2:
        return jsonify({'status': 'error', 'message': '至少需要选择2个词'}), 400
    
    if not words_data:
        return jsonify({'status': 'error', 'message': '缺少词语数据'}), 400
    
    # 找到要合并的词语
    selected_words = [w for w in words_data if w.get('id') in word_ids]
    selected_words.sort(key=lambda x: x.get('word_index', 0))
    
    if len(selected_words) < 2:
        return jsonify({'status': 'error', 'message': '未找到足够的词语'}), 400
    
    # 检查是否连续
    indices = [w.get('word_index', 0) for w in selected_words]
    if max(indices) - min(indices) + 1 != len(indices):
        return jsonify({'status': 'error', 'message': '只能合并连续的词语'}), 400
    
    # 合并词语
    merged_word = ''.join([w.get('word', '') for w in selected_words])
    merged_start = selected_words[0].get('start_pos', 0)
    merged_end = selected_words[-1].get('end_pos', 0)
    
    # 构建新的词语列表
    new_words = []
    merged_ids = set(word_ids)
    first_merged = True
    new_index = 0
    
    for w in sorted(words_data, key=lambda x: x.get('word_index', 0)):
        if w.get('id') in merged_ids:
            if first_merged:
                # 添加合并后的词
                new_words.append({
                    'id': w.get('id'),  # 保留第一个词的ID
                    'word_index': new_index,
                    'word': merged_word,
                    'pos': 'n',
                    'pos_cn': '名词',
                    'start_pos': merged_start,
                    'end_pos': merged_end
                })
                new_index += 1
                first_merged = False
            # 跳过其他被合并的词
        else:
            # 保留未合并的词，更新索引
            new_words.append({
                'id': w.get('id'),
                'word_index': new_index,
                'word': w.get('word', ''),
                'pos': w.get('pos', 'n'),
                'pos_cn': w.get('pos_cn', '名词'),
                'start_pos': w.get('start_pos', 0),
                'end_pos': w.get('end_pos', 0)
            })
            new_index += 1
    
    return jsonify({
        'status': 'success',
        'message': f'已合并为"{merged_word}"（请保存以持久化）',
        'word_annotations': new_words
    })


# ==================== 实体标注管理（前端临时操作）====================

@api_bp.route('/add_entity', methods=['POST'])
def add_entity():
    """添加实体标注（返回确认，实际保存在前端）"""
    data = request.get_json()
    text = data.get('text')
    label = data.get('label')
    start_pos = data.get('start_pos')
    end_pos = data.get('end_pos')
    
    if not all([text, label, start_pos is not None, end_pos is not None]):
        return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
    
    valid_labels = ['人名', '地名', '组织机构', '时间日期', '数值金额']
    if label not in valid_labels:
        return jsonify({'status': 'error', 'message': '无效的实体类型'}), 400
    
    # 生成临时ID（前端使用时间戳）
    import time
    temp_id = int(time.time() * 1000)
    
    return jsonify({
        'status': 'success',
        'message': '实体已添加（请保存以持久化）',
        'entity': {
            'id': temp_id,
            'text': text,
            'label': label,
            'start_pos': start_pos,
            'end_pos': end_pos
        }
    })


@api_bp.route('/update_entity/<int:entity_id>', methods=['POST'])
def update_entity(entity_id):
    """更新实体标注（返回确认，实际保存在前端）"""
    data = request.get_json()
    new_label = data.get('label')
    
    valid_labels = ['人名', '地名', '组织机构', '时间日期', '数值金额']
    if new_label and new_label in valid_labels:
        return jsonify({
            'status': 'success',
            'message': '实体已更新（请保存以持久化）',
            'label': new_label
        })
    
    return jsonify({'status': 'error', 'message': '无效的实体类型'}), 400


@api_bp.route('/delete_entity/<int:entity_id>', methods=['DELETE'])
def delete_entity(entity_id):
    """删除实体标注（返回确认，实际删除在前端）"""
    return jsonify({
        'status': 'success',
        'message': '实体已删除（请保存以持久化）'
    })


# ==================== 知识库管理 ====================

@api_bp.route('/knowledge/entities', methods=['GET'])
def get_knowledge_entities():
    """获取所有知识库实体"""
    entities = KnowledgeEntity.query.order_by(KnowledgeEntity.frequency.desc()).all()
    return jsonify({
        'status': 'success',
        'entities': [e.to_dict() for e in entities]
    })


@api_bp.route('/knowledge/add', methods=['POST'])
def add_knowledge_entity():
    """添加知识库实体"""
    data = request.get_json()
    text = data.get('text', '').strip()
    label = data.get('label', '').strip()
    
    if not text or not label:
        return jsonify({'status': 'error', 'message': '实体文本和类型不能为空'}), 400
    
    valid_labels = ['人名', '地名', '组织机构', '时间日期', '数值金额']
    if label not in valid_labels:
        return jsonify({'status': 'error', 'message': '无效的实体类型'}), 400
    
    existing = KnowledgeEntity.query.filter_by(text=text).first()
    if existing:
        return jsonify({'status': 'error', 'message': '该实体已存在'}), 400
    
    ke = KnowledgeEntity(text=text, label=label, source='manual')
    db.session.add(ke)
    db.session.commit()
    
    return jsonify({'status': 'success', 'entity': ke.to_dict()})


@api_bp.route('/knowledge/delete/<int:entity_id>', methods=['DELETE'])
def delete_knowledge_entity(entity_id):
    """删除知识库实体"""
    ke = KnowledgeEntity.query.get_or_404(entity_id)
    db.session.delete(ke)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '删除成功'})


@api_bp.route('/knowledge/batch_delete', methods=['POST'])
def batch_delete_knowledge():
    """批量删除知识库实体"""
    data = request.get_json()
    entity_ids = data.get('entity_ids', [])
    
    if not entity_ids:
        return jsonify({'status': 'error', 'message': '未指定要删除的实体'}), 400
    
    KnowledgeEntity.query.filter(KnowledgeEntity.id.in_(entity_ids)).delete(synchronize_session=False)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'已删除 {len(entity_ids)} 个实体'})


@api_bp.route('/knowledge/export', methods=['GET'])
def export_knowledge():
    """导出知识库"""
    entities = KnowledgeEntity.query.order_by(KnowledgeEntity.label, KnowledgeEntity.text).all()
    
    export_data = {
        'total': len(entities),
        'entities': [e.to_dict() for e in entities]
    }
    
    response = make_response(json.dumps(export_data, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = "attachment; filename*=UTF-8''knowledge_base.json"
    
    return response


# ==================== 统计信息 ====================

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    from sqlalchemy import func
    
    total_files = TextFile.query.count()
    completed_files = TextFile.query.filter_by(status=FileStatus.COMPLETED).count()
    total_words = WordAnnotation.query.count()
    total_entities = EntityAnnotation.query.count()
    total_knowledge = KnowledgeEntity.query.count()
    
    entity_distribution = db.session.query(
        EntityAnnotation.label,
        func.count(EntityAnnotation.id)
    ).group_by(EntityAnnotation.label).all()
    
    pos_distribution = db.session.query(
        WordAnnotation.pos_cn,
        func.count(WordAnnotation.id)
    ).group_by(WordAnnotation.pos_cn).all()
    
    return jsonify({
        'total_files': total_files,
        'completed_files': completed_files,
        'total_words': total_words,
        'total_entities': total_entities,
        'total_knowledge': total_knowledge,
        'entity_distribution': dict(entity_distribution),
        'pos_distribution': dict(pos_distribution)
    })


@api_bp.route('/pos-tags', methods=['GET'])
def get_pos_tags():
    """获取所有词性标签"""
    return jsonify({
        'pos_tags': [{'code': k, 'name': v} for k, v in POS_12.items()]
    })


@api_bp.route('/entity-types', methods=['GET'])
def get_entity_types():
    """获取所有实体类型"""
    return jsonify({
        'entity_types': ['人名', '地名', '组织机构', '时间日期', '数值金额']
    })