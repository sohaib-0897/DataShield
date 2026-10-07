from behavior import get_behavior


def calculate_dlp_score(behavior):
    score = 0

    # Sensitive activity
    score += min(
        behavior["sensitive_files_accessed"] * 2,
        20
    )

    # Repeated access
    score += min(
        behavior["repeated_accesses"] * 3,
        15
    )

    # Critical files
    score += min(
        behavior["critical_files_accessed"] * 5,
        20
    )

    # File modifications
    score += min(
        behavior["files_modified"] * 5,
        15
    )

    # After-hours activity
    score += min(
        behavior["after_hours_events"] * 3,
        15
    )

    return min(score, 100)


def get_risk_level(score):

    if score >= 75:
        return "CRITICAL"

    if score >= 50:
        return "HIGH"

    if score >= 25:
        return "MEDIUM"

    return "LOW"


def calculate_risk(username=None):

    behavior = get_behavior(username)

    dlp_score = calculate_dlp_score(behavior)

    risk_level = get_risk_level(dlp_score)

    return {
        "dlp_score": dlp_score,
        "risk_level": risk_level,
        "behavior": behavior
    }


def print_risk(username=None):

    result = calculate_risk(username)

    print()
    print("===================================")
    print("          DLP RISK ANALYSIS")
    print("===================================")

    print(
        f"DLP Risk Score:  {result['dlp_score']}/100"
    )

    print(
        f"Risk Level:      {result['risk_level']}"
    )

    print()
    print("Behavior:")
    
    for key, value in result["behavior"].items():
        print(f"{key}: {value}")

    print("===================================")


if __name__ == "__main__":
    print_risk()