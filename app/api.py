# app/api.py
from flask import Blueprint, request, jsonify, send_file
from app import db
from app.models import TextFile, TextAnnotation, WordAnnotation, EntityAnnotation, KnowledgeEntity, FileStatus
from app.utils import get_text_category, get_sentiment, segment_text, recognize_entities, add_to_knowledge_base
import json
import io
from datetime import datetime

api_bp = Blueprint('api', __name__)


@api_bp.route('/smart_annotate/<int:file_id>', methods=['POST'])
def smart_annotate(file_id):
    """智能标注 - 分别处理分词和实体"""
    try:
        file_data = TextFile.query.get_or_404(file_id)
        content = file_data.content
        
        # 清除旧标注
        WordAnnotation.query.filter_by(file_id=file_id).delete()
        EntityAnnotation.query.filter_by(file_id=file_id).delete()
        TextAnnotation.query.filter_by(file_id=file_id).delete()
        
        # 1. 文本整体标注
        text_category = get_text_category(content)
        text_sentiment, sentiment_score = get_sentiment(content)
        
        text_ann = TextAnnotation(
            file_id=file_id,
            text_category=text_category,
            text_sentiment=text_sentiment,
            sentiment_score=sentiment_score
        )
        db.session.add(text_ann)
        
        # 2. 分词和词性标注
        word_results = segment_text(content)
        for idx, word_data in enumerate(word_results):
            word_ann = WordAnnotation(
                file_id=file_id,
                word_index=idx,
                word=word_data['word'],
                pos=word_data['pos'],
                pos_cn=word_data['pos_cn']
            )
            db.session.add(word_ann)
        
        # 3. 命名实体标注（独立）
        entity_results = recognize_entities(content)
        for entity_data in entity_results:
            entity_ann = EntityAnnotation(
                file_id=file_id,
                text=entity_data['text'],
                label=entity_data['label'],
                start_pos=entity_data['start_pos'],
                end_pos=entity_data['end_pos']
            )
            db.session.add(entity_ann)
        
        file_data.status = FileStatus.PROCESSING
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'text_annotation': text_ann.to_dict(),
            'word_annotations': [w.to_dict() for w in file_data.word_annotations.order_by(WordAnnotation.word_index).all()],
            'entity_annotations': [e.to_dict() for e in file_data.entity_annotations.order_by(EntityAnnotation.start_pos).all()]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/update_word_pos', methods=['POST'])
def update_word_pos():
    """更新词性"""
    try:
        data = request.json
        word_ann = WordAnnotation.query.get(data['id'])
        
        if not word_ann:
            return jsonify({'status': 'error', 'message': '词语不存在'}), 404
        
        word_ann.pos = data['pos']
        word_ann.pos_cn = data['pos_cn']
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '词性已更新'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/merge_words', methods=['POST'])
def merge_words():
    """合并分词"""
    try:
        data = request.json
        word_ids = data.get('word_ids', [])
        
        if len(word_ids) < 2:
            return jsonify({'status': 'error', 'message': '至少选择2个词'}), 400
        
        words = WordAnnotation.query.filter(WordAnnotation.id.in_(word_ids)).order_by(WordAnnotation.word_index).all()
        
        if len(words) < 2:
            return jsonify({'status': 'error', 'message': '词语不存在'}), 400
        
        # 检查是否连续
        indices = [w.word_index for w in words]
        if max(indices) - min(indices) + 1 != len(indices):
            return jsonify({'status': 'error', 'message': '只能合并连续的词语'}), 400
        
        merged_text = ''.join(w.word for w in words)
        first_word = words[0]
        first_word.word = merged_text
        first_word.pos = 'n'
        first_word.pos_cn = '名词'
        
        # 删除其他词
        for w in words[1:]:
            db.session.delete(w)
        
        db.session.commit()
        
        # 重新编号
        file_id = first_word.file_id
        all_words = WordAnnotation.query.filter_by(file_id=file_id).order_by(WordAnnotation.word_index).all()
        for idx, w in enumerate(all_words):
            w.word_index = idx
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'已合并为: {merged_text}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/add_entity', methods=['POST'])
def add_entity():
    """添加命名实体（鼠标划选）"""
    try:
        data = request.json
        file_id = data['file_id']
        text = data['text']
        label = data['label']
        start_pos = data['start_pos']
        end_pos = data['end_pos']
        
        # 验证标签
        valid_labels = ['人名', '地名', '组织机构', '时间日期', '数值金额']
        if label not in valid_labels:
            return jsonify({'status': 'error', 'message': '无效的实体类型'}), 400
        
        # 检查重叠
        overlapping = EntityAnnotation.query.filter(
            EntityAnnotation.file_id == file_id,
            EntityAnnotation.start_pos < end_pos,
            EntityAnnotation.end_pos > start_pos
        ).first()
        
        if overlapping:
            return jsonify({'status': 'error', 'message': '实体区域重叠'}), 400
        
        entity_ann = EntityAnnotation(
            file_id=file_id,
            text=text,
            label=label,
            start_pos=start_pos,
            end_pos=end_pos
        )
        db.session.add(entity_ann)
        db.session.commit()
        
        # 加入知识库
        add_to_knowledge_base(text, label, 'manual')
        
        return jsonify({'status': 'success', 'entity': entity_ann.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/update_entity/<int:entity_id>', methods=['POST'])
def update_entity(entity_id):
    """更新实体标签"""
    try:
        data = request.json
        entity_ann = EntityAnnotation.query.get(entity_id)
        
        if not entity_ann:
            return jsonify({'status': 'error', 'message': '实体不存在'}), 404
        
        label = data['label']
        valid_labels = ['人名', '地名', '组织机构', '时间日期', '数值金额']
        if label not in valid_labels:
            return jsonify({'status': 'error', 'message': '无效的实体类型'}), 400
        
        entity_ann.label = label
        db.session.commit()
        
        # 更新知识库
        add_to_knowledge_base(entity_ann.text, label, 'manual')
        
        return jsonify({'status': 'success', 'message': '实体已更新'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/delete_entity/<int:entity_id>', methods=['DELETE'])
def delete_entity(entity_id):
    """删除实体"""
    try:
        entity_ann = EntityAnnotation.query.get(entity_id)
        
        if not entity_ann:
            return jsonify({'status': 'error', 'message': '实体不存在'}), 404
        
        db.session.delete(entity_ann)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '实体已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/save_all_annotations', methods=['POST'])
def save_all_annotations():
    """保存所有标注"""
    try:
        data = request.json
        file_id = data['file_id']
        
        # 更新文本标注
        text_ann = TextAnnotation.query.filter_by(file_id=file_id).first()
        if text_ann:
            text_ann.text_category = data.get('text_category')
            text_ann.text_sentiment = data.get('text_sentiment')
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': '保存成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/clear_annotations/<int:file_id>', methods=['POST'])
def clear_annotations(file_id):
    """清空标注"""
    try:
        WordAnnotation.query.filter_by(file_id=file_id).delete()
        EntityAnnotation.query.filter_by(file_id=file_id).delete()
        TextAnnotation.query.filter_by(file_id=file_id).delete()
        
        file_data = TextFile.query.get(file_id)
        if file_data:
            file_data.status = FileStatus.PENDING
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': '已清空标注'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除文件"""
    try:
        file_data = TextFile.query.get_or_404(file_id)
        
        # 级联删除会自动删除相关标注
        db.session.delete(file_data)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '文件已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/mark_complete/<int:file_id>', methods=['POST'])
def mark_complete(file_id):
    """标记为已完成"""
    try:
        file_data = TextFile.query.get_or_404(file_id)
        file_data.status = FileStatus.COMPLETED
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '已标记为完成'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/export_annotations/<int:file_id>')
def export_annotations(file_id):
    """导出标注结果"""
    try:
        file_data = TextFile.query.get_or_404(file_id)
        text_ann = TextAnnotation.query.filter_by(file_id=file_id).first()
        word_anns = WordAnnotation.query.filter_by(file_id=file_id).order_by(WordAnnotation.word_index).all()
        entity_anns = EntityAnnotation.query.filter_by(file_id=file_id).order_by(EntityAnnotation.start_pos).all()
        
        export_data = {
            'file_info': {
                'filename': file_data.filename,
                'content': file_data.content,
                'upload_time': file_data.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': file_data.status
            },
            'text_annotation': text_ann.to_dict() if text_ann else None,
            'word_annotations': [w.to_dict() for w in word_anns],
            'entity_annotations': [e.to_dict() for e in entity_anns],
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        buffer = io.BytesIO(json_str.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"{file_data.filename.rsplit('.', 1)[0]}_annotations.json"
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/knowledge/entities', methods=['GET'])
def get_knowledge_entities():
    """获取知识库实体列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        label_filter = request.args.get('label', '').strip()
        
        query = KnowledgeEntity.query
        
        if search:
            query = query.filter(KnowledgeEntity.text.like(f'%{search}%'))
        
        if label_filter:
            query = query.filter_by(label=label_filter)
        
        pagination = query.order_by(KnowledgeEntity.frequency.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'status': 'success',
            'entities': [e.to_dict() for e in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/knowledge/add', methods=['POST'])
def add_knowledge_entity():
    """添加知识库实体"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        label = data.get('label', '').strip()
        
        if not text or not label:
            return jsonify({'status': 'error', 'message': '文本和标签不能为空'}), 400
        
        valid_labels = ['人名', '地名', '组织机构', '时间日期', '数值金额']
        if label not in valid_labels:
            return jsonify({'status': 'error', 'message': '无效的实体类型'}), 400
        
        existing = KnowledgeEntity.query.filter_by(text=text).first()
        if existing:
            return jsonify({'status': 'error', 'message': '该实体已存在'}), 400
        
        entity = KnowledgeEntity(text=text, label=label, source='manual')
        db.session.add(entity)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '添加成功', 'entity': entity.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/knowledge/update/<int:entity_id>', methods=['POST'])
def update_knowledge_entity(entity_id):
    """更新知识库实体"""
    try:
        data = request.json
        entity = KnowledgeEntity.query.get(entity_id)
        
        if not entity:
            return jsonify({'status': 'error', 'message': '实体不存在'}), 404
        
        label = data.get('label', '').strip()
        valid_labels = ['人名', '地名', '组织机构', '时间日期', '数值金额']
        if label not in valid_labels:
            return jsonify({'status': 'error', 'message': '无效的实体类型'}), 400
        
        entity.label = label
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/knowledge/delete/<int:entity_id>', methods=['DELETE'])
def delete_knowledge_entity(entity_id):
    """删除知识库实体"""
    try:
        entity = KnowledgeEntity.query.get(entity_id)
        
        if not entity:
            return jsonify({'status': 'error', 'message': '实体不存在'}), 404
        
        db.session.delete(entity)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/knowledge/batch_delete', methods=['POST'])
def batch_delete_knowledge():
    """批量删除知识库实体"""
    try:
        data = request.json
        entity_ids = data.get('entity_ids', [])
        
        if not entity_ids:
            return jsonify({'status': 'error', 'message': '未选择实体'}), 400
        
        KnowledgeEntity.query.filter(KnowledgeEntity.id.in_(entity_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'已删除 {len(entity_ids)} 个实体'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/knowledge/import', methods=['POST'])
def import_knowledge():
    """导入知识库"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '未上传文件'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.json'):
            return jsonify({'status': 'error', 'message': '仅支持JSON格式'}), 400
        
        content = file.read().decode('utf-8')
        data = json.loads(content)
        
        if not isinstance(data, list):
            return jsonify({'status': 'error', 'message': 'JSON格式错误，应为数组'}), 400
        
        added = 0
        for item in data:
            text = item.get('text', '').strip()
            label = item.get('label', '').strip()
            
            if not text or not label:
                continue
            
            existing = KnowledgeEntity.query.filter_by(text=text).first()
            if not existing:
                entity = KnowledgeEntity(text=text, label=label, source='import')
                db.session.add(entity)
                added += 1
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'成功导入 {added} 个实体'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/knowledge/export')
def export_knowledge():
    """导出知识库"""
    try:
        entities = KnowledgeEntity.query.all()
        export_data = [e.to_dict() for e in entities]
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        buffer = io.BytesIO(json_str.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"knowledge_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500