# ANGSUMI blog

Source for **https://blog.angsumi.online/**: practical, source-cited explanations of bioinformatics and research data analysis.

- `posts/*.md`: one Markdown file per post, with front-matter (title, description, date, cluster, service, guide, guide_title, faq). The first paragraph is a 40–60-word direct answer.
- `build.py`: renders posts, index, RSS feed, sitemap and `posts.json` into `dist/` (standard library only). Styling comes from angsumi.online.
- `.github/workflows/deploy.yml`: builds and deploys on every push to `main`.

`posts.json` is read by the angsumi.online build to list recent posts on the main site.
