"""Insert a synthetic demo alert and review policy; safe to rerun."""
from sqlalchemy import select

from legacy.flask.database import session_scope
from legacy.flask.models import Alert, Event, User, AlertEvidence, AuditLog, Policy


def main():
    with session_scope() as session:
        if session.scalar(select(Policy).where(Policy.name == 'default-review')) is None:
            session.add(Policy(name='default-review', enabled=True,
                               settings={'upload_review': 'manual'}))
        if session.scalar(select(Event).where(Event.payload['upload_id'].as_string() == 'dev-demo-upload')):
            return
        user = session.scalar(select(User).where(User.name == 'demo-workstation'))
        if user is None:
            user = User(name='demo-workstation')
            session.add(user)
            session.flush()
        alert = Alert(event=Event(user_id=user.id, kind='upload',
                                  payload={'client': user.name, 'filename': 'synthetic-demo.txt',
                                           'upload_url': 'https://example.com/upload',
                                           'upload_id': 'dev-demo-upload'},
                                  timestamp='2026-01-01T12:00:00'),
                      evidence=AlertEvidence(preview='Synthetic demo content',
                                             sensitive=False, matches=[]))
        session.add(alert)
        session.flush()
        session.add(AuditLog(alert_id=alert.id, action='seed_alert_created', details={}))


if __name__ == '__main__':
    main()
