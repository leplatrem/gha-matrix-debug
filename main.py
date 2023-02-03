import sys


def matrix_combinations(matrix) -> list[dict]:
    """
    https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs#expanding-or-adding-matrix-configurations

    For each object in the include list, the key:value pairs in the object will
    be added to each of the matrix combinations if none of the key:value pairs
    overwrite any of the original matrix values. If the object cannot be added
    to any of the matrix combinations, a new matrix combination will be created
    instead. Note that the original matrix values will not be overwritten, but
    added matrix values can be overwritten.
    """
    return []


def test_include_only():
    matrix = {
        "include": [
            {"a": 42},
            {"a": "foo"},
        ]
    }
    expected = [
        {"a": 42},
        {"a": "foo"},
    ]
    assert matrix_combinations(matrix) == expected


def test_exclude():
    matrix = {
        "a": [1, 2],
        "b": [3, 4],
        "exclude": [
            {"a": 1},
            {"a": 2, "b": 4},
        ],
    }
    expected = [
        {"a": 2, "b": 3},
    ]
    assert matrix_combinations(matrix) == expected


def test_official_documentation_example():
    matrix = {
        "fruit": ["apple", "pear"],
        "animal": ["cat", "dog"],
        "include": [
            {"color": "green"},
            {"color": "pink", "animal": "cat"},
            {"fruit": "apple", "shape": "circle"},
            {"fruit": "banana"},
            {"fruit": "banana", "animal": "cat"},
        ],
    }

    expected = [
        {"fruit": "apple", "animal": "cat", "color": "pink", "shape": "circle"},
        {"fruit": "apple", "animal": "dog", "color": "green", "shape": "circle"},
        {"fruit": "pear", "animal": "cat", "color": "pink"},
        {"fruit": "pear", "animal": "dog", "color": "green"},
        {"fruit": "banana"},
        {"fruit": "banana", "animal": "cat"},
    ]

    # * {color: green} is added to all of the original matrix combinations because
    # it can be added without overwriting any part of the original
    # combinations.

    # * {color: pink, animal: cat} adds color:pink only to the
    # original matrix combinations that include animal: cat. This overwrites
    # the color: green that was added by the previous include entry.

    # * {fruit: apple, shape: circle} adds shape: circle only to the original
    # matrix combinations that include fruit: apple.

    # * {fruit: banana} cannot be
    # added to any original matrix combination without overwriting a value, so
    # it is added as an additional matrix combination.

    # * {fruit: banana, animal: cat} cannot be added to any original matrix combination
    # without overwriting a value, so it is added as an additional matrix combination.
    # It does not add to the {fruit: banana} matrix combination because that
    # combination was not one of the original matrix combinations.

    combinations = matrix_combinations(matrix)

    for combination in expected:
        assert combination in combinations
        combinations.remove(combination)
    assert len(combinations) == 0


if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("Run `pip install pyyaml`")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        content = yaml.safe_load(f)

    for name, job in content["jobs"].items():
        job_name = job.get("name", name)
        interpolated = re.findall("\\$\\{\\{([^\\}]+)\\}\\}", job_name)

        matrix = job.get("strategy", {}).get("matrix")
        if not matrix:
            continue

        combinations = matrix_combinations(matrix)

        for combination in combinations:
            for var in interpolated:
                _, field = var.split(".")  # ${{ matrix.{var} }}
                value = combination.get(field.strip(), "")
                job_name = job_name.replace(f"${{{{{var}}}}}", str(value))
            print(f"\n- {job_name}")
            for var, value in combination.items():
                print(f"  {var}: {value}")
