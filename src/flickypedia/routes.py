import datetime
import json, random
import os, time
import uuid

from flask import render_template, redirect, url_for, jsonify

from flickypedia import app, executor


@app.route("/")
def index():
    return render_template("index.html")


def upload_batch():
    try:
        print("starting task!")
        u = uuid.uuid4()

        os.makedirs("tasks", exist_ok=True)

        with open(f"tasks/{u}.json", "w") as outfile:
            outfile.write(
                json.dumps(
                    {
                        "id": str(u),
                        "date_started": datetime.datetime.now().isoformat(),
                        "state": "waiting",
                    }
                )
            )

        time.sleep(random.uniform(0.2, 3))

        d = json.load(open(f"tasks/{u}.json"))['date_started']

        with open(f"tasks/{u}.json", "w") as outfile:
            outfile.write(
                json.dumps(
                    {
                        "id": str(u),
                        "date_started": datetime.datetime.now().isoformat(),
                        "state": "processing",
                    }
                )
            )


        d = json.load(open(f"tasks/{u}.json"))['date_started']

        time.sleep(random.uniform(0.2, 3))

        if random.random() > 0.7:
            with open(f"tasks/{u}.json", "w") as outfile:
                outfile.write(
                    json.dumps(
                        {
                            "id": str(u),
                            "date_started": datetime.datetime.now().isoformat(),
                            "state": "failed",
                        }
                    )
                )
        else:

            with open(f"tasks/{u}.json", "w") as outfile:
                outfile.write(
                    json.dumps(
                        {
                            "id": str(u),
                            "date_started": datetime.datetime.now().isoformat(),
                            "state": "succeeded",
                        }
                    )
                )
    except Exception as e:
        print(f"!!! {e}")


@app.route("/jobs")
def jobs():
    j = []

    for f in os.listdir("tasks"):
        if f.endswith(".json"):
            print(f)
            j.append(json.load(open(f"tasks/{f}")))

    return jsonify(sorted(j, key=lambda t: t['date_started'], reverse=True))


@app.route("/upload_images")
def upload_images():
    executor.submit(upload_batch)

    return redirect(url_for("index"))
