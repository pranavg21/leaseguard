"""Deposit-recovery dossier: turn raw evidence into a verified, filing-ready bundle.

The dossier is built after a tenancy ends and the deposit is not returned. It
hashes every evidence file, extracts a dated timeline in which every event
quotes its source verbatim, reconciles the deposit, flags contradictions and
produces the BSA s.63(4)(c) certificate in the Schedule's form (Part A pre-filled,
Part B blank for an expert) and a draft demand notice for the user to
review, complete and sign.
"""
