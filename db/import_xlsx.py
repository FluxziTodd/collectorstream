"""Import existing WNBA Prospects spreadsheet into the database."""

import sys
from pathlib import Path
import openpyxl
from db.models import init_db, upsert_player


def import_spreadsheet(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active

    current_draft_year = None
    imported = 0

    for row in ws.iter_rows(min_row=1, values_only=True):
        first_cell = row[0]

        if first_cell is None or str(first_cell).strip() == "":
            # Check if the second column (index 1) has a header or is empty
            continue

        val = str(first_cell).strip()

        # Check if this row is a year header
        if val.isdigit() and 2025 <= int(val) <= 2035:
            current_draft_year = int(val)
            print(f"\n--- Draft Class {current_draft_year} ---")
            continue

        # Skip header row
        if val.lower() in ("name", "player", ""):
            continue

        if current_draft_year is None:
            continue

        # This is a player row
        name = val
        # Column B (index 1) is blank, Column C (index 2) is College
        school = None
        if len(row) > 2 and row[2] is not None:
            school = str(row[2]).strip() or None

        player_id = upsert_player(name, current_draft_year, school=school)
        print(f"  Imported: {name} (class of {current_draft_year})")
        imported += 1

    print(f"\nTotal imported: {imported} players")
    return imported


if __name__ == "__main__":
    init_db()
    xlsx_path = sys.argv[1] if len(sys.argv) > 1 else "/Users/toddwallace/Desktop/WNBA Prospects.xlsx"
    import_spreadsheet(xlsx_path)
