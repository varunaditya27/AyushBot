"""Table presentation helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def compact_table(rows: list[dict], empty_message: str, **kwargs) -> None:
	if not rows:
		st.info(empty_message)
		return
	st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, **kwargs)
