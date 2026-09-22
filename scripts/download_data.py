import argparse
from pathlib import Path
from urllib.request import urlopen


URLS = {
    2024: "https://price-paid-data.publicdata.landregistry.gov.uk/pp-2024.csv",
    2025: "https://price-paid-data.publicdata.landregistry.gov.uk/pp-2025.csv",
}


def download(year: int, output_dir: Path) -> Path:
    destination = output_dir / f"pp-{year}.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    with urlopen(URLS[year], timeout=60) as response, destination.open("wb") as output:
        if response.status >= 400:
            raise RuntimeError(f"download failed with HTTP status {response.status}")
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Land Registry price-paid CSV files")
    parser.add_argument("years", nargs="+", type=int, choices=URLS)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    for year in args.years:
        print(download(year, args.output_dir))