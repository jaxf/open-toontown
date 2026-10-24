"""Small invite-only account bridge. Tokens are random secrets, not passwords.

Use only over an encrypted private network until the public transport/auth audit
is complete. Astron remains the authority for Toon data; SQLite stores identity
links and SHA-256 hashes of 256-bit random invitation tokens, never raw tokens.
"""
from contextlib import closing
import hashlib
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time

ACCESS = ('NO_ACCESS', 'MODERATOR', 'DEVELOPER', 'ADMIN', 'SYSTEM_ADMIN')


class TokenStore:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if os.name == 'posix' and self.path.stat().st_mode & 0o077:
                raise ValueError('Account bridge database must have mode 0600')
        else:
            os.close(fd)
        with closing(self.connect()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS identities (
                    identity TEXT PRIMARY KEY, access TEXT NOT NULL,
                    account_id INTEGER UNIQUE);
                CREATE TABLE IF NOT EXISTS tokens (
                    digest TEXT PRIMARY KEY, identity TEXT NOT NULL,
                    expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(identity) REFERENCES identities(identity));
            ''')

    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=5)
        db.execute('PRAGMA foreign_keys = ON')
        return db

    def issue(self, identity, access='NO_ACCESS', days=30):
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', identity):
            raise ValueError('Identity must be 1–64 letters, numbers, underscores or hyphens')
        if access not in ACCESS or not 1 <= days <= 365:
            raise ValueError('Invalid access level or expiry (1–365 days)')
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode('ascii')).hexdigest()
        with closing(self.connect()) as db, db:
            # Issuing another credential must never silently change privileges.
            db.execute('INSERT OR IGNORE INTO identities(identity, access) VALUES (?, ?)',
                       (identity, access))
            existing = db.execute('SELECT access FROM identities WHERE identity=?',
                                  (identity,)).fetchone()[0]
            if existing != access:
                raise ValueError('Existing identity has a different access level')
            db.execute('INSERT INTO tokens(digest,identity,expires) VALUES (?,?,?)',
                       (digest, identity, int(time.time()) + days * 86400))
        return token

    def lookup(self, token):
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
            return None
        digest = hashlib.sha256(token.encode('ascii')).hexdigest()
        with closing(self.connect()) as db:
            row = db.execute('''SELECT i.identity, i.access, i.account_id FROM tokens t
                JOIN identities i ON i.identity=t.identity
                WHERE t.digest=? AND t.revoked=0 AND t.expires>?''',
                (digest, int(time.time()))).fetchone()
        return dict(databaseId=row[0], accessLevel=row[1], accountId=row[2] or 0) if row else None

    def bind_account(self, identity, account_id):
        if type(account_id) is not int or not 100000000 <= account_id <= 399999999:
            return False
        with closing(self.connect()) as db, db:
            try:
                changed = db.execute('''UPDATE identities SET account_id=?
                    WHERE identity=? AND (account_id IS NULL OR account_id=?)''',
                    (account_id, identity, account_id)).rowcount
            except sqlite3.IntegrityError:
                return False
        return bool(changed)

    def revoke(self, identity):
        with closing(self.connect()) as db, db:
            return db.execute('UPDATE tokens SET revoked=1 WHERE identity=?', (identity,)).rowcount
