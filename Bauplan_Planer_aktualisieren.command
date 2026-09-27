#!/usr/bin/env bash
# SC Bauplan-Planer neu bauen (Doppelklick auf macOS).
cd "$(dirname "$0")" || exit 1
python3 bauplan_planer_bauen.py && echo "Fertig. SC_Bauplan_Planer.html wurde aktualisiert."
