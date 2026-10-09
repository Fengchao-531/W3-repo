import sys
from source_relocation.cli import main


if __name__ == "__main__":
    main(["run", "--rq", "rq1", "--experiment", "preference", *sys.argv[1:]])
