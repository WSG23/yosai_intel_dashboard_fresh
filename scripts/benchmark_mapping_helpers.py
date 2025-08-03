import timeit
import pandas as pd
import re


def generate_rules(n=1000):
    english = {f"Canon{i}": [f"A{i}a", f"A{i}b"] for i in range(n)}
    japanese = {f"Canon{i}": [f"J{i}a", f"J{i}b"] for i in range(n)}

    class Rules:
        pass

    rules = Rules()
    rules.english = english
    rules.japanese = japanese
    return rules


def old_standardize(df, rules):
    mappings = {**rules.english}
    for key, vals in rules.japanese.items():
        mappings.setdefault(key, []).extend(vals)
    reverse = {}
    for canon, aliases in mappings.items():
        reverse[canon.lower()] = canon
        for alias in aliases:
            reverse[str(alias).lower()] = canon
    renamed = {}
    for col in df.columns:
        target = reverse.get(str(col).lower())
        if target:
            renamed[col] = target
    df = df.rename(columns=renamed)
    df.columns = [re.sub(r"\W+", "_", str(c)).strip("_").lower() for c in df.columns]
    return df


def new_standardize(df, rules):
    mappings = {**rules.english}
    for key, vals in rules.japanese.items():
        mappings.setdefault(key, []).extend(vals)
    reverse = {
        alias.lower(): canon
        for canon, aliases in mappings.items()
        for alias in {canon, *aliases}
    }
    renamed = {
        col: reverse[str(col).lower()]
        for col in df.columns
        if str(col).lower() in reverse
    }
    df = df.rename(columns=renamed)
    df.columns = [re.sub(r"\W+", "_", str(c)).strip("_").lower() for c in df.columns]
    return df


def generate_df(columns=1000):
    return pd.DataFrame({f"Col{i}": [i] for i in range(columns)})


def benchmark():
    df = generate_df()
    rules = generate_rules()
    t1 = timeit.timeit(lambda: old_standardize(df.copy(), rules), number=5)
    t2 = timeit.timeit(lambda: new_standardize(df.copy(), rules), number=5)
    print("Old mapping:", t1)
    print("Hash map mapping:", t2)


if __name__ == "__main__":
    benchmark()
