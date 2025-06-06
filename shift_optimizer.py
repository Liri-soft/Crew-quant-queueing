import matplotlib.pyplot as plt
import numpy as np
import erlang_staffing
import copy
from erlang_staffing import SHIFT_HOURS, SHIFT_PATTERN


# def evaluate_shift_pattern(pattern, staffing_needs_day):
#     """
#     Evaluate a shift pattern by calculating total agents needed for all three shifts
#     """
#     # Use deepcopy instead of shallow copy
#     pattern_copy = copy.deepcopy(pattern)
#     total_agents = 0

#     # Calculate agents needed for each shift in the pattern
#     for i, shift in enumerate(pattern_copy['shifts']):
#         agents = calculate_agents_needed(shift, staffing_needs_day)
#         pattern_copy['shifts'][i]['agents_needed'] = agents
#         total_agents += agents

#     # Add total agents to the pattern
#     pattern_copy['total_agents'] = total_agents

#     return pattern_copy


def generate_shift_patterns(shift_hours=SHIFT_HOURS):
    """
    Generate 8 distinct shift patterns, each consisting of three 8-hour shifts that cover a full day

    Parameters:
    shift_hours (int): Length of each shift in hours (default: 8)

    Returns:
    list: List of shift patterns, where each pattern is a list of three shifts

    Each pattern starts at a different hour (0-7), and consists of three consecutive 8-hour shifts.
    For example, pattern 0 has shifts at 0:00-8:00, 8:00-16:00, and 16:00-0:00.
    """
    patterns = []

    # We will consider 8 distinct patterns (starting at hours 0-7)
    for pattern_start in range(SHIFT_HOURS):
        pattern = []

        # Each pattern has exactly 3 shifts of 8 hours each
        for shift_index in range(SHIFT_PATTERN):
            # Calculate the start hour for this shift
            start_hour = (pattern_start + shift_index *
                          shift_hours) % erlang_staffing.HOURS_PER_DAY

            # Calculate the end hour, handling wrap-around to next day
            end_hour = (
                start_hour + shift_hours) % erlang_staffing.HOURS_PER_DAY

            # Create a list of hours covered by this shift
            hours_covered = []
            current_hour = start_hour

            # Add each hour in the shift to the hours_covered list
            for _ in range(shift_hours):
                hours_covered.append(current_hour)
                current_hour = (
                    current_hour + 1) % erlang_staffing.HOURS_PER_DAY

            # Create a shift dictionary with all needed information
            shift = {
                'start_hour': start_hour,
                'end_hour': end_hour,
                'hours': hours_covered,
                'shift_number': shift_index + 1  # 1, 2, or 3
            }

            # Add this shift to the pattern
            pattern.append(shift)

        # Add this pattern to our list of all patterns
        patterns.append({
            'pattern_number': pattern_start,
            'shifts': pattern
        })

    return patterns


def calculate_agents_needed(shift, staffing_needs_day):
    """
    Calculate how many agents are needed for a specific shift based on staffing needs

    Parameters:
    shift (dict): A shift dictionary with 'hours' key containing list of hours covered
    staffing_needs_day (list): List of staffing needs for each hour of the day

    Returns:
    int: The maximum number of agents needed during any hour of the shift

    This function finds the peak staffing requirement for any hour covered by the shift.
    We need to staff according to the peak hour to ensure adequate coverage.
    """
    # Find the maximum staffing need for any hour in this shift
    agents_needed = max([staffing_needs_day[hour] for hour in shift['hours']])

    return agents_needed


def evaluate_shift_pattern(pattern, staffing_needs_day):
    """
    Evaluate a shift pattern by calculating total agents needed for all three shifts
    and the total agent hours

    Parameters:
    pattern (dict): A pattern dictionary with 'shifts' list containing three shifts
    staffing_needs_day (list): List of staffing needs for each hour of the day

    Returns:
    dict: The pattern with agents_needed, agent_hours added to each shift and total_agents, total_agent_hours fields
    """
    total_agents = 0
    total_agent_hours = 0
    pattern_copy = copy.deepcopy(pattern)

    # Calculate agents needed for each shift in the pattern
    for i, shift in enumerate(pattern_copy['shifts']):
        agents = calculate_agents_needed(shift, staffing_needs_day)
        pattern_copy['shifts'][i]['agents_needed'] = agents
        total_agents += agents

        # Calculate agent hours for this shift
        # Get actual shift length from hours covered
        shift_length = len(shift['hours'])
        agent_hours = agents * shift_length
        pattern_copy['shifts'][i]['agent_hours'] = agent_hours
        total_agent_hours += agent_hours

    # Add total agents and agent hours to the pattern
    pattern_copy['total_agents'] = total_agents
    pattern_copy['total_agent_hours'] = total_agent_hours

    return pattern_copy


def create_shift_plan(staffing_needs):
    """
    Create an optimal shift plan based on staffing needs

    Parameters:
    staffing_needs (dict): Dictionary with staffing needs for each day and hour

    Returns:
    dict: Dictionary with optimal shift pattern for each day
    """
    # Generate all possible shift patterns
    all_patterns = generate_shift_patterns()
    shift_plan = {}

    # For each day, find the optimal shift pattern
    for day in erlang_staffing.DAYS_OF_WEEK:
        # Evaluate each pattern for this day
        evaluated_patterns = []
        for pattern in all_patterns:
            evaluated_pattern = evaluate_shift_pattern(
                pattern, staffing_needs[day])
            evaluated_patterns.append(evaluated_pattern)

        # Find the pattern with the minimum total agents
        best_pattern = min(evaluated_patterns, key=lambda p: p['total_agents'])

        # Store the best pattern for this day
        shift_plan[day] = copy.deepcopy(best_pattern)

    return shift_plan
