import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'grades.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class GradeHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    grade = db.Column(db.Float)
    target = db.Column(db.Float)
    max_possible = db.Column(db.Float)
    mode = db.Column(db.String(20))

with app.app_context():
    db.create_all()

grade_data = {
    "7": ["Math 1", "IS", "ComSci 1"],
    "8": ["Math 2", "Math 3", "Chemistry", "Biology", "ES", "Physics", "ComSci 2"],
    "9": ["Math 3", "Statistics", "Chemistry 2", "Biology 2", "Physics 2", "ComSci 3"],
    "10": ["Math 4", "Chemistry 3", "Biology 3", "Physics 3", "ComSci 4"],
    "11": ["Math 5", "Chemistry 4", "Biology 4", "Physics 4"],
    "12": ["Math 6", "Chemistry 5", "Biology 5", "Physics 5"]
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        choice = request.form.get("agreement")
        if choice == "yes":
            return redirect(url_for("calculator_page"))
    return render_template("index.html")

@app.route("/calculator", methods=["GET", "POST"])
def calculator_page():
    selected_grade = request.args.get("grade")
    subjects = grade_data.get(selected_grade, [])
    error = None
    result_data = None 
    history = GradeHistory.query.all()

    if request.method == "POST":
        try:
            plan_type = request.form.get("plan_type") or "quarterly"
            iterations = 4 if plan_type == 'yearly' else 1
            target = float(request.form.get("target_grade") or 0)
            chosen_subject = request.form.get("chosen_subject")
            
            q_grades = []
            q_maxes = []
            total_req_s = 0
            total_req_f = 0

            for i in range(1, iterations + 1):
                suf = f"_q{i}" if plan_type == 'yearly' and i > 1 else ""
                
                sw = float(request.form.get(f"summ_weight{suf}") or request.form.get("summ_weight") or 0)
                fw = float(request.form.get(f"form_weight{suf}") or request.form.get("form_weight") or 0)
                
                if (sw + fw) != 100:
                    error = f"Weights for Period {i} must add up to 100%!"
                    return render_template("calculator.html", grade=selected_grade, subjects=subjects, history=history, error=error)

                s_scores = [float(x) for x in request.form.getlist(f"s_scores{suf}[]") if x.strip()]
                s_totals = [float(x) for x in request.form.getlist(f"s_totals{suf}[]") if x.strip()]
                f_scores = [float(x) for x in request.form.getlist(f"f_scores{suf}[]") if x.strip()]
                f_totals = [float(x) for x in request.form.getlist(f"f_totals{suf}[]") if x.strip()]
                
                rem_s = float(request.form.get(f"rem_summ{suf}") or request.form.get("rem_summ") if i==1 else request.form.get(f"rem_summ{suf}") or 0)
                rem_f = float(request.form.get(f"rem_form{suf}") or request.form.get("rem_form") if i==1 else request.form.get(f"rem_form{suf}") or 0)

                s_score_sum, s_total_sum = sum(s_scores), sum(s_totals)
                f_score_sum, f_total_sum = sum(f_scores), sum(f_totals)

                ov_s_total = s_total_sum + rem_s
                ov_f_total = f_total_sum + rem_f

                if ov_s_total > 0 and ov_f_total > 0:
                    curr_q = (s_score_sum / ov_s_total * sw) + (f_score_sum / ov_f_total * fw)
                    max_q = ((s_score_sum + rem_s) / ov_s_total * sw) + ((f_score_sum + rem_f) / ov_f_total * fw)
                    q_grades.append(curr_q)
                    q_maxes.append(max_q)

                    total_req_s += max(0, round(((target * (sw/100) / (sw if sw > 0 else 1)) * ov_s_total) - s_score_sum, 1))
                    total_req_f += max(0, round(((target * (fw/100) / (fw if fw > 0 else 1)) * ov_f_total) - f_score_sum, 1))
                else:
                    error = f"Quarter {i} totals must be > 0!"
                    return render_template("calculator.html", grade=selected_grade, subjects=subjects, history=history, error=error)

            final_grade = sum(q_grades) / iterations
            final_max = sum(q_maxes) / iterations
            
            notes_path = None
            if selected_grade and chosen_subject:
                clean_name = chosen_subject.lower().replace(" ", "")
                notes_path = f"grade_{selected_grade}_notes/{clean_name}.txt"

            new_entry = GradeHistory(
                subject=chosen_subject, grade=round(final_grade, 2), 
                target=target, max_possible=round(final_max, 2), mode=plan_type
            )
            db.session.add(new_entry)
            db.session.commit()
            
            result_data = {
                "grade": round(final_grade, 2), 
                "max": round(final_max, 2),
                "target": target, 
                "subject": chosen_subject, 
                "mode": plan_type,
                "req_s": round(total_req_s, 1), 
                "req_f": round(total_req_f, 1), 
                "notes": notes_path
            }
            history = GradeHistory.query.all()

        except Exception as e:
            error = f"Error: {e}"

    return render_template("calculator.html", grade=selected_grade, subjects=subjects, result=result_data, history=history, error=error)

@app.route("/delete/<int:id>")
def delete_grade(id):
    record = GradeHistory.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("calculator_page"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_grade(id):
    record = GradeHistory.query.get_or_404(id)
    if request.method == "POST":
        record.subject = request.form.get("subject")
        record.grade = float(request.form.get("grade") or 0)
        record.target = float(request.form.get("target") or 0)
        db.session.commit()
        return redirect(url_for("calculator_page"))
    return render_template("edit.html", record=record)

if __name__ == "__main__":
    app.run(debug=True)
