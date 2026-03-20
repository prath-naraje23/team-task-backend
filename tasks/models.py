from mongoengine import (
    Document, EmbeddedDocument, StringField, DateTimeField,
    ReferenceField, ListField, EmbeddedDocumentField,
)
from datetime import datetime


class Comment(EmbeddedDocument):
    text = StringField(required=True, max_length=1000)
    author = ReferenceField('accounts.User', required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            'text': self.text,
            'author': self.author.to_dict(),
            'created_at': self.created_at.isoformat(),
        }


class Task(Document):
    title = StringField(required=True, max_length=200)
    description = StringField(max_length=2000, default='')
    # Requirement: Pending / In Progress / Done
    status = StringField(default='pending', choices=['pending', 'in_progress', 'done'])
    priority = StringField(default='medium', choices=['low', 'medium', 'high'])
    assigned_to = ReferenceField('accounts.User', null=True)
    team = ReferenceField('teams.Team', required=True)
    created_by = ReferenceField('accounts.User', required=True)
    comments = ListField(EmbeddedDocumentField(Comment), default=list)
    due_date = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'tasks',
        'indexes': ['team', 'assigned_to', 'status'],
        'ordering': ['-created_at'],
    }

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to.to_dict() if self.assigned_to else None,
            'team': str(self.team.id),
            'created_by': self.created_by.to_dict(),
            'comments': [c.to_dict() for c in self.comments],
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
