from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask import send_file

from predictor import Predictor

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import datetime

app = Flask(__name__)

model = Predictor()


# ===================================================
# HOME
# ===================================================

@app.route("/")
def home():

    return render_template("index.html")


# ===================================================
# AI PREDICTION
# ===================================================

@app.route("/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        elements = data["elements"]

        compositions = data["compositions"]

        result = model.predict(

            elements,

            compositions

        )

        # PDF এর জন্য composition save
        result["elements"] = elements
        result["compositions"] = compositions

        return jsonify(result)

    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ===================================================
# PDF REPORT
# ===================================================

@app.route("/download_report", methods=["POST"])
def download_report():

    try:

        data = request.json

        pdf_file = "static/HEA_Report.pdf"

        styles = getSampleStyleSheet()

        doc = SimpleDocTemplate(pdf_file)

        story = []

        # -------------------------

        story.append(

            Paragraph(

                "<b>PHEA-ATLAS AI</b>",

                styles["Title"]

            )

        )

        story.append(

            Paragraph(

                "Physics-Informed High Entropy Alloy Prediction",

                styles["Normal"]

            )

        )

        story.append(

            Spacer(1,20)

        )

        # -------------------------

        story.append(

            Paragraph(

                "<b>Composition</b>",

                styles["Heading2"]

            )

        )

        table_data = [

            ["Element","Composition (%)"]

        ]

        for e,c in zip(

            data["elements"],

            data["compositions"]

        ):

            table_data.append(

                [e,str(c)]

            )

        table = Table(table_data)

        table.setStyle(

            TableStyle([

                ("BACKGROUND",(0,0),(-1,0),colors.grey),

                ("TEXTCOLOR",(0,0),(-1,0),colors.white),

                ("GRID",(0,0),(-1,-1),1,colors.black),

                ("BACKGROUND",(0,1),(-1,-1),colors.beige),

                ("ALIGN",(0,0),(-1,-1),"CENTER")

            ])

        )

        story.append(table)

        story.append(Spacer(1,20))

        # -------------------------

        story.append(

            Paragraph(

                "<b>Prediction Result</b>",

                styles["Heading2"]

            )

        )

        story.append(

            Paragraph(

                f"Probability : {data['probability']} %",

                styles["Normal"]

            )

        )

        story.append(

            Paragraph(

                f"Confidence : {data['confidence']}",

                styles["Normal"]

            )

        )

        story.append(

            Paragraph(

                data["interpretation"],

                styles["Normal"]

            )

        )

        story.append(

            Spacer(1,20)

        )

        # -------------------------

        story.append(

            Paragraph(

                "<b>Physics Features</b>",

                styles["Heading2"]

            )

        )

        physics_table = [

            ["Feature","Value"]

        ]

        for k,v in data["physics"].items():

            physics_table.append(

                [k,str(v)]

            )

        table2 = Table(physics_table)

        table2.setStyle(

            TableStyle([

                ("BACKGROUND",(0,0),(-1,0),colors.darkblue),

                ("TEXTCOLOR",(0,0),(-1,0),colors.white),

                ("GRID",(0,0),(-1,-1),1,colors.black),

                ("BACKGROUND",(0,1),(-1,-1),colors.whitesmoke),

                ("ALIGN",(0,0),(-1,-1),"CENTER")

            ])

        )

        story.append(table2)

        story.append(

            Spacer(1,20)

        )

        # -------------------------

        story.append(

            Paragraph(

                "Generated : "

                + datetime.datetime.now().strftime(

                    "%d-%m-%Y %H:%M"

                ),

                styles["Normal"]

            )

        )

        story.append(

            Spacer(1,30)

        )

        story.append(

            Paragraph(

                "<b>Developed by Morsalin Hosain Dip</b>",

                styles["Heading2"]

            )

        )

        doc.build(story)

        return jsonify({

            "success": True,

            "file": "/static/HEA_Report.pdf"

        })

    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({

            "success": False,

            "error": str(e)

        })


# ===================================================

if __name__ == "__main__":

    app.run(debug=True)