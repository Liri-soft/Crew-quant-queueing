import math
import numpy as np
import matplotlib.pyplot as plt

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
AGENT_EFFICIENCY = 0.7
URGENT_TASK_WORK_MINUTES = 6.3
SHIFT_HOURS = 8  # We can change the shift hours 4, 6, 8, or 12
SHIFT_PATTERN = 3  # Number of shift pattern to cover a full day according to SHIFT_HOURS
WORKDAYS_PER_WEEK = 6

# Step 1: Implement Erlang C formula


def erlang_c(traffic_intensity, num_agents):
    """
    Calculate the probability of waiting using Erlang C formula

    Parameters:
    traffic_intensity (float): Traffic intensity (arrival rate * service time)
    num_agents (int): Number of agents/servers

    Returns:
    float: Probability of waiting
    """
    if num_agents <= traffic_intensity:
        return 1.0  # If traffic intensity >= agents, probability of waiting is 100%

    # Calculate the first part of the Erlang C formula

    # Calculate the probability that all agents are busy (numerator part 1)
    part1 = (traffic_intensity ** num_agents) / math.factorial(num_agents)

    # Calculate the adjustment factor for waiting (numerator part 2)
    part2 = num_agents / (num_agents - traffic_intensity)

    # Calculate the sum of probabilities that 0 to (num_agents - 1) agents are busy (denominator)
    sum_part = 0
    for i in range(num_agents):
        sum_part += (traffic_intensity ** i) / math.factorial(i)

    # Combine all parts to get the Erlang C probability of waiting
    probability_waiting = (part1 * part2) / (sum_part + (part1 * part2))

    # Return the probability that an arriving task will have to wait
    return probability_waiting

# Step 2: Calculate required staff based on arrival rate and service time


def calculate_required_staff(arrival_rate, service_time_minutes=URGENT_TASK_WORK_MINUTES, target_wait_probability=0.2):
    """
    Calculate the required number of staff based on arrival rate and service time

    Parameters:
    arrival_rate (float): Average arrival rate per hour
    service_time_minutes (float): Average service time in minutes (default: URGENT_TASK_WORK_MINUTES)
    target_wait_probability (float): Target probability of waiting (default: 0.2 or 20%)

    Returns:
    int: Required number of staff
    """
    # Convert service time to hours to calculate the traffic intensity
    service_time_hours = service_time_minutes / MINUTES_PER_HOUR

    # Calculate traffic intensity (arrival rate * service time)
    traffic_intensity = arrival_rate * service_time_hours

    # Start with the minimum possible number of agents
    num_agents = max(1, math.ceil(traffic_intensity))

    # Increase number of agents until we meet the target wait probability
    while erlang_c(traffic_intensity, num_agents) > target_wait_probability:
        num_agents += 1

    # Adjust for agent efficiency
    adjusted_agents = math.ceil(num_agents / AGENT_EFFICIENCY)

    return adjusted_agents

# Step 3: Calculate staffing needs for each hour of each day


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
