# run.py
"""
文本标注系统 - 启动文件
支持5种命名实体类型：人名、地名、组织机构、时间日期、数值金额
"""
import os
from app import create_app, db
from app.models import TextFile, TextAnnotation, WordAnnotation, EntityAnnotation, KnowledgeEntity

# 创建应用实例
app = create_app()


@app.shell_context_processor
def make_shell_context():
    """为Flask shell提供上下文"""
    return {
        'db': db,
        'TextFile': TextFile,
        'TextAnnotation': TextAnnotation,
        'WordAnnotation': WordAnnotation,
        'EntityAnnotation': EntityAnnotation,
        'KnowledgeEntity': KnowledgeEntity
    }


@app.cli.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    print('✅ 数据库初始化完成！')


@app.cli.command()
def reset_db():
    """重置数据库（危险操作）"""
    if input('⚠️  确定要重置数据库吗？所有数据将被删除！(yes/no): ').lower() == 'yes':
        db.drop_all()
        db.create_all()
        print('✅ 数据库已重置！')
    else:
        print('❌ 操作已取消')


@app.cli.command()
def seed_knowledge():
    """添加示例知识库数据"""
    sample_entities = [
        ('张三', '人名'),
        ('李四', '人名'),
        ('王五', '人名'),
        ('北京', '地名'),
        ('上海', '地名'),
        ('广州', '地名'),
        ('清华大学', '组织机构'),
        ('北京大学', '组织机构'),
        ('阿里巴巴', '组织机构'),
        ('2024年', '时间日期'),
        ('今天', '时间日期'),
        ('明天', '时间日期'),
        ('100元', '数值金额'),
        ('1000万', '数值金额'),
    ]
    
    added = 0
    for text, label in sample_entities:
        existing = KnowledgeEntity.query.filter_by(text=text).first()
        if not existing:
            entity = KnowledgeEntity(text=text, label=label, source='seed')
            db.session.add(entity)
            added += 1
    
    db.session.commit()
    print(f'✅ 已添加 {added} 个示例实体到知识库！')


@app.cli.command()
def show_stats():
    """显示系统统计信息"""
    total_files = TextFile.query.count()
    total_words = WordAnnotation.query.count()
    total_entities = EntityAnnotation.query.count()
    total_knowledge = KnowledgeEntity.query.count()
    
    print('\n📊 系统统计信息')
    print('=' * 50)
    print(f'文件总数: {total_files}')
    print(f'词语标注总数: {total_words}')
    print(f'实体标注总数: {total_entities}')
    print(f'知识库实体总数: {total_knowledge}')
    
    from sqlalchemy import func
    entity_stats = db.session.query(
        EntityAnnotation.label,
        func.count(EntityAnnotation.id)
    ).group_by(
        EntityAnnotation.label
    ).all()
    
    if entity_stats:
        print('\n实体类型分布:')
        for label, count in entity_stats:
            print(f'  {label}: {count}')
    
    print('=' * 50 + '\n')


if __name__ == '__main__':
    # 确保数据库已初始化
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # 检查是否是 reloader 子进程，避免重复打印
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print('\n' + '=' * 60)
        print('🚀 文本标注系统启动中...')
        print('=' * 60)
        print(f'📍 访问地址: http://127.0.0.1:{port}')
        print(f'🔧 调试模式: {"开启" if debug else "关闭"}')
        print(f'📦 支持实体类型: 人名、地名、组织机构、时间日期、数值金额')
        print('=' * 60 + '\n')
    
    app.run(host='0.0.0.0', port=port, debug=debug)