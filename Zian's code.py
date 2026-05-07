def get_valid_int(prompt, min_val=0, max_val=None):
    while True:
        try:
            val = int(input(prompt))
            if val < min_val or (max_val is not None and val > max_val):
                print(f"Please enter a number between {min_val} and {max_val}.")
                continue
            return val
        except ValueError:
            print("Invalid input. Please enter a whole number.")

def get_valid_choice(prompt, options):
    while True:
        choice = input(prompt).strip().lower()
        if choice in options:
            return choice
        print(f"Invalid choice. Please select from: {', '.join(options)}")

def calculate_subject_grade(subject_name, summ_weight, form_weight, target_grade):
    data = {"summ_score": 0, "summ_total": 0, "form_score": 0, "form_total": 0}
    
    for category in ["summative", "formative"]:
        print(f"\n--- {category.capitalize()} Assessments for {subject_name} ---")
        while True:
            score = get_valid_int(f"Enter current score for {category} (0 if none): ")
            total = get_valid_int(f"Enter points possible for this assessment: ", min_val=1)
            
            data[f"{category[:4]}_score"] += score
            data[f"{category[:4]}_total"] += total
            
            if get_valid_choice("Add another existing assessment? (y/n): ", ['y', 'n']) == 'n':
                break

    print(f"\n--- Future Opportunity for {subject_name} ---")
    rem_summ_total = get_valid_int("Total potential points LEFT in future Summatives: ", min_val=0)
    rem_form_total = get_valid_int("Total potential points LEFT in future Formatives: ", min_val=0)

    overall_summ_total = data['summ_total'] + rem_summ_total
    overall_form_total = data['form_total'] + rem_form_total

    max_summ_contrib = ((data['summ_score'] + rem_summ_total) / overall_summ_total) * summ_weight if overall_summ_total > 0 else 0
    max_form_contrib = ((data['form_score'] + rem_form_total) / overall_form_total) * form_weight if overall_form_total > 0 else 0
    max_grade = max_summ_contrib + max_form_contrib

    curr_summ_perc = (data['summ_score'] / overall_summ_total) * summ_weight if overall_summ_total > 0 else 0
    curr_form_perc = (data['form_score'] / overall_form_total) * form_weight if overall_form_total > 0 else 0
    current_grade = curr_summ_perc + curr_form_perc

    print(f"\nResults for {subject_name}:")
    print(f"Current Grade: {current_grade:.2f}% (relative to term total)")

    if current_grade >= target_grade:
        print("Status: Target Grade Reached! 🎉")
    elif max_grade < target_grade:
        print(f"Status: You are {target_grade - current_grade:.2f}% away.")
        print(f"FAILED: Goal is no longer mathematically possible. (Max possible: {max_grade:.2f}%)")
    else:
        dist_to_go = target_grade - current_grade
        print(f"Status: You are {dist_to_go:.2f}% away from your target.")
        
        summ_target_contrib = target_grade * (summ_weight / 100)
        form_target_contrib = target_grade * (form_weight / 100)
        
        pts_req_summ = ((summ_target_contrib / summ_weight) * overall_summ_total) - data['summ_score']
        pts_req_form = ((form_target_contrib / form_weight) * overall_form_total) - data['form_score']

        print(f"Minimum Summative points needed: {max(0, round(pts_req_summ, 1))}")
        print(f"Minimum Formative points needed: {max(0, round(pts_req_form, 1))}")

def main():
    print("=== Student Academic Planner ===")
    
    num_subjects = get_valid_int("How many subjects do you want to calculate? ", min_val=1, max_val=15)
    
    subjects = []
    for i in range(num_subjects):
        name = input(f"Enter name for Subject {i+1}: ").strip()
        subjects.append(name if name else f"Subject {i+1}")

    plan_type = get_valid_choice("Plan type? (yearly/quarterly): ", ['yearly', 'quarterly'])
    iterations = 4 if plan_type == 'yearly' else 1
    
    target = get_valid_int("Enter your target grade percentage: ", 0, 100)
    s_weight = get_valid_int("Summative weight %: ", 0, 100)
    f_weight = 100 - s_weight
    print(f"Formative weight set to {f_weight}%")

    for period in range(1, iterations + 1):
        label = "Quarter" if iterations == 4 else "Period"
        print(f"\n{'='*30}\nProcessing {label} {period}\n{'='*30}")
        for sub in subjects:
            calculate_subject_grade(sub, s_weight, f_weight, target)
            print("-" * 20)

if _name_ == "_main_":
    main()
