import math
import numpy as np
import matplotlib.pyplot as plt
from pyworkforce.queuing import ErlangC

# Data provided
arrival_rate_urgent = {
    "Monday": [4, 2, 1, 2, 2, 1, 2, 4, 8, 23, 77, 176, 320, 482, 473, 422, 380, 303, 225, 129, 75, 36, 21, 9],
    "Tuesday": [4, 3, 2, 2, 2, 2, 2, 3, 12, 36, 83, 172, 314, 442, 416, 367, 317, 245, 161, 117, 66, 24, 17, 8],
    "Wednesday": [4, 2, 2, 1, 1, 2, 2, 5, 12, 41, 92, 189, 340, 451, 437, 405, 362, 277, 199, 128, 66, 32, 16, 7],
    "Thursday": [5, 5, 3, 2, 2, 3, 2, 4, 11, 34, 92, 183, 329, 446, 429, 358, 315, 243, 173, 110, 61, 28, 14, 6],
    "Friday": [2, 2, 1, 3, 0, 3, 2, 4, 8, 28, 105, 203, 316, 436, 452, 395, 351, 267, 179, 122, 66, 32, 15, 8],
    "Saturday": [6, 3, 3, 1, 2, 2, 3, 6, 16, 40, 92, 212, 380, 519, 502, 470, 372, 312, 207, 123, 78, 34, 20, 9],
    "Sunday": [5, 2, 2, 3, 1, 2, 3, 4, 9, 31, 76, 142, 225, 258, 228, 169, 134, 98, 65, 30, 21, 12, 5, 5]
}

DAYS_OF_WEEK = ['Sunday', 'Monday', 'Tuesday',
                'Wednesday', 'Thursday', 'Friday', 'Saturday']
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
URGENT_TASK_WORK_MINUTES = 6.3  # Average work time for urgent tasks in minutes
SHIFT_HOURS = 8  # We can change the shift hours 4, 6, 8, or 12
SHIFT_PATTERN = 3  # Number of shift pattern to cover a full day according to SHIFT_HOURS
WORKDAYS_PER_WEEK = 6
SLA = 0.8
AVERAGE_SPEED_OF_ANSWER = 0.3  # Average speed of answer target in seconds


def calculate_required_staff(arrival_rate, service_time_minutes=URGENT_TASK_WORK_MINUTES, target_wait_probability=SLA):
    """
    Calculate the required number of staff based on arrival rate and service time
    using pyworkforce ErlangC implementation

    Parameters:
    arrival_rate (float): Average arrival rate per hour
    service_time_minutes (float): Average service time in minutes (default: URGENT_TASK_WORK_MINUTES)
    target_wait_probability (float): Target probability of waiting (default: 0.2 or 20%)

    Returns:
    int: Required number of staff
    """
    # Skip calculation if arrival rate is 0
    if arrival_rate == 0:
        return 0

    # Set up the ErlangC model with our parameters
    erlang = ErlangC(
        transactions=arrival_rate,
        aht=service_time_minutes,
        # Average speed of answer target (seconds)
        asa=AVERAGE_SPEED_OF_ANSWER,
        interval=60,  # 60-minute interval (1 hour)
        shrinkage=0  # Convert efficiency to shrinkage
    )

    # Calculate required positions for service level (1 - target_wait_probability)
    # Convert wait probability to service level

    result = erlang.required_positions(service_level=target_wait_probability)

    # Get the positions needed from the result
    # The result is a dictionary with 'positions' key
    agents_needed = result['positions']

    # Return the result as an integer, rounding up to ensure adequate staffing
    return int(np.ceil(agents_needed))


def calculate_hourly_staffing_needs():
    """
    Calculate staffing needs for each hour of each day

    Returns:
    dict: Dictionary with staffing needs for each day and hour
    """
    staffing_needs = {}

    for day in DAYS_OF_WEEK:
        staffing_needs[day] = []
        for hour in range(HOURS_PER_DAY):
            arrival = arrival_rate_urgent[day][hour]
            required_staff = calculate_required_staff(
                arrival, URGENT_TASK_WORK_MINUTES)
            staffing_needs[day].append(required_staff)

    return staffing_needs

# Function to visualize staffing needs


def visualize_staffing_needs(staffing_needs):
    """
    Create a visualization of staffing needs for each day

    Parameters:
    staffing_needs (dict): Dictionary with staffing needs for each day and hour
    """
    plt.figure(figsize=(14, 8))

    hours = list(range(HOURS_PER_DAY))

    for day in DAYS_OF_WEEK:
        plt.plot(hours, staffing_needs[day], marker='o', label=day)

    plt.xlabel('Hour of Day')
    plt.ylabel('Required Staff')
    plt.title('Hourly Staffing Needs Based on Erlang C')
    plt.grid(True)
    plt.legend()
    plt.xticks(hours)
    plt.savefig('hourly_staffing_needs.png')
    plt.close()
