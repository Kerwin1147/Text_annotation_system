# app/views.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app import db
from app.models import TextFile, TextAnnotation, WordAnnotation, EntityAnnotation, KnowledgeEntity, FileStatus
from sqlalchemy import func
from datetime import datetime
import os
import re

views_bp = Blueprint('views', __name__)


def safe_filename(filename):
    """安全处理文件名，保留中文"""
    # 移除路径分隔符和空字符
    filename = filename.replace('/', '_').replace('\\', '_').replace('\x00', '')
    # 移除其他危险字符但保留中文、字母、数字、下划线、点、横线
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    # 确保文件名不为空
    if not filename or filename.strip() == '' or filename == '.txt':
        filename = f'未命名_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    return filename.strip()


@views_bp.route('/')
def index():
    """首页 - 文件列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    pagination = TextFile.query.order_by(TextFile.upload_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    files = pagination.items
    
    # 统计信息
    total_files = TextFile.query.count()
    pending_files = TextFile.query.filter_by(status=FileStatus.PENDING).count()
    processing_files = TextFile.query.filter_by(status=FileStatus.PROCESSING).count()
    completed_files = TextFile.query.filter_by(status=FileStatus.COMPLETED).count()
    
    stats = {
        'total': total_files,
        'pending': pending_files,
        'processing': processing_files,
        'completed': completed_files
    }
    
    return render_template('index.html', 
                         files=files, 
                         pagination=pagination,
                         stats=stats,
                         total=total_files)


@views_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    if 'file' not in request.files:
        flash('未选择文件', 'error')
        return redirect(url_for('views.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('未选择文件', 'error')
        return redirect(url_for('views.index'))
    
    if file and file.filename.endswith('.txt'):
        # 使用自定义的安全文件名函数，保留中文
        filename = safe_filename(file.filename)
        content = file.read().decode('utf-8', errors='ignore')
        
        text_file = TextFile(filename=filename, content=content, status=FileStatus.PENDING)
        db.session.add(text_file)
        db.session.commit()
        
        flash('文件上传成功', 'success')
        return redirect(url_for('views.index'))
    
    flash('仅支持.txt文件', 'error')
    return redirect(url_for('views.index'))


@views_bp.route('/manual_input', methods=['POST'])
def manual_input():
    """手动输入文本"""
    task_name = request.form.get('task_name', '').strip()
    text_content = request.form.get('text_content', '').strip()
    
    if not task_name or not text_content:
        flash('任务名称和文本内容不能为空', 'error')
        return redirect(url_for('views.index'))
    
    # 使用自定义的安全文件名函数
    filename = safe_filename(task_name)
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    text_file = TextFile(filename=filename, content=text_content, status=FileStatus.PENDING)
    db.session.add(text_file)
    db.session.commit()
    
    flash('任务创建成功', 'success')
    return redirect(url_for('views.index'))


@views_bp.route('/annotate/<int:file_id>')
def annotate(file_id):
    """标注页面"""
    file_data = TextFile.query.get_or_404(file_id)
    text_ann = TextAnnotation.query.filter_by(file_id=file_id).first()
    word_anns = WordAnnotation.query.filter_by(file_id=file_id).order_by(WordAnnotation.word_index).all()
    entity_anns = EntityAnnotation.query.filter_by(file_id=file_id).order_by(EntityAnnotation.start_pos).all()
    
    return render_template('annotate.html',
                         file=file_data,
                         text_ann=text_ann,
                         word_anns=[w.to_dict() for w in word_anns],
                         entity_anns=[e.to_dict() for e in entity_anns])


@views_bp.route('/stats')
def statistics():
    """数据统计页面"""
    total_files = TextFile.query.count()
    total_anns = EntityAnnotation.query.count()
    avg_anns = round(total_anns / total_files, 1) if total_files > 0 else 0
    
    entity_distribution = db.session.query(
        EntityAnnotation.label,
        func.count(EntityAnnotation.id)
    ).group_by(EntityAnnotation.label).all()
    
    labels = [item[0] for item in entity_distribution]
    counts = [item[1] for item in entity_distribution]
    
    return render_template('stats.html',
                         total_files=total_files,
                         total_anns=total_anns,
                         avg_anns=avg_anns,
                         stats_data=entity_distribution,
                         labels=labels,
                         counts=counts)


@views_bp.route('/knowledge_base')
def knowledge():
    """知识库管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    search = request.args.get('search', '').strip()
    label_filter = request.args.get('label', '').strip()
    
    query = KnowledgeEntity.query
    
    if search:
        query = query.filter(KnowledgeEntity.text.like(f'%{search}%'))
    
    if label_filter:
        query = query.filter_by(label=label_filter)
    
    # 获取总数（应用筛选条件后）
    total_entities = query.count()
    
    pagination = query.order_by(KnowledgeEntity.frequency.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 直接传递分页后的实体对象列表
    entities = pagination.items
    
    return render_template('knowledge_base.html',
                         entities=entities,
                         pagination=pagination,
                         total=total_entities,
                         search=search,
                         label_filter=label_filter)


@views_bp.route('/help')
def help_page():
    """帮助文档页面"""
    return render_template('help.html')