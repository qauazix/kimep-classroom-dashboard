import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# -------------------------------------------------------------
# ---------------- SMART TIME PARSER (AUTO FIX) ---------------
# -------------------------------------------------------------

def to_minutes(t):
    """Convert HH:MM to minutes since midnight."""
    h, m = t.split(":")
    return int(h) * 60 + int(m)

def parse_interval_smart(interval: str):
    """
    Parse time interval and auto-correct common scheduling mistakes.
    Returns (start_min, end_min, fixed, error_message)
    """
    if not isinstance(interval, str):
        return None, None, False, "Non-string interval"

    interval = interval.replace(" ", "")

    # Must contain dash
    if "-" not in interval:
        return None, None, False, "Missing dash"

    start_str, end_str = interval.split("-", 1)

    # ONLINE/TBA etc.
    if any(x in interval.upper() for x in ["ONLINE", "TBA", "NA"]):
        return None, None, False, "Non-time entry (ONLINE/TBA)"

    # Try parsing
    try:
        start = to_minutes(start_str)
        end = to_minutes(end_str)
    except:
        return None, None, False, "Bad time format"

    fixed = False

    # Fix case: end < start
    if end <= start:
        end += 720  # add 12 hours
        fixed = True

    if end <= start:
        end += 1440  # add 24 hours
        fixed = True

    duration = end - start

    if duration > 300:
        return start, end, False, f"Duration too long ({duration} min)"

    return start, end, fixed, ""


# -------------------------------------------------------------
# ---------------------- PREPROCESS DATA -----------------------
# -------------------------------------------------------------

def preprocess_data(df):
    df = df.copy()

    required_cols = ["Days", "Class_Times", "Hall"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return pd.DataFrame(), pd.DataFrame()

    # Clean Days + Class_Times formatting
    df["Days"] = df["Days"].astype(str).str.upper().str.replace(" ", "")
    df["Class_Times"] = (
        df["Class_Times"]
        .astype(str)
        .str.replace("–", "-", regex=False)
        .str.replace("—", "-", regex=False)
        .str.replace(".", ":", regex=False)
        .str.replace(" ", "")
    )

    # Smart parse time intervals
    parsed = df["Class_Times"].apply(lambda x: pd.Series(parse_interval_smart(x)))
    parsed.columns = ["Start_Min", "End_Min", "AutoFixed", "ErrorMessage"]
    df = pd.concat([df, parsed], axis=1)

    # Duration
    df["Duration"] = df["End_Min"] - df["Start_Min"]

    # Errors and valids
    df_errors = df[df["ErrorMessage"] != ""]
    df_valid = df[df["ErrorMessage"] == ""].copy()

    # Create Start_Hour (used in dashboard filters and charts)
    df_valid["Start_Hour"] = (df_valid["Start_Min"] // 60).astype(int)

    return df_valid, df_errors


# -------------------------------------------------------------
# ------------------------- LOAD DATA --------------------------
# -------------------------------------------------------------

@st.cache_data
def load_latest_data():
    """
    Loads CSV updated by the Google Sheets scheduler.
    """
    return pd.read_csv("latest_schedule.csv")


# -------------------------------------------------------------
# ------------------------- STREAMLIT UI -----------------------
# -------------------------------------------------------------

def main():

    st.title("🎓 KIMEP Classroom Occupancy Dashboard")

    # --- Load data ---
    raw_df = load_latest_data()
    df_valid, df_errors = preprocess_data(raw_df)

    st.success("Data loaded successfully from latest_schedule.csv")

    # ---------------------------------------------------------
    # --- SECTION: Show raw data & cleaned data
    # ---------------------------------------------------------
    with st.expander("Raw Data (from Google Sheet)"):
        st.dataframe(raw_df)

    with st.expander("Cleaned Valid Data"):
        st.dataframe(df_valid)

    if not df_errors.empty:
        with st.expander("⚠ Invalid Time Intervals Detected"):
            st.dataframe(df_errors[["Class_Times", "Days", "Hall", "ErrorMessage"]])
            st.warning(f"{len(df_errors)} invalid entries detected. These were excluded from analysis.")

    # ---------------------------------------------------------
    # --------- FILTERS ---------------------------------------
    # ---------------------------------------------------------

    st.header("🔍 Filters")

    hall_list = sorted(df_valid["Hall"].dropna().unique().tolist())
    day_list = sorted(df_valid["Days"].dropna().unique().tolist())
    hour_list = sorted(df_valid["Start_Hour"].dropna().unique().tolist())

    selected_hall = st.selectbox("Filter by Hall:", ["All"] + hall_list)
    selected_day = st.selectbox("Filter by Day:", ["All"] + day_list)
    selected_hour = st.selectbox("Filter by Start Hour:", ["All"] + list(map(str, hour_list)))

    df_filtered = df_valid.copy()

    if selected_hall != "All":
        df_filtered = df_filtered[df_filtered["Hall"] == selected_hall]

    if selected_day != "All":
        df_filtered = df_filtered[df_filtered["Days"] == selected_day]

    if selected_hour != "All":
        df_filtered = df_filtered[df_filtered["Start_Hour"] == int(selected_hour)]

    st.subheader("Filtered Data")
    st.dataframe(df_filtered)

    # ---------------------------------------------------------
    # --------- VISUAL 1: Hall usage count --------------------
    # ---------------------------------------------------------

    st.header("🏫 Hall Usage Frequency")

    hall_counts = df_valid["Hall"].value_counts().reset_index()
    hall_counts.columns = ["Hall", "Count"]

    fig1 = px.bar(
        hall_counts,
        x="Hall",
        y="Count",
        title="Number of Classes per Hall",
        text="Count"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ---------------------------------------------------------
    # --------- VISUAL 2: Total minutes per hall --------------
    # ---------------------------------------------------------

    st.header("⏱ Total Minutes Each Hall is Used")

    hall_minutes = df_valid.groupby("Hall")["Duration"].sum().reset_index()
    hall_minutes.columns = ["Hall", "Total_Minutes"]

    fig2 = px.bar(
        hall_minutes,
        x="Hall",
        y="Total_Minutes",
        title="Total Usage (Minutes) per Hall",
        text="Total_Minutes"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------------------
    # --------- VISUAL 3: Distribution of Start Hours ---------
    # ---------------------------------------------------------

    st.header("🕒 Distribution of Class Start Hours")

    fig3 = px.histogram(
        df_valid,
        x="Start_Hour",
        title="Class Start Time Distribution",
        nbins=24
    )
    st.plotly_chart(fig3, use_container_width=True)


    # ---------------------------------------------------------
    # --------- Footer Section --------------------------------
    # ---------------------------------------------------------

    st.markdown("---")
    st.caption("Dashboard auto-updates when Google Sheet changes.")


# -------------------------------------------------------------
# ------------------------- RUN APP ---------------------------
# -------------------------------------------------------------

if __name__ == "__main__":
    main()
