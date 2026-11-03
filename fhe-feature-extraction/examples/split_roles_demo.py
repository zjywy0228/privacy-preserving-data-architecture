"""Runnable split-role demo: owner encrypts, evaluator computes, owner decrypts."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import split_roles  # noqa: E402


def main() -> int:
    if not split_roles.TENSEAL_AVAILABLE:
        print("Install TenSEAL: pip install -e .[fhe]")
        return 1
    result = split_roles.run_split_roles_demo()
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0 if result["max_abs_error"] < 1e-3 else 1


if __name__ == "__main__":
    sys.exit(main())
