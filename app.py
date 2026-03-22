from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# ---------------- LOAD DATA ----------------
data = pd.read_csv("dataset.csv")
data.columns = data.columns.str.strip()

# Convert to numeric safely
data["Privacy_Risk_Score"] = pd.to_numeric(
    data["Privacy_Risk_Score"], errors="coerce"
)

# Risk mapping
level_map = {
    "no": 0,
    "low": 1,
    "medium": 2,
    "high": 3
}

# ---------------- COMMON FUNCTION ----------------
def calculate_score(row):

    permission_score = (float(row["Privacy_Risk_Score"]) / 10) * 3

    comment_score = level_map.get(
        str(row["Comment_Risk_Level"]).strip().lower(), 0
    )

    policy_score = level_map.get(
        str(row["Policy_Risk_Factor"]).strip().lower(), 0
    )

    final_score = (
        permission_score * 0.5 +
        comment_score * 0.3 +
        policy_score * 0.2
    )

    return (final_score / 3) * 100


# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        app_name = request.form["app_name"].strip().lower()

        result = data[
            data["AppName"].str.strip().str.lower() == app_name
        ]

        if not result.empty:

            row = result.iloc[0]
            percentage = calculate_score(row)

            if percentage <= 30:
                level = "Low"
                description = "Low risk app with minimal data usage."

            elif percentage <= 60:
                level = "Medium"
                description = "Moderate data collection and tracking."

            else:
                level = "High"
                description = "High data usage and potential privacy risk."

            return render_template(
                "index.html",
                percentage=round(percentage, 2),
                level=level,
                description=description,
                app_name=row["AppName"]
            )

        else:
            return render_template("index.html", error="App not found")

    return render_template("index.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    comments = data["Comment_Risk_Level"].str.lower()

    high = (comments == "high").sum()
    medium = (comments == "medium").sum()
    low = (comments == "low").sum()

    return render_template(
        "dashboard.html",
        high=high,
        medium=medium,
        low=low
    )


# ---------------- COMPARE ----------------
@app.route("/compare", methods=["GET", "POST"])
def compare():

    if request.method == "POST":

        app1 = request.form["app1"].strip().lower()
        app2 = request.form["app2"].strip().lower()

        result1 = data[
            data["AppName"].str.strip().str.lower() == app1
        ]

        result2 = data[
            data["AppName"].str.strip().str.lower() == app2
        ]

        if not result1.empty and not result2.empty:

            row1 = result1.iloc[0]
            row2 = result2.iloc[0]

            score1 = round(calculate_score(row1), 2)
            score2 = round(calculate_score(row2), 2)

            return render_template(
                "compare.html",
                app1=row1["AppName"],
                app2=row2["AppName"],
                score1=score1,
                score2=score2
            )

        else:
            return render_template(
                "compare.html",
                error="One or both apps not found"
            )

    return render_template("compare.html")


# ---------------- DATASET ----------------
@app.route("/dataset")
def dataset():

    apps = data[[
        "AppName",
        "Category",
        "Privacy_Risk_Score",
        "Comment_Risk_Level",
        "Policy_Risk_Factor"
    ]]

    return render_template(
        "dataset.html",
        tables=apps.to_dict(orient="records")
    )


# ---------------- MY APPS ----------------
@app.route("/myapps", methods=["GET", "POST"])
def myapps():

    if request.method == "POST":

        input_text = request.form["app_name"].lower()

        app_names = [
            a.strip()
            for a in input_text.replace("\n", ",").split(",")
            if a.strip()
        ]

        results = []
        high = medium = low = 0

        for app in app_names:

            result = data[
                data["AppName"].str.strip().str.lower() == app
            ]

            if not result.empty:

                row = result.iloc[0]
                percentage = calculate_score(row)

                if percentage <= 30:
                    level = "Low"
                    low += 1
                elif percentage <= 60:
                    level = "Medium"
                    medium += 1
                else:
                    level = "High"
                    high += 1

                results.append({
                    "name": row["AppName"],
                    "percentage": round(percentage, 2),
                    "level": level
                })

        return render_template(
            "myapps.html",
            results=results,
            high=high,
            medium=medium,
            low=low
        )

    return render_template("myapps.html")


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run()