# AyushBot PHC Gateway Dashboard

This is a separate Streamlit dashboard for local PHC clinical operations on the Raspberry Pi gateway. It does not modify or duplicate the cloud dashboard under `cloud/dashboards`.

Run locally from the repository root using the virtual environment:

```bash
.venv/bin/streamlit run gateway/phc_dashboard/app.py
```

Or activate the virtual environment first:

```bash
source .venv/bin/activate
streamlit run gateway/phc_dashboard/app.py
```

The dashboard is offline-first and uses embedded mock data for ASHA cases, patients, referrals, tasks, guideline snippets, local sync events, and audit logs. The default first screen is the live PHC case queue.

Included pages:

- Queue
- Case Review
- Patients
- Referrals
- ASHA Tasks
- Local Sync
- Guidelines
- Daily Report
