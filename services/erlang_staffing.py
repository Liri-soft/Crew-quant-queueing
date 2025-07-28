import numpy as np
from services.logging_config import setup_logger
from pyworkforce.queuing import ErlangC
from config_variables.config import SHIFT_HOURS, AVG_HANDLING_TIME, CALL_VOLUME, TARGET_SLA, DESIRED_SLA


logger = setup_logger(__name__)

# Data provided
arrival_rate_urgent = CALL_VOLUME
DAYS_OF_WEEK = ['Sunday', 'Monday', 'Tuesday',
                'Wednesday', 'Thursday', 'Friday', 'Saturday']
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SHIFT_IN_PATTERN = HOURS_PER_DAY // SHIFT_HOURS  # Number of shift pattern to cover a full day according to SHIFT_HOURS
WORKDAYS_PER_WEEK = 6
# SLA = DESIRED_SLA/100 # Service level agreement target (e.g., 95% of calls answered within target time) 

AVERAGE_SPEED_OF_ANSWER = TARGET_SLA/60  # Average speed of answer in minutes (e.g., 0.33 minutes or 20 seconds)


def calculate_required_staff(arrival_rate, service_time_minutes=AVG_HANDLING_TIME, target_wait_probability=None):
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
        logger.debug(f"Arrival rate is 0, returning 0 staff")
        return 0

    try:
        # Set up the ErlangC model with our parameters
        logger.debug(f"Calculating staff for arrival rate {arrival_rate}, service time {service_time_minutes} min")
        erlang = ErlangC(
            transactions=arrival_rate,
            aht=service_time_minutes,  # Average speed of answer target (seconds)
            asa=AVERAGE_SPEED_OF_ANSWER,
            interval=60,  # 60-minute interval (1 hour)
            shrinkage=0  # Convert efficiency to shrinkage
        )
        
        hardcoded_service_level = 0
        # Calculate required positions for service level
        result = erlang.required_positions(service_level=hardcoded_service_level)

        # Get the positions needed from the result
        agents_needed = result['positions']

        # Return the result as an integer, rounding up to ensure adequate staffing
        staff_count = int(np.ceil(agents_needed))
        logger.debug(f"Calculated {staff_count} staff needed for arrival rate {arrival_rate}")
        return staff_count
        
    except Exception as e:
        logger.error(f"Error in Erlang C calculation: {str(e)}")
        raise  # Re-raise the exception after logging


def calculate_hourly_staffing_needs():
    """
    Calculate staffing needs for each hour of each day

    Returns:
    dict: Dictionary with staffing needs for each day and hour
    """
    logger.info("Starting calculation of hourly staffing needs")
    staffing_needs = {}

    for day in DAYS_OF_WEEK:
        staffing_needs[day] = []
        for hour in range(HOURS_PER_DAY):
            arrival = arrival_rate_urgent[day][hour]
            required_staff = calculate_required_staff(
                arrival, AVG_HANDLING_TIME)
            staffing_needs[day].append(required_staff)
            logger.debug(f"{day}, Hour {hour}: {required_staff} staff needed for {arrival} calls")

    # Log staffing needs with INFO level
    for day in DAYS_OF_WEEK:
        logger.info(f"{day} staffing needs: {staffing_needs[day]}")

    logger.info("Completed calculation of hourly staffing needs")
    return staffing_needs

if __name__ == "__main__":
    # This allows the script to be run directly
    logger.info("Running erlang_staffing.py directly")
    logger.info("Calculating staffing needs...")
    
    try:
        staffing_needs = calculate_hourly_staffing_needs()
        logger.info("Staffing calculation completed successfully")
    except Exception as e:
        logger.critical(f"Failed to calculate staffing needs: {str(e)}")