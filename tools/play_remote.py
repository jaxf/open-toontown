"""Client-only desktop test of the same session route planned for iOS."""
import argparse
import getpass
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True, help='Private/VPN IPv4 of the hosted server')
    parser.add_argument('--port', type=int, default=7198)
    parser.add_argument('--user-data', type=Path, required=True,
                        help='Writable directory outside the game checkout/app bundle')
    args = parser.parse_args()
    from toontown.mobile.Session import Session
    from toontown.mobile.Client import start
    session = Session(args.server, getpass.getpass('Invitation token (hidden): '), args.port)
    start(session, Path(__file__).resolve().parents[1], args.user_data)


if __name__ == '__main__':
    main()
