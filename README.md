# Seven Star Senior Wellness Guide

An interactive Streamlit application designed to help seniors, caregivers, and families navigate healthcare resources and Medicare options.

## Features

- 🔎 Find Healthcare Near Me
  - Search hospitals and healthcare providers by ZIP code
  - View nearby healthcare facilities

- 📋 Medicare Plan Explorer
  - Search Medicare Advantage and Part D plans
  - Filter by ZIP code, premium, star rating, drug coverage, and SNP plans
  - Compare plans side-by-side



## Data Sources

This application uses publicly available data from:

- Centers for Medicare & Medicaid Services (CMS)
- CMS Medicare Advantage Landscape files
- CMS Provider Data
- US ZIP Code Reference Data

No protected health information (PHI) is collected or stored.

## Technology Stack

- Streamlit
- Python
- Pandas
- NumPy
- Plotly

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

## Project Structure

```
app.py
requirements.txt
README.md

pages/
    1_Find_Healthcare_Near_Me.py
    3_Medicare_Basics.py

data/
    hospitals.csv
    ma_landscape.csv
    star_ratings.csv
    uszips.csv
```

## Disclaimer

This application is intended for educational and healthcare navigation purposes only.

Information is based on publicly available CMS datasets. Medicare plan availability, benefits, premiums, and provider information may change over time. Users should verify current information with Medicare.gov or the healthcare provider before making decisions.

## Future Enhancements

- Medical Library
- AI Wellness Guide
- Caregiver Knowledge Base
- Expanded Medicare comparison tools
- Additional healthcare resource search capabilities
