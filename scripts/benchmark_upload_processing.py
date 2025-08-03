import timeit
import pandas as pd


def generate_data(frames=5, rows=10000):
    data = {}
    for i in range(frames):
        data[f"df{i}"] = pd.DataFrame(
            {
                "Person ID": [f"u{j%1000}" for j in range(rows)],
                "Device name": [f"d{j%50}" for j in range(rows)],
            }
        )
    return data


def nested_version(data):
    total_events = sum(len(df) for df in data.values())
    unique_users = {
        row.get("Person ID")
        for df in data.values()
        for row in df.to_dict("records")
        if "Person ID" in row
    }
    unique_doors = {
        row.get("Device name")
        for df in data.values()
        for row in df.to_dict("records")
        if "Device name" in row
    }
    return total_events, len(unique_users), len(unique_doors)


def optimized_version(data):
    total_events = sum(len(df) for df in data.values())
    users = set()
    doors = set()
    for df in data.values():
        if "Person ID" in df.columns:
            users.update(df["Person ID"].dropna().unique())
        if "Device name" in df.columns:
            doors.update(df["Device name"].dropna().unique())
    return total_events, len(users), len(doors)


def benchmark():
    data = generate_data()
    t1 = timeit.timeit(lambda: nested_version(data), number=5)
    t2 = timeit.timeit(lambda: optimized_version(data), number=5)
    print("Nested loops:", t1)
    print("Set aggregation:", t2)


if __name__ == "__main__":
    benchmark()
