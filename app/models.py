# app/models.py
from datetime import datetime
from enum import Enum
from app import db


class FileStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'


class TextFile(db.Model):
    __tablename__ = 'text_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default=FileStatus.PENDING)
    
    text_annotations = db.relationship('TextAnnotation', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    word_annotations = db.relationship('WordAnnotation', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    entity_annotations = db.relationship('EntityAnnotation', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'content': self.content,
            'upload_time': self.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status
        }


class TextAnnotation(db.Model):
    __tablename__ = 'text_annotations'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('text_files.id'), nullable=False)
    text_category = db.Column(db.String(50))
    text_sentiment = db.Column(db.String(20))
    sentiment_score = db.Column(db.Float)
    annotate_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'text_category': self.text_category,
            'text_sentiment': self.text_sentiment,
            'sentiment_score': self.sentiment_score
        }


class WordAnnotation(db.Model):
    """分词和词性标注（独立）"""
    __tablename__ = 'word_annotations'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('text_files.id'), nullable=False)
    word_index = db.Column(db.Integer, nullable=False)
    word = db.Column(db.String(100), nullable=False)
    pos = db.Column(db.String(20))  # 12种词性之一
    pos_cn = db.Column(db.String(50))
    
    __table_args__ = (db.Index('idx_file_word', 'file_id', 'word_index'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'word_index': self.word_index,
            'word': self.word,
            'pos': self.pos,
            'pos_cn': self.pos_cn
        }


class EntityAnnotation(db.Model):
    """命名实体标注（独立于分词）"""
    __tablename__ = 'entity_annotations'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('text_files.id'), nullable=False)
    text = db.Column(db.String(200), nullable=False)  # 实体文本
    label = db.Column(db.String(50), nullable=False)  # 5种实体类型
    start_pos = db.Column(db.Integer, nullable=False)  # 起始字符位置
    end_pos = db.Column(db.Integer, nullable=False)    # 结束字符位置
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.Index('idx_file_entity', 'file_id', 'start_pos'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'text': self.text,
            'label': self.label,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos
        }


class KnowledgeEntity(db.Model):
    __tablename__ = 'knowledge_entities'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), unique=True, nullable=False)
    label = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(20), default='manual')
    frequency = db.Column(db.Integer, default=1)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.Index('idx_text', 'text'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'label': self.label,
            'frequency': self.frequency
        }