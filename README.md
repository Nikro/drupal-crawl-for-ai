# Drupal Crawl for AI

This repository contains a collection of tools to fetch and compile Drupal documentation into formats suitable for AI context feeding. These crawlers extract valuable information from Drupal.org to provide comprehensive context for AI assistants working with Drupal projects.

## Purpose

The primary goal of this project is to create specialized datasets that can be used as context for large language models (LLMs) when answering Drupal-related queries. By feeding these compiled documents to AI systems, we can enhance their understanding of:

- Drupal's architectural changes between versions
- API modifications
- Deprecations and migrations
- Best practices and coding standards

## Setup

### Prerequisites

- Python 3.6+
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/drupal-crawl-for-ai.git
   cd drupal-crawl-for-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Available Crawlers

### 1. Change Records Fetcher (`fetch_changes.py`)

This tool compiles all Drupal change records for specified versions into a single text file, which can then be used as context for AI systems.

#### Features
- Crawls Drupal.org's change records for Drupal 11 branches (11.0.x, 11.1.x, 11.2.x)
- Supports both HTML and Markdown output formats
- Follows pagination to ensure all records are captured
- Prevents duplicate entries
- Politely paces requests to avoid overwhelming the server

#### Usage

Basic usage (HTML output):
```bash
python fetch_changes.py
```

Generate Markdown output:
```bash
python fetch_changes.py --markdown
```

Specify a custom output file:
```bash
python fetch_changes.py --output drupal11_changes.txt
```

Combine options:
```bash
python fetch_changes.py --markdown --output drupal11_changes.md
```

### 2. API Documentation Fetcher (`fetch_api.py`)

This tool compiles Drupal API documentation from the official Drupal APIs page into a single text file for AI context.

#### Features
- Extracts all API links from the Drupal APIs landing page
- Follows each link to capture detailed API documentation
- Supports both HTML and Markdown output formats
- Prevents duplicate entries
- Includes polite request pacing with 1-second delays

#### Usage

Basic usage (HTML output):
```bash
python fetch_api.py
```

Generate Markdown output:
```bash
python fetch_api.py --markdown
```

Specify a custom output file:
```bash
python fetch_api.py --output drupal_apis.txt
```

Combine options:
```bash
python fetch_api.py --markdown --output drupal_apis.md
```

## Output

The generated files contain all documentation with clear separators between entries, making it easy to parse or read. Each section is prefixed with its source URL for reference.

## Additional Planned Crawlers

We are planning to add more crawlers to fetch additional Drupal documentation sources, such as:

- Drupal coding standards
- Common hooks and their implementations
- Contributed module documentation

## Intended Use

The compiled data is intended to be used as:

1. Context files for AI assistants and large language models
2. Reference material for developers working on Drupal version migrations
3. Training data for fine-tuning specialized Drupal AI models
4. Comprehensive documentation for rapid onboarding of developers new to Drupal

## License

This project is released under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
