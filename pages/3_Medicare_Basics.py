import streamlit as st


st.title("📘 Medicare Basics")
st.caption("Learn the basics of Medicare coverage, enrollment, and preventive care.")

st.markdown("""
This page helps users understand Medicare without collecting personal information.
It is educational only and does not use PHI.
""")

user_type = st.selectbox(
    "Tell us about yourself",
    [
        "Age 30-49",
        "Age 50-64",
        "Age 65+",
        "Caregiver"
    ]
)

st.divider()

st.header("Medicare at a Glance")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **Part A — Hospital Insurance**

    Helps cover:
    - Inpatient hospital stays
    - Skilled nursing facility care
    - Hospice care
    - Some home health care
    """)

with col2:
    st.info("""
    **Part B — Medical Insurance**

    Helps cover:
    - Doctor visits
    - Outpatient care
    - Preventive services
    - Medical equipment
    """)

col3, col4 = st.columns(2)

with col3:
    st.success("""
    **Part C — Medicare Advantage**

    A private-plan alternative to Original Medicare.

    Often includes:
    - Part A
    - Part B
    - Sometimes Part D
    - Extra benefits like dental, vision, or hearing
    """)

with col4:
    st.warning("""
    **Part D — Prescription Drug Coverage**

    Helps cover:
    - Prescription medications
    - Brand-name drugs
    - Generic drugs
    - Some vaccines
    """)

st.divider()

st.header("Original Medicare vs Medicare Advantage")

comparison_data = {
    "Feature": [
        "Who provides coverage?",
        "Includes Part A?",
        "Includes Part B?",
        "May include drug coverage?",
        "May include dental/vision/hearing?",
        "Network restrictions?",
        "Good for"
    ],
    "Original Medicare": [
        "Federal government",
        "Yes",
        "Yes",
        "No, usually added separately with Part D",
        "Usually no",
        "Generally fewer network restrictions",
        "People who want broad provider access"
    ],
    "Medicare Advantage": [
        "Private insurance companies approved by Medicare",
        "Yes",
        "Yes",
        "Often yes",
        "Often yes",
        "Often uses HMO/PPO networks",
        "People who want bundled benefits"
    ]
}

st.dataframe(comparison_data, use_container_width=True, hide_index=True)

st.divider()

st.header("Enrollment Basics")

with st.expander("Initial Enrollment Period"):
    st.write("""
    This is the first time many people can sign up for Medicare.
    It generally happens around the time someone turns 65.
    """)

with st.expander("General Enrollment Period"):
    st.write("""
    This may apply if someone missed their initial enrollment window.
    Late enrollment penalties may apply depending on the situation.
    """)

with st.expander("Special Enrollment Period"):
    st.write("""
    This may apply after certain life events, such as losing employer coverage.
    """)

with st.expander("Annual Open Enrollment"):
    st.write("""
    This is when many Medicare beneficiaries can review and change Medicare Advantage
    or Part D prescription drug plans.
    """)

st.divider()

st.header("Preventive Care Guide")

if user_type == "Age 30-49":
    st.markdown("""
    **Helpful focus areas:**
    - Blood pressure checks
    - Cholesterol screening
    - Diabetes risk screening
    - Routine primary care
    - Vaccines
    - Family health history awareness
    """)

elif user_type == "Age 50-64":
    st.markdown("""
    **Helpful focus areas:**
    - Colon cancer screening
    - Blood pressure checks
    - Cholesterol screening
    - Diabetes screening
    - Mammograms, if applicable
    - Lung cancer screening, if eligible
    - Planning ahead for Medicare eligibility
    """)

elif user_type == "Age 65+":
    st.markdown("""
    **Helpful focus areas:**
    - Annual wellness visit
    - Flu, COVID, shingles, and pneumonia vaccines
    - Colon cancer screening, if appropriate
    - Diabetes screening
    - Bone density screening, if appropriate
    - Medication review
    - Fall risk assessment
    """)

else:
    st.markdown("""
    **Helpful caregiver focus areas:**
    - Understand the person's Medicare coverage
    - Help compare provider quality
    - Review preventive care needs
    - Keep a medication list
    - Track plan enrollment dates
    - Compare Medicare Advantage and Part D options
    """)

st.divider()

st.header("Which Medicare Path Might Fit?")

goal = st.radio(
    "What is most important to the user?",
    [
        "Broad provider access",
        "Lower monthly premium",
        "Extra benefits like dental or vision",
        "Prescription drug coverage",
        "I am not sure"
    ]
)

if goal == "Broad provider access":
    st.write("""
    Original Medicare may be worth learning more about because it generally offers
    broad access to Medicare-participating providers.
    """)
elif goal == "Lower monthly premium":
    st.write("""
    Some Medicare Advantage plans may have low or $0 premiums, but users should still
    compare out-of-pocket costs, provider networks, and benefits.
    """)
elif goal == "Extra benefits like dental or vision":
    st.write("""
    Medicare Advantage plans may include extra benefits such as dental, vision,
    hearing, transportation, or wellness programs.
    """)
elif goal == "Prescription drug coverage":
    st.write("""
    Users should compare Part D plans or Medicare Advantage plans that include
    prescription drug coverage.
    """)
else:
    st.write("""
    A good next step is to compare Original Medicare, Medicare Advantage, and Part D
    options side by side.
    """)

st.divider()

st.info("""
This page is for education only. It does not collect names, Medicare IDs,
dates of birth, claims, diagnoses, or other PHI.
""")