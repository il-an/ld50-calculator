import math

def karber(max_dose: int, max_animals: int, died: list[int], dose_coefficient: int = 10, number_of_doses: int = 8) -> float:
    """
    counts ld50 using karber's method
    :param max_dose: maximum dose used
    :param max_animals: number of animals in a trial
    :param died: an array of numbers of dead animals for each dose
    :param dose_coefficient: the coefficient by which the dose lowers
    :param number_of_doses: the number of doses used
    :return: ld50 for the dataset
    """
    if len(died) != number_of_doses:
        raise ValueError("The number of doses must equal the number of experiments.")
    for i in died:
        if i > max_dose:
            raise ValueError("The number of deceased animals should be less than the number of animals in each group.")
    proportion_died = [died[i] / max_animals for i in range(0, number_of_doses)]
    ld50 = 10 ** (math.log(max_dose, 10) - math.log(dose_coefficient, 10)*(sum(proportion_died) - 0.5))
    return ld50


# test
if __name__ == "__main__":
    print(karber(1000000, 8, [0, 0, 0, 4, 8, 8, 8, 8]))
