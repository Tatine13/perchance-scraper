# Perchance Scraper

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Status](https://img.shields.io/badge/status-beta-orange)

**Perchance Scraper** is a specialized tool for programmatically interacting with [Perchance.org](https://perchance.org) generators. It enables batch generation, data extraction, and testing of random text generators.

## 🚀 Features

- **Generator Interface**: Connect seamlessly to any public Perchance generator.
- **Batch Processing**: Generate hundreds of outputs in a single run.
- **Structured Export**: Save results to JSON, CSV, or TXT.
- **Headless Mode**: Run efficiently in background processes.

## 📦 Installation

```bash
git clone https://github.com/Tatine13/perchance-scraper.git
cd perchance-scraper
pip install -r requirements.txt
```

## 💻 Usage

```python
from perchance_gen import PerchanceScraper

# Initialize scraper for a specific generator
scraper = PerchanceScraper(generator_url="https://perchance.org/fantasy-name-generator")

# Generate 50 items
results = scraper.generate(count=50)

# Export to file
scraper.save_json(results, "names.json")
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
