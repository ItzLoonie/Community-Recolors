from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent
OUTPUT = ROOT / "README.md"

TARGETS = [
    ROOT / "Common",
    ROOT / "BTOS2"
]

MERGE_IGNORED_PARTS = {
    "Buckets",
    "Effects"
}


def clean_name(name):
    return Path(name).stem.replace("_", " ")


def ignored(path):
    excluded_folders = ["EasterEggs", "Regular", "Effects", "Factionless", "Custom"]

    return any(
        excluded in part
        for part in path.parts
        for excluded in excluded_folders
    )

def normalize_folder(path: Path):
    parts = list(path.parts)

    # Remove ignored segments
    filtered = [p for p in parts if p not in MERGE_IGNORED_PARTS]

    return Path(*filtered)

def ignored_asset(name):
    excluded_assets = ["Ability", "Special"]

    name = name.lower()
    return any(x.lower() in name for x in excluded_assets)

def safe_relative(path: Path):
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return None

def scan_folders():
    folders = defaultdict(set)

    for root in TARGETS:
        if not root.exists():
            continue

        for folder in root.rglob("*"):
            if not folder.is_dir():
                continue

            if ignored(folder):
                continue

            norm_folder = normalize_folder(folder)

            rel = safe_relative(norm_folder)
            if rel is None:
                continue  # ❌ prevents Steam absolute path leakage

            contents = folders[str(rel)]

            for file in folder.iterdir():
                if not file.is_file():
                    continue

                if ignored(file):
                    continue

                if ignored_asset(file.name):
                    continue

                contents.add(clean_name(file.name))

    return folders

def generate_missing(folders):
    output = []

    for directory, contents in folders.items():

        # Compare against every other folder
        comparison = set()

        for other_dir, other_contents in folders.items():
            if other_dir != directory:
                comparison |= other_contents

        missing = sorted(comparison - contents)

        output.append({
            "directory": directory,
            "contents": sorted(contents),
            "missing": missing
        })

    return output


def write_markdown(data):
    grouped = defaultdict(list)

    # keep only folders with missing items
    for row in data:
        if not row["missing"]:
            continue

        root, *sub = row["directory"].split("/", 1)
        folder_name = sub[0] if sub else root

        grouped[root].append({
            "folder": folder_name,
            "missing": row["missing"]
        })

    with OUTPUT.open("w", encoding="utf-8") as f:
        f.write("# Missing assets\n\nDo keep in mind this also contains listings that are not required, as the Python script used to generate this file just checks if a file is present in one folder and not others.\nThe script also ignores status effects and abilities, otherwise it ends up being quite bloated.\n\n")

        if not grouped:
            f.write("All assets are complete 🎉\n")
            return

        for root, rows in grouped.items():
            f.write("| Directory | Missing |\n")
            f.write("|---|---|\n")

            for row in rows:
                missing = ", ".join(row["missing"])
                f.write(f"| {row['folder']} | {missing} |\n")

            f.write("\n")


if __name__ == "__main__":
    folders = scan_folders()
    report = generate_missing(folders)
    write_markdown(report)

    print("Generated Contents.md")