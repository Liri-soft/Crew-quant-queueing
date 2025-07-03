import erlang_staffing
import copy
from erlang_staffing import SHIFT_HOURS


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

    # Calculate number of shifts needed to cover 24 hours
    shifts_per_day = erlang_staffing.HOURS_PER_DAY // shift_hours

    # We will consider 8 distinct patterns (starting at hours 0-7)
    for pattern_start in range(SHIFT_HOURS):
        pattern = []

        # For each shift in the pattern, calculate its start and end hours
        for shift_index in range(shifts_per_day):
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

def display_shift_patterns(patterns):
    """
    Display all generated shift patterns in a formatted way
    
    Parameters:
    patterns (list): List of pattern dictionaries
    """
    
    print(f"\nGenerated {len(patterns)} shift patterns:")
    for pattern in patterns:
        print(f"  Pattern {pattern['pattern_number']}:")
        
        for i, shift in enumerate(pattern['shifts']):
            shift_names = ["First", "Second", "Third", 
                           "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
            
            shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
            start_time = f"{shift['start_hour']:02d}:00"
            end_time = f"{shift['end_hour']:02d}:00"
            
            print(f"    {shift_type} Shift: {start_time}-{end_time}")

def display_pattern_evaluations(all_patterns, staffing_needs):
    """
    Display evaluations of all patterns across all days
    
    Parameters:
    all_patterns (list): List of pattern dictionaries
    staffing_needs (dict): Dictionary with staffing needs for each day
    """

    print("\nAnalyzing staffing needs for each shift pattern and day:")
    
    for day in staffing_needs.keys():
        print(f"\n{day} - Staffing needs by pattern:")
        
        for pattern in all_patterns:
            evaluated_pattern = evaluate_shift_pattern(pattern, staffing_needs[day])
            total_agents = evaluated_pattern['total_agents']
            total_agent_hours = evaluated_pattern['total_agent_hours']
            
            print(f"  Pattern {pattern['pattern_number']}: Total {total_agents} agents needed, {total_agent_hours} agent hours")
            
            for i, shift in enumerate(evaluated_pattern['shifts']):
                shift_names = ["First", "Second", "Third", 
                              "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
                
                shift_type = shift_names[i] if i < len(shift_names) else f"Shift {i+1}"
                start_time = f"{shift['start_hour']:02d}:00"
                end_time = f"{shift['end_hour']:02d}:00"
                agents = shift['agents_needed']
                agent_hours = shift['agent_hours']
                
                print(f"    {shift_type} Shift ({start_time}-{end_time}): {agents} agents, {agent_hours} agent hours")

if __name__ == "__main__":
    # This allows the script to be run directly
    print("Generating shift patterns...")
    all_patterns = generate_shift_patterns()

    display_shift_patterns(all_patterns)
    


    



