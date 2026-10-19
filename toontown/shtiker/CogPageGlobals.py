COG_QUOTAS = ((30, 25, 20, 15, 10, 5, 2, 1), (45, 40, 35, 30, 25, 20, 15, 10))
COG_UNSEEN = 1
COG_BATTLED = 2
COG_DEFEATED = 3
COG_COMPLETE1 = 4
COG_COMPLETE2 = 5


def pad_collection(values, size, default=0):
    """Extend old DB arrays without losing existing progress or future slots."""
    result = list(values or ())
    result.extend([default] * max(0, size - len(result)))
    return result
