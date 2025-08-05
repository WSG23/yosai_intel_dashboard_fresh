import timeit
import numpy as np


def loop_metrics(preds, labels):
    total = len(labels)
    correct = sum(p == t for p, t in zip(preds, labels))
    accuracy = correct / total
    pos_label = 1
    tp = sum(1 for p, t in zip(preds, labels) if p == pos_label and t == pos_label)
    fp = sum(1 for p, t in zip(preds, labels) if p == pos_label and t != pos_label)
    fn = sum(1 for p, t in zip(preds, labels) if p != pos_label and t == pos_label)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return accuracy, precision, recall


def vectorized_metrics(preds, labels):
    preds_arr = np.array(preds)
    labels_arr = np.array(labels)
    accuracy = float(np.mean(preds_arr == labels_arr))
    pos_label = 1
    pred_pos = preds_arr == pos_label
    label_pos = labels_arr == pos_label
    tp = int(np.sum(pred_pos & label_pos))
    fp = int(np.sum(pred_pos & ~label_pos))
    fn = int(np.sum(~pred_pos & label_pos))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return accuracy, precision, recall


def loop_odd_time(hours, mean_hour, std_hour):
    if std_hour == 0:
        return any(h != mean_hour for h in hours)
    for h in hours:
        if abs(h - mean_hour) > 2 * std_hour:
            return True
    return False


def vectorized_odd_time(hours, mean_hour, std_hour):
    hours_arr = np.array(hours)
    if std_hour == 0:
        return np.any(hours_arr != mean_hour)
    return np.any(np.abs(hours_arr - mean_hour) > 2 * std_hour)


def benchmark():
    n = 100000
    preds = np.random.randint(0, 2, size=n)
    labels = np.random.randint(0, 2, size=n)
    hours = np.full(n, 12, dtype=int)
    mean_hour = 12
    std_hour = 3

    t_loop_metrics = timeit.timeit(lambda: loop_metrics(preds, labels), number=10)
    t_vec_metrics = timeit.timeit(lambda: vectorized_metrics(preds, labels), number=10)
    t_loop_odd = timeit.timeit(lambda: loop_odd_time(hours, mean_hour, std_hour), number=100)
    t_vec_odd = timeit.timeit(lambda: vectorized_odd_time(hours, mean_hour, std_hour), number=100)
    print("Metrics loop:", t_loop_metrics)
    print("Metrics vectorized:", t_vec_metrics)
    print("Odd-time loop:", t_loop_odd)
    print("Odd-time vectorized:", t_vec_odd)


if __name__ == "__main__":
    benchmark()
