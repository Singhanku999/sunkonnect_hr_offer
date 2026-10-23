"""Manual parity-test checklist; run inside Frappe test context after app wiring."""

TEST_CASES = [
    # designation, target monthly net, expected policy behavior
    ("Site Helper / Office Boy / Housekeeping", 15000, "gross/basic must respect Unskilled wage floor"),
    ("Consultant / Executive / Engineer", 50000, "Skilled wage category; PF/ESI and net calculation"),
    ("Intern – engineering (any qualification)", 12000, "trainee floor is max(75% category, Unskilled wage)"),
    ("Manager", 80000, "Highly skilled wage category; PF ceiling applied"),
    ("Analyst – administration / data entry / telecalling / coordination", 18000, "Semi-skilled wage category"),
]

# For each case, compare every monthly/annual output against Excel after the workbook formulas
# are repaired/recalculated in a spreadsheet engine. Record tolerances and sign-off before production.
