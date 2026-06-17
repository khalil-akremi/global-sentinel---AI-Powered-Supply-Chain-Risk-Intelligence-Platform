from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from features.feature_store import initialize_feature_store

if __name__ == "__main__":
    initialize_feature_store()