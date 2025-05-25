import math

def karber(doses: list[float], max_animals: int, died: list[int]) -> float:
    """
    counts ld50 using karber's method
    :param doses: list of doses (must be sorted descending)
    :param max_animals: number of animals in a trial
    :param died: an array of numbers of dead animals for each dose
    :return: ld50 for the dataset
    """
    if len(doses) != len(died):
        raise ValueError("Количество доз и количество значений умерших должно совпадать.")
    n = len(doses)
    # Проверка на убывание доз
    for i in range(n - 1):
        if doses[i] < doses[i + 1]:
            raise ValueError("Дозы должны быть в порядке убывания (от максимальной к минимальной).")
    for i in died:
        if i > max_animals:
            raise ValueError("Количество умерших не может превышать количество животных в группе.")
    proportion_died = [died[i] / max_animals for i in range(n)]
    # Метод Кербера для произвольных доз
    sum_term = 0.0
    for i in range(n - 1):
        diff = doses[i] - doses[i + 1]
        avg = (proportion_died[i] + proportion_died[i + 1]) / 2
        sum_term += diff * avg
    ld50 = doses[0] - sum_term
    return ld50


# test
if __name__ == "__main__":
    print(karber([1000000, 100000, 10000, 1000, 100, 10, 1, 0.1], 8, [0, 0, 0, 5, 8, 8, 8, 8]))

