# WebScraping_Bots

This repository is a growing collection of web scrapers built to extract structured product data from different platforms.  
Each scraper is designed with reliability, scalability, and maintainability in mind — perfect for both personal experiments and client-ready solutions.

---

## 🚀 Projects

### 1. WishWeb E-Commerce Scraper
- **Type:** Personal project  
- **Goal:** Scrape product data across different categories using **Selenium**.  
- **Features:**
  - Handles dynamic loading of pages.
  - Extracts product details across multiple categories.
  - Produces clean CSV outputs for analysis.  
- **Output Example:** `Output/102428_T-shirts_File.csv`

---

### 2. Idealo E-Commerce Scraper
- **Type:** Client project  
- **Goal:** Scrape product prices, expected delivery dates, and available units from **idealo.de**.  
- **Features:**
  - Input requires a product **EAN** or **title** via `Input Product Data.csv`.
  - Extracts:
    - Product price 💰
    - Expected delivery 📦
    - Number of units available (if not provided, assigns a random number between 10–75).
  - Produces a final output file: `Final_product_data.csv`.  
- **Libraries Used:**
  - `pandas`, `numpy`, `re`, `time`, `random`
  - `curl_cffi` (for robust HTTP requests with error handling)
  - `BeautifulSoup` (for HTML parsing)
  - Standard libraries: `os`, `sys`, `copy`, `urllib.parse`

---

## ⚙️ Installation & Setup

Clone the repository:

```bash
git clone https://github.com/yourusername/WebScraping_Bots.git
cd WebScraping_Bots
```

Install dependencies for each scraper:

```bash
pip install -r WishWeb_ECommerce_Scraper/requirements.txt
pip install -r Idealo_ECommerce_Scraper/requirements.txt
```

## ▶️ Usage

**WishWeb Scraper**

```bash
python WishWeb_ECommerce_Scraper/main.py
```
Output will be saved in the `Output/` folder.

**Idealo Scraper**
- Add product EANs or titles to Input Product Data.csv.
```bash
python Idealo_ECommerce_Scraper/main.py
```
- Final results will be saved as `Final_product_data.csv`.

## 🤝 Contributing
Contributions, ideas, and improvements are welcome!
Feel free to fork the repo, open issues, or submit pull requests.