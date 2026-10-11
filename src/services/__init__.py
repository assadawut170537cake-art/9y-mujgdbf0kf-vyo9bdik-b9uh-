"""
Optional local AI services for MARK-LV.

Modules here are imported lazily and guarded at the point of use, so a missing
heavy dependency (torch, unsloth, …) disables exactly one service and never
breaks the app — the same contract as the plugin extras in requirements.txt.
"""
