import sys
from source_relocation.cli import main


if __name__ == "__main__":
    main(["internal", "--experiment", "representation", *sys.argv[1:]])
