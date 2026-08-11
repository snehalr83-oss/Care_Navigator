import math
import requests
import pandas as pd
import streamlit as st


DATA_DIR = "data"



st.title("🔍 Find Healthcare Near Me")
st.caption("Search hospitals, nursing homes, and doctors using public CMS data.")


CMS_DOCTORS_API_URL = (
    "https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0"
)

SPECIALTIES = [
    "All",
    "CARDIOVASCULAR DISEASE (CARDIOLOGY)",
    "FAMILY PRACTICE",
    "INTERNAL MEDICINE",
    "NURSE PRACTITIONER",
    "PHYSICIAN ASSISTANT",
    "ORTHOPEDIC SURGERY",
    "DERMATOLOGY",
    "PSYCHIATRY",
    "NEUROLOGY",
    "OPHTHALMOLOGY",
    "OBSTETRICS/GYNECOLOGY",
    "UROLOGY",
    "GASTROENTEROLOGY",
    "PULMONARY DISEASE",
    "ENDOCRINOLOGY",
    "GENERAL SURGERY",
]


def normalize_columns(df):
    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]
    return df


def get_col(df, possible_names, default=""):
    for name in possible_names:
        if name in df.columns:
            return df[name]
    return pd.Series([default] * len(df))


@st.cache_data
def load_zip_data():
    zips = pd.read_csv(f"{DATA_DIR}/uszips.csv", dtype=str)
    zips = normalize_columns(zips)

    zips["zip"] = zips["zip"].str.zfill(5)
    zips["lat"] = pd.to_numeric(zips["lat"], errors="coerce")
    zips["lng"] = pd.to_numeric(zips["lng"], errors="coerce")

    return zips.dropna(subset=["lat", "lng"])


@st.cache_data
def load_hospitals():
    raw = pd.read_csv(f"{DATA_DIR}/hospitals.csv", dtype=str)
    raw = normalize_columns(raw)

    out = pd.DataFrame()
    out["name"] = get_col(raw, ["Facility Name", "Hospital Name", "Provider Name"], "Name unavailable")
    out["address"] = get_col(raw, ["Address", "Provider Address"], "")
    out["city"] = get_col(raw, ["City/Town", "City", "Provider City"], "")
    out["state"] = get_col(raw, ["State", "Provider State"], "")
    out["zip"] = get_col(raw, ["ZIP Code", "Zip Code", "Provider Zip Code"], "")
    out["phone"] = get_col(raw, ["Telephone Number", "Phone Number", "Provider Phone Number"], "N/A")
    out["overall_rating"] = get_col(raw, ["Hospital overall rating", "Hospital Overall Rating", "Overall Rating"], "")
    out["emergency_services"] = get_col(raw, ["Emergency Services"], "N/A")
    out["provider_category"] = "Hospital"

    return add_zip_coordinates(out)


@st.cache_data
def load_nursing_homes():
    raw = pd.read_csv(f"{DATA_DIR}/nursing_homes.csv", dtype=str)
    raw = normalize_columns(raw)

    out = pd.DataFrame()
    out["name"] = get_col(raw, ["Provider Name", "Facility Name", "Nursing Home Name", "Name"], "Name unavailable")
    out["address"] = get_col(raw, ["Provider Address", "Address", "Street Address"], "")
    out["city"] = get_col(raw, ["Provider City", "City/Town", "City", "Location City"], "")
    out["state"] = get_col(raw, ["Provider State", "State", "Location State"], "")
    out["zip"] = get_col(raw, ["Provider Zip Code", "ZIP Code", "Zip Code", "ZIP", "Location Zip"], "")
    out["phone"] = get_col(raw, ["Provider Phone Number", "Phone Number", "Telephone Number"], "N/A")
    out["overall_rating"] = get_col(raw, ["Overall Rating", "CMS Overall Rating", "Overall star rating"], "")
    out["staffing_rating"] = get_col(raw, ["Staffing Rating", "Staffing star rating"], "N/A")
    out["inspection_rating"] = get_col(raw, ["Health Inspection Rating", "Health inspection rating"], "N/A")
    out["quality_rating"] = get_col(raw, ["QM Rating", "Quality Measure Rating", "Quality measure rating"], "N/A")
    out["provider_category"] = "Nursing Home"

    return add_zip_coordinates(out)


@st.cache_data(ttl=3600)
def search_doctors_api(state, specialty, max_pages=20, page_size=500):
    all_results = []
    offset = 0
    cms_total_count = 0

    for _ in range(max_pages):
        params = {
            "conditions[0][property]": "state",
            "conditions[0][value]": state,
            "limit": page_size,
            "offset": offset,
        }

        if specialty != "All":
            params["conditions[1][property]"] = "pri_spec"
            params["conditions[1][value]"] = specialty

        response = requests.get(CMS_DOCTORS_API_URL, params=params, timeout=30)

        if response.status_code != 200:
            st.error(f"CMS API error {response.status_code}")
            st.write(response.text)
            return pd.DataFrame(), 0

        data = response.json()
        batch = data.get("results", [])
        cms_total_count = data.get("count", cms_total_count)

        if not batch:
            break

        all_results.extend(batch)

        if len(batch) < page_size:
            break

        offset += page_size

    df = pd.DataFrame(all_results)

    if df.empty:
        return df, cms_total_count

    df["Doctor Name"] = (
        df["provider_first_name"].fillna("")
        + " "
        + df["provider_last_name"].fillna("")
        + " "
        + df["cred"].fillna("")
    ).str.strip()

    df["Specialty"] = df["pri_spec"]
    df["Telehealth"] = df["telehlth"]
    df["Address"] = (
        df["adr_ln_1"].fillna("")
        + " "
        + df["adr_ln_2"].fillna("")
    ).str.strip()
    df["City"] = df["citytown"]
    df["State"] = df["state"]
    df["zip"] = df["zip_code"].astype(str).str.extract(r"(\d{5})")[0]
    df["Phone"] = df["telephone_number"]
    df["NPI"] = df["npi"]
    df["provider_category"] = "Doctor"

    keep_cols = [
        "Doctor Name",
        "Specialty",
        "Telehealth",
        "Address",
        "City",
        "State",
        "zip",
        "Phone",
        "NPI",
        "provider_category",
    ]

    return df[keep_cols].dropna(subset=["zip"]), cms_total_count


def add_zip_coordinates(out):
    out["name"] = out["name"].fillna("Name unavailable")
    out["address"] = out["address"].fillna("")
    out["city"] = out["city"].fillna("")
    out["state"] = out["state"].fillna("")
    out["phone"] = out["phone"].fillna("N/A")

    out["zip"] = out["zip"].astype(str).str.extract(r"(\d{5})")[0]
    out["overall_rating"] = pd.to_numeric(out["overall_rating"], errors="coerce")

    zips = load_zip_data()[["zip", "lat", "lng"]]
    out = out.merge(zips, on="zip", how="left")

    return out.dropna(subset=["lat", "lng"])


def add_doctor_zip_coordinates(doctors):
    zips = load_zip_data()[["zip", "lat", "lng"]]
    doctors = doctors.merge(zips, on="zip", how="left")
    return doctors.dropna(subset=["lat", "lng"])


def haversine_miles(lat1, lon1, lat2, lon2):
    radius = 3958.8

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.asin(math.sqrt(a))


def add_distance(df, user_lat, user_lng):
    df = df.copy()
    df["distance_miles"] = df.apply(
        lambda row: haversine_miles(user_lat, user_lng, row["lat"], row["lng"]),
        axis=1
    )
    return df


def recommendation_label(row):
    rating = row["overall_rating"]
    distance = row["distance_miles"]

    if pd.notna(rating) and rating >= 4 and distance <= 10:
        return "Strong nearby option"
    if pd.notna(rating) and rating >= 4:
        return "Highly rated"
    if distance <= 5:
        return "Very close"
    return "Review details"


st.title("🏥 Healthcare Quality Navigator")
st.caption("Find hospitals, nursing homes, and doctors using public CMS data.")

with st.sidebar:
    st.header("Search")

    zip_code = st.text_input("Enter ZIP code", max_chars=5, value="60601")

    provider_type = st.selectbox(
        "What are you looking for?",
        ["Hospitals", "Nursing Homes", "Doctors", "All"]
    )

    radius = st.slider("Search radius in miles", 5, 100, 25)

    if provider_type != "Doctors":
        min_rating = st.slider("Minimum CMS rating", 1, 5, 1)

    if provider_type == "Doctors":
        selected_specialty = st.selectbox("Specialty", SPECIALTIES)
        max_pages = st.slider("CMS pages to search", 1, 40, 20)


zips = load_zip_data()

zip_code = zip_code.strip().zfill(5)
zip_row = zips[zips["zip"] == zip_code]

if zip_row.empty:
    st.error("ZIP code not found. Please try another ZIP code.")
    st.stop()

user_lat = float(zip_row.iloc[0]["lat"])
user_lng = float(zip_row.iloc[0]["lng"])

if "state_id" in zips.columns:
    doctor_state = zip_row.iloc[0]["state_id"]
elif "state" in zips.columns:
    doctor_state = zip_row.iloc[0]["state"]
else:
    doctor_state = None


if provider_type == "Doctors":
    st.subheader(f"Doctors & Clinicians near ZIP {zip_code}")

    if doctor_state is None:
        st.error("Your uszips.csv file needs a state column, such as state_id or state.")
        st.stop()

    st.caption(f"Using ZIP {zip_code} → State {doctor_state} → Specialty {selected_specialty}")

    doctors, cms_total_count = search_doctors_api(
        state=doctor_state,
        specialty=selected_specialty,
        max_pages=max_pages,
        page_size=500
    )

    if doctors.empty:
        st.warning("No doctors found for that specialty.")
        st.stop()

    pulled_from_cms = len(doctors)

    doctors = add_doctor_zip_coordinates(doctors)
    doctors = add_distance(doctors, user_lat, user_lng)

    doctors = doctors[doctors["distance_miles"] <= radius].copy()
    doctors = doctors.sort_values("distance_miles")

    col1, col2, col3 = st.columns(3)
    col1.metric("CMS matching providers", cms_total_count)
    col2.metric("Pulled from CMS", pulled_from_cms)
    col3.metric("Within radius", len(doctors))

    if cms_total_count > pulled_from_cms:
        st.info(
            f"CMS reports {cms_total_count} matching providers. "
            f"The app pulled {pulled_from_cms}. "
            f"Increase 'CMS pages to search' in the sidebar to search more records."
        )

    if doctors.empty:
        st.warning("No doctors found within your selected radius. Try increasing the radius.")
        st.stop()

    display_doctors = doctors[
        [
            "Doctor Name",
            "Specialty",
            "Telehealth",
            "distance_miles",
            "Address",
            "City",
            "State",
            "zip",
            "Phone",
            "NPI",
        ]
    ].copy()

    display_doctors["distance_miles"] = display_doctors["distance_miles"].round(1)

    st.dataframe(
        display_doctors.rename(
            columns={
                "distance_miles": "Distance",
                "zip": "ZIP",
            }
        ),
        use_container_width=True,
        hide_index=True
    )

    selected_doctor = st.selectbox(
        "Select a doctor",
        doctors["Doctor Name"].dropna().unique().tolist()
    )

    selected = doctors[doctors["Doctor Name"] == selected_doctor].iloc[0]

    st.markdown("### Doctor details")

    c1, c2, c3 = st.columns(3)
    c1.metric("Specialty", selected["Specialty"])
    c2.metric("Distance", f"{selected['distance_miles']:.1f} mi")
    c3.metric("Telehealth", selected["Telehealth"])

    st.write(
        f"**Address:** {selected['Address']}, "
        f"{selected['City']}, {selected['State']} {selected['zip']}"
    )
    st.write(f"**Phone:** {selected['Phone']}")
    st.write(f"**NPI:** {selected['NPI']}")

    st.markdown("### Map")
    map_df = doctors.rename(columns={"lat": "latitude", "lng": "longitude"})
    st.map(map_df[["latitude", "longitude"]])

    st.stop()


datasets = []

if provider_type in ["Hospitals", "All"]:
    datasets.append(load_hospitals())

if provider_type in ["Nursing Homes", "All"]:
    datasets.append(load_nursing_homes())

facilities = pd.concat(datasets, ignore_index=True)
results = add_distance(facilities, user_lat, user_lng)

results = results[
    (results["distance_miles"] <= radius)
    & (
        results["overall_rating"].isna()
        | (results["overall_rating"] >= min_rating)
    )
].copy()

results["recommendation"] = results.apply(recommendation_label, axis=1)

results = results.sort_values(
    by=["overall_rating", "distance_miles"],
    ascending=[False, True],
    na_position="last"
)

st.subheader(f"Results near {zip_code}")

if results.empty:
    st.warning("No facilities found. Try increasing the radius or lowering the rating filter.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Facilities found", len(results))
col2.metric("Search radius", f"{radius} miles")
col3.metric("Minimum rating", f"{min_rating} stars")

top = results.iloc[0]

st.markdown("### 🏆 Best match")
st.write(f"**{top['name']}**")
st.write(
    f"{top['provider_category']} | "
    f"{top['overall_rating'] if pd.notna(top['overall_rating']) else 'N/A'} stars | "
    f"{top['distance_miles']:.1f} miles away"
)
st.write(f"{top['address']}, {top['city']}, {top['state']} {top['zip']}")
st.write(f"Phone: {top['phone']}")

st.markdown("### Compare facilities")

display_df = results[
    [
        "name",
        "provider_category",
        "overall_rating",
        "distance_miles",
        "recommendation",
        "address",
        "city",
        "state",
        "zip",
        "phone",
    ]
].copy()

display_df["distance_miles"] = display_df["distance_miles"].round(1)

st.dataframe(
    display_df.rename(
        columns={
            "name": "Name",
            "provider_category": "Type",
            "overall_rating": "CMS Rating",
            "distance_miles": "Distance",
            "recommendation": "Why It May Fit",
            "address": "Address",
            "city": "City",
            "state": "State",
            "zip": "ZIP",
            "phone": "Phone",
        }
    ),
    use_container_width=True,
    hide_index=True
)

st.markdown("### Map")
map_df = results.rename(columns={"lat": "latitude", "lng": "longitude"})
st.map(map_df[["latitude", "longitude"]])

st.markdown("### Facility details")

selected_name = st.selectbox(
    "Select a facility",
    results["name"].dropna().unique().tolist()
)

selected = results[results["name"] == selected_name].iloc[0]

c1, c2, c3, c4 = st.columns(4)

c1.metric("CMS Rating", selected["overall_rating"] if pd.notna(selected["overall_rating"]) else "N/A")
c2.metric("Distance", f"{selected['distance_miles']:.1f} mi")
c3.metric("Type", selected["provider_category"])
c4.metric("Phone", selected["phone"])

st.write(f"**Address:** {selected['address']}, {selected['city']}, {selected['state']} {selected['zip']}")

if selected["provider_category"] == "Hospital":
    st.write(f"**Emergency Services:** {selected.get('emergency_services', 'N/A')}")

if selected["provider_category"] == "Nursing Home":
    st.write(f"**Staffing Rating:** {selected.get('staffing_rating', 'N/A')}")
    st.write(f"**Health Inspection Rating:** {selected.get('inspection_rating', 'N/A')}")
    st.write(f"**Quality Measure Rating:** {selected.get('quality_rating', 'N/A')}")