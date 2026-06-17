"""End-to-end: rank posts -> select top spenders + positive ROI -> scrape comments
-> build + publish the searchable gallery. One command."""
from . import rank_posts, pull_comments, gallery


def main(cfg, args):
    posts, wins = rank_posts.rank(cfg)
    ids, by_spend, roi = rank_posts.select(cfg, posts)
    rank_posts.write_csvs(cfg, by_spend, roi)
    (cfg.outdir / 'post_list.txt').write_text(
        '# selected ad posts (top spenders + positive ROI)\n' + '\n'.join(sorted(ids)) + '\n',
        encoding='utf-8')

    tot_sp = sum(r[1] for r in by_spend)
    print(f"\nRanked {len(posts)} posts | total spend ${tot_sp:,.0f}")
    print(f"Positive-ROI (spend>=${cfg.num('MIN_SPEND',300):.0f} & ROAS>{cfg.num('MIN_ROAS',1):.2f}): {len(roi)}")
    print(f"Selected for comment pull: {len(ids)}\n")
    if getattr(args, 'rank_only', False):
        print("Stopping after rank (--rank-only).")
        return

    pull_comments.run_batch(cfg, ids, skip_existing=not args.fresh,
                            no_replies=args.no_replies, no_r2=args.no_r2)
    out, url = gallery.build(cfg, upload=not args.no_upload)
    print("\n=== DONE ===")
    print(f"Local gallery: {out}")
    if url:
        print(f"Shareable gallery: {url}")
    else:
        print("Gallery built locally. Configure R2 (intel setup) to publish a shareable URL.")
