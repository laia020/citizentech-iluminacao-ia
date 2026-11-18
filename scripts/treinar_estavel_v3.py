import argparse
from pathlib import Path

from citizentech_ia.v3.training_stable import run_stable


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--lr", type=float, default=0.00005)
    p.add_argument("--microsteps", type=int, default=800)
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    run_stable(Path("experimentos/v3"), args.name, args.lr, args.microsteps, args.smoke)


if __name__ == "__main__":
    main()
