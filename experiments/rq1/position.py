import sys
from source_relocation.cli import main


if __name__ == "__main__":
    main(["run", "--rq", "rq1", "--experiment", "position", *sys.argv[1:]])
