import sqlite3
from datetime import date, datetime
from io import StringIO
import csv

import pandas as pd
import streamlit as st
from supabase import create_client
@st.cache_resource
def get_supabase_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
try:
    supabase = get_supabase_client()
except Exception:
    st.error("Unable to connect. Please try again later.")
    st.stop()

APP_TITLE = "Care Crafters"
DB_PATH = "chemo_companion.db"

st.set_page_config(page_title=APP_TITLE, page_icon="💚", layout="centered")
st.markdown("""
<div style="background: linear-gradient(120deg, #e5f7f4, #edf2ff);
            padding: 30px; border-radius: 20px;
            border: 1px solid #d7eae8; margin-bottom: 22px;">
    <h1 style="color: #16324f; font-size: 38px; margin: 0;">
        💚 Care Crafters
    </h1>
    <p style="color: #087f8c; font-size: 14px; font-weight: 600;
              font-style: italic;">
        Coding with compassion. Innovating for better care.
    </p>
</div>
""", unsafe_allow_html=True)

def connect_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS symptom_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                symptom TEXT NOT NULL,
                severity INTEGER NOT NULL,
                daily_impact TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

def add_entry(entry_date, symptom, severity, daily_impact, notes):
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO symptom_entries
            (entry_date, symptom, severity, daily_impact, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entry_date.isoformat(), symptom, int(severity), daily_impact,
            notes.strip(), datetime.now().isoformat(timespec="seconds")
        ))
        conn.commit()

def get_entries():
    with connect_db() as conn:
        return pd.read_sql_query(
            "SELECT id, entry_date, symptom, severity, daily_impact, notes "
            "FROM symptom_entries ORDER BY entry_date DESC, id DESC", conn
        )

def delete_entry(entry_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM symptom_entries WHERE id = ?", (int(entry_id),))
        conn.commit()

init_db()
# Supabase authentication
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("Welcome to Care Crafters")

    auth_mode = st.radio(
        "Choose an option",
        ["Login", "Sign Up"],
        horizontal=True
    )

    email = st.text_input("Email address")
    password = st.text_input("Password", type="password")

    if auth_mode == "Sign Up":
        if st.button("Create account"):
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": email,
                        "password": password
                    })
                    st.success(
                        "Account request submitted. Check your email "
                        "to verify your account before logging in."
                    )
                except Exception as e:
                    st.error("Signup failed.")
                    st.caption(f"Error details: {e}")

    else:
        if st.button("Login"):
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                try:
                    result = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    st.session_state.user = result.user
                    st.rerun()
                except Exception:
                    st.error("Login failed. Check your details and email verification.")

    st.stop()


st.warning(
    "Prototype only: this app does not diagnose, monitor emergencies, or replace your oncology team. "
    "Use the care instructions provided by your healthcare team. Do not enter real patient information "
    "into this demo unless you have an appropriate privacy and security setup."
)

tab_home, tab_log, tab_history, tab_appointment, tab_report, tab_safety = st.tabs(
    ["Home", "Log symptoms", "History", "Appointment Summary", "Reports", "Safety"]
)

entries = get_entries()

with tab_home:
    st.subheader("Your overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Recorded entries", len(entries))
    c2.metric("Symptoms recorded", entries["symptom"].nunique() if not entries.empty else 0)
    c3.metric(
    "Latest entry",
    max(entries["entry_date"]).split("-")[2] + "-" +
    max(entries["entry_date"]).split("-")[1] + "-" +
    max(entries["entry_date"]).split("-")[0]
    if not entries.empty else "—"
)
    st.markdown("### Recent entries")
    if entries.empty:
        st.info("No entries yet. Open **Log symptoms** to add a demonstration entry.")
    else:
        recent = entries[["entry_date", "symptom", "severity", "daily_impact"]].head(5).copy()

        recent["entry_date"] = pd.to_datetime(
            recent["entry_date"], errors="coerce"
        ).dt.strftime("%d-%m-%Y")

        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True
        )

   

with tab_log:
    st.subheader("Log a symptom")
    symptom_options = [
        "Nausea", "Fatigue", "Pain", "Vomiting", "Appetite changes",
        "Constipation", "Diarrhea", "Mouth sores", "Sleep difficulties", "Other"
    ]
    with st.form("symptom_form", clear_on_submit=True):
        entry_date = st.date_input(
    "Date (DD-MM-YYYY)",
    value=date.today(),
    format="DD-MM-YYYY"
)
        symptom = st.selectbox("Symptom", symptom_options)
        severity = st.slider("Severity (0 = none, 10 = worst)", 0, 10, 3)
        daily_impact = st.selectbox(
            "Impact on daily activities",
            ["None", "Mild", "Moderate", "Severe", "Prefer not to say"]
        )
        notes = st.text_area("Optional notes", placeholder="Describe what you noticed...")
        submitted = st.form_submit_button("Save entry", type="primary")
        if submitted:
            add_entry(entry_date, symptom, severity, daily_impact, notes)
            st.success("Entry saved to this computer's local SQLite database.")
            st.rerun()

with tab_history:
    st.subheader("Symptom history")
    entries = get_entries()
    if entries.empty:
        st.info("Your history will appear here after you save an entry.")
    else:
        all_symptoms = ["All"] + sorted(entries["symptom"].dropna().unique().tolist())
        selected_symptom = st.selectbox("Filter by symptom", all_symptoms)
        filtered = entries if selected_symptom == "All" else entries[entries["symptom"] == selected_symptom]
        entry_date = st.date_input(
    "Date (DD-MM-YYYY)",
    value=date.today(),
    format="DD-MM-YYYY"
)
        if not filtered.empty:
            chart_data = filtered.copy()
            chart_data["entry_date"] = pd.to_datetime(chart_data["entry_date"]).dt.strftime("%d-%m-%Y")
            chart_data = chart_data.sort_values("entry_date")
            st.markdown("### Recorded severity")
            st.line_chart(chart_data.set_index("entry_date")["severity"])
        st.markdown("### Delete an entry")
        ids = filtered["id"].tolist()
        if ids:
            selected_id = st.selectbox(
                "Select entry ID to delete",
                ids,
                format_func=lambda x: f"ID {x} — {filtered.loc[filtered['id'] == x, 'entry_date'].iloc[0]} — "
                                      f"{filtered.loc[filtered['id'] == x, 'symptom'].iloc[0]}"
            )
            if st.button("Delete selected entry"):
                delete_entry(selected_id)
                st.success("Entry deleted.")
                st.rerun()

with tab_report:
    st.subheader("Appointment summary")
    entries = get_entries()
    if entries.empty:
        st.info("Add an entry before generating a report.")
    else:
        start_date = st.date_input(
    "From (DD-MM-YYYY)",
    value=date.today().replace(day=1),
    format="DD-MM-YYYY",
    key="report_start"
)
end_date = st.date_input(
    "To (DD-MM-YYYY)",
    value=date.today(),
    format="DD-MM-YYYY",
    key="report_end"
)
if start_date > end_date:
            st.error("The start date must be on or before the end date.")
else:
            report = entries[
                (entries["entry_date"] >= start_date.isoformat()) &
                (entries["entry_date"] <= end_date.isoformat())
            ].copy()
            st.write(f"Entries in selected period: **{len(report)}**")
            report_display = report.drop(columns=["id"], errors="ignore").copy()
            report_display["entry_date"] = pd.to_datetime(
                report_display["entry_date"], errors="coerce"
            ).dt.strftime("%d-%m-%Y")
            st.dataframe(
                report_display,
                use_container_width=True,
                hide_index=True
            )
            csv_data = report.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV report",
                data=csv_data,
                file_name="care_crafters_symptom_report.csv",
                mime="text/csv"
            )
            
summary_lines = [
                    "CARE CRAFTERS - SYMPTOM SUMMARY",
                    f"Period: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}",
                    f"Number of recorded entries: {len(report)}",
                    "",
                    "This summary contains user-entered information only and is not a diagnosis."
                ]

if not report.empty:
                    summary_lines += ["", "Recorded entries:"]
                    for _, row in report.iterrows():
                        summary_lines.append(
                            f"{pd.to_datetime(row['entry_date']).strftime('%d-%m-%Y')}: "
                            f"{row['symptom']}; severity: {row['severity']}/10; "
                            f"daily impact: {row['daily_impact']}; notes: {row['notes'] or 'None'}"
                        )

st.download_button(
                    "Download readable summary",
                    data="\n".join(summary_lines).encode("utf-8"),
                    file_name="care_crafters_appointment_summary.txt",
                    mime="text/plain"
                )

with st.expander("Generate full-history appointment summary", expanded=True):
    all_entries = get_entries()

    if all_entries.empty:
        st.info("Record symptoms first to generate an appointment summary.")
    else:
        timeline = all_entries.copy()
        timeline["entry_date"] = pd.to_datetime(
            timeline["entry_date"], errors="coerce"
        )
        timeline = timeline.dropna(subset=["entry_date"])
        timeline = timeline.sort_values("entry_date")

        st.markdown("### Symptom timeline")

        st.dataframe(
            timeline[
                ["entry_date", "symptom", "severity", "daily_impact", "notes"]
            ],
            width="stretch",
            hide_index=True,
        )
        summary_lines = [
            "CARE CRAFTERS - DOCTOR APPOINTMENT SUMMARY",
            "",
            "This report summarizes symptoms entered by the patient.",
            "It is not a diagnosis or a validated clinical triage assessment.",
            "",
            f"Total recorded entries: {len(timeline)}",
            "",
            "SYMPTOM TIMELINE",
        ]

        for _, row in timeline.iterrows():
            symptom_date = pd.to_datetime(row["entry_date"]).strftime("%d-%m-%Y")
            symptom = row["symptom"]
            severity = row["severity"]
            impact = row["daily_impact"]
            notes = row["notes"] if pd.notna(row["notes"]) and row["notes"] else "None recorded"

            summary_lines.append(
                f"{symptom_date}: {symptom}; "
                f"recorded severity: {severity}/10; "
                f"daily impact: {impact}; notes: {notes}"
            )

        summary_lines.extend([
            "",
            "PREPARE FOR THE DOCTOR",
            "- Explain when each symptom started and how it has changed.",
            "- Mention current medicines, allergies, and relevant medical history.",
            "- Ask what assessment, tests, or follow-up may be appropriate.",
            "- Tell the clinician about any symptoms that are worsening or recurring.",
            "",
            "NEXT STEPS",
            "- Arrange a medical consultation appropriate to your symptoms.",
            "- If symptoms are severe, rapidly worsening, or concerning, seek prompt medical advice.",
            "- For a possible medical emergency, contact your local emergency service immediately.",
            "",
            "Alerts and clinical guidance must follow clinician-reviewed rules.",
            "This report contains patient-entered information only.",
        ])

        st.markdown("### What to discuss with your doctor")
        st.write("Use the timeline above to explain symptom onset, recurrence, severity, and impact.")
        st.write("Bring your medication list and mention allergies and relevant medical history.")
        st.write("Ask your clinician about appropriate assessment and follow-up.")

        st.download_button(
            "Download full appointment summary",
            data="\n".join(summary_lines).encode("utf-8"),
            file_name="care_crafters_appointment_summary.txt",
            mime="text/plain",
        )

with tab_safety:
    st.subheader("Safety information")
    st.markdown("""
- Follow the instructions and emergency plan provided by your own oncology team.
- Contact your healthcare team promptly about concerning, new, or worsening symptoms.
- If you believe you are experiencing an emergency, use your local emergency service.
- This prototype is not continuously monitored and cannot determine whether a symptom is medically safe.
- Any future automated alerts must be reviewed by qualified oncology professionals before clinical use.
""")
    st.info("The severity scale is for recording a patient's report only. It is not a validated clinical triage rule.")

st.divider()
st.caption(
    "Care Crafters | Project: Chemo Companion | "
    "Coding with compassion. Innovating for better care. | "
    
)