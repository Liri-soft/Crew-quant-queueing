import erlang_staffing
import shift_optimizer
import matplotlib.pyplot as plt
import pandas as pd
import os
from create_excel_report import create_excel_report
from erlang_staffing import SHIFT_HOURS
from ideal_shift import find_ideal_shift_pattern, display_ideal_shift_pattern
from simulation import simulate_staffing_plan


def main():
    # Calculate staffing needs
    print("Calculating staffing needs based on Erlang C formula...")
    staffing_needs = erlang_staffing.calculate_hourly_staffing_needs()

    # Print staffing needs
    for day in erlang_staffing.DAYS_OF_WEEK:
        print(f"\n{day} staffing needs:")
        for hour, staff in enumerate(staffing_needs[day]):
            print(f"  Hour {hour}: {staff} staff needed")

    erlang_staffing.visualize_staffing_needs(staffing_needs)

    # Generate all possible shift patterns
    print(
        f"\nGenerating the {erlang_staffing.SHIFT_HOURS} distinct shift patterns...")
    all_patterns = shift_optimizer.generate_shift_patterns()
    print(f"\nGenerated {len(all_patterns)} shift patterns:")
    for pattern in all_patterns:
        print(f"  Pattern {pattern['pattern_number']}:")
        for i, shift in enumerate(pattern['shifts']):
            shift_names = ["First", "Second", "Third",
                           "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
            shift_type = shift_names[i] if i < len(
                shift_names) else f"Shift {i+1}"
            start_time = f"{shift['start_hour']:02d}:00"
            end_time = f"{shift['end_hour']:02d}:00"
            # Analyze all shift patterns for each day
            print(f"    {shift_type} Shift: {start_time}-{end_time}")
    print("\nAnalyzing staffing needs for each shift pattern and day:")
    for day in erlang_staffing.DAYS_OF_WEEK:
        print(f"\n{day} - Staffing needs by pattern:")
        for pattern in all_patterns:
            evaluated_pattern = shift_optimizer.evaluate_shift_pattern(
                pattern, staffing_needs[day])
            total_agents = evaluated_pattern['total_agents']
            total_agent_hours = evaluated_pattern['total_agent_hours']
            print(
                f"  Pattern {pattern['pattern_number']}: Total {total_agents} agents needed, {total_agent_hours} agent hours")
            for i, shift in enumerate(evaluated_pattern['shifts']):
                shift_names = ["First", "Second", "Third",
                               "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
                shift_type = shift_names[i] if i < len(
                    shift_names) else f"Shift {i+1}"
                start_time = f"{shift['start_hour']:02d}:00"
                end_time = f"{shift['end_hour']:02d}:00"
                agents = shift['agents_needed']
                agent_hours = shift['agent_hours']
                print(
                    f"    {shift_type} Shift ({start_time}-{end_time}): {agents} agents, {agent_hours} agent hours")

    # # Find optimal shift pattern for each day
    # print("\nFinding optimal shift pattern for each day...")
    # # Display optimal shift patterns with utilization
    # shift_plan = shift_optimizer.create_shift_plan(staffing_needs)
    # print("\nOptimal shift patterns for each day:")
    # for day in erlang_staffing.DAYS_OF_WEEK:
    #     optimal_pattern = shift_plan[day]
    #     total_agents = optimal_pattern['total_agents']
    #     total_agent_hours = optimal_pattern['total_agent_hours']

    #     # Calculate utilization with the correct agent count
    #     total_staff_hours = sum(staffing_needs[day])
    #     utilization = (total_staff_hours / total_agent_hours) * \
    #         100 if total_agent_hours > 0 else 0

    #     print(
    #         f"\n{day}: Pattern {optimal_pattern['pattern_number']} (Total agents: {total_agents}, Agent hours: {total_agent_hours}, Utilization: {utilization:.1f}%)")
    #     for i, shift in enumerate(optimal_pattern['shifts']):
    #         shift_names = ["First", "Second", "Third",
    #                        "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
    #         shift_type = shift_names[i] if i < len(
    #             shift_names) else f"Shift {i+1}"
    #         start_time = f"{shift['start_hour']:02d}:00"
    #         end_time = f"{shift['end_hour']:02d}:00"
    #         agents = shift['agents_needed']
    #         agent_hours = shift['agent_hours']
    #         print(
    #             f"  {shift_type} Shift ({start_time}-{end_time}): {agents} agents, {agent_hours} agent hours")

    print("\n=== ANALYZING IDEAL PATTERN FOR CONSISTENT WEEKLY SCHEDULING ===")
    ideal_pattern = find_ideal_shift_pattern(staffing_needs)
    display_ideal_shift_pattern(ideal_pattern)

    # Run simulation to validate staffing needs
    print("\n=== RUNNING SIMULATION TO VALIDATE STAFFING NEEDS ===")
    simulate_staffing_plan(staffing_needs)

    # Create Excel report
    create_excel_report(staffing_needs, ideal_pattern)
    print("\nProcess completed. Excel report generated.")


if __name__ == "__main__":
    main()
