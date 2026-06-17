"""CLI entrypoint:  python -m intel <command>   (or the `intel` console script)."""
import sys, argparse
from . import __version__, config as configmod


def build_parser():
    p = argparse.ArgumentParser(
        prog='intel', description='Ad Comment Intel — rank ad posts, scrape comments, publish a searchable gallery.')
    p.add_argument('--version', action='version', version=f'ad-comment-intel {__version__}')
    sub = p.add_subparsers(dest='cmd')

    sub.add_parser('setup', help='interactive onboarding (writes config.env)')
    sub.add_parser('doctor', help='verify Meta + R2 connectivity')

    r = sub.add_parser('rank', help='rank posts by spend + ROI (writes CSVs + pull list)')

    pl = sub.add_parser('pull', help='scrape comments for the selected posts')
    pl.add_argument('--fresh', action='store_true', help='re-pull posts already scraped')
    pl.add_argument('--no-replies', action='store_true', help='skip reply threads (faster)')
    pl.add_argument('--no-r2', action='store_true', help='skip media mirroring to R2')

    g = sub.add_parser('gallery', help='build + publish the gallery from the JSON store')
    g.add_argument('--no-upload', action='store_true', help='build locally, do not upload')

    rn = sub.add_parser('run', help='end-to-end: rank -> pull -> gallery')
    rn.add_argument('--rank-only', action='store_true', help='stop after ranking')
    rn.add_argument('--fresh', action='store_true', help='re-pull posts already scraped')
    rn.add_argument('--no-replies', action='store_true', help='skip reply threads')
    rn.add_argument('--no-r2', action='store_true', help='skip media mirroring')
    rn.add_argument('--no-upload', action='store_true', help='build gallery locally only')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.cmd:
        build_parser().print_help(); return 0

    cfg = configmod.load()
    if args.cmd != 'setup' and not cfg.token:
        print("No config found (or token missing). Run:  intel setup")
        return 1

    if args.cmd == 'setup':
        from . import setup_wizard; return setup_wizard.main(cfg, args)
    if args.cmd == 'doctor':
        from . import doctor; return doctor.main(cfg, args)
    if args.cmd == 'rank':
        from . import rank_posts; rank_posts.main(cfg, args); return 0
    if args.cmd == 'pull':
        from . import pull_comments; pull_comments.main(cfg, args); return 0
    if args.cmd == 'gallery':
        from . import gallery; gallery.main(cfg, args); return 0
    if args.cmd == 'run':
        from . import run; run.main(cfg, args); return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
