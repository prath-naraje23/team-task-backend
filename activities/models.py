from mongoengine import (
    Document, StringField, DateTimeField,
    ReferenceField, DictField,
)
from datetime import datetime


class Activity(Document):
    action = StringField(required=True)
    # Human-readable sentence matching the requirement format:
    # e.g. 'Saumyakanta changed status of "Design API endpoints" to In Progress.'
    message = StringField(default='')
    user = ReferenceField('accounts.User', required=True)
    task = ReferenceField('tasks.Task', null=True)
    team = ReferenceField('teams.Team', null=True)
    details = DictField(default=dict)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'activities',
        'indexes': ['user', 'task', 'team'],
        'ordering': ['-created_at'],
    }

    def to_dict(self):
        return {
            'id': str(self.id),
            'action': self.action,
            'message': self.message,
            'user': self.user.to_dict(),
            'task': str(self.task.id) if self.task else None,
            'team': str(self.team.id) if self.team else None,
            'details': self.details,
            'created_at': self.created_at.isoformat(),
        }
