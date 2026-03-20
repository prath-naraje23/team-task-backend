from mongoengine import (
    Document, EmbeddedDocument,
    StringField, EmailField, DateTimeField,
    ReferenceField, ListField, EmbeddedDocumentField,
)
from datetime import datetime
import secrets


class TeamInvitation(EmbeddedDocument):
    email = EmailField(required=True)
    token = StringField(required=True)
    status = StringField(default='pending', choices=['pending', 'accepted', 'declined'])
    created_at = DateTimeField(default=datetime.utcnow)

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)


class Team(Document):
    name = StringField(required=True, max_length=100)
    description = StringField(max_length=500, default='')
    owner = ReferenceField('accounts.User', required=True)
    members = ListField(ReferenceField('accounts.User'))
    invitations = ListField(EmbeddedDocumentField(TeamInvitation))
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'teams',
        'indexes': ['owner'],
    }

    def is_member(self, user):
        member_ids = [str(m.id) for m in self.members]
        return str(user.id) == str(self.owner.id) or str(user.id) in member_ids

    def to_dict(self, include_members=True):
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'owner': self.owner.to_dict() if include_members else str(self.owner.id),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_members:
            data['members'] = [m.to_dict() for m in self.members]
        return data
