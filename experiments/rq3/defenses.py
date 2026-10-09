import sys
from source_relocation.cli import main


if __name__ == "__main__":
    main(["run", "--rq", "rq3", "--experiment", "defenses", *sys.argv[1:]])
