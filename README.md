# KOR-Analysis

A Data Analysis project that visualizes real data from a database to help make business decisions. The app displays bike maintenance data from KOR (Keep On Riding) — tracking part wear, service history, and fleet statistics across users and shops.

## Instructions for Build and Use

Steps to build and/or run the software:

1. Install Python 3 (3.9+) if not already installed
2. Install dependencies: `pip3 install pandas matplotlib`
3. Run the application: `python3 main.py`

Instructions for using the software:

1. **Shop Dashboard** — Overview of total bikes, active users, and parts needing service. Shows bikes per shop and bike type distribution.
2. **Part Health Monitor** — Select any bike from the dropdown to see a color-coded bar chart of how worn each component is (green < 70%, orange 70–99%, red ≥ 100% overdue).
3. **Service History** — Bar charts of the most-replaced parts and service events over time, plus a scrollable table of the 30 most recent service events.
4. **Fleet Analytics** — Top users by total miles, average miles by bike type, and a breakdown of parts replaced due to breakage vs. normal wear.

## Development Environment

To recreate the development environment, you need the following software and/or libraries with the specified versions:

* Python 3.9+
* pandas (data loading and analysis)
* matplotlib (charts and visualization, embedded via TkAgg backend)
* tkinter (built into Python — no separate install needed)

## Youtube link Demo
[KOR-Analysis]()

## Useful Websites to Learn More

I found these websites useful in developing this software:

* [pandas documentation](https://pandas.pydata.org/docs/)
* [matplotlib documentation](https://matplotlib.org/stable/index.html)
* [tkinter documentation](https://docs.python.org/3/library/tkinter.html)

## Future Work

The following items I plan to fix, improve, and/or add to this project in the future:

* [ ] Add date-range filtering to the Service History tab
* [ ] Export filtered data and charts to PDF/PNG
* [ ] Add per-shop filtering across all tabs
