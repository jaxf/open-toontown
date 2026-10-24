"""Run on the server: python -m server.accounts --db PATH issue FRIEND."""
import argparse
from otp.login.TokenStore import ACCESS, TokenStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    issue = sub.add_parser('issue')
    issue.add_argument('identity')
    issue.add_argument('--access', choices=ACCESS, default='NO_ACCESS')
    issue.add_argument('--days', type=int, default=30)
    revoke = sub.add_parser('revoke')
    revoke.add_argument('identity')
    args = parser.parse_args()
    store = TokenStore(args.db)
    if args.command == 'issue':
        print(store.issue(args.identity, args.access, args.days))
    else:
        print('Revoked %s credentials. Existing sessions require disconnect/restart.' %
              store.revoke(args.identity))


if __name__ == '__main__':
    main()
