import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-od", "--out-dir",
                        help="Directory with artifacts")

    parser.add_argument("-ptr", "--path-to-remove",
                        help="Path to remove from artifacts")

    return parser.parse_args()


def main():
    args = parse_args()
    out_dir: str = args.out_dir
    path_to_remove: str = args.path_to_remove

    if path_to_remove[-1] != os.path.sep:
        path_to_remove += os.path.sep

    files_to_sanitize = [
        'CMakeCache.txt',
        os.path.join('zephyr', 'runners.yaml'),
    ]

    for file_name in files_to_sanitize:
        file_name = os.path.join(out_dir, file_name)

        if not os.path.exists(file_name):
            continue

        with open(file_name, "rt") as file:
            data = file.read()
            data = data.replace(path_to_remove, "")

        with open(file_name, "wt") as file:
            file.write(data)


if __name__ == "__main__":
    main()
