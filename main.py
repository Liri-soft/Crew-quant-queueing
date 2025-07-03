import erlang_staffing
import shift_optimizer
from create_excel_report import create_excel_report
from ideal_shift import find_ideal_shift_pattern, display_ideal_shift_pattern
# from simulation import simulate_staffing_plan
from shift_simulation import simulate_ideal_pattern


def main():
    
    # Calculate staffing needs
    print("Calculating staffing needs based on Erlang C formula...")
    staffing_needs = erlang_staffing.calculate_hourly_staffing_needs()

    # Generate all possible shift patterns
    print(f"Generating the {erlang_staffing.SHIFT_HOURS} distinct shift patterns...")
    all_patterns = shift_optimizer.generate_shift_patterns()
    
    # Display the patterns using the function from shift_optimizer
    shift_optimizer.display_shift_patterns(all_patterns)
    
    # Display evaluations for all days and patterns
    shift_optimizer.display_pattern_evaluations(all_patterns, staffing_needs)


    print("\n=== ANALYZING IDEAL PATTERN FOR CONSISTENT WEEKLY SCHEDULING ===")
    ideal_pattern = find_ideal_shift_pattern(staffing_needs)
    display_ideal_shift_pattern(ideal_pattern)

    # Simulation on ideal shift pattern
    simulation_results = simulate_ideal_pattern(ideal_pattern)

    # Create Excel report
    create_excel_report(staffing_needs, ideal_pattern, simulation_results)
    print("\nProcess completed. Excel report generated.")


if __name__ == "__main__":
    main()
