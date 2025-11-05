# Sphinx API Documentation

This directory contains the Sphinx configuration and source files for automatically generated API documentation.

## Overview

The API documentation is automatically generated from docstrings in the source code using Sphinx's `autodoc` extension. The documentation is built in HTML format and can be viewed locally or hosted online.

## Building the Documentation

### Prerequisites

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Ensure Sphinx is installed:
   ```bash
   pip install -r requirements.txt
   ```

### Build Commands

Build HTML documentation:
```bash
cd docs/sphinx
sphinx-build -b html source build
```

The generated HTML files will be in `docs/sphinx/build/`.

### Viewing the Documentation

Open `docs/sphinx/build/index.html` in a web browser to view the documentation.

### Clean Build

To remove all generated files and rebuild from scratch:
```bash
cd docs/sphinx
rm -rf build
sphinx-build -b html source build
```

## Documentation Structure

- `source/` - Sphinx source files (reStructuredText)
  - `conf.py` - Sphinx configuration file
  - `index.rst` - Main documentation index
  - `modules.rst` - API reference documentation
- `build/` - Generated documentation (HTML, etc.)
- `_static/` - Static files (CSS, images, etc.)
- `_templates/` - Custom templates

## Configuration

The main configuration file is `source/conf.py`. Key settings:

- **Autodoc**: Enabled with `sphinx.ext.autodoc` extension
- **Theme**: Read the Docs theme (`sphinx_rtd_theme`)
- **Mock Imports**: External dependencies are mocked to allow builds without all dependencies
- **Path Setup**: Project root is added to Python path for module imports

## Updating Documentation

1. **Update docstrings** in source code files
2. **Rebuild documentation**:
   ```bash
   cd docs/sphinx
   sphinx-build -b html source build
   ```
3. **Review changes** in `build/index.html`

## Adding New Modules

To document new modules:

1. Add the module to `source/modules.rst`:
   ```rst
   .. automodule:: app.new_module
      :members:
      :show-inheritance:
   ```

2. Rebuild the documentation

## Troubleshooting

### Module Import Errors

If you see "No module named 'app'" errors:
- Verify the path setup in `conf.py` is correct
- Ensure you're running from the project root
- Check that the virtual environment is activated

### Docstring Formatting Errors

Some docstring formatting issues may cause warnings. These are usually minor and don't prevent the build from succeeding. To fix:
- Ensure proper indentation in docstrings
- Use proper reStructuredText syntax
- Add blank lines where needed

## Publishing Documentation

### GitHub Pages (Recommended)

The documentation can be published to GitHub Pages using the provided script:

```bash
cd docs/sphinx
./publish.sh
```

This script will:
1. Build the documentation
2. Create/update the `gh-pages` branch
3. Copy the built files to the branch
4. Prepare for pushing to GitHub

**After running the script:**

1. Review the changes:
   ```bash
   git diff gh-pages
   ```

2. Push to GitHub:
   ```bash
   git push origin gh-pages
   ```

3. Enable GitHub Pages in repository settings:
   - Go to: Repository Settings > Pages
   - Source: Deploy from a branch
   - Branch: `gh-pages` / `/ (root)`
   - Click Save

4. Your documentation will be available at:
   `https://[username].github.io/[repository-name]/`

### Manual Publishing

To publish manually:

1. Build the documentation:
   ```bash
   cd docs/sphinx
   sphinx-build -b html source build
   ```

2. Create `.nojekyll` file in build directory:
   ```bash
   touch build/.nojekyll
   ```

3. Use one of these methods:
   - **GitHub Pages**: Copy `build/` contents to `gh-pages` branch
   - **Read the Docs**: Connect repository to Read the Docs
   - **Netlify/Vercel**: Deploy `build/` directory
   - **Static hosting**: Upload `build/` directory contents

## Integration with CI/CD

The documentation can be integrated into CI/CD pipelines:

```bash
# In CI/CD script
cd docs/sphinx
sphinx-build -b html source build
touch build/.nojekyll  # Required for GitHub Pages
# Deploy build/ directory to hosting service
```

### GitHub Actions Example

```yaml
name: Deploy Documentation
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Build documentation
        run: |
          cd docs/sphinx
          sphinx-build -b html source build
          touch build/.nojekyll
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/sphinx/build
```

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Autodoc Extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)

