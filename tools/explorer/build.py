"""Build site/explorer.html, the interactive pipeline explorer.

Reads the yearly CSVs in data/loading/, packs them into compact JSON, and
injects that JSON into tools/explorer/template.html. The page recomputes the
gold-layer values in the browser with the same logic as the dbt models, so
rebuild it whenever the data or those models change.

Usage (from the repository root):
    python tools/explorer/build.py                  # writes site/explorer.html
    python tools/explorer/build.py --fragment OUT   # page body only, no <html>/<head> wrapper
"""
import argparse
import glob
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))

# Row count of the raw CPI download (18100004.csv, 1914 onward). The raw file is
# git-ignored, so the count is recorded here; split_data.py prints the same number.
CPI_RAW_ROWS = 1154918

GEO_ORDER = [
    "Canada", "Newfoundland and Labrador", "Prince Edward Island", "Nova Scotia",
    "New Brunswick", "Quebec", "Ontario", "Manitoba", "Saskatchewan", "Alberta",
    "British Columbia", "Whitehorse, Yukon", "Yellowknife, Northwest Territories",
]
CPI_GROUPS = ["All-items", "Food", "Food purchased from stores"]


def read_years(folder):
    frames, sizes = {}, {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "loading", folder, "*.csv"))):
        year = int(f[-8:-4])
        frames[year] = pd.read_csv(f, dtype=str, keep_default_na=False)
        sizes[year] = os.path.getsize(f)
    return frames, sizes


def build_data():
    avg, avg_sizes = read_years("average-price")
    cpi, cpi_sizes = read_years("province-wise")
    a = pd.concat(avg.values())
    c = pd.concat(cpi.values())

    months = sorted(a.REF_DATE.unique())
    month_idx = {m: i for i, m in enumerate(months)}
    geo_idx = {g: i for i, g in enumerate(GEO_ORDER)}
    unknown = set(a.GEO.unique()) - set(GEO_ORDER)
    if unknown:
        raise SystemExit(f"New regions in the data, add them to GEO_ORDER: {sorted(unknown)}")
    dguid = {r.GEO: r.DGUID for r in a.drop_duplicates("GEO").itertuples()}
    products = sorted(a.Products.unique(), key=str.lower)
    prod_idx = {p: i for i, p in enumerate(products)}

    # One entry per region/product series: [vector, coordinate, first month index, raw VALUE strings]
    series = {}
    for (geo, prod), d in a.groupby(["GEO", "Products"]):
        d = d.sort_values("REF_DATE")
        first = month_idx[d.REF_DATE.iloc[0]]
        if month_idx[d.REF_DATE.iloc[-1]] - first + 1 != len(d):
            raise SystemExit(f"Series has a month gap, LAG offsets would be wrong: {geo} / {prod}")
        series[f"{geo_idx[geo]}|{prod_idx[prod]}"] = [d.VECTOR.iloc[0], d.COORDINATE.iloc[0], first, ",".join(d.VALUE)]

    cpi_months = sorted(c.REF_DATE.unique())
    cpi_series = {}
    canada = c[c.GEO == "Canada"]
    for grp in CPI_GROUPS:
        d = canada[canada["Products and product groups"] == grp].sort_values("REF_DATE")
        r = d.iloc[0]
        cpi_series[grp] = [r.DGUID, r.VECTOR, r.COORDINATE, r.UOM, r.UOM_ID, r.DECIMALS, ",".join(d.VALUE), ",".join(d.STATUS)]

    years = {
        str(y): {"a": [len(avg[y]), avg_sizes[y]], "c": [len(cpi[y]), cpi_sizes[y]]}
        for y in sorted(avg)
    }
    return {
        "months": months, "cpiMonths": cpi_months,
        "geos": [[g, dguid[g]] for g in GEO_ORDER], "products": products,
        "series": series, "cpi": cpi_series, "years": years,
        "cpiRaw": CPI_RAW_ROWS, "rawRows": len(a),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fragment", metavar="OUT", help="write the page body only (no <html>/<head> wrapper) to OUT")
    args = ap.parse_args()

    template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    data = json.dumps(build_data(), separators=(",", ":"))
    page = template.replace("/*DATA*/null", data, 1)

    if args.fragment:
        out = args.fragment
    else:
        head, body = page.split("</style>", 1)
        head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
        page = (
            '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="description" content="Follow one Statistics Canada food price row through the S3, Snowflake, dbt and Power BI pipeline.">\n'
            + head + "</style>\n</head>\n<body>\n" + body.lstrip("\n") + "\n</body>\n</html>\n"
        )
        out = os.path.join(ROOT, "site", "explorer.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {os.path.relpath(out, ROOT) if out.startswith(ROOT) else out} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
