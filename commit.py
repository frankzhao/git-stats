from datetime import datetime


class Commit:
    def __init__(
            self,
            commit='',
            abbreviated_commit='',
            tree='',
            abbreviated_tree='',
            parent='',
            abbreviated_parent='',
            refs='',
            encoding='',
            subject='',
            sanitized_subject_line='',
            body='',
            commit_notes='',
            verification_flag='',
            signer='',
            signer_key='',
            author=None,
            committer=None):
        self.commit = commit
        self.abbreviated_commit = abbreviated_commit
        self.tree = tree
        self.abbreviated_tree = abbreviated_tree
        self.parent = parent
        self.abbreviated_parent = abbreviated_parent
        self.refs = refs
        self.encoding = encoding
        self.subject = subject
        self.sanitized_subject_line = sanitized_subject_line
        self.body = body
        self.commit_notes = commit_notes
        self.verification_flag = verification_flag
        self.signer = signer
        self.signer_key = signer_key
        self.author = Author(**author)
        self.committer = Committer(**committer)


class AuthorDetails:
    def __init__(self, name, email, date):
        self.name = name
        self.email = email
        self.date = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')


class Author(AuthorDetails):
    def __init__(self, name, email, date):
        super(Author, self).__init__(name, email, date)


class Committer(AuthorDetails):
    def __init__(self, name, email, date):
        super(Committer, self).__init__(name, email, date)
