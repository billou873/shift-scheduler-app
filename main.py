import datetime
from collections import defaultdict
import csv
import streamlit as st
import pandas as pd
import io

# Streamlit UI
st.title("Πρόγραμμα Βαρδιών με Προτιμήσεις και Απουσίες")

uploaded_file = st.file_uploader("Ανεβάστε το αρχείο input.csv", type=["csv"])

if uploaded_file:
    df_input = pd.read_csv(uploaded_file)
    st.write("## Εισαγόμενα Δεδομένα:", df_input)

    employees = ["Vasilis", "Kwstas", "Andreas", "Christos", "Spyros", "Thodwris", "NikosA", "NikosK"]
    start_date = datetime.date(2025, 1, 3)

    holidays = [
        datetime.date(2025, 1, 1), datetime.date(2025, 1, 6), datetime.date(2025, 3, 3),
        datetime.date(2025, 3, 25), datetime.date(2025, 4, 18), datetime.date(2025, 4, 20),
        datetime.date(2025, 4, 21), datetime.date(2025, 5, 1), datetime.date(2025, 6, 9),
        datetime.date(2025, 8, 15), datetime.date(2025, 10, 28), datetime.date(2025, 12, 25),
        datetime.date(2025, 12, 26)
    ]

    easter_week = [datetime.date(2025, 4, 14) + datetime.timedelta(days=i) for i in range(7)]

    absences = defaultdict(list)
    preferences = defaultdict(list)

    for _, row in df_input.iterrows():
        name = row['Όνομα']
        week = int(row['Εβδομάδα'])
        status = row['Κατάσταση'].strip().lower()
        if status == 'απουσία':
            absences[name].append(week)
        elif status == 'προτίμηση':
            preferences[name].append(week)

    schedule = defaultdict(list)
    holiday_count = defaultdict(int)
    assigned_weeks = {}
    week_history = defaultdict(list)
    easter_owner = None

    for week in range(52):
        shift_start = start_date + datetime.timedelta(weeks=week)
        shift_end = shift_start + datetime.timedelta(days=6)
        shift_range = [shift_start + datetime.timedelta(days=i) for i in range(7)]
        month = shift_start.month

        if any(day in easter_week for day in shift_range):
            for emp in employees:
                if emp not in assigned_weeks.values():
                    employee = emp
                    easter_owner = emp
                    break
        else:
            recent_employees = [assigned_weeks.get(week - 1), assigned_weeks.get(week - 2)]
            eligible_employees = [e for e in employees if (
                e != easter_owner and
                week not in absences.get(e, []) and
                e not in recent_employees and
                week_history[e].count(month) < 2
            )]

            preferred = [e for e in eligible_employees if week in preferences.get(e, [])]
            candidate_pool = preferred if preferred else eligible_employees

            if not candidate_pool:
                continue

            min_shifts = min(len(schedule[e]) for e in candidate_pool)
            min_holidays = min(holiday_count[e] for e in candidate_pool)
            candidate_employees = [e for e in candidate_pool if holiday_count[e] == min_holidays]
            employee = min(candidate_employees, key=lambda e: len(schedule[e]))

        schedule[employee].append((shift_start, shift_end))
        assigned_weeks[week] = employee
        week_history[employee].append(month)

        for day in shift_range:
            if day in holidays:
                holiday_count[employee] += 1

    output = []
    for employee in employees:
        for shift in schedule[employee]:
            output.append({
                "Υπάλληλος": employee,
                "Από": shift[0].strftime('%d/%m/%Y'),
                "Έως": shift[1].strftime('%d/%m/%Y'),
                "Αργίες": holiday_count[employee]
            })

    df_output = pd.DataFrame(output)
    st.write("## Τελικό Πρόγραμμα:", df_output)

    excel_buffer = io.BytesIO()
    df_output.to_excel(excel_buffer, index=False)
    st.download_button("Λήψη Προγράμματος σε Excel", data=excel_buffer.getvalue(), file_name="προγραμμα.xlsx")
else:
    st.info("Παρακαλώ ανεβάστε αρχείο CSV με τις στήλες: Όνομα, Εβδομάδα, Κατάσταση.")
