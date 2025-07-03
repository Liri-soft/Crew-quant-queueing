# Call Volume
CALL_VOLUME = {
    "Monday": [4, 2, 1, 2, 2, 1, 2, 4, 8, 23, 77, 176, 320, 482, 473, 422, 380, 303, 225, 129, 75, 36, 21, 9],
    "Tuesday": [4, 3, 2, 2, 2, 2, 2, 3, 12, 36, 83, 172, 314, 442, 416, 367, 317, 245, 161, 117, 66, 24, 17, 8],
    "Wednesday": [4, 2, 2, 1, 1, 2, 2, 5, 12, 41, 92, 189, 340, 451, 437, 405, 362, 277, 199, 128, 66, 32, 16, 7],
    "Thursday": [5, 5, 3, 2, 2, 3, 2, 4, 11, 34, 92, 183, 329, 446, 429, 358, 315, 243, 173, 110, 61, 28, 14, 6],
    "Friday": [2, 2, 1, 3, 0, 3, 2, 4, 8, 28, 105, 203, 316, 436, 452, 395, 351, 267, 179, 122, 66, 32, 15, 8],
    "Saturday": [6, 3, 3, 1, 2, 2, 3, 6, 16, 40, 92, 212, 380, 519, 502, 470, 372, 312, 207, 123, 78, 34, 20, 9],
    "Sunday": [5, 2, 2, 3, 1, 2, 3, 4, 9, 31, 76, 142, 225, 258, 228, 169, 134, 98, 65, 30, 21, 12, 5, 5]
}
# Shift structure parameters
SHIFT_HOURS = 8          # Length of each shift (4, 6, 8, or 12)
AGENT_EFFICIENCY = 100  # Agent efficiency (e.g., 100% of time is productive)
# Call handling
AVG_HANDLING_TIME = 6.3   # Average handling time in minutes
AVG_PATIENCE = 180               # Average caller patience in seconds before abandonment
# Service level goals
TARGET_SLA = 20          # Target answer time in seconds (e.g., 20 seconds)
DESIRED_SLA = 95         # Target service level percentage (e.g., 95%)
# Call complexity distribution
CALL_COMPLEXITY_DISTRIBUTION = {
    # [normal, semicomplex, complex]
    "probabilities": [0.50, 0.30, 0.20],
    "complexity_factors": {
        "semicomplex": 1.2,  # 20% longer handling time
        "complex": 1.8,      # 80% longer handling time
    }
}
# After call work time range (seconds)
ACW_MIN = 10
ACW_MAX = 20
# Break scheduling parameters
LUNCH_BREAK_TIME = 45  # Break duration in seconds (45 minutes)
# Maximum percentage of agents on break at once
MAX_PERCENTAGE_AGENTS_ON_BREAK = 30
