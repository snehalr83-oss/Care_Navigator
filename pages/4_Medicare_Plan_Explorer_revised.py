import pandas as pd
import streamlit as st

# ============================================================
# FILE LOCATIONS
# ============================================================

DATA_DIR = "data"

ZIP_FILE = f"{DATA_DIR}/uszips.csv"
PLAN_FILE = f"{DATA_DIR}/ma_landscape.csv"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_money(series):
    """
    Convert CMS money fields such as:
    $0.00
    $35
    1,250.00
    Not Applicable
    into numeric values.
    """
    return (
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace(
            [
                "",
                "nan",
                "NaN",
                "None",
                "Not Applicable",
                "Not available",
                "N/A",
            ],
            None,
        )
        .pipe(pd.to_numeric, errors="coerce")
    )


def clean_rating(series):
    """
    Extract numeric CMS star ratings.
    Examples:
        4.5 -> 4.5
        4 Stars -> 4.0
        Not Applicable -> NaN
    """
    return (
        series.astype(str)
        .str.extract(r"(\d+\.?\d*)")[0]
        .pipe(pd.to_numeric, errors="coerce")
    )


def normalize_county(value):
    """
    Normalize county names so ZIP and CMS Landscape
    county names match more reliably.
    """
    if pd.isna(value):
        return ""

    value = str(value).upper().strip()

    replacements = [
        " COUNTY",
        " PARISH",
        " BOROUGH",
        " CENSUS AREA",
        ".",
    ]

    for item in replacements:
        value = value.replace(item, "")

    value = value.replace("SAINT ", "ST ")

    return " ".join(value.split())


def yes_value(value):
    """
    Convert common CMS Yes/No variants into boolean values.
    """
    if pd.isna(value):
        return False

    return str(value).strip().upper() in {
        "YES",
        "Y",
        "TRUE",
        "1",
    }


def format_money(value):
    if pd.isna(value):
        return "N/A"

    return f"${value:,.2f}"


def format_rating(value):
    if pd.isna(value):
        return "N/A"

    return f"{value:.1f}"


# ============================================================
# LOAD ZIP DATA
# ============================================================

@st.cache_data
def load_zip_data():

    zips = pd.read_csv(
        ZIP_FILE,
        dtype=str,
        low_memory=False,
    )

    zips.columns = [
        c.strip()
        for c in zips.columns
    ]

    required = [
        "zip",
        "state_id",
        "county_name",
    ]

    missing = [
        col
        for col in required
        if col not in zips.columns
    ]

    if missing:
        st.error(
            "The ZIP file is missing these required columns:"
        )
        st.write(missing)
        st.stop()

    zips["zip"] = (
        zips["zip"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    zips["state_id"] = (
        zips["state_id"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    zips["county_name"] = (
        zips["county_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    zips["county_normalized"] = (
        zips["county_name"]
        .apply(normalize_county)
    )

    return zips


# ============================================================
# LOAD MEDICARE LANDSCAPE DATA
# ============================================================

@st.cache_data
def load_plans():

    df = pd.read_csv(
        PLAN_FILE,
        dtype=str,
        low_memory=False,
    )

    df.columns = [
        c.strip()
        for c in df.columns
    ]

    required_columns = [
        "Contract Year",
        "State Territory Abbreviation",
        "State Territory Name",
        "County Name",
        "Parent Organization Name",
        "Organization Type",
        "Plan Name",
        "Plan Type",
        "Special Needs Plan (SNP) Indicator",
        "SNP Type",
        "Part D Coverage Indicator",
        "Annual Part D Deductible Amount",
        "Part D Total Premium",
        "Part C Premium",
        "Monthly Consolidated Premium (Part C + D)",
        "In-Network Maximum Out-of-Pocket (MOOP) Amount",
        "Overall Star Rating",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        st.error(
            "The Medicare Landscape file is missing "
            "these required columns:"
        )

        st.write(missing)
        st.stop()

    text_columns = [
        "State Territory Abbreviation",
        "State Territory Name",
        "County Name",
        "Parent Organization Name",
        "Organization Type",
        "Plan Name",
        "Plan Type",
        "Special Needs Plan (SNP) Indicator",
        "SNP Type",
        "Part D Coverage Indicator",
    ]

    for col in text_columns:

        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    df["monthly_premium"] = clean_money(
        df[
            "Monthly Consolidated Premium (Part C + D)"
        ]
    )

    df["part_c_premium"] = clean_money(
        df["Part C Premium"]
    )

    df["part_d_premium"] = clean_money(
        df["Part D Total Premium"]
    )

    df["part_d_deductible"] = clean_money(
        df["Annual Part D Deductible Amount"]
    )

    df["moop"] = clean_money(
        df[
            "In-Network Maximum Out-of-Pocket (MOOP) Amount"
        ]
    )

    df["overall_star_rating"] = clean_rating(
        df["Overall Star Rating"]
    )

    df["has_part_d"] = (
        df["Part D Coverage Indicator"]
        .apply(yes_value)
    )

    df["is_snp"] = (
        df[
            "Special Needs Plan (SNP) Indicator"
        ]
        .apply(yes_value)
    )

    df["state_normalized"] = (
        df["State Territory Abbreviation"]
        .str.upper()
        .str.strip()
    )

    df["county_normalized"] = (
        df["County Name"]
        .apply(normalize_county)
    )

    return df


# ============================================================
# PAGE
# ============================================================

st.title("📋 Medicare Plan Explorer")

st.caption(
    "Compare Medicare Advantage and Part D plan options "
    "using public CMS Medicare Landscape data."
)


# ============================================================
# LOAD DATA
# ============================================================

zips = load_zip_data()
plans = load_plans()


# ============================================================
# SIDEBAR SEARCH
# ============================================================

with st.sidebar:

    st.header("Search")

    zip_code = st.text_input(
        "Enter ZIP code",
        max_chars=5,
        value="60601",
    )

    max_premium = st.slider(
        "Maximum monthly premium",
        min_value=0,
        max_value=300,
        value=300,
        step=5,
    )

    min_rating = st.slider(
        "Minimum overall star rating",
        min_value=1.0,
        max_value=5.0,
        value=1.0,
        step=0.5,
    )

    require_drug = st.checkbox(
        "Require Part D drug coverage",
        value=False,
    )

    show_snp = st.checkbox(
        "Show SNP plans",
        value=True,
    )


# ============================================================
# VALIDATE ZIP
# ============================================================

zip_code = (
    zip_code
    .strip()
    .zfill(5)
)

if (
    not zip_code.isdigit()
    or len(zip_code) != 5
):

    st.warning(
        "Please enter a valid 5-digit ZIP code."
    )
    st.stop()


zip_row = zips[
    zips["zip"] == zip_code
]


if zip_row.empty:

    st.error(
        "ZIP code not found."
    )
    st.stop()


# ============================================================
# GET LOCATION FROM ZIP
# ============================================================

location = zip_row.iloc[0]

state = str(
    location["state_id"]
).strip().upper()

county = str(
    location["county_name"]
).strip()

county_normalized = normalize_county(
    county
)

city = ""

if "city" in zips.columns:

    city = str(
        location["city"]
    ).strip()


# ============================================================
# FILTER CMS DATA TO STATE
# ============================================================

filtered = plans[
    plans["state_normalized"] == state
].copy()


# ============================================================
# FILTER TO COUNTY
# ============================================================

if county_normalized:

    filtered = filtered[
        filtered["county_normalized"]
        == county_normalized
    ].copy()


# ============================================================
# PREMIUM FILTER
# ============================================================

filtered = filtered[
    filtered["monthly_premium"].isna()
    |
    (
        filtered["monthly_premium"]
        <= max_premium
    )
].copy()


# ============================================================
# STAR RATING FILTER
# ============================================================

filtered = filtered[
    filtered["overall_star_rating"].isna()
    |
    (
        filtered["overall_star_rating"]
        >= min_rating
    )
].copy()


# ============================================================
# PART D FILTER
# ============================================================

if require_drug:

    filtered = filtered[
        filtered["has_part_d"]
    ].copy()


# ============================================================
# SNP FILTER
# ============================================================

if not show_snp:

    filtered = filtered[
        ~filtered["is_snp"]
    ].copy()


# ============================================================
# LOCATION HEADER
# ============================================================

if city:

    st.subheader(
        f"Plans near {city}, {state} "
        f"(ZIP {zip_code})"
    )

else:

    st.subheader(
        f"Plans near ZIP {zip_code}"
    )


st.caption(
    f"County: {county}"
)


# ============================================================
# NO RESULTS
# ============================================================

if filtered.empty:

    st.warning(
        "No plans found. Try increasing the maximum "
        "premium, lowering the minimum star rating, "
        "or changing the Part D / SNP filters."
    )

    st.stop()


# ============================================================
# SORT RESULTS
# ============================================================

filtered = filtered.sort_values(
    by=[
        "overall_star_rating",
        "monthly_premium",
    ],
    ascending=[
        False,
        True,
    ],
    na_position="last",
).copy()


# ============================================================
# SUMMARY METRICS
# ============================================================

col1, col2, col3 = st.columns(3)


col1.metric(
    "Plans available",
    f"{len(filtered):,}",
)


available_premiums = (
    filtered["monthly_premium"]
    .dropna()
)

if not available_premiums.empty:

    lowest_premium_value = (
        available_premiums.min()
    )

    col2.metric(
        "Lowest premium",
        f"${lowest_premium_value:,.2f}",
    )

else:

    col2.metric(
        "Lowest premium",
        "N/A",
    )


available_ratings = (
    filtered["overall_star_rating"]
    .dropna()
)

if not available_ratings.empty:

    highest_rating_value = (
        available_ratings.max()
    )

    col3.metric(
        "Highest rating",
        f"{highest_rating_value:.1f}",
    )

else:

    col3.metric(
        "Highest rating",
        "N/A",
    )


# ============================================================
# HIGHLIGHTS
# ============================================================

st.markdown("### Highlights")


# ------------------------------------------------------------
# BALANCED CHOICE
#
# This is a simple educational comparison:
# higher rating improves score
# higher premium lowers score
#
# It is NOT an official CMS recommendation.
# ------------------------------------------------------------

filtered["balanced_choice_score"] = (
    filtered[
        "overall_star_rating"
    ].fillna(0) * 20
    -
    filtered[
        "monthly_premium"
    ].fillna(999)
)


balanced_choice = (
    filtered
    .sort_values(
        "balanced_choice_score",
        ascending=False,
    )
    .iloc[0]
)


# ------------------------------------------------------------
# LOWEST PREMIUM
# ------------------------------------------------------------

premium_candidates = filtered[
    filtered["monthly_premium"].notna()
]

if not premium_candidates.empty:

    lowest_premium = (
        premium_candidates
        .sort_values(
            "monthly_premium",
            ascending=True,
        )
        .iloc[0]
    )

else:

    lowest_premium = None


# ------------------------------------------------------------
# HIGHEST RATED
# ------------------------------------------------------------

rating_candidates = filtered[
    filtered["overall_star_rating"].notna()
]

if not rating_candidates.empty:

    highest_rated = (
        rating_candidates
        .sort_values(
            "overall_star_rating",
            ascending=False,
        )
        .iloc[0]
    )

else:

    highest_rated = None


c1, c2, c3 = st.columns(3)


# ------------------------------------------------------------
# BALANCED CHOICE
# ------------------------------------------------------------

with c1:

    st.info(
        f"**⭐ Balanced Choice**\n\n"
        f"{balanced_choice['Plan Name']}\n\n"
        f"Premium: "
        f"{format_money(balanced_choice['monthly_premium'])}\n\n"
        f"Rating: "
        f"{format_rating(balanced_choice['overall_star_rating'])}"
    )


# ------------------------------------------------------------
# LOWEST PREMIUM
# ------------------------------------------------------------

with c2:

    if lowest_premium is not None:

        st.success(
            f"**💲 Lowest Premium**\n\n"
            f"{lowest_premium['Plan Name']}\n\n"
            f"Premium: "
            f"{format_money(lowest_premium['monthly_premium'])}"
        )

    else:

        st.success(
            "**💲 Lowest Premium**\n\n"
            "Premium information unavailable."
        )


# ------------------------------------------------------------
# HIGHEST RATED
# ------------------------------------------------------------

with c3:

    if highest_rated is not None:

        st.warning(
            f"**🏆 Highest Rated**\n\n"
            f"{highest_rated['Plan Name']}\n\n"
            f"Rating: "
            f"{format_rating(highest_rated['overall_star_rating'])}"
        )

    else:

        st.warning(
            "**🏆 Highest Rated**\n\n"
            "Star rating information unavailable."
        )


st.caption(
    "Balanced Choice is based on a simple combination of "
    "CMS Overall Star Rating and monthly premium. "
    "It is not an official CMS recommendation and may not "
    "represent the best plan for every individual."
)


# ============================================================
# COMPARE PLANS
# ============================================================

st.markdown("### Compare Plans")


display_cols = [
    "Parent Organization Name",
    "Organization Type",
    "Plan Name",
    "Plan Type",
    "County Name",
    "monthly_premium",
    "part_c_premium",
    "part_d_premium",
    "part_d_deductible",
    "moop",
    "overall_star_rating",
    "Part D Coverage Indicator",
    "Special Needs Plan (SNP) Indicator",
    "SNP Type",
]


display_df = (
    filtered[
        display_cols
    ]
    .copy()
)


display_df = display_df.rename(
    columns={
        "Parent Organization Name":
            "Insurance Company",

        "Organization Type":
            "Organization Type",

        "Plan Name":
            "Plan",

        "Plan Type":
            "Plan Type",

        "County Name":
            "County",

        "monthly_premium":
            "Total Monthly Premium",

        "part_c_premium":
            "Part C Premium",

        "part_d_premium":
            "Part D Premium",

        "part_d_deductible":
            "Part D Deductible",

        "moop":
            "In-Network MOOP",

        "overall_star_rating":
            "Overall Rating",

        "Part D Coverage Indicator":
            "Part D Coverage",

        "Special Needs Plan (SNP) Indicator":
            "SNP",

        "SNP Type":
            "SNP Type",
    }
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={

        "Total Monthly Premium":
            st.column_config.NumberColumn(
                format="$%.2f"
            ),

        "Part C Premium":
            st.column_config.NumberColumn(
                format="$%.2f"
            ),

        "Part D Premium":
            st.column_config.NumberColumn(
                format="$%.2f"
            ),

        "Part D Deductible":
            st.column_config.NumberColumn(
                format="$%.2f"
            ),

        "In-Network MOOP":
            st.column_config.NumberColumn(
                format="$%.2f"
            ),

        "Overall Rating":
            st.column_config.NumberColumn(
                format="%.1f"
            ),
    },
)


# ============================================================
# PLAN DETAILS
# ============================================================

st.markdown("### Plan Details")


filtered["plan_selection_label"] = (
    filtered["Plan Name"].fillna("")
    + " — "
    + filtered["Parent Organization Name"].fillna("")
    + " — "
    + filtered["Plan Type"].fillna("")
)


plan_options = (
    filtered[
        "plan_selection_label"
    ]
    .drop_duplicates()
    .tolist()
)


selected_plan_label = st.selectbox(
    "Select a plan",
    plan_options,
)


selected = filtered[
    filtered["plan_selection_label"]
    == selected_plan_label
].iloc[0]


# ============================================================
# PLAN METRICS
# ============================================================

c1, c2, c3, c4 = st.columns(4)


c1.metric(
    "Monthly Premium",
    format_money(
        selected["monthly_premium"]
    ),
)


c2.metric(
    "Overall Rating",
    format_rating(
        selected["overall_star_rating"]
    ),
)


c3.metric(
    "Plan Type",
    (
        selected["Plan Type"]
        if selected["Plan Type"]
        else "N/A"
    ),
)


c4.metric(
    "MOOP",
    format_money(
        selected["moop"]
    ),
)


# ============================================================
# PLAN DETAILS TEXT
# ============================================================

st.write(
    "**Insurance Company:** "
    f"{selected['Parent Organization Name']}"
)

st.write(
    "**Organization Type:** "
    f"{selected['Organization Type']}"
)

st.write(
    "**Plan Name:** "
    f"{selected['Plan Name']}"
)

st.write(
    "**Plan Type:** "
    f"{selected['Plan Type']}"
)

st.write(
    "**County:** "
    f"{selected['County Name']}"
)

st.write(
    "**Contract Year:** "
    f"{selected['Contract Year']}"
)

st.write(
    "**Part D Coverage:** "
    f"{selected['Part D Coverage Indicator']}"
)

st.write(
    "**Part D Deductible:** "
    f"{format_money(selected['part_d_deductible'])}"
)

st.write(
    "**Part D Premium:** "
    f"{format_money(selected['part_d_premium'])}"
)

st.write(
    "**Part C Premium:** "
    f"{format_money(selected['part_c_premium'])}"
)

st.write(
    "**Total Monthly Premium:** "
    f"{format_money(selected['monthly_premium'])}"
)

st.write(
    "**Special Needs Plan:** "
    f"{selected['Special Needs Plan (SNP) Indicator']}"
)


if selected["is_snp"]:

    st.write(
        "**SNP Type:** "
        f"{selected['SNP Type'] or 'Not specified'}"
    )


st.write(
    "**In-Network Maximum Out-of-Pocket:** "
    f"{format_money(selected['moop'])}"
)

st.write(
    "**Overall CMS Star Rating:** "
    f"{format_rating(selected['overall_star_rating'])}"
)


# ============================================================
# DISCLAIMER
# ============================================================

st.divider()

st.info(
    "This page uses public CMS Medicare Landscape data "
    "and does not collect protected health information (PHI)."
)

st.caption(
    "This tool is for educational and healthcare navigation "
    "purposes only. Medicare plan availability, premiums, "
    "benefits, deductibles, out-of-pocket limits, and star "
    "ratings may change. Verify current information with "
    "Medicare.gov or the health plan before making enrollment "
    "decisions."
)