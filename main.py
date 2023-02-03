import itertools
import sys


def has_overlap(a: dict, b: dict) -> bool:
    a = set(a.items())
    b = set(b.items())
    return not a.isdisjoint(b)


def is_subset(a: dict, b: dict) -> bool:
    a = set(a.items())
    b = set(b.items())
    return a.issubset(b)


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
    includes = matrix.pop("include", [])
    excludes = matrix.pop("exclude", [])

    dimensions = []
    for var, values in matrix.items():
        astuples = [(var, value) for value in values]
        dimensions.append(astuples)

    original_combinations = (
        [dict(c) for c in itertools.product(*dimensions)] if dimensions else []
    )

    combinations = original_combinations

    for include in includes:
        overwrites_one = False
        overwrites_all = True
        for combination in original_combinations:
            overwrites = False
            for k, v in include.items():
                if k in combination and combination[k] != v:
                    overwrites = True
            if overwrites:
                overwrites_one = True
            overwrites_all = overwrites_all and overwrites

        if overwrites_all:
            combinations.append(include)

        elif not overwrites_one:
            combinations = [c | include for c in combinations]

        else:
            combinations = [
                c | include if has_overlap(c, include) else c for c in combinations
            ]

    filtered_combinations = [
        c
        for c in combinations
        if not any(is_subset(exclude, c) for exclude in excludes)
    ]

    return filtered_combinations


def test_include_only():
    matrix = {
        "include": [
            {"a": 42},
        ]
    }
    expected = [
        {"a": 42},
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

        matrix = job.get("strategy", {}).get("matrix")
        if not matrix:
            continue

        combinations = matrix_combinations(matrix)

        for combination in combinations:
            print("-", combination)
