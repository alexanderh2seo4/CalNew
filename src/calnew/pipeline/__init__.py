"""Modular odour pipeline: A quality -> B potency (threshold, dose-response) -> C combiner.

See docs/PIPELINE.md. Stages are trained separately and connected through out-of-fold
meta-features; the fusion encoder is a NOSE-inspired (arXiv:2604.10452) block fusion.
"""
