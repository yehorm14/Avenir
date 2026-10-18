"""Build the SOC 2020 -> ONS/Adzuna job-advert category map (reviewed, committed as data).

Usage: python -I category_map_build.py PROCESSED_DIR OUT_CSV

Every 4-digit SOC 2020 code gets exactly one of the 28 advert categories, from a rule on its
3-digit group plus 4-digit overrides, and a volatility note where the ONS flagged the category's
series as inconsistent (Education, Marketing/PR, Transport in 2023; Travel in Sept 2023).
Fails loudly if any code is unmapped or any category name is unknown.
"""
import sys
from pathlib import Path

import pandas as pd

CATEGORIES = {"Accounting / Finance", "Admin / clerical / secretarial", "Catering and hospitality", "Charity / voluntary",
              "Construction / trades", "Creative / design / arts & media", "Customer service / support", "Domestic help", "Education",
              "Energy / oil & gas", "Engineering", "Facilities / maintenance", "Graduate", "HR & recruitment", "IT / Computing / Software",
              "Legal", "Management / exec / consulting", "Manufacturing", "Marketing / advertising / PR", "Other / general",
              "Part-time / weekend", "Property", "Wholesale and retail", "Sales", "Scientific / QA", "Transport / logistics / warehouse",
              "Travel / tourism", "Healthcare and Social care"}
VOLATILE = {"Education", "Marketing / advertising / PR", "Transport / logistics / warehouse", "Travel / tourism"}

BY_GROUP = {
    "111": "Management / exec / consulting", "112": "Manufacturing", "113": "Management / exec / consulting",
    "114": "Transport / logistics / warehouse", "115": "Wholesale and retail", "116": "Other / general", "117": "Healthcare and Social care",
    "121": "Other / general", "122": "Catering and hospitality", "123": "Healthcare and Social care", "124": "Transport / logistics / warehouse",
    "125": "Management / exec / consulting",
    "211": "Scientific / QA", "212": "Engineering", "213": "IT / Computing / Software", "214": "Creative / design / arts & media",
    "215": "Scientific / QA", "216": "Scientific / QA",
    "221": "Healthcare and Social care", "222": "Healthcare and Social care", "223": "Healthcare and Social care",
    "224": "Healthcare and Social care", "225": "Healthcare and Social care",
    "231": "Education", "232": "Education",
    "241": "Legal", "242": "Accounting / Finance", "243": "Management / exec / consulting", "244": "Management / exec / consulting",
    "245": "Construction / trades", "246": "Healthcare and Social care", "247": "Education", "248": "Scientific / QA",
    "249": "Marketing / advertising / PR",
    "311": "Engineering", "312": "Engineering", "313": "IT / Computing / Software",
    "321": "Healthcare and Social care", "322": "Healthcare and Social care", "323": "Education", "324": "Healthcare and Social care",
    "331": "Other / general", "341": "Creative / design / arts & media", "342": "Creative / design / arts & media", "343": "Other / general",
    "351": "Transport / logistics / warehouse", "352": "Legal", "353": "Accounting / Finance", "354": "Sales",
    "355": "Sales", "356": "Other / general", "357": "HR & recruitment", "358": "Scientific / QA",
    "411": "Admin / clerical / secretarial", "412": "Accounting / Finance", "413": "Admin / clerical / secretarial",
    "414": "Admin / clerical / secretarial", "415": "Admin / clerical / secretarial", "421": "Admin / clerical / secretarial",
    "511": "Other / general", "521": "Manufacturing", "522": "Manufacturing", "523": "Facilities / maintenance",
    "524": "Construction / trades", "525": "Engineering", "531": "Construction / trades", "532": "Construction / trades",
    "533": "Construction / trades", "541": "Manufacturing", "542": "Manufacturing", "543": "Catering and hospitality", "544": "Manufacturing",
    "611": "Education", "612": "Other / general", "613": "Healthcare and Social care", "621": "Travel / tourism", "622": "Other / general",
    "623": "Domestic help", "624": "Facilities / maintenance", "625": "Catering and hospitality", "631": "Other / general",
    "711": "Wholesale and retail", "712": "Sales", "713": "Wholesale and retail", "721": "Customer service / support",
    "722": "Customer service / support",
    "811": "Manufacturing", "812": "Manufacturing", "813": "Manufacturing", "814": "Manufacturing", "815": "Construction / trades",
    "816": "Manufacturing", "821": "Transport / logistics / warehouse", "822": "Transport / logistics / warehouse",
    "823": "Transport / logistics / warehouse",
    "911": "Other / general", "912": "Construction / trades", "913": "Manufacturing", "921": "Admin / clerical / secretarial",
    "922": "Facilities / maintenance", "923": "Other / general", "924": "Wholesale and retail", "925": "Transport / logistics / warehouse",
    "926": "Catering and hospitality",
}
OVERRIDES = {
    "1225": "Travel / tourism", "1253": "Property", "2135": "IT / Computing / Software", "2141": "Creative / design / arts & media",
    "2142": "Creative / design / arts & media", "2161": "Scientific / QA", "2162": "Scientific / QA", "2454": "Property",
    "2455": "Construction / trades", "2481": "Engineering", "2482": "Scientific / QA", "2483": "Scientific / QA",
    "2491": "Creative / design / arts & media", "2492": "Creative / design / arts & media", "2493": "Marketing / advertising / PR",
    "2494": "Marketing / advertising / PR", "3111": "Scientific / QA", "3115": "Scientific / QA", "3116": "Manufacturing",
    "3541": "Property", "3542": "Transport / logistics / warehouse", "3543": "Admin / clerical / secretarial", "3544": "IT / Computing / Software",
    "3551": "Transport / logistics / warehouse", "3553": "Wholesale and retail", "3554": "Marketing / advertising / PR", "3555": "Property",
    "3557": "Catering and hospitality", "3581": "Scientific / QA", "3582": "Facilities / maintenance",
    "6121": "Facilities / maintenance", "6211": "Other / general", "6232": "Facilities / maintenance", "8133": "Energy / oil & gas",
    "8132": "Energy / oil & gas", "8134": "Facilities / maintenance", "9231": "Other / general", "9232": "Education", "9233": "Education",
    "9262": "Healthcare and Social care", "9267": "Travel / tourism",
}


def category_of(soc: str) -> str:
    if soc in OVERRIDES:
        return OVERRIDES[soc]
    if soc[:3] in BY_GROUP:
        return BY_GROUP[soc[:3]]
    raise KeyError(f"no advert category rule for SOC {soc}")


def main() -> None:
    proc, out = Path(sys.argv[1]), Path(sys.argv[2])
    a = pd.read_parquet(proc / "ashe_long.parquet")
    t = a[a.soc_version == 2020].drop_duplicates("soc_code").sort_values("soc_code")
    bad = [c for c in set(BY_GROUP.values()) | set(OVERRIDES.values()) if c not in CATEGORIES]
    if bad:
        raise SystemExit(f"unknown category names: {bad}")
    rows = [{"soc2020": r.soc_code, "title": r.title, "category": category_of(r.soc_code),
             "volatile_series": category_of(r.soc_code) in VOLATILE} for r in t.itertuples()]
    df = pd.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"{len(df)} codes mapped; categories used: {df.category.nunique()}; volatile: {int(df.volatile_series.sum())}")
    print(df.category.value_counts().head(12).to_string())


if __name__ == "__main__":
    main()
