# Graycat AI Server Documentation

This repository contains the documentation for Graycat AI Server, automatically built and deployed using GitHub Pages.

## Local Development

To run the documentation site locally:

```bash
# Install dependencies
cd docs
bundle install

# Serve locally
bundle exec jekyll serve

# Open http://localhost:4000
```

## Adding Documentation

### New Pages

1. Create a new `.md` file in the `docs/` directory
2. Add front matter with appropriate metadata:

```yaml
---
layout: page
title: Your Page Title
nav_order: 5
---
```

3. Write your content in Markdown
4. Commit and push to deploy automatically

### Component Documentation

For detailed component documentation, add files to `docs/_components/`:

```yaml
---
layout: page
title: Component Name
parent: Components
---
```

### Navigation

Update `docs/_config.yml` to add pages to the header navigation:

```yaml
header_pages:
  - index.md
  - getting-started.md
  - your-new-page.md
```

## Deployment

Documentation is automatically deployed to GitHub Pages when:

- Changes are pushed to the `main`/`master` branch
- Changes are made to files in the `docs/` directory
- The deployment workflow is manually triggered

The site is available at: `https://graycathq.github.io/graycat-aiserver`

## Structure

```
docs/
├── _config.yml          # Jekyll configuration
├── Gemfile             # Ruby dependencies
├── index.md            # Homepage
├── getting-started.md  # Getting started guide
├── architecture.md     # Architecture overview
├── api-reference.md    # API documentation
├── deployment.md       # Deployment guide
├── troubleshooting.md  # Troubleshooting guide
└── _components/        # Component-specific docs
    ├── api-service.md
    ├── gpu-workers.md
    ├── redis-queue.md
    └── monitoring.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your documentation changes
4. Test locally with `bundle exec jekyll serve`
5. Submit a pull request

## Theme and Styling

The documentation uses the [Minima](https://github.com/jekyll/minima) theme with custom configuration for:

- Code syntax highlighting
- Responsive navigation
- SEO optimization
- Social media integration

To customize styling, modify the theme variables in `_config.yml` or add custom CSS files.