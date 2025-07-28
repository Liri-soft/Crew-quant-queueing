import simpy
import numpy as np
import services.erlang_staffing
import services.ideal_shift
from services.erlang_staffing import arrival_rate_urgent
from config_variables.config import TARGET_SLA, DESIRED_SLA, SHIFT_HOURS, AVG_PATIENCE, LUNCH_BREAK_TIME, MAX_PERCENTAGE_AGENTS_ON_BREAK, AVG_HANDLING_TIME, CALL_COMPLEXITY_DISTRIBUTION, ACW_MIN, ACW_MAX, AGENT_EFFICIENCY

# Convert minutes to seconds for simulation
AHT = AVG_HANDLING_TIME * 60  # Average handling time in seconds
# Break time in seconds (break time varies for each agent)
LUNCH_BREAK_DURATION = LUNCH_BREAK_TIME * 60
MAX_AGENTS_ON_BREAK = MAX_PERCENTAGE_AGENTS_ON_BREAK / \
    100  # Convert percentage to fraction


def run_shift_simulation(num_agents, hourly_arrival_rates, shift_hours=SHIFT_HOURS,
                         service_time_seconds=AHT, avg_patience_seconds=AVG_PATIENCE, debug=False):
    """Run a simulation for an entire shift (multiple hours)"""
    # Set a fixed seed
    np.random.seed(42)

    def debug_print(message):
        """Print debug messages with current simulation time"""
        if debug:
            time_str = f"{env.now/3600:.2f}h" if env.now > 0 else "0h"
            print(f"[TIME {time_str}] {message}")

    if sum(hourly_arrival_rates) == 0:
        return {
            "calls_arrived": 0,
            "calls_handled": 0,
            "calls_abandoned": 0,
            "calls_expected": 0,
            "avg_wait": 0,
            "max_wait": 0,
            "service_level": 100,
        }

    # avilable_agents = num_agents * 0.5
    # Setup simulation environment
    env = simpy.Environment()

    # Adjust capacity based on agent efficiency
    agents = simpy.Resource(env, capacity=num_agents * AGENT_EFFICIENCY / 100)
    # Tracking variables
    wait_times = []
    calls_handled = 0
    calls_arrived = 0
    calls_abandoned = 0

    # Calculate total simulation duration
    sim_duration = shift_hours * 3600  # in seconds

    def call_generator(env, agents):
        """Generate calls based on arrival rates that vary by hour"""
        nonlocal calls_arrived

        # For each hour in the shift
        for hour, rate in enumerate(hourly_arrival_rates):
            # Generate arrivals for this hour
            if rate > 0:
                # Generate random arrival times within this hour
                hour_arrivals = np.random.uniform(
                    hour*3600, (hour+1)*3600, rate)

                for arrival_time in sorted(hour_arrivals):
                    # Wait until arrival time
                    yield env.timeout(arrival_time - env.now)

                    # Generate a new call
                    calls_arrived += 1
                    call_id = calls_arrived  # Unique ID for this call
                    debug_print(f"CALL {call_id} ARRIVED")
                    call_process = env.process(
                        handle_call(env, agents, call_id))
                    # print(f"call process {call_process}")

    # Add tracking for utilization
    total_busy_time = 0  # Total time agents spend on calls + ACW
    total_scheduled_time = num_agents * shift_hours * \
        3600  # Total agent seconds available

    def handle_call(env, agents, call_id):
        """Handle an incoming call with potential abandonment"""
        nonlocal calls_handled, calls_abandoned, total_busy_time
        arrival_time = env.now

        # Determine call complexity (normal, semicomplex, or complex)
        call_complexity = np.random.choice(['normal', 'semicomplex', 'complex'],  # selecting call complexity
                                           # probabilities of selecting call complexity
                                           p=[x / 100 for x in CALL_COMPLEXITY_DISTRIBUTION["probabilities"]])

        # Set handling time based on complexity
        if call_complexity == 'normal':
            # Normal calls are shorter
            complexity_factor = 1.0
        elif call_complexity == 'semicomplex':
            # Semicomplex calls use the standard time
            # increased times the average handling time
            complexity_factor = CALL_COMPLEXITY_DISTRIBUTION["complexity_factors"]["semicomplex"]
        else:  # complex
            # Complex calls take longer
            # increased times the average handling time
            complexity_factor = CALL_COMPLEXITY_DISTRIBUTION["complexity_factors"]["complex"]

        # Generate variable service and patience times
        service_time = np.random.exponential(
            service_time_seconds * complexity_factor)
        # gentate after call work time (After call is complited agent need some time to document the call)
        # seconds after call work time
        acw = np.random.uniform(ACW_MIN, ACW_MAX)
        # print(f"service time {service_time}")
        patience = np.random.exponential(avg_patience_seconds)

        # Try to get an agent
        with agents.request() as req:
            debug_print(f"CALL {call_id} REQUESTING AGENT")
            # Wait for either getting an agent or running out of patience time
            results = yield env.timeout(patience) | req
            wait_time = env.now - arrival_time  # storing wait time

            # Check if call was abandoned
            if req not in results:
                calls_abandoned += 1
                debug_print(f"CALL {call_id} ABANDONED after {wait_time:.1f}s")
                return

            # Call was handled
            debug_print(
                f"CALL {call_id} GOT AGENT after {wait_time:.1f}s wait")
            wait_times.append(wait_time)
            calls_handled += 1

            # Track the time this call will take (including ACW)
            call_duration = service_time + acw
            total_busy_time += call_duration

            # Handle the call
            # Include after call work time
            yield env.timeout(call_duration)
            debug_print(
                f"CALL {call_id} FINISHED ({service_time:.1f}s talk + {acw:.1f}s ACW)")
            # print(f"call no {calls_handled} service time {service_time}")

    def break_scheduler(env, agents):
        """Schedule breaks for agents during the shift"""

        # Calculate maximum agents that can be on break at once
        max_on_break = max(1, int(num_agents * MAX_AGENTS_ON_BREAK))

        # Number of break slots needed (based on max agents on break)
        num_break_slots = int(np.ceil(num_agents / max_on_break))

        # Calculate middle of shift
        mid_shift = (shift_hours / 2) * 3600  # Middle of shift in seconds

        # Calculate the total time span from start of first break to start of last break
        total_break_span = (num_break_slots - 1) * LUNCH_BREAK_DURATION

        # Calculate start time for first break group so all breaks are centered around mid-shift
        first_break_start = mid_shift - (total_break_span / 2)

        def agent_on_break(env, duration, break_id, group_id):
            """Process for an agent going on break"""
            # Request an agent (removing them from the available pool)
            with agents.request() as agent_req:
                yield agent_req
                debug_print(f"BREAK {break_id} (Group {group_id}) GOT AGENT")

            adherence_to_break = np.random.choice([1.0, 1.1, 1.2, 1.3],  # 60% chance of taking full break, 20% chance of taking 10% longer, etc.
                                                  # giving probabilities to choose different adherence levels
                                                  p=[0.60, 0.20, 0.10, 0.10])

            actual_duration = duration * adherence_to_break

            debug_print(
                f"BREAK {break_id} (Group {group_id}) STARTED ({actual_duration:.1f}s)")
            # print(f"break started at {env.now}secs at 8 hr shift on break for {actual_duration} seconds")

            # Wait for break duration
            yield env.timeout(actual_duration)

            debug_print(f"BREAK {break_id} (Group {group_id}) FINISHED")

        # Schedule breaks for groups of agents
        agent_count = 0
        break_counter = 0

        for group in range(num_break_slots):
            # Calculate remaining agents
            remaining = num_agents - agent_count

            # Calculate group size (min of max_on_break or remaining agents)
            group_size = min(max_on_break, remaining)

            # Calculate break start time for this group
            break_start = first_break_start + (group * LUNCH_BREAK_DURATION)
            # print({break_start})

            # Wait until break time for this group
            if break_start > env.now:
                debug_print(
                    f"WAITING {break_start - env.now:.1f}s for Break Group {group+1}")
                yield env.timeout(break_start - env.now)

            debug_print(
                f"SCHEDULING BREAK GROUP {group+1} ({group_size} agents)")
            # Send each agent in the group on break
            for i in range(group_size):
                break_counter += 1
                agent_process = env.process(agent_on_break(
                    env, LUNCH_BREAK_DURATION, break_counter, group+1))
                # print(f"Agent {agent_process} on break")
            agent_count = agent_count + group_size

    # Start the call generator process
    env.process(call_generator(env, agents))
    env.process(break_scheduler(env, agents))
    # print(f"break process {group_break}")
    # Run the simulation
    env.run(until=sim_duration)

    # Analyze results
    if len(wait_times) > 0:
        wait_array = np.array(wait_times)
        avg_wait = np.mean(wait_array)
        max_wait = np.max(wait_array)
        service_level = np.mean(wait_array <= TARGET_SLA) * 100
    else:
        avg_wait = 0
        max_wait = 0
        service_level = 100

    # Calculate utilization
    utilization = (total_busy_time / total_scheduled_time) * \
        100 if total_scheduled_time > 0 else 0

    return {
        "calls_arrived": calls_arrived,
        "calls_handled": calls_handled,
        "calls_abandoned": calls_abandoned,
        "calls_expected": sum(hourly_arrival_rates),
        "avg_wait": avg_wait,
        "max_wait": max_wait,
        "service_level": service_level,
        "utilization": round(utilization, 1),
        "total_busy_time": total_busy_time,
        "total_scheduled_time": total_scheduled_time
    }


def simulate_ideal_pattern(ideal_pattern):
    """
    Simulate the performance of the ideal shift pattern

    Parameters:
    ideal_pattern (dict): The ideal pattern structure from find_ideal_shift_pattern()

    Returns:
    dict: Dictionary containing both Erlang C and final simulation results by day and shift
    """
    import config_variables.config as config_module
    current_desired_sla = config_module.DESIRED_SLA

    erlang_results = {}  # Store initial Erlang C results
    final_results = {}  # Store results after optimization

    print("\n=== SIMULATING IDEAL SHIFT PATTERN PERFORMANCE ===")

    for day_stat in ideal_pattern['daily_stats']:
        day = day_stat['day']
        day_erlang_results = []
        day_final_results = []

        print(
            f"\nSimulating {day} with Pattern {ideal_pattern['pattern_number']}:")

        for i, shift in enumerate(day_stat['shifts']):
            shift_names = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth",
                           "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth"]
            shift_type = shift_names[i] if i < len(
                shift_names) else f"Shift {i+1}"

            # Get the hours covered by this shift
            hours = shift['hours']

            # Get the arrival rates for these hours
            arrival_rates = [arrival_rate_urgent[day][hour] for hour in hours]

            # Get the number of agents for this shift
            num_agents = shift['agents_needed']

            # Run the simulation for this shift with Erlang C agents
            erlang_result = run_shift_simulation(
                num_agents, arrival_rates, debug=False)

            # Store the Erlang C results
            erlang_shift = {
                "shift_type": shift_type,
                "hours": hours,
                "start_time": f"{shift['start_hour']:02d}:00",
                "end_time": f"{shift['end_hour']:02d}:00",
                "agents": num_agents,
                "calls_arrived": erlang_result["calls_arrived"],
                "calls_handled": erlang_result["calls_handled"],
                "calls_abandoned": erlang_result["calls_abandoned"],
                "calls_expected": erlang_result["calls_expected"],
                "avg_wait": erlang_result["avg_wait"],
                "max_wait": erlang_result["max_wait"],
                "service_level": erlang_result["service_level"],
                "utilization": erlang_result["utilization"]
            }
            day_erlang_results.append(erlang_shift)

            # Create a copy for the final results
            final_shift = erlang_shift.copy()
            current_result = erlang_result  # Track current simulation result

            # Print the Erlang C results
            print(f"SIMULATION ON ERLANG C CALCULATION FOR {shift_type} Shift")
            print(f"  {shift_type} Shift ({erlang_shift['start_time']}-{erlang_shift['end_time']}): "
                  f"{erlang_result['calls_arrived']} calls, "
                  f"{erlang_result['calls_handled']} handled, "
                  f"{erlang_result['calls_abandoned']} abandoned/Not Answered, "
                  f"{erlang_result['avg_wait']:.1f}s avg wait, "
                  f"{erlang_result['max_wait']:.1f}s max wait, "
                  f"{erlang_result['service_level']:.1f}% service level (Ans within 20 seconds) {num_agents} agents"
                  f", {erlang_result['utilization']:.1f}% utilization")

            # Add agents until service level is above 95%
            if current_result['service_level'] >= current_desired_sla:
                print(f'SIMULATION ON ERLANG C CALCULATION FOR SHIFT IS ABOVE {current_desired_sla}%')
                final_shift['total_busy_time'] = current_result['total_busy_time']
                final_shift['total_scheduled_time'] = current_result['total_scheduled_time']
            else:
                print(
                    f'SIMULATION AFTER INCREASING AGENTS UNTIL SERVICE LEVEL IS ABOVE {current_desired_sla}%')
                final_agents = num_agents

                while current_result['service_level'] < current_desired_sla:
                    final_agents += 1
                    current_result = run_shift_simulation(
                        final_agents, arrival_rates, debug=False)

                    # Update final results (not the Erlang C results)
                    final_shift['agents'] = final_agents
                    final_shift['service_level'] = current_result['service_level']
                    final_shift['utilization'] = current_result['utilization']
                    final_shift['calls_arrived'] = current_result['calls_arrived']
                    final_shift['calls_handled'] = current_result['calls_handled']
                    final_shift['calls_abandoned'] = current_result['calls_abandoned']
                    final_shift['avg_wait'] = current_result['avg_wait']
                    final_shift['max_wait'] = current_result['max_wait']
                    final_shift['total_busy_time'] = current_result['total_busy_time']
                    final_shift['total_scheduled_time'] = current_result['total_scheduled_time']

                    print(f"  Increasing agents to {final_agents} for {shift_type} Shift ({final_shift['start_time']}-{final_shift['end_time']}): "
                          f"{current_result['service_level']:.1f}% service level, {current_result['utilization']:.1f}% utilization, {current_result['calls_arrived']} Calls arrived, {current_result['calls_handled']} Calls handled,"
                          f"{current_result['calls_abandoned']} Calls abandoned, {current_result['avg_wait']:.1f}s Avg wait, {current_result['max_wait']:.1f}s Max wait")

            day_final_results.append(final_shift)

        # Store the results for this day
        erlang_results[day] = day_erlang_results

        # Calculate day summary for final results (for printing)
        final_results[day] = day_final_results
        day_calls = sum(r["calls_arrived"] for r in day_final_results)
        day_handled = sum(r["calls_handled"] for r in day_final_results)
        day_abandoned = sum(r["calls_abandoned"] for r in day_final_results)

        # Safe calculation of mean service level
        shifts_with_calls = [
            r for r in day_final_results if r["calls_handled"] > 0]
        day_sl = np.mean([r["service_level"]
                         for r in shifts_with_calls]) if shifts_with_calls else 100
        # After all shifts are processed for a day
        day_total_busy_time = sum(r.get("total_busy_time", 0)
                                  for r in day_final_results)
        day_total_scheduled_time = sum(
            r.get("total_scheduled_time", 0) for r in day_final_results)    
        day_avg_utilization = (day_total_busy_time / day_total_scheduled_time) * \
            100 if day_total_scheduled_time > 0 else 0

        print(f"\n{day} Summary: {day_calls} calls, "
              f"{day_handled} handled, "
              f"{day_abandoned} abandoned/Not Answered, "
              f"{day_sl:.1f}% service level, "
              f"{round(day_avg_utilization, 1)}% avg utilization, "
              f"total_agents = {sum(r['agents'] for r in day_final_results)}")

    # Calculate and print weekly final summary
    all_final_shifts = [shift for day_shifts in final_results.values()
                        for shift in day_shifts]
    weekly_calls = sum(shift["calls_arrived"] for shift in all_final_shifts)
    weekly_handled = sum(shift["calls_handled"] for shift in all_final_shifts)
    weekly_abandoned = sum(shift["calls_abandoned"]
                           for shift in all_final_shifts)

    # Safe calculation of mean service level
    shifts_with_calls = [
        shift for shift in all_final_shifts if shift["calls_handled"] > 0]
    weekly_sl = np.mean([shift["service_level"]
                        for shift in shifts_with_calls]) if shifts_with_calls else 100

    print(f"\nWeekly Summary: {weekly_calls} calls, "
          f"{weekly_handled} handled, "
          f"{weekly_abandoned} abandoned/Not Answered, "
          f"{weekly_sl:.1f}% service level")

    # Return both result sets
    return {
        "erlang_results": erlang_results,
        "final_results": final_results
    }

def create_sl_comparison_grid(results_by_sl, service_levels):
    """
    Create a structured grid comparing staffing needs across different service levels
    
    Parameters:
    results_by_sl (dict): Dictionary with simulation results for each service level
    service_levels (list): List of service level percentages that were simulated
    
    Returns:
    dict: Structured grid data for comparing staffing across service levels
    """
    # Days of week in standard order
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    grid = {
        "service_levels": service_levels,
        "days": {},
        "summary": {
            "weekly_agents": {},
            "avg_utilization": {}
        }
    }
    
    # Process each day
    for day in days:
        if not any(day in results_by_sl[sl]['final_results'] for sl in service_levels):
            continue  # Skip days that don't have data
            
        grid["days"][day] = {
            "shifts": {},
            "total_agents": {},
            "total_utilization": {}
        }
        
        # For each service level
        for sl in service_levels:
            day_results = results_by_sl[sl]["final_results"].get(day, [])
            if not day_results:
                continue
                
            # Calculate total agents for this day at this service level
            total_agents = sum(shift["agents"] for shift in day_results)
            grid["days"][day]["total_agents"][str(sl)] = total_agents
            
            # Calculate average utilization for this day at this service level
            total_busy_time = sum(shift.get("total_busy_time", 0) for shift in day_results)
            total_scheduled_time = sum(shift.get("total_scheduled_time", 0) for shift in day_results)
            avg_util = (total_busy_time / total_scheduled_time) * 100 if total_scheduled_time > 0 else 0
            grid["days"][day]["total_utilization"][str(sl)] = round(avg_util, 1)
            
            # Process each shift
            for shift in day_results:
                shift_key = f"{shift['shift_type']} ({shift['start_time']}-{shift['end_time']})"
                
                if shift_key not in grid["days"][day]["shifts"]:
                    grid["days"][day]["shifts"][shift_key] = {}
                
                # Store agents needed and utilization for this shift
                grid["days"][day]["shifts"][shift_key][str(sl)] = {
                    "agents": shift["agents"],
                    "utilization": shift["utilization"]
                }
    
    # Calculate weekly totals for each service level
    for sl in service_levels:
        # Total agents across all days
        weekly_agents = sum(
            grid["days"][day]["total_agents"].get(str(sl), 0) 
            for day in grid["days"]
        )
        grid["summary"]["weekly_agents"][str(sl)] = weekly_agents
        
        # Weighted average utilization across all days
        total_weighted_util = 0
        total_agents = 0
        for day in grid["days"]:
            day_agents = grid["days"][day]["total_agents"].get(str(sl), 0)
            day_util = grid["days"][day]["total_utilization"].get(str(sl), 0)
            total_weighted_util += day_agents * day_util
            total_agents += day_agents
            
        avg_util = total_weighted_util / total_agents if total_agents > 0 else 0
        grid["summary"]["avg_utilization"][str(sl)] = round(avg_util, 1)
    
    return grid

def simulate_across_service_levels(ideal_pattern, min_sl=80, max_sl=95, steps=5):
    """
    Run simulations across multiple service level targets
    
    Parameters:
    ideal_pattern (dict): The ideal shift pattern to use
    min_sl (int): Minimum service level target percentage
    max_sl (int): Maximum service level target percentage
    steps (int): Number of service level points to simulate
    
    Returns:
    dict: Comparison grid of results across service levels
    """
    import config_variables.config as config_module
    
    # Calculate service level points to test
    step_size = (max_sl - min_sl) / (steps - 1) if steps > 1 else 0
    service_levels = [min_sl + i * step_size for i in range(steps)]
    service_levels = [round(sl) for sl in service_levels]
    
    # Store original SLA setting
    original_sla = config_module.DESIRED_SLA
    
    # Dictionary to store results for each service level
    results_by_sl = {}
    
    print(f"\n=== RUNNING SERVICE LEVEL COMPARISON ({min_sl}% to {max_sl}%) ===")
    
    try:
        for sl in service_levels:
            print(f"\n--- SIMULATING WITH {sl}% SERVICE LEVEL TARGET ---")
            
            # Override SLA setting temporarily
            config_module.DESIRED_SLA = sl
            
            # This is the critical change - we need to recalculate staffing needs for each service level
            # to see the differences between service levels
            results = simulate_ideal_pattern(ideal_pattern)
            results_by_sl[sl] = results
            
    finally:
        # Always restore original SLA setting
        config_module.DESIRED_SLA = original_sla

    # # Transform results into the structure expected by create_sl_comparison_report
    # transformed_results = {}
    # for sl in service_levels:
    #     transformed_results[sl] = results_by_sl[sl]["final_results"]
    
    # Also calculate the grid for frontend display
    comparison_grid = create_sl_comparison_grid(results_by_sl, service_levels)
    
    # Return the transformed results for Excel report generation
    return {
        # "transformed_results": transformed_results,
        "comparison_grid": comparison_grid
    }