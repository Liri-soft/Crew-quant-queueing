import numpy as np
from pyworkforce.queuing import ErlangC
from config import SHIFT_HOURS, AVG_HANDLING_TIME, CALL_VOLUME

# Data provided
arrival_rate_urgent = CALL_VOLUME
DAYS_OF_WEEK = ['Sunday', 'Monday', 'Tuesday',
                'Wednesday', 'Thursday', 'Friday', 'Saturday']
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SHIFT_IN_PATTERN = HOURS_PER_DAY // SHIFT_HOURS  # Number of shift pattern to cover a full day according to SHIFT_HOURS
WORKDAYS_PER_WEEK = 6
SLA = 0.8 # Service level agreement target (e.g., 80% of calls answered within target time) 
AVERAGE_SPEED_OF_ANSWER = 0.3  # Average speed of answer in minutes (e.g., 0.3 minutes or 18 seconds)


def calculate_required_staff(arrival_rate, service_time_minutes=AVG_HANDLING_TIME, target_wait_probability=SLA):
    """
    Calculate the required number of staff based on arrival rate and service time
    using pyworkforce ErlangC implementation

    Parameters:
    arrival_rate (float): Average arrival rate per hour
    service_time_minutes (float): Average service time in minutes (default: AVG_HANDLING_TIME)
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
        aht=service_time_minutes,  # Average speed of answer target (seconds)
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
                arrival, AVG_HANDLING_TIME)
            staffing_needs[day].append(required_staff)

    # Print staffing needs
    for day in DAYS_OF_WEEK:
        print(f"\n{day} staffing needs:")
        for hour, staff in enumerate(staffing_needs[day]):
            print(f"  Hour {hour}: {staff} staff needed")

    return staffing_needs

if __name__ == "__main__":
    # This allows the script to be run directly
    print("Calculating staffing needs...")
    staffing_needs = calculate_hourly_staffing_needs()
    
    # Display staffing needs for each day
    for day, needs in staffing_needs.items():
        print(f"\n{day} staffing needs: {needs}")
